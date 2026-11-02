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

## Open questions

- Exact scaling of wheel-speed/speedometer/coolant signals under ROAD's obfuscation (identify from ambient data).
- Do the four wheel-speed values in the masquerade payload stay *mutually* consistent (correlated) while violating continuity/plausibility vs the speedometer? — this is H1's core empirical question (M2).
