# Open questions and known issues

Revised 2026-11-01. Questions answered or overtaken that day were
removed; decisions are recorded in [structural.md](structural.md)
("Changes of 2026-11-01"). The previous version is
`archive/open-questions_pre_1101.md`.

## Realism review (2026-11-09)

Two outside assessments in `../reviewdocs/` (`REALISM_REVIEW.md`,
`map_making.md`), written without the code. Both read `sw300_seed101`,
the f = 3 run of the turnover sweep on code from before 2026-11-07.
Re-measured on the whole sweep and on dom_seed101-103 (C):

| Finding | Holds? | Evidence |
|---|---|---|
| City sizes have a ceiling | Yes, in every run | top-200 slope -0.20 to -0.27 at the end at every f; top five 39-66k |
| No empires | Mostly the sweep | largest state 19.2M km² at f = 0.5, 9.3M at f = 1, 2.0M at f = 3; land is 122M km², so 6-8% at f = 1 (Rome ~3%, Mongols ~16% of Earth's) |
| Wars end in the defender's fall | Partly | 64-73% of endings, but 82-84% of those are one-city states; 10-16% for defenders of 5+ cities. "0 years" = within one 5-year tick |
| Technology saturates by year 3500 | No | leaders reach steel at 5000-6000, three peoples never; growth after is 0.03-0.07%/yr from intensification |
| Cities rarely end, no collapse | Collapse yes; cities don't respond | world population -22 to -36% within 300 yrs near year 7250-7600, yet city count rises through it; 3-14% of cities alive at 3000-5000 end within 2000 yrs |

Also: the growth-by-size table in the review is partly regression to the
mean; big cities lose cell and hinterland population at the same rate
(-0.009 vs -0.008 log per 25 yrs), so hinterland theft is not the cause.

Causes in the code (C): city size was 0.08 x the city cell + 0.04 x its
hinterland; the city-cell boost 1.5 + 2 x min(1.5, state trade) sat near
its cap for almost every state (ties climb toward 1 and decay only in war
or apart); `dominion` moved food only from other peoples' subjects; no
term for carriage by water; a city ended below ~2,100 Humans in a cell
holding 100k-250k.

**Decisions (U, 2026-11-09):** the plan as proposed. Urban population as a
derived output first (2A), not yet the city's state variable (2B). States
draw rent from their own people's countryside. Terms after a won siege
built now. Steel as the final technology over 8,000 years is intended.

**Built (forms and numbers C):** `food_flow` and `war_terms`
([structural.md](structural.md), "2026-11-09"); urban population as the
city's size; `cityfood.csv`, `deaths.csv`; `peak_km2` for every state;
`realism.py`.

**Batch results** (run-log.md, "realism batch"): food flows steepen the
city hierarchy (slope -0.22..-0.26 to -0.34..-0.41) and put urban share at
0.10-0.12; terms after a siege give 11-14% of wars a tributary end and
double the standing vassals; world population falls a quarter.

**Decided and built (U, 2026-11-09, after the batch):** 2B as
`urban_city`; the three capital levers tried in runs/urban.sh
(structural.md, "2026-11-09 (later)"); the map waits for those runs.

**Open:**
- 2B (built as `urban_city`, being tested). Evidence that led to it (C): under food flows, slow crises push a
  quarter to half of all cities below URBAN_MIN (base: almost none), yet
  cities keep being founded through every fall because founding and
  abandonment read the cell's people. So 2B is what would let crises end
  cities.
  **Found in the batch (C):** founding still reads the cell's people
  while keeping reads urban food, so most of 2B's endings are a
  found-starve-abandon-refound cycle (93% of abandoned towns end at age
  100-150, 91% never reach URBAN_MIN, 73% are refounded within 5 years
  of URBAN_REFOUND running out; run-log.md, "urban batch"). URBAN_REFOUND
  is a kludge (C, 100 years chosen without evidence) and does not stop
  it. Proposed (C, not decided): founding reads the urban food the town
  could draw (rent from the cells it would take from other cities, by
  carriage), founding above a higher bar than keeping (hysteresis), and
  URBAN_REFOUND removed, so a site stays empty as long as its cause
  lasts (salt, climate, a lost state or trade).
- **City primacy is still weak** (largest city 0.07-0.10% of the world,
  largest / 10th 1.7-2.6). States spread more than their capitals, so
  the limit is how much tax a large state can carry to its capital.
  Candidate levers (C, none tried): FF_TAX (0.05 x (0.5 + hierarchy); a
  tithe would be about 0.1), FF_KM (250 cost-km), or the capital drawing
  on the ruling lineage's rents as well as tax (absentee landlords).
- The map (`map_making.md`): names go in blank ID tables (the book holds
  names until its naming pass); draw it from a fresh default run, not
  sw300; base, regions and states can be drawn now, cities after the
  batch.

## From batch2 (2026-11-01)

- **Tolerance converges high and alliances saturate** (world tolerance
  0.70-0.81, 2.2-2.6 alliances per state). Proposed (C): take tolerance
  out of `trait_path` (its own `tol_path` already makes it path
  dependent), or raise its pivot.
- **Goblins end least violent** (traced 2026-11-01, instrumented seed
  107). Experience, not selection or acculturation: Goblin raid exposure
  is 0.014-0.017 against Humans' 0.09-0.11, war exposure under 0.02
  through year 5000. Raids happen only between peoples, and most Goblins
  live deep in their own territory (15-23% on an ethnic frontier against
  42-58% of Humans and Lizardfolk), so the steady peace push wins; below
  0.5 path dependence holds them there. Accepted as an outcome (U).

## From the cau runs (2026-11-01)

- **Superiority saturated (0.87-0.99)** and **traits ran to a bound
  under one-sided pressure.** All three fixes adopted (U): symmetric
  superiority causes, weaker path dependence, slower experience; the
  strength of the last two was tuned in the grid runs; defaults
  PATH_MIN 0.6, EXP_SCALE 0.5 kept (C). See run-log.md "grid".

## From the grid runs (2026-11-01)

- **Peoples converge after year 4000.** SD of people means fell from
  0.17 (yr 2000) to 0.10-0.14 (yr 8000) in 10 of 12 runs, faster when
  experience is slower, so contact acculturation (ACC_CROSS 0.1) is
  the likely cause. Options (C): lower ACC_CROSS (the user wanted more
  contact), or make cross-people pull depend on more than contact.
  Not yet traced with the Price output by source.
- **Stateless peoples pinned at violence 0.99, tolerance 0.01.** Ogres
  in 11 of 12 runs, Giants in most. It follows from the causal rule
  (no state, no order, no peace pull; raids keep pushing). The only way
  down is the 0.75 down-scaling under path dependence and selection
  (-0.02 to -0.035 per 1000 yrs, too weak). Question for the user:
  is a permanent corner acceptable, or should feuding at high violence
  carry a cost (population loss, fission) that selection can act on?
  Answered (U, 2026-11-02): add the cost (`feuding`); high violence is
  fine for stateless peoples, but they should vary. Testing (feud runs).
- **PATH_TOL** still open; with PATH_MIN 0.6 tolerance no longer
  converges high, so leaving it in `trait_path` (PATH_TOL 1) looks fine.

## To check in batch2 (2026-11-01)

- **Does path dependence hold to year 8000?** In 5000-year tests the
  spread of people means rose 1.5-2x (violence, tolerance, conformity).
  Not yet tested past 5000.
- **Ordering of peoples.** In the tests Goblins ended the least violent
  people (0.45, roster 0.85). Path dependence keeps peoples apart, but
  not necessarily near their roster values. Is a reordering acceptable?
- **Slower mixing between peoples** (`acc_cross`): does it keep peoples
  apart under multi-people states, and does it change who rules whom?
- **Devastation at 3% per siege:** how many cells lie waste at once,
  and how many cities it empties.
- **State churn.** batch1 small states (3-9 cities) lived a median of
  55-90 yrs with 1,000+ founded per millennium late in the run; larger
  states lived 255-305 yrs. Path dependence lowered war counts in the
  tests; check whether the swarm of small rebel states remains.
- **Alliances** rose to 360-616 at year 8000 in batch1. Unions of crowns
  are now cut to 1%; check alliances per state.


## Known causeless biases (keep minimal, U 2026-11-01)

- **Drift at lineage splits leaned toward 0.5** (logit-scale noise), and
  goods preferences crept upward (log-normal noise, mean above 1). Both
  fixed by `flat_drift` (U, 2026-11-01).
- **Skills borrow upward faster than downward** (SKILL_DOWN): correct as
  intended (U, 2026-11-01), not a bias to remove.
- **Reflection at the bounds** (`flat_drift`) pushes a trait at 0.01 or
  0.99 inward; this is the remaining edge effect.

## Deferred until after the next full runs

### Culture and peoples
- **Conquest motive.** Nothing makes a people want to rule others rather
  than raid or clear them. Options: one trait, or a combination of
  violence, statecraft and proselytism.
- **Trust radius** (U: open to it): how large a group trusts itself
  before splitting along kin lines; acts inside a people (fission,
  contested successions). Overlaps cohesion more than tolerance.
- **Mixed settlement** (U, for later). Now a cell holds one people plus
  one minority (up to 20% of capacity). General form (C): shares of
  several peoples per cell from a shared capacity, mixing held up by
  tolerance, trade and protection, pulled apart by intolerance,
  competition and expulsion. The largest refactor so far.
- **Fusion between peoples is narrow.** batch1: 0-17 fusions per run,
  all Goblins with Giants, Trolls, Ogres or Dwarves.
- **Kin wars.** Wars between lineages of one people are common (W1's
  major wars are mostly Human against Human). `SIM_SAME_SCALE` sets it.
- **Big-bodied peoples small** (accepted 2026-11-01): Trolls 1-5%, Ogres
  0-1%, Giants 1-4% of food-equivalents; likely slow domestication and
  little craft. Revisit later if wanted.

### States and war
- **Vassalage is rare** (7-31 standing at the end of batch1). The 3:1
  threshold is applied after terrain and capital defence, so it is
  seldom met. *Superseded (WP13 A, 2026-11-21):* under `war_odds` the
  3:1 rule is not read; defenders submit through SUBMIT_ODDS, 288-1,076
  times a run in `wp10c`. Vassalage is short rather than rare (42-55%
  defect). WP13 B adds annexing vassals of another people.
- **Elite model.** Elites grow whenever crowding exceeds 0.75, which
  mature states usually do; cycles or a steady rise in revolts?
- **Floodplain cities get swamp defence**, through wetness on alluvial
  lowland.
- **Some state decisions still read the ruling lineage** (found
  2026-11-07, not changed). Under `city_culture`, war, trade and alliance
  read the state's culture (its capital's, via `eff`/`ssim`). These
  three read the ruling lineage's traits instead: the revolt "alien"
  term (similarity and tolerance, `rebellions`), the weight of foreign
  subjects in strength (tolerance, `polity_stats`), and the expulsion
  of minorities (tolerance, `minorities`). Intended (the lineage's own
  view), or should they move to the state's culture? **Settled
  2026-11-22 (U, D18):** a blend, the ruling lineage moved toward the
  state's culture by its tolerance (`state_view`, rules/states.md).

