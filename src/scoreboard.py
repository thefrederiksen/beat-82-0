"""Scoreboard for the 82-0 optimization program (see program.md).

Reads history/game-*.json (append-only game records), prints a per-game table,
the best 3-consecutive-game average per strategy version, and the all-time best.

Usage: python src/scoreboard.py
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="ascii", errors="replace")

TARGET_AVG = 82.0


def load_games():
    pattern = os.path.join(os.path.dirname(__file__), "..", "history", "game-*.json")
    games = []
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as f:
            games.append(json.load(f))
    games.sort(key=lambda g: g["game"])
    return games


def best3(wins):
    """Best average over 3 consecutive entries; None if fewer than 3."""
    if len(wins) < 3:
        return None, None
    best, at = None, None
    for i in range(len(wins) - 2):
        avg = sum(wins[i:i + 3]) / 3
        if best is None or avg > best:
            best, at = avg, i
    return best, at


def main():
    games = load_games()
    if not games:
        print("No games in history/.")
        return

    print(f"{'game':>4} {'version':28} {'wins':>4} {'ovr':>6} {'grade':>5}  label")
    print("-" * 66)
    for g in games:
        r = g["result"]
        print(f"{g['game']:>4} {g['strategy_version']:28} {r['wins']:>4} "
              f"{r['ovr']:>6.1f} {r['grade']:>5}  {r['label']}")

    print()
    all_time_best, all_time_detail = None, ""
    versions = []
    for g in games:
        v = g["strategy_version"]
        if not versions or versions[-1][0] != v:
            versions.append((v, []))
        versions[-1][1].append(g)
    for v, vg in versions:
        wins = [g["result"]["wins"] for g in vg]
        avg, at = best3(wins)
        if avg is None:
            print(f"{v}: {len(wins)} game(s), need 3 consecutive for a score")
            continue
        ids = [g["game"] for g in vg[at:at + 3]]
        detail = f"games {ids[0]}-{ids[-1]} ({', '.join(str(w) for w in wins[at:at+3])})"
        print(f"{v}: best-3 avg {avg:.2f}  [{detail}]")
        if all_time_best is None or avg > all_time_best:
            all_time_best, all_time_detail = avg, f"{v}, {detail}"

    print()
    milestones = [g["game"] for g in games if g["result"]["wins"] == 82]
    print(f"ALL-TIME BEST: {all_time_best:.2f} ({all_time_detail})"
          if all_time_best is not None else "ALL-TIME BEST: n/a")
    print(f"MILESTONE (first 82-0): "
          f"{'game ' + str(milestones[0]) if milestones else 'not yet'}")
    status = ("REACHED" if all_time_best is not None and all_time_best >= TARGET_AVG
              else "not reached")
    print(f"TARGET (3-game avg {TARGET_AVG:.0f}): {status}")


if __name__ == "__main__":
    main()
