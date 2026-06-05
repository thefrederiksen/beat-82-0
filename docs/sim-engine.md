# 82-0 Simulation Engine - Reverse Engineering Notes

Source: client-side JS chunks of https://www.82-0.com/ (Next.js / Turbopack on Vercel),
deployment dpl_8xuUKZQRNiSeWBYzxGcE7Jp4snnX. Chunks saved to data/chunks/.

ALL game logic runs CLIENT-SIDE in the browser. There is no server-side simulation and
no web worker. Firebase is used only for auth, saving game results, and serving the
player dataset (players_flat.json). The win/rating math is plain JS executed on the page.

## Which chunk holds what

- data/chunks/35a16371ef5755e2.js
  - Module 89050: THE SIM ENGINE. calculatePlayerRating, calculateTeamResult,
    calculateTeamRating, projectedWins, adjustSpgBpg, grade tables. All constants here.
  - Module 23902/17428: player-data hydration (fetch players_flat.json, group by
    team+decade), team color helpers, DECADES/POSITIONS constants.
- data/chunks/750964a313d9668a.js
  - Module 31713: the slot-machine UI component (team/decade reels, SPIN button).
  - Component `ch`: the top-level game state machine (rounds, roster, skip handlers,
    end screen). Calls calculateTeamResult for the result.
- data/chunks/e21ae550434c1d50.js
  - Firestore helpers: saveGameResult, generateGameId (random Firestore doc id),
    getSharedGame, user profile. No seeding logic.
- data/chunks/f19da3c94c53dd41.js: Firebase Auth (not re-downloaded).

## Player dataset

Fetched from Firebase Storage:
  https://firebasestorage.googleapis.com/v0/b/project-4599904239656435772.firebasestorage.app/o/players_flat.json?alt=media
Cached in localStorage under key "nba_players_local_cache" (version "v2", 7-day TTL
= 6048e5 ms). Players are grouped by team abbreviation then by decade
("1960s".."2020s"). Rows with NaN in any of ppg/rpg/apg/spg/bpg for that decade slot
are filtered out during hydration.

## The five stat weights and league benchmarks (module 89050)

Top-level constants (these drive Classic mode):

```js
// stat weights (sum = 1.00)
const a = 0.46; // ppg weight
const r = 0.25; // rpg weight
const n = 0.18; // apg weight
const i = 0.07; // spg weight
const l = 0.04; // bpg weight

// team-aggregate benchmarks (sum of 5 starters' per-stat totals that = "100%")
const s = 133.4; // ppg team benchmark
const o =  39.7; // rpg team benchmark
const d =  29.3; // apg team benchmark
const p =   6.1; // spg team benchmark
const c =   3.2; // bpg team benchmark
```

There are TWO separate benchmark systems:

1. Team-level benchmarks (s,o,d,p,c above) used by Classic mode in calculateTeamResult.
2. Per-decade per-player benchmarks (object g below) used by HoopIQ player rating.

```js
// per-decade single-player "elite season" benchmarks (used by calculatePlayerRating)
const g = {
  "1960s": { ppg:30, rpg:18, apg:8,  spg:1.8, bpg:1.8 },
  "1970s": { ppg:28, rpg:13, apg:9,  spg:2,   bpg:2   },
  "1980s": { ppg:28, rpg:11, apg:11, spg:2.2, bpg:2   },
  "1990s": { ppg:27, rpg:11, apg:9,  spg:2,   bpg:2   },
  "2000s": { ppg:27, rpg:11, apg:9,  spg:2,   bpg:2   },
  "2010s": { ppg:28, rpg:11, apg:9,  spg:1.8, bpg:1.8 },
  "2020s": { ppg:28, rpg:11, apg:9,  spg:1.8, bpg:1.8 }
};

// positional stat profile (used only in HoopIQ rating to redistribute missing spg/bpg)
const u = {
  PG: { ppg:.40, rpg:.10, apg:.35, spg:.10, bpg:.05 },
  SG: { ppg:.45, rpg:.10, apg:.20, spg:.20, bpg:.05 },
  SF: { ppg:.45, rpg:.15, apg:.20, spg:.15, bpg:.05 },
  PF: { ppg:.40, rpg:.30, apg:.10, spg:.10, bpg:.10 },
  C:  { ppg:.40, rpg:.35, apg:.10, spg:.05, bpg:.10 }
};
```