### Economy and technology
- **Herding at low farming** is never worse than foraging, which loosens
  the early farming penalty on poor land.
- Technology loss, borrowing and costs: WP14 (`tech_forget`,
  `closed_borrow`, `tech_costs`; see `upgrade/WP14-design.md`).

### Landscape and climate
- **The terrain effect hasn't been isolated** (needs the same seeds with
  terrain off).
- **River changes rarely touch cities** (1-4 city ends per run); widen
  the prone set (smaller rivers, deltas)?
- **Ruins.** Sites were never empty after a city fell; devastation now
  empties some. Check after batch2.
- **Steppe stand-in.** Aridity inside a biome comes from distance to the
  coast; a real moisture field in the world build would replace it.

## Data

- Strips in the wetness, relief and alluvial inputs around 100-120°E,
  25-35°S ([world-data.md](world-data.md)).

## Empire size (checked 2026-11-02)

- The user asked why no broad unifying empires appear. Measured on the
  feud runs: 31-40 states per run reach 30+ cities, and the largest
  states at year 8000 cover 2-6M km² with 90% of their land within
  1,100-2,200 km of the capital (Rome ~5M, Han ~6M, Achaemenid ~5.5M,
  Song ~3M). E1 (4.8M km²) is wholly united in some runs (Snake folk,
  83 of 83 cities); N1 reaches 50-65% of its land; W1 (19M km²) 24-48%;
  S (75M km²) 2-10%. No state passes ~6-10M km²: no Mongol, Abbasid or
  Qing tier. Likely cause: reach (120 + 900 x admin cost-km) and
  projected strength falling as exp(-distance / 1.5 reach) from the
  capital tie every state to one radius. Answered (U): provincial reach
  and roads extending reach, maritime empires possible, sailing extends
  reach over water. Built as `provinces` and `travel_reach`. Prov runs:
  largest states 9-24M km², maritime Elf and Dwarf empires. New open
  points: the largest state on S is a Goblin state in every run, and
  Goblins rose from 25-37% to 39-54% of all heads; between-people
  spread fell slightly.

