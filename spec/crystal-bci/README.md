# crystal-bci

What membrane-crystallization taught, applied to biosignal commands:
a peak-triggered Hebbian learner extracts the blink template
("the crystal") from a noisy synthetic multichannel stream —
unsupervised — then a Youden-calibrated, fail-closed gate turns
blinks into a `next` command, or stays silent.

## The one-paragraph version

The crystallization build showed that Hebbian learning recovers
structure while the residue whitens. Applied to event detection,
that needed a correction: the template lives in the **first**
moment (the spike-triggered average), because every blink shares
nearly the same shape — the covariance around the mean carries
almost nothing about it (measured: 2% of variance). So the
crystal is the learned mean, the covariance describes what is
left, and a frozen gate decides. The learned crystal beats a fixed
canonical template 1.000/0 false alarms vs 0.765/114, because it
learned the mixing direction from the data instead of assuming it.

## Run it

```bash
python demo.py    # the full story, ~2 seconds
python tests.py   # 9 tests
```

## Measured (seed 7)

| thing | value |
|---|---|
| cosine(crystal, true blink direction), unsupervised | 0.784 |
| residue whiteness | 0.279 |
| gate tau / Youden's J | 0.522 / 0.667 |
| fresh stream: hit rate | 1.000 (17/17) |
| fresh stream: false alarms | 0 |
| blink-free 12000 ticks: false alarms | 0 |
| A/B vs fixed template (hit / FA) | 1.000 / 0 vs 0.765 / 114 |

## Honest limits

- **Synthetic signals only.** No human, no headset, no electrodes.
- **Not a medical device.** Not a diagnostic or treatment aid.
- **The device-data adapter is still missing.** This is the
  learn-and-gate half of a future pipeline; the half that reads
  real EOG recordings does not exist here.
- One command class (`next`). See DESIGN.md for the full story,
  including four designs falsified along the way.

## Files

- `crystal_bci.py` — stream synthesis, learner, crystal, gate
- `demo.py` — the full measured story
- `tests.py` — 9 tests
- `DESIGN.md` — decisions, measurements, falsified designs

Stdlib only. Seeded and reproducible. AGPL-3.0-only.
