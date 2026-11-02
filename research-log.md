# Research log (append-only)

## 2026-11-02 — kickoff (ROS 2 era)
- ROS 2 project scoped, surveyed, dataset inspected; feasibility confirmed.

## 2026-11-03 — domain pivot to CAN/ROAD
- Verified gap (2 scout rounds + cPINN threat resolved); pivoted primary domain to ROAD masquerade. ROS 2 = optional RQ4 validation.
- ROS 2 artifacts removed per owner; docs rebuilt for CAN/ROAD.
- GitHub repo created: https://github.com/ihmorol/pinn-cps-robo (public). Initial commit `research(init)`.
- Autoresearch loop created (cron, 20 min). ROAD downloaded (556.7 MB), md5 verified `cab184cfc2fe12c0834bc46188c0f330`, extracted (206 files).
- **Signal map recovered from `attacks/metadata.json` injection IDs: `0x6e0`=4×wheel speeds, `0xd0`=speedometer+reverse light, `0x4e7`=coolant temp. All 13 masquerade captures pre-decoded with per-row labels — no raw-log decoding needed for the core experiment.**
- Next: empirical verification of the map in decoded CSVs → tidy panel (M1) → ambient envelopes + per-attack physics taxonomy (M2).

## 2026-11-03 (tick 2) — literature supplement + M1 verified
- Early foundations scout: 11 verified works (2007-2017); correction: "Experimental Security Analysis of a Modern Automobile" = Koscher et al. 2010 (S&P), not Miller-Valasek. No pre-2017 physics-based CAN IDS — analytical lineage starts at CAID 2017 (claim holds).
- 2025-2026 scout: 10 verified works; novelty threat assessment NEGATIVE (nothing occupies physics-residual + ROAD masquerade + external-baseline ablation). Design implication adopted: include Moriano et al. 2026's four unsupervised baselines in the ablation ladder. SoK (NDSS 2027) = taxonomy to position against.
- Tracker now 68 entries (S01-S68). Survey updated with addendum [51]-[68].