## Peoples do not move; conquest rarely changes hands (2026-11-06)

- **The user's observation (U):** from about year 1500, whichever people
  first fills a region holds it to the end. Nothing like Assyria ->
  Persia -> Macedon -> Rome, no warring-states collapse of a unified
  empire, and no steppe waves.
- **Measured on arh_seed101** (history.npz, 500-yr windows):
  - Occupied cells that change people: 0.9-1.2% per 500 yr, flat from
    year 600 to 8000.
  - Ruled cells whose *ruling people* change: 0% before 3500, 9% at
    4500-5000, 13-19% from 5000 on.
  - State IDs change in 75-85% of ruled cells per 500 yr. 117 of the
    145 states that reach 250+ cells fall before 8000 (median life ~400
    yr), so states rise and fall, but mostly to successors of the same
    people.
  - Occupied land inside any state: 1% at 2100, 20% at 5000, 42% at
    7500. The rest is stateless and can only change hands by raid.
  - State colours are the ruling people's colour with ±15 jitter
    (`polity_color`), so successions within a people barely show on the
    political map. Cosmetic; low priority (U).
- **Why peoples cannot move (from the code):**
  1. *Exclusive occupancy.* `migrate` moves people only into cells of
     their own lineage; `budding` only into empty cells. A full foreign
     cell is a wall, whoever rules it.
  2. *Capped minorities.* A minority's capacity is MIN_CAP (0.2) x K, and
     there is one minority slot per cell. `tidy_minorities` swaps
     minority and majority only when the minority outweighs the
     majority, so a cell flips only when the majority collapses to about
     a fifth of K.
  3. *Conquest delivers nothing to the conqueror's people.* `war_chance`
     has a land-hunger motive, but winning gives no land (point 1) and
     no food. It adds strength from subjects at 0.4-0.9 weight, a
     one-off garrison minority (MIN_GARRISON 0.04), and a revolt risk up
     to 4x higher. Wars are motivated by land they cannot deliver.
  4. *Clearance kills; it does not displace.* Survivors stay put or
     die; no refugees press on neighbours, so there are no cascades.
