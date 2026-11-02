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


def solve_specs(log_path, csv_path, cid, nsig):
    """Recover (start, len) per signal by matching the raw log to the published
    CSV. The shipped anonymized DBC layouts do NOT reproduce the CSV values
    (logged finding) — the masquerade log+CSV pair is the ground truth."""
    raw, vals = [], {i: [] for i in range(1, nsig + 1)}
    for line in open(log_path):
        try:
            head, rest = line.strip().split(") ", 1)
            float(head[1:])
            cid_hex, data_hex = rest.split(" ")[1].split("#")
            if int(cid_hex, 16) == cid and len(data_hex) >= 16:
                raw.append(int(data_hex[:16], 16))
        except Exception:
            continue
    csv = pd.read_csv(csv_path)
    csv = csv[csv.ID == cid].reset_index(drop=True)
    n = min(len(raw), len(csv))
    raw = raw[:n]
    for i in range(1, nsig + 1):
        vals[i] = csv[f"Signal_{i}_of_ID"].to_numpy(dtype=np.int64)[:n]
    sh = np.arange(64, dtype=np.uint64)
    r = np.array(raw, dtype=np.uint64)
    b = ((r[:, None] >> sh) & np.uint64(1)).astype(np.int64)
    specs = []
    for i in range(1, nsig + 1):
        hit = None
        for start in range(64):
            for ln in range(1, 17):
                if start + ln > 64:
                    continue
                cand = (b[:, start:start + ln] * (1 << np.arange(ln))).sum(axis=1)
                if np.array_equal(cand, vals[i]):
                    hit = (start, ln)
                    break
            if hit:
                break
        if hit is None:
            raise RuntimeError(f"no bit mapping found for ID {cid} sig{i}")
        specs.append(hit)
    return specs


def parse_log(path, want_specs):
    """want_specs: {cid: [(start, len), ...]}"""
    rows = {cid: [] for cid in want_specs}
    with open(path) as f:
        for line in f:
            try:
                head, rest = line.strip().split(") ", 1)
                t = float(head[1:])
                iface, payload = rest.split(" ", 1)
                cid_hex, data_hex = payload.split("#")
                cid = int(cid_hex, 16)
                if cid in want_specs and len(data_hex) >= 16:
                    v = int(data_hex[:16], 16)
                    sigs = [float((v >> start) & ((1 << ln) - 1)) for start, ln in want_specs[cid]]
                    rows[cid].append((t, *sigs))
            except Exception:
                continue
    return {cid: pd.DataFrame(d, columns=["t"] + [f"s{i+1}" for i in range(len(want_specs[cid]))]).sort_values("t").reset_index(drop=True)
            for cid, d in rows.items()}


def split_ratio(vals, times, lo, hi):
    inside = vals[(times >= lo - MARGIN) & (times <= hi + MARGIN)]
    outside = vals[(times < lo - MARGIN) | (times > hi + MARGIN)]
    return (float(inside.max()) if len(inside) else np.nan,
            float(outside.max()) if len(outside) else np.nan)


