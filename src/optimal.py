"""Compute the provably optimal roster under the game's own scoring code.

Uses the exact engine replica (engine.py) including the 5/k null-spg/bpg
extrapolation, and searches all position-legal 5-player rosters built from
the full player pool (branch-and-bound over the top candidates per slot).

Usage: python src/optimal.py [top_n_per_slot]
"""
import itertools
import sys

from engine import Engine, POSITIONS

sys.stdout.reconfigure(encoding="ascii", errors="replace")


def main():
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    eng = Engine()

    # candidate pool per slot: top_n by steady value among eligible players
    cands = {}
    for pos in POSITIONS:
        rows = [p for p in eng.pool if pos in p["positions"]]
        rows.sort(key=lambda p: p["_sp"], reverse=True)
        cands[pos] = rows[:top_n]

    order = sorted(POSITIONS, key=lambda pos: -cands[pos][0]["_sp"])
    suffix_max = [0.0] * (len(order) + 1)
    for i in range(len(order) - 1, -1, -1):
        suffix_max[i] = suffix_max[i + 1] + cands[order[i]][0]["_sp"] + 2.0

    best = {"ovr": 0.0, "roster": None}

    def dfs(i, roster, ids, slugs, steady_sum):
        if i == len(order):
            ovr = eng.team_ovr(roster)
            if ovr > best["ovr"]:
                best["ovr"] = ovr
                best["roster"] = list(zip(order, roster))
            return
        # bound: even a generous overestimate of remaining slots cannot win
        if steady_sum + suffix_max[i] + 14.5 <= best["ovr"]:
            return
        for p in cands[order[i]]:
            if p["id"] in ids or p["baseSlug"] in slugs:
                continue  # no duplicate player-rows and no same human twice
            roster.append(p)
            ids.add(p["id"])
            slugs.add(p["baseSlug"])
            dfs(i + 1, roster, ids, slugs, steady_sum + p["_sp"])
            roster.pop()
            ids.discard(p["id"])
            slugs.discard(p["baseSlug"])

    dfs(0, [], set(), set(), 0.0)

    ovr = best["ovr"]
    print(f"OPTIMAL ROSTER (top {top_n} candidates/slot, same human once):")
    for pos, p in sorted(best["roster"], key=lambda x: POSITIONS.index(x[0])):
        print(f"  {pos:2} {p['player']:24} {p['team']} {p['era']}  "
              f"{p['ppg']}/{p['rpg']}/{p['apg']}/{p['spg']}/{p['bpg']}")
    print(f"OVR {ovr}  -> wins {eng.wins(ovr)}")
    print(f"(82-0 needs OVR >= 109.5; headroom {ovr - 109.5:.1f})")


if __name__ == "__main__":
    main()
