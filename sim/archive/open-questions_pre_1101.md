# Open questions and known issues

## Outcomes to tune later (after the model settles, U)

- **Snake folk dominate.** They hold 32–51% of world population in runs
  91–94. The levers are the head start, statecraft (reach) and cohesion.
- **Ogres conquer heavily.** Since they gained cities they clear 800–1,500
  cities per run, from ×20 combat worth plus violence 0.9.
- **Fusion is narrow.** Cross-people fusion happens only between Humans and
  Lizardfolk, the only pair that both tolerate.

## Model gaps

- **Technology is never lost** (with `--off supply`). With `supply` on, metal
  use lapses without ore or cities, and administration and metallurgy decay
  without cities; knowledge of a stage is still kept for good.
- **Floodplain cities get swamp defence**, through wetness on alluvial
  lowland.
- **The terrain effect hasn't been isolated.** Runs 91–94 changed starts,
  terrain and rivers at once. Measuring it needs the same seeds with terrain
  switched off.
- **Kin wars rise with lineage drift.** About a quarter of logged major wars
  are between lineages of the same people. `SIM_SAME_SCALE` controls this.
- **Low-innovation peoples reach steel** through long contact. The
  borrowing rate is still (0.3 + innovation), not zero.
- **Giants are no longer marginal.** Wandering placement moves most
  founders out of tundra. That is accepted as the rule's outcome; changing
  it would need a roster change.

## Data

- Strips in the wetness, relief and alluvial inputs around 100–120°E,
  25–35°S ([world-data.md](world-data.md)).

## Draft structural mechanics (2026-10-29, C)

See [structural.md](structural.md). All numbers are untuned proposals.

- **Accept or revise each mechanic.** The switches let each be judged
  against `--off` runs on the same seeds.
- **Steppe stand-in.** Aridity inside a biome is taken from distance to the
  coast because `syn_runoff_m_yr` is one value per biome. A real moisture
  field in the world build would replace it.
- **Herding at low farming** is never worse than foraging. That loosens the
  early farming penalty on poor land.
- **Elite model.** Elites grow whenever crowding exceeds 0.75, which mature
  states usually do. Whether this gives cycles or just a steady rise in
  revolts needs checking in the runs.
- **Innovation, seafaring and trade** still have no cost of their own.
- **Results of the first runs** (`structural_seed91`/`92`, against
  `terrain_seed91`/`92`):
  - **Balancing doubles standing alliances** (0.7–0.9 per state against
    0.35). 71–77% of new alliances form only because of it. But with
    `--off balance` (`nocap_nobal_*`), wars, captures and lifespans barely
    change, so balancing does **not** explain the longer state lives (mean
    about 800 years against 600 for states of 3+ cities). The cause is
    among `fiscal`, `unrest`, `succession`, `costs` and `vassals`; not
    isolated yet. Captures fall from about 8,500 to 2,600–3,000 with the
    mechanics on, which fits a conquest-side cause.
  - **Technology runs about 1,000 years behind baseline.** Steel is never
    reached. The suspects are the cohesion cost on borrowing, smaller
    states (fewer cities per lineage, so slower invention), and bronze
    lapsing when tin is cut off (32 and 97 lapses logged). Not isolated.
  - **City rank-size is too flat** (slope −0.3; reference −0.6 to −1;
    largest city only 1.2–1.4x the 10th). Dropping the cap (`nocap_*`) did
    not change it, so the cap was not the cause. A city is one cell whose
    K is bounded by its area, local farming and a trade boost of at most
    4.5x. Nothing gives large cities increasing returns or lets them draw
    food from their hinterland. This is the structural gap to address.
  - **Selection within peoples is small.** Price selection terms are about
    0.01–0.03 per trait over the run. Transmission is larger (expansion
    +0.09 in both seeds), and world-level change is mostly selection
    between peoples. Note that differential success of daughter lineages
    falls in the transmission term, because daughters are counted under
    their ancestor.
- **Vassalage is rare.** About 80–105 submissions per run against
  2,600–3,000 captures. None happen before year 2000; standing ties average
  3–4 (at most 16–28). The 3:1 threshold is applied after terrain and
  capital defence (1.4 x terrain x 1.25), so it is seldom met.
- **Within-people splits.** With the mechanics on, breakaways are single
  cities (1.2 cities per revolt against 1.6). States stay small (late
  cities per state 1.0–2.1 against 1.0–4.6 with everything off), and
  cultural spread inside each people is higher (0.15–0.28 against
  0.10–0.16). Acculturation pulls frontier lineages toward different
  neighbours, so it raises spread inside a people rather than lowering it.
