# WP7 design note: several peoples in a cell, and displacement

Status: proposal (**C**), for U to confirm (decision D9). Nothing is
built. Written 2026-11-18, after WP6 C, against code at 34ce886.

## Where things stand

- A cell holds one people and lineage (`cul`, `lin`, `pop`) and at most
  one minority (`mcul`, `mlin`, `mpop`, with `mcap` marking a merchant
  quarter held at MIN_CAP 0.2 of K).
- At year 8,000 of `wp6c_seed101`, 1,552 of 47,530 occupied cells (3.3%)
  have a minority. Minorities are 1.6-2.5% of heads in the `wp6b`/`wp6c`
  runs. 1-3% of occupied cells change people per 500 years.
- Under `dominion` (on) a minority that is not a merchant quarter already
  competes for the cell's food with the majority (`grow`, below). So the
  competition rule exists for two peoples. What is missing is (a) more
  than two, (b) any way to move into a cell another people holds except as
  settlers of a ruling people, garrisons and merchants, and (c) anyone
  fleeing.

## 1. Representation: slots, not a presence table

The brief recommends a presence table (one row per cell and people). I
recommend **a fixed number of slots per cell** instead: arrays `P[N, S]`
(heads), `C[N, S]` (people) and `G[N, S]` (lineage), with S = 4 (C), and
slot 0 always the plurality people (by food-equivalents).

Why:
- **Today's names stay valid.** `pop`, `cul`, `lin` become numpy views of
  slot 0 and `mpop`, `mcul`, `mlin` views of slot 1. Every one of the
  ~300 reads and ~60 writes to them keeps working, and writes go through
  to the slot arrays. Stage B is then a re-plumbing of storage with no
  change in behaviour. A presence table means rewriting every write site.
- **Capacity needs no change.** `Kf` takes (lineage, cell) pairs, so all
  rows are `Kf(G[mask], cells[mask])`, as the brief says of the table.
- **Cost.** Work only on occupied slots (about 1.05 rows per occupied cell
  today); memory is trivial (67k x 4).
- **Limit.** At most S peoples in a cell. A fifth arrival either merges
  (same people) or must displace the smallest row; I would let it in only
  if it would outweigh that row, and send the row out under stage D.
  Four peoples sharing one 0.5-degree cell is already rare in history
  outside cities.
- **Hazard.** Pickling does not keep a view tied to its base. `Sim` needs
  a `__setstate__` that rebinds the views after loading a saved state
  (and `upgrade()` builds the slot arrays from old `pop`/`mpop`).

## 2. One lineage per people per cell

Yes, as the brief recommends and as now: arrivals of another lineage of
the same people merge into the row (the larger lineage keeps the row).
`settler_lineages` still founds daughter lineages in new regions.

## 3. Competition

Row i's people eat e_i food per head; f_j = heads_j x e_j. Row i grows
logistically toward

    K_i' = K_i − Σ_{j≠i} α_ij (w_j / w_i) f_j / e_i ,   floored at a small value

