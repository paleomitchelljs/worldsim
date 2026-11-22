# Switch inventory (2026-11-02, for the streamlining)

Step 2 of "Before building" in [open-questions.md](open-questions.md).
82 switches, all on by default. The current model is archived in
`archive/v1_2026-11-02/`. Proposals are C; **accepted (U, 2026-11-02)**.

Fates:
- **Core**: always on; the switch and the off-branch are deleted.
- **Drop**: the switch and its code go (superseded, or the off-branch is
  dead weight).
- **Merge**: several switches become one mechanism.
- **Rebuild**: rewritten at the city level anyway (open-questions.md,
  "Cities as a nested unit of culture"); decide its form there, not here.
- **Keep switch**: experimental, so ablations stay possible.

"Checks" = number of `in self.on` tests in the code.

## Superseded (Drop the old path)

| Switch | Checks | What replaces it |
|---|---|---|
| `war_motive` | 1 | `war_v2`'s motive rule. Its branch runs only with `war_v2` off. Drop it and the pre-motive war rule. |
| `succession` (path without `rulers`) | 1 | `rulers`' `reign_end`. Keep succession as part of rulers; drop the old path. |
| `separation` off-branch | 5 | Spacing meaning, default since 2026-10-29. Drop the old avoidance meaning. |
| `dispersal` off-branch | 8 | Seafaring does nothing under `dispersal`; expansion drives voyages. Drop the seafaring trait entirely (it is still carried and drifted). |
| `acculturation`'s first path under `mission` | 1 | With `mission` on, the old contact-weighted path is switched off inside the code (`has_c[:] = False`). Drop it; `mission` is the mixing rule. |
| `flat_drift` off-branch | 2 | U 2026-11-01: drift in trait units, reflected at 0.01/0.99. Drop logit drift at lineage splits. |
| `dynasty` | 1 | Cohesion age from the current dynasty. Now that rulers have dynasties, tie it to those (Merge into rulers). |

## Core (remove the switch, keep the mechanism)

Long-settled, on in every run since they were added, and nothing argues
for ablating them now:

`costs`, `fiscal`, `unrest`, `vassals`, `balance`, `land`, `climate`,
`supply`, `minority`, `immunity`, `improvements`, `dragons`,
`dragon_hosts`, `hierarchy`, `patience`, `dominance`, `fishing`,
`ore_trade`, `food_units`, `shuffle`, `logistics`, `domestication`,
`craft`, `resources`, `guarded`, `salinity`, `war_goals`, `scale`,
`development`, `density_cap`, `land_pressure`, `war_v2`, `two_sided`,
`raid_order`, `kin_raids`, `sod`, `pastoral`, `devastation`, `feuding`,
`war_hardy`, `colonies`, `travel_reach`, `provinces`, `precious`,
`causal_exp` (U principle: no causeless trends).

Questions for you:
- **`density_cap`**: **drop as a hard cap (U, 2026-11-02)**: trade
  cities should support higher densities. Proposed (C): a city cell's
  capacity rises with the food its trade brings in.
- **`pastoral`**: **core (U, 2026-11-02)**; the only route to steppe
  peoples and mounted conquest.

## Merge

| New mechanism | From | Note |
|---|---|---|
| Roads | `roads`, `road_tech` | Road engineering becomes how roads work. |
| Alliances | `balance`, `ally_duty`, `ally_lapse`, `ally_balance`, `betrayal` | One alliance module: formation, duty, lapse, end of the threat, betrayal. |
| Trade and goods | `trade_assets`, `trade_mean`, `trade_floor`, `trade_posts`, `goods_value`, `goods_appetite`, `resources`, `precious`, `ore_trade` | One trade module. Nine switches for one system. |
| Superiority | `superiority`, `sup_exp` | One trait with its causes. |
| Tolerance path | `tol_path`, `trait_path` | Both are path dependence of traits; one rule. |

## Rebuild at the city level

These change form with the nested city level. Settle their shape in
the city design, not here:

| Switch | Why it moves |
|---|---|
| `acculturation`, `acc_cross`, `mission`, `conformity`, `proselytism` | Mixing becomes city to city (contact x similarity), plus the rural pull through conformity. |
| `experience`, `spiky`, `life_memory`, `revolt_exp` | Experience pushes the city that lived it, not the lineage. |
| `rulers`, `ruler_traits` | Rulers draw around the capital city's culture. |
| `turmoil` | Becomes recoverable disorder on the state and its cities, not the lineage's administration. |
| `separation`, `trade_posts`, `colonies` | Settlement and city founding are where cities get their founding culture. |
| Technology (no switch) | Invented in cities, spread between them; a rural baseline on the lineage. |

