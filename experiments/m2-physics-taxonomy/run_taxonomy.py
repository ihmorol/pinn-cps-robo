"""M2: physics taxonomy of ROAD attack captures (per protocol.md).

v2 refinements (logged): (a) attack interval derived from label-1 rows across
ALL IDs (only the attacked ID carries label 1); (b) inside/outside split by
TIME with ±0.05 s margin — absorbs the one boundary frame the publisher labels 0;
(c) added value-envelope laws L5/L6 for the 'max X' masquerades; (d) freeze law
L7 (inverted ratio: higher = frozen inside).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.physics import inter_wheel_residual, continuity_residual, relation_residual, fit_scale

ROAD = Path(sys.argv[1])
MARGIN = 0.05


def split_ratio(vals, times, t_lo, t_hi):
    inside = vals[(times >= t_lo - MARGIN) & (times <= t_hi + MARGIN)]
    outside = vals[(times < t_lo - MARGIN) | (times > t_hi + MARGIN)]
    im = float(inside.max()) if len(inside) else np.nan
    om = float(outside.max()) if len(outside) else np.nan
    return im, om, (im / om if np.isfinite(om) and om > 0 else np.nan)


def attack_interval(fr):
    ts = []
    for f in fr.values():
        if len(f):
            ts.append(f["t"][f["label"] == 1])
    ts = np.concatenate(ts) if ts else np.array([])
    return (ts.min(), ts.max()) if len(ts) else None


rows = []
amb = load_capture(ROAD / "signal_extractions/ambient/ambient_dyno_drive_basic_long.csv")
wm_amb = amb["wheel"][["s1", "s2", "s3", "s4"]].mean(axis=1).to_numpy()
wt_amb = amb["wheel"]["t"].to_numpy()
sd = amb["speedo"].sort_values("t")
alpha = fit_scale(np.interp(sd["t"].to_numpy(), wt_amb, wm_amb), sd["s6"].to_numpy())
coolant_env_amb = float(amb["coolant"]["s2"].max())
speedo_env_amb = float(amb["speedo"]["s6"].max())
print(f"alpha={alpha:.5f}  ambient envelopes: coolant_max={coolant_env_amb} speedo_max={speedo_env_amb}")

for cap in list_captures(ROAD, "attacks"):
    name = cap.stem
    fr = load_capture(cap)
    iv = attack_interval(fr)
    w, sp, c = fr["wheel"], fr["speedo"], fr["coolant"]
    if iv is None:
        rows.append((name, "no_injection", "all", np.nan, np.nan, np.nan))
        continue
    t_lo, t_hi = iv
    wm = w[["s1", "s2", "s3", "s4"]].mean(axis=1).to_numpy()
    st = w["t"].to_numpy()
    iw = inter_wheel_residual(w[["s1", "s2", "s3", "s4"]].to_numpy())
    rows.append((name, "wheel_masq", "L1_interwheel", *split_ratio(iw, st, t_lo, t_hi)))
    if len(sp):
        s6i = np.interp(st, sp.sort_values("t")["t"].to_numpy(), sp.sort_values("t")["s6"].to_numpy())
        rows.append((name, "rel", "L2_speedo_rel", *split_ratio(relation_residual(wm, s6i, alpha), st, t_lo, t_hi)))
        s6t = sp["t"].to_numpy(); s6v = sp["s6"].to_numpy()
        # freeze (inverted ratio): outside_std / inside_std
        istd = float(np.std(s6v[(s6t >= t_lo) & (s6t <= t_hi)]))
        ostd = float(np.std(s6v[(s6t < t_lo) | (s6t > t_hi)]))
        rows.append((name, "speedo_masq", "L7_speedo_freeze(inv)", ostd, istd, ostd / istd if istd > 0 else np.nan))
        inside_env = float(s6v[(s6t >= t_lo) & (s6t <= t_hi)].max())
        rows.append((name, "speedo_masq", "L5_speedo_env", inside_env, speedo_env_amb, inside_env / speedo_env_amb))
    rows.append((name, "wheel_masq", "L3_continuity", *split_ratio(continuity_residual(wm), st, t_lo, t_hi)))
    if len(c):
        ct, cv = c["t"].to_numpy(), c["s2"].to_numpy()
        rows.append((name, "coolant_masq", "L4_coolant_jump", *split_ratio(continuity_residual(cv), ct, t_lo, t_hi)))
        inside_env = float(cv[(ct >= t_lo) & (ct <= t_hi)].max())
        rows.append((name, "coolant_masq", "L6_coolant_env", inside_env, coolant_env_amb, inside_env / coolant_env_amb))

out = Path(__file__).parent / "results"
out.mkdir(exist_ok=True)
res = pd.DataFrame(rows, columns=["capture", "class", "law", "inside_max", "outside_max", "ratio"])
res.to_csv(out / "taxonomy.csv", index=False)
pd.set_option("display.float_format", lambda v: f"{v:.3g}")
print(res.to_string(index=False))
