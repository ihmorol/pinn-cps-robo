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

## Status

- **Done:** domain verification and decision (two scout rounds + threat check); literature survey; ROAD dataset assessment; evaluation protocol design.
- **Next: M1-CAN** — download ROAD (556.7 MB), map the index-named signals to wheel-speed/speedometer/coolant channels, establish ambient residual envelopes.
- Python ≥ 3.10; CPU-only (no GPU required — models are minutes-scale).

## Reproducibility rules

- Data files are quarantined in `data/raw/` and never committed; scripts that read them run in isolated mode (`python -I`) with paths passed as arguments.
- Every reported number must be regenerable by one script from raw data to table/figure.
- Session/temporal splits only — no shuffled-frame splits across time (AutoHack protocol; Arp et al. pitfalls).
- ROAD caveats are carried into every claim: simulated masquerade captures, obfuscated frame ordering, withheld vehicle model.