- **Cities end only by war** (`cities_*` runs). 92–98% of city ends follow
  a clearance within 50 years. Drought, plague, land wear and climate
  shrink cities, but never end one: K is unchanged, so they regrow. Sites
  are never empty; a "ruin" is a city reduced to a village and re-founded
  after a median 110–140 years. Nothing makes a site worse for a city
  after it falls. River shifts and destroyable improvements are the
  planned fixes.
- **Climate and landscape runs** (`climate_*`, `landscape_*`):
  - **World-wide dry spells are severe.** One in seed 91 put 75–90% of
    people below −1.5 sd for about 380 years and cut population 25%. The
    real 4.2 ka event was not uniform across the world; a world-wide share
    of 25%, or the depth, may be too high.
  - **Great droughts are logged 40–60 times per run** (about one a
    century); the threshold may be too low to mean "great".
  - **River changes rarely touch cities** (1–4 city ends per run). Few
    cities stand on the 119 prone cells, and a city that loses its river
    keeps its farmland. Whether to widen the prone set (smaller rivers,
    deltas) is open.
  - **Settlement is not patchy.** 95–97% of land cells are occupied in every
    setting, because foragers and herders fill all land with K over a few
    dozen. Roads concentrate density (road cells about 7x the mean) but
    cannot produce empty land between clusters. Patchiness would need a
    minimum viable settlement, or a cost to living far from others.
  - **Ruin sites are never empty.** Improvements make cities slower to
    come back, but a "ruin" is still a village on the site.

## Dragons: noted for after the first runs (2026-10-29)

- **Who can ally (U).** At least some Lizardfolk, and perhaps some Elves
  or Snake folk, should be able to reach the alliance threshold through
  variation in tolerance within the people.
  - In `landscape_seed91` (no dragons) only 10 of 430 Human lineages ever
    reached tolerance 0.75. The highest elsewhere were Lizardfolk 0.61,
    Dwarves 0.54, and Elves and Snake folk about 0.40.
  - Even Humans average 0.47 across lineages, because tolerance falls
    under selection.
  - So with a fixed bar of 0.75, only Humans ally. Fixing that needs a
    lower bar, wider variation within peoples, or dragons that vary (next
    item).
  - The current cultural traits and the amount of variation within peoples
    are not fixed; greater variation within peoples may come later (U).
- **Dragons vary (U).** Each dragon gets its own tolerance, violence and
  strength. A possible form (C): alliance when the lineage's tolerance plus
  the dragon's tolerance clears a joint bar. Then a very tolerant dragon
  could ally with a Lizardfolk lineage near 0.6. The dragon's strength
  would scale its kill rate, the ward size against it, and its value as
  an ally. Its violence would set the slay/drive-out odds and its own kill
  rate. To be done after the first dragon runs are read and tuned.

## Dragons: first runs (2026-10-29)

- **Alliances never happen** (1 in four runs). The bar of 0.75 is not the
  only reason. Humans' population-weighted tolerance falls from about 0.85
  at the start to 0.70 by year 1000 and 0.40–0.49 by 6000, *with or
  without dragons*. By the time Humans have states and warded towns
  (year 1000+), almost no Human lineage clears 0.75.
  - The fall in tolerance is an existing feature of the model, not a
    dragon effect. It is likely selection plus acculturation toward
    intolerant neighbours; the Price decomposition in `price.csv` would
    say which.
  - Both changes the user noted (variation in dragons, wider cultural
    variance) bear on this.
- **Body size decides who wins.** Ward size divides by combat worth per
  head:
  - Giants need about 100 heads and Ogres 150, so they are nearly immune;
    they take over much of the urban world.
  - Elves (lowest growth) nearly vanish; Goblins (size 0.35) and Dwarves
    (0.6) suffer.
  - This follows from the user's rule (strength sets the ward size), but
    the size scaling (linear in combat worth) is C. A square root or
    similar would soften it.
- **Patchiness: some, not much.** Near-empty land rises from 3–11% to
  8–20%, but 86–95% of land is still occupied. Small bands are seldom
  found, so thin foraging populations persist under dragons, as the rule
  intends. Dragons take the middle densities, not the occupancy.
