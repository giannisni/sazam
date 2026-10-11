# Filtering mainstream Shazam false positives

Shazam tends to "hear" famous anthems (Tiësto – Adagio, 2 Unlimited, System F, Rank 1 – Airwave…) inside dense, quick-cut,
layered or pitched sections of underground mixes. A track is flagged as **likely slop** when BOTH hold:

1. **Mainstream** — Deezer popularity `rank` ≥ 300,000 (`slop_scores.py`, public Deezer search API).
   e.g. Tiësto – Adagio 544k, Darude – Sandstorm 828k vs. Na Nich – Apex 26k.
2. **Weak evidence** (`slop_decide.py`) — none of:
   - ≥3 consecutive native-speed hits in the main scan (sustained run), or
   - ≥4 of 6 shifted re-check clips agreeing on it, or
   - confirmed by set79 / the artist's own tracklist.

Flagged + never 2 hits in a row → **removed**. Flagged + exactly 2 in a row → **moved to Uncertain**.

Kept despite being mainstream (solid evidence): Darude – Sandstorm (24 hits, 6/6 agree), Underworld – Born Slippy (4/6, set79),
Joy Orbison – flight fm (11-hit run), Niels van Gogh – Pulverturm (3-run), Veracocha – Carte Blanche (set79).
