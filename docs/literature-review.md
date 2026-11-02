# Physics-Residual Detection of Masquerade Attacks on Controller Area Networks: A Working Survey toward a Physics-vs-Data Attribution Study on ROAD

*Working survey for the project "Physics-Residual Detection of Masquerade Attacks on CAN". Compiled 2026-11-03; supersedes the ROS 2-era survey (preserved in project history). Companion notes: [domain-decision.md](domain-decision.md), [research-plan.md](research-plan.md), [dataset-assessment.md](dataset-assessment.md).*

## Abstract

Masquerade attacks on the CAN bus — fabricated frames sent in lieu of suspended legitimate ones — are the documented frontier of automotive intrusion detection: they preserve expected frequencies and plausible per-signal values, and the ROAD dataset's own authors state that frequency-based approaches "will almost certainly fail" against them. This working survey maps the terrain for a project that proposes vehicle-kinematics consistency residuals (four wheel speeds vs speedometer vs temporal continuity) as the detection signal, benchmarked against data-driven baselines with a strict ablation ladder. Three perspectives were scouted with per-reference verification: the masquerade literature, the model-based/physics-informed detection lineage, and dataset/evaluation methodology. Findings: (1) the masquerade problem is well-posed and active — signal-clustering, graph-ML, and lightweight statistical detectors exist on ROAD, but none uses physical-consistency residuals and none runs external-baseline ablations; (2) a sensor-consistency lineage exists in the vehicle domain since 2010, the classical CPS residual-detection theory is mature, and physics priors demonstrably help in power-system detectors — yet a true physics-informed (loss-embedded) CAN IDS is essentially unoccupied, the sole exception being a physics-informed classifier inside a homomorphic-encryption IDS focused on encryption latency; (3) evaluation norms and critiques (AUC-PR on ROAD, session splits, per-class recall, dataset-quality audits) are strong enough to support a credible benchmark, and realistic datasets collapse the 99 %+ headline numbers of the literature to 39–66 %. The survey concludes that "physics-residual detection of ROAD masquerade attacks with an attribution ablation" is an open, well-staged contribution — provided the ORNL group's active output and the dataset's simulated-masquerade caveat are handled with speed and wording discipline.

## 1. Introduction

Modern vehicles run dozens of electronic control units over a CAN bus designed without authentication or encryption; anomaly-based intrusion detection systems (IDS) are the compensating control [5]. Within this space, one attack class resists the standard toolkit: the **masquerade attack**, in which an adversary suspends legitimate frames and sends fabricated ones at the expected frequency with payload values that look plausible frame-by-frame [1], [2]. The ROAD dataset (Real ORNL Automotive Dynamometer) made this class publicly benchmarkable [1], and a research line has grown around it [2]–[4]. What that line has *not* produced is a detector grounded in the vehicle's physics: the signals on the CAN bus are not arbitrary bytes but wheel speeds, engine temperature, and display values bound together by kinematics and thermodynamics — and no published ROAD detector encodes those relations.

This survey is the working document for the project that proposes exactly that, and benchmarks it against data-driven baselines. It answers three questions:

- **RQ1.** What is the state of masquerade-attack detection on CAN, and what do its practitioners identify as open?
- **RQ2.** What evidence supports physics-based / physics-informed detection over data-driven ML, in CPS generally and in vehicles specifically — and has any of it reached CAN?
- **RQ3.** What public datasets and evaluation norms support a credible physics-vs-data attribution benchmark?

Section 4–6 develop the branches; Section 7 covers the ROS 2 validation domain; Section 8 synthesizes; Section 9 lists open problems; Section 10 answers the RQs.

## 2. Methodology

Three search perspectives were run (masquerade/CAN IDS prior art; physics-based and physics-informed detection; datasets and evaluation norms), each with multiple keyword rounds, executed as parallel retrieval agents with arXiv/Semantic Scholar/Zenodo/publisher records as ground truth, plus direct retrieval of flagged threats. Inclusion required verified existence (exact title + authors retrieved); findings are quoted only at title/abstract level. Three key papers were additionally downloaded and read from cover ([7], [6], [8]), and the sole flagged "PINN on CAN" candidate was resolved by direct retrieval of the citing paper's full text [37]. Unconfirmable items (a "Temporal-Window-Aware Physics-Informed Edge IDS" seen only in snippets; several dataset names seen without retrievable provenance) are excluded or listed in the ledger. Domain-generic references (PINN foundations, security-ML evaluation pitfalls, time-series metrics) carry over from the previous survey round where already verified. Final corpus: ~50 verified works, 50 cited.

