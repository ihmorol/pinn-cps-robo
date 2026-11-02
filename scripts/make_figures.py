"""Paper figures -> paper/figures/*.png (committed) + reports/ duplicates (gitignored)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pinn_cps_robo.data import load_capture, list_captures
from pinn_cps_robo.physics import inter_wheel_residual

ROAD = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[1] / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 9, "figure.dpi": 150})

# --- Fig 1: masquerade timeline (correlated_signal_attack_1) ---
fr = load_capture(ROAD / "signal_extractions/attacks/correlated_signal_attack_1_masquerade.csv")
w = fr["wheel"].sort_values("t").reset_index(drop=True)
t = w["t"].to_numpy()
lo, hi = 9.191851, 30.050109
fig, axes = plt.subplots(2, 1, figsize=(6.5, 3.4), sharex=True)
for i, c in enumerate(["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]):
    axes[0].plot(t, w[f"s{i+1}"], color=c, lw=0.6, label=f"wheel {i+1}")
axes[0].axvspan(lo, hi, color="red", alpha=0.12)
axes[0].set_ylabel("wheel speed (raw)")
axes[0].legend(ncol=4, loc="upper right", fontsize=7)
axes[0].set_title("Correlated wheel-speed masquerade (ROAD): payload frozen, inter-wheel consistency broken", fontsize=8)
r = inter_wheel_residual(w[["s1", "s2", "s3", "s4"]].to_numpy())
axes[1].semilogy(t, np.maximum(r, 1e-1), lw=0.6, color="k")
axes[1].axvspan(lo, hi, color="red", alpha=0.12)
axes[1].set_ylabel("inter-wheel\nresidual")
axes[1].set_xlabel("time (s)")
fig.tight_layout()
fig.savefig(OUT / "fig1_timeline.png")
plt.close(fig)

# --- Fig 2: PR curves stage 1 (per class x detector) ---
from pinn_cps_robo.detectors import ambient_reference, score_range, score_physics, _roll_std
from pinn_cps_robo.physics import continuity_residual, relation_residual, fit_scale
from sklearn.metrics import precision_recall_curve, average_precision_score

amb_caps = [load_capture(c) for c in list_captures(ROAD, "ambient") if c.stem.startswith("ambient_")]
ref = ambient_reference(amb_caps)
CLASS_STREAM = {"correlated": "wheel", "max_speedometer": "speedo", "reverse_light": "speedo",
                "max_engine_coolant": "coolant"}


def runs(v):
    v = np.asarray(v, dtype=float)
    run = np.ones(len(v))
    for i in range(1, len(v)):
        if v[i] == v[i - 1]:
            run[i] = run[i - 1] + 1
    return run


def stream_scores(fr, stream):
    f = fr[stream]
    out = {"D0a range": score_range(f, ref, stream)}
    sig = {"wheel": "s1", "speedo": "s6", "coolant": "s2"}[stream]
    out["D0b const-run"] = runs(f[sig].to_numpy(dtype=float)) / max(ref[f"max_run_{stream}"], 1.0)
    out["D1 physics"] = score_physics(f, ref, stream, cap_frames=fr)
    return out, f


fig, axes = plt.subplots(1, 4, figsize=(9.5, 2.5))
for ax, (cls, stream) in zip(axes, CLASS_STREAM.items()):
    keys = ["D0a range", "D0b const-run", "D1 physics"]
    y_all, s_all = {k: [] for k in keys}, {k: [] for k in keys}
    for cap in list_captures(ROAD, "attacks"):
        if not cap.stem.startswith(cls):
            continue
        fr = load_capture(cap)
        ss, f = stream_scores(fr, stream)
        y = f["label"].to_numpy(dtype=int)
        for k, v in ss.items():
            sv = pd.Series(v, index=f.index).dropna()
            s_all[k].append(sv.to_numpy())
            y_all[k].append(y[[f.index.get_loc(i) for i in sv.index]])
    for k in s_all:
        y = np.concatenate(y_all[k]); s = np.concatenate(s_all[k])
        p, r, _ = precision_recall_curve(y, s)
        ap = average_precision_score(y, s)
        ax.plot(r, p, lw=1.2, label=f"{k} (AP {ap:.2f})")
    ax.set_title(cls.replace("_", " "), fontsize=8)
    ax.set_xlabel("recall")
    if ax is axes[0]:
        ax.set_ylabel("precision")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    ax.legend(fontsize=6, loc="lower left")
fig.tight_layout()
fig.savefig(OUT / "fig2_pr_stage1.png")
plt.close(fig)

# --- Fig 3: attribution regimes ---
att = pd.read_csv(Path(__file__).resolve().parents[1] / "experiments/m4-attribution/results/attribution.csv")
fig, ax = plt.subplots(figsize=(3.4, 2.6))
for name, c in [("D3_twin", "#7f7f7f"), ("D2_pinn", "#1f77b4")]:
    d = att[att.model == name].sort_values("train_frac")
    ax.plot(d.train_frac, d.AP, marker="o", ms=4, color=c, label=name.replace("_", " "))
ax.set_xscale("log")
ax.set_xlabel("ambient training fraction")
ax.set_ylabel("AP (wheel masquerade)")
ax.legend(fontsize=7)
ax.set_title("Physics constraint vs free twin", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "fig3_attribution.png")
plt.close(fig)

# --- Fig 4: taxonomy heatmaps (masquerade + fabrication families) ---
tax_m = pd.read_csv(Path(__file__).resolve().parents[1] / "experiments/m2-physics-taxonomy/results/taxonomy.csv").dropna(subset=["ratio"])
tax_f = pd.read_csv(Path(__file__).resolve().parents[1] / "experiments/m2b-fabrication/results/fabrication_taxonomy.csv").dropna(subset=["ratio"])
order_law = ["L1_interwheel", "L2_speedo_rel", "L3_continuity", "L4_coolant_jump", "L5_speedo_env", "L6_coolant_env", "L7_speedo_freeze(inv)"]


def fam_pivot(t):
    t = t[t["class"] != "no_injection"].copy()
    piv = t.pivot_table(index="law", columns="class", values="ratio", aggfunc="max")
    return piv.reindex([l for l in order_law if l in piv.index])


pivs = [fam_pivot(tax_m), fam_pivot(tax_f)]
titles = ["masquerade captures", "fabrication captures"]
fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.9))
vals = [np.log10(p.replace(0, np.nan)).stack() for p in pivs]
vmin = min(v.min() for v in vals)
vmax = max(v.max() for v in vals)
for ax, piv, ttl in zip(axes, pivs, titles):
    im = ax.imshow(np.log10(piv.values), aspect="auto", cmap="viridis", vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(piv.columns)), [c.replace("_", "\n") for c in piv.columns], fontsize=6)
    ax.set_yticks(range(len(piv.index)), [l.replace("_", " ").replace("(inv)", "") for l in piv.index], fontsize=6)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.3g}", ha="center", va="center", fontsize=5,
                        color="white" if np.log10(v) < (vmin + vmax) / 2 else "black")
    ax.set_title(ttl, fontsize=8)
fig.colorbar(im, ax=axes, shrink=0.85, label="max inside/outside ratio (log)")
fig.savefig(OUT / "fig4_taxonomy.png")
plt.close(fig)

print("figures written:", sorted(p.name for p in OUT.glob("*.png")))
