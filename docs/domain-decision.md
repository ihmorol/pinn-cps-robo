# Domain Decision Brief — 2026-11-03

**Decision: pivot the primary target to physics-residual intrusion detection on automotive CAN (ROAD masquerade attacks). The completed ROS 2 work is retained as the methodology origin and becomes a cross-domain validation section. ICS/HAI is the tracked fallback, not the primary.**

Basis: two verification scouts (prior-art + datasets) and a direct retrieval of the one flagged threat (the "cPINN-CAN" citation). Constraint set unchanged: public data only, no hardware, no new attack generation, CPU-only.

---

## 1. Why CAN/ROAD beats the alternatives under "max impact + publishable recognition"

| Criterion | ROS 2 (current) | **CAN/ROAD (chosen)** | ICS SWaT/HAI | Power grid |
|---|---|---|---|---|
| Audience | niche, growing | **huge, regulatory (ISO/SAE 21434, UNECE R155)** | huge (OT security) | large |
| Attack data | 1 normal + 1 attacked run, overt flood | **real car, physically verified attacks, incl. 13 masquerade captures — the documented hard case** | real testbed attacks (SWaT gated by NDA) | synthetic/simulated |
| Physics channels | cmd_vel + odom (2 runs) | **4 wheel speeds + speedometer + coolant temp, decoded CSVs with per-row labels (17/33 captures)** | tank levels/flows (clean) | Kirchhoff (clean) |
| Prior-art density | verified empty cell | partially occupied — **specific contribution still open** | partially occupied (physics-features ablation on HAI 2026) | crowded |
| Dataset access | done | **CC BY 4.0, direct Zenodo, 556.7 MB** | HAI easy; SWaT NDA | easy |
| Realistic venue | workshops, mid journals | **NDSS AutoSec, USENIX VehicleSec, escar, JISA/Computers & Security** | similar | similar |

## 2. The verified gap (what exists, what's undone)

**Documented problem statement (the stage is set):**
- ROAD's own paper (Verma et al., PLOS ONE 2024): masquerade attacks "do not cause perceptible timing changes" — *"With this masquerade dataset, frequency-based approaches will almost certainly fail to provide accurate detection."*
- Moriano et al. (NDSS AutoSec 2022): "masquerade attacks are the stealthiest CAN attacks"; the wheel-speed mechanism (four nearly identical signals whose correlation the adversary breaks) is described — but the paper states *"We did not compare our proposed forensic framework with other methods."*
- AutoHack competition (USENIX VehicleSec 2026): on realistic data, best F1 was **39–66 %** — real datasets collapse the 99 %+ numbers seen on simplistic CAN datasets.

**Closest prior art and what each leaves undone:**
1. **Rahman, Salek, Chowdhury (arXiv:2608.17093, 2026)** — LSTM digital-twin residual on decoded powertrain CAN signals, stealthy payload attacks. Not ROAD (private log); no analytical physics; no data-driven baselines (only a range/plausibility check that "detected almost none" of the attacks); 39.6 % false-positive rate admitted.
2. **Marfo, Moriano, Tosh, Moore (IEEE TIFS 2025)** — graph-ML masquerade detection *on ROAD* (the SOTA there). No physics anywhere; baseline is an internal ablation, not RF/XGBoost/AE or a physical model.
3. **Moriano et al. (AutoSec 2022; JISA 2026)** — signal-clustering similarity on ROAD masquerade; forensic; explicitly no baselines (2022); 2026 benchmark of lightweight statistical detectors concludes "no single method detects every attack."
4. **Senthilkumar & Anbalagan (JESA 2026)** — a "conservative physics-informed neural network" inside a *homomorphic-encryption* IDS. Focused on FHE latency (encrypt 106.57 s / decrypt 47.28 s), not detection science: no masquerade focus, no ablation vs data-driven baselines, not ROAD. **Must be cited as related work; it pre-empts any "first PINN on CAN" claim.** (Verified via Alsaadi et al., Appl. Sci. 16(18):9204, 2026, which describes it; the original paper itself not yet directly retrieved — do before writing.)

**Older physics/sensor-consistency line exists but pre-dates ROAD and never ablates**: CAID (escar 2017), Ganesan et al. (WCX 2017), Li et al. (CCS 2017 poster), Guo et al. (TVT 2019), He et al. (DAC 2020), Fenzl et al. (ARES 2021), Rajapaksha et al. (CyCon 2022, GRU + context), Guo et al. (TTE 2021, physics-guided EV powertrain — closest "physics-guided NN" but powertrain-level, not CAN payload).