- **Proposed (C), not decided:**
  - A. *Shared cells under competition.* Replace the capped minority
    with two peoples sharing K (in food terms). The share shifts with
    each one's K on that land (technology, biome preference), growth,
    and political status (the ruling people gets the better land, the
    subject people pays the extraction in B). Migration within a state
    may flow into subject cells as settlers (Assyrian deportations,
    coloniae, Han military colonies, Arab garrison towns).
  - B. *Extraction.* Subject cells pay a share of their surplus to the
    state, and cities more (trade, crafts, improvements). This feeds the
    ruling people's core or the state's strength, so `war_prize` becomes
    real income. The cost falls on the subjects (slower growth, more
    unrest).
  - C. *Displacement.* Clearance and lost raids push survivors into
    their own people's neighbouring cells or onward, raising pressure
    there.
  - D. Then: a metaethnic-frontier term for cohesion and a path for
    herders to form large states (agreed in direction, U).
- **Decided (U, 2026-11-06):** build A and B together as one switch
  (`dominion`, structural.md) and look at overnight runs before C and D.
  A gets a direct technology term and a very large bonus for a people
  backed by an established state (administration, statecraft). The two
  questions put to the user (does the ruling people get privileged land;
  does extraction feed growth or only strength) were not answered
  directly; as built (C), privilege comes only through the state bonus
  and extraction, and extraction feeds the ruling people's capacity in
  their cities (so growth, and through it strength).
- **Risk to watch:** a people that is already large (Goblins, 39-54% of
  heads) could flood everything, and between-people diversity would
  collapse. Judge on spread between peoples and on how often regions
  change hands, not on any target share.

## Cities as a nested unit of culture (2026-11-02, design; not built)

Prompted by the rulers batch: turmoil cut the administration of a
*lineage*, which several states and stateless kin share, so one realm's
revolts eroded its neighbours' offices (run-log.md, "rulers batch"). The
user's diagnosis (U): the model jumps to culture-wide properties and
under-uses the city qua city. Ancient polities were often cities
influencing culturally similar cities and subjugating distinct ones.

### Decided (U, 2026-11-02)

- **Cities are *a* unit of culture, not *the* unit.** Culture is nested:
  people > lineage > city. Cities within one lineage differ in
  tolerance, conformity, dominance, hierarchy and the rest (Athens,
  Thebes, Sparta). Note (C): those three were also Ionian, Aeolic and
  Dorian, so real variation sits at both levels; measure both.
- **Technology originates in a place** and spreads by culture to similar
  places; it does not originate in a "nebulous culture".
- **A city has a founding culture** and is influenced more by nearby,
  culturally similar cities than by remote or foreign ones; it is also
  shaped from within.
- **"From within" means (a) experience** (raids, war, trade, famine),
  **(b) composition** (minorities and migrants), **(c) internal balance
  of power** (elite and populace with different values; hierarchy sets
  whose count; power shifts with success and crisis). **(d) its place in
  a state** (hegemon, subject, rival) is left emergent, or works through
  the city's dominance.
- **Rural cells carry the lineage's values, with no δ** (U: the
  rural-urban divide is as old as Gilgamesh; urbanites are seen as
  "straying"). Rural people moving into a city pull it back toward the
  lineage.
- **The lineage keeps a pull of its own as well as being the aggregate**,
  through the rural population, mediated by conformity.
- **Rural without δ unless that blocks lineages originating.** Note (C):
  it does not; rural lineages still arise from settling a new region
  (`--settle-drift`), colonies, secession and fusion. Cities add a new
  route (below).

- **Decided later the same day (U):**
  - **Elite and populace:** hierarchy weights the elite against the
    populace; revolts are how a conformist populace reins in a divergent
    elite.
  - **Technology spreads faster than other change**, by proximity,
    cultural similarity and trade.
  - **Lineages can re-merge.** Refined 2026-11-02: true, recorded
    fusion (new lineage, two parents), not requiring similar cultures;
    partial (colonists absorbed into the local lineage while the
    ancestral one carries on); spatial and slow (years of shared rule,
    not mere proximity). See structural.md, "lineage fusion".
  - **A city can be a mix of peoples.**
  - **Administration arises at the city level**; a state inherits from
    the pool of its cities: it starts at the capital's value, and its
    cities' administration rises quickly toward that of its best-run
    city, at a rate set by the state's hierarchy and conformity. If the
    capital is not the best-run city, the state learns from the best and
    deploys their bureaucrats. Hierarchy speeds it; high conformity
    resists it (U): low-conformity cultures adapt better to new
    administration, but are also pulled more easily toward violence and
    other change.
  - **Rulers draw in trait units** with reflection, like `flat_drift`.
  - **No hard density cap**: trade cities should support higher
    densities.

### Proposed (C; the design below accepted, U 2026-11-02)

| Level | Holds |
|---|---|
| People | growth rate, size, lifespan, hardiness, fortress, biome affinity (fixed) |
| Lineage | the values of its rural cells; descent (for Price) |
| City | every cultural trait as lineage value + δ at founding, then its own; technology, administration, guarded techniques, development, resources held |
| State | cohesion, ruler and dynasty, disorder, alliances, wars |

- **Founding:** a daughter city takes its mother city's values (a colony
  carries Corinth, not "the Greeks"); a city founded from countryside
  takes the lineage's.
- **City to city:** influence ∝ contact (travel distance, trade ties,
  same state) x similarity; technology by trade and contact, institutions
  more by rule (open).
- **Rural pull:** toward the lineage, ∝ the share of the city's growth
  from rural immigration x conformity. Cities that grow from within
  drift further.
