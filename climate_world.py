"""
Climate fields for the world build (WP8 stage A): annual temperature and
its seasonal range, growing-degree days, precipitation, potential and
actual evaporation, runoff and an aridity index, per grid cell.

Everything is derived from the grid by stated physical rules, not copied
from Earth's map (all forms and numbers C):

  temperature     a zonal sea-level profile from annual insolation
                  (T_pole + (T_eq - T_pole) cos^2 lat, the leading Legendre
                  term of an energy-balance model), a lapse rate on
                  fic_elev_km, colder winters and a colder mean with
                  continentality, and cooling beside upwelling coasts
                  (the paleo ocean model's vertical velocity)
  seasons         a half-amplitude that grows with latitude, more over
                  land far from the windward ocean
  precipitation   prevailing winds by circulation band (trade easterlies,
                  westerlies, polar easterlies); air takes up water over
                  the sea toward a saturation level that rises 7%/degC
                  (Clausius-Clapeyron) and rains it out over land at a
                  rate set by the band (rising air at the ITCZ and the
                  polar front, sinking air in the subtropics), more where
                  it is forced uphill and less where it descends; part of
                  the rain is evaporated again and carried on (recycling)
  water balance   potential evaporation from degree-days above 0 degC;
                  actual evaporation by Budyko's curve (Fu's form);
                  runoff = P - AET; aridity = P / PET (the UNEP index)

The free parameters are fitted so that a fixed climate-to-biome rule
(Koppen and UNEP thresholds, BIOME_RULE) reproduces the drawn biome map
(fic_biome) as well as it can. Where they still disagree the climate's
biome is used in world_v2 (syn_biome; D10, U 2026-11-19).

Run:  python derive_world.py --v2   (adds these fields to gis/world_v2.gpkg)
      python climate_world.py       (fit and QA figures only, no write)
"""
import json
import os

import numpy as np
from scipy import ndimage

NY, NX, RES = 360, 720, 0.5
HERE = os.path.dirname(os.path.abspath(__file__))
QA_DIR = os.path.join(HERE, "gis", "qa")
BIOMES = ["Jungle", "Desert", "Grassland", "Temperate forest", "Tundra"]

# ---- parameters (C) ---------------------------------------------------------
# Defaults; FIT_KEYS are refitted by fit() against the drawn biome map and
# the fitted values are kept in gis/qa/climate_fit.json.
PARAMS = dict(
    T_EQ=27.0,         # degC, sea-level annual mean at the equator
    T_POLE=-15.0,      # degC, the same at the poles (maritime)
    LAPSE=6.5,         # degC per km of elevation
    A0=1.0,            # degC, seasonal half-amplitude at the equator
    A1=22.0,           # degC x |sin lat|, half-amplitude in a continental interior
    A_SEA=0.25,        # share of A1 felt on a windward coast
    C_COLD=6.0,        # degC x sin^2 lat colder annual mean in an interior
    L_CONT=1000.0,     # km over land along the wind for continentality to reach 1-1/e
    U_COOL=4.0,        # degC cooling at full coastal upwelling
    PHI_HADLEY=30.0,   # deg, edge between trade easterlies and westerlies
    PHI_POLAR=60.0,    # deg, edge between westerlies and polar easterlies
    W_ITCZ=10.0,       # deg, half-width of the equatorial rising belt
    PHI_FRONT=50.0,    # deg, latitude of the polar-front rain belt
    W_FRONT=12.0,      # deg, its half-width
    Z_ITCZ=2.0,        # rain-out factor at the ITCZ
    Z_FRONT=1.0,       # at the polar front
    Z_BASE=0.25,       # under sinking air (subtropics, poles)
    P0=1.6,            # m/yr, rain potential of saturated air at 25 degC
    CC=0.07,           # per degC, Clausius-Clapeyron
    L_OCEAN=800.0,     # km of sea for air to come back to saturation
    L_RAIN=1500.0,     # km over land to rain out 1-1/e of the air's water at factor 1
    RECYCLE=0.5,       # share of rain evaporated again into the passing air
    V_MER=0.3,         # meridional / zonal wind speed
    K_EDDY=0.1,        # eddy mixing with each neighbouring row, per row-width travelled
    K_ORO=0.15,        # extra rain-out per (m of rise per km) of upwind slope
    K_LEE=0.1,         # rain suppression per (m of descent per km)
    PET_K=1.75e-4,     # m of potential evaporation per degree-day above 0 degC
    FU_W=2.6,          # Fu's Budyko parameter
)
FIT_KEYS = ["T_EQ", "T_POLE", "PHI_HADLEY", "W_ITCZ", "PHI_FRONT", "Z_ITCZ",
            "Z_FRONT", "Z_BASE", "P0", "L_RAIN", "K_ORO", "RECYCLE", "V_MER",
            "K_EDDY"]
