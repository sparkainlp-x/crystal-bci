# crystal-bci

What [membrane-crystallization](https://github.com/sparkainlp-x/membrane-crystallization) taught, applied to biosignal commands: a peak-triggered Hebbian learner extracts a blink template ("the crystal") from a noisy **synthetic** multichannel stream — unsupervised — then a Youden-calibrated, fail-closed gate turns blinks into a `next` command, or stays silent.

**SYNTHETIC signals only. Not a medical device. Not evaluated on human recordings.** The device-data adapter that would read real EOG (or similar) does not exist in this repo.

## The one-paragraph version

The crystallization build showed that Hebbian learning recovers structure while the residue is measured. Applied to event detection, that needed a correction: the template lives in the **first** moment (the spike-triggered average), because every blink shares nearly the same shape — the covariance around the mean carries almost nothing about it (measured on the generator: about 2% of variance along the true blink direction). So the crystal is the learned mean, the covariance describes what is left, and a frozen gate decides. Blinks in the generator are **salient** (amp 1.8–2.4); a buried-blink design was falsified and rejected (see DESIGN.md).

## Quick start

```bash
python demo.py          # one seed (seed 7), ~1 s
python sweep.py         # 20 seeds, mean ± SE (~12 s); writes the table below
pip install -r requirements-dev.txt && python -m pytest -q   # 11 tests, warnings are errors
```

## Measured in this repo

**Multi-seed (20 seeds; mean ± standard error).** Learn on a full stream, calibrate tau on the first half, evaluate on the second half. Seed 7 alone is the original demo draw — reported for comparison, not as the distribution.

| metric | mean ± SE (20 seeds) | seed 7 alone |
|---|---|---|
| cosine(crystal, true blink direction) | 0.665 ± 0.033 | 0.784 |
| residue whiteness | 0.296 ± 0.004 | 0.279 |
| gate tau / Youden's J | 0.398 ± 0.036 / 0.719 ± 0.021 | 0.522 / 0.667 |
| eval hit rate | 0.961 ± 0.011 | 1.000 |
| eval false alarms | 18.6 ± 10.9 | 0 |
| blink-free control false alarms (12000 ticks) | 24.0 ± 13.3 | 0 |
| fixed-template hit / FA (A/B) | 0.878 ± 0.029 / 86.5 ± 24.5 | 0.765 / 114 |

**Honest reading.** The learned crystal still beats a fixed canonical template on average (higher hit rate, fewer false alarms). Seed 7's perfect hit/FA rates and zero blink-free alarms are **above the mean**: across seeds the frozen gate is imperfect, and fail-closed silence on blink-free streams is not guaranteed for every seed. Full table: [results_sweep.md](results_sweep.md).

## Related repositories

- [membrane-crystallization](https://github.com/sparkainlp-x/membrane-crystallization) — streaming Hebbian covariance / residue-whiteness measurements this pipeline draws on.
- [bci-membrane-latch](https://github.com/sparkainlp-x/bci-membrane-latch) — related BCI / latch direction (multi-command scoping).

## Honest limits

- **Synthetic signals only.** Biphasic pulses + white noise + drift are not physiology. No human, no headset, no electrodes.
- **Not a medical device.** Not a diagnostic or treatment aid.
- **The device-data adapter is still missing.** This is the learn-and-gate half of a future pipeline; the half that reads real recordings does not exist here.
- One command class (`next`). Multi-command is future work.
- Residue whiteness ~0.30: leftover structure remains (noise-triggered windows). An adaptive trigger is the next experiment, not claimed here.
- Classical simulation, stdlib only, seeded.

See [DESIGN.md](DESIGN.md) for decisions and four designs falsified along the way.

## Provenance

The package as received is kept unchanged in [spec/crystal-bci/](spec/crystal-bci/). [CHANGELOG.md](CHANGELOG.md) lists what changed.

## Acknowledgements

Builds on [membrane-crystallization](https://github.com/sparkainlp-x/membrane-crystallization). Thanks to Mun Seok Lee, who is credited on that related package. The acknowledgement does not imply his endorsement of this code or its conclusions.

## How to cite

See [CITATION.cff](CITATION.cff).

## License

Copyright (c) 2026 Jean-François Brisson, Spark AI NLP.

This software is available under the GNU Affero General Public License v3.0 only (AGPL-3.0-only); see [LICENSE](LICENSE).
