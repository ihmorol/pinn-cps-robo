"""M4: PINN vs physics-free twin across training-set sizes (per protocol.md)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.evaluate import ap_score, threshold_at, recall_fpr

ROAD = Path(sys.argv[1])
Q = 0.999
LAM = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
REGIMES = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [0.001, 0.01, 0.1, 1.0]
EPOCHS = {0.001: 40, 0.01: 30, 0.1: 15, 1.0: 5}


def buildXY(f):
    """Wheel-stream supervised tuples: X=[w1..w4, s6i]_t -> Y=[w1..w4]_{t+1}."""
    w = f["wheel"].sort_values("t").reset_index(drop=True)
    W = w[["s1", "s2", "s3", "s4"]].to_numpy(dtype=float)
    sd = f["speedo"].sort_values("t")
    s6i = np.interp(w["t"].to_numpy(), sd["t"].to_numpy(), sd["s6"].to_numpy())
    X = np.hstack([W[:-1], s6i[:-1].reshape(-1, 1)])
    Y = W[1:]
    return X, Y


def train_model(Xtr, Ytr, physics, alpha, amax, mu, sd_, epochs):
    torch.manual_seed(0)
    net = nn.Sequential(nn.Linear(5, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 4))
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    mu_t = torch.tensor(mu, dtype=torch.float32)
    sd_t = torch.tensor(sd_, dtype=torch.float32)
    X = torch.tensor((Xtr - mu) / sd_, dtype=torch.float32)
    Y = torch.tensor((Ytr - mu[:4]) / sd_[:4], dtype=torch.float32)
    ds = torch.utils.data.TensorDataset(X, Y)
    dl = torch.utils.data.DataLoader(ds, batch_size=4096, shuffle=True)
    for ep in range(epochs):
        for xb, yb in dl:
            pred = net(xb)
            loss = ((pred - yb) ** 2).mean()
            if physics:
                wp = pred * sd_t[:4] + mu_t[:4]                    # de-normalized wheels
                wm = wp.mean(dim=1)
                s6 = xb[:, 4] * sd_t[4] + mu_t[4]
                l_disp = (((wm * alpha - s6) / 1000.0) ** 2).mean()
                dw = (wp - (xb[:, :4] * sd_t[:4] + mu_t[:4])).abs()
                l_acc = (torch.relu(dw / amax - 1.0) ** 2).mean()
                loss = loss + LAM * (l_disp + l_acc)
            opt.zero_grad(); loss.backward(); opt.step()
    return net


def main():
    # ambient per-capture frames; temporal split: even-index captures train pool, odd test pool
    caps = [load_capture(c) for c in list_captures(ROAD, "ambient") if c.stem.startswith("ambient_")]
    XY = [buildXY(f) for f in caps]
    Xtr_pool = np.vstack([X for i, (X, Y) in enumerate(XY) if i % 2 == 0])
    Ytr_pool = np.vstack([Y for i, (X, Y) in enumerate(XY) if i % 2 == 0])
    Xte_pool = np.vstack([X for i, (X, Y) in enumerate(XY) if i % 2 == 1])
    Yte_pool = np.vstack([Y for i, (X, Y) in enumerate(XY) if i % 2 == 1])
    mu, sd_ = Xtr_pool.mean(0), Xtr_pool.std(0) + 1e-9
    alpha = 1.1556  # from M3 ambient fit
    amax = np.maximum(np.abs(np.diff(Ytr_pool, axis=0)).max(0) * 1.5, 1.0)  # soft accel limit per wheel

    # attack test frames (wheel masquerade captures)
    atk = []
    for cap in list_captures(ROAD, "attacks"):
        if cap.stem.startswith("correlated"):
            atk.append(buildXY(load_capture(cap)))
    Xa = np.vstack([X for X, Y in atk]); Ya = np.vstack([Y for X, Y in atk])
    # benign stress: accelerator captures (genuine unusual dynamics)
    stress = []
    for cap in list_captures(ROAD, "attacks"):
        if cap.stem.startswith("accelerator"):
            stress.append(buildXY(load_capture(cap)))
    Xs = np.vstack([X for X, Y in stress]); Ys = np.vstack([Y for X, Y in stress])

    rows = []
    for frac in REGIMES:
        n = max(1000, int(frac * len(Xtr_pool)))
        rng = np.random.default_rng(0)
        idx = rng.choice(len(Xtr_pool), min(n, len(Xtr_pool)), replace=False)
        Xtr, Ytr = Xtr_pool[idx], Ytr_pool[idx]
        for name, phys in [("D3_twin", False), ("D2_pinn", True)]:
            net = train_model(Xtr, Ytr, phys, alpha, torch.tensor(amax, dtype=torch.float32), mu, sd_, EPOCHS[frac])
            with torch.no_grad():
                resid = lambda X, Y: ((net(torch.tensor((X - mu) / sd_, dtype=torch.float32)) *
                                       sd_[:4] + mu[:4] - Y).abs().mean(dim=1).numpy())
                s_amb = resid(Xte_pool, Yte_pool)
                s_atk = resid(Xa, Ya)
                s_str = resid(Xs, Ys)
            thr = threshold_at(s_amb, Q)
            y_atk = np.ones(len(s_atk), dtype=int)
            y_amb = np.zeros(len(s_amb), dtype=int)
            ap = ap_score(np.concatenate([y_atk, y_amb]), np.concatenate([s_atk, s_amb]))
            rec, fpr_amb = recall_fpr(np.concatenate([y_atk, y_amb]), np.concatenate([s_atk, s_amb]), thr)
            # stress FPR: fraction of accelerator frames above threshold
            fpr_str = float((s_str > thr).mean())
            rows.append((frac, name, ap, rec, fpr_amb, fpr_str))
            print(f"frac={frac:<6} {name}  AP={ap:.4f} recall={rec:.4f} FPR_amb={fpr_amb:.5f} FPR_accel={fpr_str:.5f}")

    res = pd.DataFrame(rows, columns=["train_frac", "model", "AP", "recall@thr", "FPR_amb", "FPR_accel"])
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / "attribution.csv", index=False)


if __name__ == "__main__":
    main()
