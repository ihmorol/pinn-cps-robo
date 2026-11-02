"""M2b: decode raw fabrication captures and run the physics taxonomy (per protocol.md)."""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture
from pinn_cps_robo.physics import inter_wheel_residual, continuity_residual, relation_residual, fit_scale

ROAD = Path(sys.argv[1])
MARGIN = 0.05
SPECS = {1760: [(5, 14), (21, 14), (37, 14), (53, 14)],
         208: [(6, 4), (1, 10), (19, 1), (26, 2), (39, 8), (45, 14), (63, 8)],
         1255: [(29, 6), (47, 8)]}


def parse_log(path, want_ids):
    rows = {cid: [] for cid in want_ids}
    with open(path) as f:
        for line in f:
            try:
                head, rest = line.strip().split(") ", 1)
                t = float(head[1:])
                iface, payload = rest.split(" ", 1)
                cid_hex, data_hex = payload.split("#")
                cid = int(cid_hex, 16)
                if cid in want_ids and len(data_hex) >= 16:
                    v = int(data_hex[:16], 16)
                    sigs = [float((v >> start) & ((1 << ln) - 1)) for start, ln in SPECS[cid]]
                    rows[cid].append((t, sigs))
            except Exception:
                continue
    return {cid: pd.DataFrame(d, columns=["t"] + [f"s{i+1}" for i in range(len(SPECS[cid]))]).sort_values("t").reset_index(drop=True)
            for cid, d in rows.items()}


def main():
    meta = json.load(open(ROAD / "attacks/capture_metadata.json"))
    meta = {k: v for k, v in meta.items()
            if "_masquerade" not in k and v.get("injection_id") is not None}

    # ---- validation gate: decoder must reproduce published CSV on a masquerade capture
    csv_ref = load_capture(ROAD / "signal_extractions/attacks/correlated_signal_attack_1_masquerade.csv")["wheel"]
    dec = parse_log(ROAD / "attacks/correlated_signal_attack_1_masquerade.log", [1760])[1760]
    n = min(len(dec), len(csv_ref))
    d1 = dec.to_numpy(dtype=float)[:n]
    d2 = csv_ref.sort_values("t").to_numpy(dtype=float)[:n]
    tmatch = np.allclose(d1[:, 0], d2[:, 0], atol=1e-6)
    vmatch = np.allclose(d1[:, 1:], d2[:, 1:], atol=1e-6)
    print(f"validation: times match={tmatch} values match={vmatch} (n={n})")
    if not (tmatch and vmatch):
        print("VALIDATION FAILED — decoder bug, stopping per protocol")
        return

    # ---- ambient floors (per-capture within-capture maxima, as M3)
    floors = {"L1": [], "L3": [], "L2d": [], "alpha": []}
    for cap in sorted((ROAD / "ambient").glob("ambient_*.log")):
        fr = parse_log(cap, [1760, 208])
        w, sp = fr[1760], fr[208]
        if not len(w) or not len(sp):
            continue
        wm = w[[f"s{i}" for i in range(1, 5)]].mean(axis=1).to_numpy()
        wmi = np.interp(sp["t"].to_numpy(), w["t"].to_numpy(), wm)
        a = fit_scale(wmi, sp["s6"].to_numpy())
        floors["alpha"].append(a)
        floors["L1"].append(float(inter_wheel_residual(w[[f"s{i}" for i in range(1, 5)]].to_numpy()).max()))
        floors["L3"].append(float(continuity_residual(wm).max()))
        ds6 = np.diff(sp["s6"].to_numpy(), prepend=sp["s6"].to_numpy()[0])
        dwm = np.diff(wmi, prepend=wmi[0])
        floors["L2d"].append(float(np.abs(ds6 - a * dwm).max()))
    fl = {k: (max(v) if k != "alpha" else float(np.median(v))) for k, v in floors.items()}
    fl["L2d"] = max(fl["L2d"], 1e-6)
    print("floors:", {k: round(v, 3) for k, v in fl.items()})

    # ---- fabrication captures
    rows = []
    for stem, meta_i in meta.items():
        if "_masquerade" in stem or meta_i.get("injection_id") is None:
            continue
        log = ROAD / "attacks" / f"{stem}.log"
        if not log.exists():
            continue
        cid = int(meta_i["injection_id"], 16)
        t_lo, t_hi = meta_i["injection_interval"]
        fr = parse_log(log, [1760, 208, 1255])
        if cid == 1760:
            w = fr[1760]
            wm = w[[f"s{i}" for i in range(1, 5)]].mean(axis=1).to_numpy()
            tt = w["t"].to_numpy()
            l1 = inter_wheel_residual(w[[f"s{i}" for i in range(1, 5)]].to_numpy())
            l3 = continuity_residual(wm)
            for law, vals in [("L1_interwheel", l1), ("L3_continuity", l3)]:
                ins, outs = split_ratio(vals, tt, t_lo, t_hi)
                rows.append((stem, "fabrication", law, ins, outs, ins / outs if outs > 0 else np.nan))
            sp = fr[208]
            if len(sp):
                wmi = np.interp(sp["t"].to_numpy(), tt, wm)
                ds6 = np.diff(sp["s6"].to_numpy(), prepend=sp["s6"].to_numpy()[0])
                dwm = np.diff(wmi, prepend=wmi[0])
                l2d = np.abs(ds6 - fl["alpha"] * dwm)
                ins, outs = split_ratio(l2d, sp["t"].to_numpy(), t_lo, t_hi)
                rows.append((stem, "fabrication", "L2d_dynamics", ins, outs, ins / outs if outs > 0 else np.nan))
        elif cid == 208:
            sp = fr[208]
            tt, v = sp["t"].to_numpy(), sp["s6"].to_numpy()
            ins, outs = split_ratio(np.abs(v), tt, t_lo, t_hi)  # max speedo: value itself
            rows.append((stem, "fabrication", "L5_speedo_env", ins, outs, np.nan))
            l2d = np.abs(np.diff(v, prepend=v[0]))
            ins, outs = split_ratio(l2d, tt, t_lo, t_hi)
            rows.append((stem, "fabrication", "L2d_display_jump", ins, outs, ins / outs if outs > 0 else np.nan))
        elif cid == 1255:
            c = fr[1255]
            tt, v = c["t"].to_numpy(), c["s2"].to_numpy()
            ins, outs = split_ratio(np.abs(v), tt, t_lo, t_hi)
            rows.append((stem, "fabrication", "L6_coolant_env", ins, outs, np.nan))

    def split_ratio(vals, times, lo, hi):
        inside = vals[(times >= lo - MARGIN) & (times <= hi + MARGIN)]
        outside = vals[(times < lo - MARGIN) | (times > hi + MARGIN)]
        return (float(inside.max()) if len(inside) else np.nan,
                float(outside.max()) if len(outside) else np.nan)

    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res = pd.DataFrame(rows, columns=["capture", "class", "law", "inside_max", "outside_max", "ratio"])
    res.to_csv(out / "fabrication_taxonomy.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
