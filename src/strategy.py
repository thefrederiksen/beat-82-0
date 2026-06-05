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
                 tail_cut=21.0, place_priority=("PF", "SG", "SF", "PG", "C"),
                 val_mode="face", target_sum=None, q_easy=17.0, q_max=26.0,
                 option_value=False):
        self.version = version
        self.skip_gain = (tuple(skip_gain) if isinstance(skip_gain, (list, tuple))
                          else (skip_gain,) * 5)
        self.tail_weight = tail_weight
        self.tail_cut = tail_cut
        self.place_priority = place_priority
        self.val_mode = val_mode  # "face" or "steady"
        # target-chasing (perfection mode): final OVR ~= steady_sum + 13.7
        # (calibrated offline, sd ~0.25), so 82-0 needs steady_sum >= ~95.8.
        # When the per-round need q is between q_easy (on pace anyway) and
        # q_max (hopeless), maximize P(this round >= q) instead of EV.
        self.target_sum = target_sum  # None disables chasing
        self.q_easy = q_easy
        self.q_max = q_max
        # when BOTH skips are held, a re-roll outcome can itself be re-rolled
        # with the other skip; price that option into the skip EVs
        self.option_value = option_value

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

        Skip decisions compare like-for-like values (current cell best vs
        re-roll EV in the same units: face or steady depending on val_mode).
        The actual pick within the kept cell maximizes exact marginal OVR
        (captures the 5/k spg/bpg interaction; exact in round 5, while
        steady valuation guides rounds 1-4 in steady mode)."""
        steady = self.val_mode == "steady"
        if steady:
            cur_face, _ = eng.best_steady_in_cell(team, era, open_pos, taken_ids)
        else:
            cur_face, _ = eng.best_face_in_cell(team, era, open_pos, taken_ids)

        # perfection chase: when the remaining per-round need q is demanding
        # but not hopeless, maximize P(value >= q) instead of expected value
        if self.target_sum is not None and steady and cur_face is not None:
            s_now = sum(p["_sp"] for p in roster)
            rounds_left = 5 - len(roster)
            q = (self.target_sum - s_now) / rounds_left
            if self.q_easy < q <= self.q_max:
                if cur_face >= q:
                    _, pick = eng.best_steady_in_cell(team, era, open_pos, taken_ids)
                    return ("pick", pick, self.place(pick, open_pos))
                hits = []  # (P_hit, action)
                if team_skip:
                    vals = eng.team_skip_values(era, team, open_pos, steady=True)
                    if vals:
                        hits.append((sum(1 for v in vals if v >= q) / len(vals),
                                     ("skip_team",)))
                if decade_skip:
                    vals = eng.decade_skip_values(team, era, open_pos, steady=True)
                    if vals:
                        hits.append((sum(1 for v in vals if v >= q) / len(vals),
                                     ("skip_decade",)))
                best_p, best_act = max(hits) if hits else (0.0, None)
                if best_p > 0:
                    return best_act
                # no path to the target this round: fall through to EV logic

        options = []  # (gain, action)
        both = team_skip and decade_skip and self.option_value
        if team_skip:
            if both:
                # each team outcome can still be decade-skipped afterwards:
                # value(t) = max(best(t, era), E_e[best(t, e)])
                vals = []
                for t in eng.teams:
                    if t == team:
                        continue
                    v = eng._cell_fast_best((t, era), open_pos, steady)
                    if v is None:
                        continue
                    dv = eng.decade_skip_values(t, era, open_pos, steady=steady)
                    if dv:
                        v = max(v, sum(dv) / len(dv))
                    vals.append(v)
            else:
                vals = eng.team_skip_values(era, team, open_pos, steady=steady)
            score = self._skip_score(vals)
            if score is not None:
                options.append((score - (cur_face if cur_face is not None else -99),
                                ("skip_team",)))
        if decade_skip:
            if both:
                # each era outcome can still be team-skipped afterwards
                vals = []
                from engine import ERAS
                for e in ERAS:
                    if e == era:
                        continue
                    v = eng._cell_fast_best((team, e), open_pos, steady)
                    if v is None:
                        continue
                    tv = eng.team_skip_values(e, team, open_pos, steady=steady)
                    if tv:
                        v = max(v, sum(tv) / len(tv))
                    vals.append(v)
            else:
                vals = eng.decade_skip_values(team, era, open_pos, steady=steady)
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

        if steady and round_idx < 4:
            _, pick = eng.best_steady_in_cell(team, era, open_pos, taken_ids)
        else:
            # final round (or face mode): exact marginal is the right objective
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


def v3():
    """v2 plus steady-state valuation: spg/bpg priced relative to the roster
    average the 5/k extrapolation supplies (fixes the early-round x5 inflation
    of marginal OVR and the face-value undervaluing of null-spg/bpg players).
    Offline (8000 games x 2 seeds): mean 70.5, P(82-0) 3.26-3.46% vs v2's
    69.15 / 2.43-2.57%."""
    return Policy(version="v3-steady-valuation",
                  skip_gain=(2.0, 1.5, 1.0, 0.5, 0.0),
                  tail_weight=0.0,
                  place_priority=("SG", "SF", "PG", "PF", "C"),
                  val_mode="steady")


def get(version_name):
    factories = {"v1-scripted": v1, "v2-declining-skips": v2,
                 "v3-steady-valuation": v3}
    return factories[version_name]()
