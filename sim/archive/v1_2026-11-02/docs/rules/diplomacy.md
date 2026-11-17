# Similarity, trade, alliance, fusion

> **Draft structural mechanics (2026-10-29)** change this topic: `balance` (alliances against a common strong neighbour), `acculturation`, merchant quarters. See [structural.md](../structural.md); they switch off with `--off`.

Code: `Sim.similarity`, `accept`, `trade_ties`, `diplomacy`, `fuse`, `blend`.

## Similarity of two lineages

- **Distance:** d = distance between their cultural traits + 0.3 x the
  distance between their log biome affinities.
- **Same people:** exp(−d / 0.8). Kin start near 1 and drift apart.
- **Different peoples:** 0.15 + 0.35 x exp(−d / 0.8), so at most 0.5.

## Acceptance (tolerance gate)

    accept(level) = σ((tol_a − need)/w) x σ((tol_b − need)/w),
    need = level x (1 − similarity)

σ is the logistic function, and both sides must pass.

| Gate | Level | Width w |
|---|---|---|
| Trade | 0.4 | 0.15 |
| Alliance | 0.8 | 0.08 |
| Fusion | 1.0 | 0.06 |

## Trade

- **Who.** Neighbouring states (by land or sea) not at war build a tie from
  0 to 1.
- **Growth rate:**

      5 x 0.03 x trade_a x trade_b x (0.4 + 0.3(tol_a + tol_b)) x accept(trade)
        x (1 + 1.0 x mean share of each state's cities on rivers)
        x (1.5 if they share a river basin)

- **Decay.** Ties decay 10% per tick if the two stop being neighbours or go
  to war.
- **What ties do:**
  - a state's total ties boost its city cells' K ([population.md](population.md));
  - they cut the chance of war;
  - they speed technology borrowing;
  - they help plague spread.

## Alliance

- **Forming.** Each tick a pair allies with probability
  5 x 0.005 x accept(alliance) x (0.3 + tie).
- **Breaking.** An alliance breaks with probability
  5 x 0.004 x (1 − accept(alliance)).
- **In war.** Allies defend each other (0.35 of strength) and never fight
  each other.

## Fusion (union within a people, fusion across peoples)

- **When.** Allies with a tie of at least 0.3 merge each tick with
  probability 5 x 0.0025 x accept(fusion) x mean statecraft. The larger
  state absorbs the smaller.
- **Blending (U).** The two ruling lineages are replaced, inside the merged
  territory, by new lineages, one per people involved:
  - their cultural traits are the population-weighted mean of the two;
  - technology takes the better of each;
  - growth, biome fit and size stay with each people.
- **Peoples never interbreed:** a fused state rules two peoples side by
  side.

## Justifications

- **Tolerance gates scaled by dissimilarity** (**U**). Moderately tolerant
  kin ally easily. Across peoples, both sides need high tolerance. Tolerance
  also drives trade directly.
- **Gate levels and widths** (**C**).
- **River trade terms** (**U**: rivers should magnify trade). The numbers
  are **C**.
