# WP11: farming density on open land

**Goal.** Grassland and forest that fill with farmers and herders once
farming has had time to spread, where the land and the technology allow.

**Evidence** (`wp8m`, year 8000; measured 2026-11-21).
- Settlement spreads fast, then stops: 45-55% of land by year 2000,
  81-85% by 5000, and 87-88% from year 6000 on. The 12% never settled is
  almost all tundra. Almost nothing is abandoned.
- Settled land is thin:

  | Biome | Area (M km²) | Median people per km² |
  |---|---|---|
  | Jungle | 28 | 0.4-0.6 |
  | Temperate forest | 26 | 0.12-0.14 |
  | Grassland | 38 | about 0.1 |
  | Desert | 9.5 | 0.03 |

- For scale (C, from memory): hunter-gatherers 0.01-0.1 per km², early
  farming regions 1-10. Most grassland and forest sits at forager
  density after 8,000 years; only the jungle river belts and a few cores
  reach farming density.
- Candidate causes in the rules (C, not yet traced):
  - the steppe cut: rain-fed farming on grassland and desert falls
    away from 400 to 1,600 km from the coast (STEPPE_KM);
  - herding density (HERD: grassland 0.45);
  - herding at low farming is never worse than foraging, which loosens
    the early farming penalty on poor land (open-questions.md);
  - biome affinity and how fast farming and metal free a lineage from it
    (`land.adapt`, BIOME_K, BIOME_ADAPT);
  - climate yields (`farm_clim`, `herd_clim`) on `world_v2`.

Read first: `wsim/land.py` (`Kf`, `K2`, `ltab`, `adapt`), `wsim/geo.py`
(capacity layers, `herd_density`), `docs/rules/population.md`,
`docs/world-data.md` (yields).

## Stage A: trace (records only)

1. For each biome, split capacity at year 8000 into its factors: soil,
   climate yield, steppe cut, elevation, affinity, technology, and
   herding against farming. Write the table and a capacity map at 8000.
2. Compare where people are against where the capacity is: is thin
   land thin because capacity is low, or because no farming lineage
   has reached it?
3. Report which factor holds each biome down. No rule changes.

## Stage B: fix (needs U)

From stage A, propose the change with physical or historical grounds
for each factor that is out of line. Set no density target: the
reference numbers are for reporting, not tuning. Sanity run, then a
5-seed batch; report the shift in peoples' shares.

## Not in this package

- Climate or biome changes (the physical model is settled, U 2026-11-21).

## Stage A results (2026-11-21)

Tool: `tools/wp11_trace.py` runs the Sim in memory (no run files) and
splits each occupied cell's capacity into land.K2's factors for its main
lineage at year 8000. Tables: `baseline/wp11a_trace_seed101.md`,
`baseline/wp11a_trace_seed103.md`; map: `baseline/wp11a_capacity_seed101.png`.
Code as `wp10c`; seed 101 reproduces `wp10c_seed101` (63.1M).

| Biome | People per km² | Capacity per km² | Fill | Best capacity per km² | Sod | Herding wins |
|---|---|---|---|---|---|---|
| Jungle | 1.3-1.8 | 2.4-3.1 | 0.53-0.57 | 4.9-5.3 | - | 11-12% |
| Temperate forest | 0.39-0.57 | 1.0-1.1 | 0.39-0.52 | 2.2-2.5 | - | 20% |
| Grassland | 0.25 | 0.60-0.64 | 0.39-0.42 | 1.65 | 0.37-0.38 | 70-75% |
| Desert | 0.14-0.18 | 0.29-0.31 | 0.48-0.58 | 0.52-0.57 | - | 76-81% |

"Fill" is people over raw capacity (before what states take). "Best" is
the capacity the most developed lineage of any people would have there.

**What holds grassland and forest down:**

1. **The peoples who hold them have no metal.** Goblins hold about half
   of all grassland and temperate forest, Humans a fifth of grassland.
   At year 8000 neither has bronze in any lineage (Goblins: agri
   0.70-0.73, metal 0.03-0.11). So:
   - sod stays at SOD0 (0.35): the plough barely works on grassland;
   - tools stay at 1;
   - herding beats farming on 70-75% of grassland.

   The most developed lineage elsewhere (Snake folk, Elves, Dwarves:
   94-96% with metal) would have **2.2-2.7 times the capacity** there.
   **This is the largest factor.** Metal does not spread to the
   grassland peoples in 8,000 years. Goblins' innovation is 0.1, and
   borrowing runs at (0.3 + innovation).
2. **Every biome sits at about half its raw capacity** (fill 0.39-0.58),
   jungle included. This is not specific to open land. The candidates,
   not traced here:
   - what states take (rent, tax, army);
   - shared-cell competition;
   - devastation;
   - lag behind growing capacity.
3. **Land factors are not the cause.**
   - The steppe cut is 0 under `climate_fields`; aridity replaced it.
   - Climate multipliers on rain-fed farming are 0.9-1.0.
   - The crop-package factor is 0.67-0.73, as in jungle (0.77-0.91).

