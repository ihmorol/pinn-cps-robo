"""M3 stage 1: D0a range, D0b const-run, D1 physics — frame-level on attacked-ID streams."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.detectors import ambient_reference, score_range, score_physics, _roll_std
from pinn_cps_robo.evaluate import ap_score, threshold_at, recall_fpr

ROAD = Path(sys.argv[1])
Q = 0.999
CLASS_STREAM = {"correlated": "wheel", "max_speedometer": "speedo", "reverse_light": "speedo",
                "max_engine_coolant": "coolant", "accelerator": "wheel"}
RUN_SIG = {"wheel": "s1", "speedo": "s6", "coolant": "s2"}


def runs(v):
    v = np.asarray(v, dtype=float)
    run = np.ones(len(v))
    for i in range(1, len(v)):
        if v[i] == v[i - 1]:
            run[i] = run[i - 1] + 1
    return run


def stream_scores(fr, ref, stream):
    out = {}
    out["D0a_range"] = score_range(fr, ref, stream)
    sig = RUN_SIG[stream]
    r = runs(fr[sig].to_numpy(dtype=float))
    out["D0b_construn"] = r / max(ref[f"max_run_{stream}"], 1.0)
    out["D1_physics"] = score_physics(fr, ref, stream, cap_frames=fr)
    return out


def main():
    # ambient reference + ambient scores
    ref = {}
    amb_scores = {"D0a_range": [], "D0b_construn": [], "D1_physics": []}
    amb_frames = {k: [] for k in ("wheel", "speedo", "coolant")}
    for cap in list_captures(ROAD, "ambient"):
        fr = load_capture(cap)
        for k in amb_frames:
            if len(fr[k]):
                amb_frames[k].append(fr[k])
    merged = {k: pd.concat(v, ignore_index=True).sort_values("t").reset_index(drop=True)
              for k, v in amb_frames.items() if v}
    ref = ambient_reference(merged)
    for stream in ("wheel", "speedo", "coolant"):
        if stream not in merged or not len(merged[stream]):
            continue
        # per-capture ambient scores (avoid cross-capture run/interp artifacts)
        for cap in list_captures(ROAD, "ambient"):
            fr = load_capture(cap)
            if not len(fr[stream]):
                continue
            ss = stream_scores(fr, ref, stream)
            for k, v in ss.items():
                amb_scores[k].append(pd.Series(v, index=fr[stream].index).dropna().to_numpy())
    amb_flat = {k: np.concatenate(v) for k, v in amb_scores.items()}
    ref["max_run_wheel"] = 1.0
    # ambient max run per stream/signal (for D0b normalization)
    for stream in ("wheel", "speedo", "coolant"):
        if stream in merged and len(merged[stream]):
            ref[f"max_run_{stream}"] = float(runs(merged[stream][RUN_SIG[stream]].to_numpy(dtype=float)).max())
    thr = {k: threshold_at(v, Q) for k, v in amb_flat.items()}
    print("ambient frames:", {k: len(v) for k, v in amb_flat.items()})
    print("thresholds(q0.999):", {k: round(v, 3) for k, v in thr.items()})

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
            s = pd.Series(s, index=f.index).dropna()
            yy = y[[f.index.get_loc(i) for i in s.index]] if len(s) != len(f) else y
            ap = ap_score(yy, s.to_numpy())
            rec, fpr = recall_fpr(yy, s.to_numpy(), thr[det])
            rows.append((cap.stem, cls, det, ap, rec, fpr, int(len(s)), int(yy.sum())))

    res = pd.DataFrame(rows, columns=["capture", "class", "detector", "AP", "recall@thr", "FPR_benign", "n", "n_attack"])
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / "stage1.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print("\n=== per class x detector (pooled over captures) ===")
    for cls in res["class"].unique():
        sub = res[res["class"] == cls]
        for det in ["D0a_range", "D0b_construn", "D1_physics"]:
            r = sub[sub["detector"] == det]
            if len(r):
                print(f"{cls:20s} {det:14s} AP={r.AP.mean():.4f} recall={r['recall@thr'].mean():.4f} "
                      f"FPR_benign={r.FPR_benign.mean():.5f} n={int(r.n.sum())}")


if __name__ == "__main__":
    main()