with K_i from `Kf`, weights w from `comp_w` (technology; the ruling
people's establishment, SH_STATE), α_ij = SHARE_ALPHA (0.9) x overlap_ij.

- **Reduces to today.** For two rows with overlap 1 this is exactly the
  `dominion` branch of `grow`: the minority's capacity is
  K_m − α (w_M / w_m) f_M / e_m, and the majority's is reduced by
  α (w_m / w_M) f_m / e_M (today's `coef`).
- **What stops the strongest from excluding everyone.** In
  Lotka-Volterra terms the product α_ij α_ji = α² overlap² (the weights
  cancel), so coexistence turns on capacities: the weaker row persists
  only where its own K on that land is high enough relative to the
  stronger's (different biome fits and food sources give different K).
  With SH_STATE 3 an established ruling people weighs up to 4x, which
  would push subjects out of most shared land. I do not think differing
  K alone is enough. Instead of a floor (which would be a causeless
  term), I propose **niche overlap**, which has a cause: peoples that
  live off different things compete less.
  overlap_ij = 1 − 0.5 x |herding share_i − herding share_j| − 0.5 x
  (1 − similarity of their biome affinities), in 0-1 (C). Farmers and
  herders on one cell, or a forest people and a grassland people,
  compete weakly and can share; two farming peoples of the same land
  compete fully. Run without it first if U prefers, and report.
- **Merchant quarters.** Today `mcap` holds them at 0.2 of K, outside the
  competition. Under shared cells they become ordinary rows whose K on a
  city cell includes the trade food that reaches the city (`loc_in`), so
  they live off trade rather than land. They may not survive; that is an
  outcome to report, not to fix.

## 4. Movement into held cells

`migrate` today moves people only to neighbours of their own lineage.
Under `shared_cells` each row drifts toward neighbouring cells where its
people would have room (K_i' minus its heads there), whether empty, its
own, or held by others, with weight

    room x sqrt(K) / edge cost x (1 − RES x (1 − tol_holder) x min(1, w_holder / w_mover))

The resistance has two causes: the holders' intolerance, and their
strength relative to the movers (RES 0.9, C). It replaces the present
`1 − 0.9 x separation x foreign` term. Inside one state, settlers of the
ruling people meet no resistance from subjects (today's `settlers` rule,
generalised to any slot). Deportation of subjects by a state is left out
(possible later). Merchants enter through `minorities` as now.

## 5. Displacement (stage D)

Clearance, sack, a raid takeover and expulsion now kill everyone they
remove. Under `displacement`:
- A share FLEE (0.5, C) of those removed flees; the rest die as now.
  Famine already moves its surplus (`famine`), unchanged.
- Refugees go up to 3 rings, to cells where their people already lives
  or that are empty, in proportion to room there. Those who find no
  room die ("died fleeing").
- They arrive as heads like any other: crowding rises in the receiving
  cells, and the existing hunger term in raids (HUNGER_RAID) and
  migration pressure carry the cascade on. No new cascade rule.
- Records: moves, not deaths, in the growth account (`displaced`, net
  zero for the world); refugees per event in `events.jsonl`.

## 6. What each routine reads

| Routine | Reads | Change |
|---|---|---|
| `grow` | every row | the form in 3 |
| `famine` | every row | each row's excess over its K' |
| `migrate`, `budding`, `pioneers`, `voyages` | every row | 4; budding and pioneers still into empty cells |
| `raids` | plurality row of each cell attacks; every row of the target suffers (as now) | new: rows of different peoples in one cell raid each other at the same formula, scaled by the `same_state` factor if both are in the state |
| `capture`, `sack`, clearance | every row | clearance removes rows of the city's people, not "the majority" |
| `disasters` (plague) | every row | host factor per row (already per majority and minority) |
| `polity_stats`, extraction, `food_flows` | every row | own vs subject per row (already for two slots): sums over slots |
| `technology` | every pair of lineages in a cell | already majority with minority |
| `city_culture`, city composition | every row, as shares | "Multi-origin cities" rule already sums majority and minority |
| `minorities` | non-ruling rows | merchants become rows; expulsion applies to any non-ruling row (flees under D) |
| `tidy_minorities` | - | replaced by sorting slots by food-equivalents each tick; a city follows its new plurality, as now |
| `dragons` | total heads | as now (`pop + mpop` becomes `P.sum(1)`) |
| territory, state formation, colours, maps | plurality | unchanged |
| records | plurality, plus all rows where heads are summed | `final_state.npz` gains the slot arrays; history keeps plurality and the largest other row |

## 7. Records and Price

`price()` uses lineages as units and their heads (in fe) as weights and
offspring, summed over majority cells only. With slots it sums every row
(`bincount` over `G`, `P x eat`). Minority heads (1.6-2.5% now) start to
count, so Price series show a small step at the change. Turnover
measures ("people changed") read the plurality; add "share of heads not
in the plurality" and "cells with two or more peoples over 10%".

## 8. Order of building

- **B.** Slot arrays with S = 2 and views; every rule as today. Since
  this changes storage only, a run of seed 101 should reproduce
  `wp6c_seed101` exactly (`events.txt` identical): one run, cheap and
  decisive. Then S = 4 with the extra slots unused (still identical).
- **C.** `shared_cells`: general competition with niche overlap,
  movement into held cells, raids inside a cell, slot sorting in place of
  the swap, merchant rows. Seeds 101 and 103, on and off; the brief's
  measures, and **stop and report if one people passes about two thirds
  of heads or the spread between peoples collapses.**
- **D.** `displacement`: flight from clearance, sack, takeover and
  expulsion.

## For U

1. Slots (S = 4) instead of the presence table?
2. Niche overlap as what lets peoples coexist, or plain competition first
   and report?
3. Raids between peoples living in one cell?
4. Displacement: half of those removed flee, up to 3 rings, the rest die?
