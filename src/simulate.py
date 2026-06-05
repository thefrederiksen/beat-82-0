"""Offline Monte Carlo of full 82-0.com games under a Policy.

The slot machine is fully known (uniform over rollable (team, era) cells;
team skip locks era, decade skip locks team -- docs/sim-engine.md), so policy
changes can be evaluated over thousands of games before risking official ones.

Usage: python src/simulate.py [n_games] [seed]        single policy report
       python src/simulate.py --tune [n_games]        grid-search parameters
"""
import random
import sys

from engine import Engine, ERAS, POSITIONS
from strategy import Policy, v1

sys.stdout.reconfigure(encoding="ascii", errors="replace")


def play_one(eng, pol, rng):
    """Simulate one full game; returns (wins, ovr, picks).

    Rare edge case: a rolled cell can have NO player fitting the open slots
    with no skips left (a soft-lock in the real game too -- the only live
    recourse is abandoning the game, which records nothing). The sim re-rolls
    the cell so comparisons stay on completed games.
    """
    open_pos = set(POSITIONS)
    taken_ids = set()
    roster = []
    team_skip, decade_skip = True, True
    cells = eng.all_cells()

    for _ in range(5):
        team, era = cells[rng.randrange(len(cells))]
        while eng.best_face_in_cell(team, era, open_pos, taken_ids)[0] is None \
                and not (team_skip or decade_skip):
            team, era = cells[rng.randrange(len(cells))]  # soft-lock re-roll
        while True:
            action = pol.decide(eng, team, era, open_pos, taken_ids, roster,
                                team_skip, decade_skip)
            if action[0] == "skip_team":
                team_skip = False
                choices = [t for t in eng.teams
                           if t != team and (t, era) in eng.cells]
                team = choices[rng.randrange(len(choices))]
            elif action[0] == "skip_decade":
                decade_skip = False
                choices = [e for e in ERAS
                           if e != era and (team, e) in eng.cells]
                era = choices[rng.randrange(len(choices))]
            else:
                _, player, slot = action
                roster.append(player)
                taken_ids.add(player["id"])
                open_pos.discard(slot)
                break

    ovr = eng.team_ovr(roster)
    return eng.wins(ovr), ovr, roster


def evaluate(pol, n_games, seed=1):
    eng = Engine()
    rng = random.Random(seed)
    wins = []
    perfects = 0
    for _ in range(n_games):
        w, ovr, _ = play_one(eng, pol, rng)
        wins.append(w)
        if w == 82:
            perfects += 1
    mean = sum(wins) / len(wins)
    # distribution of 3-consecutive averages (the program metric)
    best3s = [sum(wins[i:i + 3]) / 3 for i in range(len(wins) - 2)]
    return {
        "mean_wins": mean,
        "p_perfect": perfects / n_games,
        "p75_wins": sorted(wins)[int(0.75 * len(wins))],
        "mean_best3_window": sum(best3s) / len(best3s) if best3s else mean,
        "wins": wins,
    }


def report(name, stats):
    print(f"{name:34} mean {stats['mean_wins']:6.2f}  P(82-0) "
          f"{stats['p_perfect']*100:5.2f}%  p75 {stats['p75_wins']:3d}")


def tune(n_games):
    """Grid-search skip_gain x tail_weight x placement priority."""
    print(f"tuning over {n_games} simulated games per config...")
    base_seed = 7
    results = []
    priorities = [
        ("PF", "SG", "SF", "PG", "C"),
        ("SG", "PF", "SF", "PG", "C"),
        ("SF", "SG", "PF", "PG", "C"),
        ("SF", "SG", "PG", "PF", "C"),
        ("SG", "SF", "PG", "PF", "C"),
    ]
    gain_schedules = {
        "flat0.5": (0.5,) * 5,
        "flat1": (1.0,) * 5,
        "flat2": (2.0,) * 5,
        "flat3": (3.0,) * 5,
        "decl-3to0": (3.0, 2.0, 1.0, 0.5, 0.0),
        "decl-2to0": (2.0, 1.5, 1.0, 0.5, 0.0),
        "decl-1to0": (1.0, 0.75, 0.5, 0.25, 0.0),
        "decl-05to0": (0.5, 0.4, 0.3, 0.15, 0.0),
    }
    for gname, gains in gain_schedules.items():
        for pp in priorities:
            pol = Policy(version="tune", skip_gain=gains, place_priority=pp)
            stats = evaluate(pol, n_games, seed=base_seed)
            results.append((stats["mean_wins"], stats["p_perfect"], gname, pp))
            print(f"  gain={gname:11} place={''.join(s[0] for s in pp)}  "
                  f"mean {stats['mean_wins']:6.2f}  "
                  f"P(82-0) {stats['p_perfect']*100:5.2f}%", flush=True)
    results.sort(reverse=True)
    print("\ntop 8 by mean wins:")
    for mean, pp82, g, pp in results[:8]:
        print(f"  mean {mean:6.2f}  P(82-0) {pp82*100:5.2f}%  "
              f"gain={g} place={'-'.join(pp)}")
    print("\ntop 8 by P(82-0):")
    for mean, pp82, g, pp in sorted(results, key=lambda r: (-r[1], -r[0]))[:8]:
        print(f"  P(82-0) {pp82*100:5.2f}%  mean {mean:6.2f}  "
              f"gain={g} place={'-'.join(pp)}")


def main():
    if "--tune" in sys.argv:
        n = int(sys.argv[sys.argv.index("--tune") + 1]) \
            if len(sys.argv) > sys.argv.index("--tune") + 1 else 1000
        tune(n)
        return
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    stats = evaluate(v1(), n, seed)
    report("v1-scripted", stats)


if __name__ == "__main__":
    main()
