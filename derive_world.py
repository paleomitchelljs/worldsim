"""
Process-based derivations on top of world.gpkg (run after build_world_gis.py,
which calls this automatically).

Everything here is derived from the gridded data with stated physical rules,
not from Earth analogues:

  tectonic setting   trenches and ridges from bathymetric residuals; arcs
                     beside trenches; orogens as high, high-relief belts;
                     platforms where the fiction raised paleo shallow seas;
                     interior basins; passive margins; cratons
  history, bedrock   real tectonic events placed on each paleocontinent and
                     a rock column per cell, unroofed by erosion (see
                     tectonic_history.py)
  drainage           priority-flood routing on fic_elev_km (drawn rivers
                     burned in), closed basins kept only where lake
                     evaporation can balance inflow, discharge from a
                     biome-based runoff, Strahler order
  soil orders        per cell from diagnostic soil-forming conditions
                     (climate and organisms via biome, relief, parent
                     material via setting, time via surface age); each map
                     soil class is named by its commonest cell order
  ore deposits       marker read (with a per-marker reliability) combined
                     with a deposit-model prior for the cell's tectonic and
                     sedimentary setting; the original read is kept

Assumed constants are collected at the top so they can be argued with.
"""
import heapq
import os
import sqlite3

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import ndimage
from shapely.geometry import LineString
from shapely.ops import linemerge

HERE = os.path.dirname(os.path.abspath(__file__))
GPKG = os.path.join(HERE, "gis", "world.gpkg")
NY, NX, RES = 360, 720, 0.5
R_EARTH = 6371.0

# ---- assumptions ---------------------------------------------------------
# Runoff (m/yr) by biome: the biome map is the only humidity signal there is.
RUNOFF_M_YR = {"Jungle": 1.0, "Temperate forest": 0.4, "Grassland": 0.15,
               "Desert": 0.01, "Tundra": 0.2, "Ocean": 0.0}
# Precipitation (m/yr) by biome, for rain falling directly on lakes.
PRECIP_M_YR = {"Jungle": 2.0, "Temperate forest": 0.9, "Grassland": 0.5,
               "Desert": 0.15, "Tundra": 0.3, "Ocean": 0.0}
# Open-water evaporation (m/yr) as a function of latitude (warmer = more).
def lake_evap(lat):
    return 0.3 + 1.2 * np.cos(np.radians(lat)) ** 2
BURN_KM = 0.05            # drawn rivers lowered by this much before routing
MICRORELIEF_KM = 0.002    # +-2 m of fixed-seed roughness so flats drain dendritically
RIVER_MIN_Q = 300.0       # m3/s for a cell to count as a mapped river at 0.5 deg
RIVER_MIN_AREA = 30000.0  # km2 drainage area, same purpose
LAKE_MIN_DEPTH = 0.05     # km of fill before a depression counts as a lake
# swamp (no wetland source layer): wetness = alluvial fill x low relief x
# runoff, or 1 on a lake; a cell is swamp at wetness >= SWAMP_MIN
SWAMP_RELIEF_KM = 0.3     # relief at which wetness falls to zero
SWAMP_RUNOFF_M_YR = 0.6   # runoff at which wetness saturates
SWAMP_MIN = 0.5
# Depressions persist as lakes only where subsidence keeps making room
# (interior basins, intermontane orogen basins); elsewhere sediment supply
# fills them to the spill point and they become alluvial plains.
LAKE_SETTINGS = ("interior basin", "orogen")
PALEO_OROGEN_KM = 1.5     # paleo topography this high marks a real mountain belt
OCEAN_HALF_RATE_KM_MYR = 25.0  # spreading half-rate for sea-floor age from ridge distance
TRENCH_RESID = -0.30      # km below the local median depth
RIDGE_RESID = 0.30        # km above the local median depth
ARC_KM = 500.0            # land this close to a trench is arc
MARGIN_KM = 300.0         # land this close to the sea is margin

SETTINGS = ["abyssal plain", "trench", "ocean ridge", "shelf",
            "volcanic arc", "orogen", "platform", "interior basin",
            "passive margin", "craton"]

# P(metal | setting) from deposit models:
#   arc: porphyry Cu, magnetite skarns; orogen: Sn from crustal-melt granites;
#   platform: oolitic ironstones, red-bed Cu; interior basin: stratiform
#   sediment-hosted Cu, evaporite-associated Fe; passive margin: heavy-mineral
#   placers (cassiterite, magnetite); craton: banded iron, greenstone Cu.
ORE_PRIOR = {
    "volcanic arc":   {"copper": 0.55, "iron": 0.35, "tin": 0.10},
    "orogen":         {"copper": 0.25, "iron": 0.30, "tin": 0.45},
    "platform":       {"copper": 0.25, "iron": 0.60, "tin": 0.15},
    "interior basin": {"copper": 0.50, "iron": 0.35, "tin": 0.15},
    "passive margin": {"copper": 0.30, "iron": 0.45, "tin": 0.25},
    "craton":         {"copper": 0.25, "iron": 0.60, "tin": 0.15},
}
PLACER_TIN_BOOST = 1.8    # surface deposit on a river: cassiterite placers
# How often a marker read is right, from checking reads against the map:
# red markers sit apart and read well; purple ones overlap in clusters.
READ_RELIABILITY = {("surface", "high"): 0.90, ("surface", "low"): 0.75,
                    ("deep", "high"): 0.70, ("deep", "low"): 0.50}

SOIL_ORDERS = ["Alfisol", "Andisol", "Aridisol", "Entisol", "Gelisol", "Histosol",
               "Inceptisol", "Mollisol", "Oxisol", "Spodosol", "Ultisol", "Vertisol"]
