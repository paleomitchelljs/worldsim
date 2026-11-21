# WP10: peoples that move and mix

**Goal.** Conquest, rule and migration that can change who lives where,
so that a people's share of the world follows its history and not just
its starting land.

**Evidence.**
- **One people keeps winning.** Snake folk lead every `wp8m` seed with
  30-56% of all people, their largest share yet. Each change to the
  world has raised it.
- **Mixing is low.** With `shared_cells` on, about 2% of heads live
  outside their cell's largest people (open-questions.md, "Shared cells").
- **Conquest moves almost no one.** A conqueror settles only
  MIN_GARRISON (4%) of a captured city. Since 2026-11-06 (open-questions.md,
  "Peoples do not move"), whichever people holds a region at about year
  1500 still holds it at 8000.
- **No motive to rule.** Nothing makes a people want to rule others
  rather than raid or clear them (open-questions.md, "Conquest motive").
- **Acculturation shows no measurable effect.** ACC moved no measured
  pattern over a factor of 4 in the screen (sensitivity.md). Shifts in
  peoples' shares are not among the frozen patterns, so nothing measured
  could see it.

Read first: `wsim/shared.py`, `wsim/settlement.py` (displacement,
garrisons), `wsim/culture.py` (acculturation, fusion), `wsim/war.py`
(what a won siege does), `WP7-design.md`, open-questions.md
("Peoples do not move", "Shared cells", "Conquest motive").

## Stage A: measures (records only)

1. Add per-run measures, written to `metrics.json` by `wsim/metrics.py`:
   - each people's share of heads by millennium, and the largest share
     at 8000;
   - the share of land whose plurality people changed between 2000 and
     8000;
   - heads outside their cell's plurality people, by millennium;
   - acculturation and fusion events per millennium;
   - refugees by destination, so that cascades (displacement followed
     within 50 years by raids or displacement where they arrive) can be
     counted (WP7 stage D's missing measure).
2. Rerun nothing beyond one sanity run. Read the measures off `wp8n` if
   the saved state allows, or off one new seed.
3. Add these to `docs/patterns.md` as **reported**, not frozen: there is
   no reference for a fantasy roster's shares.

## Stage B: design note (needs U)

`docs/upgrade/WP10-design.md`, with options and a recommendation for each:
1. **Settling conquered land.** The conqueror's people settle a share of
   a captured city and its hinterland, scaled by violence and
   expansion, instead of the fixed 4%.
2. **Deportation.** A state moves part of a subject people out of
   captured land, or moves its own people in (left out of WP7).
3. **State backing for settlers.** Whether the ruling people's state
   weight (SH_STATE) should also lower subjects' resistance to settlers.
4. **A motive to rule.** Whether a war's aim can be rule (tribute,
   subjects) rather than raid or clearance, and which traits drive it:
   one new trait, or violence, statecraft and proselytism combined.
5. **Acculturation.** Why ACC is inert, and whether it should act on
   subjects of a foreign state more than on neighbours.

## Stage C: build (switches on by default once U agrees)

Build what stage B settles, one switch per mechanism. Sanity run, then
a 5-seed batch against `wp8n`. Report peoples' shares as they come out:
**do not tune them** (memory: refine the world first, and report shifts
in people shares).

## Not in this package

- New peoples or roster changes. Ratios between peoples are U's.
- Language or religion as separate layers.