## THE WIN CURVE

### Classic mode (the default; this is the one that matters for "beat 82-0")

`calculateTeamResult(players, false)` -> internal function (cleaned up):

```js
function classicResult(players) {
  if (players.length === 0)
    return { teamOvr:0, wins:0, losses:82, grade:"F", label:"TANKING", color:"#ef4444" };

  // era-adjusted steals/blocks (see adjustSpgBpg below)
  const { adjustedSpg, adjustedBpg } = adjustSpgBpg(players);

  // plain sums of the other three stats across the 5 picked players
  const sumPpg = players.reduce((x,p) => x + (p.ppg || 0), 0);
  const sumRpg = players.reduce((x,p) => x + (p.rpg || 0), 0);
  const sumApg = players.reduce((x,p) => x + (p.apg || 0), 0);

  // team OVR (0..~100+), rounded to 1 decimal
  const teamOvr = Math.round(
    100 * (
      (sumPpg / 133.4) * 0.46 +
      (sumRpg /  39.7) * 0.25 +
      (sumApg /  29.3) * 0.18 +
      (adjustedSpg / 6.1) * 0.07 +
      (adjustedBpg / 3.2) * 0.04
    ) * 10
  ) / 10;

  // NON-LINEAR WIN PROJECTION:
  const wins = Math.round(
    82 * Math.pow( Math.min(teamOvr / 110, 1), 1.15 )
  );

  const losses = 82 - wins;
  // grade from wins table h (see below)
  return { teamOvr, wins, losses, ... };
}
```

So the headline formula is:

```
ovr  = 100 * ( sumPPG/133.4*0.46 + sumRPG/39.7*0.25 + sumAPG/29.3*0.18
               + adjSPG/6.1*0.07 + adjBPG/3.2*0.04 )

wins = round( 82 * min(ovr/110, 1) ^ 1.15 )
```

There is no sigmoid / tanh / Math.exp. The "non-linear curve" is the power 1.15 on a
normalized (capped at 1.0) overall rating. The OVR is capped at 110 effective for the
win calc (ovr/110 clamped to 1.0), so an OVR of 110 or higher yields the full 82 wins.

`projectedWins(ovr)` is exported standalone with the identical formula:
```js
function projectedWins(ovr) { return Math.round(82 * Math.pow(Math.min(ovr/110, 1), 1.15)); }
```

### Era adjustment for steals/blocks (adjustSpgBpg) - module 89050

Old eras (1950s/1960s) have null spg/bpg in the dataset. Rather than treat them as 0,
Classic mode normalizes whatever non-null steal/block values exist up to a 5-player
scale:

```js
function adjustSpgBpg(players) {
  const spgs = players.filter(p => p.spg > 0).map(p => p.spg);
  const bpgs = players.filter(p => p.bpg > 0).map(p => p.bpg);
  const nS = spgs.length, nB = bpgs.length;
  return {
    // scale the sum of the present values up to "as if 5 players contributed"
    adjustedSpg: spgs.reduce((a,b)=>a+b, 0) * (nS > 0 ? 5/nS : 1),
    adjustedBpg: bpgs.reduce((a,b)=>a+b, 0) * (nB > 0 ? 5/nB : 1)
  };
}
```

Interpretation: if only k of the 5 starters have steal data, their steal sum is
multiplied by 5/k to extrapolate a full 5-man total before dividing by the 6.1
benchmark. Same for blocks with the 3.2 benchmark. This means picking players from
eras WITH steal/block data does not dilute the steal/block component; old-era picks
without spg/bpg simply do not contribute and the present ones are scaled up. The spg
and bpg terms together are only 0.07 + 0.04 = 0.11 of the OVR, so they are minor.

