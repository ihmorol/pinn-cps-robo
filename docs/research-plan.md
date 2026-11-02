# Research Plan

**Project:** Physics-Residual Detection of Masquerade Attacks on Controller Area Networks — a Physics-vs-Data Attribution Study on the ROAD Dataset
**Status:** Design frozen 2026-11-03 (domain decision verified; dataset scouting complete). Implementation not started — M1-CAN is next.
**Key documents:** [domain-decision.md](domain-decision.md) (why this domain) · [literature-review.md](literature-review.md) (verified survey) · [dataset-assessment.md](dataset-assessment.md) (ROAD facts)

## 1. Frozen research brief

**Constraints (unchanged from the charter):**
1. Existing public datasets only — no new attack data, no new attack simulations.
2. The physics-informed contribution must be demonstrated, not assumed — the ablation ladder exists precisely to make this falsifiable.
3. CPU-only compute; no vehicle hardware; no vehicle access.

**Research questions**

- **RQ1 (physics taxonomy)** — Which physical consistency laws (inter-signal kinematic consistency, temporal continuity, actuator limits) do ROAD's attack classes violate, and which do they respect?
- **RQ2 (detection)** — Do physics-consistency residual detectors detect the masquerade/fabrication attack classes that frequency- and payload-based detectors miss, under AUC-PR and per-attack-class recall?
- **RQ3 (attribution)** — In a strict ablation ladder, are detection gains attributable to *physics* (analytical residual, PINN) rather than model capacity (physics-free twin, RF/XGBoost, autoencoder)?
- **RQ4 (generality, optional)** — Does the same residual principle transfer to command-layer attacks on a ROS 2 mobile robot (Zenodo 17649537, command-suppression flood)? *(The ROS 2 kickoff analysis is preserved in git history / decision brief; the dataset is re-downloadable if this experiment is pursued.)*

**Hypotheses**

