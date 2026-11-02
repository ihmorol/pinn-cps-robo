# Protocol — M2 physics taxonomy (locked before results)

**Question (RQ1/H1):** which physics-consistency law does each ROAD attack class violate, and only inside its injection interval?

**Data:** the 17 pre-decoded attack captures (13 masquerade + 4 accelerator, no-injection) + ambient captures for envelope fitting. Fabrication (non-masquerade) variants are raw-only — excluded here, noted as limitation.

**Method:** per capture, per physics law, compare max residual inside the labeled attack window vs the benign part of the same capture:
- L1 inter-wheel: max pairwise |w_i − w_j| (0x6e0)
- L2 speedo↔wheel relation: |speedo − α·mean(wheel)| with α fit on ambient_dyno_drive_basic_long (fit_scale)
- L3 wheel continuity: max |Δwheel| between consecutive 0x6e0 frames
- L4 coolant freeze/jump: max |Δcoolant| (0x4e7)

**Prediction:** inside/outside ratio ≫ 1 for L1/L2 on wheel-speed and speedometer masquerades; accelerator captures (no injection) show ratio ≈ 1 on all laws — if they don't, our envelope definitions are wrong.

**Metric:** per-capture table `results/taxonomy.csv` (class, law, inside_max, outside_max, ratio). CONFIRMATORY for H1.
