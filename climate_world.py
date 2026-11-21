"""
Climate fields for the world build (WP8 stage A): annual temperature and
its seasonal range, growing-degree days, precipitation, potential and
actual evaporation, runoff and an aridity index, per grid cell.

Everything is derived from the grid by stated physical rules, not copied
from Earth's map (all forms and numbers C):

  temperature     a zonal sea-level profile from annual insolation
                  (T_pole + (T_eq - T_pole) cos^2 lat, the leading Legendre
                  term of an energy-balance model, plus the next term,
                  T_MID x 4 sin^2 cos^2: heat carried poleward flattens
                  the tropics), a lapse rate on fic_elev_km less the
                  warming of broad plateaus (MASS_K), colder
                  winters and a colder mean with continentality, cooling
                  beside upwelling coasts (the paleo ocean model's
                  vertical velocity), and warmer dry land (what a surface
                  does not evaporate it sheds as heat: T_DRY x
                  (1 - AET/PET))
  seasons         a half-amplitude that grows with latitude, more over
                  land far from the windward ocean
  ocean currents  wind-driven gyres from basin geometry: in each wide
                  basin, warm poleward currents on its western side and
                  cold equatorward ones on its eastern side in the
                  subtropics, the reverse in the subpolar gyres; they warm
                  or cool the sea, and the wind carries that inland
  precipitation   prevailing winds by circulation band (trade easterlies,
                  westerlies, polar easterlies), month by month: the
                  ITCZ follows the sun, further over longitudes with much
                  land and with high plateaus (the monsoon; a plateau
                  heats air above the boundary layer); that first guess
                  is then moved to where the month's near-surface moist
                  static energy peaks (Prive and Plumb 2007) and the
                  month run again; its rain belt is
                  wider over land, the trades blow toward it, between
                  the equator and a displaced ITCZ the wind turns
                  westerly (the monsoon westerly), and the
                  storm tracks and band edges shift with it; air takes up
                  water over
                  the sea toward a saturation level that rises 7%/degC
                  (Clausius-Clapeyron) and rains it out over land at a
                  rate set by the band (rising air at the ITCZ and the
                  polar front, sinking air in the subtropics), more where
                  it is forced uphill and less where it descends; part of
                  the rain is evaporated again and carried on (recycling);
                  warm land in summer adds convective rain-out (from the
                  water the air already carries); the Hadley cell's
                  sinking branch dries the air over land without rain,
                  except on the subtropical highs' western flanks in
                  summer (near a wide ocean to the east), where the flow
                  turns poleward and rises
  water balance   potential evaporation by FAO-56 Penman-Monteith, month
                  by month: net radiation from annual insolation, with
                  monthly insolation, sunshine set by cloud (more under
                  raining air), and humidity from the dew point (FAO-56's
                  rule: the night minimum, a few degrees lower in dry
                  climates; the day-night range widens under clear sky);
                  actual evaporation by Budyko's curve (Fu's form), times
                  the rain's timing: a monthly soil-water bucket's
                  evaporation with the real monthly rain over that with
                  the same rain spread evenly (rain in a short wet season
                  or in winter runs off unused); runoff = P - AET;
                  aridity = P / PET (the UNEP index), and the same times
                  the timing factor, which the biome rule and the sim's
                  yields read

The parameters take physically motivated values (PARAMS), not values
fitted to the drawn biome map: a first version was fitted to it, and the
fit learnt the map's errors (no equatorial rain belt, dry interiors; U,
2026-11-19, asked for a refit on physical grounds). One constant is set
from a global constraint: P0, the air's rain potential, is chosen so that
mean precipitation over the whole globe is P_GLOBAL (1.0 m/yr, the
planetary water cycle set by the surface energy budget). A fixed
climate-to-biome rule (Koppen and UNEP thresholds, BIOME_RULE) then gives
each cell's biome; world_v2 uses it (syn_biome; D10, U 2026-11-19). Its
agreement with the drawn map (fic_biome) is reported, not fitted.

Run:  python derive_world.py --v2   (adds these fields to gis/world_v2.gpkg)
      python climate_world.py       (QA figures and record only, no write)
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
# Values with physical grounds where there are any (lapse rate,
# Clausius-Clapeyron, Fu's w, band edges at the Hadley and Ferrel cell
# boundaries, recycling about half of land rain); the rest are round
# values. P0 is calibrated (calibrate) and kept, with the rest, in
# gis/qa/climate_fit.json.
PARAMS = dict(
    T_EQ=27.0,         # degC, sea-level annual mean at the equator
    T_POLE=-15.0,      # degC, the same at the poles (maritime)
    LAPSE=6.5,         # degC per km of elevation
    # mass-elevation effect: a broad plateau heats the air above it, so
    # its surface is warmer than the free air at the same height (about
    # 4-6 degC on the Tibetan interior); MASS_K degC per km of elevation
    # smoothed over L_MASS
    MASS_K=1.0,        # degC per km
    L_MASS=300.0,      # km, smoothing scale (gaussian sigma)
    A0=1.0,            # degC, seasonal half-amplitude at the equator
    A1=22.0,           # degC x |sin lat|, half-amplitude in a continental interior
    A_SEA=0.25,        # share of A1 felt on a windward coast
    C_COLD=6.0,        # degC x sin^2 lat colder annual mean in an interior
    L_CONT=1000.0,     # km over land along the wind for continentality to reach 1-1/e
    U_COOL=4.0,        # degC cooling at full coastal upwelling
    PHI_HADLEY=30.0,   # deg, edge between trade easterlies and westerlies
    PHI_POLAR=60.0,    # deg, edge between westerlies and polar easterlies
    W_ITCZ=5.0,        # deg, half-width of the equatorial rising belt at one season (10 for the annual mean before the seasons, 2026-11-20)
    PHI_FRONT=50.0,    # deg, latitude of the polar-front rain belt
    W_FRONT=12.0,      # deg, its half-width
    Z_ITCZ=2.0,        # rain-out factor at the ITCZ
    Z_FRONT=1.0,       # at the polar front
    Z_BASE=0.1,        # under sinking air (subtropics, poles); 0.25 until 2026-11-20 (U: lower)
    P0=2.3,            # m/yr, rain potential of saturated air at 25 degC (calibrated)
    CC=0.07,           # per degC, Clausius-Clapeyron
    L_OCEAN=800.0,     # km of sea for air to come back to saturation
    L_RAIN=2000.0,     # km over land to rain out 1-1/e of the air's water at factor 1
    RECYCLE=0.5,       # share of rain evaporated again into the passing air
    V_MER=0.3,         # meridional / zonal wind speed
    K_EDDY=0.1,        # eddy mixing with each neighbouring row, per row-width travelled
    K_ORO=0.15,        # extra rain-out per (m of rise per km) of upwind slope
    K_LEE=0.1,         # rain suppression per (m of descent per km)
    # seasons (C; Earth: the ITCZ moves about 5 deg over open ocean and
    # 15-25 deg over the monsoon continents; storm tracks about 5 deg)
    ITCZ_SEA=5.0,      # deg the ITCZ moves toward the summer pole over open ocean
    ITCZ_LAND=18.0,    # over longitudes all land within 30 deg of the equator
    LF_SMOOTH=10.0,    # deg of longitude the land fraction is averaged over
    BAND_SHIFT=5.0,    # deg band edges and the polar front move with the season
    # ocean currents (C; Earth's gyre-edge sea temperature anomalies are
    # a few degC)
    BASIN_MIN=2000.0,  # km of open sea along a row for a gyre to form
    COAST_MIN=0.5e6,   # km2: smaller landmasses do not bound a gyre
    L_WBC=400.0,       # km e-folding width of western boundary currents
    L_EBC=800.0,       # km of eastern boundary currents
    A_WBC=4.0,         # degC at a western boundary
    A_EBC=3.0,         # degC at an eastern boundary
    L_MARITIME=1000.0, # km inland over which the sea's temperature anomaly fades
    S_CLEAR=0.85,      # sunshine fraction under clear, sinking air
    S_CLOUD=0.35,      # under the most rain-bearing cloud
    P_CLOUD=1.0,       # m/yr of rain at which cloud is 1 - 1/e of its maximum
    DTR_CLOUD=6.0,     # degC day-night range under full cloud
    DTR_CLEAR=16.0,    # under clear sky
    DEW_ARID=2.5,      # degC the dew point lies below the night minimum in clear, dry air
    U2=2.0,            # m/s wind at 2 m (FAO-56 default)
    ALBEDO=0.23,       # FAO-56 reference surface
    FU_W=2.6,          # Fu's Budyko parameter
    # monsoon wind (C, 2026-11-20, U: "monsoons having their own wind"):
    # between the equator and a displaced summer ITCZ the low-level flow
    # turns westerly (the south-west monsoon); weight of the westerly
    # there (1: wholly westerly; 0: off)
    MONSOON_W=1.0,
    # rain seasonality (C, 2026-11-20, U): plant-available soil water a
    # monthly bucket carries between months (typical 100-200 mm)
    S_MAX=0.15,        # m
    # the ITCZ by moist static energy (C, 2026-11-21, U: "the bigger
    # fix"; Prive and Plumb 2007, Emanuel 1995: a monsoon's convergence
    # zone sits at the maximum of near-surface moist static energy).
    # Each summer month, the ITCZ from the land-fraction rule gives a
    # first march; the ITCZ then moves to where that march's air has the
    # most moist static energy, and the month is run again (ITCZ_ITER
    # times; 0 keeps the land-fraction rule)
    ITCZ_ITER=1,
    G_CP=9.8,          # degC per km: g / cp, height's share (dry adiabat)
    LV_CP=2490.0,      # degC per (kg/kg): latent heat / cp
    RH_BL=0.8,         # relative humidity of the marine boundary layer
    TAU_MSE=2.0,       # degC, softness of the maximum
    MSE_LAT=40.0,      # deg, furthest the ITCZ may sit from the equator
    # Earth climate check fixes (C, 2026-11-21, U: "implement those
    # climate model changes"; docs/earth-climate-check.md (a)-(d))
    # (a) heat carried poleward flattens the tropics: the profile's
    # second Legendre term (P4), as T_MID x 4 sin^2 cos^2, its warming
    # at 45 deg (cos^2 alone gives 6 degC there; Earth's zonal-mean sea
    # surface is about 12)
    T_MID=6.0,         # degC
    # a dry surface sheds as heat what a wet one evaporates: warming at a
    # surface with no evaporation (1 - AET/PET = 1)
    T_DRY=5.0,         # degC
    # (b) summer convection over warm land: rain-out factor added where
    # the month's mean is T_CONV + DT_CONV or more, from 0 at T_CONV;
    # rain only from the moisture the winds already carry
    Z_CONV=1.0,
    T_CONV=18.0,       # degC
    DT_CONV=8.0,       # degC
    # (c) high plateaus heat the air above the depth sea-level land heats
    # (the summer boundary layer, H_BL): within PLAT_LAT of the equator
    # each km above H_BL counts 1/H_BL extra land in the ITCZ's pull
    H_BL=1.5,          # km
    PLAT_LAT=40.0,     # deg
    # (d) the rain belt is wider over land: half-width at an all-land
    # longitude (W_ITCZ over open sea)
    W_ITCZ_LAND=8.0,   # deg
    # and the Hadley cell's sinking branch dries the air over land without
    # rain: dry air from aloft replaces the moist low layer, 1 - 1/e of
    # it over L_SUB of land. It acts equatorward of the Hadley edge
    # (fading over BAND_SHIFT either side of it), less toward the
    # ITCZ's core. In summer the subtropical high's western flank rises:
    # over land within about L_CONT of a wide ocean basin to the east
    # (BASIN_MIN; narrower seas count as land) the sinking fades, and
    # within L_CONT of it the trade rows' meridional flow turns poleward
    L_SUB=2000.0,      # km
)
P_GLOBAL = 1.0        # m/yr, mean precipitation over the whole globe

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


def esat(T):
    """Saturation vapour pressure (kPa) at T degC (FAO-56, Tetens)."""
    return 0.6108 * np.exp(17.27 * T / (T + 237.3))


def penman_pet(T, A, P, LAT, p):
    """Potential evaporation (m/yr) by FAO-56 Penman-Monteith, summed over
    12 months whose mean temperature is T + A sin(month), with that
    month's top-of-atmosphere radiation (FAO-56 eq. 21; declination in
    phase with the temperature, summer in each hemisphere together).
    Sunshine falls from S_CLEAR toward S_CLOUD as rain rises (cloud);
    Angstrom: Rs = (0.25 + 0.5 n/N) Ra. Humidity: the dew point is the
    night minimum (month mean - half the day-night range, which widens
    with sunshine), less up to DEW_ARID in clear air (FAO-56 Annex 6).
    Months below 0 degC and negative values add nothing.
    Returns (PET m/yr, annual-mean relative humidity, sunshine, PET of
    each month in m, (12, NY, NX), month k at local phase 2 pi k / 12)."""
    phi = np.radians(np.abs(LAT))
    clear = 1 - np.exp(-np.clip(P, 0, None) / p["P_CLOUD"])
    sun = p["S_CLEAR"] - (p["S_CLEAR"] - p["S_CLOUD"]) * clear
    c = (sun - p["S_CLOUD"]) / (p["S_CLEAR"] - p["S_CLOUD"])   # 0 cloudy .. 1 clear
    dtr = p["DTR_CLOUD"] + (p["DTR_CLEAR"] - p["DTR_CLOUD"]) * c
    u2, gam = p["U2"], 0.0665            # psychrometric constant at ~0.5 km
    tot, rh_sum, mon = np.zeros(T.shape), np.zeros(T.shape), []
    for th in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        dec = np.radians(23.44) * np.sin(th)
        ws = np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1, 1))
        Ra = 24 * 60 / np.pi * 0.0820 * (ws * np.sin(phi) * np.sin(dec) +
                                         np.cos(phi) * np.cos(dec) * np.sin(ws))
        Rs = (0.25 + 0.5 * sun) * Ra
        Rso = np.maximum(0.75 * Ra, 1e-6)
        Tm = T + A * np.sin(th)
        es = esat(Tm)
        ea = esat(Tm - dtr / 2 - p["DEW_ARID"] * c)
        rh_sum += ea / es
        D = 4098 * es / (Tm + 237.3) ** 2
        Rnl = 4.903e-9 * (Tm + 273.16) ** 4 * (0.34 - 0.14 * np.sqrt(ea)) * \
            (1.35 * np.clip(Rs / Rso, 0, 1) - 0.35)
        Rn = (1 - p["ALBEDO"]) * Rs - Rnl
        et = (0.408 * D * Rn + gam * 900 / (Tm + 273) * u2 * (es - ea)) / \
            (D + gam * (1 + 0.34 * u2))                        # mm/day
        mon.append(np.where(Tm > 0, np.clip(et, 0, None), 0.0) * 365.25 / 12 / 1000.0)
        tot += mon[-1]
    return tot, rh_sum / 12, sun, np.array(mon)


def bucket(Pmon, PETmon, smax):
    """Actual evaporation (m/yr) from a monthly soil-water bucket: each
    month's rain fills the store, evaporation takes up to that month's
    PET from it, and water beyond smax runs off. Three laps from a full
    store, the last one counted."""
    S = np.full(Pmon.shape[1:], smax)
    for lap in range(3):
        aet = np.zeros(Pmon.shape[1:])
        for k in range(12):
            S = S + Pmon[k]
            e = np.minimum(PETmon[k], S)
            S = np.minimum(S - e, smax)
            aet += e
    return aet


def march(q0_sea, land, dx, rate, west, south, mer, prev=None):
    """Carry the air's rain potential along each row with the wind. Over
    sea it relaxes toward q0_sea (rate[0] per cell); over land a share
    rate[1] of it falls as rain, and (1 - recycling) of that is lost.
    A further share rate[3] (sinking air), if given, is lost over land
    without rain. Rows in `west` are walked toward lower longitude. At each step the
    air also takes a share mer[0] from the cell upwind of it in latitude
    (the wind's meridional part: where `south`, a (NY, NX) grid, it
    blows toward the south pole) and mixes a share mer[1] with both
    neighbouring rows (eddies). A neighbour row walked the same way is at
    the same longitude at each step; one walked the other way is not, so
    its value is taken from `prev`, this march's result from a previous
    pass (without `prev`, there is no exchange with it). Two laps round
    the globe, so a row's start does not matter. Returns rain potential at
    each cell (before its own rain-out) and km of land crossed since the
    last sea cell."""
    flip = lambda a: np.where(west[:, None], a[:, ::-1], a)  # noqa: E731
    if len(rate) == 3:
        rate = tuple(rate) + (np.zeros((NY, NX)),)
    qs, ld, (rs, rl, keep, sub) = flip(q0_sea), flip(land), (flip(r) for r in rate)
    sth = flip(south)
    same_n = np.r_[False, west[1:] == west[:-1]]    # row r-1 walked the same way
    same_s = np.r_[west[:-1] == west[1:], False]    # row r+1
    has_n, has_s = np.r_[False, np.ones(NY - 1, bool)], np.r_[np.ones(NY - 1, bool), False]
    if prev is not None:
        pn = flip(np.r_[prev[:1], prev[:-1]])       # row r-1, at row r's longitudes
        ps = flip(np.r_[prev[1:], prev[-1:]])
        ok_n, ok_s = has_n, has_s
    else:
        ok_n, ok_s = same_n, same_s
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
                         q * (1 - rl[:, c] * keep[:, c] - sub[:, c]))
            qn, qsth = np.r_[q[:1], q[:-1]], np.r_[q[1:], q[-1:]]
            if prev is not None:
                qn = np.where(same_n, qn, pn[:, c])
                qsth = np.where(same_s, qsth, ps[:, c])
            up = np.where(sth[:, c], qn, qsth)
            ok_up = np.where(sth[:, c], ok_n, ok_s)
            q = q + mer[0] * ok_up * (up - q) + \
                mer[1] * ok_n * (qn - q) + mer[1] * ok_s * (qsth - q)
    return flip(Q), flip(D)


def carry(a_sea, land, dx, L, west):
    """A sea-surface quantity carried inland along each row with the wind,
    fading by exp(-dx / L) per land cell (two laps, as in march)."""
    flip = lambda a: np.where(west[:, None], a[:, ::-1], a)  # noqa: E731
    av, ld = flip(a_sea), flip(land)
    k = np.exp(-dx / L)
    a = av[:, 0].copy()
    out = np.zeros((NY, NX))
    for lap in range(2):
        for c in range(NX):
            a = np.where(ld[:, c], a * k, av[:, c])
            if lap:
                out[:, c] = a
    return flip(out)


def land_run(land, dx, west):
    """km of land crossed along each row since the last sea cell, walking
    with the wind (two laps, as in march)."""
    flip = lambda a: np.where(west[:, None], a[:, ::-1], a)  # noqa: E731
    ld = flip(land)
    d = np.zeros(NY)
    D = np.zeros((NY, NX))
    for lap in range(2):
        for c in range(NX):
            d = np.where(ld[:, c], d + dx, 0.0)
            if lap:
                D[:, c] = d
    return flip(D)


def coast_distance(land, dx):
    """For each cell, km of open sea along its row to the nearest land to
    its west and to its east (inf where the row has no land)."""
    out = []
    for west in (False, True):            # walking east measures from the west coast
        w = np.full(NY, west)
        flip = lambda a: np.where(w[:, None], a[:, ::-1], a)  # noqa: E731
        ld = flip(land)
        d = np.full(NY, np.inf)
        D = np.zeros((NY, NX))
        for lap in range(2):
            for c in range(NX):
                d = np.where(ld[:, c], 0.0, d + dx)
                if lap:
                    D[:, c] = d
        out.append(flip(D))
    return out[0], out[1]


def current_anomaly(land, LAT, dx, p):
    """Sea-surface temperature anomaly (degC) from wind-driven gyres. In a
    basin at least BASIN_MIN wide along the row: subtropical gyres (about
    8-48 deg) carry warm water poleward on the basin's western side and
    cold water equatorward on its eastern side; subpolar gyres (about
    45-70 deg) the reverse. Each fades from its coast with L_WBC or L_EBC.
    Only landmasses of COAST_MIN or more bound a basin; currents pass
    smaller islands. Also returns the mask of basin sea cells."""
    lab, n = ndimage.label(land, structure=np.ones((3, 3)))
    cell_km2 = (dx * RES * 111.2)[:, None] * np.ones((1, NX))
    big = np.r_[False, ndimage.sum(cell_km2, lab, np.arange(1, n + 1)) >= p["COAST_MIN"]]
    d_w, d_e = coast_distance(big[lab], dx)
    phi = np.abs(LAT)
    st = np.clip(np.sin(np.pi * (phi - 8) / 40), 0, None) * ((phi > 8) & (phi < 48))
    sp = np.clip(np.sin(np.pi * (phi - 45) / 25), 0, None) * ((phi > 45) & (phi < 70))
    basin = (d_w + d_e) >= p["BASIN_MIN"]
    a = p["A_WBC"] * np.exp(-d_w / p["L_WBC"]) * (st - sp) + \
        p["A_EBC"] * np.exp(-d_e / p["L_EBC"]) * (sp - st)
    basin = ~land & basin & np.isfinite(d_w + d_e)
    a = np.where(basin, a, 0.0)
    return ndimage.gaussian_filter(a, 1.0, mode=("nearest", "wrap")), basin


# twelve months, as (the sun's side: sin of the month's phase, +1 at the
# northern summer solstice; number of months with that value)
SEASONS = ((1.0, 1), (0.866, 2), (0.5, 2), (0.0, 2), (-0.5, 2), (-0.866, 2), (-1.0, 1))


def fields(inp, p=PARAMS):
    """All climate fields from the build's inputs (dict of (NY, NX) grids:
    land, elev_km, dcoast_km, upwelling) and parameters p."""
    LAT = lat_grid()
    phi = np.abs(LAT)
    lat1 = LAT[:, 0]
    land = inp["land"]
    s2 = np.sin(np.radians(LAT)) ** 2
    T0 = p["T_POLE"] + (p["T_EQ"] - p["T_POLE"]) * (1 - s2) + \
        4 * p["T_MID"] * s2 * (1 - s2)
    dx = np.maximum(RES * 111.2 * np.cos(np.radians(lat1)), 5.0)
    # upwelling: the ocean model's vertical velocity near the cell (m/s,
    # scaled so 1.5e-6 is full); cools the sea and the coast beside it
    up = np.clip(np.nan_to_num(inp["upwelling"]) / 1.5e-6, 0, 1)
    # gyre currents warm or cool the sea
    sst_anom, basin = current_anomaly(land, LAT, dx, p)
    # km from a wide ocean basin to the east, along the row
    flank = np.exp(-land_run(~basin, dx, np.ones(NY, bool)) / p["L_CONT"]) * land
    T_sea = T0 - p["U_COOL"] * up + sst_anom

    # slope on the smoothed land surface (m per km, toward higher longitude)
    Es = ndimage.gaussian_filter(np.where(land, inp["elev_km"], 0.0), 1.0,
                                 mode=("nearest", "wrap"))
    dE = (np.roll(Es, -1, 1) - np.roll(Es, 1, 1)) / 2 * 1000.0
    q_sat = p["P0"] * np.exp(p["CC"] * (T_sea - 25.0))
    r_sea = np.broadcast_to(1 - np.exp(-dx / p["L_OCEAN"])[:, None], (NY, NX))
    keep = np.full((NY, NX), 1 - p["RECYCLE"])
    per_row = dx / (RES * 111.2)
    mer = (np.clip(p["V_MER"] * per_row, 0, 0.45),
           np.clip(p["K_EDDY"] * per_row, 0, 0.25))

    # land fraction within 30 deg of the equator in each hemisphere, by
    # longitude (the summer continent's heat low draws the ITCZ)
    sig = p["LF_SMOOTH"] / RES
    lf_n = ndimage.gaussian_filter1d(land[(lat1 > 0) & (lat1 < 30)].mean(0), sig, mode="wrap")
    lf_s = ndimage.gaussian_filter1d(land[(lat1 < 0) & (lat1 > -30)].mean(0), sig, mode="wrap")
    # high plateaus heat the air above the boundary layer: extra pull
    hi = np.where(land, np.clip(inp["elev_km"] - p["H_BL"], 0, None) / p["H_BL"], 0.0)
    lf_n = lf_n + ndimage.gaussian_filter1d(
        hi[(lat1 > 0) & (lat1 < p["PLAT_LAT"])].mean(0), sig, mode="wrap")
    lf_s = lf_s + ndimage.gaussian_filter1d(
        hi[(lat1 < 0) & (lat1 > -p["PLAT_LAT"])].mean(0), sig, mode="wrap")

    # temperature before the dry-land warming (it needs the rain): the
    # convection below reads its months. Continentality: land crossed
    # along the equinox wind, and plain distance to the sea, averaged
    west0 = (np.abs(lat1) < p["PHI_HADLEY"]) | (np.abs(lat1) > p["PHI_POLAR"])
    dland = 0.5 * (land_run(land, dx, west0) + np.clip(inp["dcoast_km"], 0, None))
    cont = np.where(land, 1 - np.exp(-dland / p["L_CONT"]), 0.0)
    A = p["A0"] + p["A1"] * np.sqrt(s2) * (p["A_SEA"] + (1 - p["A_SEA"]) * cont)
    # the sea's current anomaly, carried inland on the equinox wind
    T_anom = np.where(land, carry(sst_anom, land, dx, p["L_MARITIME"], west0), sst_anom)
    T = T0 - p["U_COOL"] * up + T_anom - p["C_COLD"] * cont * s2 - \
        p["LAPSE"] * np.where(land, np.clip(inp["elev_km"], 0, None), 0.0)
    if p["MASS_K"]:
        zb = ndimage.gaussian_filter(np.where(land, np.clip(inp["elev_km"], 0, None), 0.0),
                                     p["L_MASS"] / (RES * 111.2), mode=("nearest", "wrap"))
        # never more than the cell's own height: a lowland beside a
        # plateau is not raised
        T = T + p["MASS_K"] * np.where(land, np.minimum(zb, np.clip(inp["elev_km"], 0, None)), 0.0)

    P, wsum, Pm = np.zeros((NY, NX)), 0.0, {}
    def mse_itcz(Pmon, sun):
        """Latitude (by longitude) where this month's near-surface moist
        static energy peaks in the summer hemisphere, within MSE_LAT of
        the equator: h = T + (g/cp) height + (L/cp) specific humidity (K).
        Humidity: RH_BL over sea; over land the dew point of penman_pet's
        rule (the night minimum, lower in clear dry air), with cloud
        from this month's rain Pmon; pressure falls with height. A soft
        maximum (TAU_MSE), smoothed over LF_SMOOTH of longitude."""
        Tm = T + A * sun * np.sign(LAT)
        z_km = np.where(land, np.clip(inp["elev_km"], 0, None), 0.0)
        c = np.exp(-np.clip(Pmon, 0, None) / p["P_CLOUD"])        # 0 cloudy .. 1 clear
        dtr = p["DTR_CLOUD"] + (p["DTR_CLEAR"] - p["DTR_CLOUD"]) * c
        ea = np.where(land, esat(Tm - dtr / 2 - p["DEW_ARID"] * c),
                      p["RH_BL"] * esat(Tm))
        pres = 101.3 * ((293 - 6.5 * z_km) / 293) ** 5.26          # kPa (FAO-56 eq. 7)
        h = Tm + p["G_CP"] * z_km + p["LV_CP"] * 0.622 * ea / pres
        side = LAT * np.sign(sun)
        ok = (side > 0) & (side < p["MSE_LAT"])
        h = np.where(ok, h, -np.inf)
        wgt = np.exp((h - h.max(0)[None, :]) / p["TAU_MSE"])
        lat_c = (wgt * LAT).sum(0) / wgt.sum(0)
        return ndimage.gaussian_filter1d(lat_c, sig, mode="wrap")


    def month(sun, lf, itcz):
        """One month's rain (and the air's rain potential) with the ITCZ at
        `itcz` (deg, by longitude)."""
        w_itcz = p["W_ITCZ"] + (p["W_ITCZ_LAND"] - p["W_ITCZ"]) * np.clip(lf, 0, 1)
        sh = p["BAND_SHIFT"] * sun * np.sign(lat1)          # poleward in the summer hemisphere
        hadley = p["PHI_HADLEY"] + sh
        west = (np.abs(lat1) < hadley) | (np.abs(lat1) > p["PHI_POLAR"] + sh)
        front = (p["PHI_FRONT"] + sh)[:, None]
        # summer convection over warm land (this month's temperature)
        Tm = T + A * sun * np.sign(LAT)
        conv = p["Z_CONV"] * np.clip((Tm - p["T_CONV"]) / p["DT_CONV"], 0, 1) * land
        z = p["Z_ITCZ"] * np.exp(-((LAT - itcz[None, :]) / w_itcz[None, :]) ** 2) + \
            p["Z_FRONT"] * np.exp(-((phi - front) / p["W_FRONT"]) ** 2) + \
            p["Z_BASE"] + conv
        # the trades blow toward the ITCZ, westerlies toward the pole,
        # polar easterlies toward the equator
        trade = (np.abs(lat1) < hadley)[:, None]
        south = np.where(trade, LAT > itcz[None, :], ((LAT > 0) == west[:, None]))
        # on the high's western flank in summer the flow is poleward
        up_flank = (sun * np.sign(LAT) > 0) & (flank > np.exp(-1)) & trade & \
            (np.abs(LAT) > np.abs(itcz)[None, :])
        south = np.where(up_flank, LAT < 0, south)
        slope = np.where(west[:, None], -dE, dE) / dx[:, None]
        oro = (1 + p["K_ORO"] * np.clip(slope, 0, None)) * \
            np.exp(-p["K_LEE"] * np.clip(-slope, 0, None))
        r_land = np.clip(z * oro * dx[:, None] / p["L_RAIN"], 0, 0.9)
        # the Hadley cell's sinking branch: between the ITCZ and the
        # cell's poleward edge
        g = p["Z_ITCZ"] * np.exp(-((LAT - itcz[None, :]) / w_itcz[None, :]) ** 2)
        edge = np.clip((hadley[:, None] + p["BAND_SHIFT"] - phi) / (2 * p["BAND_SHIFT"]), 0, 1)
        sink = (1 - np.clip(g / p["Z_FRONT"], 0, 1)) * edge * \
            (1 - np.clip(sun * np.sign(LAT), 0, 1) * flank)
        sub = np.minimum(sink * (1 - np.exp(-dx[:, None] / p["L_SUB"])),
                         1 - r_land * keep)
        rate = (r_sea, r_land, keep, sub)
        # rain: the share of the air's potential falling here, as a depth
        # per year over the cell (rain-out per km x L_RAIN keeps it a rate)
        rain = lambda q: np.where(land, q * r_land * p["L_RAIN"] / dx[:, None], q * z)  # noqa: E731
        q, _ = march(q_sat, land, dx, rate, west, south, mer)
        q, _ = march(q_sat, land, dx, rate, west, south, mer, prev=q)
        Pmon = rain(q)
        if sun != 0 and p["MONSOON_W"] > 0:
            # the monsoon westerly: summer-side trade rows walked eastward.
            # Air crossing the equator toward a displaced ITCZ is turned
            # east by the Coriolis force, so between the equator and the
            # ITCZ the wind is westerly, fading over W_ITCZ below the ITCZ
            # (how far the ITCZ has moved already holds land and season)
            summer = np.sign(lat1) == np.sign(sun)
            west_m = west & ~(trade[:, 0] & summer)
            qm, _ = march(q_sat, land, dx, rate, west_m, south, mer)
            qm, _ = march(q_sat, land, dx, rate, west_m, south, mer, prev=qm)
            ramp = np.clip((np.abs(itcz)[None, :] - phi) / w_itcz[None, :], 0, 1) * summer[:, None]
            m = p["MONSOON_W"] * ramp
            Pmon = (1 - m) * Pmon + m * rain(qm)
        return Pmon, q

    for sun, wt in SEASONS:
        lf = lf_n if sun > 0 else lf_s
        itcz = sun * (p["ITCZ_SEA"] + (p["ITCZ_LAND"] - p["ITCZ_SEA"]) * lf)   # (NX,)
        Pmon, q = month(sun, lf, itcz)
        for it in range(p["ITCZ_ITER"] if sun != 0 else 0):
            # the ITCZ where near-surface moist static energy peaks
            itcz = mse_itcz(Pmon, sun)
            Pmon, q = month(sun, lf, itcz)
        Pm[sun] = ndimage.gaussian_filter(Pmon, 1.0, mode=("nearest", "wrap"))
        P += wt * Pmon
        wsum += wt
    P = ndimage.gaussian_filter(P / wsum, 1.0, mode=("nearest", "wrap"))

    w = p["FU_W"]

    def fu(pet):
        ratio = pet / np.maximum(P, 1e-6)
        return P * (1 + ratio - (1 + ratio ** w) ** (1 / w))
    # dry land is warmer: what it does not evaporate it sheds as heat
    pet = penman_pet(T, A, P, LAT, p)[0]
    dry = np.where(land & (pet > 1e-3), 1 - fu(pet) / np.maximum(pet, 1e-3), 0.0)
    T = T + p["T_DRY"] * np.clip(dry, 0, 1)

    gdd = degree_days(T, A, GDD_BASE)
    pet, rh, sun, pet_mon = penman_pet(T, A, P, LAT, p)
    aet_fu = fu(pet)
    # rain seasonality: Fu's curve stands for rain spread through the
    # year; a monthly bucket with the real timing, against one with the
    # same total spread evenly, gives the factor timing makes (rain in
    # the warm season is used, rain in the cold season runs off)
    sgn = np.where(LAT >= 0, 1, -1)
    th = 2 * np.pi * np.arange(12) / 12
    ph = np.round(np.sin(th), 3)
    key = {round(k, 3): k for k in Pm}
    Pmon = np.array([np.where(sgn > 0, Pm[key[s]], Pm[key[-s] if -s != 0 else key[0.0]])
                     for s in ph]) / 12
    Pmon = Pmon * (P / np.maximum(Pmon.sum(0), 1e-9))[None]   # same annual total as P
    a_real = bucket(Pmon, pet_mon, p["S_MAX"])
    a_even = bucket(np.broadcast_to(P / 12, Pmon.shape), pet_mon, p["S_MAX"])
    season = np.where(a_even > 1e-3, a_real / np.maximum(a_even, 1e-3), 1.0)
    aet = np.minimum(aet_fu * season, np.minimum(P, pet))
    runoff = np.clip(P - aet, 0, None)
    arid = P / np.maximum(pet, 1e-3)
    # rain share of the warm half-year (local months with sin > 0)
    warm = Pmon[ph > 0].sum(0) + 0.5 * Pmon[ph == 0].sum(0)
    return dict(temp_c=T, temp_range_c=2 * A, gdd=gdd, precip_m_yr=P,
                pet_m_yr=pet, aet_m_yr=aet, runoff_m_yr=runoff, aridity=arid,
                aridity_season=arid * season, season_factor=season,
                warm_rain_share=warm / np.maximum(P, 1e-9),
                precip_jul=Pm[1.0], precip_jan=Pm[-1.0],
                rel_humidity=rh, sunshine=sun, sst_anomaly_c=T_anom,
                continentality=cont)


def biome_rule(f, rule=BIOME_RULE):
    """Biome index (BIOMES) a cell's climate implies."""
    T, A, ai = f["temp_c"], f["temp_range_c"] / 2, f["aridity_season"]
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


