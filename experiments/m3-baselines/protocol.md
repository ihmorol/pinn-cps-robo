# Protocol — M3 detector ladder, stage 1 (locked before results)

**Question (RQ2/H2):** do physics-residual detectors detect ROAD masquerade classes at frame level with low false-positive rates, versus classical statistical baselines?

**Data.** Attacked-ID streams of the 13 masquerade captures (0x6e0 for correlated; 0xd0 for speedometer + reverse-light; 0x4e7 for coolant), frame-level labels as published; benign = all frames of the 12 ambient captures (C-C) + label-0 frames of attack captures.

**Threshold discipline.** All detector thresholds/floors are computed from AMBIENT captures only. No attack data touches calibration. Capture-disjoint supervised splits come in stage 2.

**Detectors (per-frame score, higher = more anomalous):**
- **D0a range**: sum of per-signal exceedance beyond ambient [min, max] envelope.
- **D0b const-run**: current run length of frame-identical values on the attacked signal, normalized by the ambient max run length.
- **D1 physics**: max over applicable laws of residual / ambient floor — wheel stream: L1 inter-wheel, L3 continuity; speedo stream: L2 speedo↔wheel relation (wheel interp onto speedo grid), L7 freeze violation (ambient-quantile std envelope); coolant stream: L4 jump, L6 value-envelope exceedance.

**Metrics.** Per attack class: average precision (AUC-PR); recall at the operating threshold = ambient 99.9th percentile of the detector's score; FPR on ambient at that threshold (should be ≈0.1 % by construction; ties reported honestly).

**Prediction (H2, falsifiable).** D1 ≥ D0a/D0b on every class in AP; D0a fails on reverse-light masquerade (value-plausible payload) while D1 catches it via freeze. If D0a catches reverse-light, the "value-plausible" claim in findings.md is wrong and must be revised.

**Stages.** Stage 1 (this run): D0a/D0b/D1. Stage 2: D4 RF/XGBoost + D5 AE (capture-disjoint supervised splits). Stage 3 (M4): D2 PINN, D3 physics-free twin.