**So thin grassland is mostly a technology-spread question** (WP14:
borrowing; WP10/WP13: who holds the land), with a uniform half-fill on
top. It is not mainly a land rule.

## Stage B (needs U), revised by stage A

Proposals for U before any change:
1. **Trace the half-fill** (records only): split pop/K into the state's
   take, army, shared-cell overlap, waste and growth lag.
2. **Metal spread to low-innovation peoples:** whether the sod and
   tools gap should close by contact (borrowing between peoples, WP14),
   or whether Goblins without metal is intended.
3. **Herding density** (HERD grassland 0.45) only matters while farming
   is held back by sod. Leave it until 2 is settled.

## Stage B part 1 results: the half-fill (2026-11-21)

Tool: `tools/wp11_trace.py` (extended, records only). At year 8000 it
splits each occupied cell's land capacity (raw K with no drought and no
devastation) into the steps `grow` takes down to its own k, and over
the last 1,000 years it keeps a per-biome account of heads by phase and
deaths by cause, plus fill every 500 years. Tables:
`baseline/wp11b_halffill_seed101.md`, `baseline/wp11b_halffill_seed103.md`;
chart `baseline/wp11b_halffill.png`. Seeds 101 and 103 reproduce
`wp10c` (63.1M, 72.8M main rows).

Shares of land capacity at year 8000 (range over seeds 101 and 103):

| Biome | Fill | Below own k | Separation | States, gross take | States, sent back | Other rows eat | Devastation, drought |
|---|---|---|---|---|---|---|---|
| Jungle | 0.53-0.57 | 0.37-0.43 | 0.02 | 0.07-0.10 | 0.05-0.06 | 0.01 | 0 |
| Temperate forest | 0.39-0.52 | 0.45-0.56 | 0.03 | 0.04 | 0.02-0.04 | 0.01 | 0 |
| Grassland | 0.39-0.42 | 0.49-0.51 | 0.07 | 0.03 | 0.02 | 0.01 | 0 |
| Desert | 0.48-0.58 | 0.34-0.45 | 0.05 | 0.06-0.07 | 0.05-0.06 | 0.01-0.02 | 0 |
| All occupied | 0.50-0.51 | 0.43-0.44 | 0.03 | 0.06-0.07 | 0.04-0.05 | 0.01 | 0 |

**What holds every biome at half:**

1. **Population sits below its own capacity**: 0.34-0.56 of land
   capacity, nearly the whole gap. The other steps are small:
   - states take 3-10% gross, but most comes back to capitals and
     cities in the same biome (net 0-2%);
   - other peoples' rows eat 1-2%;
   - separation 2-8% (most on grassland);
   - devastation and drought are 0 at year 8000.
2. **It is a steady state, not a catch-up.** Over 7000-8000, natural
   increase per century is 0.31-0.83 of heads. Recorded deaths take
   most of it back: 0.29-0.66 per century, in this order:
   - feud 0.09-0.33 (the largest cause in seven of the eight
     biome-seeds);
   - raids 0.07-0.21;
   - plague 0.03-0.12;
   - hunger 0.01-0.04;
   - war deaths (sack, siege, ravage, expelled) under 0.02.

   With a steady death rate m, logistic growth settles at
   p/k = 1 - m/r. Here m is about 0.3-0.6% a year, and r is about
   0.8-1% a year (back-calculated from grow's net and fill). That
   gives about half. Dragons lower r further: growth forgone was
   0.05-0.34 per century, most on grassland and forest (0.26-0.34).
3. **Fill creeps up over time** (0.15-0.25 at 1000, 0.3-0.45 at 5000,
   0.39-0.58 at 8000). Jungle and desert gained most in the last
   millennium, which fits states spreading: feud stops where an
   ordered state keeps the peace (`feud`: DT x FEUD_K x f x (1 -
   order)).

**So the half-fill is mostly how much violence there is outside
ordered states** (feud, then raids), with plague and dragons on top.
What states take, shared cells and devastation are not the cause. It
is not specific to open land. Proposals for U (C): none needed for
WP11. If it should change, the place is FEUD_K, or how far state order
reaches (WP13). Feud's form is U (2026-11-02, violence carries an
internal cost) and its numbers are C. Its comment in `params.py`
assumes growth of 1.2-2% a year, giving 0.65-0.8 of capacity at
violence 0.99. That was before D7 (2026-11-18) halved growth
(R_SCALE 0.5). At today's 0.8-1%, the same FEUD_K costs about twice as
much of the equilibrium. So feud is out of line with its own grounds,
not with a density target.

**Closed (U, 2026-11-21, D14).** Part 2 (metal by contact) goes to
WP14; WP11 closes as a trace, with no rule changes. Herding density
waits with it. The feud finding (FEUD_K's grounds predate D7) is open
for U.
