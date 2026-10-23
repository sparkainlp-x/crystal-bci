"""Tests for crystal-bci. Run: python tests.py"""

import math
import random

from crystal_bci import (blink_waveform, synth_stream, CrystalLearner,
                         crystal_template, cosine, residue_whiteness,
                         template_statistic, calibrate_tau, evaluate,
                         youden_threshold)

C, L, T, TOL = 4, 24, 20000, 12
passed = []


def check(name, cond):
    assert cond, f"FAILED: {name}"
    passed.append(name)
    print(f"  ok: {name}")


def fixture(seed=7):
    rng = random.Random(seed)
    return synth_stream(T, C, 400, 0.35, 0.15, rng)


def learn(seed=7):
    s, peaks, b = fixture(seed)
    cl = CrystalLearner(C, L)
    cl.observe(s, C, L, thresh=1.5)
    return s, peaks, b, cl, crystal_template(cl)


print("crystal-bci tests")

# 1. the synthetic blink is biphasic
w = blink_waveform()
check("waveform biphasic (sums ~0)", abs(sum(w)) < 1e-9)
check("waveform has both lobes", max(w) > 0.5 and min(w) < -0.5)

# 2. the crystal recovers the blink direction, unsupervised
s, peaks, b, cl, crystal = learn()
true_vec = [w[i] * b[c] for i in range(L) for c in range(C)]
n = math.sqrt(sum(x * x for x in true_vec))
true_vec = [x / n for x in true_vec]
cos = cosine(crystal, true_vec)
check(f"cosine(crystal, truth) = {cos:.3f} > 0.6", cos > 0.6)

# 3. residue whiteness is a sane number in [0, 1]
rw = residue_whiteness(cl.covariance(), 1, [crystal])
check(f"residue whiteness {rw:.3f} in [0,1]", 0.0 <= rw <= 1.0)

# 4. the gate calibrates to a separating threshold
H = T // 2
s1, s2 = s[:H], s[H:]
p1 = [p for p in peaks if p < H]
p2 = [p - H for p in peaks if p >= H]
tau, J = calibrate_tau(s1, p1, crystal, C, L, TOL)
check(f"tau={tau:.3f} separates (J={J:.3f} > 0.5)", J > 0.5)

# 5. frozen gate: every blink caught, nothing invented
hr, fa = evaluate(s2, p2, crystal, tau, C, L, TOL)
check(f"hit rate {hr:.3f} == 1.0", hr == 1.0)
check(f"false alarms {fa} == 0", fa == 0)

# 6. blink-free control stays silent (fail-closed holds)
rng2 = random.Random(99)
s0, _, _ = synth_stream(12000, C, 400, 0.35, 0.15, rng2, blinks=False)
_, fa0 = evaluate(s0, [], crystal, tau, C, L, TOL)
check(f"blink-free false alarms {fa0} == 0", fa0 == 0)

# 7. determinism: same seed -> same crystal
_, _, _, _, c2 = learn(seed=7)
check("deterministic crystal", cosine(crystal, c2) > 0.9999)

print(f"\n{len(passed)}/{len(passed)} tests pass")