The taxonomy (Section 3) organizes the field by *signal source* — what a detector watches — crossed with study type, because the project's contribution is precisely to move detection from the traffic/payload signal to the physical-consistency signal.

## 3. Taxonomy

| Study type → <br> Signal source ↓ | Dataset | Detector | Survey / critique |
|---|---|---|---|
| **Traffic / frequency / timing** | ROAD [1]; CAN-MIRGU [6]; Car-Hacking/OTIDS [11]; SynCAN [10] | payload-ID statistics, entropy, interval detectors (benchmarked in [8], [38]) | AI-IDS survey [5]; dataset audits [1], [8] |
| **Payload values, no physics** | AutoHack [7]; CICIoV2024 [12] | signal clustering [2]; graph ML [3]; lightweight statistical [4] | — |
| **Sensor consistency / vehicle physics** | — (none public) | CAID [14]; heterogeneous-sensor consistency [15], [16], [17], [18], [19]; targeted-attack relationships [20]; vehicle-context GRU [21]; UKF+ML [22]; physics-guided EV [23]; LSTM digital twin [24] | structured anomaly sensors [13] |
| **Physics-informed (loss-embedded) × CAN × external baselines** | **— empty** | **— empty (nearest: [36], a PINN inside an FHE IDS; [35], tele-driving, not CAN)** | — |

The bottom row is the survey's central finding: the vehicle-physics signal exists in an analytical lineage a decade old, the ROAD masquerade problem is mature and public, and nothing connects them — no physics-consistency detector on ROAD, no physics-vs-data attribution ablation anywhere in the CAN IDS literature.

## 4. Masquerade Attacks: The Documented Frontier (RQ1)

The ROAD paper is both the dataset and the problem statement. Verma et al. catalog the CAN IDS dataset landscape, introduce ROAD's 33 attack captures (fuzzing, targeted ID fabrication, correlated signal fabrication, and **masquerade** variants in which spoofed frames are sent in lieu of suspended ones), and state the mechanism plainly: masquerade attacks "do not cause perceptible timing changes," and "with this masquerade dataset, frequency-based approaches will almost certainly fail to provide accurate detection" [1]. Moriano et al. name masquerades "the stealthiest CAN attacks" and describe the wheel-speed mechanism — an adversary modifying the four nearly identical wheel-speed signals to break their near-perfect correlation, flaggable "even if the modified signals are not abnormal when considered individually" — but their forensic clustering framework is explicitly unbenchmarked: "we did not compare our proposed forensic framework with other methods" [2]. The follow-ups sharpen the gap rather than close it: Moriano et al.'s 2026 benchmark of four lightweight unsupervised detectors on ROAD concludes "no single method detects every attack" [4], and Marfo et al.'s graph-machine-learning detector — the current state of the art on ROAD masquerade [3] — ablates only against its own feature variants, with no physics model and no data-driven classifier baselines.

Two neighboring works frame what "context" means for learned detectors. Rajapaksha et al. augment a GRU IDS with vehicle-dynamics context features and report F1 > 99 % against injection and masquerade attacks on *older, simpler* datasets [21] — the numbers that realistic datasets collapse (Section 6). Fenzl et al. detect targeted attacks (e.g., speedometer manipulation) via "complex relationships between sensor values" learned by genetic programming, compared against ANN and rule-based detectors [20]. Both exploit signal *relationships* — the same territory as physics residuals — but neither embeds physical laws, neither evaluates on ROAD, and neither attributes gains to physics rather than capacity.

## 5. From Sensor Consistency to Physics-Informed Residuals (RQ2)

### 5.1 The analytical lineage: consistency checks without ROAD

Model-based detection on vehicles predates ROAD by a decade. Müter et al. structured in-vehicle anomaly detection around architectural properties of the bus, including value plausibility [13]; Wasicek et al.'s CAID explicitly "adds a physical model to the detection engine" and demonstrated detection of a chip-tuning attack on a test vehicle, claiming to be the first to leverage physical models this way in automotive IDS [14]. A consistency-detection line followed through the 2017–2020 literature: cross-checking heterogeneous sensors (GPS, wheel speed, accelerometer) [15], integrated sensor-correlation regression [16], correlation-and-frequency analysis [17], sensor-consistency with frequency-domain features [18], and regression on inherently redundant sensor pairs where the estimated-vs-actual residual flags anomalies [19]. The most recent hybrid fuses an unscented Kalman filter with ML, while arguing that precise vehicle-dynamics modeling "could be impractical or prohibitively costly" — and evaluates only in simulation [22]. The lineage establishes both the mechanism and its ceiling: consistency residuals work, but this work predates ROAD's masquerade captures, uses private logs or simulation, and (with the partial exception of [20], [21]) never runs the ablation against data-driven classifiers that would attribute the gains.

