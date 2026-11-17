"""
Check whether a code change alters the simulation, from a saved late-game
state instead of a fresh multi-thousand-year run (2026-11-07). A short test
from year 0 never reaches the war, voyage and city code; a saved state at
year 5000 exercises all of it in a few seconds per tick.

  # once: run to a year and save the whole Sim. Large (~300 MB at year
  # 5000): keep it outside Dropbox. Arguments after -- are worldsim.py's.
  python snapcheck.py save /tmp/s5000.pkl --year 5000 -- \\
      --peoples peoples_regional --starts 20 --start-vary 0.1 --vary 0 \\
      --sites sites_v2.json --seed 101 --years 8000
  # run N ticks from it with the wsim package in DIR (default: this
  # folder's), writing a digest of every part of the state
  python snapcheck.py run /tmp/s5000.pkl --ticks 20 --digest new.json
  python snapcheck.py run /tmp/s5000.pkl --ticks 20 --code OLD --digest old.json
  python snapcheck.py diff old.json new.json

DIR must hold wsim/ and the roster modules (HERE in params.py), with the
map at DIR/../gis/world.gpkg. On load, the per-tick caches and
power_dist's cache are cleared, so versions whose cache layout differs can
be compared; both runs then start from the same empty caches.
"""
import argparse
import hashlib
import json
import os
import pickle
import struct
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# caches, not state; the food graph and its version are rebuilt from the
# travel graph (World.food_graph)
SKIP = {"_pt", "_sim", "pdist", "fdist", "frames", "Gf", "fver",
        "_sea_food"}


def canon(x, h):
    """Feed a canonical encoding of x into hash h (dicts in order, sets
    sorted, arrays by dtype, shape and bytes)."""
    if isinstance(x, np.ndarray):
        h.update(f"A{x.dtype}{x.shape}".encode())
        if x.dtype == object:
            for v in x.ravel():
                canon(v, h)
        else:
            h.update(np.ascontiguousarray(x).tobytes())
    elif isinstance(x, np.random.Generator):
        canon(x.bit_generator.state, h)
    elif isinstance(x, (bool, np.bool_)):
        h.update(b"b1" if x else b"b0")
    elif isinstance(x, (float, np.floating)):
        h.update(b"f" + struct.pack("<d", float(x)))
    elif isinstance(x, (int, np.integer)):
        h.update(f"i{int(x)};".encode())
    elif isinstance(x, str):
        h.update(f"s{len(x)}:".encode() + x.encode())
    elif x is None:
        h.update(b"N")
    elif isinstance(x, dict):
        h.update(f"d{len(x)}".encode())
        for k, v in x.items():
            canon(k, h)
            canon(v, h)
    elif isinstance(x, (list, tuple)):
        h.update(f"l{len(x)}".encode())
        for v in x:
            canon(v, h)
    elif isinstance(x, (set, frozenset)):
        parts = []
        for v in x:
            g = hashlib.sha1()
            canon(v, g)
            parts.append(g.digest())
        h.update(f"S{len(x)}".encode() + b"".join(sorted(parts)))
    elif hasattr(x, "indptr") and hasattr(x, "data"):     # scipy sparse
        canon((x.shape, x.data, x.indices, x.indptr), h)
    elif hasattr(x, "__dict__") and type(x).__module__.startswith("wsim"):
        canon({k: v for k, v in vars(x).items() if k not in SKIP}, h)
    else:
        h.update(f"<{type(x).__name__}>".encode())


def digest(sim):
    out = {}
    for k, v in vars(sim).items():
        if k in SKIP:
            continue
        h = hashlib.sha1()
        canon(v, h)
        out[k] = h.hexdigest()
    return out


def cmd_save(a, rest):
    sys.path.insert(0, HERE)
    import worldsim
    sim, _, t0 = worldsim.make_sim(rest)
    while sim.year < a.year:
        sim.step()
        if sim.tick % 100 == 0:
            print(f"yr {sim.year}  [{time.time() - t0:.0f}s]", flush=True)
    with open(a.state, "wb") as fh:
        pickle.dump(sim, fh, protocol=5)
    print(f"saved year {sim.year} -> {a.state}")


def cmd_run(a, rest):
    code = os.path.abspath(a.code or HERE)
    sys.path.insert(0, code)
    import wsim
    if os.path.dirname(os.path.dirname(os.path.abspath(wsim.__file__))) \
            != code:
        sys.exit(f"wsim was not imported from {code}")
    with open(a.state, "rb") as fh:
        sim = pickle.load(fh)
    if hasattr(sim, "upgrade"):
        sim.upgrade()       # a state saved by older code
    sim.pdist, sim._pt, sim._sim = {}, {}, {}
    if hasattr(sim, "fdist"):
        sim.fdist = {}
    t0 = time.time()
    for _ in range(a.ticks):
        sim.step()
    dt = time.time() - t0
    d = digest(sim)
    d["_meta"] = dict(code=code, year=sim.year, ticks=a.ticks,
                      seconds=round(dt, 2))
    with open(a.digest, "w") as fh:
        json.dump(d, fh, indent=0, sort_keys=True)
    print(f"{a.ticks} ticks to year {sim.year} in {dt:.1f}s "
          f"({dt / a.ticks:.2f}s/tick) -> {a.digest}")


def cmd_diff(a, rest):
    x, y = (json.load(open(p)) for p in (a.a, a.b))
    keys = sorted((set(x) | set(y)) - {"_meta"})
    bad = [k for k in keys if x.get(k) != y.get(k)]
    for k in bad:
        print(f"differs: {k}")
    for p, d in ((a.a, x), (a.b, y)):
        m = d.get("_meta", {})
        print(f"{p}: {m.get('ticks')} ticks, {m.get('seconds')}s")
    print("IDENTICAL" if not bad else f"{len(bad)} of {len(keys)} differ")
    sys.exit(1 if bad else 0)


def main():
    argv = sys.argv[1:]
    rest = []
    if "--" in argv:
        i = argv.index("--")
        argv, rest = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("save")
    s.add_argument("state")
    s.add_argument("--year", type=int, required=True)
    r = sub.add_parser("run")
    r.add_argument("state")
    r.add_argument("--ticks", type=int, default=20)
    r.add_argument("--code", default=None)
    r.add_argument("--digest", required=True)
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    a = ap.parse_args(argv)
    dict(save=cmd_save, run=cmd_run, diff=cmd_diff)[a.cmd](a, rest)


if __name__ == "__main__":
    main()