- **Inside the city:** experience pushes the city that lived it, not the
  lineage; minorities pull it by their share; an elite-populace split
  weighted by hierarchy (form open).
- **City to lineage:** the lineage's aggregate is the population-weighted
  culture of its rural cells and cities; a thriving city's deviations
  spread through migration and influence.
- **Speciation:** a city whose distance from its lineage passes a
  threshold founds a new lineage (cultural speciation from inside).
- **Rulers** draw around the capital city's culture. **Turmoil** and
  administration sit on the state and its cities, never on a lineage
  shared across realms (recoverable disorder, see the rulers batch).
- **Technology dies with places:** a sacked or abandoned city loses what
  only it held; collapse can come from cities falling, not a decay rate.
- **Rural technology:** the lineage keeps a rural baseline (farming,
  fishing, sailing for bands and villages); cities start from it and feed
  it back (form open).

### Trade and the commons (U 2026-11-02; form C)

- Trade is the main cause of urban commoners straying from their rural
  origins: a city's commons move toward its trade partners' commons, ∝
  trade volume / city size, opened by tolerance, resisted by conformity.
  Trade shapes the commons; rule, alliances and diplomacy shape the
  elite.
- Trade experience (directional) stays separate from trade mixing
  (toward partners); watch the two together for runaway divergence.
  Merchant minorities (trading posts) are the demographic channel,
  trade mixing the contact channel; they do not scale off one number.

### Multi-origin cities (U concern 2026-11-02; form C)

- **Composition:** a city's residents are the people of its cell and
  hinterland (`cell_city`), main and minority, as shares by lineage.
  Nothing new is stored; it follows from where people live.
- **Rural pull** goes toward the share-weighted mean of the residents'
  lineages, so a mixed city's commons sit between its origins.
- **Downstream:** each lineage receives a city's influence ∝ its share
  of the city x city size / lineage size.
- **Home lineage:** the plurality lineage (`Clin`), which can change as
  the mix changes. For Price, a mixed city belongs to each lineage by
  its share (fractional nesting).
- **Speciation:** if the commons drift past the threshold from the home
  lineage, that lineage's residents in the city found a new lineage of
  the plurality people; other residents keep theirs. Merging is within a
  people only (peoples are near-species).
- **Conquest:** the conqueror's elite replaces the city's elite; the
  local commons stay. The elite-commons gap x the commons' conformity
  drives revolt, which replaces the separate foreign-rule acculturation
  path.

### To measure

1. Variance by level over time: between cities within lineages, between
   lineages within peoples, between peoples (judge runs on variance, U).
2. Price at two levels: within cities, between cities, between lineages.
3. Where inventions start and how they spread: distance, trade, rule,
   similarity.
4. Technology lost with fallen cities, against what survives elsewhere.
5. Hegemony: in multi-city states, influence over similar cities against
   subjugation of different ones.
6. Rural-urban gap per lineage, and how it varies with conformity.
7. Rural-urban gap per city against its trade volume.

### Open

- What an internal revolt does: the elite overthrown and the city's
  values snapping toward its populace; in a subject city, also
  secession?
- Speciation and re-merging thresholds; Price with merging lineages
  (offspring shared between ancestors by weight).
- How a mixed city is held: a share per people and lineage, with its
  culture = elite + the weighted populace.
- City δ in trait units like the rulers (C: yes).

## Before building: assess and streamline the whole suite (U, 2026-11-02)

The city change rebuilds the core, so the user wants a full assessment
and simplification first ("software's simple"), then the new model.
Plan (C; U 2026-11-02: no constants inventory, no regression harness
against the old model):

1. **Archive** (done 2026-11-02) the current model before any change:
   `archive/v1_2026-11-02/` with `worldsim.py`, the rosters, sites,
   `docs/`, and a note naming the last control runs (`p_seed101-106`,
   `r_seed101-106`, the `ra_`/`rb_` ablations). Revert is then a copy.
2. **Inventory every switch** (82 now) and sort each into: core (always
   on, switch removed), superseded (drop: e.g. `war_motive` under
   `war_v2`, the non-ruler `succession` path, separation's old meaning,
   seafaring under `dispersal`), inert or untested (drop or keep
   experimental), and experimental (keep a switch). Present the list for
   decisions before cutting. Done: [switch-inventory.md](switch-inventory.md).
4. **Restructure the code** (done 2026-11-02: switches folded per the
   inventory, 82 -> 17; code split into `wsim/`; a 4,000-year all-on run
   reproduces v1 byte for byte): one 7,000-line file into modules (world,
   peoples and lineages, cities, states, war, technology, climate and
   land, diagnostics, output). City-level culture wants a city table
   like the lineage table, not dicts.
