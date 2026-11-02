"""Frame-level detectors for ROAD streams (M3 ladder).

Each detector maps a stream frame (tidy per-ID frame from data.load_capture)
plus ambient reference stats to a per-frame anomaly score. Higher = worse.
"""
import numpy as np
import pandas as pd

from .physics import inter_wheel_residual, continuity_residual, relation_residual, fit_scale

Q = 0.999  # ambient operating quantile


def ambient_reference(ambient_capture_frames, alpha=None):
    """Compute ambient envelopes/floors from a LIST of per-capture frames.

    All residuals are computed WITHIN each capture (captures restart t~0, so
    cross-capture operations are meaningless — logged lesson) and aggregated
    by max (floors/envs) or quantiles (pooled distributions).
    """
    ref = {"alphas": [], "L1": [], "L3": [], "L2": [], "L4": [],
           "sp_std": [], "motion_std": [], "run": {"wheel": [], "speedo": [], "coolant": []}}
    wenv, senv, cenv = [], [], []
    for frames in ambient_capture_frames:
        w, sp, c = frames["wheel"], frames["speedo"], frames["coolant"]
        w = w.sort_values("t"); sp = sp.sort_values("t"); c = c.sort_values("t")
        if len(w):
            wm = w[["s1", "s2", "s3", "s4"]].mean(axis=1).to_numpy()
            ref["L1"].append(float(inter_wheel_residual(w[["s1", "s2", "s3", "s4"]].to_numpy()).max()))
            ref["L3"].append(float(continuity_residual(wm).max()))
            wenv.append(w[["s1", "s2", "s3", "s4"]].to_numpy())
            ref["run"]["wheel"].append(float(_runs_max(w["s1"].to_numpy(dtype=float))))
        if len(sp) and len(w):
            wm_i = np.interp(sp["t"].to_numpy(), w["t"].to_numpy(), wm)
            ref["alphas"].append(fit_scale(wm_i, sp["s6"].to_numpy()))
            a = ref["alphas"][-1]
            ref["L2"].append(float(relation_residual(wm_i, sp["s6"].to_numpy(), a).max()))
            ds6 = np.diff(sp["s6"].to_numpy(dtype=float), prepend=sp["s6"].to_numpy(dtype=float)[0])
            dwm = np.diff(wm_i, prepend=wm_i[0])
            ref.setdefault("L2d", []).append(float(np.abs(ds6 - a * dwm).max()))
            ref["sp_std"].append(_roll_std(sp["s6"].to_numpy(), 50))
            ref["run"]["speedo"].append(float(_runs_max(sp["s6"].to_numpy(dtype=float))))
            for i in range(1, 8):
                senv.append((float(sp[f"s{i}"].min()), float(sp[f"s{i}"].max())))
        if len(c):
            ref["L4"].append(float(continuity_residual(c["s2"].to_numpy()).max()))
            cenv.append((float(c["s2"].min()), float(c["s2"].max())))
            ref["run"]["coolant"].append(float(_runs_max(c["s2"].to_numpy(dtype=float))))
    W = np.vstack(wenv) if wenv else None
    ref["wheel_env"] = (W.min(axis=0), W.max(axis=0)) if W is not None else None
    ref["alpha"] = float(np.median(ref["alphas"])) if ref["alphas"] else 1.0
    ref["floor_L1"] = max(ref["L1"]) if ref["L1"] else 1e-9
    ref["floor_L3"] = max(ref["L3"]) if ref["L3"] else 1e-9
    ref["floor_L2"] = max(max(ref["L2"]) if ref["L2"] else 1e-6, 1e-6)
    ref["floor_L2d"] = max(max(ref["L2d"]) if ref.get("L2d") else 1e-6, 1e-6)
    ref["floor_L4"] = max(ref["L4"]) if ref["L4"] else 1e-9
    ref["coolant_env"] = (min(a for a, b in cenv), max(b for a, b in cenv)) if cenv else (0.0, 0.0)
    sp_all = np.concatenate(ref["sp_std"]) if ref["sp_std"] else np.array([0.0])
    mo_all = np.concatenate(ref["motion_std"]) if ref["motion_std"] else np.array([0.0])
    ref["speedo_std_q"] = float(np.quantile(sp_all, 0.01))
    nz = mo_all[mo_all > 1e-6]
    ref["motion_std_q"] = float(0.5 * np.median(nz)) if len(nz) else 0.0
    # per-signal speedo envelope (for D0a)
    if senv:
        per = {}
        for i, (a, b) in enumerate(senv, start=1):
            if i not in per:
                per[i] = [a, b]
            else:
                per[i][0] = min(per[i][0], a)
                per[i][1] = max(per[i][1], b)
        ref["speedo_env_all"] = [tuple(per[i]) for i in sorted(per)]
    for k in ref["run"]:
        ref[f"max_run_{k}"] = max(ref["run"][k]) if ref["run"][k] else 1.0
    return ref


