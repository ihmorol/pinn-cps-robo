"""ROAD signal-mapper: verify the recovered ID map empirically.

Usage: python -I scripts/inspect_road.py ROAD_DIR
  ROAD_DIR = data/raw/zenodo-10462796/extracted/road

Checks:
  1. ID 0x6e0 (1760): four wheel-speed signals — near-identical pairwise in ambient? frozen during masquerade interval?
  2. ID 0xd0 (208): speedometer + reverse light — relation to wheel speeds in ambient? frozen during attack?
  3. ID 0x4e7 (1255): coolant temp — slow dynamics in ambient, frozen at max during attack?
  4. Label column = 1 exactly inside the published injection intervals?
"""
import csv
import sys
from collections import defaultdict

WHEEL_ID, SPEEDO_ID, COOLANT_ID = 1760, 208, 1255  # 0x6e0, 0xd0, 0x4e7


def load(path):
    rows = defaultdict(list)  # id -> list of (time, label, [signals])
    with open(path, newline="") as f:
        for r in csv.reader(f):
            if r[0] == "Label":
                continue
            label, t, can_id = int(r[0]), float(r[1]), int(r[2])
            sigs = []
            for v in r[3:]:
                if v != "":
                    try:
                        sigs.append(float(v))
                    except ValueError:
                        sigs.append(None)
                else:
                    sigs.append(None)
            rows[can_id].append((t, label, sigs))
    return rows


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    lo, hi = min(vals), max(vals)
    mean = sum(vals) / len(vals)
    return f"n={len(vals)} min={lo:.1f} max={hi:.1f} mean={mean:.1f}"


def main(road):
    amb = load(f"{road}/signal_extractions/ambient/ambient_dyno_drive_basic_long.csv")
    print("== AMBIENT (basic_long) ==")
    for name, cid in [("wheel 0x6e0", WHEEL_ID), ("speedo 0xd0", SPEEDO_ID), ("coolant 0x4e7", COOLANT_ID)]:
        rows = amb.get(cid, [])
        if not rows:
            print(f"{name}: not present"); continue
        n_sig = max(len(s) for _, _, s in rows)
        print(f"{name}: {len(rows)} msgs, {n_sig} signals, t=[{rows[0][0]:.1f}..{rows[-1][0]:.1f}]s")
        for i in range(n_sig):
            col = [s[i] for _, _, s in rows]
            print(f"   sig{i+1}: {stats(col)}")
    # pairwise wheel diffs
    w = [s for _, _, s in amb.get(WHEEL_ID, [])]
    if w and len(w[0]) >= 4:
        for a, b in [(0, 1), (0, 2), (0, 3)]:
            d = [abs(x[a] - x[b]) for x in w if x[a] is not None and x[b] is not None]
            print(f"   |wheel{a+1}-wheel{b+1}|: max={max(d):.2f} mean={sum(d)/len(d):.3f}")
        # speedometer vs wheel mean
        sp = {t: s for t, _, s in amb.get(SPEEDO_ID, [])}
        # find which 0xd0 signal tracks wheel mean: try each
        wm = [sum(x[:4]) / 4 for x in w if all(v is not None for v in x[:4])]
        pairs = [(t, s) for t, _, s in amb.get(SPEEDO_ID, []) for s in [s]]
        print("   (speedo->wheel check needs aligned sampling; see panel builder)")

    print("\n== MASQUERADE (correlated_signal_attack_1, interval 9.19-30.05s, id 0x6e0) ==")
    atk = load(f"{road}/signal_extractions/attacks/correlated_signal_attack_1_masquerade.csv")
    rows = atk.get(WHEEL_ID, [])
    inside = [s for t, l, s in rows if 9.191851 <= t <= 30.050109]
    outside = [s for t, l, s in rows if t < 9.191851]
    for tag, seg in [("outside", outside), ("inside", inside)]:
        print(f" {tag}: n={len(seg)}")
        for i in range(8):
            col = [s[i] for s in seg if i < len(s)]
            print(f"   sig{i+1}: {stats(col)}")
    lab_in = {l for t, l, _ in rows if 9.191851 <= t <= 30.050109}
    lab_out = {l for t, l, _ in rows if t < 9.191851}
    print(f" labels inside={lab_in} outside={lab_out}")

    print("\n== MASQUERADE (max_speedometer_1, interval 42.0-66.4s, id 0xd0) ==")
    atk2 = load(f"{road}/signal_extractions/attacks/max_speedometer_attack_1_masquerade.csv")
    rows = atk2.get(SPEEDO_ID, [])
    for tag, lo, hi in [("outside", 0, 42.009), ("inside", 42.009, 66.449)]:
        seg = [s for t, l, s in rows if lo <= t < hi]
        print(f" {tag}: n={len(seg)}")
        for i in range(min(14, max(len(s) for _, _, s in rows))):
            col = [s[i] for s in seg if i < len(s)]
            print(f"   sig{i+1}: {stats(col)}")


if __name__ == "__main__":
    main(sys.argv[1])