SOIL_NOTES = {
    "Alfisol": "moderately leached clay-enriched soil; temperate forest, moderate age",
    "Andisol": "volcanic-ash soil; arc settings",
    "Aridisol": "dry-climate soil with carbonate/salt horizons",
    "Entisol": "little horizon development; young surfaces, alluvium, steep ground",
    "Gelisol": "permafrost soil",
    "Histosol": "organic (peat) soil; waterlogged lowlands",
    "Inceptisol": "weakly developed; slopes and moderately young surfaces",
    "Mollisol": "dark, base-rich topsoil; grassland",
    "Oxisol": "extremely weathered iron/aluminium-oxide soil; hot, humid, old stable surfaces",
    "Spodosol": "acid leached soil with iron-humus horizon; cool humid forest",
    "Ultisol": "strongly leached clay soil; warm humid, older surfaces",
    "Vertisol": "shrink-swell clay soil; flat lowlands, seasonal moisture",
}


# ---- grid helpers ----------------------------------------------------------
def grid(df, col, dtype=float):
    out = np.full((NY, NX), np.nan if dtype is float else 0, dtype)
    out[df["row"].values, df["col"].values] = df[col].values
    return out


NBRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def neighbours(r, c):
    for dr, dc in NBRS:
        rr = r + dr
        if 0 <= rr < NY:
            yield rr, (c + dc) % NX  # longitude wraps


def wrap_filter(a, size, fn):
    """Filter with longitudinal wrap (the grid is a globe)."""
    pad = size
    ext = np.concatenate([a[:, -pad:], a, a[:, :pad]], axis=1)
    return fn(ext)[:, pad:-pad]


def dist_to_mask_km(mask, LAT):
    """Great-circle distance from every cell to the nearest True cell."""
    from scipy.spatial import cKDTree
    LON = -180 + RES * (np.arange(NX) + 0.5)
    lon, lat = np.meshgrid(LON, LAT[:, 0])

    def xyz(lo, la):
        lo, la = np.radians(lo), np.radians(la)
        return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    if not mask.any():
        return np.full((NY, NX), np.inf)
    t = cKDTree(xyz(lon[mask], lat[mask]))
    d = t.query(xyz(lon.ravel(), lat.ravel()))[0]
    return (2 * R_EARTH * np.arcsin(np.clip(d / 2, 0, 1))).reshape(NY, NX)


# ---- tectonic setting ------------------------------------------------------
def tectonic_setting(E, land, emerged, LAT, paleo_E):
    sea = ~land
    # bathymetric residual against the regional seafloor
    E_sea = np.where(sea, E, np.nan)
    med = wrap_filter(np.nan_to_num(E_sea, nan=-2.6), 15,
                      lambda a: ndimage.median_filter(a, size=15))
    resid = np.where(sea, E - med, 0.0)
    far_from_land = dist_to_mask_km(land, LAT) > 150

    def linear(mask, min_cells=6):
        lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
        keep = np.zeros(n + 1, bool)
        for i, sl in enumerate(ndimage.find_objects(lab), 1):
            comp = lab[sl] == i
            h, w = comp.shape
            if min(h, w) <= 1 or (min(h, w) <= 2 and max(h, w) > 8):
                continue  # row/column-aligned: a leftover grid line
            # elongated: long axis much longer than its filled area implies
            if comp.sum() >= min_cells and max(h, w) >= 3 * max(1, comp.sum() / max(h, w)):
                keep[i] = True
        return keep[lab]

    # subduction trenches border arcs and continents; isolated deep lines in
    # open ocean are not taken as trenches
    near_land = dist_to_mask_km(land, LAT) < 600
    trench = linear(sea & (resid < TRENCH_RESID) & (E < -2.0))
    lab, n = ndimage.label(trench, structure=np.ones((3, 3)))
    keep = np.zeros(n + 1, bool)
    keep[np.unique(lab[trench & near_land])] = True
    keep[0] = False
    trench = keep[lab]
    ridge = linear(sea & (resid > RIDGE_RESID) & (E < -1.0) & far_from_land)

    # relief on a smoothed surface, so colour-band steps in the redrawn map
    # do not read as mountain fronts: elevation range in a 7x7 window (km)
    Es = wrap_filter(np.where(land, E, 0.0), 6, lambda a: ndimage.gaussian_filter(a, 1.5))
    relief = (wrap_filter(Es, 7, lambda a: ndimage.maximum_filter(a, 7))
              - wrap_filter(Es, 7, lambda a: ndimage.minimum_filter(a, 7)))
    d_trench = dist_to_mask_km(trench, LAT)
    d_sea = dist_to_mask_km(sea, LAT)
    hi_e = np.nanpercentile(Es[land], 80)
    hi_r = np.nanpercentile(relief[land], 80)
    low_e = np.nanpercentile(E[land], 25)

    s = np.zeros((NY, NX), np.int8)  # abyssal plain
    s[sea & (E > -0.5)] = SETTINGS.index("shelf")
    s[ridge] = SETTINGS.index("ocean ridge")
    s[trench] = SETTINGS.index("trench")
    L = land
    s[L] = SETTINGS.index("craton")
    s[L & (d_sea < MARGIN_KM)] = SETTINGS.index("passive margin")
    basin = L & (E < low_e) & (d_sea >= MARGIN_KM)
    basin = ndimage.binary_opening(basin, np.ones((3, 3)))
    s[basin] = SETTINGS.index("interior basin")
    s[L & emerged] = SETTINGS.index("platform")
    # a mountain belt is high AND rugged in the fiction, or high in the paleo
    # reconstruction (which is real topography, not a redraw)
    paleo_high = ndimage.binary_dilation((np.nan_to_num(paleo_E, nan=-9) >= PALEO_OROGEN_KM)
                                         & (np.abs(LAT) < 85),  # map-edge fill near the poles
                                         np.ones((3, 3)))
    orogen = L & (((Es > hi_e) & (relief > hi_r)) | paleo_high)
    orogen = ndimage.binary_opening(ndimage.binary_closing(orogen, np.ones((3, 3))),
                                    np.ones((2, 2))) & L & (np.abs(LAT) < 85)
    s[orogen] = SETTINGS.index("orogen")
    s[L & (d_trench < ARC_KM)] = SETTINGS.index("volcanic arc")
    return s, relief, trench, ridge, d_trench