### 5.2 The classical CPS theory and the PINN evidence

The theory this project inherits is mature: Pasqualetti et al. characterized attack detectability and constructed residual generators via unknown input observers [25], and Giraldo et al. organized physics-based monitors into a survey-level taxonomy [26]. Physics-informed neural networks embed physical laws as training constraints [27], [28], and their strongest *security* evidence comes from power systems: Jabbari Zideh et al. embed Kirchhoff's law in a convolutional autoencoder's loss and report better accuracy, convergence, and stealthy-attack detection than the same AE without physics [29]; Nafees et al. report +36.4 % accuracy and fewer false positives over black-box baselines for stealthy attacks on generation control [30]. The critics bound the claim: soft physics constraints create competing objectives that fail to optimize [31], loss components converge at mismatched rates [32], PINNs never beat the finite element method on forward problems and become competitive only with measurement data [33], and physics-informed models can appear reliable while masking flaws [34]. The resolved condition: physics priors pay off when the physics is simple and dominant, data is scarce, and the attack is invisible to statistical features — conditions the kinematic setting of a passenger vehicle plausibly meets and the ablation ladder must verify rather than assume.

### 5.3 The CAN situation: one near-miss and two neighbors

No verified physics-informed (loss-embedded) CAN IDS with external baselines exists. The nearest hit is Senthilkumar & Anbalagan's "conservative physics-informed neural network" inside a privacy-preserving CAN IDS — but as described by the citing survey, that system's contribution is homomorphic-encryption operation (encrypt 106.57 s / decrypt 47.28 s), not detection science: no masquerade focus, no baseline ablation, no ROAD [36], [37]. Outside CAN but adjacent: Ghosh et al. build a physics-informed context-aware detector for false-data injection on tele-driving *steering commands* [35], and a 2025 dissertation applies PINNs to network-level traffic-flow modeling and adversarial sensor hardening — neither is in-vehicle payload detection. Within the vehicle domain, the closest "learned physics" works are Guo et al.'s physics-guided ML for EV powertrain attacks (physical models + LSTM, evaluated against its own data-driven ablation, not CAN payload IDS) [23] and Rahman et al.'s LSTM digital twin of "physical relationships among decoded powertrain signals," which detects stealthy payload/masquerade attacks on a *private* log with a range-and-plausibility baseline that "detected almost none" of the attacks and an admitted 39.6 % false-positive rate [24]. The cell "physics-consistency residuals × ROAD × ablation vs RF/XGBoost/AE" is empty; the movement toward it (Rahman 2026) is two months old at survey time — speed is a factor.

## 6. Datasets and Evaluation Methodology (RQ3)

### 6.1 The dataset landscape: ROAD leads for physics

Four public CAN datasets support masquerade-adjacent research (Table 2). ROAD is the only one that combines physically verified attacks on a real vehicle, **pre-decoded signal time series** (four wheel speeds, speedometer, engine coolant temperature) with per-row labels, and machine-readable attack-interval metadata — 556.7 MB, CC BY 4.0, direct download [1], [9]. CAN-MIRGU complements it with 17 h of real-road benign driving and 26 physically verified injection attacks (steering, brake, gear, wiper, power-steering targets), plus 10 simulated suspension/masquerade attacks with per-frame labels [6]; AutoHack (2026) contributes a three-bus, real-driving dataset with physically verified attack labels and the field's most rigorous evaluation protocol — raw frames only [7]. SynCAN is synthetic signal-space data (useful for unit tests, weak as evidence) [10], and Car-Hacking/OTIDS — the most-cited dataset — is documented as flawed: benign collected while driving, attacks while stationary, ID frequencies so altered that everything scores > 99 % [8], [11]. CICIoV2024 adds Ford-based DoS and spoofing captures with raw fields [12]. For the ICS fallback domain, HAI is frictionless (git clone, CC license) with 58 attacks across four control processes [47]; SWaT's cleaner physics sits behind an NDA (see [domain-decision.md](domain-decision.md)).

**Table 2 — Public CAN datasets relevant to a physics-vs-data benchmark.** *ROAD is the only one with decoded physics channels; AutoHack is the only one with intact real-vehicle timing.*

