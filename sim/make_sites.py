"""
Place the world's unique resources and domestication hearths, and write
them to sites.json (read by worldsim.py). The placement is drawn once with
a fixed seed, so it is part of the world; worldsim's --shuffle-sites draws
a fresh placement from the run seed instead (same rules).

Run:  ~/.venvs/worldsim/bin/python make_sites.py [--seed 1] [--v2 | --v3]

v2 (U, 2026-10-30; kinds, rules and numbers C): landmass quotas (every
landmass of 0.1M km2+ gets at least one of the 45 unique-resource sites,
the rest shared by area), more kinds (woods, fibres, clay, obsidian), and
precious metals on top (16 sites shared by area with no minimum: placer
gold, lode gold, silver). Hearths are those of v1 (U: unchanged).
Writes sites_v2.json.

v3 (U, 2026-11-19, WP8): the v2 rules on world_v2.gpkg (the climate's
biomes and rivers), with the hearths placed afresh by the v1 rule on the
same world, since the old ones sat on the drawn biomes. Capacity terms as
the simulator's defaults (`climate_fields`, `floodplain`). Writes
sites_v3.json; sites.json and sites_v2.json stay as they were, for the
runs that used them.
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


N_UNIQUE, N_PRECIOUS, MIN_AREA = 45, 16, 1e5
KIND_MAX = 5
PRECIOUS = {"placer gold": 5, "lode gold": 5, "silver": 6}


def quotas(area, n, minimum):
    """Largest-remainder shares of n by area, at least `minimum` each."""
    q = np.full(len(area), minimum, int)
    rest = n - q.sum()
    share = area / area.sum() * rest
    q += np.floor(share).astype(int)
    left = n - q.sum()
    q[np.argsort(-(share - np.floor(share)))[:left]] += 1
    return q


def site_rules(W):
    from worldsim import BIOMES
    b = W.biome
    B = {n: BIOMES.index(n) for n in BIOMES}
    alat = np.abs(W.lat)
    forest, jungle = b == B["Temperate forest"], b == B["Jungle"]
    grass, desert = b == B["Grassland"], b == B["Desert"]
    uniq = {
        "amber": W.coastal & (alat > 40) & (forest | (b == B["Tundra"])),
        "incense": desert | (grass & (W.dryness > 0.5)),
        "electrum": W.river & (W.relief > 0.4),
        "lapis": (W.relief > 0.9) & (desert | grass | (b == B["Tundra"])),
        "ivory": (jungle | grass) & (alat < 30),
        "purple dye": W.coastal & (W.pn > 0.5) & (alat < 40),
        "spice": jungle & W.coastal,
        "jade": (W.relief > 0.6) & forest,
        "pearls": W.coastal & (W.pn > 0.3) & (alat < 30),
        "fragrant timber": forest & (W.relief > 0.5),
        "dark hardwood": jungle & ~W.coastal & (W.relief < 0.6),
        "fine fibre": W.river & (grass | forest) & (W.relief < 0.5),
        "cotton fibre": W.river & (alat < 35) &
        (desert | (grass & (W.dryness > 0.4))),
        "fine clay": W.river & (jungle | forest) & (W.relief < 0.3),
        "obsidian": W.relief > 0.9,
    }
    prec = {
        "placer gold": W.river & (W.relief > 0.4),
        "lode gold": W.relief > 0.8,
        "silver": W.relief > 0.7,
    }
    return uniq, prec


def place_sites_v2(W, seed, hearths):
    """Unique resources by landmass quota, then precious metals."""
    from worldsim import gc_km
    rng = np.random.default_rng(seed)
    lm, la = W.landmass, W.landmass_area
    big = np.nonzero(la >= MIN_AREA)[0]
    big = big[np.argsort(la[big])]                 # smallest first
    uniq, prec = site_rules(W)
    taken, out, notes = [], [], []

    def ok_cells(mask, l, kind_cells, kind_sep):
        cand = np.nonzero(mask & (lm == l))[0]
        for c in taken:
            cand = cand[gc_km(W.xyz, c, cand) > 300]
        for c in kind_cells:
            cand = cand[gc_km(W.xyz, c, cand) > kind_sep]
        return cand

    def fill(rules, q, cap, label):
        got = {k: [] for k in rules}
        for l, n in zip(big, q):
            for _ in range(n):
                order = sorted(rules, key=lambda k: (len(got[k]),
                                                     rng.random()))
                pick = None
                for sep in (1500, 800):
                    for k in order:
                        if len(got[k]) >= cap.get(k, KIND_MAX):
                            continue
                        cand = ok_cells(rules[k], l, got[k], sep)
                        if len(cand):
                            pick = (k, int(rng.choice(cand)))
                            break
                    if pick:
                        break
                if pick is None:
                    # no rule fits here: the least-placed kind, anywhere on
                    # this landmass
                    k = order[0]
                    cand = ok_cells(np.ones(W.N, bool), l, [], 0)
                    if not len(cand):
                        cand = np.nonzero(lm == l)[0]
                    pick = (k, int(rng.choice(cand)))
                    notes.append(f"{label} {k}: rule relaxed on landmass {l}")
                k, c = pick
                got[k].append(c)
                taken.append(c)
                out.append(dict(kind=k, row=int(W.row[c]), col=int(W.col[c]),
                                landmass=int(l),
                                precious=label == "precious"))
        return got

    fill(uniq, quotas(la[big], N_UNIQUE, 1), {}, "unique")
    fill(prec, quotas(la[big], N_PRECIOUS, 0), PRECIOUS, "precious")
    return dict(resources=out, hearths=hearths, seed=seed, version=2,
                notes=notes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--v2", action="store_true")
    ap.add_argument("--v3", action="store_true")
    a = ap.parse_args()
    import worldsim
    if a.v3:
        W = worldsim.World(worldsim.world_path("v2"))
        W.use_climate()
        W.floodplain = True
        W.derive_rivers()
        s = place_sites_v2(W, a.seed, place_sites(W, a.seed)["hearths"])
        s["version"], s["world"] = 3, "world_v2.gpkg"
        name = "sites_v3.json"
    elif a.v2:
        W = worldsim.World(worldsim.world_path("v1"))
        with open(os.path.join(HERE, "sites.json")) as fh:
            h = json.load(fh)["hearths"]
        s = place_sites_v2(W, a.seed, h)
        name = "sites_v2.json"
    else:
        W = worldsim.World(worldsim.world_path("v1"))
        s = place_sites(W, a.seed)
        name = "sites.json"
    with open(os.path.join(HERE, name), "w") as fh:
        json.dump(s, fh, indent=1)
    print(f"{len(s['resources'])} resources, {len(s['hearths'])} hearths "
          f"-> {name}")
    for n in s.get("notes", []):
        print("  " + n)


if __name__ == "__main__":
    main()
