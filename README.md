# pinn-cps-robo

**Physics-Residual Detection of Masquerade Attacks on Controller Area Networks — a Physics-vs-Data Attribution Study on the ROAD Dataset**

Research project: vehicle-kinematics consistency residuals (four wheel speeds vs speedometer vs temporal continuity), embedded analytically and as physics-informed neural network (PINN) constraints, as the detection signal for CAN-bus masquerade/fabrication attacks — benchmarked against Random Forest, XGBoost, and Autoencoder baselines with a strict ablation ladder that attributes any gain to *physics* rather than model capacity.

**Why this matters:** masquerade attacks preserve message frequencies and per-signal plausibility — the dataset's own authors state frequency-based approaches "will almost certainly fail" against them [1] — yet no published detector on the public ROAD dataset encodes the vehicle's physical consistency laws, and no CAN IDS paper runs a physics-vs-data attribution ablation.

**Primary dataset:** [ROAD — Real ORNL Automotive Dynamometer CAN Intrusion Dataset](https://zenodo.org/records/10462796) (Oak Ridge National Laboratory, CC-BY-4.0): 33 physically verified attack captures (incl. 13 masquerade) + 12 ambient captures, with pre-decoded signal time series (four wheel speeds, speedometer, coolant temperature) and per-row labels.

[1] Verma et al., "A comprehensive guide to CAN IDS data and introduction of the ROAD dataset," PLOS ONE 19(1), 2024.

## Documentation

| Document | Contents |
|---|---|
| [docs/research-plan.md](docs/research-plan.md) | Frozen RQs/hypotheses, vehicle physics model, detector ladder, evaluation conditions, milestones M1-CAN…M5-CAN, risks |
| [docs/literature-review.md](docs/literature-review.md) | Working survey (~50 verified references): masquerade detection state of the art, physics-based detection lineage + PINN evidence/critics, dataset and evaluation norms |
| [docs/dataset-assessment.md](docs/dataset-assessment.md) | ROAD verified metadata, attack classes, caveats (timing obfuscation, simulated masquerades), M1-CAN inspection checklist |
| [docs/domain-decision.md](docs/domain-decision.md) | The 2026-11-03 domain decision: why CAN/ROAD over ROS 2 robotics and ICS, with the verified gap analysis |
| docs/papers/ | Key papers read in full (AutoHack, CAN-MIRGU, can-sleuth) |

## Repository layout

```
docs/                 research plan, working survey, dataset assessment, domain decision, papers
scripts/              standalone tools (CAN signal inspector — to come in M1-CAN)
src/pinn_cps_robo/    library code (data pipeline, physics models, detectors, evaluation)
experiments/          experiment configs and runners
data/
  raw/                untrusted downloads (quarantined, not in git) — ROAD goes here
  processed/          generated feature panels (not in git)
models/               trained model artifacts (not in git)
reports/              generated figures, metric tables
```

## Status (2026-11-03)

**Autonomous research phase complete.** All milestones executed with pre-registered protocols:

- **M1** — ROAD decoded; signal map recovered (0x6e0 = 4×wheel speeds, 0xd0 = speedometer/reverse-light, 0x4e7 = coolant) despite the shipped DBC not matching the published CSVs.
- **M2/M2b** — physics taxonomy of all 26 injection captures: every class except reverse-light violates ≥1 consistency law (ratios 178–1273×).
- **M3** — detector ladder: physics + range statistics catch 3/4 classes (recall 1.0, 0.1% ambient FPR, **detection within one CAN frame**); reverse-light evades all.
- **M4** — PINN vs physics-free twin: parity across 4 data regimes and 3 loss weights (honest negative attribution).
- **M5** — paper compiled: [paper/latex/main.pdf](paper/latex/main.pdf) (5 pp), draft v1, figures.

Python ≥ 3.10; CPU-only. Reproduce: `python -m pytest tests/` then the scripts in `experiments/*/`.

## Reproducibility rules

- Data files are quarantined in `data/raw/` and never committed; scripts that read them run in isolated mode (`python -I`) with paths passed as arguments.
- Every reported number must be regenerable by one script from raw data to table/figure.
- Session/temporal splits only — no shuffled-frame splits across time (AutoHack protocol; Arp et al. pitfalls).
- ROAD caveats are carried into every claim: simulated masquerade captures, obfuscated frame ordering, withheld vehicle model.