**What remains genuinely open (our contribution):**
- **(a)** No work encodes *vehicle-kinematics consistency residuals* (four wheel speeds vs speedometer vs temporal continuity/acceleration limits) as the detection signal on ROAD.
- **(b)** No work on ROAD runs a *strict ablation ladder* (analytical physics residual → PINN → physics-free twin → RF/XGBoost/AE → payload/rate statistics) attributing detection gains to physics. Context: only 4 of 65 surveyed CAN IDS papers evaluate against any baseline (Rajbahadur et al., per the ROAD group's own PLOS ONE guide).
- **(c)** Characterizing *which physical law each ROAD attack class violates* — a "physics taxonomy" of the dataset's attacks — does not exist and is itself a novel, reusable artifact.

## 3. Dataset facts (verified)

| | ROAD (primary) | AutoHack (complementary) | CAN-MIRGU (backup) |
|---|---|---|---|
| Source | Zenodo 10462796, CC BY 4.0, direct | Zenodo 20321379, CC BY 4.0, direct | GitHub (per paper) |
| Size | 556.7 MB zip | ~2,700-frame test… (CSV + label files) | 17 h benign + 26 attacks |
| Vehicle | withheld (mid-2010s), dynamometer | 2023 Hyundai, real road | 2016 EV, proving ground |
| Physics channels | 4 wheel speeds, speedometer, coolant temp, reverse light — **decoded CSVs, per-row 0/1 labels (17/33 attack + 12/12 ambient captures)** | raw frames only (no decoded signals) | steering, brake, gear… (per-frame labels) |
| Attack classes | fuzzing, targeted fabrication, correlated fabrication, **masquerade ×13** (simulated by frame suspension + injection), accelerator attack | DoS, fuzzing, spoofing ×5, replay, UDS spoofing — physically verified | DoS, fuzzing, replay, spoofing ×13 IDs, + simulated suspension/masquerade |
| Labels | per-row CSV labels + JSON attack intervals | per-row labels | per-frame + JSON |
| Caveats | frame order intentionally obfuscated (priority/timing info removed); signal names index-based (must map by inspection); masquerade = simulated post-processing; vehicle model withheld | raw hex only — needs decoding for physics channels | simulated suspension/masquerade |

**ROAD timing caveat is strategically useful**: because ROAD's frame order is obfuscated, timing/rate detectors are handicapped *by the dataset's own design* — which shifts the burden of detection exactly to value/physics signals, and the ROAD authors' "frequency-based approaches will almost certainly fail" statement makes the comparison non-trivial rather than rigged. AutoHack (intact timing, real driving) serves as the honesty check that physics doesn't only win where timing was removed.

## 4. Research questions and hypotheses (frozen)

- **RQ1**: Which physical consistency laws do ROAD's attack classes violate, and which do they respect? (physics taxonomy; hypothesis: masquerade/fabrication attacks violate inter-signal kinematic consistency or temporal continuity, while respecting per-signal ranges — the "flam" fabrication is designed to respect them, so partial violation is expected)
- **RQ2**: Do physics-residual detectors detect the masquerade/fabrication classes that frequency- and payload-based detectors miss, under AUC-PR and per-attack-class recall? (hypothesis: yes, with the caveat that ROAD's timing obfuscation must be reported)
- **RQ3**: In the ablation ladder, is the gain attributable to *physics* (analytical residual / PINN) rather than model capacity (physics-free twin, RF/XGBoost, AE)? (hypothesis: the physics constraint buys lower false positives on benign maneuvers; outcome either way is reportable)
- **RQ4 (cross-domain)**: Does the same residual principle transfer to a ROS 2 mobile robot (Zenodo 17649537 command-suppression)? (uses the completed kickoff work as-is)

Detector ladder (reused unchanged from research-plan.md, §3.1): rate/payload statistics → analytical kinematic residual → **PINN residual** → physics-free NN twin → RF/XGBoost → AE. Metrics: AUC-PR (Blevins et al., arXiv:2101.05781 norm), per-attack-class recall (AutoHack norm), FPR at explicit operating point, detection delay; session/temporal splits only.

## 5. Risks and mitigations

1. **The ORNL group (Moriano/Marfo/Moore/Bridges) is actively publishing on ROAD masquerade** (2022, 2024, 2025, 2026) and Rahman et al. moved toward this framing in Aug 2026. → Speed is a competitive necessity; target an arXiv preprint as soon as RQ1+RQ2 results exist.
2. **"First PINN on CAN" is unavailable as a claim** (Senthilkumar & Anbalagan 2026 exist; also the "Temporal-Window-Aware Physics-Informed Edge IDS" (PCNA-IDS context, KBS 2026) seen in snippets). → Claim instead: first *systematic physics-vs-data attribution study* on ROAD masquerade. Retrieve the Senthilkumar original before writing.
3. **ROAD masquerades are simulated post-processing** and the vehicle is obfuscated. → Wording discipline: "physically verified injection captures + simulated masquerade captures, as published"; no real-road masquerade claims.
4. **ROAD's obfuscated timing handicaps rate baselines** → run rate baselines anyway, report the handicap explicitly, and use AutoHack (intact timing) for the cross-dataset honesty check.
5. **Some fabrications are designed to be physically plausible** → RQ1 may find partial violations only; frame results as a characterization, not a guarantee. A negative RQ2 result (physics can't catch flam-class fabrication) is still a publishable finding that quantifies the boundary of physics-based CAN detection.

## 6. Execution plan (delta from existing research-plan.md)

- **M1-CAN**: download ROAD (556.7 MB, quarantined), map the index-named signals to wheel speeds/speedometer/coolant via inspection, decode remaining captures if needed (CAN-D), build the labeled panel.
- **M2-CAN**: physics taxonomy (RQ1): identify the four wheel-speed IDs, verify inter-wheel consistency in ambient data, measure which consistency laws each attack class breaks.
- **M3-CAN**: baselines (rate/payload stats, RF/XGBoost, AE) + analytical kinematic residual, under AUC-PR/per-class recall/session splits.
- **M4-CAN**: PINN + physics-free twin (RQ3 attribution).
- **M5-CAN**: cross-domain validation on the ROS 2 dataset (existing plan, unchanged) → paper assembly (arXiv preprint; venue shortlist: NDSS AutoSec, USENIX VehicleSec, escar; journals: JISA, Computers & Security).

Compute: unchanged — CPU-only, minutes-scale training. Storage: +~1 GB for ROAD.
