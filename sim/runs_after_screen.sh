#!/bin/zsh
# After the WP9 screen ends: check and sanity-run `clear_terrain` and `fire`
# (branch clearing-ext, worktree ../world-ext). Two runs at once.
cd /Users/jmitchell/Desktop/world-ext/sim
export WORLDSIM_RUNS=/Users/jmitchell/Desktop/world/sim/runs
while pgrep -f "wp9_screen.py run" >/dev/null; do sleep 60; done
PY=~/.venvs/worldsim/bin/python
STD=(--peoples peoples_regional --starts 20 --start-vary 0.1 --vary 0 --sites sites_v3.json --frame-every 100 --no-video)
$PY worldsim.py $STD --years 1000 --seed 101 --off clear_terrain,fire --out wp8k_off_seed101 > $WORLDSIM_RUNS/wp8k_off_seed101.log 2>&1 &
$PY worldsim.py $STD --years 3000 --seed 101 --out wp8k_sanity_seed101 > $WORLDSIM_RUNS/wp8k_sanity_seed101.log 2>&1 &
wait
