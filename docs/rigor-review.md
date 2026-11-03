# Rigor self-review — 2026-11-03

Adversarial audit of the full project (code, experiments, statistics, paper) using the six rigor dimensions: evidence relevance, falsifiability, scope calibration, argument coherence, exploration integrity, methodological rigor. Every finding below was either fixed or explicitly accepted with justification. Test suite after fixes: **9/9 passing**.

## Findings and dispositions

| ID | Dim | Severity | Finding | Disposition |
|---|---|---|---|---|
| F01 | rigor | **major → fixed** | M4 attribution (the paper's headline negative) was **single-seed**; the "twin edges ahead at 0.1%" observation was seed noise | Re-ran 5 seeds × {0.1%, 100%} × {twin, PINN}: exact parity (0.7062±0.0013 vs 0.7061±0.0012; 0.7114±0.0049 vs 0.7113±0.0041). Paper §6 + Fig 3 caption corrected |
| F02 | scope | **major → fixed** | Abstract/intro claimed "recall 1.0 at a 0.1% ambient false-positive rate" — 0.1% is the *calibration quantile*; measured benign-frame FP rates on attack captures were 0–0.46% | Both drafts reworded; measured rates stated explicitly |
| F03 | evidence | **major → verified safe** | The coolant envelope claim (255 vs 151) compares masquerade-family decoding against an ambient-family envelope — the 0x4e7 bit layouts were never validated cross-family | Solved both layouts empirically: **sig2 (the temperature channel) is identical (16\|8) in both families** — the claim stands; the unused sig1 differs (6 vs 5 bits), logged as further DBC-integrity evidence |
| F04 | scope | minor → fixed | "Only 4 of 65 papers evaluate against any baseline" was attributed to [1] with a duplicated citation marker; the underlying source is Rajbahadur et al.'s survey (metadata-level) | Reworded to "As cataloged in [1]…", duplicate removed; tracker note added |
| F05 | integrity | strength | Failure documentation predates this review: decoder validation gates, the broken binary freeze law, the fig5 leakage trap — all caught by gates/logs before reaching the paper | — |
| F06 | rigor | minor → fixed | `detectors.py` had zero test coverage | Added 4 tests (envelope flagging, physics payload detection, ambient floors, rolling-std equivalence); suite 9/9 |
| F07 | rigor | minor → accepted | D0b's max-run floor was computed on concatenated ambient frames (cross-capture runs) | The "D0b is dead" conclusion is robust to either accounting (within-capture max ≈ 42k vs 106k, both ≫ attack runs); left as-is |
| F08 | integrity | major → fixed | A pooled PR-curve figure mixed RF's training captures into its test pool (AP inflated 0.37 → 0.98) | Caught during figure generation, discarded before touching the paper; rule adopted: PR curves must respect splits |
| F09 | scope | suggestion | Negative attribution scoped to soft-constraint one-step formulation; structural encodings untested | Already declared in §7 |
| F10 | rigor | minor → accepted | `run_delay.py` contains a leftover `meta = json = None` line (cosmetic) | — |

## Dimension scores (calibrated)

| Dimension | Score | Basis |
|---|---|---|
| Evidence relevance | 4/5 | All claims map to executed experiments; coolant cross-family check was missing until F03 |
| Falsifiability | 4/5 | Every experiment pre-registered with predictions; P4 was self-rejected, P2/P7/P8 rejected — falsification practiced, not just declared |
| Scope calibration | 4/5 | F02 fixed; claims now carry measured rates and formulation scope |
| Argument coherence | 4/5 | Taxonomy → ladder → boundary → attribution arc holds; negative result integrated as first-class |
| Exploration integrity | 5/5 | 6 pre-registered experiments, 4 rejected predictions, 2 failed approaches on the evading class, all logged |
| Methodological rigor | 4/5 | Ambient-only calibration, capture-disjoint splits, per-class reporting, detection delay; F01 variance now reported |

**Overall: 4.2/5 — Accept band.** Remaining known limitations are declared in the paper (§7) rather than discovered by reviewers.

## Verification commands

- `python -m pytest tests/` — 9 passed
- `python -I experiments/m4-attribution/run_m4.py data/... 1.0 0.001,1.0 SEED` — per-seed attribution
- `python -I experiments/m2b-fabrication/run_m2b.py data/...` — decoder validation gate + fabrication taxonomy
