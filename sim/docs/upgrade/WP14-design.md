# WP14: design note and build (2026-11-22)

**U (2026-11-22):** "dive in on WP14"; no technology targets, and no
concern for when peoples reach which technology, so item 4 of the
brief (the timeline) is decided. The proposals below are C and were
built at once, each behind its own switch, on by default.

Measures are from the full baseline `wp12f` (five seeds; script in the
session's scratchpad, not kept): per people, the first farming, bronze,
iron and steel, metal at the end and at its peak, innovation, and
bronze-use lapses (`supply`).

## What the baseline shows

| Measure, per run | `wp12f` (five seeds) |
|---|---|
| Peoples that ever cast bronze (of 10) | 4-7 |
| Peoples that ever forge steel | 3-5 |
| Metal level at the end below its peak (any people, by 0.05+) | none of 50 people-runs |
| Bronze-use lapses for lack of ore, per people | 0-37 |
| Ogres, Giants: metal at the end | 0 in every seed |
| Lineages reaching metal 1 (bronze), lowest innovation quartile | 0.00-0.36 (other quartiles 0.49-0.95) |
| Correlation of innovation and metal over living lineages | 0.29-0.58 |

- **Knowledge is not lost.** A people's metal level almost never falls:
  `known` stays set for ever, and metal decays only outside a state
  (DECAY_METAL 0.0004 a year). Bronze *use* lapses often when ore runs
  out (`supply`), but it comes back as soon as ore does.
- **Low-innovation peoples reach bronze late, in some seeds.** Goblins
  (innovation 0.11-0.17) cast bronze in seeds 101 and 104 (7020, 7450),
  Froglok (0.23-0.30) in 102 and 103, Trolls in four seeds; none of
  them reaches iron except Trolls in seed 104 (innovation 0.46 there). The brief's
  "they reach steel through long contact" is not general. Borrowing runs
  at (0.3 + innovation), so 0.2 innovation still borrows at half the
  rate of 0.7.
- **Innovation and seafaring cost nothing.** Trade does: plague jumps
  along trade ties (PL_LINK, PL_JUMP).

## Built

### 1. Loss: `tech_forget`

A known metal stage that has been out of use for TECH_FORGET (300)
years is forgotten, with every stage above it. Metallurgy falls to
FORGET_DROP (0.2) below that stage's threshold (bronze 1.0, iron 1.8,
steel 2.6), so it has to be found again by invention or borrowing.

- "Out of use" is what `supply` already tracks (`lack`): bronze without
  copper and tin, iron without iron ore, steel without iron or without 6
  cities. So a people that loses its cities loses steel after 300 years:
  the Bronze Age collapse case.
- Agriculture, fishing, sailing, administration and craft already decay
  when unused; this adds the metal stages.

### 2. Borrowing: `closed_borrow`

Borrowing runs at BORROW0 + innovation, BORROW0 = 0 (it was 0.3). A
people at innovation 0.1 borrows at a quarter of its old rate, one at
0.7 at 70%. Cohesion still closes a people further
(1 − COST_COH × cohesion).

### 3. Costs: `tech_costs`

- **Innovation costs growth:** the growth rate × (1 − COST_INN ×
  innovation), COST_INN 0.1. Time and risk spent on new ways. A lineage
  at 0.8 grows 8% slower than one at 0, so selection can act on
  innovation within a people.
- **Seafaring costs lives:** each year a cell loses COST_SAIL (0.001) ×
  its lineage's sailing (0-1) × the cell's coastal share at sea (cause
  "sea"). A quarter of feud's FEUD_K.
- **Trade:** no new cost; plague already follows trade.

Not built: a food cost of innovation (it would duplicate the growth
cost), and loss of metal on losing cities alone (steel's 6-city rule
with `tech_forget` covers it).

## Risks

- Forgetting and slower borrowing can leave whole peoples without
  metal, and may make metal rarer late (U: not a concern).
- The innovation cost shifts peoples' shares toward low-innovation,
  fast-breeding peoples (Froglok, Goblins).
- Sea deaths fall on coastal peoples with sailing (Snake folk, Elves,
  Dwarves, Humans).

## Results (`wp14b`, 2026-11-22)

See run-log.md. Population at 8000 37.8-51.7M (`wp12f` 55.8-82.2),
states with 3+ cities 25-94 (79-210), wars about a third. Ablations on
seeds 101 and 103 point at `tech_costs`; the steel years barely move.
For U: keep `tech_costs` as it is, lower COST_INN and COST_SAIL, or
switch it off.

