# The Wheels Tell the Truth: What Kinematic Residuals Can (and Cannot) Detect in CAN Masquerade Attacks

*Draft v1 — target venue: NDSS AutoSec / USENIX VehicleSec workshop (6 pp). All citations verified; see literature/literature.csv.*

## Abstract

We present an ablation-controlled study of physics-based intrusion detection for CAN masquerade attacks. Using the public ROAD dataset, we recover the semantic identity of anonymized signals, show that each masquerade and fabrication class violates a specific physical-consistency law, and evaluate a full detector ladder — payload/range statistics, constancy heuristics, kinematic residuals, Random Forest, XGBoost, a one-class autoencoder, and a physics-informed forecaster against its own physics-free twin — under ambient-only calibration and capture-disjoint splits. Kinematic residuals detect three of four attack classes in both injection modes (residual ratios 178–1273× above the benign envelope) using no attack data. The fourth class, a live-patched reverse-light masquerade, evades every value- and physics-based detector we tested: its injected frames are dynamically consistent snapshots. A supervised XGBoost also fails on that class (AP 0.63), while a one-class autoencoder ranks it at AP 0.98 without ever seeing an attack. Our attribution experiment shows that a physics-informed forecaster gains nothing over an equal-capacity twin across four training regimes and three loss weights: the encoded physics is a linear relation the twin learns from about a thousand frames. Along the way we find that ROAD's shipped DBC cannot decode the dataset's own published signal extractions — a reproducibility hazard we resolve with an empirical layout solver. We release the protocol, code, and per-experiment logs. The contribution is not a new detector but a measured map of where physics pays in automotive intrusion detection — and where it does not.

## 1. Introduction

A masquerade attack on a CAN bus suspends legitimate frames and transmits fabricated ones at the expected frequency. The ROAD dataset's authors state the consequence plainly: frequency-based approaches "will almost certainly fail" against it [1]. The published detectors that do target this class watch signal statistics — clustering similarity [2], graph structure [3], or lightweight streaming models [4]. None of them asks the question a physicist would ask: the frames carry wheel speeds, a speedometer, and a coolant temperature, and those quantities are bound by kinematics. If the wheels say 60 km/h and the display says 160, something is wrong regardless of what the frequency spectrum says.

Whether that observation turns into a working detector — and whether the *physics* part of it earns its keep — is an empirical question. The machine-learning security literature has been burned before by evaluation shortcuts: As cataloged in [1], only 4 of 65 surveyed CAN IDS papers compare against any baseline, and realistic datasets collapse the familiar 99% accuracies to 39–66% [5]. So we built the comparison carefully before believing any result.

This paper makes four contributions.

- A **signal-recovery and physics-taxonomy method** for ROAD: we identify the anonymized wheel-speed, speedometer, and coolant channels from the publisher's own attack metadata, then show which physical-consistency law each of the four masquerade classes violates (Section 4).
- A **frame-level detector ladder** with ambient-only calibration: kinematic residuals detect three of four masquerade classes with recall 1.0, calibrated at the ambient 99.9th percentile (measured benign-frame false-positive rates 0-0.46%), using zero attack data (Section 5).
- A **boundary finding**: the reverse-light masquerade is a live-patched, dynamically consistent snapshot that evades every value- and physics-based detector we tested — and the reason it evades them is itself informative (Section 5.3).
- A **negative attribution result**: a physics-informed forecaster matches but never beats an equal-capacity twin across four training regimes and three loss weights. The physics value in this dataset is analytical, not learned (Section 6).

We position this as a measurement paper. The community has plenty of detectors; what it lacks is controlled evidence about *which signal source carries the information* — traffic statistics, payload values, learned patterns, or physical law — for the hardest attack class on the standard public dataset.

## 2. Background and Related Work