def calibrate(inp, area, p=PARAMS):
    """p with P0 set so that area-weighted precipitation over the whole
    globe (land and sea) is P_GLOBAL; precipitation scales with P0, so
    one rescaling is exact."""
    f = fields(inp, p)
    mean = (f["precip_m_yr"] * area).sum() / area.sum()
    return dict(p, P0=p["P0"] * P_GLOBAL / mean)


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
            ("aridity", "aridity index P/PET", "BrBG", (0, 2)),
            ("rel_humidity", "relative humidity, annual mean", "BuGn", (0, 1)),
            ("sunshine", "sunshine fraction", "YlOrRd", (0, 1)),
            ("sst_anomaly_c", "ocean-current temperature anomaly, sea and carried inland (degC)", "RdBu_r", (-4, 4)),
            ("aridity_season", "aridity with the rain's timing (biomes use it)", "BrBG", (0, 2)),
            ("season_factor", "water use, real rain timing / even rain (monthly bucket)", "PiYG", (0.5, 1.5)),
            ("warm_rain_share", "share of rain in the warm half-year", "RdBu", (0, 1)),
            ("precip_jul", "precipitation rate in July, northern summer (m/yr)", "Blues", (0, 4)),
            ("precip_jan", "precipitation rate in January, southern summer (m/yr)", "Blues", (0, 4))]
    for k, title, cmap, lim in spec:
        v = f[k] if k in ("sst_anomaly_c", "precip_jul", "precip_jan") \
            else np.where(land, f[k], np.nan)
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


