"""Evaluation helpers: AUC-PR, recall at ambient-quantile threshold, FPR."""
import numpy as np
from sklearn.metrics import average_precision_score


def ap_score(y, s):
    y = np.asarray(y, dtype=int)
    if y.sum() == 0 or y.sum() == len(y):
        return np.nan
    return float(average_precision_score(y, s))


def threshold_at(ambient_scores, q=0.999):
    return float(np.quantile(ambient_scores, q))


def recall_fpr(y, s, thr):
    y = np.asarray(y, dtype=int)
    s = np.asarray(s, dtype=float)
    flagged = s > thr
    rec = float(flagged[y == 1].mean()) if (y == 1).any() else np.nan
    fpr = float(flagged[y == 0].mean()) if (y == 0).any() else np.nan
    return rec, fpr
