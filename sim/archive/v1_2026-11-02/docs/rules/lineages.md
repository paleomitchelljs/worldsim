# Lineages, inheritance, extinction

Code: `Sim.new_lineage`, `settler_lineages`, `voyages`, `revolt`, `blend`,
`polity_stats` (assimilation), `record` (extinction).

A lineage is a group within a people. It carries its own cultural traits and
technology; intrinsic traits are fixed per people.

## How lineages arise

| Origin (`how`) | When | Cultural mutation (logit sd = 2.5 x value) |
|---|---|---|
| start | founding group | `--start-vary` (0.1) |
| secession | a province of the ruling lineage revolts | `--drift` (0.06) |
| colony | sea landing on a landmass the lineage never held (over 0.2M km²) | `--drift` |
| settler | settlers enter a 5° region their people never held | `--settle-drift` (0.03) |
| union / fusion | two states merge | none: population-weighted mean of the two ([diplomacy.md](diplomacy.md)) |

**What daughters inherit:**
- technology, unchanged;
- intrinsic traits (growth, biome fit), unchanged;
- the set of landmasses the parent has seen.

**What lineages lose:** lineages are absorbed into their people's ruling
lineage inside its states ([states.md](states.md)).

## Extinction

- A cell under 5 people is emptied.
- A lineage ends when it has no cells.
- A people ends when it has no cells, and it never returns. This is logged
  as `extinction`. It happened in run `sizefood_seed52`, where Trolls and
  Ogres were stranded on tundra.

## Justifications

- **Lineages** (**U**: several founding groups each, varying within a
  people).
- **Settler lineages** (**U**: a small cultural shift whenever a new area is
  colonized).
  - **Region size** (**C**): 5° per people. Per-lineage regions produced
    about 1,700 daughters per people in 1,700 years.
- **Intrinsic traits fixed** (**U**: separate intrinsic from cultural, with
  daughters inheriting intrinsic traits and technology directly).

## Typical counts (runs 91–94)

| Measure | Range across the 4 runs |
|---|---|
| Lineages alive at the end | 1,170–1,230 |
| Lineages alive at the peak | about 1,300 |
| Total created over a run | 3,000–4,400 |

Lineages created per run, by origin:

| Origin | Count |
|---|---|
| start | 200 |
| settler | 1,300–1,340 |
| secession | 840–1,550 |
| union | 550–1,120 |
| colony | 36–53 |
| fusion | 0–48 |
