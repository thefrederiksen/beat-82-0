# 82-0.com game log

All games played in Classic mode (stats visible) via cc-playwright connection `beat820`.
SUM = PPG+RPG+APG+SPG+BPG as shown in the in-game player cards (raw, not era-adjusted).

## Game 1 -- 2026-06-05 ~13:15 local

| Round | Roll (team/decade) | Skips used | Pick | Pos | PPG | RPG | APG | SPG | BPG | SUM |
|-------|--------------------|------------|------|-----|-----|-----|-----|-----|-----|-----|
| 1 | SAS / 2000s | - | Tim Duncan | PF | 21.4 | 11.7 | 3.3 | 0.8 | 2.3 | 39.5 |
| 2 | MIN / 2020s | - | Karl-Anthony Towns | C | 23.0 | 9.2 | 4.0 | 0.8 | 0.9 | 37.9 |
| 3 | CLE / 1990s -> NYK / 1990s -> NYK / 2010s | TEAM skip (CLE->NYK, era kept), then ERA skip (1990s->2010s, team kept) | David Lee | SF | 20.2 | 11.7 | 3.6 | 1.0 | 0.5 | 37.0 |
| 4 | DEN / 2000s | - | Allen Iverson | PG | 25.6 | 3.0 | 7.1 | 1.9 | 0.1 | 37.7 |
| 5 | POR / 1970s | - (none left) | Geoff Petrie | SG | 21.8 | 2.8 | 4.6 | 1.1 | 0.2 | 30.5 |

**Team totals (shown on end screen):** 112.1 PPG / 38.5 RPG / 22.6 APG / 5.6 SPG / 4.0 BPG

**Result: 64-18 -- Grade A "DYNASTY" -- 88.2 pts**

Notes:
- Round 3 original roll CLE/1990s: best fit for an open slot was Mark Price (30.0) because the
  top sums (Daugherty 35.3, Kemp 33.0, Nance 31.1) are all C/PF and both big slots were already
  filled. Team skip re-rolled team only (kept 1990s) -> NYK/1990s, which was even worse for open
  slots (Sprewell 24.4; Ewing blocked). Era skip re-rolled era only (kept NYK) -> 2010s.
- Lesson: filling C and PF in rounds 1-2 blocked Daugherty/Kemp/Ewing later. Positional
  flexibility of remaining slots matters a lot.
- Decades seen across 5 rounds: 2000s, 2020s, 2010s (after skips), 2000s, 1970s -- decades CAN
  repeat across rounds (2000s twice), contradicting the how-to-play "one player from each decade"
  wording. Teams did not repeat (SAS, MIN, NYK, DEN, POR).
- End screen shows raw stat totals (112.1 = raw sum of player PPG). The 88.2 pts rating
  presumably includes era adjustment. [Confirmed later: 88.2 pts matches the reverse-engineered
  formula exactly with NO era adjustment -- see docs/sim-engine.md.]

## Game 2 -- 2026-06-05 ~13:40 local

Strategy change: from this game on, picks ranked by reverse-engineered OVR points
(PPG x0.345 + RPG x0.630 + APG x0.614 + SPG x1.148 + BPG x1.250), not raw sum.
(Formula was extracted from the JS bundle between games 1 and 2.)

| Round | Roll (team/decade) | Skips used | Pick | Pos | PPG | RPG | APG | SPG | BPG | OVRpts |
|-------|--------------------|------------|------|-----|-----|-----|-----|-----|-----|--------|
| 1 | MIL / 1960s -> PHX / 1960s | TEAM skip (MIL was worst 60s team, best pick 12.7 OVRpts) | Gail Goodrich | SG | 23.8 | 5.4 | 6.4 | null | null | 15.5 |
| 2 | SAC / 2020s | - (era-skip EV was neutral) | Domantas Sabonis | PF | 18.5 | 12.7 | 6.2 | 0.9 | 0.4 | 19.7 |
| 3 | PHX / 1960s -> PHX / 2010s | ERA skip (PHX/60s rolled AGAIN; best left was 14.9) | Amar'e Stoudemire | C | 23.1 | 8.9 | 1.0 | 0.6 | 1.0 | 16.1 |
| 4 | MIN / 2010s | - (none left) | Jimmy Butler | SF | 22.1 | 5.3 | 4.8 | 2.1 | 0.5 | 17.0 |
| 5 | MIA / 1980s | - (none left) | Kevin Edwards | PG | 13.8 | 3.3 | 4.4 | 1.8 | 0.3 | 12.0 |