| Dataset | Vehicle / motion | Physics channels | Masquerade-class attacks | Labels | Known caveats |
|---|---|---|---|---|---|
| ROAD [1], [9] | real car, dynamometer | **wheel speeds ×4, speedometer, coolant temp (decoded CSV)** | **13 simulated masquerade captures** + correlated fabrications | per-row + JSON intervals | frame order obfuscated (timing weakened); signal names index-based; masquerade simulated |
| CAN-MIRGU [6] | EV, proving ground | steering, brake, gear… (per-frame, raw IDs) | 10 simulated suspension/masquerade | per-frame + JSON | masquerade/suspension simulated |
| AutoHack [7] | 2023 Hyundai, real road | raw frames (decoding needed) | replay/spoofing (physically verified) | per-row | no decoded signals; short attack durations |
| SynCAN [10] | synthetic | signal space | suppress attack | per-row | synthetic, unvalidated vs real vehicle |
| Car-Hacking [11] | KIA Soul (OBD-II) | raw fields | impersonation (gear/RPM) | per-row | stationary-attack artifact; trivial separability [8] |

### 6.2 Evaluation norms and the critique literature

The field audits itself well enough to design against. can-sleuth benchmarks 16 ML models across CAN datasets and shows that class imbalance (up to 927:1 — "unrealistic to the problem"), timestamp-feature inclusion, and data-field subdivision materially change model rankings [8]. The ROAD group's guide catalogs dataset flaws across the literature and records that only 4 of 65 surveyed IDS papers evaluate against any baseline [1]. The AutoHack competition put realistic numbers on the record: best F1 ranged **39–66 %**, with replay/spoofing misclassified as normal 34.9 %/21.0 % of the time — and it prescribes the protocol norms: session-based splits to prevent leakage and per-attack-class recall [7]. On ROAD specifically, the time-based benchmark established AUC-PR as the appropriate ranking metric [38]. The generic security-ML literature completes the checklist: ten pitfalls (inappropriate baselines, base-rate fallacy, lab-only evaluation) [41], [42]; Axelsson's argument that false-positive rate is the binding constraint of any IDS [43]; leakage formalization [39] and its documented prevalence across ML-based science [40]; and time-series metric discipline — range-based precision/recall over segments [44], the demonstrated inflation of point-adjusted scores [45], and the argument that flawed benchmarks create an "illusion of progress" [46]. For ICS-style interval credit, HAI's authors maintain eTaPR [47]. The project's protocol (AUC-PR + per-class recall + session splits + explicit FPR + segment-level delay) is assembled from exactly these norms.

## 7. The ROS 2 Validation Domain

The project retains a cross-domain check: the same "does the plant obey the commands" residual logic applied to a ROS 2 mobile robot. The primary dataset is a pair of ROS 2 rosbags containing a 500 Hz zero-velocity command flood [48] — inspection (previous round) confirmed both the command stream (`/mobile_base_controller/cmd_vel`) and the physical state (`/mobile_base_controller/odom`) are recorded, the robot stops within one second of flood onset while its legitimate command stream continues interleaved, and the normal run contains natural false-positive stressors. The detection literature there is traffic-centric — the closest analogue detects DoS on ROS 2 UGVs from topic-traffic features (MLP, 97 % on an overt flood) [49] — and the domain's own physics-detection survey names empirical validation as open [50]. This section is deliberately compact: it exists to support RQ4 generality, not as a second headline.

## 8. Synthesis Discussion

**The frontier is relational, and the field knows it.** Across branches, the masquerade literature converges on relationships: frequency relationships must be preserved (so frequency detectors fail [1]), and the wheel-speed signals are near-perfectly correlated (so their breakage is the flag [2]) — yet the detectors built on ROAD watch either statistics of individual signals [4] or learned graph structure [3], never the kinematic relations themselves. The analytical lineage knows how to watch them [13]–[19]; it simply predates the public masquerade data and never met the ablation discipline [1], [41].

**The physics attribution question is genuinely open in CAN.** Power-system evidence says physics priors beat data-driven baselines on stealthy attacks [29], [30]; the PINN critics say such gains are conditional on simple dominant physics and scarce data [31]–[34]; vehicle kinematics is simple dominant physics and benign driving data is comparatively scarce. Whether that conditional transfers to CAN masquerade is exactly what no work has tested — and the two nearest neighbors ([24]'s digital twin with a failing trivial baseline; [36]'s PINN inside an encryption pipeline) both leave the attribution question untouched.

**Realism is the differentiator.** The evaluation critique literature [1], [7], [8], [45], [46] has dismantled the 99 %-F1 culture: on realistic data the best systems score 39–66 % [7]. A physics-vs-data benchmark that reports per-class recall, false positives on real maneuvers, and detection delay — with the ROAD timing caveat stated — is aligned with where the field's standards are moving, which matters as much for publishability as the detection results themselves.

