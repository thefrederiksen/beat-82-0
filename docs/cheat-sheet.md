# 82-0.com CHEAT SHEET -- Classic Mode (one page)

Goal: 5 picks totaling OVR >= 109.4 -> 82-0. That is an average of 21.9 VALUE
points per pick. Every decision below is "maximize VALUE", nothing else.

## 1. THE ONLY FORMULA THAT MATTERS

Score every candidate player with his raw season stat line:

    VALUE = 0.345*PPG + 0.630*RPG + 0.614*APG + 1.148*SPG + 1.250*BPG

Mental version (within ~2%):  PPG/3 + 0.6*(REB+AST) + 1.2*(STL+BLK)

Key per-unit facts:
- 1 rebound = 1.8x a point. 1 assist = 1.8x a point. 1 steal/block = ~3.5x a point.
- NEVER pick by PPG or by raw stat sum (the UI sort). A 25/12/4 big beats a 31/4/4 scorer.
- null STL/BLK (1960s players) is NOT zero -- the engine fills it with your roster
  average. So a null is BETTER than a low value. A 0.5 stl / 0.2 blk guard actively
  drags you down; Wilt's nulls cost nothing.

Team result: OVR = sum of 5 VALUEs (with null stl/blk scaled out);
wins = round(82 * min(OVR/110,1)^1.15). 109.4+ OVR = perfect season.

## 2. PER-ROUND DECISION PROCEDURE

1. Roll lands on (TEAM, DECADE). Run: python src/oracle.py TEAM DECADE
2. Find the best ELIGIBLE pick (a position you still have open).
3. Compare it to the skip baselines in section 3. Burn a skip if the gap is >= 3.
4. Otherwise take the pick and place it at the LEAST flexible open slot he fits
   (see section 4 placement rules).

## 3. SKIP RULES (one team skip + one decade skip per GAME)

Average best pick of a random cell = 19.2. Re-roll EV by what gets locked:

TEAM SKIP (keeps decade, re-rolls team) -- expected new pick by decade:
  1970s 20.8 | 1960s 20.4 | 2020s 19.7 | 1990s 19.2 | 2010s 18.6 | 2000s 18.4 | 1980s 18.2

DECADE SKIP (keeps team, re-rolls decade) -- expected new pick by franchise:
  LAL 23.0 | PHI 21.8 | HOU 20.8 | GSW 20.6 | ORL 20.5 | SAS/BOS/WAS/NOP/SAC ~19.8
  ...worst: MIA 17.7 | TOR 17.5 | CHA 16.9 | MEM 16.6

Burn a skip when (re-roll EV - current best eligible pick) >= 3, or any time the
current cell is below ~17 and a skip is still unspent in round 4-5. Never finish a
game with an unused skip after a below-average roll. On LAL/PHI/HOU/GSW with a weak
decade, the decade skip is almost always right.

## 4. POSITION DISCIPLINE (the #1 avoidable mistake)

The jackpot picks are mostly C-only. KEEP C OPEN as long as possible. Keep PG
second-longest (Oscar/Westbrook/Luka/Harden class). Dump picks onto SG/SF/PF first.

- Multi-position player: always place at his most-replaceable slot (SG/SF first,
  then PF). Giannis (PF/PG/SF/C) goes to SF/PF, never C.
- Never put a sub-20 big at C before round 4 unless both skips are gone.

## 5. JACKPOT TABLE -- memorize these (VALUE 22+)

  GSW 60s Wilt          32.0  C     | LAL 20s Luka         23.1  PG/SG/SF
  PHI 60s Wilt          28.8  C     | SAS 20s Wembanyama   22.9  C
  MIL 70s Kareem        28.5  C     | LAL 00s Shaq         22.8  C
  LAL 70s Kareem        26.7  C     | GSW 70s Thurmond     22.6  C/PF
  DEN 20s Jokic         25.4  C     | MIN 00s Garnett      22.5  C/PF/SF
  WAS 20s Westbrook     24.2  PG    | BKN 20s Harden       22.5  PG/SG
  HOU 90s Hakeem        23.8  C     | SAC 60s Oscar        22.2  PG
  LAC 70s McAdoo        23.6  C/PF  | BOS 60s Russell      22.2  C
  MIL 20s Giannis       23.5  PF+   | LAL 10s LeBron       22.1  any
  SAS 90s D.Robinson    23.5  C     | NYK 70s McAdoo       22.1  C/PF
  CHI 80s Jordan        23.5  SG/SF | ATL 60s Pettit       22.0  C/PF
  DAL 20s Luka          23.4  PG+   | LAL 90s Shaq         22.0  C
  NOP 10s Cousins       23.4  C     | BOS 80s Bird         21.9  PF/SF
  HOU 80s Moses         23.1  C     | SAC 90s Webber       21.8  C/PF
  ORL 90s Shaq          23.1  C     | LAL 60s Wilt         23.1  C

Odds per roll: 17/180 cells (9.4%) hit 23+; 29/180 (16%) hit 21.9+. Skips roughly
double your shots. Three 23s + two 20s = 109+ = 82-0.

## 6. WHAT "WINNING EVERY TIME" REALLY MEANS

Perfect play guarantees you never lose value to a decision -- but 82-0 itself is
roll-gated: you need ~3 jackpot cells in one game (low single-digit % even played
perfectly). Played by this sheet, an average game lands ~95-100 OVR (low-70s wins,
A+/HISTORIC) and you bank an 82-0 whenever the slot machine cooperates. There is no
pick strategy that forces 82-0 from bad rolls -- value comes from (a) never
mis-picking, (b) never mis-placing, (c) spending both skips on +EV hunts.

Tools: oracle (cell ranking)  python src/oracle.py TEAM ERA
       skip sweeps            python src/oracle.py --eras TEAM | --teams ERA
       full sim check         python src/simulate.py
