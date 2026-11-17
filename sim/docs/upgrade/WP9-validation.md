# WP9: validation

**Goal.** Know which parameters matter, and test the model against
something it was not adjusted to.

**Why.** `wsim/params.py` has 400 constants (362 numeric) and 27
switches. The checks are about ten stylized facts (`docs/diagnostics.md`).
Most numbers are marked C. On 2026-11-09 three capital levers (`FF_TAX`,
`FF_CAP_KM`, `FF_ABS`) were varied and the run log notes that together
they "put the largest city in the reference range"; that is close to
tuning toward a target, which the project's principles forbid. With this
many free numbers, matching a handful of regularities says little about
whether the mechanisms are right.

Read first: `docs/README.md` (principles), `docs/diagnostics.md`,
`docs/run-log.md` (the 2026-11-09 batches), `wsim/params.py`,
`wsim/metrics.py` (from WP2).

## Stage A: freeze the measures

1. Write `docs/patterns.md`: the list of patterns a run is judged on,
   fixed **before** the screen and the later packages' batches are read.
   For each: definition (a function in `wsim/metrics.py`), the reference
   and its source, how rough the reference is, and the scale (world,
   landmass, state, city). Take the existing checks and the measures in
   `BASELINE.md`.
2. Mark which patterns have already been used to choose a parameter
   (search `docs/run-log.md` and `docs/structural.md` for where a value
   was picked after looking at a measure). Those can no longer count as
   evidence for the model.
3. Add patterns that no one has looked at yet, to serve as held-out
   checks. Candidates (C): spacing between neighbouring cities against
   local density; the size distribution of states below the top ten;
   duration distribution of wars between peers; share of cities that are
   ports or on rivers, by size class; how long a region stays under one
   state; the spread of trait values between cities of one lineage.
   Give each a reference only if one exists; a pattern can also be judged
   on its spread across seeds.
4. The principle "judge on variance" applies: for every pattern report
   the range across seeds first.

## Stage B: sensitivity screen (needs U: D4 for SALib, or hand-roll)

1. Choose about 30 parameters: the ones the run log shows were adjusted,
   plus the leading rate of each subsystem (growth, budding, raids, war
   base rate, cohesion decay, revolt base, extraction, food carriage,
   trade rate, acculturation, experience scale, technology rates,
   climate amplitude, plague). Give each a range (C: a factor of 2 either
   way unless the docs justify another).
2. Morris screening (elementary effects): `r` trajectories of `k + 1`
   runs. With `k = 30` and `r = 8` that is 248 runs. At about 14 minutes
   each and 8 at a time, roughly 7-8 hours on an idle machine; ask the
   user when to run it. Use 6,000 years to save a quarter of that if the
   patterns allow. One seed per point is acceptable for Morris, but run
   the baseline point on six seeds to know the seed noise, and report
   every effect against that noise.
3. Output: for each pattern, the parameters ranked by mean absolute
   elementary effect, with its spread (non-linearity and interactions).
   Write it up in `docs/sensitivity.md`.
4. Conclusions to draw:
   - parameters with no effect above seed noise on any pattern: freeze
     them and say so in `params.py`; if a whole mechanic is inert, propose
     removing its switch and code;
   - patterns that respond to almost nothing: they cannot discriminate;
   - patterns that respond to one parameter only: that parameter was
     effectively a dial for that pattern; flag it.
5. Do not use the screen to pick values.

## Stage C: scope an Earth test (needs U: D11; scoping only)

The strongest available check of "where do cities and states form" is to
run the same rules on real geography and compare with history. Turchin
et al. (2013, *PNAS*) did this for the Old World with a far simpler
model. This stage produces a plan and a cost, not a build.

1. **Inputs.** A world file with the same columns as `world.gpkg` at
   0.5°, for Earth: elevation and relief (ETOPO); biomes collapsed to the
   five classes (Köppen-Geiger or a potential-vegetation map, not present
   land use); rivers and discharge (HydroSHEDS / GRDC); soils; coast and
   ocean productivity; copper, tin and iron districts known in antiquity.
   List each dataset, its licence and size. Downloads need the user's
   consent.
2. **Roster.** One people (Humans) with founding groups placed where the
   record puts early farmers, or placed by the sim's own `wander` rule to
   test that too. Domestication hearths at their known locations, or drawn
   by the sim's rule. Say which choice tests what.
3. **Scoring** (all checks, none tuned on):
   - city sites: the sim's cities by year against a historical city
     dataset (Reba, Reitsma and Seto 2016 give locations and populations
     from 3700 BCE), as a rank correlation of density on a coarse grid
     and as hit rates within a distance;
   - population density at a date against HYDE, by region;
   - the areas where large states recur (Seshat or Turchin's maps);
   - timing: first cities, bronze and iron by region, to the nearest
     millennium only.
4. **What a failure means.** If the sim puts cities on every large river
   regardless of history, that is still informative: it measures how much
   of the fantasy map is geography alone, which is the question
   `BASELINE.md`'s cross-seed table raises.
5. Deliver `docs/earth-test-plan.md` with the steps, the effort per step
   and the risks, for the user to decide.

## Not in this package

- Calibrating any parameter to Earth. The test is held out; using it to
  tune would spend it.
- Formal statistical fitting (ABC, emulators). Consider only if the
  screen shows a small set of parameters that matter.
