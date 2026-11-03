"""M3 addendum: detection delay — time from attack-interval start to first flagged frame.

Completes the metric promised in the locked M3 protocol. Same calibration as stage 1
(ambient 99.9th percentile per stream). Delay = first flagged frame inside the interval
minus interval start. Captures never flagged inside their window -> no detection (ND).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.detectors import ambient_reference, score_range, score_physics

ROAD = Path(sys.argv[1])
Q = 0.999
CLASS_STREAM = {"correlated": "wheel", "max_speedometer": "speedo", "reverse_light": "speedo",
                "max_engine_coolant": "coolant"}

# ambient reference (identical to stage 1)
amb_frames = {k: [] for k in ("wheel", "speedo", "coolant")}
for cap in list_captures(ROAD, "ambient"):
    if not cap.stem.startswith("ambient_"):
        continue
    fr = load_capture(cap)
    for k in amb_frames:
        if len(fr[k]):
            amb_frames[k].append(fr[k])
ref = ambient_reference([ {k: v[i] for k, v in amb_frames.items()} for i in range(len(amb_frames["wheel"])) ])


def stream_scores(fr, stream):
    f = fr[stream]
    return {"D0a_range": score_range(f, ref, stream),
            "D1_physics": score_physics(f, ref, stream, cap_frames=fr)}


# per-stream ambient thresholds
thr = {}
for stream in ("wheel", "speedo", "coolant"):
    vals = []
    for cap in list_captures(ROAD, "ambient"):
        if not cap.stem.startswith("ambient_"):
            continue
        fr = load_capture(cap)
        if not len(fr[stream]):
            continue
        for v in stream_scores(fr, stream)["D1_physics"]:
            vals.append(v)
    thr["D1_physics", stream] = float(np.quantile(vals, Q))
vals = []
for cap in list_captures(ROAD, "ambient"):
    if not cap.stem.startswith("ambient_"):
        continue
    fr = load_capture(cap)
    if not len(fr["speedo"]):
        continue
    for v in stream_scores(fr, "speedo")["D0a_range"]:
        vals.append(v)
# D0a per stream needs its own scale; recompute per stream for completeness
for stream in ("wheel", "coolant"):
    vv = []
    for cap in list_captures(ROAD, "ambient"):
        if not cap.stem.startswith("ambient_"):
            continue
        fr = load_capture(cap)
        if len(fr[stream]):
            vv.extend(np.asarray(stream_scores(fr, stream)["D0a_range"], dtype=float))
    thr["D0a_range", stream] = float(np.quantile(vv, Q))
thr["D0a_range", "speedo"] = float(np.quantile(
    np.concatenate([np.asarray(stream_scores(load_capture(c), "speedo")["D0a_range"], dtype=float)
                    for c in list_captures(ROAD, "ambient") if c.stem.startswith("ambient_") and len(load_capture(c)["speedo"])]), Q))

meta = json = None
import json
meta = json.load(open(ROAD / "attacks/capture_metadata.json"))

rows = []
for cap in list_captures(ROAD, "attacks"):
    cls = next((c for c in CLASS_STREAM if cap.stem.startswith(c)), None)
    if cls is None or cls == "accelerator":
        continue
    stream = CLASS_STREAM[cls]
    mi = meta[cap.stem]
    if not mi.get("injection_id"):
        continue
    t_lo, t_hi = mi["injection_interval"]
    fr = load_capture(cap)
    f = fr[stream]
    if not len(f) or f["label"].sum() == 0:
        continue
    for det, s in stream_scores(fr, stream).items():
        s = pd.Series(s, index=f.index).dropna()
        tt = f["t"][s.index]
        flagged = s[(tt >= t_lo) & (tt <= t_hi + 5.0)] > thr[det, stream]
        if flagged.any():
            first_t = float(tt[flagged.index[0]]) if False else float(tt[flagged[flagged].index[0]])
            delay = first_t - t_lo
            rows.append((cap.stem, cls, det, round(delay, 3), len(s)))
        else:
            rows.append((cap.stem, cls, det, np.nan, len(s)))

res = pd.DataFrame(rows, columns=["capture", "class", "detector", "delay_s", "n"])
out = Path(__file__).parent / "results"
res.to_csv(out / "detection_delay.csv", index=False)
pd.set_option("display.float_format", lambda v: f"{v:.3g}")
print("median delay per class x detector (s; ND = never detected inside window+5s):")
print(res.pivot_table(index="detector", columns="class", values="delay_s", aggfunc="median").to_string())
print("\nND counts:")
print(res[res.delay_s.isna()].groupby(["class", "detector"]).size().to_string())