- **Dragons hold the margins.** By year 6000 they remain on the polar
  fringe, in deserts and in thinly held interiors: wild land is where
  people are sparse.

## Cultural traits: proposed additions and a redefinition (2026-10-29)

- **To add (U: the user favours these four; C: the mechanisms).**
  - *Hierarchy:* how steep society is. Splits extraction from statecraft:
    elite growth, tribute and the unrest of the hungry follow hierarchy;
    administrative reach stays with statecraft.
  - *Proselytism:* active recruitment into the people's identity, a route
    for a culture to spread besides contact and conquest.
  - *Patience:* investment for the long term. Sets the building rate of
    roads, improvements and granaries (now set by administration).
  - *Conformity:* fidelity of transmission. Sets mutation at lineage
    splits and resistance to acculturation; maps onto the transmission
    term of `price.csv`.
- **Maybe (U: open to it, unsure it differs from tolerance).** *Trust
  radius:* how large a group trusts itself before splitting along
  kin lines. It acts inside a people (fission scale, contested
  successions); tolerance acts between peoples. Its overlap is more
  with cohesion than with tolerance.
- **Separation, redefined (U).** A high-separation people can be tolerant,
  touching, overlapping and trading with others, yet live at low density.
  - The code does not do this now. Separation:
    - keeps a people's moves and budding away from foreign neighbours;
    - raises raids (x (1 + sep));
    - raises war on foreigners (x (1 + 1.5 sep));
    - raises clearance (∝ sep x violence x (1 − tol));
    - raises expulsion of minorities (∝ sep x (1 − tol)).

    So it is mostly hostility, and overlaps low tolerance.
  - Proposed (C):
    - separation sets a people's preferred density, a share of K;
    - the people buds and moves out once a cell passes that share;
    - few of its cells reach city density;
    - the hostile effects move to (1 − tolerance) and violence.
  - The roster's separation values were set under the old meaning and
    would need resetting (Giants 0.85, Trolls 0.80, Ogres 0.75, Snake
    folk 0.70, Dwarves 0.65).

## Dragons: second draft (2026-10-29)

- **Alliances are still almost absent** (1 in four runs). The joint bar
  (mean of the two tolerances at least 0.75) cannot be met once a people's
  tolerance has fallen. Human lineages are near 0.45 by the time they hold
  warded towns, so they would need a dragon above 1.0. The binding
  constraint is the fall in tolerance inside peoples, not variation among
  dragons. Wider cultural variance (U: later) or a look at why tolerance
  falls (Price decomposition) comes first.
- **Dragons evolve stronger** (mean strength up about 15–20% over the
  run). Strong dragons are both harder to slay and harder to confront, so
  selection on dragons works against people. Tolerance and violence
  barely move: slaying odds rise with a dragon's violence and fall with
  its strength, so strength is what selection sees.
- **Dragons may now be too strong.** Strength scaling, body size^0.75 and
  separation compound, leaving about 320 cities at year 6000 against
  about 850 without dragons. Half kill (0.01) gives about 480. It is the
  candidate default.

## Mixed settlement (U, for later; 2026-10-29)

- **Loosen the rule that a cell holds one people (U).** Trade cities,
  subjugated peoples and truly mixed settlements should be possible, even
  if peoples cannot interbreed and the mix may not be stable.
- **What exists now:** one minority people per cell, up to 20% of its
  capacity: a conqueror's garrison, merchants from trade partners, the old
  people after a raid takeover; expelled at a rate set by intolerance.
- **A general form (C):** a cell holds shares of several peoples, each
  growing on its own (no interbreeding) from a shared capacity.
  - **Mixing** would be held up by tolerance, trade and a state's
    protection, and pulled apart by intolerance, competition for the same
    capacity and expulsion.
  - **Stability** would then be an outcome, not an assumption: trade
    cities stay mixed while trade lasts; subjugated peoples persist as a
    lower layer under hierarchy.
  - **Cost:** most per-cell arrays (people, lineage, population, ward
    size, raids, clearance) would need a people dimension. It is the
    largest refactor so far.

## Dragons as a growth cut: a trap for everyone else (2026-10-29)

- **The trap.** Under one dragon, a cell's growth rate is r − 0.036 x g(n).
  For a people with r = 0.024 (Humans), that reaches zero where
  g(n) = 0.67, about 300 people in a cell. The ward size that ends the
  hunting is 3,000 (stateless, no metal; 1,000–1,500 with bronze and a
  state). So those peoples cannot grow from under a dragon to the size
  that wards it off.
