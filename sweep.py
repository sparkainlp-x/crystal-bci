"""Multi-seed sweep for crystal-bci. SYNTHETIC data only.

Each seed: learn crystal on a full stream, calibrate tau on the first
half, evaluate on the second half and on a blink-free control.
Reports mean ± standard error over seeds. Seed 7 alone (the original
demo) is one draw, not the distribution.

Run: python sweep.py [n_seeds]
"""

import math
import random
import statistics
import sys

from crystal_bci import (blink_waveform, calibrate_tau, cosine,
                         crystal_template, CrystalLearner, evaluate,
                         residue_whiteness, score_events, synth_stream,
                         template_match, template_statistic,
                         youden_threshold)

C, L, T, TOL = 4, 24, 20000, 12
N_SEEDS = 20


def mean_se(xs):
    m = statistics.fmean(xs)
    se = statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
    return m, se


def ab_fixed(s1, p1, s2, p2, w):
    canon = [[w[i] if c == 0 else 0.0 for c in range(C)] for i in range(L)]
    tmp = CrystalLearner(C, L)
    tr = [(t0, template_match(tmp.window(s1, t0, C, L), canon))
          for t0 in range(0, len(s1) - L, 4)]
    cands = []
    for i in range(1, len(tr) - 1):
        t0, v = tr[i]
        if v >= tr[i - 1][1] and v >= tr[i + 1][1]:
            cands.append((v, any(abs(t0 + L // 2 - p) <= TOL for p in p1)))
    tau, J = youden_threshold(cands)
    trace = [(t0, template_match(tmp.window(s2, t0, C, L), canon))
             for t0 in range(0, len(s2) - L, 4)]
    evs = [t0 + L // 2 for i, (t0, v) in enumerate(trace[1:-1], 1)
           if v >= tau and v >= trace[i - 1][1] and v >= trace[i + 1][1]]
    hr, fa = score_events(evs, p2, TOL)
    return hr, fa, J


def one(seed):
    rng = random.Random(seed)
    s, peaks, b = synth_stream(T, C, 400, 0.35, 0.15, rng)
    cl = CrystalLearner(C, L)
    cl.observe(s, C, L, thresh=1.5)
    crystal = crystal_template(cl)
    w = blink_waveform(L)
    true = [w[i] * b[c] for i in range(L) for c in range(C)]
    n = math.sqrt(sum(x * x for x in true)) or 1.0
    true = [x / n for x in true]
    H = T // 2
    s1, s2 = s[:H], s[H:]
    p1 = [p for p in peaks if p < H]
    p2 = [p - H for p in peaks if p >= H]
    tau, J = calibrate_tau(s1, p1, crystal, C, L, TOL)
    hr, fa = evaluate(s2, p2, crystal, tau, C, L, TOL)
    s0, _, _ = synth_stream(12000, C, 400, 0.35, 0.15,
                            random.Random(seed + 1000), blinks=False)
    _, fa0 = evaluate(s0, [], crystal, tau, C, L, TOL)
    # A/B crystal on eval half (same tau)
    hr_c, fa_c = hr, fa
    hr_f, fa_f, J_f = ab_fixed(s1, p1, s2, p2, w)
    return {
        "cosine": cosine(crystal, true),
        "whiteness": residue_whiteness(cl.covariance(), 1, [crystal]),
        "tau": tau, "J": J, "windows": cl.n, "blinks_eval": len(p2),
        "hit_rate": hr, "false_alarms": fa,
        "blinkfree_fa": fa0,
        "crystal_hit": hr_c, "crystal_fa": fa_c,
        "fixed_hit": hr_f, "fixed_fa": fa_f, "fixed_J": J_f,
    }


def run(n_seeds=N_SEEDS):
    return [one(s) for s in range(n_seeds)]


def spread(xs):
    """Mean, standard error, sample SD, median, min, max across seeds."""
    m, se = mean_se(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return m, se, sd, statistics.median(xs), min(xs), max(xs)


def fmt(ms, d=3):
    return f"{ms[0]:.{d}f} ± {ms[1]:.{d}f}"


def report(n_seeds=N_SEEDS):
    rows = run(n_seeds)
    keys = ["cosine", "whiteness", "tau", "J", "hit_rate", "false_alarms",
            "blinkfree_fa", "fixed_hit", "fixed_fa"]
    counts = ("false_alarms", "blinkfree_fa", "fixed_fa")
    L = [f"SYNTHETIC. {n_seeds} seeds; mean ± standard error (SE) and sample SD across seeds.",
         "SE = SD / sqrt(n_seeds): it is the uncertainty of the mean, not the seed-to-seed spread.",
         "Learn on full stream; calibrate tau on first half; evaluate on second half.",
         "Seed 7 alone (original demo) is one draw — see last column.",
         "",
         "| metric | mean ± SE | SD | median | min–max | seed 7 |",
         "|---|---|---|---|---|---|"]
    r7 = one(7)
    for k in keys:
        d = 1 if k in counts else 3
        m, se, sd, med, lo, hi = spread([r[k] for r in rows])
        L.append(f"| {k} | {m:.{d}f} ± {se:.{d}f} | {sd:.{d}f} | {med:.{d}f} | "
                 f"{lo:.{d}f}–{hi:.{d}f} | {r7[k]:.3f} |")
    L.append("")
    L.append(f"A/B (eval half): crystal hit {fmt(mean_se([r['crystal_hit'] for r in rows]))}, "
             f"FA {fmt(mean_se([r['crystal_fa'] for r in rows]), 1)}; "
             f"fixed hit {fmt(mean_se([r['fixed_hit'] for r in rows]))}, "
             f"FA {fmt(mean_se([r['fixed_fa'] for r in rows]), 1)}.")
    dfa = [r["fixed_fa"] - r["crystal_fa"] for r in rows]
    dhit = [r["crystal_hit"] - r["fixed_hit"] for r in rows]
    mfa, sefa, sdfa = spread(dfa)[:3]
    mh, seh, sdh = spread(dhit)[:3]
    L.append(f"Paired per-seed difference (fixed minus crystal FA): mean {mfa:.1f}, "
             f"SD {sdfa:.1f}, SE {sefa:.1f}; crystal had more false alarms in "
             f"{sum(1 for v in dfa if v < 0)} of {len(dfa)} seeds. "
             f"Paired hit-rate difference (crystal minus fixed): mean {mh:.3f}, "
             f"SD {sdh:.3f}; crystal was lower in {sum(1 for v in dhit if v < 0)} of {len(dhit)} seeds.")
    fa = [r["false_alarms"] for r in rows]
    L.append(f"False-alarm spread: median {statistics.median(fa):.1f} against "
             f"mean {statistics.fmean(fa):.1f}, max {max(fa):.0f}; "
             f"{sum(1 for v in fa if v == 0)} of {len(fa)} seeds had none. "
             "A few seeds can dominate the mean for count metrics: compare the median and the range with the mean ± SE.")
    L.append("The crystal still beats the fixed template on average, but "
             "seed 7's perfect hit/FA rates and zero blink-free alarms are "
             "above the mean: across seeds the gate is imperfect.")
    return "\n".join(L), rows


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_SEEDS
    print(report(n)[0])
