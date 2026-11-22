# WP13 stage A: design note (2026-11-21)

For U to decide before any code. Measures are from `wp10c` (five
seeds, 101-104 and 106, 8,000 years, full tables). Every proposal and
number here is C. Script: the session's scratchpad (not kept); the
tables below give what it measured.

## What the baseline shows

| Measure (per run) | Range over seeds |
|---|---|
| Wars | 1,205-4,906 |
| Cross-people wars, share | 0.24-0.36 |
| Wars with no siege | 0.53-0.56 |
| Wars with 2+ sieges | 0.17-0.20 |
| Wars that take 2+ cities | 0.03-0.04 |
| War length, median / 90th percentile (years) | 4-6 / 15 |
| Years from declaration to the first siege, median | 3.5-4 (never 0) |
| Odds at a war's first siege / at later ones (median) | 0.41-0.54 / 0.33-0.37 |
| Ends: peace / defender fell / submitted / abandoned / tributary | 0.22-0.32 / 0.20-0.29 / 0.14-0.19 / 0.12-0.16 / 0.08-0.10 |
| Abandoned wars that never laid a siege | 0.92-0.96 |
| Attackers with one city | 0.38-0.62 |
| Submissions (vassal made) | 288-1,076 (cross-people 24-37%) |
| Vassals that defect / are annexed | 42-55% / 4-13% |
| Vassals standing at once, mean after 6000 | 6-21 (of 170-260 states) |
| Camp states / with 2+ cities at peak / 5+ | 341-511 / 11-19 / 0 |
| States with 5+ / 20+ cities at peak | 23-62 / 0-6 |
| Small-state (1-3 city) reigns: wars declared per century, by ruler offense quartile | flat (for example 0.15, 0.17, 0.18, 0.17 in seed 101) |

## 1. Campaigns: the muster, and what a war is for

**Finding.**
- No war lays a siege in the year it is declared. The median wait is
  4 years.
- The attacker decides on its full strength (`deter` reads `projected`
  with no field share). But it fights at `field(A)`, starting from 0 and
  closing half the gap a year (ARMY_RAISE 2).
- Meanwhile the defender raises its own army, and its walls hold
  ARMY_GARRISON (0.5) with no army at all. So odds fall from the first
  siege to later ones (0.41-0.54 to 0.33-0.37).
- 92-96% of abandoned wars never lay a siege.

The muster lag is real, but it is not the main thing that stops
campaigns. **The goal is:**
- A motivated war aims at one city.
- Once that city falls, `done` makes the war end at WAR_DONE (0.8 per 5
  years).
- So 96-97% of wars take at most one city.

**Proposals.**
- **1a. Muster (`muster`).** A state that declares a war starts it with
  MUSTER_F (C: 0.5) of its full levy, raised at once from its own cells
  under the usual raising rules (the same food cost through `army_x`).
  The defender starts as now. This lines up the attacker's decision
  with its fight and shortens the wait to the first siege.
  - Cost: the levy's heads leave their cells at once, and a war that
    finds no siege still pays for the army.
  - Expected: fewer wars with no siege, more first sieges taken, more
    "defender fell". Not by itself more cities per war.
- **1b. Campaign goals (`campaign`).** When the goal city falls, a war
  whose motive is land, rule or resource picks the defender's next
  nearest city as a new goal, if the attacker's odds there are still
  at or above ODDS_MID. Otherwise it is done as now. Exhaustion
  (EXH_K, soldiers lost) and the end hazard still close it.
  - Expected: wars that take 2+ cities rise from 3-4%, larger states
    sooner, and more cross-people captures before year 6000 (WP10's
    limit on mixing).
  - Risk: one state snowballing. Report the largest state's share and
    peoples' shares; do not tune.

Recommend: build both, as two switches, 1b being the one that makes
campaigns.

## 2. Vassalage

**Finding.** The brief's premise is out of date.
- VASSAL_RATIO is read only with `war_odds` off. Under `war_odds` (the
  default), a defender submits through SUBMIT_ODDS before a siege.
- That happens a lot: 288-1,076 submissions per run, and 14-19% of
  wars end that way.
- Vassalage is **short**, not rare:
  - 42-55% of vassals defect (`vassal_politics`: the chance rises
    with the vassal's strength against its lord, the lord's low
    cohesion, and different peoples, x1.5);
  - a ruler's death frees vassals with chance VASSAL_ACC;
  - **only same-people vassals can ever be annexed** (3 cities or
    fewer, after 50 years).
- So a vassal of another people never becomes part of its lord's
  state, and a third of all vassals are of that kind.

