# WP5 stage F: polities without cities (design note, 2026-11-18)

For U to confirm before any code. D8 is decided (U, 2026-11-18: build,
as camps). Everything below is C unless marked.

## The choice of form

The brief proposes a camp as a record in `self.cities` with `kind =
"camp"`. I recommend the other form: **a camp polity keeps an empty
`P["cities"]` and a seat cell `P["camp"]`, which is also its
`P["capital"]`. The camp is not in `self.cities`.**

Why:
- `self.cities` is read in about 130 places: urban abandonment, city
  culture rows, city sizes, food flows into cities, trade posts, city
  records, maps. Each would need a "not a camp" test. A camp outside
  the table is skipped by all of them without a change (brief point 1).
- `len(P["cities"])` thresholds (succession, provinces at 4+, steel at
  6, revolts at 2+) count only cities as they stand (brief point 5).
- The cost moves to the places that assume a live state has a city.
  The audit found these:
  - `recapital` kills a state with no cities;
  - `deter` and the siege code pick "the defender's nearest city";
  - `war_bound` and `war_chance` return 0 without cities;
  - `wars_step` closes a war when a side has no cities;
  - about six lookups of `self.cities[P["capital"]]` in `cities.py`
    and `states.py` (city culture and administration).

  Each gets an explicit camp branch.

## 1. What a camp is

- A seat cell, `P["camp"]`. It carries no urban population and keeps
  no city record, culture row or ruin.
- **Territory.** `territory` adds camp seats as sources alongside
  cities. Reach = CAMP_REACH x cohesion x (1 + CAMP_HERD x herding
  share), not administration. (Built with CAMP_REACH 300, about a
  one-city state's reach. The REACH0 (120) first written here gave a
  camp one cell, and most dispersed within 25 years.) With CAMP_HERD 1.5, mounted peoples reach about
  2.5 times as far.
- **Strength.** As for any state (`polity_stats`), from the people in
  its territory.
- **Moving.** Every CAMP_MOVE (10) years the seat moves to the densest
  cell of its lineage within reach. This is a step, not a migration of
  people.

## 2. Forming

- Every CAMP_EVERY (25) years, for each lineage, take its stateless
  occupied cells (`cell_pol < 0`) within CAMP_R (500 km) of its
  densest stateless cell.
- A camp forms there with chance CAMP_P (0.2) per check when heads x
  cohesion trait x (0.5 + hierarchy) >= CAMP_N (C: 150,000; to be set
  by looking at the distribution in one run, not to hit a count).
- It is seated at that densest cell, with origin `camp`.
- Brief's risk: thousands of short-lived camps. The fix is to raise
  CAMP_N, not to add a rule.

## 3. War

- **Camps declare** through `war_chance` like any state. Deterrence
  reads the defender's nearest city, or its seat for a camp defender.
  A camp attacking a city state lays sieges as now. Taking a city
  makes it a city state (section 4).
- **Camps cannot be besieged.** Against a camp, each year the attacker
  fights one battle at the seat:
  - odds PA² / (PA² + PB²), with PB = the camp's projected strength x
    CAMP_EVADE (1.5, mobility);
  - under `army`, the losses are as for a decided siege.
- **A won battle.** With chance (0.5 + the attacker's dominance) / 2
  the camp becomes a vassal (`submit`). Otherwise it scatters: the
  polity ends "scattered" and its land becomes stateless again.
- **A lost battle** costs the attacker cohesion, as a failed siege
  does.
- Raids between cells are unchanged. A camp's raids on a neighbour
  become wars through the usual chance of war.

## 4. Becoming a city state

- When a camp polity takes (captures or is ceded) a city, or a city is
  founded inside its territory and joins it, it becomes an ordinary
  state with that city as capital. `P["camp"]` is dropped.
- A camp's city founding uses the same join rule as for states.

## 5. Ending

- A camp polity ends ("dispersed") when its territory holds fewer than
  CAMP_N / 3 weighted heads at a formation check.
- It also ends when scattered (section 3), absorbed (fusion,
  annexation by a lord, as now), or when its ruling lineage dies out
  and no kin hold the seat.

## Records and switch

- Switch `camps`, on by default, as other switches are.
- `polities.csv`: `camp_years` (years as a camp), and origin `camp`.
- Events of kind `camp`: forming, scattering, the first city.
- `metrics.py` reports the stateless land share by millennium, if not
  already there.

## What I expect, and what to watch

- Expected: the 68% of land outside any state shrinks. Herder peoples
  get polities and a path to large states, by taking cities. Some
  raid-heavy borders become wars.
- Watch:
  - the count and median life of camp polities;
  - whether herders now flood settled land: diversity of peoples per
    landmass;
  - population, since more of the world is at war.

## Decisions for U

1. Form: camps outside `self.cities` (recommended) or inside, as the
   brief has it.
2. Defeat of a camp: scatter or vassal, as above, or vassal only.
3. Formation threshold: set from one run's distribution as above, or a
   number you prefer.
