# WP15: loose ends

Small fixes that need no design note. Each is one session or less, and
none needs U unless marked. Do them in any order, or alongside another
package that touches the same code.

1. **State decisions that read the ruling lineage** (open-questions.md,
   "States and war"). Under `city_culture`, war, trade and alliance read
   the state's culture. Three still read the ruling lineage's traits:
   - the revolt "alien" term (`rebellions`);
   - foreign subjects' weight in strength (`polity_stats`);
   - expulsion of minorities (`minorities`).
   **Needs U:** intended (the lineage's own view), or move them to the
   state's culture?
2. **Third and further peoples.** Technology contact, city composition,
   famine, clearance targeting and history snapshots still ignore a
   cell's third and further peoples (structural.md). About 140 cells
   per run.
3. **Allies missing from war records.** Since 2026-11-07 an attacker's
   allies help it hold its cities, but `wars.csv`'s `helpers` lists only
   the defender's.
4. **SITE_DEF_SD** showed no clear direction on any pattern
   (sensitivity.md). Check whether site defence reaches the siege odds.

Each with a sanity run; no batch unless a fix changes the rules (2 and
4 may).

## Status (2026-11-22)

- 1: done. U: "state's culture with ruling lineage's tolerance
  determining how much the state ends up culturally compromising".
  Switch `state_view`: the three read the ruling lineage's values moved
  toward the state's culture by the lineage's tolerance (rules/states.md).
- 2: done. Technology contact, city composition, famine, clearance and
  the snapshots read extra rows (structural.md).
- 3: done, `wars.csv` column `att_helpers`.
- 4: checked, no change: site defence reaches the odds and halves how
  often hard sites are besieged; the odds gate hides it from outcomes
  (sensitivity.md).