def build(df, verbose=True):
    """Calibrate P0, compute the fields, write the QA figures and the
    record (parameters, biome areas, agreement with the drawn map).
    Returns (fields, climate biome, params, record)."""
    inp, drawn, area = inputs_from_cells(df)
    land = inp["land"]
    path = os.path.join(QA_DIR, "climate_fit.json")
    p = calibrate(inp, area)
    f = fields(inp, p)
    pred = biome_rule(f)
    rec, mean_rec, overall = agreement(pred, drawn, land, area)
    conf = confusion(pred, drawn, land, area)
    record = dict(params={k: float(f"{v:.4g}") for k, v in p.items()},
                  calibrated=["P0"], rule=BIOME_RULE,
                  land_precip_m_yr=round(float((f["precip_m_yr"] * area)[land].sum()
                                               / area[land].sum()), 3),
                  biome_area_mkm2={b: round(float(area[land & (pred == k)].sum()) / 1e6, 1)
                                   for k, b in enumerate(BIOMES)},
                  recall_by_biome={k: round(v, 3) for k, v in rec.items()},
                  mean_recall=round(mean_rec, 3), overall=round(overall, 3),
                  confusion=conf.round(3).to_dict(orient="records"))
    os.makedirs(QA_DIR, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(record, fh, indent=1)
    qa_figures(f, drawn, pred, land)
    if verbose:
        print("climate: P0", round(p["P0"], 3), "land P", record["land_precip_m_yr"],
              "biome areas", record["biome_area_mkm2"])
        print("climate: agreement by drawn biome", record["recall_by_biome"],
              "mean", record["mean_recall"], "overall", record["overall"])
        print(conf.round(3).to_string(index=False))
    return f, pred, p, record


if __name__ == "__main__":
    import geopandas as gpd
    cells = gpd.read_file(os.path.join(HERE, "gis", "world.gpkg"),
                          layer="cells", ignore_geometry=True)
    build(cells)