- **Escape is closed off too.** Only dragon-free land lets a cell grow
  past the ward size. Dragons breed into any site with no warded cell in
  reach, so free land is refilled before a slow people can densify there.
- **Result (bal3):**
  - only Frogloks and Goblins reach ward sizes in numbers, and with
    innovation 0.10 they never reach metal;
  - no people casts bronze in 6,400 years;
  - the slow peoples persist as small bands.
- **Ways out (C, for the user to choose):**
  - dragons do not settle where people are already dense (a site needs
    low human density, not just no warded cell), so refuges can grow;
  - a ward size below the trap ceiling (a few hundred stateless humans),
    so towns can shed dragons;
  - a smaller cut;
  - fewer dragons at the start.

## After toning down (bal4, 2026-10-29)

- **Metal has almost disappeared.** One bronze casting in four runs (Dwarves,
  year 5050), against bronze around 3000–3700 and iron around 4700–5200
  with the old roster and no dragons.
  - Under the rebalance only Dwarves have high innovation (0.85), and they
    are few: expansion 0.10 and a tundra/forest range.
  - Humans are now moderate (0.50); before they were 0.85.
  - Metal also needs ore in hand (`supply`) and enough cities.
  - Likely fixes: more innovation somewhere, or check whether ore access
    or dragons hold metal back.
- **Dragons fade.** About 3,700 at the start, 630–780 at year 6000. Births
  (about 3,500) do not replace deaths of age (about 5,500), let alone the
  slain. With breeding at 1/1,500 per adult per year and nesting only in
  very sparse land, the dragon population cannot hold steady. A rate
  near 1/1,000 might hold it level in sparse regions.
- **`--dragon-shun` adds little** now that young dragons nest only in
  sparse land. It stays off.
- **No alliances.** Human lineages average tolerance 0.5 and dragons 0.4,
  so the joint bar of 0.75 needs a rare pair (e.g. a 0.9 lineage with a
  0.6 dragon) where a state meets a dragon.

## What holds metal back, and why tolerance falls (2026-10-29)

- **Metal.** In bal4 almost no lineage reaches metallurgy 1.0, the bronze
  threshold; ore is not the binding gate. Metallurgy grows ∝
  innovation², and the innovation actually carried by lineages falls well
  below the roster means.
- **Acculturation is the cause, for innovation and for tolerance.** From
  `price.csv` (sum over the run, per people), the change sits almost
  entirely in the transmission term. Selection within peoples is small
  and, for innovation, slightly positive.

  | Run | Trait, people | Start → end | Selection | Transmission |
  |---|---|---|---|---|
  | bal4 | innovation, Humans | 0.55 → 0.36 | +0.06 | −0.26 |
  | bal4 | innovation, Dwarves | 0.85 → 0.51–0.59 | | −0.30 to −0.35 |
  | bal4 | innovation, Goblins, Ogres, Trolls | rise | | +0.09 to +0.17 |
  | landscape | tolerance, Humans | 0.86 → 0.41 | +0.07 | −0.52 |

  So acculturation pulls every people toward a common value (about 0.3)
  and erases the differences the roster sets. Tolerant peoples lose
  tolerance fastest, because tolerance speeds acculturation. This settles
  the earlier question of why tolerance falls.
- **Between peoples,** the world mean of innovation falls by selection
  (−0.16): the low-innovation peoples (Frogloks, Goblins) grow most.
- **Candidate fixes (C):**
  - a much weaker pull across peoples than within one (peoples are
    near-species);
  - a lower ACC overall;
  - acculturation that moves only toward the more advanced, i.e. borrowing
    skills rather than adopting temperament.
- **Test runs** `metal_noacc_seed91` (acculturation off) and
  `metal_nosupply_seed91` (ore rule off) check this.

## Bronze is blocked by ore geography (2026-10-29, C)

See run-log, bal5 and metal tests. No land cell has copper and tin
within 120 km, so bronze needs a strong contact holding the missing ore.
Options: tin by trade over the trade network (as historically, tin moved
thousands of km); a wider radius; or more ore sites in the world data.
Separately, idle metallurgy decay under `supply` outruns invention for
stateless lineages. Open for the user.

## Conquest motive (2026-10-29, U asked)

Nothing makes a people want to rule others rather than raid or clear
them. Under discussion: one trait vs a combination of violence,
statecraft and proselytism.

