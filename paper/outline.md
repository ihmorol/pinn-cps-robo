# Paper — working folder

Writing workflow: drafts get written with the paper-writing skill and then pass through the humanizer skill (owner's voice: short sentences, direct claims, no AI-isms — no em-dash piles, no "testament/pivotal/landscape", no rule-of-three).

## Target

Working title: "The Wheels Tell the Truth: Physics-Residual Detection of Masquerade Attacks on CAN"
Venue shortlist: NDSS AutoSec → USENIX VehicleSec → JISA / Computers & Security. arXiv preprint as soon as M2+M3 results exist.

## Outline (skeleton, fills as results land)

1. Introduction — masquerade attacks defeat frequency/payload detectors; the wheels are bound by kinematics; we watch the relations. Contribution list (3 items max).
2. Background & related work — from literature-review.md; position vs [Marfo TIFS'25], [Moriano '22/'26], [Rahman '26].
3. Physics model — the three consistency laws (inter-wheel, speedometer-wheel, temporal continuity); envelope identification from ambient.
4. Physics taxonomy of ROAD attacks (RQ1) — which law each attack class violates. Table.
5. Detector ladder & protocol (RQ2/RQ3) — ladder table; AUC-PR, per-class recall, session splits, FPR at operating point.
6. Results — main table + FP-on-benign table + delay.
7. Discussion — what physics can't catch (flam-class), ROAD obfuscation caveat, limitations.
8. Conclusion.

## Assets

- findings.md → feeds sections 4-6.
- research-log.md → feeds the reproducibility statement.
- Cross-domain (ROS 2) → one paragraph in Discussion if RQ4 runs.