- **H1**: Masquerade and fabrication captures violate inter-signal kinematic consistency (e.g., four wheel speeds vs speedometer vs plausible longitudinal dynamics) while respecting per-signal ranges — i.e., the violations are *relational*, not marginal. Expected nuance: the "flam"-class fabrications are designed to be plausible, so violations may be partial; H1 is a characterization, not a guarantee.
- **H2**: Physics-residual detection outperforms payload/rate statistics on the stealthy classes (documented context: frequency-based approaches "will almost certainly fail" on ROAD masquerade per the dataset's own authors).
- **H3**: The physics constraint buys lower false positives on benign maneuvers than an equal-capacity physics-free model — the attribution result. Either outcome (physics helps / doesn't) is reportable.

## 2. Physics model for a passenger vehicle

From the CAN-decoded signals available in ROAD (four wheel speeds, speedometer, engine coolant temperature):

1. **Inter-wheel consistency**: the four wheel-speed signals are near-identical on a straight and differ predictably in curves (inner/outer wheel speed differ by `ω_track/2·ω_yaw`); their pairwise residuals must stay within a tight envelope. (The masquerade mechanism described by Moriano et al. is exactly the breaking of this near-perfect correlation.)
2. **Speedometer–wheel-speed consistency**: the displayed speedometer is a deterministic function of wheel speed (scaling + rounding).
3. **Temporal continuity / actuator limits**: vehicle speed is continuous with bounded acceleration (typ. |dv/dt| ≤ ~3–4 m/s² hard braking, far less in dynamometer runs); coolant temperature evolves on a minutes scale.
4. **Learned residual**: a network predicts next-step signals from recent history (and, for the PINN variant, with the kinematic relations above embedded as constraints); the prediction residual is the detection statistic.

Identified parameters (scaling, envelope widths, acceleration bounds) come from the 12 ambient captures only.

## 3. Method design

### 3.1 Detector ladder (the ablation — core of the contribution)

| # | Detector | Physics? | Learned? | Purpose |
|---|---|---|---|---|
| 0 | Payload/rate statistics (ID frequencies, byte distributions, entropy) | ✗ | ✗ | Trivial baseline; documented to fail on masquerade — quantifies the failure |
| 1 | Analytical kinematic residual (relations in §2, thresholds from ambient) | ✓ | ✗ | Classical model-based baseline |
| 2 | **PINN residual** (kinematic constraints in the loss + learned residual dynamics) | ✓ | ✓ | The proposed method |
| 3 | Physics-free NN forecaster (same capacity, no physics constraint) | ✗ | ✓ | Attribution control for RQ3 |
| 4 | Random Forest / XGBoost on windowed features | ✗ | ✓ | Conventional-ML baselines (charter) |
| 5 | Autoencoder (one-class, reconstruction error) | ✗ | ✓ | Charter baseline; the physics-AE comparison point from power-system literature |

### 3.2 Evaluation conditions

- **C-A (ROAD, full)**: all features incl. timing — with the dataset caveat stated: ROAD's frame order is intentionally obfuscated, which itself handicaps timing features. Detector 0's result is reported under this handicap explicitly.
- **C-B (value-only)**: timing features removed; only signal values + physics. The scientifically meaningful condition for RQ2/RQ3.
- **C-C (benign stress)**: all 12 ambient captures incl. road-driving segments — false-positive behavior on real maneuvers (turns, stops, gear changes) is the base-rate-fallacy response.
- **C-D (cross-dataset, if time)**: AutoHack (intact timing, real driving, physically verified labels) as the honesty check that physics doesn't only win where timing was obfuscated.

### 3.3 Metrics and protocol

- **AUC-PR** as the headline ranking metric (the norm established for ROAD by the time-based benchmark literature); **per-attack-class recall** (AutoHack norm) — aggregate F1 hides class-level failures.
- **FPR at an explicit operating point** with absolute counts (Axelsson base-rate discipline); benign captures are the FP stress set.
- **Segment-level credit / detection delay** (range-based precision-recall; eTaPR-style), since attacks are intervals, not points — point-adjust is banned.
- **Splits**: session-based/temporal only (AutoHack's competition protocol): train on ambient + (for supervised baselines) held-out attack captures; test on unseen attack captures of the same class. No shuffled-frame splits across time; no capture-level features crossing the split.
- Fixed seeds; every number regenerable by one script from raw data.

### 3.4 Scope guard (constraint #1)

All robustness analyses operate on the published recordings only (segment selection, masking, message-level analysis of the existing captures), labeled as sensitivity analyses of published data — never new attack generation.

## 4. Milestones

| Phase | Deliverable | Depends on |
|---|---|---|
| **M1-CAN** | ROAD downloaded + quarantined; index-named signals mapped to semantic channels (wheel speeds / speedometer / coolant) by inspection; decode raw captures not covered by the published CSVs if the masquerade captures aren't among them; tidy labeled panel | — |
| **M2-CAN** | Physics taxonomy (RQ1): per-attack-class violation map; ambient-data residual envelopes | M1 |
| **M3-CAN** | Detectors 0, 1, 4, 5 under C-A/C-B/C-C with the full metric suite | M2 |
| **M4-CAN** | PINN (2) + physics-free twin (3); attribution result (RQ3) | M3 |
| **M5-CAN** | (Optional) ROS 2 cross-domain check (RQ4); paper assembly; arXiv preprint; submission | M4 |

**Venue shortlist**: NDSS AutoSec workshop (where the ROAD group's masquerade work is published — exact fit), USENIX VehicleSec (2026 Best Artifact went to AutoHack there), escar (industry); journals: Journal of Information Security and Applications, Computers & Security. Strategy: arXiv preprint as soon as M2+M3 results exist (the ORNL group publishes actively on ROAD — speed matters).

## 5. Risks

1. **The ORNL group is actively publishing on ROAD masquerade** (2022, 2024, 2025, 2026) and Rahman et al. (Aug 2026) moved toward learned-twin detection on CAN. → arXiv early; position explicitly against [the TIFS 2025 graph-ML work] and [the digital-twin work].
2. **"First PINN on CAN" is unavailable as a claim** (Senthilkumar & Anbalagan 2026 exist within an FHE IDS). → Claim: first *systematic physics-vs-data attribution study* on ROAD masquerade. Retrieve the Senthilkumar original before writing.
3. **ROAD masquerades are simulated post-processing** (frame suspension + injection), vehicle model withheld. → Wording discipline: "physically verified injection captures + published masquerade captures"; no real-road masquerade claims.
4. **Some fabrications are designed to be physically plausible** → H1/H2 may hold only partially; a negative result on the stealthiest class is still a publishable boundary finding.
5. **Signal names are index-based** in the published CSVs; mapping is inspection work (M1-CAN). If the masquerade captures are not among the 17 pre-decoded captures, decoding raw `.log` files with the published attack-interval JSON is the fallback (CPU-feasible).
6. **Two-domain scope creep** → RQ4 is optional and explicitly last; the paper stands on RQ1–RQ3 alone.