## Keep a switch (experimental)

| Switch | Why |
|---|---|
| `revolt_viol` | Drives the violence rise in the rulers batch; still a live question. |
| `fortress` | New, single number, effect not yet separated. |
| `diagnostics` | Records only (`price.csv`, `checks.txt`); keep for speed. |

## A correction on drift (C, 2026-11-02)

Earlier today I said cultural traits drift on the logit scale. That is
wrong for default runs: `flat_drift` is on by default (your decision
of 2026-11-01, made to remove the logit lean toward 0.5), so drift at
lineage splits is in trait units, reflected at 0.01 and 0.99. Logit is
used only for run-to-run and founding-group jitter (`--vary`,
`--start-vary`) and, since today, for ruler draws and the ruler pull.

So the ruler draws reintroduce the lean toward 0.5 that `flat_drift` was
made to remove. You accepted that mean reversion for rulers knowingly,
but the decision rested on my wrong premise. **Decided (U,
2026-11-02): rulers draw in trait units** with reflection, like
`flat_drift`. Open: the same for city δ (C: yes, for consistency).

## Optional switches (off unless named in `--on`)

From WP4 stage B (2026-11-17), `params.OPTIONAL` lists mechanics that
are off by default and switched on with `worldsim.py --on NAME`.
`--off all` leaves them as they are. The list is empty since WP4 D.
`--on` also takes a default switch, so that a branch from a state saved
before that switch became a default can turn it on.