## 9. Open Problems

1. **Physics-consistency detection on ROAD is unoccupied** — no work encodes wheel-speed/speedometer/continuity residuals as the detection signal on the public masquerade captures (Section 3, empty cell).
2. **No CAN IDS paper runs a physics-vs-capacity ablation** — the closest works either compare to trivial baselines [24] or only their own ablations [3], [4]; the 4-of-65 baseline deficit [1] persists in the masquerade subfield.
3. **A physics taxonomy of ROAD attacks does not exist** — which physical law each attack class violates (and which the "flam"-class fabrications deliberately respect) is unpublished; it bounds what physics-based detection can and cannot catch.
4. **Masquerade detection on *moving* vehicles is data-starved** — ROAD's masquerades are simulated by post-processing and the vehicle ran on a dynamometer [1]; CAN-MIRGU's real-road masquerades are likewise simulated [6]. The stealthy-suppression-on-real-drive cell is [unconfirmed: no public dataset retrieved].
5. **Timing-obfuscated datasets bias the detector landscape** — ROAD's frame-order obfuscation weakens timing detectors by design [1]; cross-dataset honesty checks (intact-timing data like [7]) are unretrieved in the masquerade literature.

## 10. Conclusion

**RQ1.** Masquerade detection on CAN is an active, well-posed problem with a public benchmark (ROAD) and a documented mechanism (broken inter-signal correlation), served by clustering [2], graph ML [3], and lightweight statistical detectors [4] — all statistical, none physics-based, none externally ablated; the field's own guides call frequency-based failure "almost certain" [1] and baseline comparisons absent [1].

**RQ2.** Physics-based detection has a mature classical theory [25], [26], an analytical vehicle lineage since 2010 [13]–[22], and conditional evidence that physics priors beat data-driven baselines on stealthy attacks [29], [30], bounded by PINN critics [31]–[34]. In CAN specifically, only a PINN-inside-FHE outlier [36], [37] and two non-CAN neighbors [23]–[24], [35] exist: the physics-residual × ROAD cell is empty.

**RQ3.** ROAD uniquely supports the study (decoded physics channels, per-row labels, masquerade captures, CC BY 4.0) [1], [9]; CAN-MIRGU and AutoHack complement it [6], [7]; and the evaluation norms (AUC-PR [38], session splits and per-class recall [7], dataset audits [1], [8], security-ML pitfalls [41], [42], [43], time-series metrics [44]–[46]) are sufficient for a credible attribution benchmark.

**Contribution of this survey.** It establishes — with per-reference verification and three papers read from cover — that the cell "vehicle-kinematics residuals × ROAD masquerade × external-baseline ablation" is empty, identifies the three works any successor must position against ([3], [4], [24]), and converts the field's evaluation critiques into the benchmark protocol of [research-plan.md](research-plan.md).

## References

*Author lists limited to retrieved metadata (surnames only where initials unconfirmed; et al. after three authors).*

