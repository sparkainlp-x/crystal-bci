# crystal-bci — DESIGN.md

## What crystallization taught

The membrane-crystallization build ended with two measurement-driven
findings:

1. **Hebbian learning recovers the subspace, not the basis.**
2. **What optimizes is the residue** — structure extracted, white
   noise left.

Applying that machinery to biosignal commands forced a correction
to finding 1, and the correction is the interesting part:

**For event detection, the template lives in the first moment, not
the second.** Every blink window shares nearly the same shape, so
their mean carries the template while the covariance around that
mean carries almost nothing about it (measured: the true blink
direction held 2% of the covariance's variance — the rest was
noise). The covariance's honest job is characterizing what is
LEFT: the residue. So the crystal here is the spike-triggered
average (mean of peak-triggered windows), and the residue-whiteness
metric from membrane-crystallization still applies to what remains.

## Pipeline

```
synthetic multichannel stream (blink + noise + drift)
  -> energy trigger -> peak alignment -> centered windows
  -> crystal = mean window, normalized        (unsupervised)
  -> residue whiteness of covariance          (what is left)
  -> statistic = normalized correlation with crystal
  -> tau from Youden's J on candidates, then FROZEN
  -> event-level detection (local maxima >= tau)
  -> blink -> "next" command, else silence     (fail-closed)
```

## Design decisions

- **Peak alignment, not threshold-crossing alignment.** The first
  version aligned windows to the threshold crossing and the mean
  washed out (cosine 0.105). Real spike-sorting aligns to the peak;
  doing so raised cosine to 0.784. Documented, not hidden.
- **Per-channel baseline removal** on every window. Without it the
  crystal learned the slow drift common-mode instead of the blink
  (cosine 0.005) — the simulation's own lesson about preprocessing.
- **Salient events.** The first attempt buried blinks in the noise
  floor (mean peak energy 1.0 vs noise p99 1.32) and nothing
  unsupervised could work — correctly so. Real EOG blinks tower
  over background EEG; the generator matches that (amp 1.8–2.4).
- **Event-level scoring**, not window-level. Stride-grid windows
  misalign with events; scoring local maxima of the statistic
  trace against true peaks (±12 ticks) is how real detectors are
  scored.
- **Fail-closed gate.** Below tau: silence, no command. Verified
  on a blink-free control stream: 0 false alarms over 12000 ticks.

## Measured results (seed 7)

- cosine(crystal, true blink direction) = 0.784, unsupervised
- residue whiteness = 0.279 (residual still structured — reported,
  not polished away)
- gate: tau = 0.522, Youden's J = 0.667 (calibration) / 0.625 (A/B)
- fresh stream: hit rate 1.000, 0 false alarms (17 blinks)
- A/B: learned crystal (hit 1.000, FA 0) vs fixed canonical
  template (hit 0.765, FA 114) — the crystal wins because it
  learned the mixing direction from the data instead of assuming it

## Honest limits

- **Synthetic signals only.** Biphasic pulses + white noise + drift
  are not physiology. No human, no headset, no electrodes.
- **Not a medical device.** Not a diagnostic, not a treatment
  aid. A learning-and-gating simulation.
- **The device-data adapter is still missing.** This is the half
  of a future pipeline that learns and gates; the half that reads
  real recordings (e.g. NeuroViu-class EOG) does not exist here.
- One command class ("next" on blink). Multi-command
  (yes/no/next/help) is future work, and the bci-membrane-latch
  repo already scopes that direction.
- Residue whiteness 0.279: the extracted crystal is good, the
  leftover is not white — the noise-triggered windows pollute it.
  A better trigger (adaptive threshold) would be the next experiment.
- Classical simulation throughout, stdlib only, seeded.

## Falsified along the way

1. Covariance-top-eigenvector as the crystal — wrong moment for
   event templates (2% variance along truth).
2. Threshold-crossing window alignment — washes out the mean.
3. No baseline removal — learns drift, not blinks.
4. Sub-threshold blink salience — correctly unlearnable; fixed by
   matching real EOG blink/background ratios, not by tuning the
   learner.
