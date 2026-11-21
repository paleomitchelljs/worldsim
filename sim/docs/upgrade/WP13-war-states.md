# WP13: campaigns, vassals and rulers

**Goal.** Wars that run as campaigns, vassalage that happens, and
rulers whose talent can make a small state grow.

**Evidence.**
- **No campaigns.** The multi-siege campaigns the WP5 brief expected
  did not come from the yearly step or the army stock (STATUS, WP5
  stage E). The likely lever: an attacker that chose its war starts
  with its army partly raised (a muster). Not built.
- **Vassalage is rare.** VASSAL_RATIO (3:1) is checked after terrain
  and capital defence, so it is seldom met (open-questions.md).
- **Gifted rulers don't pick fights.** A ruler's edge counts in battle
  but not in the attacker's reading of its odds, so a gifted ruler of a
  small state doesn't start the wars that would let it grow (STATUS,
  WP5 stage B; the Cyrus case, U 2026-11-18).
- **No herder route to large states.** Camps that take a city become
  one-city states with the usual odds (STATUS, WP5 stage F).
- **Inert parameters.** WAR_GAIN and WAR_IDLE moved no measured
  pattern over a factor of 4; war onset is set by the odds and raid
  paths (sensitivity.md).

Read first: `wsim/war.py`, `wsim/states.py`, `WP5-politics-war.md`,
`WP5F-camps-design.md`, open-questions.md ("WP5 stages B-F",
"Small-state succession").

## Stage A: design note (needs U)

For each item above: the change, its form, and what it would move. In
particular:
1. The muster: how much army an attacker can raise ahead of a war it
   chose, and what it costs.
2. Vassalage: test the strength ratio before or after defence.
3. The ruler's edge in the war decision (this reverses "does not change
   their chance of going to war", so U's call).
4. Herder conquest: whether camps that take cities can keep camp-style
   rule over several cities.
5. WAR_GAIN and WAR_IDLE: remove them, or find why the war motive does
   not reach onset.

## Stage B: build

As decided, one switch each. Sanity run, then a 5-seed batch. Report
S1-S7 and W1-W3 (patterns.md) against `wp8n`.
