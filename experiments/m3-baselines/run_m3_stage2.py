"""M3 stage 2: D4 RF/XGBoost (capture-disjoint supervised) + D5 one-class AE."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.evaluate import ap_score, threshold_at, recall_fpr

ROAD = Path(sys.argv[1])
Q = 0.999
CLASS_STREAM = {"correlated": "wheel", "max_speedometer": "speedo", "reverse_light": "speedo",
                "max_engine_coolant": "coolant"}
NSIG = {"wheel": 4, "speedo": 7, "coolant": 2}
RUN_SIG = {"wheel": "s1", "speedo": "s6", "coolant": "s2"}


def features(f, stream):
    """Windowed features: raw signals + rolling mean/std (10 frames)."""
    cols = [f"s{i+1}" for i in range(NSIG[stream])]
    X = [f[cols].to_numpy(dtype=float)]
    for c in cols:
        v = f[c].to_numpy(dtype=float)
        s = pd.Series(v)
        X.append(s.rolling(10, min_periods=1).mean().to_numpy().reshape(-1, 1))
        X.append(s.rolling(10, min_periods=1).std().fillna(0).to_numpy().reshape(-1, 1))
    return np.hstack(X)


def main():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    try:
        from xgboost import XGBClassifier
        HAS_XGB = True
    except ImportError:
        HAS_XGB = False

    amb = {s: [] for s in NSIG}
    for cap in list_captures(ROAD, "ambient"):
        if not cap.stem.startswith("ambient_"):
            continue
        fr = load_capture(cap)
        for s in NSIG:
            if len(fr[s]):
                amb[s].append(fr[s])

    rows = []
    for cls, stream in CLASS_STREAM.items():
        caps = {c.stem: c for c in list_captures(ROAD, "attacks") if c.stem.startswith(cls)}
        frames = {n: load_capture(p)[stream] for n, p in caps.items()}
        sig = RUN_SIG[stream]
        # ambient train/test benign (temporal 50/50 within each ambient capture)
        Xa = np.vstack([features(f, stream) for f in amb[stream]])
        Xa_tr, Xa_te = Xa[::2], Xa[1::2]
        ya_tr = np.zeros(len(Xa_tr), dtype=int)

        stems = sorted(frames)
        if cls == "max_engine_coolant":
            f = frames[stems[0]]
            lab1 = f[f.label == 1]
            k = int(0.6 * len(lab1))
            train_frames, test_frames = [lab1.iloc[:k]], [f]  # test = whole capture, train = first 60% of attacks
            y_test = test_frames[0]["label"].to_numpy(dtype=int)
        else:
            train_frames = [frames[s] for s in stems[:2]]
            test_frames = [frames[stems[-1]]]
            y_test = test_frames[0]["label"].to_numpy(dtype=int)

        Xtr = np.vstack([features(f, stream) for f in train_frames])
        ytr = np.concatenate([f["label"].to_numpy(dtype=int) for f in train_frames])
        Xte = np.vstack([features(f, stream) for f in test_frames])

        # benign test pool = held-out ambient + label-0 frames of test captures
        Xb_te = np.vstack([Xa_te] + [features(f[f.label == 0], stream) for f in test_frames if (f.label == 0).any()])
        yb_te = np.zeros(len(Xb_te), dtype=int)

        # D4a RF
        rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", n_jobs=-1, random_state=0)
        rf.fit(np.vstack([Xa_tr, Xtr]), np.concatenate([ya_tr, ytr]))
        s_pos = rf.predict_proba(Xte)[:, 1]
        s_ben = rf.predict_proba(Xb_te)[:, 1]
        thr = threshold_at(s_ben, Q)
        rec, fpr = recall_fpr(np.concatenate([y_test, yb_te]), np.concatenate([s_pos, s_ben]), thr)
        rows.append((cls, "D4a_rf", ap_score(y_test, s_pos), rec, fpr, len(Xte)))

        # D4b XGB
        if HAS_XGB:
            spw = (len(ytr) - ytr.sum()) / max(ytr.sum(), 1)
            xgb = XGBClassifier(n_estimators=300, max_depth=6, scale_pos_weight=spw,
                                random_state=0, n_jobs=-1, eval_metric="logloss")
            xgb.fit(np.vstack([Xa_tr, Xtr]), np.concatenate([ya_tr, ytr]))
            s_pos = xgb.predict_proba(Xte)[:, 1]
            s_ben = xgb.predict_proba(Xb_te)[:, 1]
            thr = threshold_at(s_ben, Q)
            rec, fpr = recall_fpr(np.concatenate([y_test, yb_te]), np.concatenate([s_pos, s_ben]), thr)
            rows.append((cls, "D4b_xgb", ap_score(y_test, s_pos), rec, fpr, len(Xte)))

        # D5 one-class AE on ambient only
        n_train = min(len(Xa_tr), 200_000)
        rng = np.random.default_rng(0)
        idx = rng.choice(len(Xa_tr), n_train, replace=False)
        sc = StandardScaler().fit(Xa_tr[idx])
        ae = MLPRegressor(hidden_layer_sizes=(32, 16, 32), max_iter=30, early_stopping=True,
                          random_state=0)
        ae.fit(sc.transform(Xa_tr[idx]), Xa_tr[idx])
        rec_err = lambda X: ((ae.predict(sc.transform(X)) - X) ** 2).mean(axis=1)
        s_pos, s_ben = rec_err(Xte), rec_err(Xb_te)
        thr = threshold_at(s_ben, Q)
        rec, fpr = recall_fpr(np.concatenate([y_test, yb_te]), np.concatenate([s_pos, s_ben]), thr)
        rows.append((cls, "D5_ae", ap_score(y_test, s_pos), rec, fpr, len(Xte)))

    res = pd.DataFrame(rows, columns=["class", "detector", "AP", "recall@thr", "FPR_benign", "n_test"])
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / "stage2.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
