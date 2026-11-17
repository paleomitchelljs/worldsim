"""
Place the world's unique resources and domestication hearths, and write
them to sites.json (read by worldsim.py). The placement is drawn once with
a fixed seed, so it is part of the world; worldsim's --shuffle-sites draws
a fresh placement from the run seed instead (same rules).

Run:  ~/.venvs/worldsim/bin/python make_sites.py [--seed 1]
"""
import argparse
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def place_sites(W, seed):
    """Unique resources and hearths: each kind on cells meeting its rule,
    kept apart from each other."""
    from worldsim import BIOMES, gc_km
    rng = np.random.default_rng(seed)
    b = W.biome
    B = {n: BIOMES.index(n) for n in BIOMES}
    alat = np.abs(W.lat)
    # (kind, count, rule)
    RES = [
        ("amber", 4, W.coastal & (alat > 40) &
         np.isin(b, [B["Temperate forest"], B["Tundra"]])),
        ("incense", 4, (b == B["Desert"]) |
         ((b == B["Grassland"]) & (W.dryness > 0.5))),
        ("electrum", 4, W.river & (W.relief > 0.4)),
        ("lapis", 3, (W.relief > 0.9) &
         np.isin(b, [B["Desert"], B["Grassland"], B["Tundra"]])),
        ("ivory", 4, np.isin(b, [B["Jungle"], B["Grassland"]]) & (alat < 30)),
        ("purple dye", 4, W.coastal & (W.pn > 0.5) & (alat < 40)),
        ("spice", 4, (b == B["Jungle"]) & W.coastal),
        ("jade", 3, (W.relief > 0.6) & (b == B["Temperate forest"])),
        ("pearls", 3, W.coastal & (W.pn > 0.3) & (alat < 30)),
        ("silver", 3, W.relief > 0.7),
    ]
    out_res, taken = [], []

    def pick(mask, n, kind_sep, any_sep, weight=None):
        got = []
        cand = np.nonzero(mask)[0]
        for _ in range(n):
            ok = cand.copy()
            for c in taken:
                ok = ok[gc_km(W.xyz, c, ok) > any_sep]
            for c in got:
                ok = ok[gc_km(W.xyz, c, ok) > kind_sep]
            if not len(ok):
                break
            w = None if weight is None else weight[ok] / weight[ok].sum()
            c = int(rng.choice(ok, p=w))
            got.append(c)
            taken.append(c)
        return got

    for kind, n, mask in RES:
        for c in pick(mask, n, 1500, 300):
            out_res.append(dict(kind=kind, row=int(W.row[c]),
                                col=int(W.col[c])))
    # domestication hearths: (kind, biome, count); on the better farm or
    # herd land of the biome
    HEARTH = [("crop", "Grassland", 2), ("crop", "Temperate forest", 2),
              ("crop", "Jungle", 2), ("crop", "Desert", 1),
              ("animal", "Grassland", 2), ("animal", "Desert", 1),
              ("animal", "Tundra", 1), ("animal", "Temperate forest", 1),
              ("animal", "Jungle", 1)]
    out_h = []
    for kind, bn, n in HEARTH:
        m = b == B[bn]
        v = W.farm if kind == "crop" else W.herd
        if bn == "Desert" and kind == "crop":
            m = m & W.river
        if not m.any():
            continue
        good = m & (v >= np.percentile(v[m], 70))
        for c in pick(good, n, 2000, 300):
            out_h.append(dict(kind=kind, biome=bn, row=int(W.row[c]),
                              col=int(W.col[c])))
    return dict(resources=out_res, hearths=out_h, seed=seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    import worldsim
    W = worldsim.World()
    s = place_sites(W, a.seed)
    with open(os.path.join(HERE, "sites.json"), "w") as fh:
        json.dump(s, fh, indent=1)
    print(f"{len(s['resources'])} resources, {len(s['hearths'])} hearths "
          "-> sites.json")


if __name__ == "__main__":
    main()