# ---- drainage ----------------------------------------------------------------
def priority_flood(E, land, extra_seeds=()):
    """Route every land cell to the sea (or a closed-basin sink).
    Returns filled surface, receiver index (-1 = outlet/sink), visit order."""
    filled = E.copy()
    recv = np.full(NY * NX, -1, np.int64)
    seen = ~land.copy()
    heap = []
    # seeds: land cells touching the sea drain to that sea cell
    for r, c in zip(*np.nonzero(land)):
        for rr, cc in neighbours(r, c):
            if not land[rr, cc]:
                heapq.heappush(heap, (E[r, c], r, c, rr * NX + cc))
                seen[r, c] = True
                break
    for r, c in extra_seeds:
        if not seen[r, c]:
            heapq.heappush(heap, (E[r, c], r, c, -1))
            seen[r, c] = True
    order = []
    # filled depressions get a small random down-gradient toward the spill
    # point instead of a dead-flat surface, as a depositional plain would
    rng = np.random.default_rng(1)
    while heap:
        z, r, c, to = heapq.heappop(heap)
        recv[r * NX + c] = to
        order.append(r * NX + c)
        for rr, cc in neighbours(r, c):
            if not seen[rr, cc]:
                seen[rr, cc] = True
                filled[rr, cc] = max(E[rr, cc], z + 1e-5 * rng.uniform(1, 100))
                heapq.heappush(heap, (filled[rr, cc], rr, cc, r * NX + c))
    return filled, recv, np.array(order)


def accumulate(order, recv, w):
    acc = w.ravel().astype(float).copy()
    for i in order[::-1]:
        j = recv[i]
        if j >= 0:
            acc[j] += acc[i]
    return acc.reshape(NY, NX)


def drainage(E, land, drawn_river, runoff, precip, area, LAT, setting_name):
    rough = np.random.default_rng(0).uniform(-MICRORELIEF_KM, MICRORELIEF_KM, E.shape)
    Eb = E - BURN_KM * drawn_river + rough
    yield_ = runoff * area * 1e6 / 3.156e7  # m3/s from each cell
    filled, recv, order = priority_flood(Eb, land)
    depth = np.where(land, filled - Eb, 0)
    dep_lab, n = ndimage.label(depth > LAKE_MIN_DEPTH, structure=np.ones((3, 3)))
    acc_q = accumulate(order, recv, np.where(land, yield_, 0))

    sinks = []
    endorheic = np.zeros((NY, NX), bool)
    for i, sl in enumerate(ndimage.find_objects(dep_lab), 1):
        reg = dep_lab == i
        rr, cc = np.nonzero(reg)
        idx = rr * NX + cc
        # spill cell: the region cell whose receiver lies outside the region
        out = [k for k in idx if recv[k] < 0 or not reg.flat[recv[k]]]
        inflow = max(acc_q.flat[k] for k in out) if out else acc_q[reg].max()
        lake_area_m2 = area[reg].sum() * 1e6
        evap = lake_evap(LAT[reg]).mean() * lake_area_m2 / 3.156e7  # m3/s
        rain = precip[reg].mean() * lake_area_m2 / 3.156e7
        if inflow + rain < evap:  # evaporation can hold the basin below its sill
            k = int(np.argmin(np.where(reg, Eb, np.inf)))
            sinks.append(divmod(k, NX))
            endorheic |= reg

    if sinks:
        filled, recv, order = priority_flood(Eb, land, extra_seeds=sinks)
    acc_q = accumulate(order, recv, np.where(land, yield_, 0))
    acc_a = accumulate(order, recv, np.where(land, area, 0))
    depth = np.where(land, filled - Eb, 0)
    subsiding = np.isin(setting_name, LAKE_SETTINGS)
    deep = depth > LAKE_MIN_DEPTH
    lab, n = ndimage.label(deep, structure=np.ones((3, 3)))
    lake = np.zeros((NY, NX), bool)
    alluvial = np.zeros((NY, NX), bool)
    for i in range(1, n + 1):
        reg = lab == i
        # a closed (evaporative) basin holds a lake only as large as
        # evaporation less rain on it can balance its inflow, filling from
        # the lowest cells; the rest of its floor is dry sediment. Any
        # other depression stays open water if most of it subsides (it
        # fills and spills), else it silts up
        if endorheic[reg].any():
            rr, cc = np.nonzero(reg)
            k = np.argsort(Eb[rr, cc])
            net = np.maximum(lake_evap(LAT[rr, cc]) - precip[rr, cc], 1e-3)[k]  # m/yr
            inflow = acc_q[reg].max() * 3.156e7                      # m3/yr
            # cells, lowest first, while their net evaporation is still
            # needed to balance the inflow (always at least one)
            need = np.cumsum(net * area[rr, cc][k] * 1e6) - net * area[rr, cc][k] * 1e6
            wet = np.zeros(len(k), bool)
            wet[k[need < inflow]] = True
            wet[k[0]] = True
            lake[rr[wet], cc[wet]] = True
            alluvial[rr[~wet], cc[~wet]] = True
        elif subsiding[reg].mean() > 0.5:
            lake |= reg
        else:
            alluvial |= reg
    terminal = np.zeros((NY, NX), bool)
    for r, c in sinks:
        terminal[r, c] = True

    river = land & (acc_q > RIVER_MIN_Q) & (acc_a > RIVER_MIN_AREA) & ~lake

    # basin id = outlet cell index
    basin = np.full(NY * NX, -1, np.int64)
    for i in order:
        j = recv[i]
        basin[i] = i if (j < 0 or not land.flat[j]) else basin[j]
    basin = basin.reshape(NY, NX)

    # Strahler order on the river network
    strahler = np.zeros(NY * NX, np.int8)
    up_max = np.zeros(NY * NX, np.int8)
    up_cnt = np.zeros(NY * NX, np.int8)
    rv = river.ravel()
    for i in order[::-1]:
        if not rv[i]:
            continue
        s = max(1, up_max[i] + (1 if up_cnt[i] >= 2 else 0)) if up_max[i] else 1
        strahler[i] = s
        j = recv[i]
        if j >= 0 and rv[j]:
            if s > up_max[j]:
                up_max[j], up_cnt[j] = s, 1
            elif s == up_max[j]:
                up_cnt[j] += 1
    return dict(recv=recv, order=order, q=acc_q, area=acc_a, river=river,
                lake=lake, alluvial=alluvial, endorheic=endorheic, terminal=terminal,
                basin=basin, strahler=strahler.reshape(NY, NX), filled=filled)


