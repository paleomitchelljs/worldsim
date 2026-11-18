# War, conquest, raids

> **Draft structural mechanics (2026-10-29)** change this topic: `vassals` (submission, tribute, defection), mounted herders, garrisons left as minorities. See [structural.md](../structural.md); they switch off with `--off`.

Code: `Sim.wars_step`, `projected`, `capture`, `raids`; `World.defence`.

## Declaring war

Neighbouring states, by land or by sea within 2 x sailing distance, are
checked each tick. The chance the first declares on the second is:

    5 x 0.012 x violence x S x min(3, strength ratio)^1.2 / 2
      x [0.5 + (1 − similarity)(1 + 1.5 x separation)]
      x (1 − trade tie) x (1 − 0.4 x tolerance)

There is no war between allies or during a truce (30 years after a war).

## Sieges (one per war per tick)

1. **Target:** the enemy city nearest the attacker's capital.
2. **Projected strength:** strength x exp(−distance / (1.5 x reach)).
3. **Defender's side:**
   - adds 0.35 x each ally's projected strength;
   - is multiplied by 1.4 x terrain defence, and by 1.25 more at a
     capital.
4. **Terrain defence** = biome factor x (1 + 0.6 x relief km, up to 1.5)
   x (1 + 0.6 x wetness). Biome factors:

   | Grassland | Temperate forest | Tundra | Desert | Jungle |
   |---|---|---|---|---|
   | 1.0 | 1.1 | 1.3 | 1.6 | 1.7 |

5. **Odds:** the attacker takes the city with probability A²/(A² + D²), so
   a 2:1 edge wins 80%.
6. **Cost:** every siege costs the target 3% of its population. A failed
   siege costs the attacker 2% of its cohesion.
7. **End:** the war ends each tick with probability 0.12 + 0.03 x ticks
   elapsed.

## Odds-gated war (`war_odds`, WP5 stage B, 2026-11-18)

U: build it (2026-11-18); forms from the upgrade review; numbers C. On
by default. See [structural.md](../structural.md), "2026-11-18".

- **Declaring.** In `war_chance`, the deterrence factor min(1, 2R²/(1 +
  R²)) becomes a steeper gate: floor + (1 − floor) x logistic((ln R − ln
  0.7) / 0.35). Without the floor it is 0.05 at R = 0.25, 0.28 at
  R = 0.5 and 0.74 at R = 1. The floor is 0.05 x min(1, R / 0.7) x
  min(1, (1 − fed) + the enmity motive + the faith motive): hunger,
  hatred and faith still drive wars at long odds, less the longer they
  are. With the floor at its full value the gate stays below the old
  rule at every R (0.011 against 0.020 at R = 0.1, 0.30 against 0.40
  at R = 0.5).
- **Besieging.** A side lays a siege only when its win probability is at
  least 0.15 (SIEGE_MIN). Below that the attacker ravages the target
  city's hinterland with chance = its violence: RAVAGE_K (0.1) x
  violence of the people there die (cause "ravage"), and improvements
  fall by 0.3 x that share, as in a raid. Otherwise it sits. A
  counter-offensive below the threshold is not laid.
- **Stall.** A war with no siege by either side for 15 years
  (WAR_STALL) ends "abandoned".
- **Submission before a hopeless defence.** Before each siege, a
  defender facing odds p >= 0.6 (SUBMIT_ODDS) submits as a tributary
  with chance clip((p − 0.6) / 0.4, 0, 1) x (1.2 − cohesion) x (0.5 +
  the attacker's dominance). Without the switch it submits only when
  the attacker's projected strength is over 3x its own (odds 0.9), at
  half that chance. A defender never cedes its last city; it fights or
  submits.
- **Record fix (both settings).** A war that ends by cession is closed
  "ceded" before the city changes hands. Before, a one-city defender's
  cession ended the state first and the war was recorded as "defender
  fell".

## Site defence (`site_defence`, 2026-11-18)

U: each city gets a random defence boost for whatever in its ground
makes it easier or harder to take than terrain says; most alike, a few
vulnerable, a few very hard. Numbers C. Each cell draws m = exp(0.12 x
t), with t Student-t (3 degrees of freedom), clipped to 0.5-3. The draw
belongs to the site, so a city refounded there keeps it. m multiplies
the terrain defence of a city there in sieges, counter-offensives,
cessions and deterrence. Half of sites lie in 0.91-1.10 and 9 in 10 in
0.75-1.33. 1 in 200 is at 0.5 (clipped) and 1 in 200 above 2.0.

## Ruler generalship (`ruler_mil`, 2026-11-18)

U: some rulers are better at offense. This does not change the chance
of going to war, but at war their state punches above its weight, and
the edge fades over later reigns. Numbers C.
- Each ruler draws a talent g, exponential with mean 0.1, capped at 1.
  Half are under 0.07, 1 in 20 over 0.3 and 1 in 140 over 0.5.
- A state's offense is 1 + g + legacy. At each succession, legacy
  becomes 0.5 x (legacy + the old ruler's g).
- Offense multiplies the strength the state brings when it besieges
  (its own sieges and its counter-offensives) and when it presses for a
  cession.
- It does not enter defence or deterrence, so the chance of declaring is
  unchanged. It moves the siege odds, so it moves the siege threshold
  and the defender's choice to submit.
- Succession runs only in states of 3+ cities, so a smaller state keeps
  its founder's g until it grows.

## Terms after a won siege (`war_terms`, 2026-11-09)

The winner chooses (U: built now; form and numbers C; structural.md,
"2026-11-09"): **annex** the city (Capture, below), take the defender as
a **tributary** vassal and end the war, or **sack** the city and leave it
to the defender. Weights: annex gov x (0.5 + dominance); tributary
(1 - gov) x (0.5 + dominance), only if the defender is no one's vassal;
sack 0.5 x violence x (1.5 - dominance). gov = the share of its strength
the winner projects to the city. The war's goal doubles its own outcome.
Without the switch every won siege annexes.

## Capture

- **Losses:** the city loses 10% + 40% x the conqueror's violence of its
  population.
- **Clearance:** if the conquered people differ, the conqueror clears with
  probability separation x violence x (1 − tolerance). The city's hinterland
  of that people drops to 15% and the city to 30%.

## Raids (cell scale, outside sieges)

- **Chance.** Along every border between two peoples, each side raids each
  tick with probability

      5 x 0.02 x violence x (0.5 + crowding) x (1 + separation) x (1 − 0.5 x tolerance)

  That is multiplied by 0.2 inside a single state.
- **Damage:** 0.12 x violence x sqrt(attacker size ÷ defender size) ÷
  terrain defence, at most 60% of the defender's cell. The raider loses 1%.
- **Take-overs:** see [colonization.md](colonization.md).

## Justifications

- **Size in strength** (**U**: Giants 30, Ogres 20, Trolls 10; penalties for
  small peoples). It is paired with food per head (**C**), see
  [../traits/intrinsic.md](../traits/intrinsic.md).
- **Terrain defence** (**U**: hard to win in swamp, jungle, mountains and
  desert, easy in grassland and temperate forest). The numbers are **C**.
  Observed effect (runs 91–94 against 81–84), as capital falls per 100k
  city-years:

  | Biome | Before | After |
  |---|---|---|
  | Jungle | 7.1 | 2.5 |
  | Desert | 6.7 | 3.7 |
  | Grassland | 9.1 | 7.1 |

  Wandering starts and rivers changed in the same runs, so this comparison
  is not isolated.
- **Squared-strength odds** (**C**): a Lanchester-like square law.
