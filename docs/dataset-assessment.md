# Dataset Assessment — ROAD (Zenodo 10462796)

**Status: VIABLE — primary dataset selected. Download and signal-mapping pending (M1-CAN).**
Assessed 2026-11-03 from verified metadata (Zenodo record, official project page, the PLOS ONE guide [read in full], and the CAN-MIRGU / AutoHack / can-sleuth papers [local PDFs in `docs/papers/`]). Direct bag/signal inspection happens in M1-CAN and will update this note.

---

## 1. Provenance

| Field | Value |
|---|---|
| Title | Real ORNL Automotive Dynamometer (ROAD) CAN Intrusion Dataset |
| Publisher | Oak Ridge National Laboratory (DOE Contract DE-AC05-00OR22725) |
| Published | 2020-12-28 (v1 modified 2024-01-05) |
| DOI | Zenodo `10.5281/zenodo.10462796` (concept `...10462795`); ORNL DOI `10.13139/ORNLNCCS/1728694` |
| License | **CC BY 4.0 — direct download, no registration** |
| Size | `road.zip` **556.7 MB**, md5 `cab184cfc2fe12c0834bc46188c0f330` |
| Describing paper | Verma et al., "A comprehensive guide to CAN IDS data and introduction of the ROAD dataset," PLOS ONE 19(1):e0296879, 2024 (arXiv:2012.14600) |
| Vehicle | withheld ("mid 2010s"); logged at the **OBD-II port** via SocketCAN + Kvaser Leaf Light V2, can-utils `candump` format |
| Coverage | 3 h 27 m total: **33 attack captures (~30 min attack duration) + 12 ambient captures (~3 h)**; attacks "physically verified on the vehicle" |

## 2. Contents and formats

Three representations per capture:
1. **Raw SocketCAN `.log`** (candump format) — not per-message labeled.
2. **CSV signal time series** — produced with the CAN-D decoder for **17 of 33 attack captures and all 12 ambient captures**; columns `Label, ID, Time, Signal-<i>-of-ID`; **per-row label 0/1**. ⚠️ Signal names are **index-based** — semantic mapping (which index = wheel speed etc.) must be done by inspection (M1-CAN).
3. **JSON metadata** per capture — description, duration, dynamometer flag; for attacks: injection ID, injected data (wildcard "X" = unmodified bytes), and **injection interval (start, end)**.

### Attack classes (33 captures)
- Fuzzing ×3 (random IDs / max payload / 0.005 s periodicity)
- Targeted ID fabrication ("flam" delivery — "most stealthy fabrication possible in public data")
- **Correlated signal fabrication ×3 + Masquerade ×3** — four false wheel-speed values
- Max speedometer fabrication ×3 + Masquerade ×3
- Max engine coolant temp fabrication ×1 + Masquerade ×1
- Reverse light off/on fabrication ×3+3 + Masquerade ×3+3
- Accelerator attack (Drive ×2, Reverse ×2) — a disclosed real vulnerability with **no injected frames**

**13 masquerade captures total.** Masquerade = simulated post-processing: legitimate frames are suspended and fabricated ones sent at the expected frequency ("spoofed frames sent in lieu of suspended ones"). They "do not cause perceptible timing changes" — the dataset's authors state frequency-based approaches "will almost certainly fail" on them.

### Physics channels (verified present in decoded CSVs)
Four wheel speeds (one ID, four 2-byte signals), speedometer, engine coolant temperature, reverse light state. Steering angle / brake / IMU: **not present** in what has been verified — design uses wheel-speed/speedometer/temp relations only.

## 3. Known caveats (must shape claims and protocol)

1. **Frame order intentionally obfuscated** — "intentional changes were made to the order of CAN frames, resulting in the removal of priority information" (CAN-MIRGU's critique; confirmed in the ROAD guide). Timing/rate detectors are handicapped *by the dataset's own design*. → Report detector-0 results under this handicap explicitly; use AutoHack (intact timing, real driving) as the cross-dataset honesty check.
2. **Masquerade captures are simulated post-processing** — claims must say "published masquerade captures," not real-road masquerade attacks.
3. **Data obfuscation** — timestamps shifted, IDs anonymized, data fields scrambled, filler messages inserted, diagnostic IDs removed. Consequence: no absolute physical units guarantee (e.g., speed scaling must be identified from ambient data, which is fine for residual-based detection).
4. **Only 17/33 attack captures pre-decoded** — if masquerade captures are not among the 17, decode the raw `.log` files using the JSON attack intervals (CPU-feasible; CAN-D or `python-can`/`cantools`).
5. **Dynamometer-only attack collection** (ambient includes 2 road captures) — driving-profile diversity is limited; benign-envelope estimation must respect that.

## 4. Fitness for the project's RQs

| RQ | Supported by ROAD? | Notes |
|---|---|---|
| RQ1 physics taxonomy | ✅ | correlated-fabrication vs single-signal fabrication vs masquerade classes give a natural gradient of physical consistency |
| RQ2 physics-vs-data detection | ✅ | per-row labels + intervals → AUC-PR, per-class recall, detection delay all computable; frequency detectors documented to fail on masquerade |
| RQ3 attribution ablation | ✅ | ambient captures (incl. road driving) provide benign-envelope + FP stress material |
| RQ4 ROS 2 cross-domain (optional) | separate dataset | Zenodo 17649537, re-downloadable; prior analysis exists (git history) |

**Verdict: GO.** All four constraints (public data, no hardware, no new attacks, CPU-scale) are satisfied; the decoded CSVs alone (17 attack + 12 ambient captures) may suffice without touching the raw logs.

## 5. M1-CAN checklist (next step)

1. Download `road.zip` into `data/raw/zenodo-10462796/` (quarantine), verify md5, extract.
2. Inventory the JSON metadata: which captures are masquerade; are they among the 17 decoded?
3. Map `Signal-<i>-of-ID` columns to semantics by inspection: identify the wheel-speed ID (four 2-byte signals), speedometer ID, coolant-temp ID; identify scaling using ambient captures (obfuscated units).
4. Cross-check ambient inter-wheel/speedometer consistency (establish residual envelopes).
5. If needed: decode raw `.log` for the missing captures.
6. Output: tidy per-capture panel (`data/processed/`), mapping table in this note.

## 6. Complementary datasets (tracked, not primary)

| Dataset | Use | Access |
|---|---|---|
| AutoHack (USENIX VehicleSec 2026) | intact-timing honesty check (C-D); real driving | Zenodo 20321379, CC BY 4.0, direct (raw frames only) |
| CAN-MIRGU (VehicleSec 2024) | backup; steering/brake channels, real-road benign | GitHub (per paper), per-frame labels |
| SynCAN (ETAS) | unit tests of the pipeline only — synthetic | github.com/etas/SynCAN (non-commercial license) |
| HAI (ICS fallback) | fallback domain if CAN collapses | github.com/icsdataset/hai, git clone |