[1] Verma, Bridges, Iannacone, et al., "A comprehensive guide to CAN IDS data and introduction of the ROAD dataset," PLOS ONE 19(1):e0296879 (arXiv:2012.14600), 2024.
[2] Moriano, Bridges, Iannacone, "Detecting CAN masquerade attacks with signal clustering similarity," NDSS AutoSec Workshop (arXiv:2201.02665), 2022.
[3] Marfo, Moriano, Tosh, Moore, "Detecting masquerade attacks in controller area networks using graph machine learning," IEEE Transactions on Information Forensics and Security 20 (arXiv:2408.05427), 2025.
[4] Moriano, Hespeler, Li, Bridges, "Evaluating lightweight unsupervised online IDS for masquerade attacks in CAN," Journal of Information Security and Applications 98:104392 (arXiv:2406.13778), 2026.
[5] S. Rajapaksha, H. Kalutarage, M. O. Al-Kadri, A. Petrovski, G. Madzudzo, M. Cheah, "AI-based intrusion detection systems for in-vehicle networks: a survey," ACM Computing Surveys 55, 2023.
[6] S. Rajapaksha, G. Madzudzo, H. Kalutarage, A. Petrovski, M. O. Al-Kadri, "CAN-MIRGU: a comprehensive CAN bus attack dataset from moving vehicles for intrusion detection system evaluation," Symposium on Vehicles Security and Privacy (VehicleSec), 2024.
[7] Y. Song, S. Ahn, S. Baek, H. Kim, H. K. Kim, S. Jeon, "AutoHack: a physically verified multi-bus CAN dataset for intrusion detection system evaluation," 4th USENIX Symposium on Vehicle Security and Privacy, 2026.
[8] B. Kidmose, W. Meng, "can-sleuth: investigating and evaluating automotive intrusion detection datasets," European Interdisciplinary Cybersecurity Conference (EICC), pp. 19–28, 2024.
[9] "Real ORNL Automotive Dynamometer (ROAD) CAN intrusion dataset," Zenodo, DOI 10.5281/zenodo.10462796, 2020.
[10] "SynCAN: synthetic CAN intrusion detection dataset," ETAS GmbH, github.com/etas/SynCAN, 2021.
[11] Lee, Jeong, Kim, "OTIDS: a novel intrusion detection system for in-vehicle network," IEEE International Conference on Privacy, Security and Trust (PST), 2017.
[12] Neto, et al., "CICIoV2024: a benchmark dataset for intra-vehicle networks cybersecurity," Internet of Things, 2024.
[13] M. Müter, A. Groll, F. C. Freiling, "A structured approach to anomaly detection for in-vehicle networks," International Conference on Information Assurance and Security, 2010.
[14] A. Wasicek, M. Pesé, A. Weimerskirch, et al., "Context-aware intrusion detection in automotive control systems," escar Europe, 2017.
[15] A. Ganesan, R. Rao, K. Shin, "Exploiting consistency among heterogeneous sensors for vehicle anomaly detection," SAE World Congress Experience, 2017.
[16] Li, Zhao, Sastry, Yang, "Intrusion detection system for in-vehicle networks using sensor correlation and integration (poster)," ACM CCS, 2017.
[17] Sharma, Petti, Lin, "Pearson correlation analysis to detect misbehavior in CAN," IEEE VTC-Fall, 2018.
[18] Guo, Wang, Du, et al., "Detecting vehicle anomaly by sensor consistency and frequency characteristics," IEEE Transactions on Vehicular Technology 68(6), 2019.
[19] He, Zhang, Kong, Salekin, "Exploring inherent sensor redundancy for automotive anomaly detection," ACM/IEEE DAC, 2020.
[20] Fenzl, Rieke, Dominik, "In-vehicle detection of targeted CAN bus attacks," ARES, 2021.
[21] S. Rajapaksha, H. Kalutarage, M. O. Al-Kadri, G. Madzudzo, A. Petrovski, "Keep the moving vehicle secure: context-aware intrusion detection system for in-vehicle CAN bus security," IEEE CyCon, 2022.
[22] Bian, Farsi, Azad, Hobbs, "Data-driven intrusion detection in vehicles: integrating unscented Kalman filter (UKF) with machine learning," ICINCO (arXiv:2506.22404), 2025.
[23] Guo, Ye, Yang, "Cyberattack detection for electric vehicles using physics-guided machine learning," IEEE Transactions on Transportation Electrification 7(3), 2021.
[24] Rahman, Salek, Chowdhury, "Digital twin-based intrusion detection for vehicle powertrain CAN bus systems," arXiv:2608.17093, 2026.
[25] F. Pasqualetti, F. Dörfler, F. Bullo, "Attack detection and identification in cyber-physical systems," IEEE Transactions on Automatic Control 58(11), 2013.
[26] J. Giraldo, A. Cardenas, N. Quijano, "A survey of physics-based attack detection in cyber-physical systems," ACM Computing Surveys 51(4), 2018.
[27] M. Raissi, P. Perdikaris, G. E. Karniadakis, "Physics-informed neural networks: a deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations," Journal of Computational Physics 378, 2019.
[28] G. E. Karniadakis, I. G. Kevrekidis, L. Lu, P. Perdikaris, S. Wang, L. Yang, "Physics-informed machine learning," Nature Reviews Physics 3(6), 2021.
[29] Jabbari Zideh, et al., "Physics-informed convolutional autoencoder for cyber anomaly detection in power distribution grids," arXiv:2312.04758, 2023.
[30] Nafees, et al., "On the efficacy of physics-informed context-based anomaly detection for power system attacks," IEEE SmartGridComm, 2022.
[31] A. Krishnapriyan, A. Gholami, S. Zhe, R. Kirby, M. W. Mahoney, "Characterizing possible failure modes in physics-informed neural networks," NeurIPS, 2021.
[32] Wang, et al., "When and why PINNs fail to train: a neural tangent kernel perspective," Journal of Computational Physics (arXiv:2007.14527), 2022.
[33] T. Grossmann, U. Komorowska, J. Latz, C. Schönlieb, "Can physics-informed neural networks beat the finite element method?" ICLR, 2024.
[34] M. Z. Naser, "Fundamental flaws of physics-informed neural networks and explainability methods in engineering systems," Computers & Industrial Engineering, 2025.
[35] Ghosh, Zaboli, Hong, Kwon, "A physics-informed context-aware approach for anomaly detection in tele-driving operations under false data injection attacks," arXiv:2410.13962 / IEEE Access, 2025.
[36] Senthilkumar, Anbalagan, "An intrusion detection and defence mechanism for securing autonomous vehicle CAN bus using AI-based homomorphic encryption," Journal of European Des. Syst. Autom. 59:855, 2026.
[37] E. Alsaadi, A. Musuroi, B. Groza, "Privacy-preserving in-vehicle intrusion detection via nearest centroid classification under homomorphic encryption," Applied Sciences 16(18):9204, 2026.
[38] Blevins, et al., "Time-based CAN intrusion detection benchmark," NDSS AutoSec Workshop (arXiv:2101.05781), 2021.
[39] S. Kaufman, S. Rosset, C. Perlich, O. Stitelman, "Leakage in data mining: formulation, detection, and avoidance," ACM TKDD 6(4), 2012.
[40] S. Kapoor, A. Narayanan, "Leakage and the reproducibility crisis in machine-learning-based science," Patterns 4(9), 2023.
[41] D. Arp, E. Quiring, F. Pendlebury, A. Warnecke, F. Pierazzi, C. Wressnegger, L. Cavallaro, K. Rieck, "Dos and don'ts of machine learning in computer security," USENIX Security Symposium, 2022.
[42] D. Arp, E. Quiring, F. Pendlebury, A. Warnecke, F. Pierazzi, C. Wressnegger, L. Cavallaro, K. Rieck, "Pitfalls in machine learning for computer security," Communications of the ACM 67(11), 2024.
[43] S. Axelsson, "The base-rate fallacy and its implications for the difficulty of intrusion detection," ACM Transactions on Information and System Security 3(3), 2000.
[44] N. Tatbul, T. J. Lee, S. Zdonik, M. Alam, J. Gottschlich, "Precision and recall for time series," NeurIPS, 2018.
[45] S. Kim, K. Choi, H.-S. Choi, B. Lee, S. Yoon, "Towards a rigorous evaluation of time-series anomaly detection," AAAI, 2022.
[46] R. Wu, E. J. Keogh, "Current time series anomaly detection benchmarks are flawed and are creating the illusion of progress," IEEE TKDE (arXiv:2009.13807), 2020/2022.
[47] Shin, Lee, Yun, Kim, "HAI 1.0: HIL-based augmented ICS security dataset," USENIX CSET, 2020.
[48] D. Sobrín Hidalgo, "Simulated attacks Rosbags against mobile robot in ROS 2," Zenodo, DOI 10.5281/zenodo.17649537, 2025.
[49] Fraga Da Silva, Santoso, Zheng, "A deep learning-based intrusion detection system for safeguarding ROS 2-powered unmanned ground vehicles against DoS attacks," IEEE IJCNN, 2025.
[50] Fraga Da Silva, Santoso, Zheng, "Physics-based attack detection for ROS 2 robotic systems: a survey of physics-based validation and open challenges," IEEE Open Journal of the Industrial Electronics Society, 2026.