Note: there is NO per-decade multiplier applied to ppg/rpg/apg in Classic mode. The
per-decade benchmark table `g` is used only by HoopIQ rating, not by Classic. In
Classic mode a 1960s 30/18/8 line is summed at face value against the league team
benchmarks - i.e. old-era box-score inflation is NOT discounted in Classic. That is a
major exploitable property: high-volume old-era stat lines (e.g. Wilt) score very high.

### HoopIQ / "ball knowledge" mode rating (calculatePlayerRating, testMode=true)

`calculateTeamResult(players, true)`:

```js
function hoopIqResult(players) {
  if (players.length === 0) return { teamOvr:0, wins:0, losses:82, grade:"F", ... };
  const ratings = players.map(p => calculatePlayerRating(p, true)); // 0..100 each
  // geometric mean * 1.1, 1 decimal
  const teamOvr = Math.round(
    1.1 * Math.pow(ratings.reduce((a,b)=>a*b, 1), 1/ratings.length) * 10
  ) / 10;
  // different, steeper exponent (2.2) for HoopIQ
  const wins = Math.round(82 * Math.pow(Math.min(teamOvr/110, 1), 2.2));
  return { teamOvr, wins, losses: 82-wins, ... };
}
```

`calculatePlayerRating(player, ballKnowledge)` (module 89050):

```js
function calculatePlayerRating(p, bk=false) {
  const expo = bk ? 1.25 : 1;                 // boost exponent for above-benchmark stats
  const bench = g[p.decade || "2020s"] || g["2020s"];   // per-decade benchmark
  let n = 0;

  if (bk) {
    // start from positional weights; if spg/bpg are missing, redistribute their weight
    // onto ppg/rpg/apg (so a player is not penalized for missing steals/blocks)
    const w = { ...(u[p.positions?.[0] || p.pos || "SF"] || u.SF) };
    const missing = ["spg","bpg"].filter(k => p[k] == null || isNaN(p[k]));
    if (missing.length) {
      const present = ["ppg","rpg","apg","spg","bpg"].filter(k => !missing.includes(k))
                        .reduce((a,k)=>a + w[k], 0);
      const scale = present > 0 ? 1/present : 1;
      ["ppg","rpg","apg"].forEach(k => w[k] *= scale);
      missing.forEach(k => w[k] = 0);
    }
    ["ppg","rpg","apg","spg","bpg"].forEach(k => {
      const v = p[k];
      if (v != null && !isNaN(v)) {
        let ratio = v / bench[k];
        if (ratio > 1) ratio = Math.pow(ratio, expo); // reward exceeding the benchmark
        n += w[k] * ratio;
      }
    });
  } else {
    // non-HoopIQ single-player rating: simple sum of stat/benchmark ratios
    ["ppg","rpg","apg","spg","bpg"].forEach(k => {
      const v = p[k];
      if (v != null && !isNaN(v)) n += v / bench[k];
    });
  }

  let base = 60 + 40 * n;                      // map to ~60..100 band
  const posCount = p.positions?.length || 1;   // versatility bonus
  let star = 0;
  if (bk) {
    const name = p.player?.toLowerCase() || "";
    star = 2.5 * (STAR_SET.has(name) ? 1 : 0); // hand-picked "intangibles" bonus
  }
  // +bonus for multi-position eligibility (3 per extra pos in HoopIQ, else 2)
  return Math.min(100, Math.round((base + (posCount-1)*(bk?3:2) + star) * 10) / 10);
}
```

The HoopIQ "intangibles" STAR_SET (the `F` Set, players that get +2.5):
larry bird, tim duncan, kevin durant, magic johnson, shaquille o'neal,
hakeem olajuwon, bill russell, kobe bryant, oscar robertson, karl malone,
kevin garnett, isiah thomas, tony parker, manu ginobili, draymond green,
scottie pippen, dennis rodman, stephen curry, nikola jokic, dirk nowitzki.

## Grade / label tables

Wins -> grade table (`h`), used by both modes (find by wins >= minWins, first match):