BOUNDS = dict(T_EQ=(22, 32), T_POLE=(-30, 0), PHI_HADLEY=(20, 38),
              W_ITCZ=(5, 20), PHI_FRONT=(40, 62), Z_ITCZ=(0.5, 4),
              Z_FRONT=(0.3, 3), Z_BASE=(0.05, 1), P0=(0.5, 6),
              L_RAIN=(400, 4000), K_ORO=(0, 0.5), RECYCLE=(0, 0.8),
              V_MER=(0, 0.6), K_EDDY=(0, 0.25))

# Climate-to-biome rule (fixed, C, standard thresholds): Koppen E (warmest
# month under 10 degC) is tundra; UNEP arid (P/PET < 0.2) is desert; UNEP
# semi-arid and dry subhumid (< 0.65) is grassland; Koppen A (coldest month
# 18 degC or more) is jungle; the rest is temperate forest.
BIOME_RULE = dict(TUNDRA_WARM=10.0, DESERT_AI=0.2, GRASS_AI=0.65,
                  JUNGLE_COLD=18.0)
GDD_BASE = 5.0


def lat_grid():
    lat = 90 - RES * (np.arange(NY) + 0.5)
    return np.repeat(lat[:, None], NX, 1)


def degree_days(T, A, base):
    """Degree-days above `base` in a year whose daily mean is the annual
    mean T plus a sinusoid of half-amplitude A (degC x days)."""
    th = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    d = np.maximum(T[..., None] + A[..., None] * np.sin(th) - base, 0)
    return 365.0 * d.mean(-1)


def march(q0_sea, land, dx, rate, west, south, mer):
    """Carry the air's rain potential along each row with the wind. Over
    sea it relaxes toward q0_sea (rate[0] per cell); over land a share
    rate[1] of it falls as rain, and (1 - recycling) of that is lost.
    Rows in `west` are walked toward lower longitude. At each step the
    air also takes a share mer[0] from the row upwind of it in latitude
    (the wind's meridional part: `south` rows blow toward the south pole)
    and mixes a share mer[1] with both neighbouring rows (eddies); both
    only between rows walked the same way, so the columns line up. Two
    laps round the globe, so a row's start does not matter. Returns rain
    potential at each cell (before its own rain-out) and km of land
    crossed since the last sea cell."""
    flip = lambda a: np.where(west[:, None], a[:, ::-1], a)  # noqa: E731
    qs, ld, (rs, rl, keep) = flip(q0_sea), flip(land), (flip(r) for r in rate)
    same_n = np.r_[False, west[1:] == west[:-1]]    # row r-1 walked the same way
    same_s = np.r_[west[:-1] == west[1:], False]    # row r+1
    adv = mer[0] * np.where(south, same_n, same_s)
    mix_n, mix_s = mer[1] * same_n, mer[1] * same_s
    q = qs[:, 0].copy()
    d = np.zeros(NY)
    Q = np.zeros((NY, NX))
    D = np.zeros((NY, NX))
    for lap in range(2):
        for c in range(NX):
            sea = ~ld[:, c]
            d = np.where(sea, 0.0, d + dx)
            if lap:
                Q[:, c], D[:, c] = q, d
            q = np.where(sea, q + (qs[:, c] - q) * rs[:, c],
                         q * (1 - rl[:, c] * keep[:, c]))
            qn, qsth = np.r_[q[:1], q[:-1]], np.r_[q[1:], q[-1:]]
            q = q + adv * (np.where(south, qn, qsth) - q) + \
                mix_n * (qn - q) + mix_s * (qsth - q)
    return flip(Q), flip(D)