---

### Addendum (2026-11-03): early foundations and 2025-2026 update

Supplement scout rounds (verified via Crossref/arXiv/publisher retrieval; same protocol).

**Early foundations (2007–2017).** The masquerade concept traces to Hoppe & Dittmann's 2007 work on faking in-vehicle CAN communication [51], with practical attacks and first IDS proposals in Hoppe et al. [52]; the vehicle-threat roadmap starts with Larson & Nilsson [53] and Wampler et al. [54]; the canonical experimental compromise is Koscher et al., IEEE S&P 2010 [55] (note: this title is Koscher et al., not Miller–Valasek); Kleberger et al. wrote the widely cited early survey [56]; Müter & Asaj's entropy IDS [57] is the earliest statistical CAN detector (sibling of [13]); Miller & Valasek's public tooling [58], [59] industrialized the threat; sequence-based detection arrives with Taylor et al.'s LSTM [60] and Markovitz & Wool's per-field statistical models [61]. No pre-2017 physics-based CAN IDS was found — the analytical lineage (Section 5.1) genuinely starts at CAID [14].

**2025–2026 update.** Serag et al.'s SoK (arXiv:2510.02960, NDSS 2027 to appear) systematizes CAN security knowledge and becomes the taxonomy to position against [62]. Physics-informed detection exists at the sector's edges but not on CAN frames: Philip et al. apply physics-informed temporal learning to vehicle *platoons* (simulation) [63] and Bourouis et al. build a physics-informed edge IDS for IoV *BSM* misbehavior [64]; PCNA-IDS [65] and ACHILLES [66] are data-driven (ACHILLES benchmarks across ROAD and others, masquerade coverage unconfirmed). Longari et al. document adversarial evasion of CAN IDS [67], and Althunayyan et al. survey learning-based automotive IDS with masquerade-type stealth coverage [68]. **Threat assessment: no work occupies physics-residual × ROAD masquerade × external-baseline ablation.** Design implication adopted: the ablation ladder must include the four external unsupervised baselines that Moriano et al. replay on ROAD masquerade [4].