def river_lines(dr):
    LON = -180 + RES * (np.arange(NX) + 0.5)
    LATS = 90 - RES * (np.arange(NY) + 0.5)
    segs, attrs = [], []
    rv, recv = dr["river"].ravel(), dr["recv"]
    for i in np.nonzero(rv)[0]:
        j = recv[i]
        if j < 0:
            continue
        r0, c0 = divmod(i, NX)
        r1, c1 = divmod(j, NX)
        if abs(c1 - c0) > 1:
            continue  # do not draw across the date line
        segs.append(LineString([(LON[c0], LATS[r0]), (LON[c1], LATS[r1])]))
        attrs.append((int(dr["strahler"].flat[i]), float(dr["q"].flat[i]),
                      float(dr["area"].flat[i]), int(dr["basin"].flat[i])))
    g = gpd.GeoDataFrame(attrs, columns=["strahler", "q_m3s", "area_km2", "basin"],
                         geometry=segs, crs="EPSG:4326")
    # merge reaches of equal order within a basin into polylines
    rows = []
    for (o, b), grp in g.groupby(["strahler", "basin"]):
        merged = linemerge(list(grp.geometry))
        parts = getattr(merged, "geoms", [merged])
        for p in parts:
            rows.append(dict(strahler=o, basin=b, q_m3s_max=grp.q_m3s.max(),
                             area_km2_max=grp.area_km2.max(), geometry=p))
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


# ---- soils -----------------------------------------------------------------
STEEP_PCTL = 85  # relief percentile (land) above which ground counts as steep


def swamp_wetness(alluvial, relief, runoff, lake):
    """0-1 wetness: waterlogged alluvial lowland (wetter with runoff, drier
    with relief), or open lake."""
    w = (alluvial > 0) * np.clip(1 - relief / SWAMP_RELIEF_KM, 0, 1) * \
        np.clip(runoff / SWAMP_RUNOFF_M_YR, 0, 1)
    return np.maximum(w, (lake > 0).astype(float))


def soil_order_cells(df):
    """Per-cell USDA order from diagnostic conditions, most diagnostic first:
    permafrost, volcanic ash, waterlogging, aridity, slope, surface youth,
    then climate x vegetation on stable ground."""
    lat = np.abs(df.lat.values)
    b = (df.syn_biome if "syn_biome" in df else df.fic_biome).values
    st = df.syn_setting.values
    relief = df.syn_relief_km.values
    land = df.fic_land.values == 1
    steep = relief > np.nanpercentile(relief[land], STEEP_PCTL)
    low = df.fic_elev_km.values < 0.25
    flat = relief < np.nanpercentile(relief[land], 40)
    wet = ((df.syn_lake.values == 1) | (df.syn_alluvial_fill.values == 1)) & low
    young = (df.syn_alluvial_fill.values == 1) | (df.syn_river.values == 1) | \
            ((df.syn_coast_status.values == 2) & (df.fic_dist_coast_km.values < 150))
    rules = [
        ("Gelisol", (b == "Tundra") | (lat > 65)),
        ("Andisol", st == "volcanic arc"),
        ("Histosol", wet & (b != "Desert")),
        ("Aridisol", b == "Desert"),
        ("Inceptisol", steep),
        ("Entisol", young),
        ("Vertisol", (b == "Grassland") & low & flat),
        ("Oxisol", (b == "Jungle") & np.isin(st, ["craton", "interior basin"]) & flat),
        ("Ultisol", b == "Jungle"),
        ("Spodosol", (b == "Temperate forest") & (lat >= 45)),
        ("Alfisol", b == "Temperate forest"),
        ("Mollisol", b == "Grassland"),
    ]
    out = np.full(len(df), None, object)
    for name, cond in rules:
        take = land & (out == None) & cond  # noqa: E711
        out[take] = name
    out[land & (out == None)] = "Inceptisol"  # noqa: E711
    return out


def name_soils(df):
    """Name each map soil class by the order most of its cells get."""
    L = df[df.fic_land == 1]
    tab = pd.crosstab(L.fic_soil_id, L.syn_soil_order_cell, normalize="index")
    names, share, second = {}, {}, {}
    for i in tab.index:
        o = tab.loc[i].sort_values(ascending=False)
        names[int(i)], share[int(i)] = o.index[0], round(float(o.iloc[0]), 2)
        second[int(i)] = f"{o.index[1]} ({o.iloc[1]:.2f})"
    return names, share, second, tab.round(3)


# ---- ores --------------------------------------------------------------------
def reclassify_ores(deps, setting_name, river, land, LAT):
    """Islands smaller than a cell put some markers in sea cells; those take
    the setting of the nearest land cell (flagged offshore)."""
    from scipy.spatial import cKDTree
    out = deps.copy()
    rows = np.clip(((90 - out.lat) / RES).astype(int), 0, NY - 1).to_numpy().copy()
    cols = np.clip(((out.lon + 180) / RES).astype(int), 0, NX - 1).to_numpy().copy()
    lr, lc = np.nonzero(land)
    tree = cKDTree(np.c_[lr, lc])
    out["offshore"] = (~land[rows, cols]).astype(int)
    for k in np.nonzero(~land[rows, cols])[0]:
        j = tree.query([rows[k], cols[k]])[1]
        rows[k], cols[k] = lr[j], lc[j]
    out["_r"], out["_c"] = rows, cols
    metals = ["copper", "iron", "tin"]
    post_cols = {m: [] for m in metals}
    final = []
    for _, d in out.iterrows():
        r, c = int(d._r), int(d._c)
        st = setting_name[r, c]
        prior = dict(ORE_PRIOR.get(st, ORE_PRIOR["passive margin"]))
        if d.depth == "surface" and river[max(0, r - 1):r + 2, max(0, c - 1):c + 2].any():
            prior["tin"] *= PLACER_TIN_BOOST
        rel = READ_RELIABILITY[(d.depth, d.confidence)]
        lik = {m: rel if m == d.read_metal else (1 - rel) / 2 for m in metals}
        p = np.array([lik[m] * prior[m] for m in metals])
        p /= p.sum()
        for m, v in zip(metals, p):
            post_cols[m].append(round(float(v), 3))
        final.append(metals[int(np.argmax(p))])
    out["setting"] = setting_name[out._r.values, out._c.values]
    for m in metals:
        out[f"p_{m}"] = post_cols[m]
    out["metal"] = final
    out["changed"] = (out.metal != out.read_metal).astype(int)
    out["ore_type"] = out.depth + "_" + out.metal
    return out