| Switch | Since | What it does |
|---|---|---|
| `site_defence` | 2026-11-18 (U) | Each city site's own defence multiplier, clip(exp(0.12 t3), 0.5, 3), on top of terrain ([rules/war.md](rules/war.md)) |
| `ruler_mil` | 2026-11-18 (U) | Each ruler's offensive talent (exponential, mean 0.1) multiplies the state's strength when it besieges; half carries into each later reign ([rules/war.md](rules/war.md)) |
| `war_odds` | 2026-11-18 (WP5 B, U: build) | Steeper odds gate on declaring war (with a floor for the hungry, the hating, the zealous); sieges only at win probability >= 0.15, else ravage or sit; wars with no siege for 15 years end "abandoned"; a defender facing odds >= 0.6 may submit before the siege and never cedes its last city ([structural.md](structural.md)). A state saved before WP5 B keeps it off unless the branch names `--on war_odds` |
| `pol_step` | 2026-11-18 (WP5 D, U: build; sieges with a length) | Diplomacy, war and rebellion run every year inside the 5-year tick (DT_POL); a siege lasts 1-8 years by the city's defence and is decided at its end; territory and strength refreshed after a year in which a city changed hands ([rules/war.md](rules/war.md)). Off: one political step per tick, sieges decided when laid |
| `army` | 2026-11-18 (WP5 E) | Field armies: states at war raise up to 4% of their people from their own cells over about 2 years, feed them from their own harvest (`taken_army`), and send survivors home in peace; the field share scales siege strength and half of city defence; decided sieges cost the loser 20% and the winner 5% of its army (deaths "battle"); the war's ending rises with soldiers lost, not age; replaces WAR_COST ([rules/war.md](rules/war.md)). A state saved before WP5 E needs `--on army` |
| `camps` | 2026-11-18 (WP5 F, U: build as camps outside the city table) | Polities without cities: a stateless lineage forms a camp polity when heads x cohesion x (0.5 + hierarchy) near its densest cell pass 2.1e4; the seat moves; reach from cohesion and herding; no rent or tax; cannot be besieged, only brought to battle (defeat: vassal or scattered); taking a city makes it a state ([rules/states.md](rules/states.md)). A state saved before WP5 F needs `--on camps` |
| `epidemic` | 2026-11-18 (WP6 C; U: plague spreads over time and reaches people outside states) | Plague as an epidemic: any city may start one (crowd size x trade ties); it spreads cell to cell (up to 60 rings a tick, faster in dense land) and along trade ties, strikes each cell once, and ends when it reaches no new cell. Off: the old one-tick burst through states ([rules/disasters.md](rules/disasters.md)) |
| `upkeep` | 2026-11-18 (WP6 C) | Improvements need hands: where a cell's people fall below 0.7 of their 50-year mean, its works decay at up to 0.1 a year, so capacity lost in a crash takes decades to rebuild ([rules/population.md](rules/population.md)) |
| `shared_cells` | 2026-11-18 (WP7 C; U: D9, presence table, niche overlap, inner raids) | Any number of peoples per cell, one row each in the presence table: competition for food weighted by niche overlap, movement into cells others hold, raids inside a cell, rows ordered by food-equivalents each tick. Off: one people plus one capped or competing minority, as before ([rules/population.md](rules/population.md)) |
| `displacement` | 2026-11-18 (WP7 D; U: flight share 1 − violence) | Of those removed by raid takeover, sack, clearance or expulsion, the share 1 − attacker violence flees up to 3 cells to its own people or empty land; the rest die ([rules/population.md](rules/population.md)) |
| `trade_debit` | 2026-11-17 (WP4 B); default since 2026-11-18 (WP4 D, U) | Trade food is sold from the exporter's surplus cells (TRADE_SURPLUS, C: 0.5) and arrives less carriage between the two states' nearest cities, instead of being created ([structural.md](structural.md)). Needs `food_flow`. Now in `FEATURES`, so `--off trade_debit` turns it off. A state saved before WP4 D keeps it off unless the branch names `--on trade_debit` |
| `climate_fields` | 2026-11-19 (WP8 B) | On a world file with climate fields (`world_v2.gpkg`, the default): steppe and dryness from aridity (P/PET) instead of distance to the coast and runoff by biome; farming and herding get a gradient within each biome from growing-degree days and aridity, normalised so each biome's total stays as it was ([model-description.md](model-description.md) 2.3). No effect on `world.gpkg` |
| `floodplain` | 2026-11-19 (WP8 C); default since 2026-11-19 (U) | Irrigation on the floodplain's area (valley length × a width growing with √discharge, wider on alluvium and at deltas, narrower in relief) at 20 people/km² of irrigated land, instead of 9 × √(Q/3000) over the whole river cell ([model-description.md](model-description.md) 2.3). A state saved before WP8 keeps it off unless the branch names `--on floodplain` |
| `clearing` | 2026-11-20 (U); default | Farmers clear the forest they work and herders burn for pasture; the cleared share of a jungle or temperate-forest cell farms, forages and herds at grassland's values, and grows back when unused ([structural.md](structural.md#land-clearing-clearing)). A state saved before it starts with nothing cleared |
| `clear_terrain` | 2026-11-20 (U); default (untested until the screen ends) | Cleared forest's travel cost and terrain defence blend toward grassland's by the cleared share, every 50 years where the share has moved by 0.05 ([structural.md](structural.md#cleared-land-as-terrain-clear_terrain)) |
| `fire` | 2026-11-20 (U); default (untested until the screen ends) | Foragers keep up to 0.3 of temperate forest burnt open; the burnt share forages × 1.25, and farmers start clearing from it ([structural.md](structural.md#burning-by-foragers-fire)) |
| `conquest_settle` | 2026-11-21 (U, D13); default | After a city of another people is taken, the conqueror's people settle it and its land, up to CQ_MAX of the hosts' food x expansion x establishment, from the state's crowded cells; hosts of equal food pushed out (WP10, `wsim/movement.py`) |
| `deport` | 2026-11-21 (U, D13); default | A state moves DEP_FRAC of a subject city's people to its core and settles its own people there (WP10) |
| `assimilate` | 2026-11-21 (U, D13); default | Under long rule by another people, subjects join the ruler's people at ASSIM_RATE x the `acc_cross` clock x tolerance x (0.5 + proselytism) (WP10) |
| `muster` | 2026-11-21 (U, D15); default | A state that declares a war starts it with half its full levy raised at once from its own cells ([rules/war.md](rules/war.md)) |
| `campaign` | 2026-11-21 (U, D15); default | A land, rule or resource war that takes its goal aims at the defender's next nearest city while the odds there stay at ODDS_MID or better ([rules/war.md](rules/war.md)) |
| `ruler_odds` | 2026-11-21 (U, D15); default | The ruler's offense enters the attacker's reading of its odds when deciding on war ([rules/war.md](rules/war.md)) |
| `camp_tribute` | 2026-11-21 (U, D15); default | Herding camps make the cities they win pay tribute (vassals) instead of taking them, and stay camps ([rules/war.md](rules/war.md)) |
| `vassal_annex_cross` | 2026-11-21 (U, D15); default | Lords may annex vassals of another people, at the kin rate x (1 - vassal's tolerance) x lord's dominance ([rules/states.md](rules/states.md)) |
