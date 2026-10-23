"""Demo: the crystal learns the blink, then gates the command.

1. Learn: peak-triggered Hebbian crystal from a noisy synthetic
   multichannel stream. Report what it recovered.
2. Calibrate: Youden's J gate on labeled candidates, then frozen.
3. Evaluate: hit rate + false alarms on a fresh stream, plus a
   blink-free control.
4. A/B: learned crystal vs a fixed canonical template.

Run: python demo.py
"""

import math
import random

from crystal_bci import (blink_waveform, synth_stream, CrystalLearner,
                         crystal_template, cosine, residue_whiteness,
                         template_statistic, template_match,
                         calibrate_tau, evaluate, detect,
                         score_events, youden_threshold)

C, L, T, TOL = 4, 24, 20000, 12


def main():
    rng = random.Random(7)
    s, peaks, b = synth_stream(T, C, 400, 0.35, 0.15, rng)

    print("== 1. the crystal forms ==")
    cl = CrystalLearner(C, L)
    cl.observe(s, C, L, thresh=1.5)
    crystal = crystal_template(cl)
    w = blink_waveform(L)
    true_vec = [w[i] * b[c] for i in range(L) for c in range(C)]
    n = math.sqrt(sum(x * x for x in true_vec))
    true_vec = [x / n for x in true_vec]
    print(f"windows collected : {cl.n}")
    print(f"cosine(crystal, truth): {cosine(crystal, true_vec):.3f}")
    print("residue whiteness : "
          f"{residue_whiteness(cl.covariance(), 1, [crystal]):.3f}")
    print("unsupervised, no labels used -- the stream taught the shape.\n")

    H = T // 2
    s1, s2 = s[:H], s[H:]
    p1 = [p for p in peaks if p < H]
    p2 = [p - H for p in peaks if p >= H]

    print("== 2. the gate calibrates (then freezes) ==")
    tau, J = calibrate_tau(s1, p1, crystal, C, L, TOL)
    print(f"tau = {tau:.3f}, Youden's J = {J:.3f}\n")

    print("== 3. fresh stream: does 'next' fire correctly? ==")
    hr, fa = evaluate(s2, p2, crystal, tau, C, L, TOL)
    print(f"hit rate {hr:.3f} | false alarms {fa} | blinks {len(p2)}")
    rng2 = random.Random(99)
    s0, _, _ = synth_stream(12000, C, 400, 0.35, 0.15, rng2,
                            blinks=False)
    _, fa0 = evaluate(s0, [], crystal, tau, C, L, TOL)
    print(f"blink-free control (12000 ticks): {fa0} false alarms\n")

    print("== 4. A/B: learned crystal vs fixed template ==")
    canon = [[w[i] if c == 0 else 0.0 for c in range(C)]
             for i in range(L)]
    flat = [canon[i][c] for i in range(L) for c in range(C)]
    nn = math.sqrt(sum(x * x for x in flat))
    flat = [x / nn for x in flat]
    tmp = CrystalLearner(C, L)
    for name, fn in [("crystal", lambda wn: template_statistic(wn, crystal)),
                     ("fixed  ", lambda wn: template_match(wn, canon))]:
        tr = [(t0, fn(tmp.window(s1, t0, C, L)))
              for t0 in range(0, len(s1) - L, 4)]
        cands = []
        for i in range(1, len(tr) - 1):
            t0, v = tr[i]
            if v >= tr[i - 1][1] and v >= tr[i + 1][1]:
                cands.append((v, any(abs(t0 + L // 2 - p) <= TOL
                                    for p in p1)))
        t2, J2 = youden_threshold(cands)
        # event-level detection with this statistic, frozen tau:
        trace = [(t0, fn(tmp.window(s2, t0, C, L)))
                 for t0 in range(0, len(s2) - L, 4)]
        evs = [t0 + L // 2 for i, (t0, v) in enumerate(trace[1:-1], 1)
               if v >= t2 and v >= trace[i - 1][1] and v >= trace[i + 1][1]]
        h, f = score_events(evs, p2, TOL)
        print(f"{name}: J={J2:.3f} -> hit {h:.3f}, false alarms {f}")
    print("\nthe crystal wins because it learned the mixing direction\n"
          "from the data instead of assuming it.\n")

    print("== verdict ==")
    print("Crystallization, applied: the template lives in the first\n"
          "moment (spike-triggered average), the covariance describes\n"
          "what is left. Fail-closed gating on top. Synthetic only --\n"
          "the device-data adapter to real recordings is still missing.")


if __name__ == "__main__":
    main()
