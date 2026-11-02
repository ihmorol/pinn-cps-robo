import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pinn_cps_robo.physics import inter_wheel_residual, continuity_residual, relation_residual, fit_scale, freeze_score


def test_inter_wheel_benign_small_attack_huge():
    benign = np.tile([100.0, 101.0, 99.0, 100.5], (10, 1))
    r = inter_wheel_residual(benign)
    assert r.max() <= 2.0
    attack = np.tile([6489.0, 1349.0, 0.0, 16383.0], (10, 1))  # observed ROAD masquerade payload
    ra = inter_wheel_residual(attack)
    assert ra.min() == 16383.0


def test_continuity_jump_detected():
    v = np.array([0.0] * 50 + [16383.0] * 50)  # frozen then max
    d = continuity_residual(v)
    assert d[50] == 16383.0
    assert d[10] == 0.0


def test_scale_fit_recovers_ratio():
    rng = np.random.default_rng(0)
    x = rng.uniform(1, 100, 1000)
    y = 0.5 * x + rng.normal(0, 0.1, 1000)
    s = fit_scale(x, y)
    assert abs(s - 0.5) < 0.01


def test_freeze_score_zero_for_constant():
    v = np.full(100, 7.0)
    assert freeze_score(v, 10).max() == 0.0
    v2 = np.concatenate([np.full(50, 7.0), np.linspace(7, 8, 50)])
    assert freeze_score(v2, 10)[-1] > 0.0


def test_relation_residual():
    r = relation_residual(np.array([10.0, 20.0]), np.array([5.0, 10.0]), 0.5)
    assert np.allclose(r, 0.0)