6. **Clear chaff** (snapshots done: `archive/snaps/`; docs still to
   do, after the city build so they describe it): the 18 `snap_*.py` copies in `sim/` to the archive;
   stale docs (model-description.md's switch list is out of date);
   fold structural.md's changelog and rules/ into one current spec plus
   a changelog.
7. **Profile** (done 2026-11-02, 5,000 yrs seed 101): carrying capacity
   (`Kf`/`K2`) is ~55% of time, called ~145k times, mostly from
   migration and budding; then raids 12%, war deterrence and projection
   9%, technology 8%. A per-tick capacity cache is the obvious first
   speed-up.
8. **Then build the city level**, with the multi-level Price and the
   variance-by-level diagnostics first, so the first runs can be read.

## Does the half-resolution climate field lower population? (2026-11-17, WP1)

Five seeds with the local climate field drawn at half resolution
(`CLIM_LOCAL_COARSE` 2, the default since WP1) ended at a median of 116M
people (86-164M). The same five seeds with the full-resolution field ended
at 147M (108-178M); rank-sum p about 0.15. Urban share, cities ended and
the dragon share of deaths move back with it; all follow population. The field's statistics, and the
drought shares they produce, match. Most likely seed noise, but unresolved.
The default went back to 1 (U, 2026-11-17).
Recheck with a larger batch once WP2's metrics exist (`run-log.md`,
2026-11-17 WP1 stage F).

## Food taken from minorities vanishes (2026-11-17, WP4 stage A; fixed WP4 D)

**Fixed (U, 2026-11-18, WP4 D):** `T` is now worked out per lineage as
proposed below; `taken_capacity` equals `taken`. The text below is as
found.


`Kf` debits a minority's capacity at the rate its people pay (`ff_xo` or
`ext_x`), but `food_flows` works out the take `T` from the main
lineage's capacity only, with a rate blended by the shares of the two
peoples. The minority's payment is never counted and never arrives
anywhere: 89k fe a tick at year 5,000 of seed 101, or 4.5% of the take
(`food.csv` `taken_capacity` against `taken`, 3.7-4.8% from 5,000 to
6,000). Simplest fix (C): work out `T` per lineage, the main lineage
and the minority each on its own capacity at its own rate, and drop the
blend. Not fixed: stage A changes no mechanics.

A smaller leak: food sent to a capital cell where no ruling people
live feeds nobody (`cap_unused`, 1.1% of capital food over the run).

## Make `trade_debit` the default? (2026-11-17, WP4 stage B; decided)

**Decided (U, 2026-11-18):** yes, and carriage port to port. Both done in
WP4 D (structural.md, run-log.md). The text below is as it stood.


Comparison table: run-log.md, "WP4 stage B". With trade food debited:
- population falls by 11% (D5 accepted that);
- urban share falls by a third;
- the largest city loses 30-45%, and largest / 10th falls from 2.3-3.2
  to 1.7-2.6;
- the overall rank-size slope steepens a little;
- states and wars fall by a fifth to a third.

Trade then feeds 3-4% of city food, against about 40%.
- My recommendation (C): make it the default, since it removes food made
  from nothing.
- Do not raise FF_TRADE or TRADE_SURPLUS to restore the top cities
  (GUIDE.md: no targets). The brief's remedies are mechanisms: WP5's
  tribute and conquest income, and WP8's water transport of bulk food.
- One form question first: carriage is now measured capital to capital.
  Most of the traded food (63%) is lost. A port-to-port distance would
  lose less on sea routes.

## Feud and dragons dominate the people account (2026-11-17, WP4 stage C)

`growth.csv` for seed 101:
- feud is 56% of all removals (more than raids and wars together);
- growth forgone under dragons is 1.35 x natural increase.

Both are older rules (C) that the new account makes visible. Neither
was changed. Worth a look when WP5 or WP6 touches violence and dragons.

## WP5 stages B-F: what stage A says (2026-11-18; B decided)

**Decided (U, 2026-11-18):** build B as recommended, item 3 first; the
size classes and other stage A choices stand. Built in WP5 B (`war_odds`,
on by default); results in run-log.md, "2026-11-18 WP5 stage B". The
recording quirk (item 6) is fixed. Items 2-5 stay open: D waits on B's
results; sea adjacency was not put in scope, so it is not changed.

Findings in `run-log.md`, "2026-11-18 WP5 stage A". Recommendations are
mine (C).

1. **Stage B (odds-gated war): build it, item 3 first.** Equal-sized
   states besiege at median odds of 0.02-0.05. 7-9% of the attacker's
   sieges are 1-4 city states against 5+ city states, under 0.1 in
   86-100% of cases. A gate on declaring and on besieging targets
   exactly these. Most one-tick wars, though, are a large state taking a
   one-city state at good odds (0.80-0.86) or by cession, and a gate
   will not stop those. Item 3 (a hopeless defender submits or pays
   tribute before a siege) is the part that would keep one-city states
   alive, as tributaries.
2. **Stage D (yearly step): defer until B is measured.** The clock does
   not cause most short wars (above). Expect D to change only the 27-36%
   of wars that survive their first tick.
3. **Throwaway states are mostly not a war problem.** Cities founded
   outside a state are 15-44% of polities. 95-97% never gain a second
   city, and 70-79% end when their city is abandoned. Ethnic revolts
   live a median of 20 years. Neither WP5 B nor D touches them. Options:
   (a) leave them, since they are one-city states with records;
   (b) a city outside any state founds a polity only above a size or
   cohesion threshold, and is otherwise stateless (this fits stage F's
   camps);
   (c) report them separately in the metrics.
   I recommend (c) now and (b) inside stage F.
