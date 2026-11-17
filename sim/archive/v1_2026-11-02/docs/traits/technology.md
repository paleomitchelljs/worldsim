# Technology

> **Draft structural mechanics (2026-10-29)** change this topic: `supply`: metal stages need ongoing ore supply and idle skills decay, so technology can be lost; cohesion slows borrowing (`costs`). See [structural.md](../structural.md); they switch off with `--off`.

There are four technologies, one level each per lineage.
A fifth, **fishing**, comes with `fishing` (U, 2026-10-29): see
[../structural.md](../structural.md#dispersal-and-fishing-dispersal-fishing).
- **Inheritance:** daughter lineages inherit them unchanged.
- **Fusion:** a fused state takes the better of the two.
- **Loss:** technology is never lost.

Code: `Sim.technology` (progress and borrowing), with effects spread through
`Kf`, `grow`, `polity_stats`, `voyages`, `sea_adjacency`, `territory`,
`rebellions` and `adapt`.

## Progress

Each tick, technology advances by invention plus borrowing.
- **Invention.** Each technology has its own rate:

  | Technology | Starts at | Invention rate per year |
  |---|---|---|
  | Farming (0–1) | 0.25 | 0.0009 x innovation x size factor x (1 − level). The size factor runs from 0.5 at a tiny group to 1 at a million people. |
  | Metallurgy (open scale) | 0 | 0.0005 x innovation² x (1 + ln(1 + cities)/3), and only once farming > 0.5. It is capped at 1.2 before bronze, 2.0 before iron and 3.5 after. |
  | Sailing (0–1) | 0.05 x seafaring | 0.0012 x seafaring x (coastal share + 0.1) x (1 − level) |
  | Administration (0–1) | 0 | 0.0008 x statecraft x (1 − level) x sqrt(min(1, cities/5)); with `ruler_traits`, the state's effective statecraft (ruler-weighted) for ruling lineages |
  | Road engineering (0–1, `road_tech`) | 0 | 0.001 x innovation x share living in a state x (1 − level); borrowed at 0.002; idle decay as administration |

- **Borrowing.**
  - Rate = factor x the gap to the single most advanced contact x contact
    strength x (0.3 + innovation).
  - The factor is 0.004 for farming, 0.0008 for metallurgy, 0.001 for
    sailing and 0.002 for administration.
  - Contact comes from shared borders, rule (ruler and subject) and trade
    ties (x30).

## Metal stages

| Stage | Metallurgy needed | Also needs |
|---|---|---|
| Bronze | 1.0 | copper and tin within 120 km of the group's own settled cells, or of a close contact |
| Iron | 1.8 | iron ore |
| Steel | 2.6 | iron, plus at least 6 cities |

## Effects

| Technology | Effects |
|---|---|
| Farming | Carrying capacity blends forage and farm density by the level. Growth x (0.6 + 0.4 x farming). Loosens biome preference (half of `adapt`). |
| Metallurgy | War strength x 2 / 3 / 4.5 at bronze / iron / steel. Farm yield +25% with iron and +25% more with steel. Loosens biome preference (half of `adapt`). |
| Sailing | Typical voyage distance D = 40 + 2500 x sail^1.5 km. Voyage targets are weighted by exp(−d/D), with no minimum range. Voyage frequency ∝ seafaring x (0.1 + sail). States within 2D by sea count as neighbours for war, trade and alliance. River leaps run 6 + 30 x sail cells. |
| Road engineering | Quality of roads built: 0.15 + 0.85 x engineering x (0.8 + 0.2 x admin). Travel cost x (1 − 0.5 x stock x quality). |
| Administration | Reach = 120 + 900 x admin km (travel cost). Reach sets how much land a city rules, how much strength a state projects into a war, and how rebellious far provinces are. City size cap = 6000 x (3 + 40 x admin²) food-equivalents, only with `--city-cap` (off by default). |

**How technology loosens biome preference.**
- `adapt = 0.5 x clip((farming − 0.25)/0.75) + 0.5 x clip(metal/2.6)`.
- The exponent then falls: `k = 2.5 x (1 − 0.6 x adapt)`. With full farming
  and steel, `k` = 1 and the roster's affinities apply as written.

## Justifications

- **Bigger technology effects** (**U**: "technology should have a big
  impact"; numbers **C**). Strength from metal went from 1.5/2.1/2.8 to
  2/3/4.5, and tool yields from +15/+12% to +25/+25%.
- **Sailing as a distance kernel** (**U**). It replaced a hard minimum range
  of 160 km that worked like an on/off switch. Short coastal hops are
  possible from year 0.
- **Technology loosens biome preference** (**U**). Farming and metal tools
  let a people make a living outside its home biome.
- **Borrowing from the best contact only** (**C**). Summing over all
  contacts let Trolls, with innovation 0.2, reach steel by sheer number of
  neighbours.
- **The admin cap on city size** (**U**). It ties how big a city can get to
  the state's capacity to run it.
