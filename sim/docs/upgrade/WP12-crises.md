# WP12: crises that last

**Goal.** Falls in population that take generations to recover from,
so that history has dark ages and not only dips.

**Evidence.**
- Population tracks capacity once land fills (WP6 stages B and C).
  Slower growth and epidemics slowed recovery, but not by much.
- In the screen, P4 (the largest 100-year fall after year 3000)
  responded to none of the 30 parameters, CLIM_AMP included
  (sensitivity.md). Its seed sd is nearly as large as its mean, so it
  is noise-dominated rather than proven inert.
- Two options were left open at WP6 (STATUS, WP6 stage A):
  - **lagged capacity:** destroyed field works, herds and clearing take
    decades to rebuild, so capacity itself falls after a crisis;
  - **plague not tied to city size:** epidemics that reach rural land
    and small states.
- What already exists: `waste` (devastation recovers over WASTE_YEARS),
  `improvements`, `clearing` (land grows back when empty), epidemics
  (PL_*).

Read first: `wsim/land.py` (`grow`, `famine`, `prepare_capacity`),
the epidemics code (`PL_*` in `params.py`), `WP6-demography.md`,
open-questions.md ("Plague and growth", "Epidemics and upkeep").

## Stage A: measures (records only)

1. For each fall of 20% or more in a landmass group or state: its cause
   (war, famine, plague, climate), how deep, and years to 90% recovery.
2. The share of time each landmass group spends below 80% of its
   capacity.
3. Report on `wp8n`.

## Stage B: design note (needs U)

The two options above, plus any stage A suggests, with what each would
change and what it risks (a timeline that stretches; steel after year
8000).

## Stage C: build

As decided, one switch each. 5-seed batch; report P2-P4 and the
timeline.
