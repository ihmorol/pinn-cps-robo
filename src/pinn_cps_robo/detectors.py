"""Frame-level detectors for ROAD streams (M3 ladder).

Each detector maps a stream frame (tidy per-ID frame from data.load_capture)
plus ambient reference stats to a per-frame anomaly score. Higher = worse.
"""
import numpy as np
import pandas as pd

from .physics import inter_wheel_residual, continuity_residual, relation_residual, fit_scale

Q = 0.999  # ambient operating quantile


def ambient_reference(ambient_frames, alpha=None):
    """Compute ambient envelopes/floors per stream. alpha = speedo~wheel scale
    (fit here if not given). Returns dict of reference stats."""
    w, sp, c = ambient_frames["wheel"], ambient_frames["speedo"], ambient_frames["coolant"]
    ref = {}
    if len(w):
        wm = w[["s1", "s2", "s3", "s4"]].mean(axis=1).to_numpy()
        ref["floor_L1"] = float(inter_wheel_residual(w[["s1", "s2", "s3", "s4"]].to_numpy()).max())
        ref["floor_L3"] = float(continuity_residual(wm).max())
        ref["wheel_env"] = (w[["s1", "s2", "s3", "s4"]].to_numpy().min(axis=0),
                            w[["s1", "s2", "s3", "s4"]].to_numpy().max(axis=0))
        wt = w["t"].to_numpy()
    if len(sp):
        sd = sp.sort_values("t")
        if len(w) and alpha is None:
            wm_i = np.interp(sd["t"].to_numpy(), wt, wm)
            alpha = fit_scale(wm_i, sd["s6"].to_numpy())
        ref["alpha"] = alpha
        ref["floor_L2"] = float(relation_residual(
            np.interp(sd["t"].to_numpy(), wt, wm) if len(w) else np.zeros(len(sd)),
            sd["s6"].to_numpy(), alpha).max())
        ref["floor_L2"] = max(ref["floor_L2"], 1e-6)
        ref["speedo_env"] = (float(sp["s6"].min()), float(sp["s6"].max()))
        # freeze violation: ambient rolling-std lower quantile per window
        ref["speedo_std_q"] = float(np.quantile(_roll_std(sp["s6"].to_numpy(), 50), 0.01))
        ref["speedo_env_all"] = [(sp[f"s{i}"].min(), sp[f"s{i}"].max()) for i in range(1, 8)]
    if len(c):
        ref["floor_L4"] = float(continuity_residual(c["s2"].to_numpy()).max())
        ref["coolant_env"] = (float(c["s2"].min()), float(c["s2"].max()))
    return ref


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
        if stream == "speedo":
            lo, hi = env[i]
        else:
            lo, hi = env[0][i] if stream == "wheel" else env[0]
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
        freeze = np.maximum(0.0, ref["speedo_std_q"] - rstd) / max(ref["speedo_std_q"], 1e-9)
        out = freeze
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