def _runs_max(v):
    v = np.asarray(v, dtype=float)
    best = cur = 1
    for i in range(1, len(v)):
        cur = cur + 1 if v[i] == v[i - 1] else 1
        best = max(best, cur)
    return best


def _roll_std(v, k):
    v = np.asarray(v, dtype=float)
    c1 = np.concatenate(([0.0], np.cumsum(v)))
    c2 = np.concatenate(([0.0], np.cumsum(v * v)))
    n = len(v)
    out = np.zeros(n)
    for i in range(n):
        lo = max(0, i - k + 1)
        m = i - lo + 1
        s, s2 = c1[i + 1] - c1[lo], c2[i + 1] - c2[lo]
        out[i] = max(0.0, s2 / m - (s / m) ** 2) ** 0.5
    return out


def score_range(frame, ref, stream):
    """D0a: total exceedance beyond ambient per-signal envelopes."""
    ncol = {"wheel": 4, "speedo": 7, "coolant": 2}[stream]
    env = ref["wheel_env"] if stream == "wheel" else (
        ref["speedo_env_all"] if stream == "speedo" else [ref["coolant_env"]] * ncol)
    out = np.zeros(len(frame))
    for i in range(ncol):
        v = frame[f"s{i+1}"].to_numpy(dtype=float)
        if stream == "wheel":
            lo, hi = env[0][i], env[1][i]
        elif stream == "speedo":
            lo, hi = env[i]
        else:
            lo, hi = env[0]
        out += np.maximum(0, v - hi) + np.maximum(0, lo - v)
    return out


def score_const_run(frame, ref, stream, sig):
    """D0b: run length of identical consecutive values on one signal."""
    v = frame[sig].to_numpy(dtype=float)
    run = np.ones(len(v))
    for i in range(1, len(v)):
        if v[i] == v[i - 1]:
            run[i] = run[i - 1] + 1
    floor = ref.get(f"max_run_{stream}_{sig}")
    return run, floor


def score_physics(frame, ref, stream, cap_frames=None):
    """D1: max over applicable physics laws of residual / ambient floor."""
    if stream == "wheel":
        w = frame[["s1", "s2", "s3", "s4"]].to_numpy(dtype=float)
        wm = w.mean(axis=1)
        s1 = inter_wheel_residual(w) / max(ref["floor_L1"], 1e-9)
        s3 = continuity_residual(wm) / max(ref["floor_L3"], 1e-9)
        return np.maximum(s1, s3)
    if stream == "speedo":
        sd = frame.sort_values("t")
        t = sd["t"].to_numpy()
        v = sd["s6"].to_numpy(dtype=float)
        s2 = None
        if cap_frames is not None and len(cap_frames["wheel"]):
            w = cap_frames["wheel"]
            wt = w["t"].to_numpy()
            wm = w[["s1", "s2", "s3", "s4"]].mean(axis=1).to_numpy()
            wmi = np.interp(t, wt, wm)
            s2 = relation_residual(wmi, v, ref["alpha"]) / ref["floor_L2"]
        rstd = _roll_std(v, 50)
        # L2d — dynamics-consistency law (replaces the binary freeze law, which
        # failed because ambient idling legitimately freezes the display):
        # the display's CHANGE must track the wheels' change, |ds6 - a*dwm|.
        l2d = np.zeros(len(v))
        if cap_frames is not None and len(cap_frames["wheel"]) and ref.get("floor_L2d"):
            w = cap_frames["wheel"]
            wt = w["t"].to_numpy()
            wm = w[["s1", "s2", "s3", "s4"]].mean(axis=1).to_numpy()
            wmi = np.interp(t, wt, wm)
            ds6 = np.diff(v, prepend=v[0])
            dwm = np.diff(wmi, prepend=wmi[0])
            l2d = np.abs(ds6 - ref["alpha"] * dwm) / ref["floor_L2d"]
        out = l2d
        if s2 is not None:
            out = np.maximum(out, s2)
        return pd.Series(out, index=sd.index).reindex(frame.index).to_numpy()
    if stream == "coolant":
        v = frame["s2"].to_numpy(dtype=float)
        lo, hi = ref["coolant_env"]
        s6 = (np.maximum(0, v - hi) + np.maximum(0, lo - v)) / max(hi - lo, 1e-9)
        s4 = continuity_residual(v) / max(ref["floor_L4"], 1e-9)
        return np.maximum(s6, s4)
    raise ValueError(stream)
