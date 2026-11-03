import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pinn_cps_robo.detectors import ambient_reference, score_range, score_physics, _roll_std


def _toy_frames(n=500, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 0.01
    w = pd.DataFrame({"t": t, "label": 0,
                      "s1": 100 + rng.normal(0, 1, n),
                      "s2": 100 + rng.normal(0, 1, n),
                      "s3": 100 + rng.normal(0, 1, n),
                      "s4": 100 + rng.normal(0, 1, n)})
    sp = pd.DataFrame({"t": t, "label": 0,
                       "s1": np.zeros(n), "s2": np.zeros(n), "s3": np.zeros(n), "s4": np.zeros(n),
                       "s5": rng.normal(0, 1, n),
                       "s6": 0.5 * (w.s1 + w.s2 + w.s3 + w.s4) / 4, "s7": np.zeros(n)})
    c = pd.DataFrame({"t": t[::10], "label": 0, "s1": 20.0, "s2": 100 + 0.01 * t[::10]})
    return {"wheel": w, "speedo": sp, "coolant": c}


def test_ambient_reference_floors_positive():
    frames = [_toy_frames(seed=s) for s in range(3)]
    ref = ambient_reference(frames)
    assert ref["floor_L1"] > 0
    assert ref["floor_L3"] > 0
    assert ref["floor_L2d"] > 0
    assert 0.4 < ref["alpha"] < 0.6  # s6 = 0.5 * wheel mean


def test_score_range_flags_only_exceedance():
    fr = _toy_frames()
    ref = ambient_reference([fr])
    clean = score_range(fr["speedo"], ref, "speedo")
    assert np.all(clean == 0)
    odd = fr["speedo"].copy()
    odd.loc[7, "s6"] = 1e6  # far outside ambient envelope
    flagged = score_range(odd, ref, "speedo")
    assert flagged[7] > 0 and flagged.sum() == flagged[7]


def test_score_physics_wheel_catches_inconsistent_payload():
    fr = _toy_frames()
    ref = ambient_reference([fr])
    atk = fr["wheel"].copy()
    atk.loc[10:20, ["s1", "s2", "s3", "s4"]] = [6489.0, 1349.0, 0.0, 16383.0]
    s = score_physics(atk, ref, "wheel", cap_frames={"wheel": atk, "speedo": fr["speedo"], "coolant": fr["coolant"]})
    assert s[10:21].min() > 1.0   # flagged (above ambient-normalized floor)
    assert s[:10].max() < 1.0     # benign frames below floor


def test_roll_std_matches_naive():
    rng = np.random.default_rng(1)
    v = rng.normal(0, 3, 300)
    k = 20
    fast = _roll_std(v, k)
    for i in range(100, 110):
        lo = max(0, i - k + 1)
        assert abs(fast[i] - v[lo:i + 1].std(ddof=0)) < 1e-9
