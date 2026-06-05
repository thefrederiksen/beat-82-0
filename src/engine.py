"""Exact offline replica of the 82-0.com Classic-mode engine (docs/sim-engine.md).

Provides the player pool indexed by (team, era) cell, weighted pick values,
the exact OVR/wins computation (verified to the decimal on games 1-5), and
roll-distribution helpers for skip expected-value math.
"""
import json
import os

ERAS = ("1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s")
POSITIONS = ("PG", "SG", "SF", "PF", "C")

# weighted "OVR points" per stat unit (100 * weight / team benchmark)
W = {
    "ppg": 100 * 0.46 / 133.4,
    "rpg": 100 * 0.25 / 39.7,
    "apg": 100 * 0.18 / 29.3,
    "spg": 100 * 0.07 / 6.1,
    "bpg": 100 * 0.04 / 3.2,
}

# wins == 82 requires displayed OVR (rounded to 1 decimal) >= this
PERFECT_OVR = 109.5

# typical roster averages among picks with spg/bpg data (used by the
# steady-state valuation: a steal value only helps relative to the average
# that the 5/k extrapolation would otherwise supply)
AVG_SPG = 1.3
AVG_BPG = 1.0


def _v(x):
    return 0.0 if x is None else float(x)


def load_pool():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "players_flat.json")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    return [p for p in rows if p["era"] in ERAS]


