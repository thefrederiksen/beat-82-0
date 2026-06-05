# history/ -- append-only game records

One JSON per game, `game-NNN.json`, numbering global and monotonic. NEVER delete or
edit a record after the game is played (negative results are first-class data; see
program.md section 5). Games 001-005 were backfilled from the manual session logged
in docs/game-log.md (2026-06-05).

## Schema

| Field | Meaning |
|-------|---------|
| game | global game number (int, matches filename) |
| played_at | local timestamp (approx for the manual era) |
| mode | "classic" (HoopIQ would be "hoopiq"; none played yet) |
| strategy_version | policy that produced the picks (see program.md scoreboard) |
| rounds[] | one entry per round (5 per game) |
| rounds[].rolls[] | every (team, era) the slot machine showed this round, in order; `skip_after` = "team" / "decade" / null = which skip was burned AFTER seeing this roll |
| rounds[].pick | player chosen from the final roll |
| rounds[].position | court slot the player was placed on (PG/SG/SF/PF/C) |
| rounds[].stats | the player's card stats; null spg/bpg = no data for that era (handled by the engine's 5/k extrapolation, see docs/sim-engine.md) |
| rounds[].ovr_pts | weighted OVR contribution: 0.345*ppg + 0.630*rpg + 0.614*apg + 1.148*spg + 1.250*bpg (nulls as 0) |
| rounds[].rationale | why this pick / skip decision was made (mined during ANALYZE) |
| totals | end-screen team stat totals (raw sums) |
| result | end-screen result: wins, losses, ovr ("pts"), grade, label |

Consistency invariant: `result.ovr` must equal the formula in docs/sim-engine.md
applied to `totals` (with the 5/k spg/bpg adjustment). All 5 backfilled games verify.

Read with: `python src/scoreboard.py`
