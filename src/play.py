"""Live browser harness: plays official games on 82-0.com under a Policy and
writes one history/game-NNN.json per game (schema: history/README.md).

Connects over CDP to the Brave instance of cc-playwright connection `beat820`
(launch it first: cc-playwright --connection beat820 start --url https://www.82-0.com/).

Usage: python src/play.py --games N [--version v1-scripted] [--port 9223]
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

from engine import Engine, POSITIONS
import strategy

sys.stdout.reconfigure(encoding="ascii", errors="replace")

BASE = "https://www.82-0.com/"
HIST = os.path.join(os.path.dirname(__file__), "..", "history")

ERA_MAP = {"60's": "1960s", "70's": "1970s", "80's": "1980s", "90's": "1990s",
           "00's": "2000s", "10's": "2010s", "20's": "2020s"}


class Harness:
    def __init__(self, page, eng, pol):
        self.page = page
        self.eng = eng
        self.pol = pol

    # ---- low-level helpers ---------------------------------------------

    def text(self):
        return self.page.evaluate("() => document.body.innerText")

    def wait_text(self, pred, timeout=25.0, what="condition"):
        deadline = time.time() + timeout
        while time.time() < deadline:
            t = self.text()
            if pred(t):
                return t
            time.sleep(0.3)
        raise RuntimeError(f"timeout waiting for {what}; page text starts: "
                           f"{self.text()[:300]!r}")

    def click_court_slot(self, slot):
        """Click the court position button (w-16 class, exact text)."""
        ok = self.page.evaluate(
            """(slot) => {
                document.querySelectorAll('#cc-slot-target').forEach(
                    e => e.removeAttribute('id'));
                const b = [...document.querySelectorAll('button')].find(
                    e => e.textContent.trim() === slot && e.className.includes('w-16'));
                if (!b) return false;
                b.id = 'cc-slot-target';
                return true;
            }""", slot)
        if not ok:
            raise RuntimeError(f"court slot button {slot} not found")
        self.page.click("#cc-slot-target")

    def click_skip(self, kind):
        """kind: 'team' or 'era' -- the header respin buttons."""
        ok = self.page.evaluate(
            """(kind) => {
                document.querySelectorAll('#cc-skip-target').forEach(
                    e => e.removeAttribute('id'));
                const b = [...document.querySelectorAll('button')].find(
                    e => e.textContent.trim().toLowerCase().includes(kind)
                         && e.querySelector('svg') && !e.disabled);
                if (!b) return false;
                b.id = 'cc-skip-target';
                return true;
            }""", kind)
        if not ok:
            raise RuntimeError(f"{kind} skip button not found or disabled")
        self.page.click("#cc-skip-target")

    def click_player(self, name):
        """Search for the player, then click their card by exact name text."""
        box = self.page.locator("input[placeholder*='Search']")
        box.fill(name)
        time.sleep(0.4)
        self.page.get_by_text(name, exact=True).first.click()

    # ---- state parsing ---------------------------------------------------

    @staticmethod
    def parse_roll(t):
        """From selecting-phase text: round number, team, era ('Round 2/5\\nMIN\\n20's...')."""
        m = re.search(r"Round (\d)/5\n([A-Z]{3})\n(\d0's)", t)
        if not m:
            return None
        return int(m.group(1)), m.group(2), ERA_MAP[m.group(3)]

    @staticmethod
    def parse_result(t):
        # site renders "64<en dash>18" and "<middle dot> 88.2 pts"
        m = re.search("PROJECTED RECORD\s*\n+(\d+)\u2013(\d+)\n+(\S+)\n(\w+)\n\u00b7 ([\d.]+) pts", t)
        if not m:
            raise RuntimeError(f"cannot parse end screen: {t[:400]!r}")
        wins, losses = int(m.group(1)), int(m.group(2))
        grade, label, ovr = m.group(3), m.group(4), float(m.group(5))
        totals = {}
        for key in ("PPG", "RPG", "APG", "SPG", "BPG"):
            tm = re.search(r"([\d.]+)\n\n" + key + r"\n", t)
            totals[key.lower()] = float(tm.group(1)) if tm else None
        return {"wins": wins, "losses": losses, "ovr": ovr,
                "grade": grade, "label": label}, totals

    # ---- one full game ---------------------------------------------------

    def play_game(self, game_no):
        page = self.page
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        # defensive: dismiss first-run modal / cookie banner if present
        for txt in ("Don't Show Again", "Decline"):
            loc = page.get_by_text(txt, exact=True)
            if loc.count() and loc.first.is_visible():
                loc.first.click()
                time.sleep(0.3)
        page.get_by_text("Play Classic", exact=True).first.click()

        open_pos = set(POSITIONS)
        taken_ids = set()
        roster = []
        rounds = []
        team_skip, decade_skip = True, True

        for round_no in range(1, 6):
            self.wait_text(lambda t: "SPIN" in t and f"Round {round_no}/5" in t,
                           what=f"round {round_no} spin phase")
            page.get_by_text("SPIN", exact=True).first.click()
            t = self.wait_text(
                lambda t: "players available" in t and self.parse_roll(t),
                what=f"round {round_no} selecting phase")
            _, team, era = self.parse_roll(t)
            rolls = []

            while True:
                action = self.pol.decide(self.eng, team, era, open_pos, taken_ids,
                                         roster, team_skip, decade_skip)
                if action[0] in ("skip_team", "skip_decade"):
                    kind = "team" if action[0] == "skip_team" else "era"
                    rolls.append({"team": team, "era": era,
                                  "skip_after": "team" if kind == "team" else "decade"})
                    if kind == "team":
                        team_skip = False
                    else:
                        decade_skip = False
                    old = (team, era)
                    self.click_skip(kind)
                    t = self.wait_text(
                        lambda t: "players available" in t
                        and self.parse_roll(t)
                        and (self.parse_roll(t)[1], self.parse_roll(t)[2]) != old,
                        what=f"respin after {kind} skip")
                    _, team, era = self.parse_roll(t)
                    continue

                _, player, slot = action
                rolls.append({"team": team, "era": era, "skip_after": None})
                val = self.eng.marginal(roster, player)
                self.click_player(player["player"])
                self.wait_text(lambda t: "Placing:" in t,
                               what=f"placement prompt for {player['player']}")
                self.click_court_slot(slot)
                roster.append(player)
                taken_ids.add(player["id"])
                open_pos.discard(slot)
                rounds.append({
                    "round": round_no, "rolls": rolls,
                    "pick": player["player"], "position": slot,
                    "stats": {k: player[k] for k in
                              ("ppg", "rpg", "apg", "spg", "bpg")},
                    "ovr_pts": round(self.eng.face_pts(player), 2),
                    "rationale": f"policy {self.pol.version}: exact marginal "
                                 f"+{val:.2f} OVR, slot {slot}",
                })
                print(f"  r{round_no}: {team}/{era} -> {player['player']} "
                      f"({slot}, +{val:.2f})"
                      + ("" if len(rolls) == 1 else f"  [{len(rolls)-1} skip(s)]"))
                break

        t = self.wait_text(lambda t: "PROJECTED RECORD" in t, what="end screen")
        result, totals = self.parse_result(t)

        predicted = self.eng.team_ovr(roster)
        if abs(predicted - result["ovr"]) > 0.05:
            raise RuntimeError(
                f"engine mismatch: predicted OVR {predicted} but site shows "
                f"{result['ovr']} -- investigate before trusting the policy")

        record = {
            "game": game_no,
            "played_at": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
            "mode": "classic",
            "strategy_version": self.pol.version,
            "rounds": rounds,
            "totals": totals,
            "result": result,
        }
        path = os.path.join(HIST, f"game-{game_no:03d}.json")
        with open(path, "w", encoding="ascii") as f:
            json.dump(record, f, indent=2, ensure_ascii=True)
        print(f"game {game_no}: {result['wins']}-{result['losses']} "
              f"(OVR {result['ovr']}, {result['grade']} {result['label']}) -> {path}")
        return result


def next_game_no():
    nums = [int(re.search(r"game-(\d+)\.json", p).group(1))
            for p in glob.glob(os.path.join(HIST, "game-*.json"))]
    return max(nums) + 1 if nums else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=1)
    ap.add_argument("--version", default="v1-scripted")
    ap.add_argument("--port", type=int, default=9223)
    args = ap.parse_args()

    eng = Engine()
    pol = strategy.get(args.version)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://localhost:{args.port}")
        ctx = browser.contexts[0]
        page = next((p for p in ctx.pages if "82-0.com" in p.url), None)
        if page is None:
            page = ctx.new_page()
        h = Harness(page, eng, pol)

        for _ in range(args.games):
            n = next_game_no()
            print(f"--- game {n} ({pol.version}) ---")
            h.play_game(n)


if __name__ == "__main__":
    main()