def fields(inp, p=PARAMS):
    """All climate fields from the build's inputs (dict of (NY, NX) grids:
    land, elev_km, dcoast_km, upwelling) and parameters p."""
    LAT = lat_grid()
    phi = np.abs(LAT)
    land = inp["land"]
    s2 = np.sin(np.radians(LAT)) ** 2
    T0 = p["T_POLE"] + (p["T_EQ"] - p["T_POLE"]) * (1 - s2)
    # upwelling: the ocean model's vertical velocity near the cell (m/s,
    # scaled so 1.5e-6 is full); cools the sea and the coast beside it
    up = np.clip(np.nan_to_num(inp["upwelling"]) / 1.5e-6, 0, 1)
    T_sea = T0 - p["U_COOL"] * up

    # prevailing wind and rain-out factor by band
    west = (phi[:, 0] < p["PHI_HADLEY"]) | (phi[:, 0] > p["PHI_POLAR"])
    z = p["Z_ITCZ"] * np.exp(-(LAT / p["W_ITCZ"]) ** 2) + \
        p["Z_FRONT"] * np.exp(-((phi - p["PHI_FRONT"]) / p["W_FRONT"]) ** 2) + \
        p["Z_BASE"]
    dx = np.maximum(RES * 111.2 * np.cos(np.radians(LAT[:, 0])), 5.0)
    # slope along the wind on the smoothed land surface (m per km)
    Es = ndimage.gaussian_filter(np.where(land, inp["elev_km"], 0.0), 1.0,
                                 mode=("nearest", "wrap"))
    dE = (np.roll(Es, -1, 1) - np.roll(Es, 1, 1)) / 2 * 1000.0
    slope = np.where(west[:, None], -dE, dE) / dx[:, None]
    oro = (1 + p["K_ORO"] * np.clip(slope, 0, None)) * \
        np.exp(-p["K_LEE"] * np.clip(-slope, 0, None))
    r_land = np.clip(z * oro * dx[:, None] / p["L_RAIN"], 0, 0.9)
    q_sat = p["P0"] * np.exp(p["CC"] * (T_sea - 25.0))
    r_sea = np.broadcast_to(1 - np.exp(-dx / p["L_OCEAN"])[:, None], (NY, NX))
    keep = np.full((NY, NX), 1 - p["RECYCLE"])
    # trades and polar easterlies blow toward the equator, westerlies
    # toward the pole; shares of a row taken per step scale with the step
    south = (LAT[:, 0] > 0) == west
    per_row = dx / (RES * 111.2)
    mer = (np.clip(p["V_MER"] * per_row, 0, 0.45),
           np.clip(p["K_EDDY"] * per_row, 0, 0.25))
    q, dup = march(q_sat, land, dx, (r_sea, r_land, keep), west, south, mer)
    # rain: the share of the air's potential falling here, as a depth per
    # year over the cell (rain-out per km x L_RAIN keeps it a rate);
    # smoothed a little for the wind's meridional part and for eddies
    P = np.where(land, q * r_land * p["L_RAIN"] / dx[:, None], q * z)
    P = ndimage.gaussian_filter(P, 1.0, mode=("nearest", "wrap"))

    # continentality: land crossed along the wind, and plain distance to
    # the sea, averaged
    dland = 0.5 * (dup + np.clip(inp["dcoast_km"], 0, None))
    cont = np.where(land, 1 - np.exp(-dland / p["L_CONT"]), 0.0)
    A = p["A0"] + p["A1"] * np.sqrt(s2) * (p["A_SEA"] + (1 - p["A_SEA"]) * cont)
    T = T_sea - p["C_COLD"] * cont * s2 - \
        p["LAPSE"] * np.where(land, np.clip(inp["elev_km"], 0, None), 0.0)

    gdd = degree_days(T, A, GDD_BASE)
    pet = p["PET_K"] * degree_days(T, A, 0.0)
    ratio = pet / np.maximum(P, 1e-6)
    w = p["FU_W"]
    aet = P * (1 + ratio - (1 + ratio ** w) ** (1 / w))
    runoff = np.clip(P - aet, 0, None)
    arid = P / np.maximum(pet, 1e-3)
    return dict(temp_c=T, temp_range_c=2 * A, gdd=gdd, precip_m_yr=P,
                pet_m_yr=pet, aet_m_yr=aet, runoff_m_yr=runoff, aridity=arid,
                continentality=cont)


def biome_rule(f, rule=BIOME_RULE):
    """Biome index (BIOMES) a cell's climate implies."""
    T, A, ai = f["temp_c"], f["temp_range_c"] / 2, f["aridity"]
    out = np.full(T.shape, BIOMES.index("Temperate forest"))
    out[T - A >= rule["JUNGLE_COLD"]] = BIOMES.index("Jungle")
    out[ai < rule["GRASS_AI"]] = BIOMES.index("Grassland")
    out[ai < rule["DESERT_AI"]] = BIOMES.index("Desert")
    out[T + A < rule["TUNDRA_WARM"]] = BIOMES.index("Tundra")
    return out


