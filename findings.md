# Findings — running synthesis

## Current understanding (2026-11-03)

- ROAD ships an `anonymized.dbc` (105 IDs, signals named `Unknown_N` with bit layouts only) — semantics must be recovered empirically.
- The attack metadata (`signal_extractions/attacks/metadata.json`) leaks the semantics directly: injection IDs identify `0x6e0` = four wheel speeds, `0xd0` = speedometer + reverse light, `0x4e7` = coolant temp. Injection intervals give exact ground-truth windows.
- All 13 masquerade captures are pre-decoded with per-row labels — no raw-log decoding needed for the core experiment.
- Masquerade injection payloads are *constant* values (e.g., `595945450000FFFF` on 0x6e0) held for the whole interval — the attack replaces a *varying* signal with a frozen/fabricated one.

## Lessons and constraints

- ROAD frame order is obfuscated: timing features are unreliable by dataset design; value-based physics is the load-bearing signal.
- Zenodo download ≈ 300 KB/s; use background curl with resume (`-C -`).
- Publisher PDFs must not go into the public git repo (copyright) — `docs/papers/README.md` carries links instead.
- Subagent calls can fail with "Model request failed" under concurrency — retry, or run serially.

## M1-CAN results (2026-11-03, scripts/inspect_road.py)

- ID map empirically verified. Ambient (basic_long, 1251 s): 0x6e0 four channels mean 3691.9/3679.3/3696.0/3694.8, pairwise |diff| mean ~13, max ~111 (≈1.5 % of signal) → tight inter-wheel envelope exists.
- Correlated wheel-speed masquerade (0x6e0): payload frozen constant for the whole interval (n=2086, zero variance); values 6489/1349/0/16383 — inter-wheel residual explodes from ≈13 to ≈16,383 (~1200×). **H1 preliminary: supported for wheel-speed masquerades.**
- Speedometer masquerade (0xd0): sig6 = speedometer, frozen at 16128–16383 (max) inside interval vs benign 0–1391. sig1 (0–15) = gear candidate; sig3 (0/1) = reverse-light candidate (verify M2).
- Per-row Label column aligns exactly with published injection intervals (inside={1}, outside={0}) → ground truth exact.
- Implication: ROAD's masquerade payloads violate inter-signal consistency grossly, not subtly — the interesting question shifts to the fabrication variants ("flam", mutually consistent values) and to FP behavior on benign maneuvers.

## M2-CAN results (2026-11-03, experiments/m2-physics-taxonomy/)

Physics taxonomy of the 13 masquerade captures (inside/outside max-residual ratios; benign floors from the same captures' benign parts):

| Attack class (n) | L1 inter-wheel | L2 speedo↔wheel | L3 continuity | L5/L6 value envelope | L7 freeze (inv) |
|---|---|---|---|---|---|
| wheel-speed masquerade (3) | **178–585×** | 84–659× | **258–1024×** | — | — |
| speedometer masquerade (3) | — | **~165×** | — | 1.31× (mild) | 6.3–10.6× |
| reverse-light masquerade (6) | — | — | — | — (value-plausible!) | **9.9–42.8×** |
| coolant masquerade (1) | — | — | — | **1.69×** (255 vs ambient 151) | — |

- **H1 CONFIRMED (masquerade classes): every class violates ≥1 physics law inside its interval only; benign parts respect all laws.** Benign noise floors: L1 ≤112, L2 ≤94, L3 ≤62.
- Crown jewel: reverse-light masquerades are value-plausible AND frequency-identical — caught only by the freeze/dynamics law (speedo frozen while wheels move). This is the "physics sees what statistics cannot" headline.
- Accelerator captures (4): no injection, all labels 0 → C-C benign-stress material for M3.
- Fabrication (non-masquerade) variants remain raw-only — decode in M3 if time; noted limitation.

## Lessons (experiment refinements — logged in results)

- Only the attacked ID's rows carry Label=1 → attack intervals must be derived globally (any-ID label-1 rows) and splits done by TIME (±0.05 s margin).
- One boundary frame per interval end carries payload with Label=0 → time-split with margin absorbs it; envelope laws should compare vs AMBIENT envelope, not within-capture outside.
- L2 relation noise floor ~90 units comes from interpolation misalignment between 0x6e0 and 0xd0 grids → M3 must use frame-aware alignment (or evaluate L2 on the speedo's own grid).

## M3 stage 1 results (2026-11-03, experiments/m3-baselines/)

Frame-level, ambient-only calibration (q0.999 per stream), 1.05M wheel / 0.99M speedo / 99k coolant benign frames:

| Class | D0a range AP/rec | D0b const-run | D1 physics AP/rec |
|---|---|---|---|
| wheel masquerade (3) | 0.999 / 1.00 | AP 0.995, rec 0 | 0.999 / 1.00 |
| speedometer masquerade (3) | 0.9995 / 1.00 | AP 0.42, rec 0 | 0.995 / 1.00 |
| coolant masquerade (1) | 1.00 / 1.00 | AP 0.10, rec 0 | 0.966 / 1.00 |
| **reverse-light masquerade (6)** | **0.49 / 0.00** | **0.34 / 0.00** | **0.44 / 0.00** |

- D0b (const-run) is dead on ROAD: ambient stationary periods give runs up to 106k frames → neutralized. Honest baseline failure.
- **Reverse-light masquerade evades every current detector — genuine boundary finding.** Failure analysis: the injector live-patches the light bit (counter keeps rolling), the window is short and the motion steady, so the patched frame is a *dynamically consistent snapshot* — kinematics cannot flag it. Gear↔light law untestable: the gear signal is not identifiable from the anonymized DBC (s1=counter, s4 not cleanly gear; naive law fails 48.6% on ambient).
- Implication for the paper: physics catches 3/4 masquerade classes; the state-bit class needs actuator-model semantics (real DBC) or other channels — the honest scope line.
- D0a ≈ D1 on the 3 payload-exceeding classes (both catch the out-of-envelope values); the physics-vs-data question moves to stage 2 (RF/XGB/AE, capture-disjoint) and M4 (FP behavior on benign stress).

## Lessons (M3 failures → fixes, all logged in git history)

1. Ambient reference must be computed WITHIN each capture (t restarts per capture; merged-sort interleaves them → floor_L3 inflated 758→10765 by cross-capture jumps).
2. Binary freeze law failed: ambient idling legitimately freezes the display (std_q=0) → replaced by L2d dynamics law |Δs6 − α·Δwm| (floor 276).
3. Only the attacked ID's rows carry Label=1; one boundary frame per interval carries payload with Label=0 → time-split with ±0.05s margin.
4. Publisher ships duplicate CSVs of attack captures inside ambient/ → calibration filtered to the 12 canonical ambient_* files.

## Open questions

- Exact scaling of wheel-speed/speedometer/coolant signals under ROAD's obfuscation (identify from ambient data).
- Do the four wheel-speed values in the masquerade payload stay *mutually* consistent (correlated) while violating continuity/plausibility vs the speedometer? — this is H1's core empirical question (M2).
