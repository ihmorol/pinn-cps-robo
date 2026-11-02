# Protocol — M2b: physics taxonomy of the FABRICATION variants (locked before results)

**Question.** Do the non-masquerade fabrication captures ("flam"-class, described by the ROAD authors as the most stealthy fabrication possible in public data) violate the same physics laws as the masquerades? This extends the M2 taxonomy to the stealthiest value-crafted class and tests the boundary finding's other half.

**Method.** Decode the raw `.log` captures with the anonymized DBC layouts (Intel, start|len): 0x6e0 = four 14-bit wheel speeds (bits 5/21/37/53); 0xd0 = 7 signals; 0x4e7 = 2 signals. VALIDATION GATE: the decoder must reproduce the published CSV values on a masquerade capture before any fabrication result is reported; mismatch = decoder bug, stop and fix. Injection intervals from `attacks/metadata.json` (time split, ±0.05 s margin, as in M2). Same laws L1–L7, same floors as M3 (per-capture ambient max).

**Predictions (falsifiable).**
- P4: correlated fabrications carry four *mutually consistent* wheel speeds → L1 does not fire; L3 fires only via the injection entry/exit jumps.
- P5: max-speedometer and max-coolant fabrications exceed value envelopes → L5/L6 fire.
- P6: reverse-light fabrications behave like their masquerade twins (bit patch only) → no law fires.
If P4 fails (L1 fires), the "correlated" name is a misnomer in the data and the class is not stealthy to physics — report as-is.