[51] Hoppe, Dittmann, "Vortäuschen fahrzeuginterner CAN-Kommunikation," VDI/VW Automotive Security, 2007.
[52] Hoppe, Kiltz, Dittmann, "Security threats to automotive CAN networks — practical examples and selected short-term countermeasures," SAFECOMP (RESS journal version 2011), 2008.
[53] Larson, Nilsson, "Securing vehicles against cyber attacks," CSIIRW, ACM, 2008.
[54] Wampler, Fu, Zhu, et al., "Security threats and countermeasures for intra-vehicle networks," IEEE IAS, 2009.
[55] Koscher, Czeskis, Roesner, et al., "Experimental security analysis of a modern automobile," IEEE S&P, 2010.
[56] Kleberger, Olovsson, Jonsson, "Security aspects of the in-vehicle network in the connected car," IEEE Intelligent Vehicles Symposium, 2011.
[57] Müter, Asaj, "Entropy-based anomaly detection for in-vehicle networks," IEEE Intelligent Vehicles Symposium, 2011.
[58] Miller, Valasek, "Adventures in automotive networks and control units," DEF CON 21 / IOActive, 2013.
[59] Miller, Valasek, "A survey of remote automotive attack surfaces," Black Hat USA / IOActive, 2014.
[60] Taylor, Leblanc, Japkowicz, "Anomaly detection in automobile control network data with LSTM networks," IEEE DSAA, 2016.
[61] Markovitz, Wool, "Field classification, modeling and anomaly detection in unknown CAN bus networks," Vehicular Communications, 2017.
[62] Serag, et al., "SoK: kicking CAN down the road — systematizing CAN security knowledge," arXiv:2510.02960 (NDSS 2027 to appear), 2025.
[63] Philip, et al., "Physics-informed temporal learning for cyber attack detection in vehicle platoons," IEEE ISI, 2026.
[64] Bourouis, et al., "Temporal-window-aware physics-informed edge IDS for multi-class IoV misbehavior detection," Vehicles 8(9):215, 2026.
[65] Qu, et al., "PCNA-IDS: an integrated lightweight intrusion detection system in Internet of Vehicles with federated contrastive learning and differential privacy," Knowledge-Based Systems 336:115346, 2026.
[66] Mowla, et al., "ACHILLES: a machine learning framework for explainable and generalized automotive intrusion detection system," IEEE Access, 2026.
[67] Longari, et al., "Assessing the resilience of automotive intrusion detection systems to adversarial manipulation," ACM (arXiv:2506.10620), 2025.
[68] Althunayyan, et al., "A survey of learning-based intrusion detection systems for in-vehicle network," arXiv:2505.11551, 2025.

---

### Verification ledger (working-document appendix)

Corpus provenance: two verification scouts (CAN/ICS prior art; datasets + evaluation norms), plus direct retrieval of the flagged cPINN-CAN threat (full text of [37], which resolves [36]) and cover-to-cover reads of [7], [6], [8] (local PDFs in `docs/papers/`). Domain-generic references ([25]–[34], [39]–[46]) carried over from the previous survey round, where each was individually verified. Metadata-level items pending direct retrieval: [36] (verified only as described in [37]'s reference list and related-work section — retrieve before writing), [12] (title from dataset page + catalog records), [11] (authors/venue verified; title from common citation practice). Excluded as unverifiable: "Temporal-Window-Aware Physics-Informed Edge IDS for Multi-Class IoV" (snippet only), M-CAN/B-CAN/can-train-and-test (partial provenance only), WeepingCAN/MAuth-CAN (snippet level). Known caveats carried into claims: ROAD masquerade captures are simulated post-processing and the vehicle ran on a dynamometer [1]; ROAD frame order is intentionally obfuscated (timing caveat) [1].