# ---- previews -----------------------------------------------------------------
SETTING_RGB = {"abyssal plain": (20, 40, 90), "trench": (0, 0, 0), "ocean ridge": (255, 140, 0),
               "shelf": (90, 140, 200), "volcanic arc": (220, 30, 30), "orogen": (140, 70, 30),
               "platform": (120, 200, 120), "interior basin": (240, 220, 120),
               "passive margin": (200, 200, 200), "craton": (90, 120, 60)}
SOIL_RGB = {"Alfisol": (190, 150, 90), "Andisol": (120, 60, 120), "Aridisol": (235, 210, 150),
            "Entisol": (200, 200, 170), "Gelisol": (220, 230, 240), "Histosol": (60, 50, 40),
            "Inceptisol": (170, 140, 110), "Mollisol": (90, 70, 40), "Oxisol": (190, 60, 40),
            "Spodosol": (150, 150, 160), "Ultisol": (210, 120, 70), "Vertisol": (80, 80, 90)}


def write_previews(df, dr, folder):
    from PIL import Image, ImageDraw
    os.makedirs(folder, exist_ok=True)
    r, c = df["row"].values, df["col"].values
    land = (df.fic_land.values == 1)

    def save(img, name, legend):
        im = Image.fromarray(img).resize((NX * 2, NY * 2), Image.NEAREST)
        canvas = Image.new("RGB", (NX * 2, NY * 2 + 22 + 18 * ((len(legend) + 5) // 6)), "white")
        canvas.paste(im, (0, 22))
        d = ImageDraw.Draw(canvas)
        d.text((6, 5), name, fill="black")
        for i, (label, rgb) in enumerate(legend):
            x, y = 6 + (i % 6) * 238, NY * 2 + 26 + 18 * (i // 6)
            d.rectangle([x, y, x + 12, y + 12], fill=rgb, outline="black")
            d.text((x + 18, y), label, fill="black")
        canvas.save(os.path.join(folder, name + ".png"))

    lith_rgb = {
        "alluvium": (238, 232, 170), "limestone": (110, 190, 230), "dolostone": (80, 150, 200),
        "chalk": (200, 235, 250), "marl": (150, 200, 210), "evaporite": (250, 130, 200),
        "shale": (120, 120, 120), "black shale": (50, 50, 50), "slate-phyllite": (90, 90, 110),
        "sandstone": (240, 200, 110), "red-bed sandstone": (200, 90, 60), "quartzite": (255, 255, 255),
        "conglomerate": (210, 160, 90), "greywacke": (150, 140, 110), "melange": (120, 90, 140),
        "coal measures": (20, 20, 20), "glacial diamictite": (190, 200, 180), "oolitic ironstone": (160, 60, 20),
        "basalt": (70, 40, 40), "andesite": (180, 60, 60), "amphibolite": (60, 90, 60),
        "granite-gneiss": (235, 160, 170), "schist-gneiss": (200, 140, 200), "granulite-gneiss": (170, 100, 170),
        "granodiorite": (230, 90, 120), "S-type granite": (255, 60, 90), "schist": (180, 160, 210),
        "marble": (220, 220, 255), "greenschist": (110, 160, 110), "blueschist-melange": (90, 110, 170)}
    img = np.full((NY, NX, 3), (25, 35, 60), np.uint8)
    for k, v in lith_rgb.items():
        m = df.syn_surface_lith.values == k
        img[r[m], c[m]] = v
    present = set(df.syn_surface_lith.dropna())
    save(img, "syn_surface_lith", [(k, v) for k, v in lith_rgb.items() if k in present])

    prov = sorted(df.syn_basement_province.dropna().unique())
    pal = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48),
           (145, 30, 180), (70, 240, 240), (240, 50, 230), (210, 245, 60), (250, 190, 212),
           (0, 128, 128), (220, 190, 255), (170, 110, 40), (255, 250, 200), (128, 0, 0),
           (170, 255, 195), (128, 128, 0), (255, 215, 180)]
    img = np.full((NY, NX, 3), (25, 35, 60), np.uint8)
    for k, v in zip(prov, pal):
        m = (df.syn_basement_province.values == k) & land
        img[r[m], c[m]] = v
    save(img, "syn_basement_province", list(zip(prov, pal)))

    img = np.zeros((NY, NX, 3), np.uint8)
    for k, v in SETTING_RGB.items():
        m = df.syn_setting.values == k
        img[r[m], c[m]] = v
    save(img, "syn_setting", list(SETTING_RGB.items()))

    for col in ("syn_soil_order_cell", "syn_soil_order"):
        img = np.full((NY, NX, 3), (40, 60, 100), np.uint8)
        for k, v in SOIL_RGB.items():
            m = df[col].values == k
            img[r[m], c[m]] = v
        save(img, col, list(SOIL_RGB.items()))

    img = np.zeros((NY, NX, 3), np.uint8)
    img[r[land], c[land]] = (200, 190, 160)
    hyd = [("land", (200, 190, 160)), ("alluvial fill", (170, 200, 140)),
           ("closed basin", (255, 150, 60)), ("lake", (80, 160, 255))]
    for col, rgb in (("syn_alluvial_fill", hyd[1][1]), ("syn_endorheic", hyd[2][1]),
                     ("syn_lake", hyd[3][1])):
        m = df[col].values == 1
        img[r[m], c[m]] = rgb
    for o, rgb in ((1, (120, 120, 230)), (2, (60, 60, 220)), (3, (20, 20, 180)),
                   (4, (0, 0, 120)), (5, (0, 0, 60)), (6, (0, 0, 30))):
        m = (df.syn_river.values == 1) & (df.syn_strahler.values == o)
        img[r[m], c[m]] = rgb
        if m.any():
            hyd.append((f"river order {o}", rgb))
    save(img, "syn_drainage", hyd)


# ---- main ----------------------------------------------------------------------
def main(gpkg=GPKG, out=None, climate=False):
    """Run on a temporary copy outside the synced folder, then swap it in:
    rewriting layers in place while Dropbox syncs the file corrupts it.
    With `out`, the result goes there and `gpkg` is left alone."""
    import shutil
    import tempfile
    out = out or gpkg
    tmp = os.path.join(tempfile.mkdtemp(prefix="world_gis_"), "world.gpkg")
    shutil.copy2(gpkg, tmp)
    previews = "previews" if out == gpkg else "previews_" + \
        os.path.splitext(os.path.basename(out))[0].split("_")[-1]
    res = derive(tmp, os.path.join(os.path.dirname(out), previews), climate=climate)
    shutil.move(tmp, out)
    return res


def derive(gpkg, previews_dir, climate=False):
    print("derive: loading ...")
    cells = gpd.read_file(gpkg, layer="cells")
    deps = gpd.read_file(gpkg, layer="ore_deposits")
    if "read_metal" not in deps:
        deps["read_metal"] = deps["metal"]
    df = cells

    LAT = grid(df, "lat")
    E = grid(df, "fic_elev_km")
    land = grid(df, "fic_land") > 0.5
    emerged = grid(df, "syn_coast_status") == 2
    area = grid(df, "area_km2")
    drawn = grid(df, "fic_river") > 0.5
    biome = np.empty((NY, NX), object)
    biome[df["row"].values, df["col"].values] = df["fic_biome"].values
    runoff = np.vectorize(lambda b: RUNOFF_M_YR.get(b, 0.0))(biome)
    precip = np.vectorize(lambda b: PRECIP_M_YR.get(b, 0.0))(biome)
    clim = None
    if climate:
        print("derive: climate fields ...")
        import climate_world as cw
        clim, clim_biome, _, _ = cw.build(df)
        # WP8, D10 (U 2026-11-19: the climate wins everywhere): the
        # biome is the one the climate implies, and runoff and lake rain
        # are the climate's own
        biome = np.where(land, np.array(cw.BIOMES, object)[clim_biome], "Ocean")
        runoff = np.where(land, clim["runoff_m_yr"], 0.0)
        precip = np.where(land, clim["precip_m_yr"], 0.0)

    print("derive: tectonic setting ...")
    s, relief, trench, ridge, d_trench = tectonic_setting(E, land, emerged, LAT,
                                                          grid(df, "paleo_elev_km"))
    setting_name = np.array(SETTINGS, object)[s]

    print("derive: tectonic history ...")
    import tectonic_history as th
    LON = np.broadcast_to(-180 + RES * (np.arange(NX) + 0.5), (NY, NX))
    block, columns, events, collision_now, crust = th.build_history(
        df, land, LAT, LON, setting_name, trench)
    # the ongoing Caledonian collision is a mountain belt whether or not the
    # redrawn elevation shows it
    setting_name = np.where(collision_now & land, "orogen", setting_name).astype(object)

    print("derive: drainage ...")
    dr = drainage(E, land, drawn.astype(float), runoff, precip, area, LAT, setting_name)

    print("derive: bedrock ...")
    volcanic_now = land & (setting_name == "volcanic arc") & (d_trench < 350)
    surf, surf_num, strat = th.unroof(columns, land, E, relief, setting_name, emerged,
                                      dr["alluvial"], dr["river"], dr["endorheic"],
                                      volcanic_now, LAT, block, strahler=dr["strahler"])
    convergent = trench | collision_now
    d_conv = dist_to_mask_km(convergent, LAT)
    d_ridge = dist_to_mask_km(ridge, LAT)
    oceanic = ~land & ~crust

    r, c = df["row"].values, df["col"].values
    new = {
        "syn_setting": setting_name[r, c],
        "syn_relief_km": relief[r, c],
        "syn_dist_trench_km": d_trench[r, c],
        "syn_runoff_m_yr": runoff[r, c],
        "syn_discharge_m3s": np.where(land[r, c], dr["q"][r, c], np.nan),
        "syn_drainage_area_km2": np.where(land[r, c], dr["area"][r, c], np.nan),
        "syn_river": dr["river"][r, c].astype(np.int8),
        "syn_strahler": dr["strahler"][r, c],
        "syn_lake": dr["lake"][r, c].astype(np.int8),
        "syn_alluvial_fill": dr["alluvial"][r, c].astype(np.int8),
        "syn_endorheic": dr["endorheic"][r, c].astype(np.int8),
        "syn_basin_id": np.where(land[r, c], dr["basin"][r, c], -1),
        "syn_flow_to": np.where(land[r, c], dr["recv"].reshape(NY, NX)[r, c], -1),
    }
    wet = swamp_wetness(dr["alluvial"], np.nan_to_num(relief), runoff, dr["lake"])
    new["syn_wetness"] = np.where(land[r, c], wet[r, c], np.nan)
    new["syn_swamp"] = (land[r, c] & (wet[r, c] >= SWAMP_MIN)).astype(np.int8)
    ri = r * NX + c
    new.update({
        "syn_block": np.where(block[r, c] == "", None, block[r, c]),
        "syn_crust": np.where(land[r, c] | crust[r, c], "continental", "oceanic"),
        "syn_basement_province": surf["basement_province"][ri],
        "syn_basement_lith": surf["basement_lith"][ri],
        "syn_basement_age_ma": surf_num["basement_age"][ri],
        "syn_surface_lith": surf["surface_lith"][ri],
        "syn_surface_unit": surf["surface_unit"][ri],
        "syn_surface_event": surf["surface_event"][ri],
        "syn_surface_age_ma": surf_num["surface_age"][ri],
        "syn_cover_km": surf_num["cover_km"][ri],
        "syn_erosion_km": surf_num["erosion_km"][ri],
        "syn_paleolat_540": th.paleolat(block, LAT, 540)[r, c],
        "syn_paleolat_445": th.paleolat(block, LAT, 445)[r, c],
        "syn_ocean_crust_age_myr": np.where(oceanic[r, c], d_ridge[r, c] / OCEAN_HALF_RATE_KM_MYR,
                                            np.nan),
        "syn_dist_convergent_km": d_conv[r, c],
        "syn_seismic_index": np.exp(-d_conv[r, c] / 250.0),
        "syn_active_volcanic": volcanic_now[r, c].astype(np.int8),
    })
    if clim is not None:
        for k in ("temp_c", "temp_range_c", "gdd", "precip_m_yr", "pet_m_yr",
                  "aet_m_yr", "aridity"):
            new[f"syn_{k}"] = clim[k][r, c]
        new["syn_runoff_climate_m_yr"] = clim["runoff_m_yr"][r, c]
        new["syn_biome"] = np.where(land[r, c], biome[r, c], None)
    for k, v in new.items():
        df[k] = v
    # dist to derived river
    river_d = dist_to_mask_km(dr["river"], LAT)
    df["syn_dist_river_km"] = np.where(land[r, c], river_d[r, c], np.nan)

    print("derive: soils ...")
    df["syn_soil_order_cell"] = soil_order_cells(df)
    names, share, second, tab = name_soils(df)
    df["syn_soil_order"] = df["fic_soil_id"].map(names).where(df.fic_land == 1, None)

    print("derive: ore deposits ...")
    deps2 = reclassify_ores(deps, setting_name, dr["river"], land, LAT)
    # per-cell counts and distances from the reviewed classification
    from scipy.spatial import cKDTree
    LONg = -180 + RES * (np.arange(NX) + 0.5)

    def xyz(lo, la):
        lo, la = np.radians(lo), np.radians(la)
        return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    cell_xyz = xyz(LONg[c], LAT[r, c])
    ore_meta = []
    for ot in sorted({f"{d}_{m}" for d in ("surface", "deep") for m in ("copper", "iron", "tin")}):
        cnt = np.zeros((NY, NX), np.int16)
        sel = (deps2.ore_type == ot).values
        np.add.at(cnt, (deps2._r.values[sel], deps2._c.values[sel]), 1)
        df[f"syn_n_{ot}"] = cnt[r, c]
        ore_meta.append((f"syn_n_{ot}", "syn", "derived", "count",
                         "deposits in cell after geological review; offshore markers on nearest land"))
    for m in ("copper", "iron", "tin"):
        sel = (deps2.metal == m).values
        t = cKDTree(xyz(deps2.lon.values[sel], deps2.lat.values[sel]))
        df[f"syn_dist_{m}_km"] = 2 * R_EARTH * np.arcsin(np.clip(t.query(cell_xyz)[0] / 2, 0, 1))
        ore_meta.append((f"syn_dist_{m}_km", "syn", "derived", "km",
                         "to nearest deposit after geological review, any depth"))
    deps2 = deps2.drop(columns=["_r", "_c"])

    print("derive: writing ...")
    df.to_file(gpkg, layer="cells", driver="GPKG")
    deps2.to_file(gpkg, layer="ore_deposits", driver="GPKG")
    rl = river_lines(dr)
    rl.to_file(gpkg, layer="rivers", driver="GPKG")

    con = sqlite3.connect(gpkg)
    # the image-extracted rivers stay as rivers_drawn (written by the build)
    leg = pd.read_sql("select * from legend_soil", con)
    leg["soil_name"] = leg.soil_id.map(names)
    leg["name_share"] = leg.soil_id.map(share)
    leg["runner_up"] = leg.soil_id.map(second)
    leg["basis"] = leg.soil_name.map(SOIL_NOTES)
    leg.to_sql("legend_soil", con, index=False, if_exists="replace")
    tab.index.name = "soil_id"
    tab.reset_index().to_sql("soil_order_scoring", con, index=False, if_exists="replace")
    pd.DataFrame({"setting_id": range(len(SETTINGS)), "setting": SETTINGS}).to_sql(
        "legend_setting", con, index=False, if_exists="replace")
    pd.DataFrame(strat, columns=["cell", "seq_from_top", "unit", "lithology", "age_ma",
                                 "age_bp_myr", "thickness_km", "eroded_km", "event"]
                 ).to_sql("strat_columns", con, index=False, if_exists="replace")
    pd.DataFrame(events).to_sql("tectonic_events", con, index=False, if_exists="replace")
    pd.DataFrame([dict(block=b, age_ma=a, paleolat=v) for b, tr in th.PALEOLAT.items()
                  for a, v in zip(th.AGES, tr)]).to_sql("paleolatitude", con, index=False,
                                                       if_exists="replace")
    pd.DataFrame([dict(innovation=k, earth_onset_ma=v, world_onset_ma=th.onset(k),
                       offset_myr=th.BIOTIC_OFFSET_MYR) for k, v in th.EARTH_ONSET_MA.items()]
                 ).to_sql("biotic_clock", con, index=False, if_exists="replace")
    pri = pd.DataFrame(ORE_PRIOR).T.reset_index().rename(columns={"index": "setting"})
    pri.to_sql("ore_prior", con, index=False, if_exists="replace")
    meta = [
        ("syn_setting", "syn", "derived", "class", "tectonic/sedimentary setting; see legend_setting"),
        ("syn_relief_km", "syn", "derived", "km",
         "elevation range in a 7x7 window of the smoothed (sigma 1.5 cell) land surface"),
        ("syn_dist_trench_km", "syn", "derived", "km", "to nearest detected trench"),
        ("syn_runoff_m_yr", "syn", "derived", "m/yr",
         "precipitation - actual evaporation (climate_world)" if climate
         else "assumed runoff by biome"),
        ("syn_discharge_m3s", "syn", "derived", "m3/s", "accumulated runoff routed over fic_elev_km"),
        ("syn_drainage_area_km2", "syn", "derived", "km2", "upstream area"),
        ("syn_river", "syn", "derived", "0/1", f"discharge > {RIVER_MIN_Q} m3/s and area > {RIVER_MIN_AREA} km2"),
        ("syn_strahler", "syn", "derived", "order", "Strahler order of syn_river cells"),
        ("syn_lake", "syn", "derived", "0/1",
         f"depression > {LAKE_MIN_DEPTH} km deep in a subsiding setting, or a closed basin"),
        ("syn_alluvial_fill", "syn", "derived", "0/1",
         "depression in a non-subsiding setting, taken as sediment-filled plain"),
        ("syn_endorheic", "syn", "derived", "0/1", "closed basin: lake evaporation >= inflow"),
        ("syn_wetness", "syn", "derived", "0-1",
         f"alluvial fill x clip(1 - relief/{SWAMP_RELIEF_KM} km) x "
         f"clip(runoff/{SWAMP_RUNOFF_M_YR} m/yr), or 1 on a lake"),
        ("syn_swamp", "syn", "derived", "0/1", f"syn_wetness >= {SWAMP_MIN}"),
        ("syn_basin_id", "syn", "derived", "id", "cell index (row*720+col) of the basin outlet or sink"),
        ("syn_flow_to", "syn", "derived", "id", "cell index this cell drains to; -1 at outlets"),
        ("syn_dist_river_km", "syn", "derived", "km", "to nearest syn_river cell"),
        ("syn_soil_order_cell", "syn", "derived", "class",
         "USDA order from this cell's own conditions (see derive_world.soil_order_cells)"),
        ("syn_soil_order", "syn", "derived", "class",
         "USDA order naming this cell's map soil class: the commonest cell order in the class"),
    ]
    meta += [
        ("syn_block", "syn", "tectonic_history", "name", "paleocontinent the cell belongs to"),
        ("syn_crust", "syn", "tectonic_history", "class", "continental (paleo crust or land) or oceanic"),
        ("syn_basement_province", "syn", "tectonic_history", "class", "crustal province of the basement"),
        ("syn_basement_lith", "syn", "tectonic_history", "class", "basement rock type"),
        ("syn_basement_age_ma", "syn", "tectonic_history", "Ma (Earth-eq.)",
         "age of basement formation or last metamorphism; subtract 430 for age before present"),
        ("syn_surface_lith", "syn", "tectonic_history", "class", "rock exposed at the surface"),
        ("syn_surface_unit", "syn", "tectonic_history", "name", "stratigraphic unit exposed"),
        ("syn_surface_event", "syn", "tectonic_history", "name", "event that made the exposed unit"),
        ("syn_surface_age_ma", "syn", "tectonic_history", "Ma (Earth-eq.)", "age of the exposed unit"),
        ("syn_cover_km", "syn", "tectonic_history", "km", "sedimentary/volcanic cover left above basement"),
        ("syn_erosion_km", "syn", "tectonic_history", "km",
         "erosion depth from elevation, relief and setting"),
        ("syn_paleolat_540", "syn", "tectonic_history", "deg", "paleolatitude at 540 Ma (Earth-eq.)"),
        ("syn_paleolat_445", "syn", "tectonic_history", "deg", "paleolatitude at 445 Ma (Earth-eq.)"),
        ("syn_ocean_crust_age_myr", "syn", "derived", "Myr",
         f"distance to ridge / {OCEAN_HALF_RATE_KM_MYR} km/Myr half-rate; oceanic crust only"),
        ("syn_dist_convergent_km", "syn", "derived", "km", "to nearest trench or active collision"),
        ("syn_seismic_index", "syn", "derived", "0-1", "exp(-distance to convergent boundary / 250 km)"),
        ("syn_active_volcanic", "syn", "derived", "0/1", "volcanic arc within 350 km of a trench"),
    ]
    meta += ore_meta
    if clim is not None:
        src = "climate_world"
        meta += [
            ("syn_temp_c", "syn", src, "degC", "annual mean temperature: insolation profile, lapse "
             "rate, continentality, coastal upwelling"),
            ("syn_temp_range_c", "syn", src, "degC", "warmest minus coldest month"),
            ("syn_gdd", "syn", src, "degC days", "growing-degree days above 5 degC"),
            ("syn_precip_m_yr", "syn", src, "m/yr",
             "precipitation: ocean moisture carried on the prevailing wind of each "
             "circulation band, rained out by band, uplift and distance"),
            ("syn_pet_m_yr", "syn", src, "m/yr", "potential evaporation, FAO-56 Penman-Monteith by month: insolation, "
             "sunshine from cloud, dew-point humidity"),
            ("syn_aet_m_yr", "syn", src, "m/yr", "actual evaporation, Budyko curve (Fu form)"),
            ("syn_aridity", "syn", src, "ratio", "precipitation / potential evaporation (UNEP index)"),
            ("syn_runoff_climate_m_yr", "syn", src, "m/yr", "precipitation - actual evaporation"),
            ("syn_biome", "syn", src, "class",
             "biome the climate fields imply (climate_world.BIOME_RULE); replaces fic_biome "
             "in this world (D10, U 2026-11-19)"),
        ]
    fd = pd.read_sql("select * from field_dictionary", con)
    fd = fd[~fd.field.isin([m[0] for m in meta])]
    fd = pd.concat([fd, pd.DataFrame(meta, columns=fd.columns)], ignore_index=True)
    fd.to_sql("field_dictionary", con, index=False, if_exists="replace")
    con.close()

    write_previews(df, dr, previews_dir)

    print("derive: settings", pd.Series(setting_name[land]).value_counts().to_dict())
    print("derive: trench cells", int(trench.sum()), "ridge cells", int(ridge.sum()))
    print("derive: river cells", int(dr["river"].sum()), "lake cells", int(dr["lake"].sum()),
          "endorheic cells", int(dr["endorheic"].sum()), "max order", int(dr["strahler"].max()))
    print("derive: soils", names)
    print("derive: ores changed", int(deps2.changed.sum()), "of", len(deps2),
          deps2.groupby("ore_type").size().to_dict())
    return dict(setting=s, dr=dr, names=names, deps=deps2)


if __name__ == "__main__":
    import sys
    if "--v2" in sys.argv:
        # WP8: the world with climate fields, written beside world.gpkg
        main(out=os.path.join(HERE, "gis", "world_v2.gpkg"), climate=True)
    else:
        main()