**Team totals:** 101.3 PPG / 35.6 RPG / 22.8 APG / 5.4 SPG / 2.2 BPG

**Result: 59-23 -- Grade B "CONTENDER" -- 82.5 pts**

Notes:
- PHX/1960s rolled twice in one game (rounds 1 and 3) -- team/decade combos can repeat
  within a game. Picked players are removed from the pool on repeat rolls (Goodrich was
  gone the second time).
- Formula verification: 82.5 pts matches OVR formula exactly IF null spg/bpg players are
  excluded and the non-null sum is scaled by 5/k (k=4 here, Goodrich null):
  adjSPG = 5.4*5/4 = 6.75, adjBPG = 2.2*5/4 = 2.75 -> OVR 82.54 -> 82*(0.75)^1.15 = 58.9 -> 59 wins.
  Game 1 (all 5 players had spg/bpg data, k=5): OVR 88.21, wins 63.6 -> 64. Both match.
- KAT and Kevin Love were both blocked in round 4 (C and PF already filled) -- positional
  blocking cost ~4 OVRpts again.

## Game 3 -- 2026-06-05 ~13:55 local

Full weighted-OVR strategy with skip-EV calculations per round.

| Round | Roll (team/decade) | Skips used | Pick | Pos | PPG | RPG | APG | SPG | BPG | OVRpts |
|-------|--------------------|------------|------|-----|-----|-----|-----|-----|-----|--------|
| 1 | HOU / 1980s | - | Moses Malone | C | 28.2 | 14.7 | 1.8 | 1.0 | 1.6 | 23.1 |
| 2 | PHI / 2000s | - (era skip EV 19.1 < AI 19.4 once Wilt/Embiid blocked by C taken) | Allen Iverson | PG | 29.9 | 3.9 | 6.1 | 2.4 | 0.2 | 19.4 |
| 3 | SAC / 2010s -> SAC / 1960s | ERA skip (best open-slot fit was Rudy Gay 14.4) | Jerry Lucas | PF | 19.7 | 19.1 | 3.0 | null | null | 20.7 |
| 4 | CHI / 2010s -> HOU / 2010s | TEAM skip (best fit LaVine 14.4, EV 17.0) | James Harden | SG | 29.1 | 6.0 | 7.7 | 1.8 | 0.6 | 21.3 |
| 5 | DET / 2000s | - (none left) | Grant Hill | SF | 25.8 | 6.6 | 5.2 | 1.4 | 0.6 | 18.6 |

**Team totals:** 132.7 PPG / 50.2 RPG / 23.8 APG / 6.5 SPG / 2.9 BPG

**Result: 78-4 -- Grade A+ "HISTORIC" -- 105.9 pts**

Notes:
- Formula verified to the decimal a third time: k=4 (Lucas null spg/bpg), adjSPG=6.5*5/4=8.125,
  adjBPG=2.9*5/4=3.625 -> OVR=105.85 -> 82*(105.9/110)^1.15=78.49 -> 78 wins.
- Category ratios are NOT capped at 1.0 individually (RPG 50.2/39.7=1.26 counted fully);
  only the final OVR/110 is capped.
- HOU rolled twice (rounds 1 and 4 after team skip from CHI) -- another repeat.
- Oscar Robertson (29.7/8.7/10.5, ~25 OVRpts) was blocked in round 3 because AI held PG.
  In hindsight AI should have gone to SG in round 2, or been passed for Webber C/PF... no,
  Webber was 16.6 -- AI was still right, but PG-blocking cost the Oscar jackpot.
- 105.9 pts is 3.5 short of the ~109.4 needed for 82-0. The ceiling is visible.

## Game 4 -- 2026-06-05 ~14:10 local

