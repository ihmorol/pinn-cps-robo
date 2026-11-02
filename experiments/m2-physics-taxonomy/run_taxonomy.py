"""M2: physics taxonomy of ROAD attack captures (per protocol.md)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures, WHEEL_ID, SPEEDO_ID, COOLANT_ID
from pinn_cps_robo.physics import inter_wheel_residual, continuity_residual, relation_residual, fit_scale

ROAD = Path(sys.argv[1])


def wheel_frame(df):
    return df.dropna(subset=["w1"])[["w1", "w2", "w3", "w4", "w_label", "w_t"]]


def law_stats(df, law_fn, label_col, sig_cols):
    vals = law_fn(df[sig_cols].to_numpy(dtype=float))
    labs = df[label_col].to_numpy(dtype=int)
    inside, outside = vals[labs == 1], vals[labs == 0]
    imax = float(inside.max()) if len(inside) else np.nan
    omax = float(outside.max()) if len(outside) else np.nan
    return imax, omax, (imax / omax if omax and np.isfinite(omax) and omax > 0 else np.nan)


rows = []
# ambient scale fit: speedo sig6 vs mean wheel (align by nearest time)
amb = load_capture(ROAD / "signal_extractions/ambient/ambient_dyno_drive_basic_long.csv")
aw = wheel_frame(amb)
wmean = aw[["w1", "w2", "w3", "w4"]].mean(axis=1).to_numpy()
wt = aw["w_t"].to_numpy()
asub = amb.dropna(subset=["s6"]).sort_values("s_t")
alpha = fit_scale(np.interp(asub["s_t"].to_numpy(), wt, wmean), asub["s6"].to_numpy())
print(f"ambient speedo~wheel scale alpha = {alpha:.5f}")

for cap in list_captures(ROAD, "attacks"):
    name = cap.stem
    df = load_capture(cap)
    w = wheel_frame(df)
    if w["w_label"].sum() == 0:
        for law in ["L1_interwheel", "L2_speedo_rel", "L3_continuity"]:
            rows.append((name, "no_injection", law, np.nan, np.nan, np.nan))
        continue
    wm = w[["w1", "w2", "w3", "w4"]].mean(axis=1).to_numpy()
    st = w["w_t"].to_numpy()
    # L1
    im, om, r = law_stats(w, inter_wheel_residual, "w_label", ["w1", "w2", "w3", "w4"])
    rows.append((name, "wheel_masq", "L1_interwheel", im, om, r))
    # L2: speedo relation on wheel-time grid (interp speedo sig6 to wheel times)
    sd = df.dropna(subset=["s6"]).sort_values("s_t")
    s6i = np.interp(st, sd["s_t"].to_numpy(), sd["s6"].to_numpy())
    rel = relation_residual(wm, s6i, alpha)
    labs = w["w_label"].to_numpy(dtype=int)
    im2, om2 = rel[labs == 1].max(), rel[labs == 0].max()
    rows.append((name, "wheel_masq", "L2_speedo_rel", float(im2), float(om2), float(im2 / om2 if om2 > 0 else np.nan)))
    # L3
    cont = continuity_residual(wm)
    im3, om3 = cont[labs == 1].max(), cont[labs == 0].max()
    rows.append((name, "wheel_masq", "L3_continuity", float(im3), float(om3), float(im3 / om3 if om3 > 0 else np.nan)))
    # L4 coolant (label from c_label)
    cd = df.dropna(subset=["c2"])
    if len(cd) and cd["c_label"].sum() > 0:
        cc = cd["c2"].to_numpy(dtype=float)
        cl = cd["c_label"].to_numpy(dtype=int)
        ccont = continuity_residual(cc)
        im4, om4 = ccont[cl == 1].max(), ccont[cl == 0].max()
        rows.append((name, "coolant_masq", "L4_coolant_jump", float(im4), float(om4), float(im4 / om4 if om4 > 0 else np.nan)))

out = Path(__file__).parent / "results"
out.mkdir(exist_ok=True)
res = pd.DataFrame(rows, columns=["capture", "class", "law", "inside_max", "outside_max", "ratio"])
res.to_csv(out / "taxonomy.csv", index=False)
print(res.to_string(index=False))
