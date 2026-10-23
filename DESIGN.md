# crystal-bci — design notes

SYNTHETIC. Classical simulation only. Not a medical device. Not evaluated on human recordings.

## What crystallization taught

The membrane-crystallization build ended with two measurement-driven findings:

1. Hebbian learning recovers the subspace, not the basis.
2. What is measured as "complete" is the residue — structure extracted, leftover spectrum checked.

Applying that machinery to biosignal commands forced a correction to finding 1:

**For event detection, the template lives in the first moment, not the second.** Every blink window shares nearly the same shape, so their mean carries the template while the covariance around that mean carries almost nothing about it (measured: the true blink direction held about 2% of the covariance's variance). The covariance's honest job is characterizing what is LEFT. So the crystal here is the spike-triggered average (mean of peak-triggered windows), and the residue-whiteness metric still applies to what remains.

## Pipeline

```
synthetic multichannel stream (blink + noise + drift)
  -> energy trigger -> peak alignment -> centered windows
  -> crystal = mean window, normalized        (unsupervised)
  -> residue whiteness of covariance          (what is left)
  -> statistic = normalized correlation with crystal
  -> tau from Youden's J on candidates, then FROZEN
  -> event-level detection (local maxima >= tau)
  -> blink -> "next" command, else silence     (fail-closed intent)
```

## Design decisions

- **Peak alignment, not threshold-crossing alignment.** Threshold-crossing alignment washed out the mean (cosine 0.105). Aligning to the peak raised cosine to ~0.78 on seed 7.
- **Per-channel baseline removal** on every window. Without it the crystal learned slow drift (cosine ~0.005).
- **Salient events.** Burying blinks in the noise floor made unsupervised learning fail — correctly. Real EOG blinks tower over background; the generator matches that (amp 1.8–2.4). The buried-blink case was falsified and rejected, not tuned around.
- **Event-level scoring**, not window-level.
- **Fail-closed gate intent.** Below tau: silence. On seed 7's blink-free control: 0 false alarms. Across 20 seeds the blink-free FA mean is 24 ± 13 — the gate is not silently perfect for every seed.

## Measured (20 seeds; see results_sweep.md)

| metric | mean ± SE | seed 7 |
|---|---|---|
| cosine | 0.665 ± 0.033 | 0.784 |
| hit rate | 0.961 ± 0.011 | 1.000 |
| false alarms | 18.6 ± 10.9 | 0 |
| blink-free FA | 24.0 ± 13.3 | 0 |
| fixed-template hit / FA | 0.878 / 86.5 | 0.765 / 114 |

Seed 7 alone overstates the gate's reliability. The crystal still beats the fixed template on average.

## Honest limits

- Synthetic only; not a medical device; device-data adapter missing.
- One command class. See [bci-membrane-latch](https://github.com/sparkainlp-x/bci-membrane-latch) for related multi-command scoping.
- Residue whiteness ~0.30: leftover structure remains.
- Stdlib only, seeded.

## Falsified along the way

1. Covariance top eigenvector as the crystal — wrong moment for event templates (~2% variance along truth).
2. Threshold-crossing window alignment — washes out the mean.
3. No baseline removal — learns drift, not blinks.
4. Sub-threshold blink salience — correctly unlearnable; fixed by matching real EOG blink/background ratios, not by tuning the learner.
