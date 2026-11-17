# WP1: speed

**Goal.** Cut run time without changing the rules, then add branching
from a saved state so a set of variants shares its early millennia.

**Evidence.** `BASELINE.md`, "Speed". Cost per millennium is flat from
year 0: it scales with the 66,895 cells, not with states. Carrying
capacity (`Kf` -> `K2`) is a quarter of all time at about 209 calls per
tick; `migrate` is a third (its `voyages` alone 15% late on); `raids` 18%;
`climate` about 10%.

I expect stages A-C together to give somewhat under 2x. That is an
estimate from the profile, not a measurement; measure and report.

Read first: `wsim/land.py` (`prepare_capacity`, `dev`, `adapt`,
`biome_fit`, `Kf`, `K2`, `climate`), `wsim/settlement.py` (`migrate`,
`budding`, `voyages`), `wsim/war.py` (`raids`, `deter`, `wars_step`),
`wsim/states.py` (`power_dist`, `projected`, `eff`), `snapcheck.py`,
`docs/running.md`.

**Rules for this package.** These are refactors: the rules of the model
must not change, but histories need not match old runs seed for seed
(reordered arithmetic is fine). Testing is one sanity run per stage
(`GUIDE.md`). Profile before and after with `tools/profile_phases.py` on
an idle machine (`uptime` first) and put both tables in the handoff; the
speed-up is the result that matters.

## Stage A: a per-tick polity table

Polities are dicts in `self.polities`. The array "ruling lineage of each
polity id" (`pl`) is rebuilt by a Python loop in at least `land.climate`,
`land.land_use`, `war.feud`, `war.raid_order`, `culture.exposure`,
`economy.pref_spread`, `settlement.minorities`, `technology.technology`,
`states.polity_stats`, `states.extraction` and `states.food_flows`.
`states.eff` is called 1.68M times per 100 ticks through dict lookups.

1. Add one cached builder that returns arrays indexed by polity id: live
   flag, ruling lineage, people, capital cell, and the ruling lineage's
   administration. Invalidate it with a version counter bumped wherever a
   polity is created, ends, or changes lineage, people or capital
   (`new_polity`, `kill_polity`, `recapital`, the lineage hand-over at the
   top of `polity_stats`, `fuse`, `blend`, successions; grep for
   `p["lin"] =`, `["culture"] =`, `["capital"] =`).
2. Replace each rebuild with the cached arrays. Mind that some call sites
   want only live polities (`-1` for ended ones) and `feud`/`exposure`
   want administration with 0 for ended ones.
3. `eff(P, a)`: under `city_culture` it reads `state_vec(P)`, cached per
   tick in `self._pt`. Keep the cache but hoist `self.city_cols()` and
   `RT_TRAITS.index(a)` out of the call (module-level dicts).

## Stage B: factor carrying capacity

`K2(L, j)` recomputes, for every (lineage, cell) pair it is given,
quantities that depend on the cell alone or the lineage alone.

Cell-only (one vector over all cells, valid until the named arrays
change):

- rain-fed, irrigated, fishing, forage and herd terms: `W.rain_ws`,
  `W.irr_w`, `W.fish`, `W.forage`, `W.herd`, the climate multipliers
  `self.cm`, improvements `self.imp`, land `self.land`, salt `self.salt`
  with `W.irr_share`;
- the grassland flag, `W.area`, `self.Kcell`, `W.water`, `W.wet`,
  `self.Kcap`, the ecotone blend `eco_f` / `eco_tgt`.

Lineage-only (one row per living lineage, valid from the end of
`technology()` to the next, plus any event that edits a lineage's
technology):

- `agri`, the tools factor from `iron`/`steel`, the sod factor from
  `bronze`/`iron`, `fishing`, `dev(L)`, food per head;
- per-biome tables (lineage x 5 biomes): the crop and animal package
  weights from `domlv` with `h_wc`/`h_wa`, and `biome_fit`.

Steps:

1. Build the cell vectors once in `prepare_capacity` (after `climate`).
   Find every later write in the tick to an input: `land_use` (end of
   `grow`) writes `land`, `salt`, `imp`; `raids`, `capture` and `sack`
   write `imp`; `famine` and others do not. Refresh only the affected
   cells at those points (`raid_K` in `war.py` is already such a hook).
2. Build the lineage tables at the end of `technology()`. Find every other
   write to `agri`, `metal`, `bronze`, `iron`, `steel`, `fishing`, `sail`,
   `admin`, `craft`, `domlv` (at least `new_lineage`, which copies the
   parent's row, plus `blend`, `lineage_fusion`, `city_admin`,
   `city_feedback`; grep to be sure) and refresh those rows.
3. Rewrite `K2` as gathers and products over these. Before deleting the
   old `K2`, compare the two once on a few thousand random (lineage,
   cell) pairs late in a run; they should agree to rounding. That one
   comparison is the test.
