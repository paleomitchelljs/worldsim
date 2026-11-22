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

## Sieges (one per war per tick; see `pol_step` below for sieges with a length)

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
7. **End:** the war ends with probability 0.12 + 0.006 x years elapsed
   per 5 years (stage C, 2026-11-18: written in years; the same at a
   5-year tick).

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
vulnerable, a few very hard. Numbers C. Each cell draws m = exp(0.18 x
t), with t Student-t (3 degrees of freedom), clipped to 0.5-3. The draw
belongs to the site, so a city refounded there keeps it. m multiplies
the terrain defence of a city there in sieges, counter-offensives,
cessions and deterrence. The spread was 0.12 until 2026-11-18, when U
asked for it a bit wider. With 0.18, half of sites lie in 0.87-1.15 and
9 in 10 in 0.65-1.53. 1 in 18 is above 1.5, 1 in 65 above 2.0 and 1 in
230 at the cap of 3. 1 in 65 is held at the floor of 0.5.

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
- It does not enter defence or the defender's deterrence. It moves the
  siege odds, so it moves the siege threshold and the defender's choice
  to submit. Under `ruler_odds` (below) it also enters the attacker's
  own reading of its odds when deciding on war.
- Successions run in states of any size (U, 2026-11-18; before then
  only at 3+ cities, so a smaller state kept its founder's g until it
  grew). A small state can draw a talented ruler and, in that reign,
  take its neighbours faster.

## Yearly political step (`pol_step`, WP5 stage D, 2026-11-18)

U: build it, with sieges that take time. Numbers C.
- Inside each 5-year tick, diplomacy, war and rebellion run five times,
  one year each (DT_POL 1). Polity statistics (strength, fed share,
  cohesion, neighbours) are computed once per tick. After a year in
  which a city changed hands, territory is redrawn and each state's
  strength is scaled by the change in its weighted people.
- A siege takes L = ceil(exponential(SIEGE_YEARS x D)) years, 1 to 8,
  with D = 1.4 x terrain x site x walls x 1.25 at a capital, the same
  defence the odds use. With SIEGE_YEARS 1 most sieges take 2-4 years.
- The besieged city loses 3% of its people (SIEGE_TOLL) over the whole
  siege, a share each year. The siege is decided at its end, on the
  odds then (allies, lord and vassals as they stand).
- Each side runs as many sieges at once as its logistics allow (1 +
  floor(2 G)), at distinct cities. A slot falls free when its siege is
  decided or its city changes hands.
- Chances per 5 years (war ending, cession, counter-offensive,
  ravaging) are applied each year as 1 - (1 - p)^(1/5). Rates per year
  (declaring, alliances, revolts, vassal defection) are applied per
  year. A war with a siege under way is not "abandoned".
- Submission is drawn when a siege would be laid, as before. Because a
  slot now falls free every 2-4 years, not every 5, a war has more such
  draws and more sieges in the same time.

## Field armies (`army`, WP5 stage E, 2026-11-18)

Forms from the review; numbers C.
- A state at war, or an ally that joined one, raises a field army
  toward ARMY_SHARE (4%) of its people. Each year it closes half the gap
  (ARMY_RAISE 2 years). The soldiers leave their own people's cells, in
  proportion to the cells' people. In peace the survivors go home the
  same way.
- The army eats from its people's harvest. Their capacity falls by the
  army's heads over their capacity, at most half (`food.csv`
  `taken_army`). Soldiers out of their cells do not breed.
- The field share f = army / (4% of the people), 0-1, multiplies the
  strength the state brings to its sieges and counter-offensives, and
  to pressing a cession. A city's defence takes 0.5 + 0.5 f (walls and
  townsmen hold half without a field army). Declaring still reads the
  whole state's strength.
- A decided siege costs the side that lost it 20% of its army and the
  side that won 5% (deaths "battle"). At a fortress people's city the
  besieger's fortress toll falls on its army.
- Exhaustion: the chance of ending per 5 years is 0.12 + 25 x the
  larger of the two sides' soldiers lost over its people, instead of
  rising with the war's age. A side that has lost 2% of its people in
  soldiers ends its war with chance about 0.6 per 5 years.
- It replaces the flat WAR_COST on everyone in a state at war.
- An army whose state ends is lost.

## Campaigns, vassals, rulers and herders (WP13 B, 2026-11-21)

U (2026-11-21, D15): build all five proposals of
`docs/upgrade/WP13-design.md`. Forms and numbers C.
- **Muster (`muster`).** A state that declares a war raises its army at
  once to MUSTER_F (0.5) of its full levy (4% of its people), from its
  own people's cells (at most half their people). It then raises the
  rest as under `army`. The defender starts from what it has.
- **Campaign goals (`campaign`).** When a land, rule or resource war
  takes its goal city, its next goal is the defender's city nearest the
  attacker's capital, if the attacker's strength there is at least
  ODDS_MID (0.7) of the defence (as `siege_odds` reads both). Otherwise
  the war is done and ends as before (WAR_DONE). Exhaustion and the end
  hazard still apply.
- **The ruler in the decision (`ruler_odds`).** The attacker's strength
  ratio in `war_chance` (deterrence and the prey motive) is multiplied
  by its offense (1 + talent + legacy). This reverses the 2026-11-18
  form ("does not change the chance of going to war"; U 2026-11-21).
- **Herders take tribute (`camp_tribute`).** A camp polity whose state
  herds (herding share >= 0.5) does not annex a city it wins: the
  city's state becomes its tributary vassal, or, if it is already
  another lord's vassal, is sacked. A city it would be ceded becomes
  submission in the same way. The camp stays a camp, gains tribute
  (VASSAL_TRIB) and does not annex its vassals. Camps that do not herd
  take cities and become city states as before.
- Annexing vassals of another people (`vassal_annex_cross`) is in
  [states.md](states.md).

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
