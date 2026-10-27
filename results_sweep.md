SYNTHETIC. 20 seeds; mean ± standard error (SE) and sample SD across seeds.
SE = SD / sqrt(n_seeds): it is the uncertainty of the mean, not the seed-to-seed spread.
Learn on full stream; calibrate tau on first half; evaluate on second half.
Seed 7 alone (original demo) is one draw — see last column.

| metric | mean ± SE | SD | median | min–max | seed 7 |
|---|---|---|---|---|---|
| cosine | 0.665 ± 0.033 | 0.149 | 0.682 | 0.278–0.892 | 0.784 |
| whiteness | 0.296 ± 0.004 | 0.017 | 0.293 | 0.275–0.322 | 0.279 |
| tau | 0.398 ± 0.036 | 0.162 | 0.403 | 0.136–0.626 | 0.522 |
| J | 0.719 ± 0.021 | 0.092 | 0.714 | 0.496–0.930 | 0.667 |
| hit_rate | 0.961 ± 0.011 | 0.050 | 1.000 | 0.882–1.000 | 1.000 |
| false_alarms | 18.6 ± 10.9 | 48.6 | 1.5 | 0.0–218.0 | 0.000 |
| blinkfree_fa | 24.0 ± 13.3 | 59.5 | 0.5 | 0.0–267.0 | 0.000 |
| fixed_hit | 0.878 ± 0.029 | 0.128 | 0.913 | 0.500–1.000 | 0.765 |
| fixed_fa | 86.5 ± 24.5 | 109.6 | 47.0 | 0.0–400.0 | 114.000 |

A/B (eval half): crystal hit 0.961 ± 0.011, FA 18.6 ± 10.9; fixed hit 0.878 ± 0.029, FA 86.5 ± 24.5.
Paired per-seed difference (fixed minus crystal FA): mean 67.9, SD 128.1, SE 28.6; crystal had more false alarms in 2 of 20 seeds. Paired hit-rate difference (crystal minus fixed): mean 0.083, SD 0.155; crystal was lower in 4 of 20 seeds.
False-alarm spread: median 1.5 against mean 18.6, max 218; 10 of 20 seeds had none. A few seeds can dominate the mean for count metrics: compare the median and the range with the mean ± SE.
The crystal still beats the fixed template on average, but seed 7's perfect hit/FA rates and zero blink-free alarms are above the mean: across seeds the gate is imperfect.