**Masquerade attacks on CAN.** The masquerade concept goes back to Hoppe and Dittmann's 2007 work on faking in-vehicle communication [6]; Koscher et al. demonstrated systematic compromise of a modern car in 2010 [7]; Miller and Valasek industrialized the threat with public tooling [8]. Moriano et al. call masquerades "the stealthiest CAN attacks" and describe the wheel-speed mechanism — four nearly identical signals whose correlation the adversary breaks — but their forensic framework was explicitly unbenchmarked [2]. Marfo et al. hold the state of the art on ROAD masquerade with graph machine learning, ablating only against their own feature variants [3]. The 2026 benchmark of lightweight unsupervised detectors concludes that no single method detects every attack [4]. A 2025 SoK systematizes the field and leaves physical-consistency detection open [9]. Rahman et al. come closest to our setting with an LSTM digital twin on decoded powertrain signals, but on a private log, against a range check that "detected almost none" of the attacks, with a 39.6% false-positive rate [10]. None of these works encodes vehicle kinematics as the detection signal on ROAD, and none runs the ablation ladder we run here. Sensor-consistency detection itself is old — Wasicek et al.'s CAID added a physical model to automotive IDS in 2017 [11], following a structured-proposal lineage from Müter et al. [12] — but the lineage predates ROAD and never meets the masquerade captures.

**Evaluation pitfalls.** Axelsson's base-rate argument [13] and the ten pitfalls of Arp et al. [14] shape our protocol: ambient-only threshold calibration, capture-disjoint supervised splits, per-class reporting, and explicit false-positive accounting. For time-series scoring we report precision-recall curves rather than point-adjusted F1, following [15] and [16]. The AutoHack competition provides the sobering calibration: on realistic data, the best IDS reached 39–66% F1 [5].

## 3. Signals and Physics Model

**Data.** ROAD [1], [17] contains 33 physically verified attack captures and 12 ambient captures from a real vehicle on a dynamometer, distributed with per-row labeled signal extractions for 17 attack and all 12 ambient captures (556.7 MB, CC BY 4.0). Thirteen captures are masquerades: fabricated frames sent in lieu of suspended ones, on four targets (three wheel-speed captures, three speedometer, six reverse-light, one coolant). The publisher ships a DBC with anonymized signal names.

**Signal recovery.** The anonymization hides semantics but the attack metadata leaks them: each capture's JSON records the injected arbitration ID. Injection of `0x6e0` with data `595945450000FFFF` identifies the four wheel-speed channels; `0xd0` carries the speedometer and reverse-light bit; `0x4e7` the coolant temperature. We verified the map empirically — the four `0x6e0` signals agree pairwise within 1.5% across ambient driving, and the speedometer channel freezes at its maximum exactly inside the published intervals.

**Consistency laws.** From these channels we derive four families of residuals, each with a floor estimated from ambient captures only: (L1) inter-wheel consistency, the maximum pairwise wheel-speed difference (benign floor 729 raw units, ~7% of scale, reached while cornering); (L2/L2d) speedometer–wheel relation in level and difference form, |Δs6 − α·Δw| with the scale α fit on ambient (floor 276); (L3) temporal continuity of wheel speed (floor 758); (L4–L6) per-signal value envelopes (coolant 255 vs. ambient 151); (L7) relational freeze, a display may only stop moving if the wheels do.

Two protocol details matter and are easy to get wrong. First, only the attacked arbitration ID's rows carry labels, so attack intervals must be derived across all IDs and split by time with a margin; one boundary frame per interval carries attack payload with a benign label. Second, ambient captures include long stationary stretches where a frozen display is correct — an unconditional "frozen signal" law produces false positives by design. Both failures occurred in our own pipeline before we fixed them; we log them as part of the contribution.

## 4. A Physics Taxonomy of ROAD Masquerades

Figure 1 shows the canonical example: the wheel-speed payload freezes at 6489/1349/0/16383 for twenty seconds while the benign inter-wheel residual sits near 10. The residual jumps four orders of magnitude at injection and drops back on release.