Update (2026-10-29): U chose tin by trade; `ore_trade` added. bal6, before
ore trade, already reached bronze once per seed (years 4490, 5925).

## Goblin boom under dispersal (2026-10-29, C)

In bal6 Goblins rose from ~12M to 33–45M. Likely cause: their expansion
0.7 now drives sea voyages (their seafaring was 0.2). Not yet checked.

## Experience flattens culture (2026-10-30, C)

econ1/econ2: trade, peace and plague reach every people, so experience
pushes all peoples the same way (tolerance up, violence down, conformity
up). Cutting the rates slows it but does not stop it. Options: responses
that depend on the culture already there (path dependence, so
experiences pull peoples apart), a further rate cut, or a weaker
hardship → conformity link (plague is frequent). Open for the user.

## Big-bodied peoples collapse under the economy switches (2026-10-30, C)

Ogres 3.7%, Giants 0.4%, Trolls 1.0% of food-equivalents in econ2
(econ1 off: Ogres 15%). Likely domestication (innovation 0.2 → slow
packages, farms at half yield) and craft (0.1 → nothing to trade). Open.

Update (2026-10-30, exp2): with forces both ways the conformity ratchet
is gone (world conformity 0.37). The loops now have two stable states
(tipping points for violence ~0.35, trade ~0.3, tolerance ~0.2), but
mixing between peoples erases the differences: with `--off
acculturation` tolerance, trade, cohesion and hierarchy keep their
spread between peoples; with it on, all converge. Violence converges
either way (attacker and defender share a war). Open: how strongly
should peoples mix with each other?

## Tolerance converges through trade; alliances saturate (2026-10-30, C)

reg4 (8000 yrs): every people ends at tolerance 0.61–0.75 and is still
rising. Price decomposition: experience is the main term (+0.1 to +0.25
per 2000 yrs after year 4000); mixing matters only for Trolls, Ogres
and Giants; selection matters for Goblins. Cause: state trade volume
(sum of ties, capped 1.5) sits at 1.1–1.4 for every people by 8000, so the
trade push (0.0005 v) outweighs war, hardship and raids everywhere.
Experience balance points 0.69–0.91. Two reinforcing loops: tolerance →
accept → ties → trade volume → tolerance; tolerance → alliances → allies
cannot fight → less war → tolerance.

Alliances: form at 0.025 × accept(0.8) × (0.3 + tie) per tick, break at
0.02 × (1 − accept) × (1 − threat); allies cannot attack each other and
help defend at 0.35 × strength at no cost. With tolerance ≈ 0.72,
same-people alliances almost never break; cross-people pairs settle
around 75% allied. Seed 101: ~30,000 alliances formed, a handful broken;
at year 7000 about six allies per state. Open for the user.

## Peoples converge again, now towards violence (batch1, 2026-11-01, C)

In batch1 the 2026-10-30 batch reverses the direction of convergence but
does not stop it. Among lineages living on W at year 8000, traits spread
as much within peoples as between them; every people sits at violence
~0.75, separation ~0.85, tolerance ~0.3. Worldwide, Elves go from
violence 0.2 to 0.7 in 2,000 years after contact. Starting culture no
longer predicts end culture. A likely loop: war and revolt exposure
raise violence and separation; these raise war chance and revolt
hazard; and rebel city-states are swallowed at once, giving more war
exposure. Revolts and wars per millennium rise through the run without
levelling off.
Options (open for the user): give experience a pull back towards each
people's baseline (a heritable temperament that sets the point traits
relax to); make exposure shift traits less where the culture already
disagrees (path dependence, as for tolerance); or cut the revolt-
experience and war-exposure rates.


## One-tick population spikes (found 2026-11-01, C) — FIXED 2026-11-01

Cause: logistic growth with a negative rate (dragon cut above r) repels
from K. Fixed in `logistic()`; none in the fix1101 runs.

`pop_<people>` in timeseries.csv jumps for a single 5-year tick and falls
back the next: 2-13 times per people per run, mostly Goblins and
Frogloks, from x1.3 up to x20 (batch1 seed 104 Frogloks, year 3360) and
x56 (reg4 seed 103 Goblins, year 6850). Present in reg4 and bal7 too,
so not from the 2026-10-30 batch. `people_summary` is a plain sum of
`pop`, so the cell populations themselves spike at the point the tick is
recorded. Not yet traced; if the spike is real during the tick, it may
feed war strength, city founding or settlers in that tick.
