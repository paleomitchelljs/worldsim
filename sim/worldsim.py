"""
Zero-player civilization simulator on world.gpkg.

Full documentation: sim/docs/README.md (rules, traits, startup, data).

Peoples (a roster module, --peoples) start as founding bands and grow,
migrate, farm, found cities, form polities, trade, raid, conquer, clear
land, rebel, and collapse on the 0.5-degree world grid. Nobody plays it;
you watch what the map does.

Three layers, each driving the next:

  people     population, people and lineage per land cell. Peoples never
             mix: a cell holds one people or none. Each people starts as
             several founding groups; each group is a lineage with its own
             slightly different traits and its own technology. Lineages
             split (secession, colonies on new land) with small mutations,
             learn technology from lineages they touch, and are absorbed
             into the ruling lineage of their own people over time. A people can move into
             empty land, or into land another people has lost (raided out,
             cleared by conquest, emptied by famine or plague).
  cities     a cell becomes a city when it is dense and locally central
             (river, coast, ore, trade). Each city rules the land nearest
             to it by travel cost, out to its people's administrative reach.
  polities   a set of cities under one capital, ruled by a lineage.
             Tolerant neighbours trade, ally and may fuse into one state,
             the threshold rising with how unlike they are (kin easily,
             other peoples only if both are highly tolerant). Polities make
             war on
             neighbours (land or, for sailors, sea), take cities, absorb or
             clear conquered foreigners, trade with partners, and fragment
             when cohesion (asabiya) runs down and provinces lie far from
             the capital.

One tick is DT years. The world file is opened read-only.

Run:  ~/.venvs/worldsim/bin/python worldsim.py --seed 1 --years 4000
Out:  <runs root>/seed<N>/, or --out (runroot.py; root is $WORLDSIM_RUNS
      or sim/runs)  (history.gif, final.png, legacy.png,
      population.png, events.txt, cities.csv, polities.csv, timeseries.csv)
"""
import argparse
import importlib
import os
import platform
import shlex
import subprocess
import sys
import time

import numpy as np

import runroot
from wsim import params

# Only wsim.params is imported here. The command line writes its overrides
# into params before any other wsim module loads (make_sim), so every module
# that does `from .params import *`, and every default argument bound to a
# constant at import, sees the value as set.


def __getattr__(name):
    """Library use (worldsim.World, worldsim.font, constants such as
    worldsim.NY): load the wsim modules on first use."""
    from wsim import geo, output, render, sim
    for m in (params, geo, render, sim, output):
        if hasattr(m, name):
            return getattr(m, name)
    raise AttributeError(f"module 'worldsim' has no attribute {name!r}")


def setp(name, value):
    """Override a constant in wsim.params and in every wsim module already
    loaded (snapcheck.py changes constants on a loaded state)."""
    for m in list(sys.modules.values()):
        if getattr(m, "__name__", "").startswith("wsim") and \
                hasattr(m, name):
            setattr(m, name, value)


def code_version():
    """Git commit of this folder and whether tracked files differ from it
    (None when git is unavailable)."""
    def git(*a):
        return subprocess.run(["git", "-C", runroot.HERE, *a],
                              capture_output=True, text=True,
                              timeout=20).stdout.strip()
    try:
        commit = git("rev-parse", "HEAD") or None
        dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    except (OSError, subprocess.SubprocessError):
        return dict(commit=None, dirty=None)
    return dict(commit=commit, dirty=dirty if commit else None)


