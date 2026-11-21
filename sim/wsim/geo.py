"""Geometry, the world grid, small math helpers."""
import math
import os
import sqlite3
import zlib
import numpy as np
from scipy import ndimage, sparse
from scipy.spatial import cKDTree

from .params import *  # noqa: F401,F403


def stream(seed, name):
    """The random stream `name` of a run with this seed (WP1 stage F): a
    child of the seed keyed on the name, so each subsystem's draws depend
    only on the seed and its own name, never on how often another
    subsystem drew."""
    return np.random.default_rng(np.random.SeedSequence(
        seed, spawn_key=(zlib.crc32(name.encode()),)))


def unit_xyz(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo),
                     np.sin(la)], -1)


def gc_km(xyz, i, j=None):
    """Great-circle km between cell i and cells j (every cell if None).
    The chord is summed per coordinate: the same result, bit for bit, as
    np.linalg.norm(axis=-1), and ~3.7x faster on the whole grid."""
    d = (xyz if j is None else xyz[j]) - xyz[i]
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    ch = np.sqrt(x * x + y * y + z * z)
    return 2 * R_EARTH * np.arcsin(np.clip(ch / 2, 0, 1))


def vary_peoples(peoples, seed, amount):
    """Jitter every people's cultural traits for one run, on the logit
    scale by N(0, amount), so archetypes bend without all collapsing to the
    middle. Intrinsic traits (r, biome affinity, size) are left as given."""
    if amount <= 0:
        return [dict(p) for p in peoples]
    rng = stream(seed, "vary")
    out = []
    for p in peoples:
        q = dict(p)
        for t in TRAITS:
            x = np.clip(p.get(t, 0.5), 0.02, 0.98)
            z = math.log(x / (1 - x)) + rng.normal(0, 2.5 * amount)
            q[t] = round(float(1 / (1 + math.exp(-z))), 2)
        out.append(q)
    xr = stream(seed, "vary_x")
    for p, q in zip(peoples, out):
        for t in XTRAITS:
            x = np.clip(p.get(t, 0.5), 0.02, 0.98)
            z = math.log(x / (1 - x)) + xr.normal(0, 2.5 * amount)
            q[t] = round(float(1 / (1 + math.exp(-z))), 2)
    return out


# ---- world ---------------------------------------------------------------
CELL_COLS = ["row", "col", "lon", "lat", "area_km2", "fic_land",
             "fic_elev_km", "fic_biome", "fic_soil_bar_value",
             "syn_relief_km", "syn_discharge_m3s", "syn_river",
             "syn_lake", "syn_reach_productivity", "syn_dist_copper_km",
             "syn_dist_tin_km", "syn_dist_iron_km", "syn_surface_lith",
             "syn_alluvial_fill", "syn_runoff_m_yr", "fid",
             "syn_flow_to", "syn_basin_id", "syn_wetness",
             "fic_dist_coast_km"]
CELL_TEXT = {"fic_biome", "syn_surface_lith", "syn_biome"}
# read when the world file has them (world_v2.gpkg, WP8); syn_biome, the
# climate's biome, then replaces fic_biome (D10, U 2026-11-19)
# syn_aridity_season (the aridity with the rain's timing, 2026-11-20) is
# read in place of syn_aridity when present
CELL_OPT = ["syn_aridity", "syn_aridity_season", "syn_gdd", "syn_biome"]