```js
const winGrades = [
  { minWins:80, grade:"S",  label:"PERFECT",   color:"#a855f7" },
  { minWins:72, grade:"A+", label:"HISTORIC",  color:"#22c55e" },
  { minWins:62, grade:"A",  label:"DYNASTY",   color:"#22c55e" },
  { minWins:57, grade:"B",  label:"CONTENDER", color:"#3b82f6" },
  { minWins:50, grade:"C",  label:"PLAYOFF",   color:"#f59e0b" },
  { minWins:40, grade:"D",  label:"LOTTERY",   color:"#64748b" },
  { minWins:0,  grade:"F",  label:"TANKING",   color:"#ef4444" }
];
```

To get 82-0 (PERFECT) you need wins == 82, i.e. round(82 * min(ovr/110,1)^1.15) == 82.
Solving: min(ovr/110,1)^1.15 >= 81.5/82 -> ovr/110 >= (81.5/82)^(1/1.15) ~= 0.99468
-> ovr >= ~109.4. Because ovr is computed then the power applied, an OVR around 109.4+
already rounds to 82 wins (and the ovr/110 term is clamped to 1.0 at ovr>=110).

There is also a separate OVR-grade table `t` (S/A/B/C/D/F at min 97/91/85/78/70/0) and
`getGrade(ovr)`, but the end screen uses the WINS-based table above for the result.

## Slot machine mechanics (module 31713 + component `ch`)

ALL randomness is client-side, unseeded `Math.random()`. There is NO seed, no daily
shared seed, no server roll. Confirmed: no "daily", "dailySeed", "mulberry", "xmur",
"getDailySeed" anywhere in any chunk. `generateGameId()` (module e21ae) just returns a
random Firestore document id and is used to tag a saved result, not to seed rolls. The
only "seed" strings in the bundle are Next.js App Router internals (seedData / flight
router), unrelated to the game.

Rounds and roster (component `ch` in 750964...):
- 5 rounds, 5 positions ["PG","SG","SF","PF","C"]. After choosing a player you place
  them on any OPEN court slot that matches one of their eligible positions (observed
  in play; players list a positions[] array, e.g. Giannis PF/PG/SF/C).
  Round counter `P` (useState(1)) increments each pick; game ends ("complete" phase)
  when the roster object M has 5 keys.
- Per round flow: phase "spinning" -> SPIN -> slot machine pre-determines the final
  team+decade, animates the reels (50ms tick), then onSpinComplete sets selectedTeam
  and selectedDecade and moves to phase "selecting", where the player picks one actual
  player from that team+decade roster.

Drawing a team+decade (slot machine effect, module 31713):
```js
// e = teams, t = decades, m = excludedTeamId, h = excludedDecade
let availTeams   = (m !== null) ? e.filter(x => x.id !== m) : e;
let availDecades = (h !== null) ? t.filter(x => x !== h)    : t;

if (lockedTeam !== null && lockedDecade !== null) { team=lockedTeam; decade=lockedDecade; }
else if (lockedTeam !== null) {
  team = lockedTeam;
  const ok = availDecades.filter(d => getPlayersByTeamAndDecade(team.id, d).length > 0);
  decade = ok[Math.floor(Math.random() * ok.length)];        // random valid decade
}
else if (lockedDecade !== null) {
  decade = lockedDecade;
  const ok = availTeams.filter(tm => getPlayersByTeamAndDecade(tm.id, decade).length > 0);
  team = ok[Math.floor(Math.random() * ok.length)];          // random valid team
}
else {
  // build every (team, decade) pair that actually has players, pick uniformly at random
  const combos = [];
  for (const tm of availTeams) for (const d of availDecades)
    if (getPlayersByTeamAndDecade(tm.id, d).length > 0) combos.push({team:tm, decade:d});
  const pick = combos[Math.floor(Math.random() * combos.length)];
  team = pick.team; decade = pick.decade;
}
```

Key consequences:
- The draw is a uniform random pick over all team/decade COMBINATIONS that have at least
  one player (not a two-step team-then-decade draw). DECADES = the 7 strings
  1960s..2020s (the home-screen calls them "60's".."20's").