**Proposals.**
- **2a.** Leave VASSAL_RATIO as the `war_odds`-off rule. Mark it
  "used only with `war_odds` off" in params.py and in the open
  question.
- **2b. Annexing foreign vassals (`vassal_annex_cross`).** A lord may
  annex a vassal of another people on the same terms as a kin vassal,
  at a lower rate: x (1 - the vassal's tolerance) x the lord's
  dominance; the annexed cities' people stay as subjects.
  - Expected: more cross-people rule (WP10's assimilation clock then
    runs on it).
  - Also more revolts, since subjects of another people revolt more.
- **2c.** No change to defection. It is the counterweight, and it has
  causes.

Recommend: 2a and 2b.

## 3. The ruler's edge in the war decision (U's call)

**Finding.**
- Ruler offense (`ruler_mil`) counts in sieges, cession and battle,
  but not in `war_chance`.
- Small-state reigns declare at the same rate whatever their ruler's
  talent: flat across offense quartiles in all five seeds.
- Offense is small for most rulers: median 0.07, 95th percentile 0.30
  (cap 1.0).

**Proposal 3 (`ruler_odds`).** The attacker reads its odds with its
ruler's edge: R x offense(A) in `war_chance` (and in `war_bound`'s cap,
which stays a valid bound).
- This reverses U's form of 2026-11-18 ("does not change their chance
  of going to war").
- Expected: at the gate's centre (ODDS_W 0.35), a 95th-percentile ruler
  (x1.3) roughly doubles the chance of declaring. The median ruler
  changes little.
- It is the cheapest way to get a small state's gifted ruler to start
  the wars that let it grow (the Cyrus case). It will not make many
  bursts unless 1b is on as well, since one war still takes one city.

Recommend: yes, with 1b.

## 4. Herder conquest

**Finding.**
- 341-511 camp states per run. 11-19 ever hold 2+ cities; none 5+.
- `decamp` turns a camp that takes its first city into an ordinary
  city state, which then has a one-city state's administration, reach
  and odds.

**Proposal 4 (`camp_tribute`, C).** A camp polity whose people herd at
the seat (herding share >= 0.5) does not take the city it wins.
- The city's state submits to the camp as a tributary vassal, and the
  camp stays a camp: it cannot be besieged, is lost only in battle,
  and keeps its herder reach.
- Tribute (VASSAL_TRIB) builds the camp's strength, so it can take on
  larger states.
- A camp people that does not herd decamps as now.

This uses the vassal code that exists, and fits steppe empires that
ruled through tribute. The other form, a camp that keeps several
cities under camp-style reach, would touch territory, administration
and city culture (WP5F audit), and is much more code.

Expected: a herder route to large tributary networks.
- They will be short-lived if defection works as now, since
  cross-people vassals defect at x1.5.
- 2b does not apply to camps: camp lords do not annex.

Recommend: yes.

## 5. WAR_GAIN and WAR_IDLE

**Finding.**
- Neither is read anywhere in the code. They belong to the old
  `war_motive` form, which `war_v2` replaced.
- So the sensitivity screen's "moved nothing" for them is an artefact,
  not evidence that the war motive does not reach onset.
- The motive terms in use (HUNGER_WAR, LP_K, PREY_K, ENM_K, IRR_K,
  WAR_GAIN_CAP, WAR_EPS) were not in the screen. WAR_BASE and ODDS_MID
  were, and move wars strongly.

**Proposal 5.** Delete WAR_IDLE and WAR_GAIN and their comment from
params.py, and correct sensitivity.md. Whether the motive matters is
then a question for a small screen of the live terms, which I would
only run if U wants it.

Recommend: delete; no screen now.

## Order and testing (stage B)

1. 5 first (pure deletion).
2. 1a and 1b.
3. 3.
4. 2b.
5. 4.

Each behind its own switch. One sanity run, then a 5-seed batch with
`--keep summary`. Report S1-S7 and W1-W3, the table above, and
peoples' shares against `wp10c`.

## For U

1. Build 1a (muster) and 1b (campaign goals)?
2. 2b (annexing vassals of another people)?
3. 3: let the ruler's talent enter the decision to go to war (reverses
   your 2026-11-18 form)?
4. 4: herder camps rule cities as tributaries?
5. 5: delete WAR_IDLE and WAR_GAIN?

## Built (WP13 B, 2026-11-21; U: D15, all five)

All five are built as switches, on by default. In the five-seed batch
(`wp13b`, run-log.md), 1b fired only 0-17 times a run. 86-90% of the
goals taken are a one-city defender's only city, so the war ends with
the defender. Section 1's diagnosis was therefore mostly wrong: few
states have a second city to campaign on.
