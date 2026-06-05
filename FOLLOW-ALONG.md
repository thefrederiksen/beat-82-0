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

**Best 3-game average: 70.67 wins** (games 3-5: 78, 66, 68)

`[#################...]` **70.67 / 82**

**Best single game: 78-4** (game 3, rated "HISTORIC")

**First 82-0:** not yet... the chase is on

*5 games played -- latest: game 5, 68-14 (2026-06-05)*

### Recent games

| # | Result | Rating | Grade |
|--:|:------:|------:|:-----:|
| 5 | 68-14 | 93.9 | A |
| 4 | 66-16 | 91.5 | A |
| 3 | 78-4 | 105.9 | A+ |
| 2 | 59-23 | 82.5 | B |
| 1 | 64-18 | 88.2 | A |

### Strategy versions

| Strategy | Games | Best 3-game avg |
|:---------|:-----:|----------------:|
| `v0-raw-sum` | 1 | (need 3 games) |
| `v1-weighted-ev-skips` | 2-5 | **70.67** |
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
3. **Curious how deep it goes?**
   - [program.md](program.md) -- the improvement loop the AI follows
     (play, score, analyze, improve, repeat).
   - [docs/sim-engine.md](docs/sim-engine.md) -- the reverse-engineered game math.
   - [history/](history/) -- every game ever played, every roll, every decision,
     including the bad ones. Nothing gets deleted.

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
