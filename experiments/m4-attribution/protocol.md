# Protocol — M4 attribution: PINN vs physics-free twin (locked before results)

**Question (RQ3/H3):** is detection gain attributable to the *physics constraint* rather than learned capacity — and under what data regimes?

**Task.** One-step wheel-speed forecasting on the 0x6e0 stream: input [w1..w4, s6(interp)] → predict [w1..w4] next frame. MLP (64,64), ReLU, Adam 1e-3, batch 4096, standardized on ambient. Both models identical except the loss:
- **D2 PINN**: L = MSE(data) + λ·L_phys, λ=1 fixed a priori; L_phys = display-tracking (|mean(w_pred)·α − s6|²) + soft acceleration limit (relu(|Δw|/a_max − 1)², a_max = ambient per-capture max Δ).
- **D3 twin**: L = MSE(data) only.

**Data regimes (the experiment).** Train on {0.1 %, 1 %, 10 %, 100 %} of ambient wheel frames (seeded subsample). Held-out ambient temporal half = benign test. Attack test: the 3 wheel-masquerade captures (frame labels). Benign stress: the 4 accelerator captures (genuine but unusual dynamics).

**Metrics.** AP + recall@ambient-q0.999 per model per regime; FPR on accelerator captures (the attribution signal: unusual-but-real motion must NOT be flagged).

**Predictions (falsifiable).**
- P1: at 100 % data, D2 ≈ D3 (parity — the relation is learnable from 1M frames).
- P2: at 0.1–1 % data, D2 > D3 on benign-stress FPR (physics regularizes where data can't speak).
- P3: attack AP stays ≈1 for both at all regimes (the payload is grossly out-of-distribution).
If D3 beats D2 in any regime, that is the honest headline — physics priors are not free (Krishnapriyan/Grossmann lessons).

**Scope.** Attribution is per-stream (wheel); speedo/coolant classes are out of scope here (their physics is already analytical in D1). CPU budget: ≤ 15 min total.