def load_cells(gpkg):
    """The cells table's columns as arrays: numbers as float (NULL ->
    NaN), CELL_TEXT columns as objects (NULL -> None). Turning
    the SQLite rows into arrays is most of World()'s load time, so the
    arrays are cached in the runs root (_world_cache.npz), keyed on the
    world file's path, size and modification time; any change to the file
    rebuilds the cache."""
    import runroot
    st = os.stat(gpkg)
    con = sqlite3.connect(f"file:{os.path.abspath(gpkg)}?mode=ro", uri=True)
    have = {r[1] for r in con.execute("pragma table_info(cells)")}
    cols = CELL_COLS + [c for c in CELL_OPT if c in have]
    key = f"{os.path.abspath(gpkg)}|{st.st_size}|{st.st_mtime_ns}|" + \
        ",".join(cols)
    # one cache per world file, so runs on two worlds do not evict each other
    stem = os.path.splitext(os.path.basename(gpkg))[0]
    path = os.path.join(runroot.root(), "_world_cache.npz" if stem == "world"
                        else f"_world_cache_{stem}.npz")
    try:
        with np.load(path) as z:
            if str(z["key"]) == key:
                con.close()
                return {c: (np.where(z[c] == "", None, z[c].astype(object))
                            if c in CELL_TEXT else z[c]) for c in cols}
    except (OSError, KeyError, ValueError):
        pass
    rows = con.execute(f"select {','.join(cols)} from cells").fetchall()
    con.close()
    d = {c: np.array([r[k] for r in rows], object) if c in CELL_TEXT else
         np.array([np.nan if r[k] is None else r[k] for r in rows], float)
         for k, c in enumerate(cols)}
    # several runs may start at once: write under a unique name, then rename
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "wb") as fh:
        np.savez(fh, key=np.array(key), **{
            c: np.array(["" if v is None else v for v in a], str)
            if c in CELL_TEXT else a for c, a in d.items()})
    os.replace(tmp, path)
    return d