4. **Sea adjacency drives war exposure.** It gives a coastal state 10-14
   possible enemies (median) against 1-2 for states that lasted
   millennia, at the same land-neighbour count. Any two coastal cities
   within twice the sailing range count. A narrower rule (once the
   range, or ports only) would change who fights whom a lot. That is
   outside WP5 as written ("Not in this package": what motivates war is
   out, but this is who can reach whom). Decide whether to add it to
   stage B.
5. **Persistent borders: not needed for fragmentation.** 86-92% of the
   largest states' extra land pieces are within sailing range of the
   rest (years 6,000-8,000). Drop the idea unless the 15-45% of states
   with true exclaves matter for the books.
6. **Recording quirk, fix in B:** a one-city defender that cedes its only
   city is recorded as "defender fell" (because `kill_polity` closes the
   war before `cede` does), not "ceded".

## Odds-gated war makes peer wars rarer (2026-11-18, WP5 stage B)

Under `war_odds` peer wars (both sides 5+ cities) are 1.2-1.6% of wars,
against 2.1-2.7%. Wars still end inside one tick 59-63% of the time. Of
those, about a quarter are a one-city defender falling at the first
siege at odds of 0.74-0.85. Seed 103's population is 18% lower and the
cause is unknown (run-log). Worth a look before stage D: whether the
gate centre (ODDS_MID 0.7, C) is too high for peers, and whether a
5-seed batch confirms the population effect. Do not tune ODDS_MID to
restore the peer-war share; decide on the mechanism.

## What stage D must still decide about time (2026-11-18, WP5 stage C)

Stage C wrote the political clocks and rates in years (list in STATUS.md).
Some quantities are counted per event or per tick, and a shorter step
does not convert them:
- **Sieges per step.** `wars_step` lays 1 + floor(2 x logistics) siege
  attempts per war per tick. At a yearly step that would be five times
  as many sieges per 5 years. Either attempts become a rate per year, or
  a siege is given a length in years. This is the main design choice
  for stage D (C: give a siege a length).
- **Per-event effects**: the siege toll (SIEGE_TOLL, 3%), cohesion lost
  per failed siege (SIEGE_COH), submission and ravaging (drawn once per
  siege attempt), capture and sack effects, call to allies. These follow
  from the siege count.
- **"Once per tick" caps**: one sack per war per tick, one cultural spike
  per state per tick (`pevent`), one band per target per tick. The
  per-tick accumulators `revolted`, `sup_win` and `sup_loss` are read
  and reset by culture once per tick. A sub-stepped war must keep adding
  to them, not reset them.
- **Minimum reign** `max(DT, ...)`: one tick. At a yearly step it could
  be one year.
- Diplomacy and rebellions were already written per year (DT x rate);
  their unnamed numbers (alliance break 0.004, formation 0.005, fusion
  0.0025, vassal annexation 0.004 per year) were left as they are.

## Small-state succession: no bursts, and lower late growth? (2026-11-18)

U asked for successions in small states so that a gifted ruler could
make a small state grow fast. In `wp5c_*` it does not happen
(run-log.md): rulers do not affect the chance of declaring, and a
one-city state declares about once in 300-400 years. Options (C):
(a) let the ruler's offense enter the attacker's own reading of the odds
(deterrence) for the attacker only, so a gifted ruler of a small state
picks fights it can win. This reverses U's form of `ruler_mil` (the
talent "does not change their chance of going to war"), so it needs U.
(b) Leave it: bursts then come from long reigns and luck, as now.
Separately, growth in 7000-8000 fell to 0.009%/yr in both seeds with
small-state succession on (0.029 in seed 101 without it). A 5-seed batch
would tell whether this is real before anything is built on it.

## Plague and growth: two links that bias WP6's measures (2026-11-18)

- **Plague reaches only people inside states.** `land.disasters` masks
  the mortality by `cell_pol`, so people outside states (11% at the
  2026-11-16 review) never catch it. Noted by the WP6 brief; not fixed.
- **Plague frequency follows urban population.** The chance per year is
  PLAGUE_P x min(1, urban / 3e6). With slower growth (WP6 stage A) there
  are fewer and later cities, so fewer plagues: 15 in the seed 101
  baseline and 1 at R_SCALE 0.33. That makes the slow-growth settings
  look *less* volatile around the 200-year mean, although recovery from
  a given fall takes longer. A test of recovery alone would need the
  same shocks in each setting, for example branches from one saved state
  with plague forced at one year.

## Small metric problems found at WP6 B (2026-11-18)

- **`created / city food` blows up before cities exist.** In the
  `wp6b_` batch the 1000-2000 value reaches 2.6e13 in one seed: the
  base city boost is divided by city food that is near zero when the
  first city has only just been founded. The measure should be blank
  when city food is below some floor. Analysis only; the sim is not
  affected.
- **The saved states are stale.** `runs/wp1f_s10{1,3}_y{3000,5000}.pkl`
  were made before WP4-WP6. Branch tests from them run the new code on
  an old world (twice the population, more cities). Remake them from
  `wp6b_` settings when a branch test is next needed.

## Epidemics and upkeep (WP6 C, 2026-11-18)

- **Steel near the end again.** With both on, seed 101 reached steel at
  7,340 (5,425 without). If more seeds land after 8,000, that conflicts
  with "steel as the final technology over 8,000 years" (U).