- Teams CAN repeat across the 5 rounds, and decades CAN repeat across the 5 rounds.
  There is no "5 distinct decades" rule and no cross-round exclusion. After each pick
  the handler resets excludedTeamId and excludedDecade to null:
  ```js
  // on player pick (handler in `ch`):
  const next = { ...roster, [position]: player };
  setRoster(next);
  if (Object.keys(next).length === 5) setPhase("complete");
  else { setRound(P+1); setSelectedTeam(null); setSelectedDecade(null);
         setExcludedTeamId(null); setExcludedDecade(null); setPhase("spinning"); }
  ```

Skip (re-roll) logic, gated by `!hardMode`, once per type per GAME (`A` =
{team:bool, decade:bool} tracks "skipsUsed"; note the pick handler resets excluded*/
locked* but NOT skipsUsed, so each skip type is usable only once across all 5 rounds --
confirmed by play: after using both skips in round 3 of game 1, both buttons stayed
disabled for rounds 4-5):
```js
// J(kind, currentTeamId, currentDecade)
function J(kind, teamId, decade) {
  if (skipsUsed[kind]) return;               // only one team-skip and one decade-skip per round
  setSkipsUsed({ ...skipsUsed, [kind]: true });
  if (kind === "team") {                     // "Skip Team": keep decade, re-roll team
    setLockedDecade(decade);                 // lock the decade you got
    setLockedTeam(null);
    setExcludedTeamId(teamId);               // and exclude the team you are skipping
    setExcludedDecade(null);
  } else {                                   // "Skip Decade": keep team, re-roll decade
    setLockedTeam(teamId);
    setLockedDecade(null);
    setExcludedTeamId(null);
    setExcludedDecade(decade);               // exclude the decade you are skipping
  }
  setPhase("spinning"); setIsSpinning(true); // respin (one axis locked, other re-rolled)
}
```
So a "team skip" locks your decade and re-spins only the team (excluding the one you
just had); a "decade skip" locks your team and re-spins only the decade. The reel shows
"RESPINNING TEAM..." / "RESPINNING DECADE..." accordingly. Skips are disabled in
hardMode. The exclusion only lasts for that single respin (it is cleared on the next
round's pick).

Hard mode: `hardMode` removes the ability to skip team or decade
(canSkipTeam = canSkipDecade = !hardMode).

Test mode ("Team Draft", admin only): lets you manually choose team+decade each round
instead of spinning, and forces player ratings visible. Uses the same calc.

## End screen / shared result

- The end screen calls `calculateTeamResult(rosterArray, ballKnowledgeMode)` and shows
  teamOvr (labeled "OVR ... pts"), wins, losses, grade, label, color.
- `finalScore` saved to Firestore == teamOvr (the OVR rating), along with mode and
  roster. A shareable JPEG of a canvas (#shareable-image-canvas) is generated for
  sharing, and a shareUrl is built from the saved game id (getSharedGame fetches it
  back for the /share view). None of this feeds back into the simulation.

## Summary of exploit-relevant facts (for "beat 82-0")

1. Win curve: wins = round(82 * min(OVR/110, 1)^1.15). Need OVR ~109.4+ for 82 wins.
2. OVR (Classic) = 100 * ( sumPPG/133.4*0.46 + sumRPG/39.7*0.25 + sumAPG/29.3*0.18
   + adjSPG/6.1*0.07 + adjBPG/3.2*0.04 ), summed over your 5 picked players' RAW
   season stats. PPG dominates (weight 0.46, benchmark 133.4 total).
3. NO per-decade discount on ppg/rpg/apg in Classic. Old-era inflated box scores
   (e.g. 1960s Wilt 50/25) count at face value -> very high OVR. Era adjustment only
   touches steals/blocks (scaled to a 5-man total), which are 11% of OVR combined.
4. Slot rolls are unseeded Math.random on the client; teams and decades can repeat;
   no daily seed. With skips enabled you get one team re-roll and one decade re-roll
   per round, so you can steer toward (team, decade) cells containing elite stat lines.
5. To maximize: chase 5 high-PPG (and high-RPG) seasons. Old-era high-volume scorers
   and modern 30+ PPG seasons both inflate OVR. Roughly, you need the 5 starters' total
   PPG/RPG/APG/SPG/BPG to push the weighted normalized sum to >= ~1.094.