class World:
    def __init__(self, gpkg=GPKG):
        self.gpkg = os.path.normpath(gpkg)
        d = load_cells(gpkg)

        def num(c, fill=0.0):
            a = d[c]
            return np.where(np.isfinite(a), a, fill)

        row = num("row").astype(int)
        col = num("col").astype(int)
        land2 = np.zeros((NY, NX), bool)
        land2[row, col] = num("fic_land") > 0
        prod2 = np.zeros((NY, NX))
        prod2[row, col] = num("syn_reach_productivity")
        self.land2 = land2

        L = num("fic_land") > 0
        self.row, self.col = row[L], col[L]
        self.lon, self.lat = num("lon")[L], num("lat")[L]
        self.area = num("area_km2")[L]
        self.elev = num("fic_elev_km")[L]
        self.relief = num("syn_relief_km")[L]
        # swamp layer (derive_world.swamp_wetness): 0-1
        self.wet = num("syn_wetness")[L]
        self.Q = num("syn_discharge_m3s")[L]
        self.river = num("syn_river")[L] > 0
        # river network: downstream land cell (or -1) and upstream river
        # cells, for travel along rivers; basin ids for river trade
        fid = num("fid").astype(np.int64)
        fl = num("syn_flow_to", -1).astype(np.int64)
        lidx = {int(f) - 1: k for k, f in enumerate(fid[L])}  # flow_to is
        # a 0-based cell index (fid - 1)
        down = np.array([lidx.get(int(t), -1) for t in fl[L]])
        # full drainage network (every land cell), for routing discharge
        # and for rivers that change course
        self.flow = down.copy()
        self.runoff = num("syn_runoff_m_yr", 0.4)[L]
        self.alluvial = num("syn_alluvial_fill")[L] > 0
        self.basin = num("syn_basin_id", -1).astype(np.int64)[L]
        self.lake = num("syn_lake")[L] > 0
        self.d_cu = num("syn_dist_copper_km", 9e9)[L]
        self.d_sn = num("syn_dist_tin_km", 9e9)[L]
        self.d_fe = num("syn_dist_iron_km", 9e9)[L]
        soil = num("fic_soil_bar_value", np.nan)[L]
        biome = np.array(d["syn_biome" if "syn_biome" in d else "fic_biome"],
                         object)[L]
        lith = np.array(d["syn_surface_lith"], object)[L]
        self.biome = np.array([BIOMES.index(b) if b in BIOMES else 4
                               for b in biome])
        self.N = N = L.sum()
        self.xyz = unit_xyz(self.lon, self.lat)
        self.yield_ = self.runoff * self.area * 1e6 / 3.156e7   # m3/s
        self.route()

        idx = -np.ones((NY, NX), int)
        idx[self.row, self.col] = np.arange(N)
        self.idx2 = idx
        offs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1),
                (1, 0), (1, 1)]
        nb = -np.ones((N, 8), int)
        nd = np.zeros((N, 8))
        coastal = np.zeros(N, bool)
        coast_prod = np.zeros(N)
        for k, (dr, dc) in enumerate(offs):
            r2 = self.row + dr
            c2 = (self.col + dc) % NX
            ok = (r2 >= 0) & (r2 < NY)
            r2c = np.clip(r2, 0, NY - 1)
            nb[:, k] = np.where(ok, idx[r2c, c2], -1)
            sea = ok & ~land2[r2c, c2]
            coastal |= sea
            coast_prod = np.maximum(coast_prod,
                                    np.where(sea, prod2[r2c, c2], 0))
            dy = 0.5 * 111.2 * dr
            dx = 0.5 * 111.2 * np.cos(np.radians(self.lat)) * dc
            nd[:, k] = np.maximum(np.hypot(dx, dy), 1.0)
        self.nb, self.coastal = nb, coastal
        self.nd = nd
        self.defence = np.array([TERRAIN_DEF[b] for b in BIOMES])[self.biome] \
            * (1 + DEF_RELIEF * np.clip(self.relief, 0, 1.5)) * \
            (1 + DEF_WET * self.wet)
        self.defence0 = self.defence.copy()
        self.colonize = np.exp(-np.clip(self.relief, 0, None) / COL_RELIEF) \
            * (1 - COL_WET * self.wet)

        # undirected edge list (each land pair once)
        e1, e2, ek = [], [], []
        for k in (2, 4, 6, 7):          # NE, E, S, SE
            j = nb[:, k]
            m = j >= 0
            e1.append(np.nonzero(m)[0]); e2.append(j[m])
            ek.append(np.full(int(m.sum()), k))
        self.E1, self.E2 = np.concatenate(e1), np.concatenate(e2)
        self.EK = np.concatenate(ek)

        # short sea crossings between coastal cells
        ci = np.nonzero(coastal)[0]
        self.coast_idx = ci
        self.coast_tree = cKDTree(self.xyz[ci])
        pairs = np.array(sorted(self.coast_tree.query_pairs(
            2 * math.sin(STRAIT_KM / R_EARTH / 2))), int)
        if len(pairs):
            a, b = ci[pairs[:, 0]], ci[pairs[:, 1]]
            dkm = 2 * R_EARTH * np.arcsin(np.clip(np.linalg.norm(
                self.xyz[a] - self.xyz[b], axis=1) / 2, 0, 1))
            far = dkm > 90          # not already a land neighbour
            sa, sb, sw = a[far], b[far], 2.0 * dkm[far]
        else:
            sa = sb = sw = np.array([], int)
        self.sea_links = (sa, sb, sw)

        # landmasses (for logging first landings)
        lab, nlab = ndimage.label(land2, structure=np.ones((3, 3)))
        self.landmass = lab[self.row, self.col]
        self.landmass_area = np.bincount(self.landmass, weights=self.area)

        # ---- carrying capacity (people/km2) before people-specific terms
        # (the parts that do not depend on rivers; derive_rivers does the
        # rest, and runs again whenever a river changes course)
        self.fert = np.where(np.isfinite(soil), np.clip((soil + 3.75) / 5.5,
                                                        0, 1), 0.3)
        b = self.biome
        self.pn = np.clip((coast_prod - 0.0003) / 0.0006, 0, 1)
        self.elevpen = np.clip(1 - (self.elev - 1.5) / 1.5, 0.2, 1) / \
            (1 + 0.5 * np.clip(self.relief, 0, 2))
        alluv = np.array([l == "alluvium" for l in lith])
        self.alluvium = alluv               # alluvium at the surface
        self.wetf = np.where(alluv, 1.3, 1.0) * np.where(self.lake, 1.2, 1.0)
        # structural layers: steppe farming (rain-fed part cut far inland on
        # grassland and desert), herding density, dryness
        self.dcoast = num("fic_dist_coast_km", 0.0)[L]
        steppe = np.clip((self.dcoast - STEPPE_KM[0]) /
                         (STEPPE_KM[1] - STEPPE_KM[0]), 0, 1) * \
            np.isin(b, [BIOMES.index("Grassland"), BIOMES.index("Desert")])
        self.steppe = steppe
        self.steppe_cut = steppe
        self.dryness = np.clip(1 - self.runoff / 0.5, 0, 1)
        # climate fields (world_v2.gpkg), used under `climate_fields`
        ai = next((k for k in ("syn_aridity_season", "syn_aridity")
                   if k in d), None)
        self.aridity = num(ai)[L] if ai else None
        self.gdd = num("syn_gdd")[L] if "syn_gdd" in d else None
        self.farm_clim = self.herd_clim = np.ones(N)
        self.herd_density()
        self.ecotones(land2)
        self.derive_rivers()

        # rendering base
        base = np.zeros((NY, NX, 3), np.uint8)
        base[:] = (28, 48, 78)
        bcol = np.array([(62, 96, 58), (176, 160, 118), (128, 138, 84),
                         (84, 112, 72), (176, 182, 184)], np.uint8)
        base[self.row, self.col] = bcol[b]
        shade = np.clip(1 - 0.25 * np.clip(self.relief, 0, 1.5), 0.6, 1)
        base[self.row, self.col] = (base[self.row, self.col] *
                                    shade[:, None]).astype(np.uint8)
        self.base = base
        rows_land = np.nonzero(land2.sum(1) > 40)[0]
        self.r0 = max(0, rows_land.min() - 8)
        self.r1 = min(NY, rows_land.max() + 4)


    def herd_density(self):
        """Herding density (people/km2) before people-specific terms."""
        self.herd = np.array([HERD[x] for x in BIOMES])[self.biome] * \
            np.clip(1 - (self.elev - 2.5) / 1.5, 0.2, 1) * \
            (1 + 0.5 * self.steppe) * self.herd_clim

    def within_biome(self, v):
        """v relative to its biome's area-weighted mean, capped at
        CLIM_RATIO_MAX and renormalised to a mean of 1 in each biome (1
        where a biome's mean is 0)."""
        out = np.ones(self.N)
        for k in range(len(BIOMES)):
            m = self.biome == k
            a = self.area[m]
            x = v[m]
            for _ in range(3):
                mu = (x * a).sum() / max(a.sum(), 1e-9)
                if mu <= 0:
                    break
                x = np.minimum(x / mu, CLIM_RATIO_MAX)
            else:
                out[m] = x / ((x * a).sum() / a.sum())
        return out

    def use_climate(self):
        """`climate_fields` (WP8 stage B): dryness and the steppe from the
        aridity index instead of runoff by biome and distance to the
        coast, and farming and herding gradients within each biome from
        growing-degree days and aridity. Nothing changes on a world
        without the fields."""
        if self.aridity is None or self.gdd is None:
            return
        ai, gdd = self.aridity, self.gdd
        lo, hi = CLIM_STEPPE_AI
        self.steppe = np.clip((lo - ai) / (lo - hi), 0, 1) * np.isin(
            self.biome, [BIOMES.index("Grassland"), BIOMES.index("Desert")])
        self.steppe_cut = np.zeros(self.N)
        self.dryness = np.clip(1 - ai / CLIM_DRY_AI, 0, 1)
        self.farm_clim = self.within_biome(
            np.clip(gdd / CLIM_FARM[0], 0, 1) * np.clip(ai / CLIM_FARM[1], 0, 1))
        self.herd_clim = self.within_biome(
            np.clip(gdd / CLIM_HERD[0], 0, 1) * np.clip(ai / CLIM_HERD[1], 0, 1))
        self.herd_density()
        self.derive_rivers()

    # ---- rivers
    def route(self):
        """Topological levels of the drainage network: a cell's level is
        one more than the highest level draining into it."""
        N, down = self.N, self.flow
        deg = np.bincount(down[down >= 0], minlength=N)
        level = np.zeros(N, int)
        front = list(np.nonzero(deg == 0)[0])
        order = []
        while front:
            nxt = []
            for i in front:
                order.append(i)
                j = down[i]
                if j >= 0:
                    level[j] = max(level[j], level[i] + 1)
                    deg[j] -= 1
                    if deg[j] == 0:
                        nxt.append(j)
            front = nxt
        self.order = np.array(order)
        self.levels = [np.nonzero((level == lv) & (down >= 0))[0]
                       for lv in range(level.max() + 1)]

    def accumulate(self, v):
        """Sum v over each cell and everything upstream of it."""
        acc = v.astype(float).copy()
        for c in self.levels:
            np.add.at(acc, self.flow[c], acc[c])
        return acc

    def derive_rivers(self):
        """Everything that depends on where the rivers run: river links,
        foraging and irrigation, city locus and travel costs."""
        N, b = self.N, self.biome
        coastal, pn = self.coastal, self.pn
        self.down = np.where(self.river, self.flow, -1)
        self.down[self.down >= 0] = np.where(
            self.river[self.down[self.down >= 0]], self.down[self.down >= 0],
            -1)
        self.up = [[] for _ in range(N)]
        for k in np.nonzero(self.down >= 0)[0]:
            self.up[self.down[k]].append(int(k))
        near_river = self.river | (self.Q > 50)
        forage = np.array([FORAGE[x] for x in BIOMES])[b] * \
            (1 + 2.0 * coastal * pn) * (1 + 0.8 * near_river)
        farm = FARM_MAX_DENS * self.fert ** 1.3 * \
            np.array([FARM[x] for x in BIOMES])[b] * self.elevpen * \
            self.farm_clim
        if getattr(self, "floodplain", False):
            irr = IRRIG_FP_DENS * self.floodplain_area() / self.area * \
                np.array([IRRIG[x] for x in BIOMES])[b]
        else:
            irr = IRRIG_MAX_DENS * np.sqrt(np.clip(self.Q / 3000, 0, 1)) * \
                np.array([IRRIG[x] for x in BIOMES])[b] * self.river
        wetf = self.wetf
        rain = farm
        farm = (rain + irr) * wetf + 1.0 * coastal * pn
        self.forage, self.farm = forage, farm
        steppe = self.steppe_cut
        self.farm_steppe = (rain * (1 - (1 - STEPPE_MIN) * steppe) + irr) * \
            wetf + 1.0 * coastal * pn
        self.irr_share = np.clip(irr * wetf / np.maximum(farm, 1e-9), 0, 1)
        # the same, in parts, for the climate to scale separately
        self.rain_w = rain * wetf
        self.rain_ws = rain * (1 - (1 - STEPPE_MIN) * steppe) * wetf
        self.irr_w = irr * wetf
        self.fish = 1.0 * coastal * pn
        # waterside: coasts (more where the sea is rich), rivers, lakes
        self.water = np.maximum.reduce([coastal * (0.5 + 0.5 * pn),
                                        self.river * 1.0, self.lake * 1.0,
                                        (self.Q > 50) * 0.5])
        self.locus = (1 + 0.6 * self.river + 0.4 * coastal +
                      0.3 * (np.minimum(self.d_cu, self.d_sn) < 150) +
                      0.2 * (self.d_fe < 100))
        self.travel()

    def floodplain_area(self):
        """`floodplain` (WP8 C): irrigable km2 in each river cell, the
        valley's length in the cell (to the cell it drains to, or the
        cell's width at an outlet) times the floodplain's width, which
        grows with discharge, widens on alluvium (surface alluvium or
        alluvial fill) and narrows in relief; deltas (coastal river cells
        on alluvium) are wide. 0 off the rivers."""
        al = self.alluvial | self.alluvium
        w = FP_W0 * np.sqrt(np.clip(self.Q, 0, None) / 1000) * \
            np.where(al, FP_ALLUV, 1.0) * \
            np.exp(-np.clip(self.relief, 0, None) / FP_RELIEF)
        w = np.where(self.coastal & al, np.maximum(w, FP_DELTA_KM), w)
        k = np.argmax(self.nb == self.flow[:, None], 1)
        length = np.where(self.flow >= 0, self.nd[np.arange(self.N), k],
                          np.sqrt(self.area))
        return np.minimum(length * w, self.area) * self.river

    def travel(self, road=None):
        """Travel cost per cell (biome, relief, rivers, and roads if
        given as a 0-1 cost multiplier), then per edge, and the graph."""
        N, nb, nd = self.N, self.nb, self.nd
        if road is None:
            road = getattr(self, "road", None)
        tc = (1 + 1.5 * np.clip(self.relief, 0, 2)) * \
            np.array([MOVE[b] for b in BIOMES])[self.biome]
        tc = np.where(self.river, 0.7 * tc, tc)
        mx = getattr(self, "move_x", None)
        if mx is not None:
            # `clear_terrain`: cleared forest crossed as open country
            tc = tc * mx
        if road is not None:
            tc = tc * road
        old = getattr(self, "edgecost", None)
        ec = np.zeros((N, 8))
        for k in range(8):
            j = nb[:, k]
            ec[:, k] = np.where(j >= 0, nd[:, k] * 0.5 *
                                (tc + tc[np.maximum(j, 0)]), np.inf)
        self.edgecost = ec
        EW = ec[self.E1, self.EK]
        sa, sb, sw = self.sea_links
        I = np.concatenate([self.E1, self.E2, sa, sb])
        J = np.concatenate([self.E2, self.E1, sb, sa])
        Wt = np.concatenate([EW, EW, sw, sw])
        self.G = sparse.csr_matrix((Wt, (I, J)), shape=(N, N))
        # so cached distances know when the graph has changed, and where:
        # the cells whose edge costs moved (both ends of every changed
        # edge), kept for the last 64 versions (changed_since)
        self.gver = getattr(self, "gver", 0) + 1
        self.note_change("g", None if old is None else
                         np.nonzero((ec != old).any(1))[0])
        self.food_graph()

    def note_change(self, g, cells):
        """Record the cells touched by the change that made the current
        version of graph g ("g": travel, "f": food); None if unknown.
        Kept for the last 64 versions."""
        v = self.gver if g == "g" else self.fver
        log = self.__dict__.setdefault(g + "chg", {})
        if cells is not None:
            log[v] = cells
        log.pop(v - 64, None)

    def changed_since(self, v, g="g"):
        """Cells whose edges changed in graph g after its version v, or
        None if that is no longer known."""
        log = self.__dict__.get(g + "chg", {})
        now = self.gver if g == "g" else self.fver
        vs = range(v + 1, now + 1)
        if any(x not in log for x in vs):
            return None
        return np.concatenate([log[x] for x in vs] + [np.zeros(0, int)])

    def food_graph(self):
        """`food_flow`: the graph bulk food moves on. Land edges cost as
        travel (roads included); river channels FF_RIVER per km; coastal
        cells within STRAIT_KM of each other FF_SEA per km. Its own
        version counter, so building it leaves gver alone."""
        N = self.N
        e1, e2, ek = self.E1, self.E2, self.EK
        EW = self.edgecost[e1, ek].copy()
        riv = (self.down[e1] == e2) | (self.down[e2] == e1)
        EW[riv] = np.minimum(EW[riv], self.nd[e1[riv], ek[riv]] * FF_RIVER)
        if not hasattr(self, "_sea_food"):
            ci = self.coast_idx
            pairs = np.array(sorted(self.coast_tree.query_pairs(
                2 * math.sin(STRAIT_KM / R_EARTH / 2))), int).reshape(-1, 2)
            a, b = ci[pairs[:, 0]], ci[pairs[:, 1]]
            dkm = 2 * R_EARTH * np.arcsin(np.clip(np.linalg.norm(
                self.xyz[a] - self.xyz[b], axis=1) / 2, 0, 1))
            key = np.minimum(a, b).astype(np.int64) * N + np.maximum(a, b)
            ekey = np.minimum(e1, e2).astype(np.int64) * N + \
                np.maximum(e1, e2)
            o = np.argsort(ekey)
            pos = np.clip(np.searchsorted(ekey[o], key), 0, len(o) - 1)
            land = ekey[o][pos] == key
            # edge index of each coastal pair that is also a land edge
            self._sea_food = (a, b, dkm, land, o[pos[land]])
        a, b, dkm, land, li = self._sea_food
        # a coastal pair that is also a land edge: the cheaper of the two
        EW[li] = np.minimum(EW[li], dkm[land] * FF_SEA)
        sa, sb, sw = a[~land], b[~land], dkm[~land] * FF_SEA
        I = np.concatenate([e1, e2, sa, sb])
        J = np.concatenate([e2, e1, sb, sa])
        Wt = np.concatenate([EW, EW, sw, sw])
        old = getattr(self, "Gf", None)
        self.Gf = sparse.csr_matrix((Wt, (I, J)), shape=(N, N))
        self.fver = getattr(self, "fver", 0) + 1
        ch = None
        if old is not None:
            # both ends of every edge whose cost moved (inf - inf is nan,
            # which counts as moved)
            r, c = (self.Gf - old).nonzero()
            ch = np.unique(np.concatenate([r, c]))
        self.note_change("f", ch)

    def reroute(self, i, j):
        """Cell i now drains to j (-1: straight to the sea). Discharge,
        rivers, basins and everything derived from them are recomputed."""
        self.flow[i] = j
        self.route()
        self.Q = self.accumulate(self.yield_)
        darea = self.accumulate(self.area)
        self.river = (self.Q > 300) & (darea > 30000) & ~self.lake
        basin = np.arange(self.N)
        for k in self.order[::-1]:
            if self.flow[k] >= 0:
                basin[k] = basin[self.flow[k]]
        self.basin = basin
        self.derive_rivers()

    def ecotones(self, land2):
        """For each cell, the biome a drier or a wetter climate would push
        it toward, and how close that biome is (1 next door, falling off
        over a few cells)."""
        dist = {}
        for k, nm in enumerate(BIOMES):
            g = np.ones((NY, NX), bool)
            g[self.row[self.biome == k], self.col[self.biome == k]] = False
            dist[nm] = ndimage.distance_transform_edt(g)[self.row, self.col]
        drier = {"Jungle": ["Grassland"], "Temperate forest": ["Grassland"],
                 "Grassland": ["Desert"]}
        wetter = {"Desert": ["Grassland"],
                  "Grassland": ["Temperate forest", "Jungle"]}
        for nm, table in (("dry", drier), ("wet", wetter)):
            tgt = -np.ones(self.N, int)
            prox = np.zeros(self.N)
            for k, b in enumerate(BIOMES):
                m = self.biome == k
                for t in table.get(b, []):
                    d = dist[t]
                    p = np.exp(-(np.maximum(d, 1) - 1) / 2.0)
                    better = m & (p > prox)
                    tgt[better] = BIOMES.index(t)
                    prox[better] = p[better]
            setattr(self, f"eco_{nm}", tgt)
            setattr(self, f"eco_{nm}_prox", prox)


# ---- simulation ----------------------------------------------------------
def dsig(x):
    """Logistic, for arrays."""
    return 1 / (1 + np.exp(-np.clip(x, -50, 50)))


def sigmoid(x):
    return 1 / (1 + math.exp(-max(-50.0, min(50.0, x))))


def logistic(p, k, r):
    """Population after one tick of logistic growth at rate r toward
    capacity k. Where r < 0 (a dragon's toll above a people's growth
    rate) the people decline at that rate, and never above k: the closed
    form with r < 0 makes k a repeller, and cells above it ran off to
    huge or negative numbers for a tick (bug found 2026-11-01)."""
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        e = np.exp(-r * DT)
        up = k * p / (p + (k - p) * e)
        return np.where(r >= 0, up, np.minimum(p * np.exp(r * DT), k))