- **Which of the two shrinks the world** (population -17 to -25% at
  8,000, a third fewer 3+ city states) is untested; one run each with
  `--off epidemic` and `--off upkeep` would say.
- **The epidemic tail.** Epidemics linger for decades as a few cells a
  tick in thin country, often up to the 100-year cap (PL_MAXT). The
  deaths there are small, but it means an epidemic can still be "under
  way" when another starts nearby (a city inside one cannot start
  another). If this matters, a floor on density for transmission would
  end them sooner.
- **Plague recovery measure.** `wp6_growth.py` measures each state's
  fall from the epidemic's start year, up to 50 years on. A wave that
  reaches a state decades after it started is measured late or missed.

## Shared cells (WP7 C and D, 2026-11-18)

- **Mixing stays low.** With shared cells on, heads outside their cell's
  plurality people are 2.0-2.6% (2.2% off). Entry into held cells is the
  limit: room is K − 0.9 x overlap x the holders' food, and overlaps run
  about 0.8-0.95, so a full cell has little room. If U wants more mixing,
  the causes to look at (not numbers to tune) are: conquest that settles
  the conqueror's people in captured land (only a 4% garrison now);
  deportation by states (left out of the design); and whether the ruling
  people's state weight (SH_STATE 3) should also cut the subjects'
  resistance to settlers outside the ruler's own state.
- **Routines that still ignore third and further peoples:** none since
  WP15 (2026-11-22), apart from the `minority_pop` record.
- **Cascades not measured:** refugees are not recorded by destination,
  so the brief's stage D measure (displacement followed within 50 years
  by raids or more displacement where refugees arrive) needs a record.
- **No 5-seed batch** for WP6 C or WP7. The current defaults (all on)
  have two seeds behind them (`wp7c_seed101`, `103`).

## WP8: climate fields and the drawn biome map (2026-11-19)

- **D10, decided (U, 2026-11-19).** The climate's biome replaces the
  drawn one everywhere in `world_v2` (`syn_biome`), which is the default
  world. The southern belt was "probably an old error". The report that
  led to it, for the record: the climate the build derives
  reproduces only 56% of the drawn biome map on average over biomes; by
  area, 47% of land agrees. The main conflict is coherent:
  - the southern supercontinent has jungle and temperate forest at
    40–75°S, beside the polar tundra, with desert at 20–40°S;
  - 16.6M km² of temperate forest lies at 0–30°N.

  [world-data.md](world-data.md) has the table, and the map is
  `../gis/qa/climate_biome_disagreement.png`.
  - Refit (U, 2026-11-19): the parameters now take physical values, with
    only P0 calibrated to 1.0 m/yr of global rain; agreement with the
    drawn map is reported, not fitted.
  - PET is Penman–Monteith since 2026-11-20 (U), and the rain-out floor
    under sinking air (Z_BASE) was lowered from 0.25 to 0.1 the same day
    (U). That gave desert 22.8M km².
  - The monthly circulation (ITCZ migration and land monsoon), gyre
    currents and cross-edge exchange came the same day (U). With them
    desert is back to 5.5M km²: the land monsoon wets the subtropics to
    about 20° (world-data.md has the ablation).
  - Open: whether the monsoon's reach over land (ITCZ_LAND 18°) is right
    for these continents. It is Earth's value for an all-land column;
    the drawn map has far more desert. Not changed.
  - The monsoon westerly and rain timing came the same day (U). Rain
    timing turns seasonally wet jungle and winter-rain forest into
    grassland (+4.6M km²). The westerly moves July rain −20% to +15%
    within its zone but changes no biome area: monsoon rain here comes
    mostly with the meridional flow. Open: whether that meridional
    supply (V_MER 0.3) is too strong for the zonal wind to matter.
- **Closed-basin lakes are sized** (U, 2026-11-19): a closed basin's lake
  covers only what its net evaporation needs to balance the inflow,
  lowest cells first; the rest of the basin is alluvial fill. Lake cells
  on `world_v2`: 931 (2,249 before). `world.gpkg` on disk predates this.
- **Ecotones** still use distance to the nearest other biome. Now that the
  biomes come from the climate, the aridity field could say directly
  which cells sit near a threshold. Not changed.
- **Tools that build a World** (`figures.py`, `timeline.py`,
  `landmasses.py`, `landmass_report.py`) load the default world, now
  `world_v2.gpkg`. The run loader (`wsim/runio.Run.W`) uses each run's
  world since WP8, but these tools draw an older run on the new world.
- **Sites:** `sites_v3.json` is placed on `world_v2`
  (`make_sites.py --v3`) and is in the standard command. `sites.json` and
  `sites_v2.json` stay as they were, made on `world.gpkg`.

## Feud costs more than its grounds since D7 (2026-11-21, WP11 B)

`FEUD_K`'s comment in `params.py` assumes growth of 1.2-2% a year,
which would settle land at 0.65-0.8 of capacity at violence 0.99. Since
D7 (R_SCALE 0.5), growth near capacity is about 0.8-1%. So the same
FEUD_K costs about twice that share. Feud is the largest single cause
of the half-fill: 0.09-0.33 of heads per century (WP11 brief, "Stage B
part 1 results"). Undecided (U): rescale FEUD_K to its stated grounds,
leave it, or take it up under WP13 (how far state order reaches).