Table 1 summarizes all thirteen captures. Every masquerade class violates at least one law, and each class is identifiable by *which* law it breaks. Wheel-speed masquerades break inter-wheel consistency (178–585×) and continuity (258–1024×). Speedometer masquerades break the display–wheel relation (~165×) and mildly exceed the value envelope. Coolant masquerades exceed the envelope (255 vs. 151). The six reverse-light masquerades break nothing we can measure in these channels — which Section 5.3 explains.

This taxonomy is itself useful: it tells a defender which sensor pairs to monitor for which threat model, and it bounds what physics can promise.

**Fabrication variants.** ROAD distributes each injection in two modes: a masquerade capture (fabricated frames replace suspended ones) and a fabrication capture (fabricated frames join the live traffic). We decoded all thirteen fabrication captures from the raw logs — necessary because ROAD's shipped DBC does not reproduce its own published extractions (Section 7) — and ran the same taxonomy. The results mirror the masquerades exactly: correlated fabrications break inter-wheel consistency (178–585×) and continuity (258–1273×); speedometer fabrications exceed the value envelope (16384 vs. a benign 573–1590) and jump the display relation (190–211×); the six reverse-light fabrications evade every law, like their twins. Two consequences. First, ROAD's "correlated" fabrication — advertised as the most stealthy fabrication possible in public data — is not stealthy to physics: its injected wheel values are grossly inter-inconsistent once decoded with the correct layout (we reject our own pre-registered prediction here). Second, the reverse-light boundary is a property of the attack technique, not of one injection mode.

## 5. Detector Ladder

### 5.1 Setup

Frame-level scores on the attacked-ID stream. All thresholds come from the 99.9th percentile of ambient scores — no attack data touches calibration. We report average precision and recall at that operating point, per class, with PR curves in Figure 2.

### 5.2 Results

Table 2 gives the stage-1 comparison. Range statistics and kinematic residuals both catch the three payload classes perfectly (AP 0.97–1.0, recall 1.0); the payload values exceed ambient envelopes, so a plain range check suffices there. The constancy heuristic is dead on this dataset — ambient stationary stretches produce runs of 106,279 identical frames, so it never fires. Detection is immediate where detection happens: the median delay from injection onset to the first flagged frame is 0.005--0.007 s --- one CAN frame at 100 Hz --- for all three payload classes. The interesting row is the reverse-light class: range statistics fail (AP 0.49), the constancy heuristic fails (0.34), and kinematic residuals fail (0.44).

### 5.3 Why the reverse-light masquerade evades physics

The injector live-patches the light bit: the frame's rolling counter keeps incrementing during the attack (we measured maximum in-attack counter runs of one frame), and the patched frame is a snapshot taken at injection time. During those windows the vehicle moves steadily, so the frozen display value is consistent with the wheels. The attack is a *dynamically consistent snapshot* — physically valid at injection and for as long as the vehicle state does not change. Kinematics cannot flag it. A semantic law could (the light bit must agree with the gear), but ROAD's anonymized DBC hides the gear signal; our best guess fails on 48.6% of ambient frames, so we report the class as open rather than force a broken detector.

Two supervised models confirm the difficulty: Random Forest generalizes across captures but reaches AP 0.37 on this class, XGBoost 0.63. The one-class autoencoder — trained on ambient frames, never shown an attack — ranks the class at AP 0.98, though at the strict ambient operating point its recall is near zero. The class is rankable, not thresholdable.

## 6. Attribution: Does the Physics Constraint Pay?

The remaining question is whether *learning with physics* beats learning without it. We train a one-step wheel-speed forecaster twice: a PINN whose loss adds display-tracking and acceleration-limit terms, and an identical twin with the data loss only. Figure 3 shows average precision across four ambient training fractions.

