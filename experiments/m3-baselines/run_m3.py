"""M3 stage 1: D0a range, D0b const-run, D1 physics — frame-level, per-stream thresholds.

v3 refinements (logged): ambient floors computed within each capture then
aggregated (cross-capture ops are meaningless — t restarts); L2d dynamics law
(|ds6 - a*dwm|) replaces the failed binary freeze law; per-stream thresholds.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.detectors import ambient_reference, score_range, score_physics
from pinn_cps_robo.evaluate import ap_score, threshold_at, recall_fpr

ROAD = Path(sys.argv[1])
Q = 0.999
CLASS_STREAM = {"correlated": "wheel", "max_speedometer": "speedo", "reverse_light": "speedo",
                "max_engine_coolant": "coolant", "accelerator": "wheel"}
RUN_SIG = {"wheel": "s1", "speedo": "s6", "coolant": "s2"}
STREAMS = ("wheel", "speedo", "coolant")


def runs(v):
    v = np.asarray(v, dtype=float)
    run = np.ones(len(v))
    for i in range(1, len(v)):
        if v[i] == v[i - 1]:
            run[i] = run[i - 1] + 1
    return run


def stream_scores(fr, ref, stream):
    f = fr[stream]
    out = {}
    out["D0a_range"] = score_range(f, ref, stream)
    sig = RUN_SIG[stream]
    r = runs(f[sig].to_numpy(dtype=float))
    out["D0b_construn"] = r / max(ref[f"max_run_{stream}"], 1.0)
    out["D1_physics"] = score_physics(f, ref, stream, cap_frames=fr)
    return out


def main():
    amb_frames = {k: [] for k in STREAMS}
    amb_caps = []
    for cap in list_captures(ROAD, "ambient"):
        if not cap.stem.startswith("ambient_"):
            continue  # ambient/ duplicates attack captures; the 12 ambient_* files are calibration
        fr = load_capture(cap)
        amb_caps.append(fr)
        for k in STREAMS:
            if len(fr[k]):
                amb_frames[k].append(fr[k])
    ref = ambient_reference(amb_caps)
    print("ref:", {k: (round(v, 4) if isinstance(v, float) else v)
                   for k, v in ref.items() if k.startswith(("floor", "alpha", "motion", "speedo_std", "max_run"))})

    # per-stream ambient scores -> per-stream thresholds
    amb_scores = {det: {s: [] for s in STREAMS} for det in ("D0a_range", "D0b_construn", "D1_physics")}
    for fr in amb_caps:
        for s in STREAMS:
            if not len(fr[s]):
                continue
            for det, v in stream_scores(fr, ref, s).items():
                amb_scores[det][s].append(pd.Series(v, index=fr[s].index).dropna().to_numpy())
    thr = {det: {s: threshold_at(np.concatenate(v), Q) if v else np.inf
                 for s, v in d.items()} for det, d in amb_scores.items()}
    n_amb = {s: sum(len(v) for v in amb_scores["D0a_range"][s]) for s in STREAMS}
    print("ambient frames per stream:", n_amb)
    print("thresholds(q0.999):", {d: {s: round(x, 4) for s, x in t.items()} for d, t in thr.items()})

    rows = []
    for cap in list_captures(ROAD, "attacks"):
        cls = next((c for c in CLASS_STREAM if cap.stem.startswith(c)), None)
        if cls is None or cls == "accelerator":
            continue
        stream = CLASS_STREAM[cls]
        fr = load_capture(cap)
        f = fr[stream]
        if not len(f) or f["label"].sum() == 0:
            continue
        ss = stream_scores(fr, ref, stream)
        y = f["label"].to_numpy(dtype=int)
        for det, s in ss.items():
            sv = pd.Series(s, index=f.index).dropna()
            yy = y[[f.index.get_loc(i) for i in sv.index]]
            ap = ap_score(yy, sv.to_numpy())
            rec, fpr = recall_fpr(yy, sv.to_numpy(), thr[det][stream])
            rows.append((cap.stem, cls, det, ap, rec, fpr, int(len(sv)), int(yy.sum())))

    res = pd.DataFrame(rows, columns=["capture", "class", "detector", "AP", "recall@thr", "FPR_benign", "n", "n_attack"])
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / "stage1.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print("\n=== per class x detector (pooled over captures) ===")
    for cls in sorted(res["class"].unique()):
        for det in ["D0a_range", "D0b_construn", "D1_physics"]:
            r = res[(res["class"] == cls) & (res["detector"] == det)]
            if len(r):
                print(f"{cls:20s} {det:14s} AP={r.AP.mean():.4f} recall={r['recall@thr'].mean():.4f} "
                      f"FPR_benign={r.FPR_benign.mean():.5f} n={int(r.n.sum())}")


if __name__ == "__main__":
    main()
