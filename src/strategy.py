"""Versioned play policy for the 82-0 optimization program (see program.md).

A Policy decides, for each round state, one of:
  ("skip_team",)            burn the team skip (era locked, team re-rolled)
  ("skip_decade",)          burn the decade skip (team locked, era re-rolled)
  ("pick", player, slot)    pick this player and place them on this open slot

Decisions are EV-based using the exact offline engine. Parameters are tunable
offline via src/simulate.py; the live harness (src/play.py) runs the same code.
"""
from engine import Engine, POSITIONS


class Policy:
    """EV-driven skip policy + exact-marginal pick + slot-protection placement.

    Parameters:
      version          version string recorded in history JSONs
      skip_gain        burn a skip when (skip EV - current best) >= this;
                       scalar, or a 5-tuple of per-round thresholds (a skip
                       held to the end expires worthless, so later rounds
                       should demand less gain)
      tail_weight      adds tail_weight * P(outcome >= tail_cut) * 10 to skip EV
                       (variance seeking toward jackpot cells; 0 = pure EV)
      tail_cut         OVR-points level that counts as a jackpot outcome
      place_priority   placement order among eligible open slots (first match
                       wins); protects the rightmost slots for future jackpots
    """

    def __init__(self, version="v1-scripted", skip_gain=3.0, tail_weight=0.0,
                 tail_cut=21.0, place_priority=("PF", "SG", "SF", "PG", "C")):
        self.version = version
        self.skip_gain = (tuple(skip_gain) if isinstance(skip_gain, (list, tuple))
                          else (skip_gain,) * 5)
        self.tail_weight = tail_weight
        self.tail_cut = tail_cut
        self.place_priority = place_priority

    # ------------------------------------------------------------------

    def _skip_score(self, values):
        """Score a re-roll distribution: mean, plus optional jackpot-tail bonus."""
        if not values:
            return None
        mean = sum(values) / len(values)
        if self.tail_weight:
            p_tail = sum(1 for v in values if v >= self.tail_cut) / len(values)
            mean += self.tail_weight * p_tail * 10
        return mean

    def decide(self, eng: Engine, team, era, open_pos, taken_ids, roster,
               team_skip, decade_skip):
        """One decision for the current roll. Caller loops after a skip.

        Skip decisions compare FACE values (current cell best vs re-roll EV,
        same units); the actual pick within the kept cell maximizes exact
        marginal OVR (captures the 5/k spg/bpg interaction)."""
        cur_face, _ = eng.best_face_in_cell(team, era, open_pos, taken_ids)

        options = []  # (gain, action)
        if team_skip:
            vals = eng.team_skip_values(era, team, open_pos)
            score = self._skip_score(vals)
            if score is not None:
                options.append((score - (cur_face if cur_face is not None else -99),
                                ("skip_team",)))
        if decade_skip:
            vals = eng.decade_skip_values(team, era, open_pos)
            score = self._skip_score(vals)
            if score is not None:
                options.append((score - (cur_face if cur_face is not None else -99),
                                ("skip_decade",)))

        if cur_face is None:
            # no eligible player in this cell for the open slots: forced skip
            if options:
                return max(options)[1]
            raise RuntimeError(
                f"stuck: no eligible player in {team}/{era} for {sorted(open_pos)} "
                "and no skips left")

        round_idx = len(roster)  # 0-based: rounds played so far
        best_gain, best_action = max(options) if options else (None, None)
        if best_gain is not None and best_gain >= self.skip_gain[round_idx]:
            return best_action

        _, pick = eng.best_in_cell(team, era, open_pos, taken_ids, roster)
        slot = self.place(pick, open_pos)
        return ("pick", pick, slot)

    def place(self, player, open_pos):
        """Choose the open slot for a picked player: first eligible slot in
        place_priority order (keeps C, then PG, open for future jackpots)."""
        eligible = set(player["positions"]) & open_pos
        for s in self.place_priority:
            if s in eligible:
                return s
        raise RuntimeError(f"{player['player']} fits none of {sorted(open_pos)}")


# named versions ------------------------------------------------------------

def v1():
    """Scripted version of the manual v1 play (games 2-5): pure-EV skips at
    +3.0 gain, exact-marginal picks, C/PG-protecting placement."""
    return Policy(version="v1-scripted", skip_gain=3.0, tail_weight=0.0)


def v2():
    """Tuned offline (simulate.py --tune 6000, 2026-06-05): declining skip
    thresholds (a held skip expires worthless, so demand less gain late) and
    SG-SF-PG-PF-C placement (protect C, then PF). Offline: mean 69.05 wins,
    P(82-0) 2.38% vs v1's 67.65 / 1.07%."""
    return Policy(version="v2-declining-skips",
                  skip_gain=(2.0, 1.5, 1.0, 0.5, 0.0),
                  tail_weight=0.0,
                  place_priority=("SG", "SF", "PG", "PF", "C"))


def get(version_name):
    factories = {"v1-scripted": v1, "v2-declining-skips": v2}
    return factories[version_name]()