| Round | Roll (team/decade) | Skips used | Pick | Pos | PPG | RPG | APG | SPG | BPG | OVRpts |
|-------|--------------------|------------|------|-----|-----|-----|-----|-----|-----|--------|
| 1 | OKC / 1970s | - | Spencer Haywood | PF | 24.9 | 12.1 | 2.3 | 0.8 | 1.5 | 20.5 |
| 2 | UTA / 1970s | - (held skips; Truck Robinson 21.0 blocked by PF) | Pete Maravich | SG | 25.7 | 4.4 | 5.8 | 1.4 | 0.3 | 17.2 |
| 3 | MIL / 2000s -> MIL / 2010s | ERA skip (best fit Payton 15.2; EV 19.2 with Kareem/Giannis live) | Giannis Antetokounmpo | SF | 18.8 | 8.3 | 4.1 | 1.2 | 1.3 | 17.3 |
| 4 | POR / 2000s -> NOP / 2000s | TEAM skip (best fit Rasheed 15.3, EV 18.2) | Chris Paul | PG | 19.4 | 4.8 | 9.9 | 2.4 | 0.1 | 18.6 |
| 5 | CHI / 2000s | - (none left) | Elton Brand | C | 20.1 | 10.1 | 2.5 | 0.9 | 1.6 | 17.8 |

**Team totals:** 108.9 PPG / 39.7 RPG / 24.6 APG / 6.8 SPG / 4.8 BPG

**Result: 66-16 -- Grade A "DYNASTY" -- 91.5 pts**

Notes:
- Formula verified (4th time): all 5 players non-null (k=5), OVR = 91.47 -> 66 wins.
- Era skip on MIL paid only the median outcome (Giannis 2010s 17.3, not Kareem 28.5 or
  Giannis 2020s 23.5).
- An all-rounds-17-18 team scores ~91; you need 2-3 rounds in the 23+ range to approach 109.

## Game 5 -- 2026-06-05 ~14:20 local

| Round | Roll (team/decade) | Skips used | Pick | Pos | PPG | RPG | APG | SPG | BPG | OVRpts |
|-------|--------------------|------------|------|-----|-----|-----|-----|-----|-----|--------|
| 1 | SAS / 1980s -> SAS / 2010s | ERA skip (best 16.9; EV 20.5 w/ D-Rob 23.5, Wemby 22.9) -- drew the WORST outcome | DeMar DeRozan | SF | 21.2 | 6.0 | 6.2 | 1.1 | 0.5 | 16.8 |
| 2 | SAC / 1960s | - | Oscar Robertson | PG | 29.7 | 8.7 | 10.5 | null | null | 22.2 |
| 3 | ATL / 1980s | - (skip EVs neutral ~18.0-18.4 vs 17.9) | Moses Malone | C | 20.2 | 11.8 | 1.4 | 1.0 | 1.2 | 17.9 |
| 4 | CHA / 2020s | - (team-skip EV +1.3, held as round-5 insurance) | LaMelo Ball | SG | 21.4 | 5.6 | 7.4 | 1.4 | 0.3 | 17.4 |
| 5 | LAC / 2020s | - (team-skip EV 17.2 = Paul George 17.4, neutral; skip unused) | Paul George | PF | 23.5 | 6.2 | 4.9 | 1.6 | 0.4 | 17.4 |

**Team totals:** 116.0 PPG / 38.3 RPG / 30.4 APG / 5.1 SPG / 2.4 BPG

**Result: 68-14 -- Grade A "DYNASTY" -- 93.9 pts**

Notes:
- Formula verified (5th time): k=4 (Oscar nulls), adjSPG=6.375, adjBPG=3.0 -> OVR 93.86 -> 68 wins.
- Round-1 era skip landed the single worst era in the SAS deck (16.8 vs avg 20.5) -- skips
  raise EV but variance is real.
- Round-1 placement error: putting DeRozan (SF/SG/PF) at SF blocked Dominique Wilkins (19.2)
  in round 3. Multi-position players should be placed in the slot with the FEWEST future
  jackpot players (here SG, since SF-only stars like Wilkins/Bird-class are more common than
  SG-only stars).
- Team skip went unused -- holding it past a +1.3 EV spot was probably right, but it expired
  worthless. With neutral EV in round 5 there is no reason NOT to gamble the skip... unless
  the variance downside (62 available players -> re-roll into a team with no PF over 12) bites.

## Five-game summary

| Game | Record | Pts (OVR) | Grade | Strategy |
|------|--------|-----------|-------|----------|
| 1 | 64-18 | 88.2 | A DYNASTY | raw-sum picks |
| 2 | 59-23 | 82.5 | B CONTENDER | weighted picks, bad rolls |
| 3 | 78-4 | 105.9 | A+ HISTORIC | weighted picks + EV-based skips |
| 4 | 66-16 | 91.5 | A DYNASTY | weighted picks + EV-based skips |
| 5 | 68-14 | 93.9 | A DYNASTY | weighted picks + EV-based skips |