def agreement(pred, drawn, land, area):
    """Area-weighted recall per drawn biome, its mean (the fit's score),
    and overall area-weighted agreement."""
    rec = {}
    for k, b in enumerate(BIOMES):
        m = land & (drawn == k)
        if m.any():
            rec[b] = float(area[m & (pred == k)].sum() / area[m].sum())
    overall = float(area[land & (pred == drawn)].sum() / area[land].sum())
    return rec, float(np.mean(list(rec.values()))), overall


def fit(inp, drawn, area, n_random=300, n_rounds=4, seed=0, verbose=True):
    """Fit FIT_KEYS: a random search inside BOUNDS, then coordinate
    refinement, maximising mean per-biome agreement (so no biome's area
    swamps the others)."""
    rng = np.random.default_rng(seed)
    land = inp["land"]

    def score(p):
        return agreement(biome_rule(fields(inp, p)), drawn, land, area)[1]

    best = dict(PARAMS)
    best_s = score(best)
    for _ in range(n_random):
        p = dict(best)
        for k in FIT_KEYS:
            lo, hi = BOUNDS[k]
            p[k] = rng.uniform(lo, hi)
        s = score(p)
        if s > best_s:
            best, best_s = p, s
    if verbose:
        print(f"climate fit: random search best {best_s:.3f}")
    for rd in range(n_rounds):
        step = 0.25 / (rd + 1)
        for k in FIT_KEYS:
            lo, hi = BOUNDS[k]
            for sgn in (-1, 1):
                p = dict(best)
                p[k] = float(np.clip(best[k] + sgn * step * (hi - lo), lo, hi))
                s = score(p)
                if s > best_s:
                    best, best_s = p, s
        if verbose:
            print(f"climate fit: round {rd + 1} {best_s:.3f}")
    return best, best_s


def within_biome(v, drawn, area, land, cap=4.0):
    """v relative to its drawn biome's area-weighted mean on land, capped
    at `cap` and renormalised to a mean of 1 in each biome (1 at sea and
    where a biome's mean is 0). Used to give a by-biome quantity the
    climate's gradient while keeping each biome's total (C)."""
    out = np.ones(v.shape)
    for k in range(len(BIOMES)):
        m = land & (drawn == k)
        a, x = area[m], np.clip(v[m], 0, None)
        for _ in range(3):
            mu = (x * a).sum() / max(a.sum(), 1e-9)
            if mu <= 0:
                break
            x = np.minimum(x / mu, cap)
        else:
            out[m] = x / ((x * a).sum() / a.sum())
    return out


# ---- QA ------------------------------------------------------------------------
BIOME_RGB = np.array([(20, 90, 30), (225, 200, 140), (175, 200, 100),
                      (90, 140, 70), (235, 235, 235)], np.uint8)


