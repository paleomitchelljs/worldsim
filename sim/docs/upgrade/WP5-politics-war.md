# WP5: politics and war

**Goal.** An interstate system: wars that have odds, duration and cost;
fewer throwaway states; polities that can exist without a city.

**Evidence** (`BASELINE.md`, `al_seed103`).
- 69% of wars end inside the 5-year tick in which they start; 57% have at
  most one siege.
- 3.8% of wars are between two states of 5+ cities.
- The median siege is launched at a win probability of 0.064 (both sides
  pooled); 21.5% succeed.
- 66% of polities never pass one city; their median life is 35 years.
  5,872 polities in 8,000 years.
- 6-12% of states with 2+ cities are at war at a time.
- 54 of 910 ended states with 3+ cities lasted over 1,000 years (longest
  4,720).
- The largest state is 23 disconnected pieces.

**What the code does** (read these before changing them).
- `war.war_chance`: chance per tick = `DT x WAR_BASE x cohesion x
  (0.5 + violence) x (1 - tie) x deterrence x motive`. Deterrence is
  `min(1, 2R²/(1 + R²)) ** DET_K`, with `R` from `war.deter` (strength
  projected to the defender's nearest city over its defence there). At
  R = 0.25 that is 0.12: a war at 1:4 is eight times less likely than one
  at par, not ruled out, and weak neighbours are many.
- `war.wars_step`: every tick each war gets `1 + LOG_SIEGE x logistics`
  sieges at the defender's city nearest the attacker's capital (or the
  goal), whatever the odds; the win probability is
  `PA² / (PA² + PB²)`. Then the war ends with probability
  `WAR_END0 + 0.03 x ticks` (less with logistics).
- Strength (`states.polity_stats`) is recomputed each tick from
  population; there is no army that is raised, lost and rebuilt. War costs
  a flat `WAR_COST` of population per tick in states at war.
- `states.update_cities`: a new city inside a state joins it with
  probability `0.3 + 0.7 x statecraft` (same people) or 0.7 (another
  people); otherwise, and always outside any state, it founds a polity.
  Revolts, shattering and partition also found polities.
- `states.territory`: each tick, every cell goes to the nearest city (by
  travel cost) if within that city's state's reach. Nothing persists.
- A polity cannot exist without a city.

Read first: `wsim/war.py` (all), `wsim/states.py` (`update_cities`,
`territory`, `polity_stats`, `diplomacy`, `rebellions`, `revolt`,
`reach`, `projected`, `power_dist`), `docs/rules/war.md`,
`docs/rules/states.md`, `docs/structural.md` (war sections),
`docs/open-questions.md` ("Empire size", "Peoples do not move").

Do WP1 and WP2 first. Stages B onward are mechanic changes, each behind
its own switch, each tried on one or two full runs (`GUIDE.md`).

## Stage A: diagnosis (records only)

Do not design fixes before these are measured. Each is a small record
plus a table in `docs/run-log.md`.

1. **Where polities come from.** Tag every `new_polity` call with its
   origin: city founded outside any state; city founded inside a state
   that did not join; revolt (by kind); shatter; partition; colony. Write
   it to `polities.csv` (`origin`). Tabulate count, median life and how
   each origin ends.
2. **Sieges by side.** Split the odds distribution by `side` (attacker's
   sieges against counter-offensives) and by the size of both states.
3. **Why wars are short.** For wars ending inside a tick: the ending
   (`why`), sieges, and the defender's size. How many are a one-city
   defender falling at the first siege?
4. **Long-lived states.** For states that lasted over 1,000 years: the
   landmass, peak size, number of neighbours over time, wars fought,
   revolts suffered, dynasties. Are they isolated island states that
   nothing can reach?
5. **Contiguity.** For the twenty largest states at each millennium:
   pieces joined by land, and pieces within sailing range of one another.
   How much of the fragmentation is sea empire?

Put the findings and a recommended form for stages B-F to the user. The
forms below are the review's proposals; change them if stage A says so.

## Stage B: odds-gated war (switch `war_odds`)

1. **Declaring.** Replace the deterrence factor with a steeper gate on
   `R`: a logistic in `log R` centred at `ODDS_MID` (C: 0.7) with width
   `ODDS_W` (C: 0.35). Long odds stay possible where history has them:
   multiply the gate's floor by desperation (`1 - fed`) and by the enmity
   and faith motives. Update `war_bound`, which must stay an upper bound
   of `war_chance`.
2. **Besieging.** In `wars_step`, an attacker besieges a city only when
   the win probability passes `SIEGE_MIN` (C: 0.15); otherwise it ravages
   (a raid on the target's hinterland: improvements and population, as
   `raids` does) or sits. A war with no siege for `WAR_STALL` years ends
   as "abandoned".
3. **A defender that would lose anyway.** `siege_terms` and the submit
   branch already let a weak defender become a tributary; check they fire
   before a hopeless defence, not only after a won siege.

Expected: fewer wars; a higher share of sieges won; more tributaries;
one-city states living longer. Watch the largest states: easier
submission could grow them, harder declaration could shrink them.

## Stage C: time constants in years

Preparation for stage D. Several rates are written per tick, not per
year. Find them and express them in years so that at `DT = 5` the values are
the same as now:

- truces (`self.tick + 6`), the plague gap (`self.tick + 10`), war ending
  (`WAR_END0 + 0.03 x ticks`), `WAR_COST`, the siege toll (3% per siege),
  cohesion loss per failed siege, `FISC_EMA`, tie decay (`x 0.9` per
  tick), `sea_adjacency` every 4 ticks, the 0.5 cap on war probability,
  `SUPPLY_GRACE`, and any other bare per-tick number (grep for literals in
  `wars_step`, `diplomacy`, `rebellions`, `trade_ties`, `disasters`).

List what you found in the handoff, including any you chose to leave.

## Stage D: a yearly political step (switch `pol_step`)

1. Inside each 5-year tick, run war, diplomacy and rebellion `DT / DT_POL`
   times (`DT_POL` C: 1 year), reading polity statistics computed once per
   tick. Land, growth, migration, technology and culture stay at 5 years.
2. Deaths and captures apply as they happen; `territory` and
   `polity_stats` are refreshed after a sub-step only when a city changed
   hands in it.
3. Cost: `wars_step` is about 5-12% of step time at one call per tick, so
   five calls could add 25-50% without WP1 stage D's caches. Measure.

Expected: war durations spread over years; campaigns of several sieges;
the share of states at war rises. If wars still end inside a year, the
cause is in the ending rule or the one-city defenders, not the clock.

## Stage E: armies as a stock (switch `army`)

1. Each state has a field army: a share of its strength it has raised.
   Raising takes time (`ARMY_RAISE`, years) and removes those people from
   their cells; standing costs food (through the ledger of WP4);
   demobilising returns the survivors.
2. Sieges and battles consume the army, not a flat share of the whole
   population. A side whose army is spent cannot besiege; it sues for
   terms or the war lapses. This replaces `WAR_COST`.
3. Projected strength at a target is the army's, with the existing decay
   over distance.
4. Exhaustion: the chance of ending rises with cumulative losses over the
   state's population, not with ticks elapsed.

Keep it to these four points. No units, no generals, no battles on the
map.

## Stage F: polities without cities (needs U: D8; switch `camps`)

For tribes, confederations and herder states. Almost every routine
iterates `P["cities"]` and assumes the capital is one of them
(`deter` takes the nearest of the defender's cities; an empty set
crashes it). The least invasive form:

1. A **camp** is a record in `self.cities` with `kind = "camp"`: no urban
   population, exempt from `urban_city` abandonment and from city-level
   culture, and able to move (to the densest cell of its people within
   reach, every `CAMP_MOVE` years).
2. A stateless region of one lineage forms a camp-seated polity when its
   people's cohesion and numbers pass a threshold, with a hierarchy
   bonus. Its reach comes from cohesion and herding (mounted peoples
   reach far), not administration.
3. Camps can be raided, defeated and made tributary, but not besieged and
   annexed as cities are: a won "siege" scatters the polity or makes it a
   vassal.
4. A camp polity that takes or founds a city becomes an ordinary state
   with that city as capital.
5. Everything that counts cities for a threshold (`nc >= 3` for
   succession, provinces at 4+, steel at 6 cities) must ignore camps;
   audit every `len(P["cities"])`.

This is the largest stage. Write a one-page design note first, covering
those five points against the code, and get it confirmed.

Expected: the 68% of land outside any state shrinks; herders get a path to
large states (the 2026-11-06 item D); raids between polities become wars.
Risk: thousands of short-lived camp polities. If so, raise the formation
threshold rather than adding a rule.

## Not in this package

- Persistent borders or claims. Decide after stage A.5 shows how much
  fragmentation is real.
- Changing what motivates war (the `g[...]` terms).
- Anything about culture. If a stage shifts trait means, report it; do
  not compensate.
