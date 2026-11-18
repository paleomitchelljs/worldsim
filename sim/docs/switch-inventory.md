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
| `trade_debit` | 2026-11-17 (WP4 B); default since 2026-11-18 (WP4 D, U) | Trade food is sold from the exporter's surplus cells (TRADE_SURPLUS, C: 0.5) and arrives less carriage between the two states' nearest cities, instead of being created ([structural.md](structural.md)). Needs `food_flow`. Now in `FEATURES`, so `--off trade_debit` turns it off. A state saved before WP4 D keeps it off unless the branch names `--on trade_debit` |
