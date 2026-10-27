# Changelog

## 0.1.0 (unreleased)

- First commit: the package exactly as received (`spec/crystal-bci/`).
- Authorship: Jean-François Brisson (ORCID + affiliation). Mun Seok Lee acknowledged for the related membrane-crystallization lineage only.
- Converted the custom `tests.py` runner to a real pytest suite (now 12 tests, warnings are errors).
- Added a 20-seed sweep (`sweep.py`, `results_sweep.md`) with mean ± SE; README and DESIGN now lead with the distribution, and treat seed 7 as one draw.
- Wording: "Verified" → measured language; "not validated on any human" → "not evaluated on human recordings".
- Sweep report now also gives SD, median and min–max per metric, labels the ± as standard error, and adds paired per-seed differences and a heavy-tail note for false alarms (wording and reporting only; the simulation, learner and gate are unchanged and every mean ± SE is identical). `results_sweep.md` is the output of `python sweep.py`.
- SYNTHETIC / not a medical device / device-data adapter missing kept front and center; buried-blink falsification noted.
- Related-repos note linking membrane-crystallization and bci-membrane-latch.
- CI on Python 3.10 to 3.13; CITATION.cff and .zenodo.json with spark-ai-nlp community.
