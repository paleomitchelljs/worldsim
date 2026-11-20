"""WP9 stage B: Morris screen (elementary effects) of 30 parameters.

    python wp9_screen.py design        # write the design (once)
    python wp9_screen.py run [-j 8]    # run every point not yet done
    python wp9_screen.py status

The design is r = 8 trajectories of k + 1 = 31 points (SALib, 4 levels),
all on seed 101 (common random numbers: a point differs from the one
before it only in one parameter and in the path noise that change sets
off). Seed noise is read on the default point over six seeds: the
baseline batch (seeds 101-104, 106) and `base_seed105` here.

Each run keeps only metrics.json, run.json, final_maps.png and the tail
of its log (U, 2026-11-20: summaries only), in runs/wp9b/<name>/; the
full run folder is deleted once metrics.json is written. Ranges are a
factor of 2 either way on a log scale (C, the brief's default) except
where a bound would leave the parameter's meaning (marked lin).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, SIM)
import runroot  # noqa: E402
from wsim import params  # noqa: E402

OUT = os.path.join(runroot.root(), "wp9b")
DESIGN = os.path.join(HERE, "..", "baseline", "wp9b_design.json")
SEED, R, LEVELS = 101, 8, 4
STD = ["--peoples", "peoples_regional", "--starts", "20", "--start-vary",
       "0.1", "--vary", "0", "--sites", "sites_v3.json", "--years", "8000",
       "--frame-every", "100", "--no-video"]
KEEP = ("metrics.json", "run.json", "final_maps.png")

# (name, subsystem, scale, low, high); log ranges are default / 2 .. x 2
LIN = {"PATH_MIN": (0.3, 0.9), "BUD_PRESS": (0.3, 0.6),
       "ODDS_MID": (0.5, 1.0)}
FACTORS = [
    ("R_SCALE", "growth"), ("R_MAX", "growth"), ("BUD_PRESS", "budding"),
    ("RAID_RATE", "raids"), ("KIN_RAID", "raids"), ("FEUD_K", "raids"),
    ("WAR_BASE", "war"), ("WAR_GAIN", "war"), ("WAR_IDLE", "war"),
    ("ODDS_MID", "war"), ("SITE_DEF_SD", "war"),
    ("COH_DECAY", "states"), ("REVOLT_BASE", "states"), ("UNREST", "states"),
    ("SUCC_P", "states"), ("EXT_SUBJ", "extraction"),
    ("FF_RENT", "food flows"), ("FF_TAX", "food flows"),
    ("FF_TRADE", "trade"), ("FF_KM", "food carriage"),
    ("TRADE_RATE2", "trade"), ("ACC", "acculturation"),
    ("EXP_SCALE", "experience"), ("PATH_MIN", "experience"),
    ("DEV_K", "development"), ("AGRI_INV", "technology"),
    ("METAL_INV", "technology"), ("ADM_INV", "technology"),
    ("CLIM_AMP", "climate"), ("PL_EMERGE", "plague"),
]


def bounds():
    out = []
    for name, _ in FACTORS:
        v = float(getattr(params, name))
        if name in LIN:
            out.append(("lin", *LIN[name]))
        else:
            out.append(("log", np.log10(v / 2), np.log10(v * 2)))
    return out


def design():
    from SALib.sample import morris
    b = bounds()
    problem = {"num_vars": len(FACTORS), "names": [n for n, _ in FACTORS],
               "bounds": [[lo, hi] for _, lo, hi in b]}
    X = morris.sample(problem, N=R, num_levels=LEVELS, seed=9)
    vals = np.array([[10 ** x if s == "log" else x for x, (s, _, _) in
                      zip(row, b)] for row in X])
    points = [{"name": f"p{i:03d}", "seed": SEED,
               "set": {n: float(v) for (n, _), v in zip(FACTORS, row)}}
              for i, row in enumerate(vals)]
    points.append({"name": "base_seed105", "seed": 105, "set": {}})
    os.makedirs(os.path.dirname(DESIGN), exist_ok=True)
    with open(DESIGN, "w") as fh:
        json.dump({"problem": problem, "scales": [s for s, _, _ in b],
                   "unit_X": X.tolist(), "levels": LEVELS, "r": R,
                   "points": points}, fh, indent=1)
    print(f"{len(points)} points -> {DESIGN}")


def done(name):
    return os.path.exists(os.path.join(OUT, name, "metrics.json"))


def launch(pt):
    name = f"wp9b_{pt['name']}"
    cmd = [sys.executable, os.path.join(SIM, "worldsim.py"), *STD,
           "--seed", str(pt["seed"]), "--out", name]
    for k, v in pt["set"].items():
        cmd += ["--set", f"{k}={v!r}"]
    log = open(os.path.join(OUT, f"{pt['name']}.log"), "w")
    return subprocess.Popen(cmd, cwd=SIM, stdout=log, stderr=subprocess.STDOUT)


def harvest(pt, rc):
    src = os.path.join(runroot.root(), f"wp9b_{pt['name']}")
    dst = os.path.join(OUT, pt["name"])
    os.makedirs(dst, exist_ok=True)
    for f in KEEP:
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    lp = os.path.join(OUT, f"{pt['name']}.log")
    with open(lp) as fh:
        tail = fh.readlines()[-40:]
    with open(os.path.join(dst, "log_tail.txt"), "w") as fh:
        fh.write(f"exit {rc}\n" + "".join(tail))
    os.remove(lp)
    shutil.rmtree(src, ignore_errors=True)


def run(jobs):
    with open(DESIGN) as fh:
        pts = [p for p in json.load(fh)["points"] if not done(p["name"])]
    # the seed-noise point first, so it is ready with the first trajectory
    pts.sort(key=lambda p: p["name"] != "base_seed105")
    os.makedirs(OUT, exist_ok=True)
    live, t0 = {}, time.time()
    while pts or live:
        while pts and len(live) < jobs:
            p = pts.pop(0)
            live[p["name"]] = (p, launch(p))
        time.sleep(20)
        for n, (p, proc) in list(live.items()):
            rc = proc.poll()
            if rc is not None:
                harvest(p, rc)
                del live[n]
                print(f"{time.strftime('%H:%M')} {n} exit {rc}; "
                      f"{len(pts)} queued, {len(live)} running, "
                      f"{(time.time() - t0) / 3600:.1f} h", flush=True)


def status():
    with open(DESIGN) as fh:
        pts = json.load(fh)["points"]
    ok = [p["name"] for p in pts if done(p["name"])]
    print(f"{len(ok)} of {len(pts)} done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["design", "run", "status"])
    ap.add_argument("-j", type=int, default=8)
    a = ap.parse_args()
    {"design": design, "run": lambda: run(a.j), "status": status}[a.what]()
