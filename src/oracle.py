"""Pick oracle for 82-0.com Classic mode - ranks players by true OVR contribution.

Reverse-engineered formula (see docs/sim-engine.md):
  OVR  = 100 * ( sumPPG/133.4*0.46 + sumRPG/39.7*0.25 + sumAPG/29.3*0.18
                 + adjSPG/6.1*0.07 + adjBPG/3.2*0.04 )
  wins = round( 82 * min(OVR/110, 1)^1.15 )
  82-0 requires OVR >= ~109.4 (i.e. avg ~21.9 OVR pts per player).

Per-unit OVR points: PPG 0.3448, RPG 0.6297, APG 0.6143, SPG 1.1475, BPG 1.2500.
adjSPG/adjBPG: sum of non-null values scaled by 5/k (k = players with data),
so null spg/bpg defers to the roster average instead of hurting.

Usage: python oracle.py TEAM ERA [top_n]
       python oracle.py --eras TEAM      (best weighted pick per era for a team)
       python oracle.py --teams ERA      (best weighted pick per team for an era)
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="ascii", errors="replace")

W_PPG = 100 * 0.46 / 133.4
W_RPG = 100 * 0.25 / 39.7
W_APG = 100 * 0.18 / 29.3
W_SPG = 100 * 0.07 / 6.1
W_BPG = 100 * 0.04 / 3.2


def norm_era(s):
    s = s.lower().replace("'", "")
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 2:
        digits = ("19" if int(digits) >= 50 else "20") + digits
    return digits + "s"


def v(x):
    return 0.0 if x is None else float(x)


def ovr_pts(p):
    """Player OVR contribution, spg/bpg at face value when present."""
    return (W_PPG * v(p["ppg"]) + W_RPG * v(p["rpg"]) + W_APG * v(p["apg"])
            + W_SPG * v(p["spg"]) + W_BPG * v(p["bpg"]))


def raw_sum(p):
    return v(p["ppg"]) + v(p["rpg"]) + v(p["apg"]) + v(p["spg"]) + v(p["bpg"])


def load():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "players_flat.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def show(rows, top_n):
    rows.sort(key=ovr_pts, reverse=True)
    hdr = (f"{'player':26} {'pos':9} {'PTS':>5} {'REB':>5} {'AST':>5} {'STL':>5} {'BLK':>5}"
           f" {'SUM':>6} {'OVRpts':>7}")
    print(hdr)
    print("-" * len(hdr))
    for p in rows[:top_n]:
        def fmt(x):
            return "  n/a" if x is None else f"{x:5.1f}"
        print(f"{p['player']:26} {'/'.join(p['positions']):9} {fmt(p['ppg'])} {fmt(p['rpg'])}"
              f" {fmt(p['apg'])} {fmt(p['spg'])} {fmt(p['bpg'])}"
              f" {raw_sum(p):6.1f} {ovr_pts(p):7.2f}")


def main():
    pool = load()
    if sys.argv[1] == "--eras":
        team = sys.argv[2].upper()
        print(f"Best weighted pick per era for {team} (game eras only):")
        for era in ("1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"):
            rows = [p for p in pool if p["team"] == team and p["era"] == era]
            if not rows:
                print(f"  {era}: (no players)")
                continue
            best = max(rows, key=ovr_pts)
            print(f"  {era}: {best['player']:24} {'/'.join(best['positions']):9}"
                  f" OVRpts {ovr_pts(best):6.2f}")
        return
    if sys.argv[1] == "--teams":
        era = norm_era(sys.argv[2])
        print(f"Best weighted pick per team for {era}:")
        out = []
        for team in sorted({p["team"] for p in pool}):
            rows = [p for p in pool if p["team"] == team and p["era"] == era]
            if not rows:
                continue
            best = max(rows, key=ovr_pts)
            out.append((ovr_pts(best), team, best))
        out.sort(reverse=True)
        for pts, team, best in out:
            print(f"  {team}: {best['player']:24} {'/'.join(best['positions']):9}"
                  f" OVRpts {pts:6.2f}")
        return

    team = sys.argv[1].upper()
    era = norm_era(sys.argv[2])
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    rows = [p for p in pool if p["team"] == team and p["era"] == era]
    if not rows:
        print(f"No players for {team} {era}")
        return
    print(f"{team} {era}: {len(rows)} players")
    show(rows, top_n)


if __name__ == "__main__":
    main()
