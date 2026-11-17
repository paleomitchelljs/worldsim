# Open questions and known issues

Revised 2026-11-01. Questions answered or overtaken that day were
removed; decisions are recorded in [structural.md](structural.md)
("Changes of 2026-11-01"). The previous version is
`archive/open-questions_pre_1101.md`.

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
  seldom met.
- **Elite model.** Elites grow whenever crowding exceeds 0.75, which
  mature states usually do; cycles or a steady rise in revolts?
- **Floodplain cities get swamp defence**, through wetness on alluvial
  lowland.

### Economy and technology
- **Innovation, seafaring and trade have no cost of their own.**
- **Herding at low farming** is never worse than foraging, which loosens
  the early farming penalty on poor land.
- **Technology is never lost** as knowledge (with `supply`, use lapses
  without ore or cities).
- **Low-innovation peoples reach steel** through long contact; borrowing
  runs at (0.3 + innovation), never zero.

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

### Proposed (C)

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

### Open

- Which forms for (c), the elite-populace split: two value sets per
  city, or one δ that hierarchy weights?
- Does technology spread by the same rule as dispositions?
- Speciation threshold, and whether lineages can re-merge.
- Administration per city (the state reads its capital's) or per state
  only. Per city is what makes subject cities matter for hegemony.

## Before building: assess and streamline the whole suite (U, 2026-11-02)

The city change rebuilds the core, so the user wants a full assessment
and simplification first ("software's simple"), then the new model.
Plan (C; U 2026-11-02: no constants inventory, no regression harness
against the old model):

1. **Archive** the current model before any change:
   `archive/v1_2026-11-02/` with `worldsim.py`, the rosters, sites,
   `docs/`, and a note naming the last control runs (`p_seed101-106`,
   `r_seed101-106`, the `ra_`/`rb_` ablations). Revert is then a copy.
2. **Inventory every switch** (82 now) and sort each into: core (always
   on, switch removed), superseded (drop: e.g. `war_motive` under
   `war_v2`, the non-ruler `succession` path, separation's old meaning,
   seafaring under `dispersal`), inert or untested (drop or keep
   experimental), and experimental (keep a switch). Present the list for
   decisions before cutting.
4. **Restructure the code**: one 7,000-line file into modules (world,
   peoples and lineages, cities, states, war, technology, climate and
   land, diagnostics, output). City-level culture wants a city table
   like the lineage table, not dicts.
6. **Clear chaff**: the 18 `snap_*.py` copies in `sim/` to the archive;
   stale docs (model-description.md's switch list is out of date);
   fold structural.md's changelog and rules/ into one current spec plus
   a changelog.
7. **Profile**: runs take 3,000-6,800 s; find the hot spots before adding
   a city level.
8. **Then build the city level**, with the multi-level Price and the
   variance-by-level diagnostics first, so the first runs can be read.
