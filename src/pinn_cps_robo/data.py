"""ROAD decoded-CSV loader -> tidy per-ID frames.

CSV format: Label,Time,ID,Signal_1_of_ID,...  (rows are CAN frames; each row
fills only its ID's signal columns; per-row Label 0/1 from the publisher).
Returns {'wheel': df, 'speedo': df, 'coolant': df} — one row per CAN frame of
that ID, columns: t, label, s1..sn (raw decoded signal values).
"""
from pathlib import Path
import pandas as pd

WHEEL_ID = 1760    # 0x6e0 — four wheel speeds (verified: injection metadata + empirical)
SPEEDO_ID = 208    # 0xd0 — s6 = speedometer, s3 = reverse-light candidate, s1 = gear candidate
COOLANT_ID = 1255  # 0x4e7 — s2 = coolant temp (attacked), s1 = ambient temp candidate

SPECS = {"wheel": (WHEEL_ID, 4), "speedo": (SPEEDO_ID, 7), "coolant": (COOLANT_ID, 2)}


def load_capture(csv_path):
    df = pd.read_csv(csv_path)
    out = {}
    for tag, (cid, ncols) in SPECS.items():
        sub = df[df["ID"] == cid]
        if len(sub) == 0:
            out[tag] = pd.DataFrame(columns=["t", "label"] + [f"s{i+1}" for i in range(ncols)])
            continue
        sig = sub[[f"Signal_{i}_of_ID" for i in range(1, ncols + 1)]].to_numpy(dtype=float)
        out[tag] = pd.DataFrame(
            {"t": sub["Time"].to_numpy(dtype=float), "label": sub["Label"].to_numpy(dtype=int),
             **{f"s{i+1}": sig[:, i] for i in range(ncols)}}
        ).reset_index(drop=True)
    return out


def list_captures(road_dir, kind):
    d = Path(road_dir) / "signal_extractions" / kind
    return sorted(d.glob("*.csv"))