The result is parity, and it is exact: across five random seeds the two models are statistically indistinguishable in every regime (at 0.1% of the data — about a thousand frames — AP 0.706 ± 0.001 for both; at 100%, 0.711 ± 0.005). A sweep of the physics weight λ ∈ {0.1, 1, 10} moves nothing outside noise. Both models handle the accelerator captures — real, unusual driving — with zero false positives.

The mechanism is straightforward. The physics we can encode in a loss (display tracks wheels, speed changes smoothly) is a linear relation the twin learns from a thousand examples, and ROAD provides a million. This reproduces, in automotive security, the finding that physics priors pay off when the physics is hard to learn or the data is scarce [18]–[20]. On this dataset, neither condition holds for the forecaster formulation. The physical knowledge that *does* pay is the analytical form: it needs no training, no attack data, and it diagnoses *which* law broke — something a learned residual cannot name.

## 7. Limitations

ROAD's masquerade captures are simulated by post-processing, the vehicle ran on a dynamometer, and the frame ordering is deliberately obfuscated — our timing features are weakened by the dataset's own design, and our claims are case-study evidence, not deployment results. A dataset-integrity finding deserves its own warning: the shipped anonymized DBC does not decode the published CSV signal extractions, and the bit layouts differ between capture families (four 14-bit fields in ambient extractions; 13/11/10/14 in masquerade extractions). We recovered the layouts empirically from log-CSV pairs and validated them by exact reproduction; anyone reusing ROAD's DBC will silently misdecode signals. One fabrication capture (coolant, n=1) has an unresolved decoding anomaly and is excluded from our claims. The gear signal required for a semantic reverse-light law is unrecoverable from the anonymized DBC. Our PINN encodes physics as soft constraints on a one-step forecaster; structural encodings (hard kinematic constraints, multi-step prediction) remain untested, so our negative attribution result is scoped to this formulation. Finally, the reverse-light finding may not transfer to a vehicle whose DBC exposes gear state — the class is open on ROAD, not closed in general.

## 8. Conclusion

We asked where physics pays in the detection of CAN masquerade attacks, and measured the answer on the public benchmark. Kinematic residuals carry real information — three of four masquerade classes at recall 1.0 with zero attack data, at ratios up to 1024× the benign envelope — and they diagnose which law broke, which no learned detector offers. Learned soft-physics constraints add nothing here. One class evades everything value-based, physics-based, and supervised; a one-class autoencoder ranks it without seeing attacks. The wheels do tell the truth, most of the time — and knowing exactly when they fall silent is what this paper adds.

## References (verified subset; full tracker in literature/literature.csv)

[1] Verma et al., PLOS ONE 2024. [2] Moriano et al., AutoSec 2022. [3] Marfo et al., IEEE TIFS 2025. [4] Moriano et al., JISA 2026. [5] Song et al., USENIX VehicleSec 2026. [6] Hoppe & Dittmann 2007. [7] Koscher et al., IEEE S&P 2010. [8] Miller & Valasek 2013/2014. [9] Serag et al., arXiv:2510.02960 (NDSS 2027). [10] Rahman et al., arXiv:2608.17093, 2026. [11] Wasicek et al., escar 2017. [12] Müter et al., IAS 2010. [13] Axelsson, ACM TISSEC 2000. [14] Arp et al., USENIX Security 2022 / CACM 2024. [15] Tatbul et al., NeurIPS 2018. [16] Kim et al., AAAI 2022. [17] ROAD dataset, Zenodo 10462796, 2020. [18] Krishnapriyan et al., NeurIPS 2021. [19] Grossmann et al., ICLR 2024. [20] Jabbari Zideh et al., arXiv:2312.04758, 2023.

## Figures

- Fig 1: `figures/fig1_timeline.png` — masquerade timeline + inter-wheel residual.
- Fig 2: `figures/fig2_pr_stage1.png` — PR curves, four classes × three detectors.
- Fig 3: `figures/fig3_attribution.png` — PINN vs twin across training fractions.
- Fig 4: `figures/fig4_taxonomy.png` — taxonomy heatmap.