def qa_figures(f, drawn, pred, land, folder=QA_DIR):
    """One map per field, the climate-implied biomes beside the drawn ones,
    and a map of where they disagree."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(folder, exist_ok=True)
    ext = (-180, 180, -90, 90)
    spec = [("temp_c", "annual mean temperature (degC)", "RdYlBu_r", None),
            ("temp_range_c", "seasonal range, warmest - coldest month (degC)",
             "magma", None),
            ("gdd", "growing-degree days above 5 degC", "YlGn", None),
            ("precip_m_yr", "precipitation (m/yr)", "Blues", (0, 3)),
            ("pet_m_yr", "potential evaporation (m/yr)", "Oranges", None),
            ("runoff_m_yr", "runoff, P - AET (m/yr)", "PuBu", (0, 1.5)),
            ("aridity", "aridity index P/PET", "BrBG", (0, 2))]
    for k, title, cmap, lim in spec:
        v = np.where(land, f[k], np.nan)
        fig, ax = plt.subplots(figsize=(12, 6))
        lo, hi = lim or (np.nanpercentile(v, 1), np.nanpercentile(v, 99))
        im = ax.imshow(v, extent=ext, cmap=cmap, vmin=lo, vmax=hi,
                       interpolation="nearest")
        ax.contour(np.linspace(-180, 180, NX), np.linspace(90, -90, NY),
                   land.astype(float), [0.5], colors="k", linewidths=0.3)
        ax.set_title(f"syn_{k}: {title}")
        fig.colorbar(im, ax=ax, shrink=0.7)
        fig.savefig(os.path.join(folder, f"climate_{k}.png"), dpi=90,
                    bbox_inches="tight")
        plt.close(fig)

    def rgb(cls):
        img = np.full((NY, NX, 3), (40, 90, 160), np.uint8)
        img[land] = BIOME_RGB[cls[land]]
        return img
    fig, axs = plt.subplots(3, 1, figsize=(12, 18))
    axs[0].imshow(rgb(drawn), extent=ext)
    axs[0].set_title("drawn biomes (fic_biome)")
    axs[1].imshow(rgb(pred), extent=ext)
    axs[1].set_title("biomes the derived climate implies (syn_biome, used in world_v2)")
    dis = np.full((NY, NX, 3), 255, np.uint8)
    dis[~land] = (200, 215, 230)
    agree = land & (pred == drawn)
    dis[agree] = (170, 170, 170)
    bad = land & ~agree
    dis[bad] = BIOME_RGB[pred[bad]]
    axs[2].imshow(dis, extent=ext)
    axs[2].set_title("disagreements, coloured by the climate's biome "
                     "(grey: agree)")
    from matplotlib.patches import Patch
    axs[2].legend(handles=[Patch(color=BIOME_RGB[k] / 255, label=b)
                           for k, b in enumerate(BIOMES)],
                  loc="lower left", fontsize=8)
    for a in axs:
        a.set_xticks(range(-180, 181, 60))
        a.set_yticks(range(-90, 91, 30))
    fig.savefig(os.path.join(folder, "climate_biome_disagreement.png"),
                dpi=80, bbox_inches="tight")
    plt.close(fig)


def confusion(pred, drawn, land, area):
    """Area (share of each drawn biome) by climate biome."""
    import pandas as pd
    rows = []
    for k, b in enumerate(BIOMES):
        m = land & (drawn == k)
        tot = area[m].sum()
        rows.append([b] + [float(area[m & (pred == j)].sum() / tot)
                           for j in range(len(BIOMES))] + [float(tot)])
    return pd.DataFrame(rows, columns=["drawn"] + BIOMES + ["area_km2"])


def inputs_from_cells(df):
    """The (NY, NX) input grids from the cells table."""
    def g(col, fill=np.nan):
        out = np.full((NY, NX), fill, float)
        out[df["row"].values, df["col"].values] = df[col].values
        return out
    land = g("fic_land", 0) > 0.5
    drawn = np.full((NY, NX), -1, int)
    b = df["fic_biome"].map({x: i for i, x in enumerate(BIOMES)}).fillna(-1)
    drawn[df["row"].values, df["col"].values] = b.astype(int).values
    up = np.where(land, g("syn_reach_upwelling"),
                  g("syn_ocean_vertical_velocity"))
    return dict(land=land, elev_km=g("fic_elev_km", 0.0),
                dcoast_km=g("fic_dist_coast_km", 0.0), upwelling=up), \
        drawn, g("area_km2", 0.0)


def build(df, refit=True, verbose=True):
    """Fit (or load the saved fit), compute the fields, write the QA
    figures and the fit record. Returns (fields, climate biome, params,
    record)."""
    inp, drawn, area = inputs_from_cells(df)
    land = inp["land"]
    path = os.path.join(QA_DIR, "climate_fit.json")
    if refit or not os.path.exists(path):
        p, s = fit(inp, drawn, area, verbose=verbose)
    else:
        with open(path) as fh:
            p = {**PARAMS, **json.load(fh)["params"]}
    f = fields(inp, p)
    pred = biome_rule(f)
    rec, mean_rec, overall = agreement(pred, drawn, land, area)
    conf = confusion(pred, drawn, land, area)
    record = dict(params={k: float(f"{v:.4g}") for k, v in p.items()},
                  fitted=FIT_KEYS, rule=BIOME_RULE,
                  recall_by_biome={k: round(v, 3) for k, v in rec.items()},
                  mean_recall=round(mean_rec, 3), overall=round(overall, 3),
                  confusion=conf.round(3).to_dict(orient="records"))
    os.makedirs(QA_DIR, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(record, fh, indent=1)
    qa_figures(f, drawn, pred, land)
    if verbose:
        print("climate: agreement by drawn biome", record["recall_by_biome"],
              "mean", record["mean_recall"], "overall", record["overall"])
        print(conf.round(3).to_string(index=False))
    return f, pred, p, record


if __name__ == "__main__":
    import geopandas as gpd
    cells = gpd.read_file(os.path.join(HERE, "gis", "world.gpkg"),
                          layer="cells", ignore_geometry=True)
    build(cells)
