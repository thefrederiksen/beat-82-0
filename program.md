# program.md -- The 82-0 Optimization Program

A Karpathy-style improvement loop for beating 82-0.com: treat the play strategy as a
model, treat games as evaluation runs, keep ALL run history, and only promote a new
strategy version when it measurably beats the previous best on a fixed metric.

```
        +-------------------------------------------------------+
        |                                                       |
        v                                                       |
  [strategy vN] --play 3+ games--> [history/*.json] --score--> [best-3 avg]
                                                                |
                                  avg > previous best? ---------+
                                  |                   no -> analyze failures,
                                  | yes                      write vN+1, loop
                                  v
                          commit + push to GitHub
                          (strategy + full history + scoreboard)
                          loop until TARGET reached
```

## 1. Metric, baseline, target

- **Score of a game** = simulated wins (0..82) in Classic mode.
- **METRIC** = best average over 3 CONSECUTIVE games played with the same strategy
  version. Consecutive means game order within `history/` (no cherry-picking).
- **BASELINE** (2026-06-05, strategy v1): games 3-5 scored 78, 66, 68
  -> best-3-consecutive average = **70.67**.
- **MILESTONE** = first single 82-0 game (OVR >= ~109.4). Expected to arrive long
  before the target; record and commit immediately when it happens.
- **TARGET (stop condition)** = a 3-consecutive-game average of **82.0**, i.e. three
  perfect 82-0 seasons in a row. This is the formal end of the program.

Improvement rule: a strategy version vN+1 REPLACES vN only when its best-3-consecutive
average strictly exceeds the previous best. Every improvement is committed and pushed.
Worse runs are NEVER deleted -- they stay in `history/` as negative results.

## 2. Why the metric can climb (and where it caps)

The sim is fully cracked (docs/sim-engine.md, verified to the decimal on 5 games):

```
OVR  = 100*( sumPPG/133.4*0.46 + sumRPG/39.7*0.25 + sumAPG/29.3*0.18
             + adjSPG/6.1*0.07 + adjBPG/3.2*0.04 )
wins = round( 82 * min(OVR/110, 1)^1.15 )
```

Picks are deterministic given a roll; the only randomness is the slot machine
(uniform over 180 (team, decade) cells, plus one team-skip and one decade-skip per
game). So strategy improvements raise the EXPECTATION of wins; the 3-game-average
metric then climbs as both the policy improves and luck cooperates. Known levers,
in descending order of remaining headroom:

1. Skip policy (when to burn team/decade skips; EV thresholds; jackpot hunting).
2. Position placement (which slot to give a multi-position player so future
   C-only/PG-only jackpots are not blocked).