class Engine:
    def __init__(self):
        self.pool = load_pool()
        self.cells = {}
        for p in self.pool:
            self.cells.setdefault((p["team"], p["era"]), []).append(p)
        self.teams = sorted({t for t, _ in self.cells})
        # precompute face-value and steady-state points and, per cell, the
        # best value at each position (fast approximation for skip-EV scans)
        for p in self.pool:
            p["_fp"] = self.face_pts(p)
            p["_sp"] = self.steady_pts(p)
        self.cell_pos_best = {}
        self.cell_pos_best_steady = {}
        for cell, players in self.cells.items():
            best, best_s = {}, {}
            for p in players:
                for pos in p["positions"]:
                    if p["_fp"] > best.get(pos, -1.0):
                        best[pos] = p["_fp"]
                    if p["_sp"] > best_s.get(pos, -999.0):
                        best_s[pos] = p["_sp"]
            self.cell_pos_best[cell] = best
            self.cell_pos_best_steady[cell] = best_s

    # ---- pick valuation -------------------------------------------------

    @staticmethod
    def face_pts(p):
        """Weighted OVR points with spg/bpg at face value (nulls as 0)."""
        return sum(W[k] * _v(p[k]) for k in W)

    @staticmethod
    def steady_pts(p):
        """Weighted OVR points with spg/bpg priced RELATIVE to the roster
        average the 5/k extrapolation would supply anyway. A null player is
        neutral on defense stats; a non-null value only helps (hurts) by its
        distance above (below) the typical average, scaled by the ~5/(k+1)
        extrapolation factor (k ~= 3.5 -> factor ~1.1)."""
        base = (W["ppg"] * _v(p["ppg"]) + W["rpg"] * _v(p["rpg"])
                + W["apg"] * _v(p["apg"]))
        if p["spg"] is not None and p["spg"] > 0:
            base += 1.1 * W["spg"] * (p["spg"] - AVG_SPG)
        if p["bpg"] is not None and p["bpg"] > 0:
            base += 1.1 * W["bpg"] * (p["bpg"] - AVG_BPG)
        return base

    @staticmethod
    def team_ovr(roster):
        """Exact end-screen OVR for a roster (list of player rows), incl. the
        5/k null-spg/bpg extrapolation and the 1-decimal rounding."""
        if not roster:
            return 0.0
        s_ppg = sum(_v(p["ppg"]) for p in roster)
        s_rpg = sum(_v(p["rpg"]) for p in roster)
        s_apg = sum(_v(p["apg"]) for p in roster)
        spgs = [p["spg"] for p in roster if p["spg"] is not None and p["spg"] > 0]
        bpgs = [p["bpg"] for p in roster if p["bpg"] is not None and p["bpg"] > 0]
        adj_spg = sum(spgs) * (5 / len(spgs)) if spgs else 0.0
        adj_bpg = sum(bpgs) * (5 / len(bpgs)) if bpgs else 0.0
        ovr = 100 * (
            s_ppg / 133.4 * 0.46 + s_rpg / 39.7 * 0.25 + s_apg / 29.3 * 0.18
            + adj_spg / 6.1 * 0.07 + adj_bpg / 3.2 * 0.04
        )
        return round(ovr * 10) / 10

    @staticmethod
    def wins(ovr):
        """Exact win projection from the displayed (1-decimal) OVR."""
        return round(82 * min(ovr / 110, 1) ** 1.15)

    def marginal(self, roster, p):
        """Exact OVR gain of adding p to the current roster (captures the 5/k
        interaction that face_pts misses)."""
        return self.team_ovr(roster + [p]) - self.team_ovr(roster)

    # ---- cell queries ---------------------------------------------------

    def eligible(self, team, era, open_pos, taken_ids):
        """Players in a cell who fit any open slot and are not already picked."""
        out = []
        for p in self.cells.get((team, era), []):
            if p["id"] in taken_ids:
                continue
            if set(p["positions"]) & open_pos:
                out.append(p)
        return out

    def best_in_cell(self, team, era, open_pos, taken_ids, roster):
        """(value, player) of the best eligible pick by exact marginal OVR."""
        best_v, best_p = None, None
        for p in self.eligible(team, era, open_pos, taken_ids):
            val = self.marginal(roster, p)
            if best_v is None or val > best_v:
                best_v, best_p = val, p
        return best_v, best_p

    def best_face_in_cell(self, team, era, open_pos, taken_ids):
        """(face value, player) of the best eligible pick by face points --
        the same units the face skip-EV distributions use."""
        best_v, best_p = None, None
        for p in self.eligible(team, era, open_pos, taken_ids):
            if best_v is None or p["_fp"] > best_v:
                best_v, best_p = p["_fp"], p
        return best_v, best_p

    def best_steady_in_cell(self, team, era, open_pos, taken_ids):
        """(steady value, player) of the best eligible pick by steady points."""
        best_v, best_p = None, None
        for p in self.eligible(team, era, open_pos, taken_ids):
            if best_v is None or p["_sp"] > best_v:
                best_v, best_p = p["_sp"], p
        return best_v, best_p

    # ---- roll distributions (for skip EV) -------------------------------

    def all_cells(self):
        """Every rollable (team, era) cell (>=1 player), as the game draws them."""
        return list(self.cells.keys())

    def _cell_fast_best(self, cell, open_pos, steady=False):
        """Fast approximate best-pick value in a cell for the open slots
        (precomputed; ignores already-taken players, a negligible collision)."""
        best = (self.cell_pos_best_steady if steady else self.cell_pos_best).get(cell)
        if not best:
            return None
        vals = [best[pos] for pos in open_pos if pos in best]
        return max(vals) if vals else None

    def team_skip_values(self, era, exclude_team, open_pos, steady=False):
        """Approx best-pick value per possible outcome of a team skip
        (era locked, team re-rolled uniformly among teams with players)."""
        vals = []
        for t in self.teams:
            if t == exclude_team:
                continue
            v = self._cell_fast_best((t, era), open_pos, steady)
            if v is not None:
                vals.append(v)
        return vals

    def decade_skip_values(self, team, exclude_era, open_pos, steady=False):
        """Approx best-pick value per possible outcome of a decade skip
        (team locked, era re-rolled uniformly among eras with players)."""
        vals = []
        for e in ERAS:
            if e == exclude_era:
                continue
            v = self._cell_fast_best((team, e), open_pos, steady)
            if v is not None:
                vals.append(v)
        return vals
