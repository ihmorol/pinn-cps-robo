"""Context-consistency detection of the reverse-light bit (per protocol.md)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.evaluate import ap_score, threshold_at, recall_fpr

ROAD = Path(sys.argv[1])
Q = 0.999
MARGIN = 0.05
SPECS = {208: [(59, 4), (48, 10), (43, 1), (33, 2), (24, 8), (8, 14), (0, 1)],
         1760: [(48, 14), (32, 14), (16, 14), (0, 14)],
         1255: [(32, 5), (16, 8)]}
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments/m2b-fabrication"))
from run_m2b import parse_log  # noqa: E402


def context_features(f, wf):
    """Live signals of 0xd0 + wheel state interpolated onto its timeline."""
    X = f[["s1", "s2", "s4", "s5", "s6", "s7"]].to_numpy(dtype=float)
    if wf is not None and len(wf):
        wt = wf["t"].to_numpy()
        W = wf[["s1", "s2", "s3", "s4"]].to_numpy(dtype=float)
        wm = W.mean(axis=1)
        wsi = np.interp(f["t"].to_numpy(), wt, W.std(axis=1))
        wmi = np.interp(f["t"].to_numpy(), wt, wm)
        X = np.hstack([X, wmi.reshape(-1, 1), wsi.reshape(-1, 1)])
    else:
        X = np.hstack([X, np.zeros((len(f), 2))])
    return X


def main():
    from sklearn.ensemble import GradientBoostingClassifier

    # ambient train/test (temporal 50/50 per capture) + wheel frames for context
    amb = []
    for cap in list_captures(ROAD, "ambient"):
        if not cap.stem.startswith("ambient_"):
            continue
        fr = load_capture(cap)
        amb.append(fr)
    # use CSV-decoded ambient (validated pipeline)
    tr_X, tr_y, te_X, te_y = [], [], [], []
    for i, fr in enumerate(amb):
        f = fr["speedo"]
        if not len(f):
            continue
        X = context_features(f, fr["wheel"])
        y = f["s3"].to_numpy(dtype=int)
        if i % 2 == 0:
            tr_X.append(X); tr_y.append(y)
        else:
            te_X.append(X); te_y.append(y)
    Xtr, ytr = np.vstack(tr_X), np.concatenate(tr_y)
    Xte, yte = np.vstack(te_X), np.concatenate(te_y)

    clf = GradientBoostingClassifier(random_state=0)
    clf.fit(Xtr, ytr)
    p_amb = clf.predict_proba(Xte)[:, 1]
    amb_ap = ap_score(yte, p_amb)
    print(f"ambient context-predictability of the light bit: AP={amb_ap:.4f} "
          f"(base rate {yte.mean():.4f})")
    if amb_ap <= 0.9:
        print("P8 branch: bit not context-determined — class stays open (per protocol)")
        return

    thr = threshold_at(np.abs(yte - p_amb), Q)

    rows = []
    for cap in list_captures(ROAD, "attacks"):
        if not (cap.stem.startswith("reverse_light") or cap.stem.startswith("max_engine_coolant")):
            continue
        if cap.stem.endswith("_masquerade"):
            fr = load_capture(cap)  # CSV-decoded
            f = fr["speedo"]
            wf = fr["wheel"]
        else:
            fr = parse_log(ROAD / "attacks" / f"{cap.stem}.log", SPECS)
            for k in fr:
                if len(fr[k]):
                    fr[k]["t"] -= fr[k]["t"].iloc[0]
            f = fr[208]
            wf = fr[1760]
        if not len(f) or f["label"].sum() == 0:
            continue
        X = context_features(f, wf)
        y = f["label"].to_numpy(dtype=int)
        s = None
        if "speedo" in cap.stem or cap.stem.startswith("reverse_light"):
            p = clf.predict_proba(X)[:, 1]
            s = np.abs(f["s3"].to_numpy(dtype=float) - p)
        rows.append((cap.stem, ap_score(y, s), *recall_fpr(y, s, thr), len(s)))

    res = pd.DataFrame(rows, columns=["capture", "AP", "recall@thr", "FPR", "n"])
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / "bitctx.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print(res.to_string(index=False))
    print("\npooled: AP=%.4f recall=%.4f" % (
        res.AP.mean(), res["recall@thr"].mean()))


if __name__ == "__main__":
    main()
