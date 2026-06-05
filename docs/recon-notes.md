# Recon notes

## 2026-06-05 -- initial recon

### Site fingerprint

- `https://www.82-0.com/` -- Next.js (App Router, Turbopack build), `meta generator: v0.app`,
  deployed on Vercel (`?dpl=dpl_8xuUKZQRNiSeWBYzxGcE7Jp4snnX` deployment id on assets).
- Returns **403 Forbidden** to default curl / WebFetch user agents. A browser UA
  (`Mozilla/5.0 ...`) gets through fine.
- Analytics: PostHog (`app.posthog.com`) + Google Analytics (G-DHMPGYKYK0).
- Social: bluesky `82-0.bsky.social`, an X account linked in the footer.

### Pages

- `/` -- the game. Shell renders "Loading player data..." then hydrates.
- `/how-to-play` -- full rules (mirrored into README).

### Static chunk analysis

Downloaded all 12 script chunks referenced by the homepage. Findings:

- No bundled player JSON/CSV. No `/api/...` routes other than PostHog's own.
- No supabase/firebase client config in the static chunks.
- Conclusion: the player pool arrives via a runtime request after hydration --
  either a Next.js server action (POST to the page route with `next-action`
  header) or a dynamically imported chunk not referenced in the initial HTML.

### Next step: network capture