def main():
    global SPECS
    meta = json.load(open(ROAD / "attacks/capture_metadata.json"))
    meta = {k: v for k, v in meta.items()
            if "_masquerade" not in k and v.get("injection_id") is not None}

    # ---- solve bit mappings from masquerade log+CSV pairs (DBC layouts are wrong — logged)
    SPECS = {}
    for cid, nsig, mlog, mcsv in [
        (1760, 4, "correlated_signal_attack_1_masquerade", "correlated_signal_attack_1_masquerade"),
        (208, 7, "max_speedometer_attack_1_masquerade", "max_speedometer_attack_1_masquerade"),
        (1255, 2, "max_engine_coolant_temp_attack_masquerade", "max_engine_coolant_temp_attack_masquerade"),
    ]:
        SPECS[cid] = solve_specs(ROAD / f"attacks/{mlog}.log",
                                 ROAD / f"signal_extractions/attacks/{mcsv}.csv", cid, nsig)
        print(f"ID {cid:#x} solved mapping: {SPECS[cid]}")

    # ---- validation gate: reproduce published CSV on the calibration capture
    csv_ref = load_capture(ROAD / "signal_extractions/attacks/correlated_signal_attack_1_masquerade.csv")["wheel"]
    dec = parse_log(ROAD / "attacks/correlated_signal_attack_1_masquerade.log", SPECS)[1760]
    n = min(len(dec), len(csv_ref))
    d1 = dec.to_numpy(dtype=float)[:n]
    d2 = csv_ref.sort_values("t").to_numpy(dtype=float)[:n]
    tmatch = np.allclose(d1[:, 0] - d1[0, 0], d2[:, 0] - d2[0, 0], atol=1e-6)
    vmatch = np.allclose(d1[:, 1:], d2[:, 2:], atol=1e-6)  # d2 cols: t, label, s1..s4
    print(f"validation: times match={tmatch} values match={vmatch} (n={n})")
    if not (tmatch and vmatch):
        print("VALIDATION FAILED — decoder bug, stopping per protocol")
        return

    # ---- ambient floors (per-capture within-capture maxima, as M3)
    floors = {"L1": [], "L3": [], "L2d": [], "alpha": []}
    MAP_AMB = {1760: [(48, 14), (32, 14), (16, 14), (0, 14)],
               208: SPECS[208], 1255: SPECS[1255]}
    for cap in sorted((ROAD / "ambient").glob("ambient_*.log")):
        fr = parse_log(cap, {1760: MAP_AMB[1760], 208: MAP_AMB[208]})
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

    # ---- fabrication captures (decode with BOTH candidate wheel mappings; select by
    # benign inter-wheel consistency — the publisher's extractions differ per family,
    # and fabrication CSVs do not exist to disambiguate directly)
    MAP_MASQ = SPECS
    rows = []
    for stem, meta_i in meta.items():
        if "_masquerade" in stem or meta_i.get("injection_id") is None:
            continue
        log = ROAD / "attacks" / f"{stem}.log"
        if not log.exists():
            continue
        try:
            cid = int(meta_i["injection_id"], 16)
        except ValueError:
            continue  # fuzzing captures use randomized IDs ('XXX') — out of scope
        t_lo, t_hi = meta_i["injection_interval"]
        if cid == 1760:
            best, best_map, best_floor = None, None, None
            for tag, mp in [("14bit", MAP_AMB), ("masq", MAP_MASQ)]:
                fr = parse_log(log, mp)
                for f in fr.values():
                    if len(f):
                        f["t"] -= f["t"].iloc[0]
                w = fr[1760]
                benign = w[(w.t < t_lo - MARGIN) | (w.t > t_hi + MARGIN)]
                if not len(benign):
                    continue
                r = float(inter_wheel_residual(benign[["s1", "s2", "s3", "s4"]].to_numpy()).mean())
                if best is None or r < best:
                    best, best_map, best_floor = r, tag, r
            print(f"{stem}: selected wheel mapping = {best_map} (benign inter-wheel mean {best:.2f})")
            fr = parse_log(log, MAP_AMB if best_map == "14bit" else MAP_MASQ)
            for f in fr.values():
                if len(f):
                    f["t"] -= f["t"].iloc[0]
        else:
            fr = parse_log(log, {k: (MAP_AMB if cid != 1760 else MAP_MASQ)[k] for k in (cid, 1760, 208, 1255) if k in (MAP_AMB if cid != 1760 else MAP_MASQ)})
            for f in fr.values():
                if len(f):
                    f["t"] -= f["t"].iloc[0]
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

    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    res = pd.DataFrame(rows, columns=["capture", "class", "law", "inside_max", "outside_max", "ratio"])
    res.to_csv(out / "fabrication_taxonomy.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
