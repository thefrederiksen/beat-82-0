# Can an AI go 82-0?

**An AI is trying to build the perfect NBA team and win every single game of an
82-game season. This page is the live scoreboard.**

---

## The game

[82-0.com](https://www.82-0.com/) is a free browser game. A slot machine hands you
a random NBA team and a random decade -- like "Spurs, 2000s" or "Lakers, 1970s".
You pick one player from that team and era. Do that 5 times to fill a starting
lineup (PG, SG, SF, PF, C). The game then simulates a whole 82-game NBA season
with your five players and tells you your record.

A perfect season -- **82 wins, 0 losses** -- is the whole point of the game, and
it is extremely hard. Most decent teams land around 55-65 wins.

## The twist

Instead of guessing, the AI (Claude) did what a scout with unlimited time would do:

1. **Read the game's own code** and found the exact math it uses to turn five
   players into a season record. No guessing -- the formula is known, to the decimal.
2. **Downloaded the full player database** -- 10,932 player-seasons.
3. Built a **pick oracle**: for any team+decade the slot machine rolls, it instantly
   knows the best possible pick -- and it is often NOT the famous name. Rebounds,
   steals and blocks are secretly worth way more per unit than points in this game.

The one thing the AI cannot control: **the slot machine**. The rolls are pure luck.
Perfect play makes every roll count, but a perfect season still needs lucky rolls --
like pulling Wilt Chamberlain's 1960s seasons, the single best card in the game.
That tension (perfect strategy vs. random rolls) is what makes this fun to watch.

## The mission

- **Score per game** = season wins (out of 82).
- **Official metric** = the average of 3 games in a row. No cherry-picking.
- **Starting baseline: 70.67** (the first serious session scored 78, 66, 68).
- Every time a new strategy beats the old best average, it gets promoted and
  this page updates.
- **Milestone**: the first single 82-0 game.
- **Final target**: a 3-game average of 82 -- three perfect seasons in a row.

---

<!-- SCOREBOARD:START -->
## Live scoreboard

**Best 3-game average: 77.00 wins** (games 61-63: 81, 72, 78)

`[###################.]` **77.00 / 82**

**Best single game: 82-0** (game 29, rated "PERFECT")

**First 82-0:** GAME 29 -- DONE!

*126 games played -- latest: game 126, 67-15 (2026-06-05)*

### Recent games

| # | Result | Rating | Grade |
|--:|:------:|------:|:-----:|
| 126 | 67-15 | 92.8 | A |
| 125 | 78-4 | 105.9 | A+ |
| 124 | 71-11 | 97.0 | A |
| 123 | 68-14 | 93.5 | A |
| 122 | 74-8 | 100.3 | A+ |
| 121 | 80-2 | 108.1 | S |
| 120 | 76-6 | 102.8 | A+ |
| 119 | 62-20 | 86.5 | A |
| 118 | 69-13 | 94.4 | A |
| 117 | 76-6 | 103.5 | A+ |
| 116 | 59-23 | 82.7 | B |
| 115 | 77-5 | 104.2 | A+ |
| 114 | 68-14 | 93.6 | A |
| 113 | 71-11 | 97.4 | A |
| 112 | 66-16 | 91.4 | A |

*Showing the last 15 of 126 games -- full records in [history/](history/).*

### Strategy versions

| Strategy | Games | Best 3-game avg |
|:---------|:-----:|----------------:|
| `v0-raw-sum` | 1 | (need 3 games) |
| `v1-weighted-ev-skips` | 2-5 | **70.67** |
| `v1-scripted` | 6-10 | **68.33** |
| `v2-declining-skips` | 11-20 | **74.67** |
| `v3-steady-valuation` | 21-126 | **77.00** |
<!-- SCOREBOARD:END -->

---

## How to follow along

1. **Bookmark this page.** The scoreboard above updates automatically with every
   batch of games.
2. **Watch the commit feed**:
   [github.com/thefrederiksen/beat-82-0/commits/main](https://github.com/thefrederiksen/beat-82-0/commits/main).
   The commit messages tell the story:
   - `improve:` -- the AI found a better strategy. These are the wins.
   - `history:` -- more games played, no record broken yet.
   - `program:` / `tooling:` -- upgrades to the machinery.
3. **Want to try the strategy yourself?** The one-page human version:
   [docs/cheat-sheet.md](docs/cheat-sheet.md) -- the value formula, when to burn
   your skips, which positions to keep open, and the jackpot table to memorize.
4. **Curious how deep it goes?**
   - [program.md](program.md) -- the improvement loop the AI follows
     (play, score, analyze, improve, repeat).
   - [docs/sim-engine.md](docs/sim-engine.md) -- the reverse-engineered game math.
   - [history/](history/) -- every game ever played, every roll, every decision,
     including the bad ones. Nothing gets deleted.

## The dream team (computed from the game's own code)

Since the AI has the game's exact scoring code, it can compute the best roster
the game allows -- IF the slot machine handed over every needed combo:

| Slot | Player | From |
|:----:|:-------|:-----|
| PG | Oscar Robertson | Royals, 1960s |
| SG | Michael Jordan | Bulls, 1980s |
| SF | Elgin Baylor | Lakers, 1960s |
| PF | Bob Pettit | Hawks, 1960s |
| C | Wilt Chamberlain | Warriors, 1960s |

That lineup rates **139.4** -- the perfect season needs just 109.5, so there is
plenty of headroom. The fun part: steals were not recorded in the 1960s, and the
game fills the gap by scaling up whoever HAS data -- so prime Jordan's steals
get counted five times over. Four legends with no defensive stats plus peak MJ
is, according to the game's own math, the strongest team ever assembled.

(`src/optimal.py` proves this by exhaustive search over every legal roster.)

## Fair questions

**Is this cheating?** It is a free single-player browser game with no opponents and
no stakes -- this project never logs in, never touches a leaderboard, and never
modifies the game. It just plays very, very well. Think of it as a speedrun.

**Why can't it just win immediately?** Because the slot machine is random. The AI
plays each roll perfectly, but a perfect season needs roughly three jackpot rolls
out of five. Only 17 of the 180 possible team+decade combos hold a jackpot-level
player. That is why this is a chase, not a calculation.

**What does the AI actually do each round?** Scores every available player with the
game's own formula, checks whether re-rolling (you get one team re-roll and one
decade re-roll per game) has better expected value than the current best pick, and
places players so the rare superstars are never blocked from their position later.

---

*Independent fan project. Not affiliated with 82-0.com or the NBA.
Everything here is reproducible from this repository.*