def make_sim(argv=None):
    """Parse the command line and build the Sim (not yet run); returns
    (sim, out folder, start time)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=6000)
    ap.add_argument("--frame-every", type=int, default=20,
                    help="ticks between animation frames")
    ap.add_argument("--homelands", choices=["continents", "anywhere"],
                    default="continents",
                    help="continents: founders start on the two large "
                    "landmasses so peoples meet; anywhere: any good site")
    ap.add_argument("--vary", type=float, default=0.0,
                    help="per-run trait jitter (0 = peoples.py as written; "
                    "0.3 = strong)")
    ap.add_argument("--peoples", default="peoples",
                    help="module in sim/ defining PEOPLES "
                    "(e.g. peoples_fantasy)")
    ap.add_argument("--start-pool", type=float, default=0.02,
                    help="share of habitable cells founders may start in "
                    "(0 = only the best ~60 sites; 0.3 = wide)")
    ap.add_argument("--starts", type=int, default=3,
                    help="founding groups per people (a roster entry's "
                    "'starts' overrides)")
    ap.add_argument("--start-vary", type=float, default=0.05,
                    help="trait jitter between a people's founding groups")
    ap.add_argument("--drift", type=float, default=0.06,
                    help="trait mutation when a daughter lineage splits off")
    ap.add_argument("--cluster-km", type=float, default=0,
                    help="if >0, a people's later groups start within this "
                    "distance of its first; 0 = anywhere")
    ap.add_argument("--settle-drift", type=float, default=0.03,
                    help="trait mutation when a lineage settles a new 5-deg "
                    "region (founds a daughter lineage); 0 = off")
    ap.add_argument("--size-food", choices=["none", "kleiber"],
                    default="kleiber",
                    help="kleiber: each head eats size**0.75 humans' food, "
                    "so large peoples live sparser")
    ap.add_argument("--city-pop", type=float, default=params.CITY_POP,
                    help="food-equivalent cell population that founds a "
                    "city (a roster `city` factor scales it per people)")
    ap.add_argument("--city-cap", type=float, nargs=2, default=None,
                    metavar=("CAP0", "CAP1"),
                    help="turn on the city size cap = city-pop * (CAP0 + "
                    "CAP1 * admin^2); off by default (the old runs used 3 40)")
    ap.add_argument("--start-mode", choices=["wander", "score"],
                    default="wander",
                    help="wander: founders random-walk toward suitable land "
                    "before the run; score: pick sites by suitability")
    ap.add_argument("--wander-steps", type=int, default=2000)
    ap.add_argument("--dragon-shun", type=float, default=params.DRAGON_SHUN,
                    help="dragons do not settle near cells holding this "
                    "share of their ward size (0 = off)")
    ap.add_argument("--dragon-penalty", type=float, default=params.DRAGON_PEN,
                    help="cut in the yearly growth rate per unit of dragon "
                    "hazard at the worst group size (dragons feature)")
    ap.add_argument("--off", default="",
                    help="structural mechanics to switch off, comma-"
                    "separated, or 'all': " + ",".join(params.FEATURES))
    ap.add_argument("--set", action="append", default=[],
                    metavar="NAME=VALUE",
                    help="override a numeric constant (repeatable)")
    ap.add_argument("--shuffle-sites", action="store_true",
                    help="draw resource sites and hearths from the run seed "
                    "instead of sites.json")
    ap.add_argument("--sites", default="sites.json",
                    help="site file (sites_v2.json: landmass quotas, more "
                    "kinds, precious metals)")
    ap.add_argument("--out", default=None,
                    help="run folder; a bare name goes in the runs root "
                    "($WORLDSIM_RUNS or sim/runs); default seed<N>")
    a = ap.parse_args(argv)
    for kv in a.set:
        k, v = kv.split("=", 1)
        g = vars(params)
        if k not in g or not isinstance(g[k], (int, float)):
            ap.error(f"--set: no numeric constant {k}")
        setp(k, type(g[k])(float(v)) if isinstance(g[k], float) else int(v))
    off = params.FEATURES if a.off == "all" else \
        [x for x in a.off.split(",") if x]
    bad = set(off) - set(params.FEATURES)
    if bad:
        ap.error(f"unknown feature(s): {', '.join(sorted(bad))}")
    setp("CITY_POP", a.city_pop)
    setp("DRAGON_PEN", a.dragon_penalty)
    setp("DRAGON_SHUN", a.dragon_shun)
    if a.city_cap is not None:
        setp("CITY_CAP", True)
        setp("CITY_CAP0", a.city_cap[0])
        setp("CITY_CAP1", a.city_cap[1])
    from wsim.geo import World, vary_peoples
    from wsim.sim import Sim
    out = runroot.path(a.out or f"seed{a.seed}")
    t0 = time.time()
    code = code_version()
    world = World()
    print(f"world: {world.N} land cells, loaded in {time.time()-t0:.1f}s")
    sim = Sim(world, seed=a.seed, years=a.years,
              frame_every=a.frame_every, out=out, homelands=a.homelands,
              peoples=vary_peoples(importlib.import_module(
                  a.peoples).PEOPLES, a.seed, a.vary),
              start_pool=a.start_pool, starts=a.starts,
              start_vary=a.start_vary, drift=a.drift,
              cluster_km=a.cluster_km, settle_drift=a.settle_drift,
              size_food=a.size_food, start_mode=a.start_mode,
              wander_steps=a.wander_steps, off=off,
              shuffle_sites=a.shuffle_sites, sites=a.sites)
    sim.vary = a.vary
    sim.overrides = a.set
    sim.manifest = dict(
        code=code,
        command=shlex.join(sys.argv if argv is None
                           else ["worldsim.py", *argv]),
        python=platform.python_version(), numpy=np.__version__,
        t0=t0)
    for p in sim.P:
        print(f"  {p['key']} {p['label']:16s} r={p['r']:.4f} " +
              " ".join(f"{t[:4]}={p.get(t, 0.5):.2f}" for t in params.TRAITS))
    return sim, out, t0


def main():
    sim, out, t0 = make_sim()
    sim.run()
    from wsim.output import write_outputs
    write_outputs(sim, out)
    print(f"done in {time.time()-t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
