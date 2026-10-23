"""Pytest suite for crystal-bci (converted from the custom runner)."""

import math
import random
import statistics

import pytest

from crystal_bci import (blink_waveform, calibrate_tau, cosine, crystal_template,
                         CrystalLearner, evaluate, residue_whiteness,
                         synth_stream, youden_threshold)
import sweep

C, L, T, TOL = 4, 24, 20000, 12


@pytest.fixture(scope="module")
def learned():
    rng = random.Random(7)
    s, peaks, b = synth_stream(T, C, 400, 0.35, 0.15, rng)
    cl = CrystalLearner(C, L)
    cl.observe(s, C, L, thresh=1.5)
    return s, peaks, b, cl, crystal_template(cl)


def test_waveform_biphasic():
    w = blink_waveform()
    assert abs(sum(w)) < 1e-9
    assert max(w) > 0.5 and min(w) < -0.5


def test_crystal_recovers_direction_unsupervised(learned):
    _, _, b, _, crystal = learned
    w = blink_waveform(L)
    true = [w[i] * b[c] for i in range(L) for c in range(C)]
    n = math.sqrt(sum(x * x for x in true))
    true = [x / n for x in true]
    assert cosine(crystal, true) > 0.6


def test_residue_whiteness_in_unit_interval(learned):
    _, _, _, cl, crystal = learned
    rw = residue_whiteness(cl.covariance(), 1, [crystal])
    assert 0.0 <= rw <= 1.0


def test_gate_separates(learned):
    s, peaks, _, _, crystal = learned
    H = T // 2
    tau, J = calibrate_tau(s[:H], [p for p in peaks if p < H], crystal, C, L, TOL)
    assert J > 0.5 and 0.0 <= tau <= 1.0


def test_frozen_gate_on_seed7_eval(learned):
    s, peaks, _, _, crystal = learned
    H = T // 2
    s1, s2 = s[:H], s[H:]
    p1 = [p for p in peaks if p < H]
    p2 = [p - H for p in peaks if p >= H]
    tau, _ = calibrate_tau(s1, p1, crystal, C, L, TOL)
    hr, fa = evaluate(s2, p2, crystal, tau, C, L, TOL)
    assert hr == 1.0 and fa == 0


def test_blink_free_control_seed7_style(learned):
    s, peaks, _, _, crystal = learned
    H = T // 2
    tau, _ = calibrate_tau(s[:H], [p for p in peaks if p < H], crystal, C, L, TOL)
    s0, _, _ = synth_stream(12000, C, 400, 0.35, 0.15, random.Random(99),
                            blinks=False)
    _, fa0 = evaluate(s0, [], crystal, tau, C, L, TOL)
    assert fa0 == 0


def test_deterministic_crystal():
    def learn(seed):
        rng = random.Random(seed)
        s, _, _ = synth_stream(T, C, 400, 0.35, 0.15, rng)
        cl = CrystalLearner(C, L)
        cl.observe(s, C, L, thresh=1.5)
        return crystal_template(cl)
    assert cosine(learn(7), learn(7)) > 0.9999


def test_youden_rejects_empty():
    with pytest.raises(ValueError):
        youden_threshold([])


def test_sweep_mean_se_and_seed7_draw():
    rows = sweep.run(n_seeds=5)
    m, se = sweep.mean_se([r["hit_rate"] for r in rows])
    assert 0.5 <= m <= 1.0 and se >= 0.0
    r7 = sweep.one(7)
    assert r7["hit_rate"] == 1.0 and r7["false_alarms"] == 0


def test_sweep_crystal_beats_fixed_on_average():
    rows = sweep.run(n_seeds=5)
    assert statistics.fmean([r["crystal_hit"] for r in rows]) >=         statistics.fmean([r["fixed_hit"] for r in rows]) - 0.05
    assert statistics.fmean([r["crystal_fa"] for r in rows]) <         statistics.fmean([r["fixed_fa"] for r in rows])


def test_sweep_report_labelled():
    text, _ = sweep.report(n_seeds=2)
    assert text.startswith("SYNTHETIC")
    assert "validated" not in text.lower()
