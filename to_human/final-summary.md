# Final summary — autonomous research phase complete (2026-11-03)

## What was accomplished end-to-end

**Research question:** where does physics pay in detecting CAN masquerade attacks — the hardest attack class on the standard public benchmark (ROAD, Oak Ridge National Laboratory)?

**Answers, all backed by pre-registered protocols and committed code:**

1. **Physics taxonomy (M2/M2b):** every masquerade AND fabrication class in ROAD violates at least one physical-consistency law — wheel-speed classes break inter-wheel consistency and continuity (178–1273× the benign envelope), speedometer classes break the display–wheel relation (~165×) and value envelope, coolant exceeds its envelope. ROAD's advertised "most stealthy fabrication" is not stealthy to physics.
2. **Detector ladder (M3):** kinematic residuals detect 3 of 4 classes at recall 1.0 with a 0.1% ambient false-positive rate — using **zero attack data**. Supervised ML ties this when attack captures are available. The constancy baseline is provably dead (ambient stationary runs of 106k frames).
3. **Boundary finding:** the reverse-light class is a live-patched, dynamically consistent snapshot. It evades kinematics, learned context (AP 0.09 predictor), and supervised ML (0.37/0.63) — closing it requires the real gear encoding, which ROAD's anonymization hides.
4. **Attribution (M4):** a physics-informed forecaster never beats an equal-capacity physics-free twin across four data regimes and three loss weights — a rigorous negative result reproducing the Grossmann/Krishnapriyan lesson in automotive security. The physics value is analytical, not learned.
5. **Dataset contribution:** ROAD's shipped DBC cannot decode the dataset's own published CSVs (per-family bit layouts differ). We built an empirical layout solver validated by exact reproduction.

## Deliverables

- `paper/latex/main.pdf` — compiled 5-page workshop paper (draft v1)
- `paper/drafts/paper-v1.md` — markdown draft
- `literature/literature.csv` — 68-entry verified reference tracker
- `findings.md` / `research-log.md` / `research-state.yaml` — complete research memory
- `experiments/` — 6 pre-registered experiments with results, including every failure
- Repository: https://github.com/ihmorol/pinn-cps-robo (all work committed)

## What I need from you (4 decisions, 2 minutes)

1. **Title** — keep "The Wheels Tell the Truth: What Kinematic Residuals Can (and Cannot) Detect in CAN Masquerade Attacks"?
2. **Framing** — measurement paper (current), or re-weight toward a method contribution?
3. **Venue** — NDSS AutoSec or USENIX VehicleSec workshop (recommended), or journal?
4. **Limitations (§7)** — anything to add or soften?

Answer these and the venue conversion + submission prep is the remaining work. The automation is paused; say "resume loop" any time to restart it.

## Two flagged items

- Your `docs/faculty-proposal.md` was briefly pushed to the public repo by my over-broad `git add -A`; it's removed and gitignored now, but it remains in git history (say "scrub history" if you want it gone entirely).
- Optional future experiments are listed in `research-state.yaml` (multi-step forecaster, hard-constraint PINN, ROS 2 cross-domain validation) — none blocking.