4. `dev(L)` is also called from `prepare_capacity`, `deter`, sieges,
   `trade_ties` and `exposure`; serve those from the table too.

## Stage C: cache the resident lineage's capacity

The capacity of each occupied cell for the lineage that holds it is
recomputed in `famine`, `grow`, `migrate`, `raids`, `polity_stats`,
`technology` (the "unused farming" term), `food_flows` (with `raw=True`)
and `diagnostics.urban`.

1. Hold `K_res` (and the raw value before the state's take) per cell with
   a dirty mask. Mark a cell dirty when its lineage changes or any input of
   stage B changes there; `extraction` changes the non-raw value for every
   ruled cell, so recompute after it.
2. Serve those call sites from the cache. `migrate` already keeps `Kown`
   and updates it where lineages change; fold that into the same cache.
3. A wrong cache is silent, so this is the one place worth a check: once,
   late in a run, compare the cache with a fresh `Kf` at the start of each
   phase of a single tick. Then remove the comparison.

## Stage D: the remaining hot spots

In the order of the profile; stop when the next item is under about 2% of
step time.

- **`voyages`** (15% late). A Python loop per lineage with a KD-tree ball
  query per voyage and `kept()` called 71,278 times per 100 ticks. Batch
  the ball queries (`query_ball_point` takes arrays), and compute the
  "could be taken" mask once per tick for all coastal cells, per people.
- **`raids`** (18%). Most of the cost is capacity (stages B-C). Then
  replace `np.isin(x, list(self.cities))` with a boolean `is_city` array
  kept current where cities are founded and ended, and build the
  kin-similarity lookup without the Python `zip`.
- **`budding`** runs twice per tick and calls `Kf` per direction; with the
  factored form compute capacity once for all (source, neighbour) pairs.
  `adjacency_by_people` runs three times per tick; it loops over 8
  directions x peoples and can be one `bincount` per direction.
- **`climate`** (about 10%). `W.accumulate` uses `np.add.at` once per
  drainage level, every tick. `np.add.at` is slow; use one precomputed
  sparse upstream matrix (discharge = matrix x cell yield), rebuilt when a
  river changes course. The local noise field is a Gaussian filter of a
  360 x 720 normal draw per tick; draw it at a quarter of the resolution
  and upsample.
- **`wars_step`** (rising to 12%). `power_dist` is called 192,441 times
  per 100 ticks; each call rebuilds `sources(P)` and compares lists before
  returning the cached array. Cache per tick, per state: its sources,
  reach, logistics and the distance array, invalidated by the polity
  version counter of stage A and the graph version `W.gver`.
- **`gc_km`** (62,083 calls). Many are one capital against a state's
  cities; keep a per-tick city coordinate array.

## Stage E: branching from a saved state

Early millennia cost as much as late ones, so six variants that differ
only after year 5000 can share 60% of their run time.

1. Promote `snapcheck.py`'s save and load into `worldsim.py`:
   `--save-state YEAR PATH` (may repeat) and `--from-state PATH`.
2. With `--from-state`, apply `--set`, `--off` and feature switches to the
   loaded state before stepping (`Sim.upgrade()` is the hook for state
   added by newer code), and record in `run.json` the state's own
   `run.json`, the branch year and what changed.
3. Saved states are about 300 MB; refuse to write one inside Dropbox.
4. Check once that a branched run starts and finishes.
5. Document the caveat in `docs/running.md`: a mechanic switched on at the
   branch year has a switch-on transient (the urban batch saw one), so
   branch at least 500 years before the period you compare, and never use
   branching for a mechanic that acts from year 0.

## Stage F: RNG streams and the new baseline (needs U: D12)

Optional. Do it last.

1. One generator (`self.rng`) serves founding, migration, raids, wars,
   diplomacy, revolts, disasters and more, so any change to how often one
   subsystem draws reshuffles all the others. Climate, dragons, rulers,
   city culture and preferences already have their own streams. Give each
   remaining subsystem a named child stream from
   `np.random.SeedSequence(seed).spawn` (or a fixed name-to-offset table,
   as the existing streams use). A/B comparisons then share draws wherever
   the change does not reach, and need fewer seeds.
2. Run a new baseline: seeds 101 and 103, sweep settings, defaults (more
   seeds only if the user wants a batch). Run `realism.py` and, once WP2
   stage B exists, the new metrics. Record the table in `docs/run-log.md`
   and update `BASELINE.md`. If a measure is far from the old runs', say
   so.
3. Save year-3000 and year-5000 states outside Dropbox for later
   packages to branch from.

## Out of scope

- numba, Cython or a rewrite in another language. Revisit only if the
  vectorised model is still too slow after this package.
- Changing `DT`, the cadence of any phase, or the grid.
- Parallelism inside a run. Batches already use the cores.
