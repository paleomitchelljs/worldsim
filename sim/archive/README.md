# archive

Since 2026-11-17 the project is under git, so nothing new goes here
(`docs/upgrade/GUIDE.md`). The ~31 `worldsim_*.py` copies and the
`wsim_2026-11-07_pre_speedups/` and `wsim_2026-11-09_pre_foodflow/` folders
that the docs cite were removed in commit 04a5711. They are still in the
first commit, 3338050:

    git show 3338050:sim/archive/worldsim_2026-10-30_pre_war2.py
    git ls-tree -r --name-only 3338050 sim/archive/

`v1_2026-11-02/` (the last single-file model) and `snaps/` are kept here.
