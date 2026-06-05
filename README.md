# beat-82-0

Tooling and research to win at [82-0.com](https://www.82-0.com/) -- the NBA all-time
roster game where you try to build a team that goes a perfect 82-0.

## The game

Each round, a slot machine assigns you a **team + decade** combination. You pick the
best available player from that team in that era. Five rounds, five roster spots.
When the roster is full, a simulation engine runs your aggregate stats through an
82-game schedule. The goal is a perfect 82-0 season.

### Rules (from the official How to Play)

1. **Decades Rule** -- era diversity is enforced across the draft pool:
   1960s, 1970s, 1980s, 1990s, 2000s, 2010s, 2020s (no 1950s).
2. **Statistical aggregation** -- the engine uses each player's peak performance
   within their decade, across five metrics: **PTS, REB, AST, STL, BLK**.
   Team Strength Rating = cumulative total across all roster spots.
3. **Non-linear win curve** -- each additional win gets harder. Reaching 82-0
   requires maximizing ALL five categories simultaneously; a deficiency in even
   one category can sink a perfect season.
4. **Era adjustment** -- 30 PPG in the 1960s is not 30 PPG in the 2020s. The engine
   uses era-adjusted benchmarks.
5. **Skips** -- one team skip and one decade skip per game. Save them for weak
   team/era combinations.
6. **Game modes** -- Classic (stats visible) and HoopIQ (stats hidden, memory only).

## Strategy to win

The game is fully client-side (Next.js, generated with v0.app, hosted on Vercel).
That means the player database and the simulation engine both run in the browser
and can be reverse-engineered.

### Plan

| Phase | Goal | Status |
|-------|------|--------|
| 1. Capture the player data | Intercept the runtime data load ("Loading player data...") via browser network capture; dump the full player pool to `data/` | TODO |
| 2. Reverse the sim engine | Find the win-projection curve and era-adjustment factors in the JS bundle; reimplement in `src/` | TODO |
| 3. Build the pick oracle | Given any (team, decade) slot, return the best pick -- precomputed lookup table for every combination | TODO |
| 4. Skip advisor | Quantify when burning the team skip / decade skip beats taking the best available pick | TODO |
| 5. HoopIQ cheat sheet | Human-memorizable best-pick tables for the stats-hidden mode | TODO |

### Recon so far (2026-06-05)

- Static JS chunks contain no player data and no API routes -- data arrives via a
  runtime fetch (likely a Next.js server action or lazy chunk). Needs network
  capture from a live session.
- Analytics: PostHog + GA. No auth wall on the game itself.
- Site returns 403 to non-browser user agents; a normal browser UA works.

## Repo layout

```
data/   captured player pool, era benchmarks, simulation constants
docs/   research notes, reverse-engineering writeups
src/    sim engine reimplementation + pick oracle
```

## Disclaimer

Independent fan project for a free browser game. Not affiliated with 82-0.com
or the NBA.
