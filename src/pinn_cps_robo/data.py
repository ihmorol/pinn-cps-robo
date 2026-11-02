"""ROAD decoded-CSV loader -> tidy per-capture panels.

CSV format: Label,Time,ID,Signal_1_of_ID,...  (rows are CAN frames; each row
fills only its ID's signal columns; per-row Label 0/1 from the publisher).
"""
from pathlib import Path
import numpy as np
import pandas as pd

WHEEL_ID = 1760    # 0x6e0 — four wheel speeds (verified empirically + via injection metadata)
SPEEDO_ID = 208    # 0xd0 — sig6 = speedometer, sig3 = reverse-light candidate, sig1 = gear candidate
COOLANT_ID = 1255  # 0x4e7 — sig2 = coolant temp (attacked byte), sig1 = ambient temp candidate


def load_capture(csv_path):
    """Return tidy frame indexed by time with the mapped signals + label."""
    df = pd.read_csv(csv_path)
    out = df[["Label", "Time"]].rename(columns={"Label": "label", "Time": "t"}).copy()
    for cid, tag, cols in [
        (WHEEL_ID, "w", 4),
        (SPEEDO_ID, "s", 7),
        (COOLANT_ID, "c", 2),
    ]:
        sub = df[df["ID"] == cid]
        sig = sub[[f"Signal_{i}_of_ID" for i in range(1, cols + 1)]].to_numpy(dtype=float)
        lab = sub["Label"].to_numpy(dtype=int)
        t = sub["Time"].to_numpy(dtype=float)
        for i in range(cols):
            out[f"{tag}{i+1}"] = pd.Series(sig[:, i], index=out.index)
        # frame-level label for this ID (rows of the ID carry their own label)
        out[f"{tag}_label"] = pd.Series(lab, index=out.index)
        out[f"{tag}_t"] = pd.Series(t, index=out.index)
    return out


def list_captures(road_dir, kind):
    d = Path(road_dir) / "signal_extractions" / kind
    return sorted(d.glob("*.csv"))
