# Model v1, archived 2026-11-02

The model as it stood before the streamlining and the city-level
rebuild (docs/open-questions.md, "Cities as a nested unit of culture"
and "Before building"). Includes the 2026-11-02 rulers batch
(`ruler_traits`, `turmoil`, `revolt_viol`, `road_tech`, `fortress`).

To revert: copy these files back into `sim/` (docs/ into `sim/docs/`).

Last runs on this code (in `runs/`):
- `p_seed101-106`: controls, without the five 2026-11-02 switches
  (`runs/prov.sh`, code `snap_prov.py`).
- `r_seed101-106`: everything on (`runs/rulers.sh`, code
  `snap_rulers.py`).
- `ra_<switch>_seed101`, `rb_*_seed101`: ablations
  (`runs/rulers_ablate.sh`, `runs/rulers_ablate2.sh`).
Results: docs/run-log.md, "2026-11-02: rulers batch".
