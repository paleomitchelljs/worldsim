# Structural mechanics (draft, 2026-10-29)

Ten additions from Claude's structural review, drafted at the user's
request. The mechanisms and every number are **C**; none has been tuned.
Constants are in the `structural mechanics` block at the top of
`../worldsim.py`.

Each mechanic is a switch. `--off NAME,...` turns some off, and `--off all`
gives back the earlier model draw for draw ([running.md](running.md)).

| Switch | Item | What it adds |
|---|---|---|
| `costs` | 1 | a cost for cohesion, statecraft, violence and expansion |
| `fiscal` | 2 | strength and reach follow the fed population |
| `unrest` | 2 | elites, political stress, and revolts driven by crowding |
| `succession` | 2 | disputed successions |
| `vassals` | 3 | submission, tribute, defection, annexation |
| `balance` | 3 | alliances against a common strong neighbour |
| `pastoral` | 4 | herding as a way of life; a stand-in for steppe |
| `land` | 5 | land condition that farming wears down |
| `climate` | 5 | structured climate: quasi-cycles, abrupt dry spells, moving biome edges, river discharge and course changes, famine migration; replaces the random droughts ([climate section](#climate-climate)) |
| `supply` | 6 | metal use needs ore supply; idle skills decay |
| `minority` | 7 | one minority people per cell |
| `acculturation` | 8 | cultural traits spread between lineages, across peoples too |
| `immunity` | 9 | plague with a host people and immunity per cell |
| `diagnostics` | 10 | `price.csv` and `checks.txt` ([diagnostics.md](diagnostics.md)) |
| `roads` | later | states build roads that cut travel cost ([roads](#roads-roads)) |
| `improvements` | later | field works, terraces and canals, built up and wrecked ([improvements](#improvements-improvements)) |
| `clearing` | on (2026-11-20, U) | farmers and herders clear forest, which farms and herds as grassland; unused clearings grow back ([land clearing](#land-clearing-clearing)) |
| `clear_terrain` | on (2026-11-20, U; untested until the screen ends) | cleared forest is crossed and defended as open country ([cleared land as terrain](#cleared-land-as-terrain-clear_terrain)) |
| `fire` | on (2026-11-20, U; untested until the screen ends) | foragers keep part of temperate forest burnt open, which forages better ([burning by foragers](#burning-by-foragers-fire)) |
| `separation` | later | separation becomes preferred spacing; its hostile effects move to low tolerance ([separation](#separation-as-spacing-separation)) |
| `hierarchy` | later | a hierarchy trait: elite growth, extraction, levies ([traits/cultural.md](traits/cultural.md)) |
| `patience` | later | a patience trait: building, granaries, land care ([traits/cultural.md](traits/cultural.md)) |
| `conformity` | later | a conformity trait: fidelity of transmission ([traits/cultural.md](traits/cultural.md)) |
| `proselytism` | later | a proselytism trait: pushing customs and identity on others ([traits/cultural.md](traits/cultural.md)) |
| `dragons` | later | large predators holding territories; slain, driven off or allied as people grow dense ([dragons](#dragons-dragons)) |
| `dispersal` | later | seafaring merges into expansion; sailing is a route for dispersal ([dispersal](#dispersal-and-fishing-dispersal-fishing)) |
| `fishing` | later | rivers, lakes and coasts feed more people; a fishing technology raises the bonus ([dispersal](#dispersal-and-fishing-dispersal-fishing)) |
| `dominance` | later | a dominance trait: the wish to rule others; war motive, sparing and keeping the conquered ([traits/cultural.md](traits/cultural.md)) |
| `ore_trade` | later | copper and tin reach every state joined by trade ties ≥ 0.3 to a state holding a worked deposit (U, 2026-10-29; threshold C) |
| `food_units` | later | founding groups, the dragon finding constant, prestige, the invention size factor, the plague trigger, city sizes and Price weights in food-equivalents |
| `shuffle` | later | war declarations checked in random order of pairs and sides |
| `dynasty` | later | the age in cohesion decay runs from the current dynasty |
| `logistics` | later | administration × statecraft sets sieges per tick, campaign length and projection range |
| `domestication` | later | crop and animal packages from hearths, developed nearby and borrowed elsewhere |
| `craft` | later | a craft technology from a craftsmanship trait |
| `resources` | later | unique resource sites held by states |
| `guarded` | later | guarded techniques, leaking slowly, taken by conquest |
| `trade_assets` | later | more trade, and goods carrying trade past intolerance |
| `war_motive` | later | wars without motive rarer; wars for resources, rule or land |
| `salinity` | later | salt on irrigated land |
| `war_goals` | later | motivated wars have a goal city; cession; wars end once it is taken |
| `scale` | later | invention faster in large, connected, varied realms |
| `development` | later | general gains of technology (building, engineering, canals, ports) |
| `density_cap` | later | a hard cap per cell in food-equivalents |
| `experience` | later | trade, war and hardship shape traits |
| `mission` | later | mixing driven one way by proselytism and gated by similarity; churn breeds unrest; faith wars |
| `dragon_hosts` | later | Goblins and Frogloks never ward off dragons |
| `land_pressure` | later | crowding without room becomes a war motive, sooner for domineering peoples; strong neighbours of the weak are drawn to attack |
| `war_v2` | later | one war rule: deterrence × named motives (land, prey, rule, resource, enmity, faith, irredentism); a small causeless baseline; war costs people |
| `ruler_traits` | later | rulers draw violence, dominance, expansion and statecraft from a fat-tailed distribution; dynasties; the state follows its ruler, the people follow or revolt; needs `rulers` |
| `turmoil` | later | lost cities, raids and revolts wear down administration |
| `revolt_viol` | later | provincial revolt × (0.5 + violence) |
| `road_tech` | later | road engineering as a technology; road quality from engineering and (a little) administration |
| `fortress` | later | attackers of a fortress people (Dwarves) lose extra people in raids and sieges |

## 1. Trait costs (`costs`)

Before this draft, cohesion, statecraft and innovation had no downside.

| Trait | Cost |
|---|---|
| cohesion | Technology borrowing x (1 − 0.5 x cohesion). Closed societies take less from outsiders. |
| statecraft | Political stress x (1 + 2 x statecraft x hunger), where hunger = 1 − fed. Extraction bites in bad years. |
| violence | Chance of a succession crisis x (0.5 + violence). |
| expansion | Raid damage on thinly settled cells x (1 + 0.8 x expansion x thinness), where thinness = clip(1 − 2 pop/K). |

Innovation, seafaring, trade, separation and tolerance get no new cost.
Trade already carries plague exposure.

## 2. Fiscal health, unrest, succession

**Fed share (`fiscal`).**
- **Fed share:** `fed` = Σ min(pop, K) / Σ pop over a state's cells, smoothed
  (weight 0.2 per 5 years). At equilibrium it is about 1. It falls after a
  drought, a dry phase or land decline leaves people above K.
- **Strength:** x (0.4 + 0.6 x fed).
- **Reach:** x (0.6 + 0.4 x fed).

**Elites and stress (`unrest`).** This is a reduced structural-demographic
model (Goldstone; Turchin's secular cycles).
- **Crowding:** the population-weighted mean of pop/K, smoothed.
- **Elite load `e`** (starts at 1, range 0.3–4) changes by
  0.004 x e x (crowding − 0.75) / 0.25 per year. Crowded land means cheap
  labour and high rents, so elites multiply.
- **Stress:** max(0, crowding² x e − 0.6) x the statecraft cost x
  (1 + 4 x hunger).
- **Effect on revolt:** the revolt hazard ([rules/states.md](rules/states.md))
  is multiplied by (1 + 3 x stress).
- **Feedback:** each revolt cuts `e` by 20%.

**Succession (`succession`).**
- **When:** states of 1 or more cities (SUCC_MIN_CITIES; 3 until
  2026-11-18, U) draw reign lengths (exponential, mean 25 years).
- **Crisis chance** at each succession: 0.12 x (1.3 − 0.6 x statecraft),
  times (0.5 + violence) when `costs` is on.
- **A crisis:** cohesion x 0.8, elites x 0.85.
- **Civil war:** with probability 0.3 + 0.3 x stress (at most 0.9), the
  largest provincial city revolts under a pretender.
- **Logged** as `succession`.

## 3. Vassals and balancing

**Vassals (`vassals`).**
- **Submission.** In a siege, if the attacker's projected strength is more
  than 3x the defender's (after terrain and allies), the defender submits
  with probability 0.5 x (1.2 − its cohesion). The war ends and a 30-year
  truce follows.
- **Tribute.** 25% of a vassal's strength moves to its lord each tick.
- **Defence.** The lord defends the vassal at 0.5 of its projected strength.
  Vassals send 0.35 to a lord under attack. A lord and its vassal never
  fight or ally.
- **Defection** per year: 0.01 x min(2, 2 x vassal/lord strength) x
  (1.5 − lord cohesion), x 1.5 if they are of different peoples.
- **Annexation.** A kin vassal of 3 or fewer cities, after 50 years, is
  annexed at 0.004 x (0.5 + lord statecraft) per year.
- **Logged** as `vassal`.

**Balancing (`balance`).**
- **Threat.** For two neighbouring states, threat = min(1, (S_c / (S_a +
  S_b) − 1) / 2) for the strongest neighbour c they share. It is 0 until c
  outweighs both together and reaches 1 at three times.
- **Effect.** Alliance chance gains DT x 0.005 x 4 x threat x the trade-level
  tolerance gate. That gate is looser than the alliance gate, so the threat
  overrides cultural distance. Alliances under threat break less often
  (x (1 − threat)).

## 4. Pastoralism (`pastoral`)

- **Herding density** (people/km²): grassland 0.45, temperate forest 0.12,
  desert 0.08, tundra 0.06, jungle 0.02.
  - It is cut above 2.5 km elevation.
  - It is raised by up to 50% on steppe.
- **When herding is available.** It ramps in as farming goes from 0.35 to
  0.75, through domestic animals. Herding K blends forage and herd density
  by that ramp.
- **Each cell takes the better of farming and herding.** A cell whose
  herding K beats its farming K, once herding is available, is a herding
  cell.
- **Effects of herding cells:**
  - war and raid worth x 1.6 (mounted);
  - raid frequency x 1.5;
  - they count as 0.3 of their population toward founding a city;
  - a state's reach x (1 + 0.5 x its herding share);
  - a border between herding and farming cells counts as a frontier for
    cohesion (Turchin's metaethnic frontier).
- **Steppe stand-in.** The world file has one runoff value per biome, so
  aridity inside a biome isn't available.
  - Steppe = grassland or desert 400–1,600 km from the coast, ramping 0 to 1.
  - Rain-fed farming there falls to 35%; irrigation is untouched.
  - This is a rough stand-in. Replacing it with a real moisture field is
    an open data question.
- **Side effect.** Even at low farming, a cell never does worse than pure
  foraging (herding K with no herding is just forage). That loosens the
  early farming penalty in poor-soil land.

## 5. Land and climate

**Land condition (`land`).**
- **Range:** a value per cell, 0.3–1, that multiplies farm density.
- **Intensity** = farming level x min(1, pop / farming K), on farming cells.
- **Decline:** 0.0003 x intensity x (1 + 3 x irrigated share) x condition
  per year. Irrigated land salinizes.
- **Recovery:** 0.004 x (1 − condition) per year (fallow, flushing).
- **Equilibrium:** each cell settles at 0.004 / (0.004 + 0.0003 x intensity
  x (1 + 3 x irrigated)). That is about 0.93 for fully used rain-fed land
  and 0.77 for fully irrigated land. The approach takes centuries, and the
  level moves with how hard the land is used.
- **Earlier form, dropped.** The first draft gated recovery by
  (1 − intensity). Settled cells sit near K, so land only ever declined
  (mean 1.0 → 0.46 over 6,000 years, runs `structural_seed91`/`92` v1), and
  world population fell to a third of the baseline.

**Climate (`climate`).** Rewritten 2026-10-29 (U: "realistic periodicity
and amplitude", replacing the ad hoc droughts); form and numbers **C**. See
[Climate](#climate-climate) below.

## 6. Supply and loss of technology (`supply`)

- **Known vs in use.** Each lineage keeps which metal stages it knows; that
  is never lost.
- **In use** needs the current supply:
  - bronze needs copper and tin in hand or through a close contact;
  - iron needs iron ore and knowing bronze, not current tin;
  - steel needs iron in use and 6 cities.
- **Grace period.** A stage goes out of use after 4 ticks (20 years)
  without supply, and comes back as soon as supply does. Cutting the trade
  that brings tin can end a lineage's bronze age.
- **Logged** for lineages over 300k people.
- **Decay outside states.** Administration decays at up to 0.002 per year
  and metallurgy at 0.0004 per year, scaled by the share of the lineage's
  population living outside any state.
  - *Earlier form, dropped:* scaled by 1 − min(1, cities/3). A lineage with
    one city lost metallurgy nearly as fast as it invented it. Bronze came
    2,000–3,000 years late, and iron never came (runs v1).
- **Fusion** takes the union of known stages.

## 7. Minorities (`minority`)

- **What.** A cell can hold one minority: another people with its own
  lineage.
- **Food and growth.** It eats from the same K, which lowers the majority's.
  It grows logistically toward 0.2 of its own K in the cell.
- **Sources:**
  - **Garrison.** A conqueror leaves 4% of the captured city (in food terms)
    of its own people.
  - **Merchant quarter.** With a cross-people trade tie over 0.5, each side
    may plant 3% x tie of the other's capital each tick (chance
    0.01 x tie per year).
  - **Underclass.** When raiders take over a cell, half of the remaining
    defenders stay on.
- **Expulsion.** A state's ruler expels foreign minorities at
  0.01 x separation x (1 − tolerance) per cell per year.
- **Promotion.** A minority that outgrows the majority (in food terms)
  becomes the majority. A city carries on under its new people instead of
  ending. Logged as `minority`.
- **Merger.** A minority of the majority's own people merges into it.
- **Effects:**
  - minorities count in a state's strength (as foreign subjects unless
    they share the ruler's people);
  - they suffer raids, sieges and plague;
  - they are a strong technology and culture contact with their hosts.

## 8. Acculturation (`acculturation`)

- **What moves.** Cultural traits, across peoples too. Intrinsic traits
  never move.
- **Target.** Each lineage moves toward the contact-weighted mean of its
  contacts' traits. The weight is contact strength (borders, rule, trade
  x 30, minorities) x the square root of the contact's population
  (prestige).
- **Rate** per year: 0.001 x openness x min(1, total contact) x
  (1.5 − conformity). Openness is tolerance, plus 0.5 x the contacts'
  proselytism.
  - The base was 0.004 until 2026-10-29. It pulled every people toward a
    common value of about 0.3 for innovation and tolerance (see
    [open-questions.md](open-questions.md)). U: slower in general.
- **Foreign rule (U, 2026-10-29; C numbers).** A lineage living under a
  ruler of another people moves toward the ruling lineage's traits at
  0.01 x (share of the lineage so ruled) x (1.5 − conformity) per year:
  fast when conquered.
- **Skill dispositions fall slowly (U, 2026-10-29; C number).**
  Innovation, seafaring and statecraft can be pulled down by contact or
  rule, but at 0.25 x the rate they are pulled up. (A first version
  that same day let them only rise; U: skills should be able to go down,
  treated differently.) These are cultural dispositions. Technology
  levels (knowledge) are a separate layer: they spread only upward by
  borrowing and fall only through disuse (idle decay of administration
  and metallurgy outside states, and loss of metal stages without ore,
  both under `supply`).
- The previous form is archived as `archive/worldsim_2026-10-29_acc_fast.py`.
- **Effect on similarity.** Neighbours drift together, which raises their
  similarity and so trade and alliance.

## 9. Plague with hosts and immunity (`immunity`)

- **Host.** A plague's host is the people of the city where it starts.
- **Spread.** States of another people catch it at 0.7 x the usual chance.
- **Deaths.** Cells of other peoples suffer 0.3 x the deaths.
- **Immunity per cell:**
  - set to 0.8 after a plague;
  - decays at 1.2% per year;
  - held at 0.5 or more in cities over 5x the founding threshold
    (endemic).
- **Mortality** x (1 − 0.8 x immunity), so first contact is the worst case.
- **Logged** with the host people.

## Not done

- **Mixing pastoral and cell modes.** A cell is all herding or all farming.
- **Elites and revenue as a separate state budget.** `fed` stands in for
  revenue.
- **War aims and negotiated peace** other than submission.
- **Cultural transmission that favours the conqueror** beyond rule contact.

## Climate (`climate`)

It replaces both the random droughts and the first draft's red noise.
Climate draws from its own random stream, so a seed has the same climate
(and the same river history) whatever else is on. From 2026-11-07 it is
also drawn for 20,000 years (CLIM_YEARS) whatever the run's length, so a
shorter run has the climate of the start of a longer one (C; before,
the draws depended on --years).

**Moisture anomaly** `m` per cell, sd about 1, built from:
- **Fixed patterns:** world-wide, a latitude pattern (cos 4 x latitude),
  distance inland, and 4 smooth random regional fields (Gaussian, sigma 20
  cells, about 1,100 km). Weights 0.35 / 0.25 / 0.25 / 0.35 each,
  normalized.
- **A time series for each pattern**, precomputed for the run. It mixes
  broad spectral peaks, not strict cycles (variance shares):

  | Part | Form | Share | Real-world analogue |
  |---|---|---|---|
  | interannual–decadal | white at 5-year steps | 0.30 | ENSO-like (5-year means) |
  | multidecadal | damped oscillator, period 60, damping 60 years | 0.15 | Pacific and Atlantic oscillation analogues |
  | centennial | period 200, damping 250 | 0.20 | solar-linked (about 200 years) |
  | millennial | period 1,500, damping 1,500 | 0.20 | Bond-like (periodicity contested) |
  | background | red noise, 400 years | 0.15 | — |

- **A local field drawn fresh each tick** (sigma 6 cells, about 330 km;
  weight 0.45). This is the old drought's role. `CLIM_LOCAL_COARSE` > 1
  draws it on a coarser grid (every k-th row and column, the same sigma
  in km) and interpolates bilinearly to the land cells, for speed (WP1
  stage D, C). The default is 1, the full grid (U, 2026-11-17): five
  seeds with 2 ended with fewer people (open-questions.md).
- **Abrupt dry spells.** About one per 2,000 years: 150–400 years long,
  1.5–2.5 sd deep, setting in over 25 years and lifting over 75. A quarter
  are world-wide; the rest have a regional footprint. Modelled on the 8.2,
  4.2 and 3.2 thousand-year events.

A smoke run (seed 91, 2,500 years) put the population-weighted world
anomaly's variance at 18% in 5–20-year periods, 34% at 20–100, 25% at
100–400 and 23% at 400–3,000.

**Effects of the anomaly:**
- **Precipitation:** fractional anomaly = (0.10 + 0.12 x dryness) x m,
  clipped ±0.7. Dryness = 1 − runoff/0.5, clipped 0–1; deserts are most
  variable.
- **Rain-fed yield:** x (1 + (1 + dryness) x anomaly), clipped 0.1–1.6.
  Semi-arid yields respond more than proportionally.
- **Foraging and herding:** x (1 + 0.8 (1 + dryness) x anomaly), clipped
  0.2–1.5.
- **River discharge.** Each cell's runoff changes by 1.5 x its anomaly,
  and discharge is summed over the whole catchment upstream. Irrigation
  scales with sqrt(discharge / normal), clipped 0.2–2. A dry upstream
  starves a wet delta.
- **Biome edges.** Beyond 0.5 sd, a cell blends toward the drier (or
  wetter) neighbouring biome. The blend is 0.35 per sd beyond 0.5, at most
  0.7, times closeness to that biome (1 next door, e-folding over 2 cells).
  The blend applies to farm, forage and herd densities and to each people's
  biome fit. Pairs:
  - drier: jungle or temperate forest → grassland, grassland → desert;
  - wetter: desert → grassland, grassland → the nearer of temperate forest
    or jungle.
- **Granaries.** Inside a state, cells feel the climate smoothed over
  15 x administration years. Granaries buffer bad decades, not bad
  centuries.
- **Famine migration.** Cells holding more than 1.05 x K send half the
  excess to the cell with most room among 16 random cells within 8 cells.
  Only empty land or the same lineage's land counts. At most 600 source
  cells per tick. The rest die back as the land allows.
- **Hunger and conflict.** War declarations x (1 + 2 x (1 − fed));
  raids x (1 + 1.5 x the raider's excess over K).
- **Logged:** dry spells starting and lifting (`climate`), and a great
  drought (`drought`) when over 30% of people (and over 1M) are below
  −1.5 sd, at least 200 years after the last one logged (U 2026-11-01:
  about 10 per run; was 8% below −2 sd, 50 years apart, 42-65 per run).

**Rivers change course (avulsion).** River cells on alluvial fill, below
0.3 km relief and elevation, carrying over 1,000 m³/s, are prone (119
cells in 29 basins on this map).
- **Chance:** each prone cell breaks per year with chance 2.5e-4 x
  (discharge / normal)², clipped 0.3–3. Floods do it.
- **New course:** a neighbour no more than 0.03 km higher that does not
  drain back through the cell, weighted toward the lowest, or straight to
  the sea from a coastal cell.
- **Recomputed afterwards:** discharge, river cells (over 300 m³/s and
  30,000 km² of catchment, as the world build defines them), basins,
  irrigation, the river foraging bonus, city locus and travel costs.
- **Cities left dry** get a `river lost` shock, and the change is logged.
- **Rate:** about 75 course changes in 2,500 years of the smoke run (about
  190 per run). Historical rates differ a lot: the Yellow River shifted
  far more often, Mississippi delta lobes switch about every 1,000–1,500
  years. The rate is **C**.

## Roads (`roads`)

- **Building.** Every 50 years, each state with 2+ cities builds along the
  cheapest routes (Dijkstra on the travel graph, within 1.5 x reach) from
  its capital to each city. Each cell on a route gains 0.6 x the ruler's
  administration x (1 − stock).
- **Effect.** Travel cost x (1 − 0.5 x stock). That feeds territory, reach,
  movement and budding, so settlement funnels along routes.
- **Decay.** Stock decays with a 1,500-year life inside a state and 300
  years outside.
- **Rebuild.** The travel graph is rebuilt after each round (and after each
  river change).

## Improvements (`improvements`)

- **What:** field works, terraces and canals: 0–1 per cell. Clearing
  the forest itself is `clearing` (below); until 2026-11-20 this stock
  stood for cleared fields too.
- **Building:** 0.003 x use x (0.5 + the ruler's administration) x (1 −
  stock) per year. Use = farming level x min(1, pop/farm K), on farming
  cells.
- **Decay:** 1/400 x (1 − use) x stock per year, so works fall in when
  unused.
  `[upkeep]` (WP6 C, 2026-11-18, **C**): plus 0.1 x shortfall x stock,
  shortfall = (0.7 x pmem − pop) / (0.7 x pmem) clipped to 0–1 (0 on
  herding cells), pmem the cell's people averaged over about 50 years
  (`Sim.pmem`): works are sized to the hands that kept them.
- **Effects:**
  - irrigation reaches 40% of its potential without canals and all of it
    with them;
  - rain-fed farming gains up to 30%;
  - settlers prefer improved land (colonizability x up to 3, at most 1).
- **Damage:**
  - a sack wrecks 0.6 x violence of the city cell's works and half that
    across its hinterland;
  - a clearance halves the hinterland's;
  - raids take 0.3 x the population loss.
- **Side effect:** early irrigation now reaches less than before, because
  canals must be built.

## Land clearing (`clearing`)

U (2026-11-20): "do we have a capacity for people to change their
biomes? Eg, can humans clear forest to make grass/farm land?" Form and
numbers **C**.

- **What:** the cleared share of a jungle or temperate-forest cell, 0–1
  (`Sim.clear`). The climate's biome does not change; clearing is land
  use on top of it.
- **Effect:** the cleared share farms, forages and herds at grassland's
  values. Rain-fed farming, forage and herd capacity are each multiplied
  by 1 + clear × (grassland's value / the biome's − 1), the blend the
  climate's ecotones use. At full clearing:
  - jungle farms × 2.2, forages × 0.6 and herds × 22.5 (from 0.02);
  - temperate forest farms × 1.33, forages × 0.83 and herds × 3.75.
  The people's fitness stays that of the climate's biome. Cleared forest
  has no grassland sod to break.
- **Clearing:** each cell moves toward a target at CLEAR_RATE 0.01 per
  year of the gap, about a century; medieval assarting cleared lowland
  Europe over about three.
  - On a farming cell the target is the share of the land in use: farming
    level × pop / farming capacity (the improvements' `use`).
  - On a herding cell it is CLEAR_HERD 0.5 × pop / herding capacity
    (burning for pasture).
- **Regrowth:** above the target, a clearing grows back at
  CLEAR_REGROW 1/150 per year. An emptied cell's target is 0. Secondary
  forest closes its canopy in decades to a century or two.
- **Not modelled:** clearing's effect on the climate (albedo, rain
  recycling) and on erosion. Movement and defence are
  `clear_terrain`, and foragers' burning is `fire` (both below). Wars
  touch clearing only through the people they kill: raids and ravaging
  already wreck field works, and emptied land grows back.
- **Records:** `cleared_km2` in `timeseries.csv`; `clear` in
  `final_state.npz`.
- **Test** (`wp8j_sanity_seed101`, 3,000 years; with `--off clearing`
  the run is identical to `wp8i_seed101`).
  - 5.6M km² is cleared by year 3,000: 11% of jungle and of temperate
    forest, most in the long-settled cores.
  - Population is 13-26% above `wp8i` at years 1,000-3,000.

## Cleared land as terrain (`clear_terrain`)

U (2026-11-20): "prepare the extensions" (the clearing items not yet
modelled). Form and numbers **C**.

- **What:** cleared forest is crossed and held like open country.
- **When:** every ROAD_EVERY (50) years, before roads, in cells whose
  cleared share has moved by CLEAR_TERRAIN_STEP (0.05) or more since it
  was last applied. The step keeps the travel graph's cached distances
  valid outside the cells that changed.
- **Travel cost:** the biome's MOVE is × (1 + clear × (grassland's MOVE /
  the biome's − 1)). At full clearing, jungle is × 0.59 and temperate
  forest × 0.8. Relief, rivers and roads keep their own factors.
- **Terrain defence:** TERRAIN_DEF is blended the same way. At full
  clearing, jungle is × 0.59 and temperate forest × 0.91. Relief and
  wetland keep theirs. Raids, ravaging and sieges read it as before.
- **State:** `Sim.clear_at` holds the share last applied, and the
  world's `move_x` and `defence0` (the defence before clearing) are kept
  with the world. A state saved before this starts from the uncleared
  terrain.
- **Not modelled:** forest cleared along roads (the road stock is its own
  multiplier).

## Burning by foragers (`fire`)

U (2026-11-20): "prepare the extensions". Form and numbers **C**.

- **What:** foragers in temperate forest keep a share of it burnt open:
  a mosaic of regrowth and edge (`Sim.burn`, 0–1). Examples are
  Australian fire-stick farming and the Holocene burning of Europe's and
  North America's woodlands.
- **Jungle is left out.** Closed rainforest carries little fire.
- **Target:** BURN_MAX 0.3 × (1 − farming level) × clip(pop / farming K,
  0, 1) on non-herding cells, 0 elsewhere.
- **Rates:** the share rises at BURN_RATE 0.1 per year of the gap, and
  grows back at BURN_REGROW 1/20 per year above the target.
- **Effect:** the burnt share of the uncleared forest forages × (1 +
  BURN_GAIN 0.25). Hunting returns run higher on recently burnt ground
  (Bliege Bird et al. 2008, *PNAS*). With `clearing` the factor is 1 +
  0.25 × burn × (1 − clear).
- **Farmers take over burnt land.** Their cleared share is first raised
  to the burnt share, up to their own target, so farming starts from
  what foragers kept open.
- **Not modelled:**
  - the burnt mosaic's effect on travel and defence (it stays forest);
  - fires that escape;
  - burning of grassland, which is open already.
- **Records:** `burnt_km2` in `timeseries.csv`; `burn` in
  `final_state.npz`.

## Separation as spacing (`separation`)

U: a high-separation people may be tolerant (in contact with others,
overlapping them, trading freely) and still live at low density. C: the
form and numbers.

- **Preferred density.** A lineage fills a cell only to
  `1 − 0.8 x separation²` of its capacity. City cells are exempt: once a
  city stands, it fills. Past that share the lineage moves on or buds off
  as if the cell were full: drift within the lineage, budding, pioneers
  and voyages all use the pressure against the preferred density.
- **Roster values under the new meaning** (`peoples_headstart`, kept as
  set before):

  | People | Separation | Share of capacity filled |
  |---|---|---|
  | Giants | 0.85 | 0.42 |
  | Trolls | 0.80 | 0.49 |
  | Ogres | 0.75 | 0.55 |
  | Snake folk | 0.70 | 0.61 |
  | Dwarves | 0.65 | 0.66 |
  | Humans | 0.35 | 0.90 |
  | Elves | 0.30 | 0.93 |

  The values were set under the old meaning and may need resetting
  ([open-questions.md](open-questions.md)).
- **Hostility moves to tolerance.** Each of these used separation and now
  uses (1 − tolerance) in its place:
  - avoiding foreign neighbours when moving and budding;
  - raid frequency, x (1 + ·);
  - war on foreigners, x (1 + 1.5 ·);
  - clearance, ∝ · x violence x (1 − tolerance);
  - expulsion of minorities, ∝ · x (1 − tolerance).
- **Cost.** Fewer people per cell means less strength, and with `dragons`
  more time at the group sizes dragons hunt.

## Dragons (`dragons`)

The user's design (U): dragons are large predators holding territories.
Their attacks depend on group size:
- dense settlements are left alone;
- very small groups are attacked but seldom found;
- bands, tribes and towns in between are hunted routinely.

The group size that wards off a dragon depends on strength, technology and
resources. Overlapping territories raise deaths sharply. Where people grow
dense, dragons are slain, driven out, or taken as allies, but only by very
tolerant societies. Allies:
- lower local deaths;
- help administration;
- raise a state's chances in war.

Dragons start abundant, breed slowly, and live up to 3,000 years. The
functional forms and every number below are Claude's (C) unless marked.

- **Territory.** The cells within 80 km of the dragon's home (about 20,000
  km²; 9 cells at the equator). Wild dragons' homes stay 110 km apart, so
  territories overlap and most covered cells have one or two dragons (C).
- **Start.** A random packing of homes 110 km apart, 50% of them held
  (80% until the change below): about 3,500 dragons (C; U: "quite
  abundant", then "high, not overpowering").
- **Hunting: a cut in the growth rate (U, second form, 2026-10-29).**
  Dragons lower the yearly growth rate of a cell's people by
  0.036 x hazard x g(n). The cut is the same for every people (U); only
  fast breeders stay above zero under a dragon (U).
  - **Hazard** is the summed hunting weight of the wild dragons covering
    the cell, about 1 for one ordinary dragon.
  - **The number (U→C):** 0.036 is set so that Frogloks and Goblins
    (r = 0.06) grow at the human rate (0.024) under one dragon. Everyone
    else's growth goes below zero, so their cells shrink.
  - **The frontier boost** to growth applies only while the cut leaves
    growth above zero.
  - **Minorities** take the same cut.
  - **People killed** are counted as the shortfall against growth without
    dragons.
  - **The first draft** was a separate death rate of 0.02 x g(n) per year
    per dragon (archived as `archive/worldsim_2026-10-29_dragon_kill.py`).

  In both forms, n is the cell's people, minority included:
  `g(n) = n / (n + 150) x 1 / (1 + (n / ward)^4)`
  - The first factor is the chance of being found: a band of 15 is found
    a tenth as often as a large group (C; U).
  - The second factor falls steeply once n passes the ward size (C; U).
- **Ward size.** `ward = 3000 / (body size x metal x organization)` heads
  (U: strength, technology, resources; C: numbers):
  - **body size** is the roster's combat worth per head;
  - **metal** is the military multiplier, 1 + bronze + iron + 1.5 steel;
  - **organization** is 1 + the ruler's administration inside a state, else
    1.

  So a stateless human cell needs 3,000 people; a bronze-using state with
  administration 0.5 needs 1,000. Giants (size 30) need 100 heads, Goblins
  (0.35) 8,600.
- **Confrontation.** Each warded cell in a wild dragon's territory brings a
  confrontation at 1% per year (C). The most populous warded cell decides
  the outcome and loses 2% of its people in the fight (C). In order:
  1. **Alliance** (U: only very tolerant societies). Needs a state and the
     lineage's tolerance at least 0.75 (C). The chance is (tolerance −
     0.75) / 0.25 (C). The dragon moves its home to that cell.
  2. **Slain**, with chance 0.3 + 0.5 x violence (C).
  3. **Driven out** to a free site, about 110–1,000 km away (C). If none is
     found in 12 tries, it is lost.
- **Allies** (C numbers):
  - **guard their territory:** wild-dragon hazard there is cut by 90%
    (U: lower local deaths);
  - **strengthen their state:** strength x (1 + 1.0 x √allied dragons)
    (U: much better odds in war), which also shapes war declarations and
    submissions;
  - **lengthen its reach:** x (1 + 0.3 x √allied dragons) (U: help
    administration).

  An allied dragon follows its state's capital if its home is lost. It
  goes wild if the state ends.
- **Life.**
  - **Lifespan:** at most 3,000 years (U); starting ages are uniform over
    0–3,000.
  - **Other deaths:** wild dragons also die at 1/10,000 per year (C).
  - **Breeding:** from age 300, each dragon has a 1/500 chance per year of
    an offspring (C; U: slow), which settles a free site, if one is found.
  - **Free site:** no other home within 110 km and no warded cell in
    reach.
- **Dragons vary (U; second draft, 2026-10-29), heritably (C).**
  - Each dragon has a tolerance and a violence, logit-normal around 0.4
    and 0.5 (sd 1.0 on the logit scale), and a strength, log-normal around
    1 (sd 0.3).
  - Young take after their parent, with drift 0.15 on the logit or log
    scale. Dragons can therefore evolve under slaying, alliance and
    driving-off.
  - **Hunting weight:** strength x (0.5 + violence) x (1.3 − 0.6 x
    tolerance). A cell's hazard is the sum of the weights of the wild
    dragons covering it.
  - **Ward size:** x the weighted mean strength of those dragons.
  - **Confrontation:** a cell counts against a dragon only once it passes
    that dragon's own ward size.
    - The fight costs the cell 2% x strength x (0.5 + violence) of its
      people.
    - The odds of slaying it are x (0.5 + violence) / strength: a violent
      dragon stands and fights, and a strong one survives.
  - **Alliance:** needs a state and the mean of the lineage's and the
    dragon's tolerance at least 0.75. The chance is (mean − 0.75) / 0.25.
    So a 0.6 Lizardfolk lineage can ally with a dragon of 0.9 or more.
  - **Ally boons:** these scale with √(summed strength of the state's
    allied dragons).
  - **Body size:** the ward size divides by body size^0.75, not body size.
    The ward is then the same in food-equivalents for every body size.
    In heads, Giants need about 230, Ogres 320, Trolls 530 and Goblins
    6,600, against Humans' 3,000. The first draft was linear (C, both).
  - **Outputs:** `dragons.csv` gains parent, tolerance, violence,
    strength and the allied people; the timeseries gains the wild
    dragons' mean `dragon_tol`, `dragon_viol` and `dragon_str`.
  - The first draft is kept as `archive/worldsim_2026-10-29_dragons_v1.py`.
- **Fewer dragons, slower breeding, and growing up (U, 2026-10-29; numbers
  C).**
  - **Start:** 50% of the packed sites held (was 80%), about 3,500
    dragons.
  - **Breeding:** 1/1,500 per adult per year (was 1/500), so people have
    time to grow in dragon-free land.
  - **Growing up:** a dragon's strength is its full strength x
    min(1, age / 300), at least 0.05. Strength sets its hunting weight,
    the ward size against it, the cell size that confronts it, and its
    odds of surviving a fight. A band of about 150 stateless humans can
    confront and almost surely kill a newly fledged dragon; at 300 years
    it is fully grown (U).
  - **Nesting:** a young dragon settles only where no cell in reach holds
    5% or more of its full-size ward size, about 150 stateless humans
    (U: very sparsely populated land).
  - The previous form is archived as
    `archive/worldsim_2026-10-29_dragons_v3.py`.
- **Own random stream** (seed 70,000 + seed), as with climate.
- **City ends:** a dragon loss over 5% in a tick counts as a blow when
  attributing a city's end ("dragon").
- **Outputs:**
  - `dragons.csv`: every dragon, with birth, first home, end, fate, ally
    and moves;
  - `final_state.npz` gains `dragon_home`, `dragon_ally` and `dragon_age`;
  - on the peoples panel of the maps, wild dragons are dark red dots and
    allied dragons gold;
  - `timeseries.csv` columns are listed in [diagnostics.md](diagnostics.md).
- **`--dragon-shun F`** (C, off by default): dragons do not breed into or
  move to sites where any cell in reach holds F x its ward size or more.
  This gives slow peoples refuges to grow in (see
  [open-questions.md](open-questions.md)).
- **`--dragon-penalty`** sets the 0.036 cut for sensitivity runs (it
  replaced `--dragon-kill`).

## Dispersal and fishing (`dispersal`, `fishing`)

**U, 2026-10-29:** seafaring should be dispersal, with sailing a
technology that allows one kind of dispersing; the merge with expansion
was agreed; waters are bountiful regardless, and a fishing technology
should raise the bonus. Forms and numbers are **C**. The earlier model is
archived as `archive/worldsim_2026-10-29_pre_dispersal.py`.

- **`dispersal`.**
  - Sea voyages run at 2.5 x expansion x (0.1 + sailing) x sqrt(coastal
    cells), not seafaring. Sailing still sets their range. River leaps
    already worked this way.
  - Sailing is invented at 0.0012 x fishing x (coastal share + 0.1) x
    (1 − sailing): boats come from fishing. Without `fishing`, innovation
    stands in for fishing. Every founding group starts at sailing 0.025.
  - Founders no longer avoid coasts for low seafaring.
  - Seafaring stays in the trait array but does nothing, and is left out
    of similarity.
- **`fishing`.**
  - A waterside score per cell, 0–1: the largest of coast x (0.5 + 0.5 x
    sea productivity), river 1, lake 1, and a smaller stream 0.5.
  - Carrying capacity (farming and herding) x (1 + (0.25 + 0.75 x
    fishing) x waterside). This replaces the old coastal bonus of x (1 +
    0.5 x seafaring) on coasts only. The fixed water terms in the land
    itself (coastal foraging, river foraging, the coastal fish yield) are
    unchanged.
  - Fishing is a technology, 0–1. It starts at 0.1. It is invented at
    0.001 x innovation x (waterside share + 0.05) x (1 − fishing), and
    borrowed at factor 0.002, like the other technologies. Daughters
    inherit it; fused states take the better. It is never lost.
  - The same bonus at fishing 0.1 enters homeland choice.
- **Roster.** Frogloks' expansion 0.65 → 0.35 (U: "adjust them down";
  number C). Lower expansion also means they fill a cell further before
  they bud off.

## Further changes (2026-10-29)

- **Ore trade (`ore_trade`; U: "tin moving is exactly what I want").**
  See the table above. Iron stays local. Threshold 0.3 is C.
- **All added traits mix (U: fix the gaps).** Hierarchy, patience,
  conformity, proselytism and dominance now move under acculturation and
  foreign rule like the other cultural traits, and enter `price.csv`.
  They are still left out of similarity.
- **Sailing from innovation (U; form C).** Under `dispersal` with
  `fishing`, sailing is invented at 0.0012 × innovation × (0.5 + fishing)
  × (coastal share + 0.1) × (1 − sailing).
- **Loss by disuse (`supply`; U: farming, fishing and sailing can be
  lost; forms and rates C).** Per year, 0.001 × share not using it ×
  (level − floor). Farming: people in herding cells or below 0.1 of K,
  floor 0.25. Fishing: 1 − waterside share, floor 0.1. Sailing: 1 −
  coastal share, floor 0.025.
- Previous version archived as `archive/worldsim_2026-10-29_pre_oretrade.py`.

### Review fixes and logistics (2026-10-29)

From an outside review (another Claude session), checked against the
code; U: "do the fix-nows".

- **`food_units` (C).** Founding groups were 400 heads, so Giants arrived
  with 28× the food-equivalents of Goblins; now 400 food-equivalents. The
  dragon's finding constant (150) was in heads beside a ward in
  food-equivalents; now 150 / food per head. Prestige (√pop) in
  acculturation, the invention size factor, the plague trigger, recorded
  city sizes and Price weights also move to food-equivalents.
- **Tolerance counted once (C).** With `separation` on, hostility is
  already 1 − tolerance, so the separate tolerance factors in raids (1 −
  0.5 tol), war (1 − 0.4 tol), clearance and expulsion (1 − tol) are
  dropped.
- **Seafaring left alone under `dispersal` (C):** not moved by
  acculturation, omitted from `price.csv`.
- **Territory search limit** follows the largest reach (allied dragons
  could exceed the old fixed 1,530 cost-km).
- **`shuffle` (C):** declarations had gone to the lower state id first.
- **"Worn land" label** threshold 0.75 → 0.6 (the irrigated equilibrium
  is about 0.70–0.77). Records only.
- **`dynasty` (U: "Sure on state age resets"; C: which events).** Age
  resets when the ruling lineage changes (dies out, or a fusion) or a
  succession is disputed. Not at revolts: revolts are frequent enough
  that age would stay near zero and the decay term would vanish.
- **`logistics` (U: "The size edge in war should be very large—but so
  should technology and, in particular, statecraft/administration.
  Logistics win wars, size wins battles."; forms and numbers C).**
  G = admin × (0.5 + statecraft). Sieges per war per tick 1 + floor(2G);
  war-end chance × (1 − 0.6 G / 1.5); projection range × (1 + G); a
  failed siege costs 0.02 × (1.5 − G / 1.5) of cohesion. Battle odds
  (size, metal) unchanged.
- **Culture (U):** roster values are starting points; culture is fully
  mutable and there is no pull back toward them.
- Previous version archived as `archive/worldsim_2026-10-29_pre_units.py`.

## Economy, growth and experience (2026-10-29/30)

Built in `worldsim_dev.py` while ens1 ran on `worldsim.py`, then swapped
in. Forms and numbers are **C** unless marked; final numbers come from the
tuning rounds in [run-log.md](run-log.md).

- **Domestication (U: "domestication should be a technology"; C: tied to
  hearths rather than a second farming level, because farming already
  stood for generic domestication).**
- **Craft (U: "the ability to create coveted items"; craftsmanship levels
  U: Elves, Dwarves very high; Humans, Lizardfolk, Snake folk average;
  Frogloks, Goblins low; Ogres, Trolls, Giants very low).**
- **Resources (U: "locality-limited materials ... intrinsic boost to
  trade"; placement fixed in `sites.json` with `--shuffle-sites`, C).**
- **Guarded techniques (U: "the silk worm problem").**
- **Trade (U: more trade overall; an asset bonus lets intolerant peoples
  trade raw for crafted goods).**
- **War (U: "making pointless wars rarer ... offsetting by more practical
  wars ... less warring but more rational").**
- **Salinity (U: land depletion "to a realistic level").**
- **War goals (U: yes to war goals; C: goal from the largest motive,
  cession by a weaker defender).**
- **Scale (U: "big realms get resources and develop faster"; C: pool of
  connected people, not area, after Kremer and Henrich).**
- **Development (U: "an extra effect of technological advancement ...
  architecture, engineering, canals, ports").**
- **Density cap (U: "a hard limit on how much a given cell can support";
  in food-equivalents, U confirmed; numbers C).**
- **Experience (U: trade raises tolerance; war lowers tolerance, raises
  violence, maybe hierarchy and administration; C added: war raises
  cohesion and conformity; plague and famine raise conformity and lower
  tolerance; long peace lowers violence; Price `experience` column).**
- `--set NAME=VALUE` overrides any numeric constant for a run.

## Experience revised, mission, dragon hosts (2026-10-30)

- **Experience both ways (U: "I like the proposals in (2)").** Every
  trait experience moves now has forces both ways: wealth and long peace
  loosen cohesion (after Ibn Khaldun) and hierarchy; trade and safety
  loosen conformity (after Gelfand); unused trade skill fades. Numbers C.
- **Conformity no longer slows experience (U: "(3) makes sense").** It
  still slows mixing and mutation.
- **Mission (U: "mixing towards similar cultures, with nearby-mixing low
  compared with trade/conquest ... an effect of proselytism and
  asymmetrical"; trade-offs U: "rate of cultural change should be
  positively correlated with internal unrest, and the size of cultural
  differences between neighboring cultures should be positively
  correlated with the chance of war"; C: proselytism partly offsets the
  similarity barrier; backlash and holy-war motives; churn counts mixing
  and foreign rule, not experience; numbers C).**
- **Dragon hosts (U: "goblins/frogloks can never repel dragons ... they
  may enter into alliances, they may not ... safe harbors for dragons").**
  Host alliance rate C.
- Previous version archived as `archive/worldsim_2026-10-30_pre_mission.py`.

## Land pressure and the second war form (2026-10-30)

- **Land pressure (U: "If your population is approaching the carrying
  capacity of your territory, this should cause you to either spread or
  collapse internally"; U: "Domineering culture should then emerge as how
  close to 'full' a territory needs to be before the land-pressure
  triggers a war"; U: a strength asymmetry "a function of a culture's
  domineering, the culture's 'fullness', and the differential in
  strength"; forms and numbers C).**
- **War audit and second form (U: "Truly pointless wars, wars with
  absolutely no cause, should be rare since a war is costly ... built
  around historically-valid war causes"; U approved the clean structure
  and dominance tilting resource-getting from trade toward conquest).**
  Bugs fixed: ores bought by trade no longer count as war booty;
  declarations weigh projected strength with allies, terrain and walls.
  Double counts removed: strength enters once (deterrence) plus the prey
  motive; cultural hostility is a named motive. Added: target land value,
  irredentism, a cost of war in people. Causes after Holsti (1991).
  First deterrence form (min(1, R)²) let through 30 wars in 4,000 years;
  replaced by twice the odds of taking the city.
- Churn weight on stress 30 → 10 (mis1: stress ~3 everywhere).
- Previous version archived as `archive/worldsim_2026-10-30_pre_war2.py`.

## Raids as experience (2026-10-30)

U: "Very much yes to raids counting as violence." A lineage's share of
people in cells that raided or were raided raises violence (0.01) and
lowers tolerance (0.005); C: the peace and trade pulls on violence
halved (0.0001, 0.000125). war2 showed war exposure averaging 2.6% of
the time and a violence balance point near 0.06. Starting violence left
as it was (C: the start only delays the balance point). U: population at
~84M food-equivalents is fine. Previous version archived as
`archive/worldsim_2026-10-30_pre_raidexp.py`.

## Raid order (2026-10-30)

raid1 (raids as experience at 0.01) took world violence to 0.68; raid2
tried 0.004. U preferred changing how often raids happen: "I like your 1
and 2 a lot" (states with administration suppress raids on their
borders; trade, alliance and truce between states damp raids across
them; numbers C); a lower base rate (3) only after assessing. Raid
experience back at 0.01. Raids per tick now counted (`n_raid`). Previous
version archived as `archive/worldsim_2026-10-30_pre_raidorder.py`.

## Peace and trade pulls on violence restored (2026-10-30)

raid3: state order cut raiding tenfold, but violence stayed ~0.57,
raised in the stateless first millennia and falling only slowly with the
halved pulls. U agreed to restore them (peace 0.0002, trade 0.00025).
`reg2` tests this with regional starts.

## Sod (2026-10-30)

U: "historical grasslands rarely produced extensive farming ... Cities &
farms had strong historical ties to rivers & coasts." Assessment (raid3,
year 6400): 73% of cities on a big river (9% of land), 25% coastal, 7%
on neither: the water tie works. But grassland was the best rain-fed
farmland (FARM 1.0) from the start and held 30% of people and 31% of
cities; herders 3–9% of people. Change: rain-fed grassland farming ×
0.35 before bronze, × 0.6 with bronze (U: keep a bronze step), full with
iron (numbers C). Previous version archived as
`archive/worldsim_2026-10-30_pre_sod.py`.

## Lizardfolk (2026-10-30)

reg1–reg3: Lizardfolk ~1% of food-equivalents. Their island is 51%
temperate forest, 30% grassland, 19% jungle; their early fit outside
jungle was 0.35 of their best; Frogloks, dragon hosts, made the island a
refuge for 150–290 dragons. U: raise Lizardfolk forest tolerance (0.8 →
1.1, C) and put Humans, Lizardfolk and Frogloks on both western islands.
U: the refuge "should be only where frogloks occupy": young and
driven-off dragons now settle only where every settled cell in reach is
of a host people or empty (C: the warding rule was already per cell; the
spread came from dragons settling next to thinly settled neighbours).

## Regional starts (2026-10-30)

U: "regionalize the starts for everyone except goblins and dragons (they
begin everywhere) ... they wander (mostly) on separate landmasses, with
some masses unpeopled except dragons/goblins. So only by inventing
seafaring do they merge." Roster keys `region` and `anywhere`;
`peoples_regional.py` ([scenarios.md](scenarios.md)).

## Lifespan (2026-10-30)

- **Lifespan** (U): a biological roster trait, a multiple of a human
  life, fixed per people. Humans 1.0; Goblins 0.43 (a 30-year-old goblin
  ~ a 70-year-old human); Frogloks 0.71 (50 ~ 70); Lizardfolk, Snake folk
  1.15; Ogres 0.9; Giants 1.5; Trolls 2.0; Dwarves 2.5; Elves 10. Numbers
  U→C (0.43 = 30/70, 0.71 = 50/70). Not yet used; planned for reign
  length with ruler tracking.

## Changes of 2026-11-01

- **Growth fix** (bug, C): logistic growth with a negative rate (dragon
  cut above r) now declines exponentially, capped at K, instead of
  running off from K. Ends the one-tick population spikes. Changes runs
  with `dragons` on; `--off all` unchanged.
- **Path dependence for all experience-driven traits** (`trait_path`, U
  chose this over a baseline pull, 2026-11-01): PATH_PIVOT 0.5 (tolerance
  0.2), PATH_PW 0.1, PATH_MIN 0.3 (C).
- **Devastation** (`devastation`, U): a siege lays waste a cell (capacity
  to 0, linear regrowth); WASTE_P 0.03 per siege (U, after tests at 0.01
  gave ~13 cells waste at a time), WASTE_YEARS 100 (C).
- **Slower mixing between peoples** (`acc_cross`, U: slow it, especially
  between neighbours; very low for 3-4 generations under foreign rule):
  contact acculturation between different peoples x ACC_CROSS 0.1 (C);
  rule acculturation x ACC_RULE0 0.05 rising to 1 around ACC_GENS 3.5
  generations of the same rule (C).
- **Unions of crowns cut** (U): UNION_CROWN 0.03 -> 0.01 (C number).
- **Superiority** (`superiority`, U: a trait for rejecting influence
  from unlike peoples; high across the board, Humans and Lizardfolk
  lower): pulls from other peoples x (1 - superiority); drifts, moves
  toward kin only; roster 0.75 / Hum, Liz 0.50 / Elf 0.90 (U→C).
- **What moves superiority** (`sup_exp`, U): winning wars against other
  peoples raises it, losing lowers it; trading with less advanced or
  less crafted peoples raises it. EXP_SUP_WAR 0.01, EXP_SUP_TRADE
  0.0005 (C); the slow fall EXP_SUP_CALM 0.00005 went with `causal_exp`
  (removed from the code 2026-11-17). Between peoples only; within a
  people, conformity does that work (U).
- **No causeless change** (`causal_exp`, U: remove all secular
  directionality; random noise is fine). Peace, calm and safety pulls
  now act only inside ordered states (x administration); hierarchy falls
  with stateless life, separation with trade, trade disposition with war
  and raids; superiority's steady fall dropped (forms C).
- **Raids within peoples** (`kin_raids`, U; low administration already
  raises raids through `raid_order`): KIN_RAID 0.1 (C; 0.5 drove every
  people to violence ~0.95 by year 2000 in seed 107, 0.03 still drifts
  everyone up slowly: before states nothing lowers violence).
- **Unbiased drift** (`flat_drift`, U): split noise in trait units,
  reflected at the bounds; preference noise with mean 1.
- **Superiority's causes made symmetric** (U): captures and losses by
  share of a state's cities; trade with the more advanced lowers it.
- **Weaker path dependence and slower experience** (U; numbers under
  tuning): PATH_MIN 0.3 -> 0.6, EXP_SCALE 1 -> 0.5 as defaults; the grid
  runs vary PATH_MIN {0.6, 0.8} x EXP_SCALE {1, 0.5, 0.25}.
- **Appetite for goods** (`goods_appetite`, U: driven up by craft,
  technology, administration, violence and trade): APP0 0.5, APP_K 1.5,
  equal weights (C).
- **Feuding** (`feuding`, U 2026-11-02: an internal cost of violence;
  stateless peoples may stay violent but should vary): FEUD_K 0.004,
  FEUD_PIVOT 0.6 (C). Reason: in the grid runs Ogres and Giants sat at
  violence 0.99 / tolerance 0.01 for thousands of years, with selection
  against violence too weak to move them.
- **Troll hardiness** (`war_hardy`, U 2026-11-02): Trolls take 0.3 of the
  usual losses from raids, levies, sieges, sacks and clearances (number
  U→C), so that losing wars need not drive them to extinction.
- **Roster** (U 2026-11-02, numbers U→C): Giants violence 0.80 -> 0.70,
  tolerance 0.30 -> 0.35, craftsmanship 0.10 -> 0.30 (between Ogres and
  Humans); Goblins r 0.040 -> 0.035.
- **Provincial reach and travel distance** (`provinces`,
  `travel_reach`, U 2026-11-02; forms and numbers C): PROV_N 0.5,
  PROV_HOLD 100 yrs, PROV_LINK 0.3; PROV_CR 2.34 (measured), sea factor
  1.5 − 1.2 × sailing. Reason: no state passed ~6M km², every state was
  tied to one radius around its capital, and the straight-line distance
  ignored roads and treated sea and land alike.
- **Ruler traits** (`ruler_traits`, U 2026-11-02; forms and numbers C;
  next-batch.md items 22-29). At accession a ruler draws violence,
  dominance, expansion and statecraft on the logit scale, Student-t df
  RT_DF 3, scale RT_SD 0.5 × (1.5 − conformity): around the culture's mean
  (population-weighted over the state's lineages of his people) when a
  dynasty begins, else around his predecessor's (U). A disputed
  succession or pretender ends the dynasty; a state founded by revolt
  starts its own; partition heirs carry it on; union of crowns keeps the
  larger state's ruler (U; last C). No mean correction (U).
  - State decisions read culture + w × (ruler − culture) on the logit,
    culture = the ruling lineage (C), w = min(1, hierarchy × (1.5 −
    conformity)) (U: hierarchy = the king's influence, conformity = elite
    pushback; form C). These are war declaration and motives, military
    strength, land pressure, submission, sack, sparing and clearance,
    succession risk, fusion, vassal absorption, cities joining the state,
    logistics and administration progress (list C). Raids, migration,
    budding and acculturation stay on the lineage. Expansion has no
    state-level use, so a ruler's expansion acts only through the pull.
  - Pull (U): the state's lineages of his people move toward him on the
    logit at RT_PULL 0.03 × hierarchy × administration per year (C); not
    slowed by conformity (U); logged as the `ruler` column of `price.csv`.
  - Mismatch revolts (U): own-people provinces revolt × (1 + RT_REVOLT 1.0
    × conformity × gap), gap = RMS logit distance between ruler and the
    city's lineage (C).
  - Incompetence (U): administration falls by RT_ADMIN 0.004 × (culture's
    statecraft − ruler's, if positive) per year (C).
  - `rulers.csv` gains dynasty, the ruler's four traits (0-1), w, and the
    gap to the ruling lineage at his death.
- **Turmoil** (`turmoil`, U 2026-11-02: proportional; numbers C): the
  ruling lineage's administration × (1 − ADM_LOSS 0.5 × share) for the
  share of the state's cities lost to capture, cession or revolt, and ×
  (1 − ADM_RAID 0.05 × share of its cells raided) per tick. Watch for a
  collapse spiral (lower administration → shorter reach → more revolt).
- **Violent peoples revolt more** (`revolt_viol`, U 2026-11-02; form C):
  provincial revolt chance × (0.5 + the city lineage's violence).
- **Road engineering** (`road_tech`, U 2026-11-02; numbers C): see
  [traits/technology.md](traits/technology.md). Road quality ROAD_Q0 0.15
  (U: a low floor) + 0.85 × engineering × (0.8 + 0.2 × administration)
  (U: administration mostly sets the amount, a little the quality);
  travel cost × (1 − 0.5 × stock × quality).
- **Fortresses** (`fortress`, U 2026-11-02: Dwarves in underground
  fortresses impose extra casualties on attackers; numbers C): roster
  `fortress`, Dwarves 1, others 0. Raiders of a fortress cell lose 0.01 ×
  (1 + FORT_RAID 4 × f) of their people (5% for Dwarves, 1% otherwise); a
  state besieging a fortress city loses FORT_SIEGE 0.1 × f × the city's
  people across its cells, against the city's own 3%.
- **Great-drought logging** (U: log fewer; records only): 30%+ of people
  below −1.5 sd, 200+ years apart; about 11 per run (7-15) on batch1's
  climate series (C calibration). From batch3 on; batch2 uses the old rule.
- **Answered and closed** (U, 2026-11-01): keep colonies on occupied
  coast at COL_OCC 0.2 (U wants more contact); accept the small
  big-bodied peoples, Goblin numbers, and rare dragon alliances; keep
  the Earth-sized planet. Closed as solved or stale: population spikes,
  Snake folk dominance, metal and ore geography, city rank-size,
  patchiness, the separation redefinition and the four added traits,
  the dragon growth trap and dry-spell severity notes.

## Batch of 2026-10-30 (built; see next-batch.md for the list)

All behind switches; with `--off all` the model is unchanged (regression).
Provenance: the mechanism is the user's in each case (U); forms and
numbers are Claude's (C) unless marked.

- **Sites v2** (`sites_v2.json`): landmass quotas, 45 unique (U), 16
  precious on top (U), new kinds (U: woods, fibres, clay; list and rules
  C), Elf continent ~1 precious site via the quota (U wanted few).
- **Two-sided wars** (`two_sided`, U): COUNTER_K 0.5, repulse rule (C).
- **Alliances** (`ally_duty`, `ally_lapse`, `ally_balance`, `betrayal`,
  U): ALLY_J0 0.3, ALLY_LAPSE 0.002/yr, ALLY_GONE 0.02/yr, ALLY_OUTGROW
  0.01/yr above ratio 3, BETRAY_K 0.15 (C).
  Ally costs (U confirmed 2026-10-30): a joined ally takes war exposure
  and the war cost only; losses from sieges stay with the defender.
- **Trade and tolerance** (`trade_mean`, `tol_path`, U): mean tie;
  TOL_PIVOT 0.35 → 0.2 (U, "between low and middle"), TOL_PW 0.08 (C);
  softening share floor PHI_MIN 0.3 (U: even intolerant societies trade;
  number C); `trade_floor` TRADE_FLOOR 0.2 (U; number C).
- **Revolts harden** (`revolt_exp`, U: violence up, tolerance down,
  separation and conformity up): EXP_REVOLT 0.01 (C).
- **Memory** (`life_memory`, U: lifespan and patience): factor lifespan x
  (0.5 + patience) (C); IRR_MEM 150 yrs (C).
- **Spiky change** (`spiky`, U: per-year background, spikes at
  generations and major events): EXP_BG 0.5, GEN_YEARS 12.5, SPIKE_EVENT
  10 (C).
- **Rulers** (`rulers`, U; reign = 25 yrs x lifespan, lifespans U):
  partibility trait starting 0.1 (U: "generally single heirs"), PART_N 6,
  LONG_K 0.3, ACC_YEARS 10, ACC_K 1, OPP_K 1, ALLY_RENEW 0.3, VASSAL_ACC
  0.2, UNION_CROWN 0.03 (C).
- **Colonies** (`colonies`, U): COL_THIN 3000 (C).
- **Trading posts** (`trade_posts`, U): POST_K 0.02, MIN_POST 0.02 (C).
- **Value of goods** (`goods_value`, U: random draws, craft multiplier,
  starting biases U): PREF_SD 0.5, favoured x2, disdained x0.25, spread
  rates 0.01 (C). Preferences kept out of cultural similarity (C).
- **Precious metals** (`precious`, U: stacking, trade value, soldiers, war
  motive, depletion): MINE_RATE 1/600 per yr (placer 2x), PREC_STR 0.3,
  lode needs bronze (C).
- **Records** (U): `relations.csv`, `wars.csv`, `sieges.csv`,
  `revolts.csv`, `rulers.csv`; `timeline.py`.

## City histories (bookkeeping only)

- **`relations.csv`** (C, 2026-10-30): on each frame tick, every pair
  of neighbouring live states (land or sea adjacency) with similarity,
  enmity and faith motives each way, trade tie, war, alliance and truce.
  Reads state only; runs are unchanged. From 2026-11-07 similarity and
  motives are those war_chance reads (the states' cultures under
  `city_culture`; before, always the ruling lineages'), with the ruling
  lineages' similarity as a last column, `similarity_lin`.
- **`city_sizes.csv`:** every 25 years, every city (size, cell
  population, people, state) and every ruin (empty or settled).
- **`cities.csv`** gains: id, cause of end, peak year, number of sacks,
  previous city on the site, re-founding year, ruin years (and years
  empty), and successor.
- **Cause of end:** the most serious blow within 50 years before it, in
  the order clearance, sack, raid take-over, river lost, plague, drought,
  raid, siege. Without one, the cause is worn land (condition below 0.75),
  dry climate (moisture below −1 sd), or decline.
- **Ruins:** a site is a ruin until a new city is founded within 2 cells.

## City build, stages 1-3 (2026-11-02; forms and numbers C unless marked)

Code: `wsim/cities.py`; constants in `wsim/params.py` ("City culture",
"City administration"). Design and decisions: open-questions.md, "Cities
as a nested unit of culture".

- **Stage 1.** No hard density cap (U; city capacity already rises with
  trade, up to 4.5x). Seafaring dropped (inert). Rulers draw in trait
  units with reflection (U), RT_SD 0.125, RT_REVOLT 4. `dynasty` folded
  into rulers: cohesion ages from the dynasty's start.
- **Stage 2, `city_culture`.** Each city has an elite and a commons
  (all 14 traits). Commons: toward the residents' lineages (hinterland,
  main and minority) at CITY_RURAL x (0.5 + their conformity); toward
  nearby similar cities (CITY_NEAR, exp(-km/300) x similarity x
  sqrt(size)); toward trade partners' capitals' commons (CITY_TRADE x
  volume x port/river), both x (0.5 + tolerance) x (1.5 - conformity);
  experience (war, trade, hardship, raids, revolt) as for lineages but
  without path dependence or spikes; noise. Elite: toward its capital's
  elite under rule (CITY_RULE x hierarchy) and toward the ruler; a
  conquered or ceded city takes the conqueror's elite (replacing the
  foreign-rule acculturation path). A city acts on hierarchy-weighted
  elite + commons; a state on its capital's (cached per tick), through
  `eff`, `ssim`, `saccept`. Internal revolt ∝ conformity x (elite-commons
  gap / 0.1)²: the elite keeps a quarter of its difference; in a capital
  the dynasty ends, in a subject city the province may break away. A
  new city takes its mother city's culture. Lineages move toward their
  cities' commons (CITY_DOWN); a city whose commons stray 0.2 (RMS) from
  its home lineage founds a new lineage with its hinterland; lineages of
  a people in contact within 0.01 merge (0.03 erased new lineages as
  fast as they split: 248 lineages at yr 1250 against ~650).
  Diagnostics: `citylevel.csv` (variance by level, rural-urban and
  elite-commons gaps), `citygaps.csv` (per city, with trade volume).
- **Stage 3, `city_admin`.** Administration is invented and borrowed
  by cities and spread inside a state from its best-run city at ADM_UP
  x hierarchy x (1.5 - conformity) (U); the state's is its capital's,
  written onto the ruling lineage where the rest of the model reads it.
  `turmoil` does nothing under it (lost cities take their offices).

## 2026-11-02: lineage fusion replaces lineage merge (U)

User: "True fusion that is recorded. It also shouldn't require near
identical cultures... Partial fusion, whereby colonists end up absorbed
into a local lineage while their ancestral lineage remains & continues to
change should also be possible"; "Spatial & time based... Lineages
shouldn't fuse immediately due to proximity."

- Old `lineage_merge` (same people, in contact, RMS < 0.01, smaller
  folded into larger, unrecorded) removed with `LIN_MERGE`.
- `lineage_fusion` (wsim/cities.py): pairs of one people touching inside
  one state age by FUSE_EVERY each check (reset if they part or the
  state changes). Contact zone = each one's cells in the state within
  FUSE_KM of the other's. Chance/yr FUSE_K x min(1, age/FUSE_T) x
  (1 - mean separation) x (0.5 + larger's tolerance) x exp(-d/FUSE_D).
- Zone minority < FUSE_SHARE: absorbed into the local lineage (which
  takes a population-weighted share of its culture). Otherwise fusion: a
  new lineage (how=fusion, parent = larger, parent2 = smaller) from both
  zones. Outside the zone both lineages carry on.
- Recorded: `lineage_events.csv`; `lineages.csv` gains parent2 and fate
  (absorb:L / fuse:L for lineages wholly taken). Counters lineage_absorb,
  lineage_fuse, and _whole variants.
- Numbers C: FUSE_K 0.004, FUSE_T 400 yr, FUSE_D 0.15, FUSE_KM 300,
  FUSE_SHARE 0.25. Stateless lineages do not fuse (C).

## 2026-11-02: city history, weaker rule contact, per-city trade (U)

User: "Let's please implement the city memory of experience and weaken the
pull towards the capital. Let's just do both together." Then: "Lets include
it" (per-city trade exposure).

Diagnosis (ct batch, docs/run-log.md): cities of one state were near-alike
(SD 0.013) because cities followed their lineages and lineages under one
state converged. No pull acts directly from a capital on city commons; the
state-wide effect came from rule contact (each subject cell links its
lineage to the ruling lineage, moving customs at the trade-tie rate). The
effect shows in traits experience never touches, so it is contact, not
shared experience.

- `city_history`: experience pushes build an offset H per city, fading over
  CITY_HIST 500 yr (C); rural, neighbour and trade pulls move the commons
  toward target + H. Inherited from the mother city; reset when the city
  founds a lineage. Noise not in H (C).
- `rule_weak`: rule contact split from trade ties for the movement of
  customs, at MIS_RULE 0.0005 (a quarter of MIS_TRADE; C). Technology
  borrowing unchanged.
- `city_trade`: a city's trade exposure x (0.5 + 0.5 coastal or river)
  (form as CITY_TRADE; C). Recorded as trade_city in citygaps.csv.
- New records: h_rms in citytraits.csv; rural_urban_signed in citylevel.csv;
  lineage_pairs.csv (every pair at risk of fusion every 500 yr).
- Batch: runs/history.sh -> h_seed101-106.

**`trade_local`** (U 2026-11-03: each city trades most with the foreign
cities nearest it, so a frontier city can take on its neighbour's ways
while the heartland does not; form and number C). CITY_TRADE now pulls a
city toward the cities of each partner state rather than its capital.
Partner q counts tie x exp(-km to q's nearest city / CITY_TRADE_KM 500)
and offers its cities' mean commons weighted exp(-km / 500) x sqrt(size);
volume = min(1, sum of those weights). A city 500 km from the nearest
partner city gets 0.37 of the old pull, 1500 km 0.05. Total trade pull
falls for heartland cities and is unchanged for border cities, so the
mean pull drops (a side effect, not a target). Trade experience (the
tolerance push) and state trade volumes are unchanged. Recorded as
trade_near in citygaps.csv. Batch: runs/tradelocal.sh -> tl_seed101-106.

**`city_influence`** (U 2026-11-04: states do not impose their culture;
one city's effect on another is a function of trade volume, trade
asymmetry, distance, administration and influence; forms and numbers
C). One pull replaces the neighbour pull (CITY_NEAR), the trade pull
(CITY_TRADE, and `trade_local`) and the capital's pull on subject elites
(CITY_RULE). The weight of city j on city i is sqrt(pop_j) x (contact +
CITY_INF_TRADE x trade x asymmetry + CITY_INF_ADM x admin):

- contact: exp(-km / CITY_NEAR_KM) x similarity, as the old neighbour pull;
- trade: the tie between their states (CITY_TIE_IN = 1 inside a state) x
  exp(-km / CITY_TRADE_KM) x both cities' port factors;
- asymmetry: 2 x j's share of the pair's market reach (each city's sum of
  trade x sqrt(pop) over all cities), so a hub sways its partners more
  than they sway it;
- admin: from i's own capital only, the capital's administration x
  exp(-km / CITY_ADM_KM); a capital reaches its provinces farther than
  contact alone would carry it, and a better-run one more.

Commons move toward the weighted mean of the others' commons, elites
toward the others' elites, each at CITY_INF x min(1, total weight /
CITY_INF_W) x its own openness. The ruler now pulls only the capital's
elite; his ways reach the provinces through the capital's weight.
Kept as before: a new city copies its mother city; a conquered city gets
its conqueror's elite (`city_elite_to`); the lineage-level rule contact
under `rule_weak` (MIS_RULE). A heartland can arise from composition
alone: near the capital the capital and same-state cities (internal
trade at tie 1) dominate the weights; near a border, foreign cities'
contact and trade do. Recorded in citygaps.csv: adm, w_capital (the
capital's share of a city's weight), w_state (its own state's share).
Off: the old pulls.

**`adm_reach`** (U 2026-11-04: administration should widen a capital's
influence, in reach as well as weight, and reach is not a fixed
distance: roads and sailing extend it, as for maritime empires; numbers
C). On top of `city_influence`, the admin term becomes administration x
exp(-d / (ADM_REACH_F x reach)) at weight ADM_REACH_W = 6 (was 2, over a
fixed 1000 km). d is the state's own travel distance to the city
(power_dist, as for projected power and provincial revolt: roads cut
land cost, sailing cuts sea crossings from a coastal seat, provincial
seats relay at PROV_LINK); reach is the state's administrative reach
(REACH0 + REACH1 x administration, cut when underfed, longer with mounted
herders and allied dragons). ADM_REACH_F = 2: at administration 0.75 and
well fed the scale is ~1600 cost-km. Batch: runs/admreach.sh ->
ar_seed101-106, each under cProfile (ar_seed*.prof).

## 2026-11-06: dominion: extraction and shared cells (`dominion`)

Prompted by the user's observation that peoples do not move and that
conquest rarely changes hands (open-questions.md, "Peoples do not move").
Direction U: conquering a cell, and above all a city, should be worth
something; peoples should be able to move into conquered land. Shared
cells must include a direct technology term and a very large bonus for a
people backed by an established state (administration and statecraft)
(U). Built together with extraction at the user's request (U); forms and
numbers C. Code: `extraction` (states.py), `Kf` and `comp_w` (land.py),
the minority branch of `grow`, `settlers` and `tidy_minorities`
(settlement.py), the subject term in `rebellions`.

**Extraction.** Each tick (after `polity_stats`):
- Rate on every people in a state other than its ruling people:
  EXT_SUBJ (0.15) x (0.5 + hierarchy), x EXT_CITY (1.5) in city cells, at
  most EXT_MAX (0.5). Subjects' capacity is multiplied by (1 - rate).
- Food taken: rate x the subjects' food-equivalents (majority and
  minority). EXT_EFF (0.6) of it reaches the state's ruling people in the
  state's cities, shared by their food-equivalents there; a state with
  none of its people in a city feeds its capital. Received food raises
  the ruling people's capacity in that cell, smoothed at FISC_EMA (0.2
  per tick). When an empire loses its subjects, its cities lose the food
  and famine sends the surplus away.
- A subject city's revolt hazard x (1 + EXT_REVOLT (2) x its rate).
- Recorded: `extract` per state, n_ext_food per tick.

**Shared cells.** The minority slot becomes a share of the land. A
minority now grows toward the cell's full capacity for it, less
SHARE_ALPHA (0.9) x (w_majority / w_minority) x the majority's food, and
the majority's capacity loses SHARE_ALPHA x (w_minority / w_majority) x
the minority's food (Lotka-Volterra in food terms). Weight
w = (1 + SH_TECH x tech) x (1 + SH_STATE x est):
- tech = mean of farming, bronze, iron and steel; SH_TECH = 1.
- est = administration x (0.5 + statecraft) of the cell's state's ruling
  lineage, clipped to 1, and only for that state's ruling people;
  SH_STATE = 3, so a well-run state's people weigh up to 4x.
- Merchant quarters and trading posts stay capped at MIN_CAP (0.2) of K
  and are held back as before. Garrisons, colonists, the old people left
  by a raid takeover, and an old majority after a swap share the land.
- The existing swap (minority outweighs majority in food) flips the
  cell; under `dominion` it counts n_flip_to_ruler / n_flip_other.

**Settlers.** In `migrate`, after budding: a cell of a state's ruling
people above SET_PRESS (0.7) of its capacity sends SET_FRAC (0.02) of its
people per tick, at most half the room, into the neighbouring cell of the
same state, held by another people, where it has the most room (capacity
less the weighted majority's food, less settlers already there). They
join the minority slot if it is empty or already theirs. Recorded:
n_settler_heads. Settlers enter foreign land only inside their own state.

Off: everything as before, draw for draw (the off branch changes no
arithmetic).

Analysis: `turnover.py RUN ...` prints, per 500 years, the share of
occupied cells that changed people, of ruled cells whose ruling people
changed, of land in a state, of ruled land held by a foreign people, and
each people's share of heads.

## 2026-11-09: food flows (`food_flow`) and terms after a siege (`war_terms`)

Prompted by the realism review of 2026-11-09 (open-questions.md). City
sizes had a ceiling and cities ignored crises because a city was a cell
whose size was a fixed share of the cell and its hinterland, and no food
moved to cities except `dominion`'s tribute from other peoples. Decisions
U (2026-11-09): rent from a state's own people, the state's take to its
capital first, carriage by water, trade as a per-city volume, terms after
a won siege built now. Forms and numbers C. Code: `food_flows` and
`food_dist` (states.py), `Kf` and `prepare_capacity` (land.py),
`World.food_graph` (geo.py), `siege_terms` and `sack` (war.py). The code
before is in `archive/wsim_2026-11-09_pre_foodflow/`.

**Food flows** (needs `dominion`; replaces its extraction step). Each
tick, for every occupied cell in a state:
- **Rates.** Rent FF_RENT (0.12) x (0.5 + hierarchy) x exp(-travel cost
  to the cell's city / FF_KM), on every people, outside city cells:
  landlords take what can be carted to town. Tax on the ruling people
  FF_TAX (0.05) x (0.5 + hierarchy), outside city cells. Subjects pay
  EXT_SUBJ x (0.5 + hierarchy), x EXT_CITY in city cells, as before. The
  total is capped at EXT_MAX (0.5).
- **Peasants eat first.** The cell yields Q = its raw capacity x food per
  head. Of the nominal take x Q, FF_FORCE (0.5) comes whatever the
  harvest; the rest only from what is left after the cell's people eat
  (Q - need, clipped to 0..xQ). At equilibrium the whole take comes; when
  a bad spell leaves more people than the land feeds, the take falls
  faster than the harvest (with x = 0.15, a 36% fall in the harvest cuts
  the take by about two-thirds until the people thin). Each people's
  capacity is x (1 - its effective rate).
- **Where it goes.** Rent goes to the cell's own city. Tax goes to the
  capital x exp(-food distance / FF_KM); what cannot be carried is spent
  in the cell's own city (officials, garrisons). In a one-city state
  capital and town are one. All of it x EXT_EFF (0.6). A vassal sends
  FF_VASSAL (0.3) of what reaches its capital to its lord's capital,
  carried the same way.
- **Food distance** (`World.food_graph`): land edges cost as travel
  (terrain, rivers 0.7, roads); river channels FF_RIVER (0.15) per km;
  coastal cells within STRAIT_KM (160 km) of each other FF_SEA (0.04) per
  km. Diocletian's price edict puts sea, river and land carriage near
  1 : 5 : 30-50. FF_KM = 250 cost-km is the distance over which land
  carriage eats most of a load (e-fold), so by sea the e-fold is ~6,000
  km and along rivers ~1,700 km. Searched to FF_LIMIT (4) x FF_KM from
  each capital of a state of 2+ cities; cached on the capital and the
  graph's version (roads, rivers).
- **Trade food.** Each state's volume V = sum over its trade ties of tie
  x sqrt(FE_a x FE_b) (FE = food-equivalents in the state; a gravity
  form). FF_TRADE (0.003) x V reaches its cities in proportion to their
  food-equivalents x (0.5 + 0.5 x waterside). This is the one flow that
  adds food (gains from exchange) rather than moving it; it replaces the
  trade term of the city-cell boost, which keeps its base 1.5 x (1 +
  DEV_CITY x development) (gardens, manure and labour around a town).
- **Who eats it.** The ruling people in the capital cell receive the
  capital's take (`ext_in`); a city cell's majority people receive rent,
  local tax spending and trade food (`loc_in`). Both smoothed at
  FISC_EMA. A subject city's revolt hazard still reads its subjects'
  rate.
- Recorded: n_ff_rent, n_ff_tax, n_ff_trade, n_ext_food (all taken)
  per tick; per city, `cityfood.csv`.
- **Rent and trade set after a test** (C; seed 101 to year 6000, one
  seed). At FF_RENT 0.08 and FF_TRADE 0.01, trade was 75% of the food
  reaching cities, ports that were not capitals filled the top ranks,
  and urban share was 0.17. At 0.12 and 0.003: trade 37%, rent 34%, the
  state's take at capitals 17%, provincial spending 12%; the twelve
  largest cities are all capitals; urban share 0.11. Chosen on the mix of
  sources (towns lived mostly on rents and taxes; trade-fed cities were
  the exception), not on a target hierarchy.
- **World population falls** (6000 yrs: 89-99M against 154M with the
  switch off). Measured as urban population, a third of the old model's
  people (0.34) lived on the trade term of the city-cell boost, which
  made food rather than moving it; removing it removes them.

Off: `dominion`'s extraction as before (checked: with both switches off,
20 ticks from a year-5000 state are identical to the code before, every
part of the state but the records).

**Terms after a won siege** (`war_terms`). See rules/war.md. A sack:
the city's improvements and people suffer as in a capture (no
clearance, no garrison), the winner may take a guarded secret, the
defender loses administration (turmoil) and, if it was its capital,
20% of its cohesion; the winner gains 0.03 cohesion; a prey war's goal
is met. One sack per war per tick. A tributary: `submit`, the war ends
("tributary"), truce for 30 years. Recorded: `sieges.csv` `terms`,
`wars.csv` `sacks`, n_war_tributary, n_war_sack.

Analysis: `realism.py` (diagnostics.md).

## 2026-11-09 (later): cities as urban places (`urban_city`) and capital levers

Decisions U (2026-11-09, after the realism batch): build 2B; try the three
capital levers. Forms and numbers C. Code: `update_cities`, `city_weight`
(states.py), `city_sizes` and the size terms in `city_culture`,
`city_feedback` and `city_experience` (cities.py).

**Cities as urban places** (`urban_city`; reads the urban population of
the last tick, diagnostics.md):
- **Abandonment.** A city whose urban population stays below URBAN_MIN
  (2,000 food-equivalents) for URBAN_YEARS (50) ends, "abandoned", once
  it is URBAN_GRACE (100) years old. Its farmers stay: the cell loses the
  city's boost and the food sent to it, and its people thin to what the
  land feeds. The end cause is the latest blow as before (sack, plague,
  dry climate, salted land, decline...). The old rule (the cell's people
  below 0.35 x the founding threshold) still applies.
- **Founding.** No city is founded in a cell in famine (people above 1.05
  x capacity, famine's own trigger), so falls no longer breed towns; and
  none within 2 cells of a city abandoned less than URBAN_REFOUND (100)
  years ago, so a dying town is not refounded at once as a new state.
- **Size as the state reads it.** The capital after a capital is lost,
  and a pretender's city in a disputed succession, are the largest city
  by urban population. City culture's size terms use urban population:
  influence weight sqrt(size), a city's weight in its lineage's mean,
  and urban life (0 at URBAN_MIN townspeople, 1 at ten times that; was
  the cell's people against the founding threshold).
- Not changed: nothing in war decisions reads city size, so there was no
  siege value to switch; what taking a city is worth now comes through
  the food flows. Plague still reads city cells' people (chance, endemic
  immunity, origin).

**Capital levers** (defaults leave runs unchanged; tried in
runs/urban.sh): FF_CAP_KM, the e-fold of the capital's take over the food
graph (default FF_KM, 250; tried 500: a state carries its tax grain
further than a landlord his rents); FF_ABS, the share of the ruling
people's rent that goes to the capital with the tax (default 0; tried
0.5: absentee landlords); FF_TAX (default 0.05; tried 0.10, a tithe).

Check: with `urban_city` off and the levers at their defaults, 20 ticks
from a year-5000 state with `food_flow` and `war_terms` on are identical
to the realism batch's code in every part of the state but the records.

## 2026-11-17: debited trade food (`trade_debit`, WP4 stage B; off by default until WP4 D)

Forms and numbers are C unless marked. D5 (U, 2026-11-17): accept the
population fall. D6 (U): keep the base city boost and show it in the
ledger.

Under `food_flow`, trade food was created: FF_TRADE x V arrived in each
state's cities and no cell was debited. `trade_debit` moves it from
somewhere instead (`states.debit_trade`).
- **Marketable surplus** of a ruled cell: TRADE_SURPLUS (0.5) x max(0,
  raw capacity x food per head - what its people eat - what the state
  takes). Farmers sell part of a surplus, not all. A state's surplus is
  its cells' sum.
- **Flows.** Each live trade tie carries today's gravity term,
  FF_TRADE x tie x sqrt(FE_a x FE_b), one way. It runs from the state
  with more surplus per food-equivalent to the one with less. Before,
  each side received the term, so the wanted volume is half of what was
  created.
- An exporter's flows are scaled down together to its surplus. They
  are debited from its cells in proportion to their surplus, as a rate
  `tr_x` that Kf takes from the cell's main lineage alongside rent and
  tax. Because the flow is capped at surplus, selling does not starve
  the sellers.
- **Carriage.** Food arrives in the importer's cities (weights as
  before) x exp(-d / FF_CAP_KM). Here d is the food distance from the
  exporter's capital to the importer's capital. A pair beyond the food
  graph's reach (FF_LIMIT x FF_CAP_KM) trades no food. Capitals stand in
  for the brief's "nearest ports or capitals", because `food_dist` is
  computed only from capitals.
- **Smoothing.** Both sides at FISC_EMA: `tr_x` is smoothed as `loc_in`
  is.
- The base city boost is unchanged (D6).
- `food.csv` gains `trade_out`, `trade_in`, `lost_trade` and
  `gap_trade`. Under the switch `created_trade` is 0, so created food
  is the boost alone.

**Seeds 101 and 103, 8,000 years, on against off** (run-log.md):
- **Population at 8,000.** 139M against 156M (101) and 147M against
  166M (103): -11% both times.
- **Urban share.** 0.055 against 0.090, and 0.065 against 0.097.
- **Largest city.** 69k against 126k fe, and 122k against 176k.
- **Top of the hierarchy flattens:** largest / 10th city falls from
  2.34 to 1.70 and from 3.22 to 2.61.
- **The rank-size slope does not flatten.** It steepens (-0.36 to
  -0.42, and -0.35 to -0.43), because the loss falls on the largest few
  cities and small towns lose less.
- **Trade food is now 3-4% of city food** (it was 39-43%). Rent rises
  to 51-52%, provincial spending to 24-25% and the capital's take to
  20-21%.
- Trade sold is 0.5-0.6% of production in the last millennium, and
  54-63% of it is lost in carriage. Distant ties carry little that
  arrives.
- **Who exports.** Net exporters are smaller states with spare land
  (median food-equivalents 49-72k against 102-109k for importers).
  Trade mostly runs within a people: Elves, Dwarves, Humans and Snake
  folk in 101; mostly Elves in 103.
- **Fewer states and wars.** States: -18% and -21%. Wars: -30% and
  -35%. The largest state is smaller: 5.9 against 8.3M km2, and 5.6
  against 7.8.

Caution on noise: `wp4a_seed101` has the same mechanics as the off run
of seed 101. It differs only in the order of a floating-point sum, and
it ended at 126M, not 156M. A seed's history therefore moves by about
20% from rounding alone. The on/off differences point the same way in
both seeds, but two seeds do not give a size for them.

## 2026-11-17: deaths and growth account (WP4 stage C)

Records, and two small fixes to the bookkeeping. Forms are in
[rules/population.md](rules/population.md#accounting-for-people-wp4-stage-c-2026-11-17).
- Dragons' cut in the growth rate is no longer a cause of death. It is
  `forgone_dragon` in `growth.csv`.
- `growth.csv` closes a per-century account per people:
  change = natural increase - removals + made + phase nets.
- The account found five gaps, and all are now recorded or fixed:
  - raid takeovers dropped half the old majority and any old minority
    (now raid deaths);
  - a cell sending two takeover bands paid for one (fixed);
  - colonists refused by an occupied minority slot vanished (they now
    stay home);
  - natives pushed out by colonists (`displaced`), expelled minorities
    (`expelled`) and tiny remnants cleared by `tidy` (`dwindled`) were
    unrecorded.
- Minority heads added from no cell are shown as `made`: merchant
  quarters, trading posts, garrisons. They are an existing rule (C),
  now visible: 8M over 8,000 years of seed 101, mostly Dwarves and Snake
  folk, against 1,153M natural increase.

## 2026-11-18: trade_debit the default, carriage between nearest cities, the take per lineage (WP4 D)

Decisions U (2026-11-18), on the three questions left by WP4 A-C: make
`trade_debit` the default, carry traded food port to port, and fix the
minority leak. Forms C.
- **`trade_debit` is a default.** It moves from `params.OPTIONAL` to
  `FEATURES`, so `--off trade_debit` restores created trade food. A
  state saved before WP4 D keeps its own switches; a branch from it
  names `--on trade_debit` to turn it on (`--on` now takes defaults
  too).
- **Carriage between the nearest cities.** Traded food is carried over
  the food graph between the nearest pair of the two states' cities
  (`trade_dist`: one multi-source search from all of the exporter's
  cities, cached on its cities and the graph's version). Before, it was
  capital to capital. Over water the nearest pair are ports, since sea
  edges cost FF_SEA (0.04) per km against about 1 on land; between land
  neighbours it is the two border towns. This is wider than "port to
  port" in the strict sense (C): a strict rule would have stopped land
  neighbours without ports from trading food, or needed a second rule
  for them. Arrivals are spread over the importer's cities by size and
  waterside, as before.
- **The take per lineage** (the stage A leak). The main lineage and the
  minority now each pay their own people's rate on their own capacity:
  T = T_own + T_subject, each with "peasants eat first" applied to that
  group's capacity and needs. Before, one rate blended by the two
  peoples' shares was applied to the main lineage's capacity alone, while
  `Kf` debited the minority as well, and that payment went nowhere.
  `ff_xo` and `ext_x` are now the effective rates of the two groups, so
  what `Kf` removes equals T (`taken_capacity` = `taken`).
- **Trade debit on both lineages.** `tr_x` is now charged to every
  lineage in a cell in proportion to its capacity, since the cell's
  surplus now counts the minority's harvest. Before, the main lineage
  alone sold.
- `food.csv` `produced` now includes the minority's harvest.

**Seeds 101 and 103, 8,000 years** (run-log.md, 2026-11-18):
- `taken_capacity` = `taken` in every century; ledger gaps and the
  growth residual are 0.
- Carriage loss on traded food falls from 63% to 20-25%; traded food is
  3-4% of city food in the last millennium.
- Population at 8,000 against stage C with trade food created: -3% and
  +3%, inside seed noise. B's -11% did not recur; the runs do not
  separate the three changes.

## 2026-11-18: odds-gated war (`war_odds`, WP5 stage B)

U (2026-11-18): build stage B as stage A recommended, item 3 first.
Forms are from the upgrade review; every number is C. Stage A
(run-log.md, "2026-11-18 WP5 stage A") found:
- equal-sized states besieging at median odds of 0.02-0.05;
- a submission rule that fired only at a 3:1 edge (odds 0.9), while
  one-city defenders fell at odds of 0.80-0.86;
- one-city defenders ceding their only city.

- **Gate on declaring.** In `war_chance`, deterrence becomes floor +
  (1 - floor) x logistic((ln R - ln ODDS_MID) / ODDS_W). ODDS_MID is
  0.7 and ODDS_W 0.35. The floor is ODDS_FLOOR (0.05) x min(1, R /
  ODDS_MID) x min(1, desperation + enmity + faith). The gate is at most
  1, so `war_bound` is still an upper bound.
  - A flat floor, without the R factor, was tried first
    (`wp5b_seed101`, `103`). Below R = 0.16 it was looser than the old
    rule. 13-14% of wars were declared at a whole-state strength ratio
    under 0.5, against 1%. Half of all wars had no siege, and
    population ended 15-19% lower.
- **Gate on besieging.** In `wars_step` and `counteroffensive`, a siege
  needs odds >= SIEGE_MIN (0.15).
  - Below it the attacker `ravage`s (chance = violence) or sits.
    Ravaging kills RAVAGE_K x violence of the target city's hinterland
    in the defender's territory (less for hardy peoples) and cuts
    improvements by 0.3 x that share. This is the raid rule's damage
    form, at the city's land rather than at a border.
  - `WAR_STALL` (15 years) without a siege by either side ends the war
    "abandoned".
- **Submitting first.** The pre-siege submission now reads the odds:
  SUBMIT_K x clip((p - SUBMIT_ODDS) / (1 - SUBMIT_ODDS)) x (1.2 -
  cohesion) x (0.5 + dominance), with SUBMIT_ODDS 0.6 and SUBMIT_K 1.
  The old form was 0.5 x the same last two factors, only past a 3:1
  edge.
- **No ceding a last city.** A defender may not cede the goal when it is
  its only city: ceding would end the state, where submitting keeps it.
- **Record fix.** The cession branch closes the war before `cede`, so a
  last-city cession reads "ceded".
- New: `wars.csv` `ravages`; the death cause and city shock "ravage";
  the counter `war_ravage`; `growth.csv` `dead_ravage`.

## 2026-11-18: site defence and ruler generalship (`site_defence`, `ruler_mil`)

Both are U's (2026-11-18); forms and numbers are C. Details are in
rules/war.md.
- `site_defence`: `Sim.site_def` is one draw per cell on its own stream
  (`new_state_v5`, also run by `upgrade()`). `Sim.city_def(c)` replaces
  `W.defence[c]` wherever a city is the target. Raids between cells
  still read the terrain alone.
- `ruler_mil`: `P["gen"]` (this ruler) and `P["gen_legacy"]` are set in
  `new_polity` and at each `reign_end`. `WarMixin.offense(P)` multiplies
  the besieger's projected strength in `wars_step` (and in the cession
  test) and in `counteroffensive`. `deter` does not read it, so
  `war_chance` is unchanged. rulers.csv `offense` is each reign's g.

## 2026-11-18: clocks in years and a yearly political step (WP5 C, D; `pol_step`)

U (2026-11-18): build stage D, with sieges that have a length. Numbers C.
- **Stage C.** Truces, war ages, last sieges and the plague gap are held
  in years; rates once written per tick are quoted per 5 years (SPAN)
  and applied with `params.over(p, years)`. `upgrade()` converts old
  saved states (flag `clock_years`).
- **`Sim.politics`.** Runs `diplomacy`, `wars_step` and `rebellions`
  DT / DT_POL times a tick, setting `self.year` to each sub-year and
  `self.dtp` to the sub-step's length. Every rate in those three (and in
  `war_chance`, `war_bound`, `vassal_politics`, `succession`) reads
  `self.dtp`. If a city's polity changed in a sub-step (not the last),
  `pol_refresh` redraws territory and scales strength by the change in
  weighted people (`_popw`, cached by `polity_stats`); a state founded
  that tick takes its parent's strength per weighted head.
- **Sieges.** `wars_step` keeps a list `w["on"]` of sieges under way:
  side, city, start and end year. `sieges_run` charges each its share of
  SIEGE_TOLL and decides those whose time is up (`siege_end`, on the
  odds then); `sieges_open` and `counteroffensive` fill free slots
  (`siege_start`). Without `pol_step` a siege is decided when laid, as
  before.
- **Not converted.** One sack per war per step; the cultural spike, the
  `revolted` and `sup_*` accumulators, per tick.

## 2026-11-18: field armies (`army`, WP5 E)

Forms from the review (four points: raise and feed an army, sieges use
it, projected strength is the army's, exhaustion by losses); numbers C.
- `WarMixin.army_step` (start of each `wars_step`) moves each state's
  `P["army"]` toward ARMY_SHARE x people if it is at war, to 0 if not,
  taking heads from or returning them to its own people's cells. It sets
  `Sim.army_x`, which `Kf` adds to the ruling people's removal rate and
  `food_ledger` reports as `taken_army` (and inside `taken_capacity`).
- `field(P)` and `garrison(P)` scale the odds in `siege_odds`,
  `siege_end` and `counteroffensive`, and the cession test.
- `army_loss` at each decided siege; `w["lost"]` keeps the heads lost
  per side for the exhaustion term. Deaths "battle" are booked per
  people directly (soldiers have no cell). `heads()` counts soldiers,
  so the people account stays closed.
- `polity_stats` records `K_own`, the capacity of a state's own people,
  for the army's food share.

## 2026-11-18: camp polities (`camps`, WP5 F)

U (2026-11-18): camps outside the city table; defeat scatters or makes a
vassal; threshold from one run's distribution. Numbers C.
- A camp polity has `P["camp"]` = its seat cell (also `P["capital"]`)
  and an empty `P["cities"]`. `territory` adds camp seats as Dijkstra
  sources; their cells get `cell_pol` but not `cell_city`.
- `camps_step` (after `update_cities`) moves seats, disperses weak
  camps and forms new ones. `decamp` turns a camp holding a city into a
  state, after each political sub-step and each tick.
- `seated(P)` replaces "has cities" in `war_bound`, `war_chance` and
  the war loop. `deter` reads a camp's seat. `sieges_open` and
  `counteroffensive` send a camp opponent to `camp_battle`. `set_goal`
  falls back to the capital.
- `reach(P)` for a camp: CAMP_REACH x cohesion x (1 + CAMP_HERD x
  herd). `food_flows` gives camp-ruled cells no rates.
- `len(P["cities"])` thresholds see a camp as 0 cities, so it gets no
  provinces, steel or partition. Succession runs for camps as for
  states.

## 2026-11-18: epidemics and upkeep (`epidemic`, `upkeep`, WP6 C)

U asked for plague that spreads over time and reaches people outside
states, and for capacity that rebuilds slowly after a crash; forms and
numbers C.
- `LandMixin.disasters` calls `plague_onset` and `plague_step` under
  `epidemic` (else `plague_burst`, the old rule). `Sim.epi` holds the
  epidemics under way: origin, host, start, mortality, a `seen` mask over
  cells, the cells reached last tick (`src`), states struck, deaths.
- `plague_step` spreads over `plague_adj()` (8-neighbour land grid plus
  `W.sea_links`, cached on the world) and along `ties`; `plague_kill`
  removes the dead (records via `dead`, so the growth account still
  closes), sets immunity, hardship, city shocks and spikes.
- `land_use` adds the `upkeep` lapse to the improvement decay.

## 2026-11-18: the presence table (WP7 B)

Storage only; no rule changed (U chose a presence table over fixed slots,
and the layout with fixed first two rows; `docs/upgrade/WP7-design.md`).
- `Sim.rows_new` builds one table of rows: cell `rc`, people `rp`,
  lineage `rl`, heads `rh`, merchant cap `rm`. Row i < N is cell i's main
  people, row N + i its minority; an empty row has people -1. Rows from
  2N on will hold further peoples under `shared_cells` (WP7 C); none
  exist yet.
- `pop`, `cul`, `lin`, `mpop`, `mcul`, `mlin`, `mcap` are numpy views of
  those rows (`rows_bind`), so every routine reads and writes the table
  through them. Code must not rebind these names; a reallocation of the
  table must call `rows_bind`.
- Pickling leaves the views out and `__setstate__` rebinds them;
  `upgrade()` copies an older state's arrays into a new table.
- Check: `wp7b_seed101` reproduces `wp6c_seed101` exactly (`events.txt`
  and `timeseries.csv` byte-identical), and a state saved at year 3,000
  and continued to 3,500 ends as the run that saved it.

## 2026-11-18: shared cells and flight (`shared_cells`, `displacement`, WP7 C and D)

Design and decisions in `docs/upgrade/WP7-design.md`; numbers C.
- `wsim/shared.py` (`SharedMixin`). Rows past 2N ("extra rows") hold
  third and further peoples. `rows_put` adds heads to a people's row in a
  cell, or the free main or minority row, or queues an extra row;
  `rows_flush` (from `acct_mark` and `tidy`) writes the queue, so the
  table is reallocated only between phases; `rows_compact` drops empty
  extra rows. `rows_find` looks a (cell, people) up.
- `grow_shared` (from `grow`) replaces the minority block: niche-overlap
  competition among all rows of a cell (`overlap`, `rows_pairs`).
- `infiltrate` (after `migrate`), `inner_raids` (after `raids`),
  `rows_sort` (in `tidy`, replacing `tidy_minorities`' swap).
- `flee` and `lost_rows` (`displacement`): called at raid takeovers,
  sacks (capture and `sack`), clearances and expulsions; `rows_scale`
  gives extra rows the minority's share of raid, ravage and sack damage.
- Extra rows are also read by: `heads` (growth account), `dead`/`forgone`
  (`rows=True`), plague (`plague_kill`), `polity_stats`, `extraction`,
  `food_flows`, the food ledger, dragons' head counts, `add_minority`
  (garrisons and merchants may take an extra row), `minorities`
  (expulsion) and `price` (now all rows, the minority included).
- Since WP15 (2026-11-22) also read by: technology contact (each
  extra row counts as a minority, 2 per cell, with the cell's main
  lineage); city composition (`city_culture`'s residents and diversity,
  and the cities' `min_share` record); famine (`famine_rows`: minority
  and extra rows move their surplus over their share of capacity);
  clearance (minority and extra rows of the city's people lose 0.85 x
  hardiness, under `shared_cells`); the history snapshots (table `xr_*`:
  cell, people, lineage, heads per extra row). `minority_pop` in the
  timeseries is still the minority row alone.
