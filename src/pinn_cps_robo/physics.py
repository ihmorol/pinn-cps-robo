"""Physics-consistency residual functions for CAN signal panels.

Pure functions over numpy arrays — no I/O. Each returns a residual time series
aligned with the input; larger = more physics-violating. These are the paper's
core object: every detector in the ladder consumes one or more of these.
"""
import numpy as np


def inter_wheel_residual(w):
    """w: (n, >=4) wheel-speed matrix. Max pairwise |diff| across the 4 wheels."""
    w = np.asarray(w, dtype=float)
    cols = w[:, :4]
    a, b = np.triu_indices(4, k=1)
    return np.max(np.abs(cols[:, a] - cols[:, b]), axis=1)


def continuity_residual(v, dt=None):
    """|first difference| of a series (optionally per unit time). Freeze -> 0 is
    NOT a violation by itself; a *jump* is. For frozen-vs-should-vary detection
    combine with freeze_score."""
    v = np.asarray(v, dtype=float)
    d = np.abs(np.diff(v, prepend=v[0]))
    if dt is not None:
        d = d / np.maximum(np.asarray(dt, dtype=float), 1e-9)
    return d


def relation_residual(x, y, scale):
    """|y - scale*x|: violation of a proportional signal relation
    (e.g., speedometer vs mean wheel speed). scale identified on ambient data."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return np.abs(y - scale * x)


def fit_scale(x, y):
    """Least-squares scale for y ≈ scale*x (through origin, robust fallback: median of ratios)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = (x > 0) & np.isfinite(x) & np.isfinite(y)
    if m.sum() < 10:
        return 1.0
    ratios = y[m] / x[m]
    med = float(np.median(ratios))
    ls = float(np.dot(x[m], y[m]) / max(np.dot(x[m], x[m]), 1e-12))
    return 0.5 * (med + ls)


def freeze_score(v, window):
    """Rolling std (zero = frozen). A signal frozen while the vehicle moves is
    the masquerade signature (payload holds one frame value)."""
    v = np.asarray(v, dtype=float)
    n = len(v)
    out = np.empty(n)
    csum = np.concatenate(([0.0], np.cumsum(v)))
    csum2 = np.concatenate(([0.0], np.cumsum(v * v)))
    for i in range(n):
        lo = max(0, i - window + 1)
        m = i - lo + 1
        s, s2 = csum[i + 1] - csum[lo], csum2[i + 1] - csum2[lo]
        out[i] = max(0.0, s2 / m - (s / m) ** 2) ** 0.5
    return out
