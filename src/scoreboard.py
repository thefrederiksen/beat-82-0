"""Scoreboard for the 82-0 optimization program (see program.md).

Reads history/game-*.json (append-only game records), prints a per-game table,
the best 3-consecutive-game average per strategy version, and the all-time best.

Usage: python src/scoreboard.py                 (terminal report)
       python src/scoreboard.py --update-page   (regenerate the scoreboard section
                                                 in FOLLOW-ALONG.md, phone-friendly)
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="ascii", errors="replace")

TARGET_AVG = 82.0
PAGE = os.path.join(os.path.dirname(__file__), "..", "FOLLOW-ALONG.md")
MARK_START = "<!-- SCOREBOARD:START -->"
MARK_END = "<!-- SCOREBOARD:END -->"
RECENT_GAMES = 15


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


def version_groups(games):
    """Games grouped by consecutive strategy_version runs, in play order."""
    groups = []
    for g in games:
        v = g["strategy_version"]
        if not groups or groups[-1][0] != v:
            groups.append((v, []))
        groups[-1][1].append(g)
    return groups


def all_time_best(games):
    """(best_avg, version, [3 games]) across version groups, or (None, None, None)."""
    best, best_v, best_games = None, None, None
    for v, vg in version_groups(games):
        wins = [g["result"]["wins"] for g in vg]
        avg, at = best3(wins)
        if avg is not None and (best is None or avg > best):
            best, best_v, best_games = avg, v, vg[at:at + 3]
    return best, best_v, best_games


def progress_bar(value, target, width=20):
    filled = int(round(width * min(value / target, 1.0)))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def page_markdown(games):
    """Phone-friendly scoreboard markdown for FOLLOW-ALONG.md."""
    best, best_v, bg = all_time_best(games)
    milestones = [g["game"] for g in games if g["result"]["wins"] == 82]
    latest = games[-1]
    lines = ["## Live scoreboard", ""]

    if best is not None:
        bar = progress_bar(best, TARGET_AVG)
        lines += [f"**Best 3-game average: {best:.2f} wins** "
                  f"(games {bg[0]['game']}-{bg[-1]['game']}: "
                  f"{', '.join(str(g['result']['wins']) for g in bg)})",
                  "",
                  f"`{bar}` **{best:.2f} / {TARGET_AVG:.0f}**", ""]
    top = max(games, key=lambda g: g["result"]["wins"])
    lines += [f"**Best single game: {top['result']['wins']}-{top['result']['losses']}** "
              f"(game {top['game']}, rated \"{top['result']['label']}\")",
              "",
              "**First 82-0:** " + (f"GAME {milestones[0]} -- DONE!" if milestones
                                    else "not yet... the chase is on"),
              "",
              f"*{len(games)} games played -- latest: game {latest['game']}, "
              f"{latest['result']['wins']}-{latest['result']['losses']} "
              f"({latest['played_at'].split('T')[0]})*",
              "", "### Recent games", "",
              "| # | Result | Rating | Grade |",
              "|--:|:------:|------:|:-----:|"]
    for g in reversed(games[-RECENT_GAMES:]):
        r = g["result"]
        mark = " **<-- 82-0!**" if r["wins"] == 82 else ""
        lines.append(f"| {g['game']} | {r['wins']}-{r['losses']}{mark} "
                     f"| {r['ovr']:.1f} | {r['grade']} |")
    if len(games) > RECENT_GAMES:
        lines += ["", f"*Showing the last {RECENT_GAMES} of {len(games)} games -- "
                      "full records in [history/](history/).*"]

    lines += ["", "### Strategy versions", "",
              "| Strategy | Games | Best 3-game avg |",
              "|:---------|:-----:|----------------:|"]
    for v, vg in version_groups(games):
        wins = [g["result"]["wins"] for g in vg]
        avg, _ = best3(wins)
        ids = f"{vg[0]['game']}-{vg[-1]['game']}" if len(vg) > 1 else str(vg[0]["game"])
        cell = f"**{avg:.2f}**" if avg is not None else "(need 3 games)"
        lines.append(f"| `{v}` | {ids} | {cell} |")
    return "\n".join(lines)


def update_page(games):
    with open(PAGE, encoding="utf-8") as f:
        text = f.read()
    start = text.index(MARK_START) + len(MARK_START)
    end = text.index(MARK_END)
    new = text[:start] + "\n" + page_markdown(games) + "\n" + text[end:]
    with open(PAGE, "w", encoding="ascii", newline="\n") as f:
        f.write(new)
    print(f"updated {os.path.normpath(PAGE)}")


def main():
    games = load_games()
    if games and "--update-page" in sys.argv:
        update_page(games)
        return
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