3. Pick scoring refinements (null spg/bpg synergy: adjSPG = avg(non-null)*5, so the
   marginal value of a pick depends on current roster's steal/block average).
4. Volume (target score is luck-gated; more games per iteration tightens the
   estimate of a strategy's true mean -- do not promote on a lucky 3-run).

## 3. Repo layout for the program

```
program.md            this file (process spec; updated as the process evolves)
FOLLOW-ALONG.md       public explainer + live scoreboard (the link to share);
                      scoreboard section is auto-generated, do not edit by hand
history/              one JSON per game, append-only, never pruned
  game-001.json ...   schema below; numbering is global and monotonic
  README.md           schema documentation
src/
  oracle.py           per-cell pick ranking + era/team sweeps (exists)
  scoreboard.py       reads history/, prints per-game table, best-3 avg, verdict
  strategy.py         versioned policy: pick scoring, skip EV rules, placement  [iteration 0]
  play.py             cc-playwright harness: plays one full game end-to-end,
                      writes history/game-NNN.json                              [iteration 0]
docs/
  sim-engine.md       reverse-engineered engine (win curve, slot mechanics)
  game-log.md         human-readable narrative log (manual era)
  recon-notes.md      site recon + strategy notes
data/
  players_flat.json   full player pool (10,932 rows)
```

## 4. Game record schema (history/game-NNN.json)

```json
{
  "game": 3,
  "played_at": "2026-06-05T13:55 -0400 (approx)",
  "mode": "classic",
  "strategy_version": "v1-weighted-ev-skips",
  "rounds": [
    {
      "round": 1,
      "rolls": [
        {"team": "SAS", "era": "2010s", "skip_after": "era"},
        {"team": "SAS", "era": "1960s", "skip_after": null}
      ],
      "pick": "Jerry Lucas",
      "position": "PF",
      "stats": {"ppg": 19.7, "rpg": 19.1, "apg": 3.0, "spg": null, "bpg": null},
      "ovr_pts": 20.71,
      "rationale": "best open-slot fit; era-skip EV 18.95 > Rudy Gay 14.44"
    }
  ],
  "totals": {"ppg": 132.7, "rpg": 50.2, "apg": 23.8, "spg": 6.5, "bpg": 2.9},
  "result": {"wins": 78, "losses": 4, "ovr": 105.9, "grade": "A+", "label": "HISTORIC"}
}
```

Required: every roll seen (including skipped ones), every skip decision, the pick
with stats and weighted pts, and the end-screen result. `rationale` is free text --
it is the data the analyze step mines for policy mistakes.

## 5. The loop (one iteration)

1. **PLAY**: run the current strategy for at least 3 games (more when variance is
   high; 5+ once averages pass ~75). Manual play guided by src/oracle.py is allowed
   until src/play.py lands, but every game MUST produce a history JSON.
2. **SCORE**: `python src/scoreboard.py` -> per-game table + best-3-consecutive
   average per strategy version + ALL-TIME BEST. Then
   `python src/scoreboard.py --update-page` to regenerate the public scoreboard
   in FOLLOW-ALONG.md (phone-friendly; MUST be part of every history/improve
   commit so the public page never lags the data).
3. **COMPARE**:
   - New best-3 avg > previous best -> **PROMOTE**: update the scoreboard section
     below, commit `strategy + history/ + program.md` with message
     `improve: vN best-3 avg X.XX -> vN+1 Y.YY (games A-B)`, and push.
   - No improvement -> do NOT commit a promotion. History still gets committed
     periodically (append-only data is valuable) with message
     `history: games A-B under vN (no improvement, best-3 X.XX)`.
4. **ANALYZE**: read the worst rounds across the iteration's games. Categorize every
   lost point against the levers in section 2 (bad skip EV call? position block?
   scoring error? pure slot luck?). Pure-luck losses get no policy response.
5. **IMPROVE**: write the next strategy version (bump version string, document the
   delta in the scoreboard table), then loop.
6. **STOP** when a game hits 82-0 (record MILESTONE) and formally when best-3 avg
   = 82.0 (TARGET).

Rules:
- Never compare averages across different metrics or game counts; the unit is
  always 3 consecutive games.
- Never tune the strategy mid-iteration; version changes happen only at step 5.
- Negative results are first-class: a rejected vN+1 stays in git history with its
  games, so failed ideas are not retried blindly.

## 6. Scoreboard (update on every promotion)

| Version | Description | Games | Best-3 avg | Promoted |
|---------|-------------|-------|------------|----------|
| v0-raw-sum | pick max raw PTS+REB+AST+STL+BLK; ad-hoc skips | 1-2 | n/a (2 games) | -- |
| v1-weighted-ev-skips | pick max weighted OVRpts; EV-computed skips; manual placement heuristics | 3-5 | **70.67** (78, 66, 68) | baseline |
| v1-scripted | same policy automated (src/play.py); flat +3.0 skip threshold | 6-10 | 68.33 (75, 63, 67) | no |
| v2-declining-skips | offline-tuned: skip thresholds decline by round (2, 1.5, 1, 0.5, 0 -- a held skip expires worthless), SG-SF-PG-PF-C placement | 11-20 | **74.67** (74, 77, 73) | 2026-06-05 |
| v3-steady-valuation | v2 + steady-state spg/bpg pricing (relative to the 5/k roster average; fixes early-round x5 marginal inflation and null undervaluation) | 21-30 | **76.33** (76, 71, 82) | 2026-06-05 |

ALL-TIME BEST: **76.33** (v3-steady-valuation, games 27-29)
MILESTONE (first 82-0): **GAME 29** -- 2026-06-05, v3, OVR 120.1 (S PERFECT).
Roster: Russell Westbrook PG (WAS/2020s), Allen Iverson SG (PHI/2000s),
Charles Barkley SF (PHI/1990s), Karl Malone PF (UTA/1990s),
Wilt Chamberlain C (GSW/1960s).
TARGET (3-game avg 82.0): not reached

## 7. Provable ceiling (src/optimal.py)

Branch-and-bound over all position-legal rosters under the exact engine:
optimum = Oscar (PG, SAC/60s), MJ (SG, CHI/80s), Baylor (SF, LAL/60s),
Pettit (PF, ATL/60s), Wilt (C, GSW/60s) -> OVR 139.4 (needs 109.5; headroom
29.9). The null-spg/bpg extrapolation is the kicker: MJ is the only pick with
defensive stats, so they count 5x. Converged at top-40 and top-80 candidates
per slot.

## 8. Iteration 0 backlog (next actions)

1. `src/strategy.py`: codify v1 as executable policy (weighted pick scoring with
   roster-aware adjSPG/adjBPG marginals, skip-EV computation vs full re-roll
   distribution, placement rules that protect C then PG).
2. `src/play.py`: automate one full game via cc-playwright connection `beat820`
   (spin -> parse roll -> oracle pick -> place -> end-screen parse -> JSON).
3. `src/scoreboard.py`: done (reads history/, computes best-3 averages).
4. Then run iteration 1: 5 games under scripted v1 to get a clean automated
   baseline before changing policy (manual-play noise removed).

## 8. GitHub conventions

- Remote: https://github.com/thefrederiksen/beat-82-0 (branch main).
- Commit types: `improve:` (promotion), `history:` (games without promotion),
  `program:` (process/spec changes), `tooling:` (harness/scripts).
- Third-party site assets (downloaded JS chunks, raw HTML mirrors) stay LOCAL
  (gitignored) -- analysis and cleaned-up excerpts live in docs/sim-engine.md.
- ASCII only in all files.
