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
