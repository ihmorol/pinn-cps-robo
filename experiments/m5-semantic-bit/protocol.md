# Protocol — context-consistency detection of the reverse-light bit (locked before results)

**Question.** The reverse-light masquerade/fabrication classes evade kinematics because the patched frame is a dynamically consistent snapshot. Can the patched BIT still be caught from its live context — using ambient data only?

**Method.** Train a classifier on AMBIENT 0xd0 frames to predict the light bit s3 from the frame's other live signals (s1, s2, s4, s5, s6, s7) plus the wheel-speed state interpolated at the frame time (mean + std over a 50-frame window). Gradient Boosting, seeded. Detection score per frame: |s3_observed − P(s3=1)|. Threshold: ambient 99.9th percentile (no attack data in calibration).

**Evaluation.** The 12 reverse-light captures (6 masquerade + 6 fabrication), frame-level labels; ambient held-out for FPR. Also applied to the coolant fabrication capture as a diagnostic for its unresolved 255/255 anomaly (with the ambient-family 0x4e7 mapping as an alternative decode).

**Predictions.**
- P7: if the light bit is context-predictable on ambient (ambient AP of the predictor > 0.9 when predicting s3 from held-out context), then the patched frames violate context-consistency and are detected (AP > 0.9, recall > 0.5 at the operating point).
- P8: if ambient AP ≤ 0.9, the bit is not context-determined and the class remains genuinely open to ambient-only methods — reported as-is.

**Scope.** Learned-context detector — this is a D0-family (data-driven) method by our taxonomy, not physics. Its role in the paper: close the open class and sharpen the boundary statement (physics misses it; benign-data context learning catches it).