Use cc-playwright (separate connection, NOT the user's live browser) to:

1. Open `https://www.82-0.com/`, record all network requests after load.
2. Identify the request that returns the player pool; save raw response to `data/`.
3. Play one full game while recording -- capture the request/response shape of
   the slot machine roll and the final simulation call (if server-side) or
   confirm the sim is purely client-side.
4. Pull the lazily-loaded chunks observed at runtime and diff against the static
   list -- the sim engine constants (win curve, era adjustments) live somewhere.

### Open questions

- Is the slot machine roll seeded server-side (anti-cheat) or client random?
- Is the daily puzzle shared across players (wordle-style) or fully random per run?
- The rules mention 7 decades but only 5 roster spots -- presumably the slot
  machine draws 5 distinct decades out of the 7 per game. Verify in play.

## 2026-06-05 -- session 2: live exploration, data capture, 5 games, engine cracked

Everything below is from a live cc-playwright session (connection `beat820`) plus full
JS-bundle reverse engineering (see docs/sim-engine.md for code-level detail) and five
complete Classic games (see docs/game-log.md). Screenshots in docs/screenshots/.

### Player data: captured

- The "Loading player data..." fetch goes to Firebase Storage:
  `https://firebasestorage.googleapis.com/v0/b/project-4599904239656435772.firebasestorage.app/o/players_flat.json?alt=media`
  Saved raw to `data/players_flat.json` (3.2 MB, 10,932 rows). Fields: team, player,
  pos, ppg, rpg, apg, spg, bpg, positions[], id, baseSlug, era.
- 8 eras in data (1950s-2020s) but the game only rolls 1960s-2020s (1950s rows are
  dead weight). 30 modern franchise codes; historical teams are folded into modern
  ones (Cincinnati Royals under SAC, Seattle under OKC, New Orleans Jazz under UTA...).
- spg/bpg are null for pre-tracking eras (1,065 rows) -- they display as 0.0 in the
  UI but are handled specially by the sim (see below).
- The URL is public: a plain `Invoke-WebRequest` downloads it (no auth, no browser UA
  needed -- only 82-0.com itself UA-blocks).
- Client caches it in localStorage (`nba_players_local_cache`, v2, 7-day TTL).

### Answers to the open questions

1. **Server-seeded rolls?** NO. All randomness is unseeded client-side `Math.random()`
   in the slot-machine component. No anti-cheat. The roll is a uniform draw over all
   (team, decade) cells that contain at least one player (not team-then-decade).
2. **Daily shared puzzle?** NO. Nothing daily, no shared seed, every spin is
   independent per client. Firestore is only used to SAVE results (finalScore = OVR)
   and serve share links.
3. **7 decades vs 5 slots?** There is NO distinct-decade constraint. Decades AND teams
   can repeat across the 5 rounds (observed: PHX/1960s twice in one game, 2000s three
   times in another; HOU twice). The how-to-play "select exactly one player from each
   of the following decades" wording is simply wrong/aspirational. The 5 rounds map to
   the 5 court positions (PG/SG/SF/PF/C); you place each pick on any open slot the
   player is eligible for (positions[] in the data).
4. **Sim location:** 100% client-side (chunk 35a16371ef5755e2.js, module 89050). The
   82-game "simulation" is one closed-form formula, no game-by-game sim at all.

### How the sim actually behaves (verified against all 5 games to the decimal)

```
OVR  = 100 * ( sumPPG/133.4*0.46 + sumRPG/39.7*0.25 + sumAPG/29.3*0.18
               + adjSPG/6.1*0.07 + adjBPG/3.2*0.04 )
wins = round( 82 * min(OVR/110, 1)^1.15 )      // 82-0 needs OVR >= ~109.4
```

- Raw season stats, summed over the 5 picks. NO era discount on PPG/RPG/APG in
  Classic, despite what the how-to-play page claims ("era-adjusted benchmarks" applies
  only to HoopIQ player ratings and to the spg/bpg extrapolation).
- "A deficiency in even one category can sink a perfect season" is also overstated:
  category ratios are linear with NO caps and NO penalty floor -- excess rebounds
  fully compensate missing steals. The only non-linearity is the gentle ^1.15 at the
  end. Balance does not matter; weighted totals do.
- adjSPG/adjBPG: players with null spg/bpg are excluded and the remaining sum is
  scaled by 5/k. So a 1960s pick with nulls inherits the roster average rather than
  contributing 0 -- old-era picks are NOT penalized on defense stats (and a sub-average
  steals guy actively hurts more than a null).
- Per-unit OVR value: 1 PPG = 0.345 pts, 1 RPG = 0.630, 1 APG = 0.614, 1 SPG = 1.148,
  1 BPG = 1.250. Rebounds are worth ~1.8x points per unit; raw-sum picking (what the
  UI's default PPG sort nudges you toward) is significantly suboptimal.
- Grades by wins: 80+=S PERFECT, 72+=A+ HISTORIC, 62+=A DYNASTY, 57+=B, 50+=C, 40+=D.

### Skips (verified in play)

- One TEAM skip and one DECADE skip per game (not per round; both usable in the same
  round). Team skip locks the rolled decade and re-rolls the team (excluding the
  current one); decade skip locks the team and re-rolls the decade. Exclusion lasts
  only that respin. Skips are disabled in hard mode.

### What drives wins

Five-game ladder (docs/game-log.md): 64-18 (raw-sum picks) -> 59-23 -> 78-4 -> 66-16
-> 68-14 (weighted picks + EV-computed skips). Pts: 88.2, 82.5, 105.9, 91.5, 93.9.

- You need to average ~21.9 weighted OVR points per pick for 82-0. The distribution
  of "best available weighted pick" per (team, decade) cell averages ~17-18, so an
  average game tops out around 90 OVR / high-60s wins. 82-0 requires hitting 3+ of
  the ~25 cells whose best pick is 23+ (Wilt GSW-60s 32.0, PHI-60s Wilt 28.8, Kareem
  MIL-70s 28.5, LAL-70s Kareem ~26, Giannis MIL-20s 23.5, Jokic DEN-20s ~25, D-Rob
  SAS-90s 23.5, Moses HOU-80s 23.1, MJ CHI-80s 23.5...), which is luck-gated by the
  slot machine even with perfect play.
- Positional blocking is the biggest avoidable leak: the monster cells are mostly
  C-only players. Filling C early (or wasting C/PF slots on mediocre bigs) repeatedly
  cost 4-8 OVRpts in games 1-3 (blocked Daugherty/Kemp/Ewing, Wilt, Embiid, Cousins,
  Oscar at PG, Dominique at SF).

## Strategy: how to get to 82-0

Target: 5 picks totaling OVR >= 109.4, i.e. avg 21.9 weighted pts per pick.

1. **Rank every pick by weighted OVR points, never raw sum or PPG.**
   pts = 0.345*PPG + 0.630*RPG + 0.614*APG + 1.148*SPG + 1.250*BPG.
   src/oracle.py does this for any (team, era) cell, plus --eras/--teams sweeps for
   skip decisions.
2. **Compute skip EV every round** (oracle does it in seconds): compare the current
   cell's best ELIGIBLE pick against the mean of best-eligible picks across the
   re-roll distribution (era skip: same team x 6 other decades; team skip: same
   decade x other teams). Burn a skip whenever the gap is >= ~3 pts; never let a
   skip expire on a below-average roll (game 5 wasted one on a neutral spot).
3. **Protect the C slot.** The 23+ jackpot picks are overwhelmingly C-only (Wilt,
   Kareem, Russell, Moses, Robinson, Jokic, Shaq, Wemby). Place flexible bigs at PF,
   flexible wings at SG/SF, and keep C open as long as possible. Similarly prefer
   keeping PG open over SG/SF (Oscar/Magic/CP3-class are PG-only).
4. **Exploit the no-era-adjustment bug**: 1960s/70s volume stats count at face value,
   AND null spg/bpg defers to the roster average (5/k scaling). A 1960s Wilt season
   (39.6/24.3/3.1, nulls) is worth ~32 pts -- the single best pick in the game --
   with zero defensive-stat downside. Prioritize old-era big men.
5. **Pair the nulls with steal/block monsters.** Since adjSPG = avg(non-null)*5,
   two picks like Hakeem (2.0 stl / 3.1 blk) + Wilt(null) beat five mediocre 1.0/0.5
   defenders. Avoid LOW non-null spg/bpg players (a 0.1-bpg guard drags the
   extrapolated average down; a null would not).
6. **Use both skips to hunt jackpot cells, not to dodge mediocrity.** Exactly 17 of
   the 180 rollable (team, decade) cells have a best pick >= 23 weighted pts (29
   cells >= 21.9); 11 of those 17 are C-only players. Each skip is a second lottery
   ticket; spend them chasing 24+ picks rather than upgrading 15->18.
7. **Expected outcome with perfect play:** the per-roll chance of a 23+ cell is
   ~9.4% (17/180), roughly doubled by skips; stacking 3 such hits plus two 20s in
   one game is a low-single-digit-percent event. Best observed so far: 105.9 (78-4).
   Without slot luck the deterministic ceiling of an average roll sequence is ~95-100.

Theoretical max roster (slot machine willing): Wilt GSW-60s at C (31.96) + Oscar
SAC-60s at PG (22.18) + Pettit ATL-60s at PF (22.04) + Baylor LAL-60s at SF (20.99)
+ West LAL-70s at SG (20.90) = 118.1 OVR -> capped, 82-0. Only 10 of 17 jackpot
cells can coexist positionally, but 109.4 needs just ~3 of them; 82-0 is absolutely
reachable -- it is a slot-luck grind, not a skill ceiling.
