"""
Earth climate check (WP9 stage C, step C of docs/earth-test-plan.md; U,
2026-11-20: "do the climate check"): run climate_world.py, unchanged, on
Earth's land and elevation, and compare its fields and biomes with
Earth's observed climate.

Inputs (gis/earth/worldclim/, not in git; WorldClim 2.1, Fick and
Hijmans 2017, 10 arc-minute monthly 1970-2000 normals, free for
non-commercial use): elevation, mean / minimum / maximum temperature,
precipitation, solar radiation, vapour pressure and wind. Each is averaged
over the 3 x 3 pixels of a 0.5 degree cell; a cell is land where at least
half its pixels have data.

The model (all C):
  - climate_world.fields() with PARAMS as they stand; P0 by the model's
    own rule (global mean precipitation 1.0 m/yr), not fitted to Earth;
  - no coastal upwelling input (the fantasy world's comes from its paleo
    ocean model; Earth has none here), so cold eastern-boundary coasts
    come only from the gyre rule.

The observed side goes through the same definitions:
  - T is the mean of the monthly means;
  - A, the seasonal half-amplitude, is half the warmest month less the
    coldest;
  - PET is FAO-56 Penman-Monteith from the observed months (radiation,
    vapour pressure, wind at 2 m, the elevation's psychrometric
    constant), with months under 0 degC counted as 0, as in the model;
  - the timing factor uses the same monthly bucket (S_MAX) and the
    observed monthly rain;
  - the biome comes from the same BIOME_RULE.
So the check is of the climate model: the same rule turns both climates
into biomes. Whether the rule matches Earth's vegetation is a separate
question, not asked here.

Nothing is tuned to the result; the parameters are not changed by it.

Run:  ~/.venvs/worldsim/bin/python earth_climate.py [--tag fix1]
      (writes gis/qa/earth_climate_*.png and gis/qa/earth_climate.json;
      with --tag, earth_climate_<tag>_*.png and earth_climate_<tag>.json,
      so the first check's record is kept)

After the fixes of 2026-11-21 (U), the check is spent for the climate
model: a rerun shows whether the fixes worked, not that it is right.
"""
import json
import os

import numpy as np

import climate_world as cw

HERE = os.path.dirname(os.path.abspath(__file__))
WC = os.path.join(HERE, "gis", "earth", "worldclim")
QA = cw.QA_DIR
TAG = ""
NY, NX, RES = cw.NY, cw.NX, cw.RES

# named regions for the table: (name, lat lo, lat hi, lon lo, lon hi)
REGIONS = [
    ("Sahara", 18, 30, -10, 30),
    ("Arabia", 17, 30, 40, 55),
    ("Amazon", -10, 2, -70, -50),
    ("Congo basin", -5, 4, 12, 28),
    ("India (monsoon)", 15, 28, 72, 88),
    ("Southeast Asia", 10, 22, 95, 108),
    ("Western Europe", 45, 55, -5, 15),
    ("Siberia (boreal)", 55, 65, 60, 120),
    ("Central Asia", 38, 48, 55, 75),
    ("Eastern US", 33, 42, -90, -77),
    ("US Southwest", 31, 38, -117, -106),
    ("Atacama", -28, -18, -71, -69),
    ("Interior Australia", -30, -20, 120, 145),
    ("Sahel", 11, 16, -15, 30),
    ("East China", 25, 40, 105, 122),
    ("Mediterranean", 36, 44, -8, 28),
]


def read(var, month=None):
    """A WorldClim layer averaged to the 0.5 degree grid, and the share
    of each cell's pixels with data."""
    import rasterio
    name = f"wc2.1_10m_{var}" + (f"_{month:02d}" if month else "") + ".tif"
    with rasterio.open(os.path.join(WC, var, name)) as r:
        a = r.read(1).astype(float)
        a[a == r.nodata] = np.nan
        a[a < -1e30] = np.nan
    b = a.reshape(NY, 3, NX, 3)
    ok = np.isfinite(b).sum((1, 3))
    with np.errstate(invalid="ignore"):
        return np.nansum(b, (1, 3)) / np.maximum(ok, 1), ok / 9.0


def coast_km(land):
    """Great-circle km from each cell to the nearest sea cell (0 at sea)."""
    from scipy.spatial import cKDTree
    lat = np.radians(cw.lat_grid())
    lon = np.radians(-180 + RES * (np.arange(NX) + 0.5))[None, :] * np.ones((NY, 1))
    xyz = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    d = cKDTree(xyz[~land]).query(xyz[land])[0]
    out = np.zeros((NY, NX))
    out[land] = 2 * np.arcsin(np.clip(d / 2, 0, 1)) * 6371.0
    return out


def observed(land, elev_km):
    """Observed climate on the grid, in the model's definitions."""
    m = {v: np.array([read(v, k)[0] for k in range(1, 13)])
         for v in ("tavg", "tmin", "tmax", "prec", "srad", "vapr", "wind")}
    T = m["tavg"].mean(0)
    A = (m["tavg"].max(0) - m["tavg"].min(0)) / 2
    Pmon = m["prec"] / 1000.0
    P = Pmon.sum(0)
    # FAO-56 Penman-Monteith, month by month (eqs. 6-8, 11-13, 21-25, 39, 47)
    phi = np.radians(cw.lat_grid())
    z = np.clip(np.nan_to_num(elev_km), 0, None) * 1000.0
    gam = 0.665e-3 * 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26
    u2 = m["wind"] * 4.87 / np.log(67.8 * 10 - 5.42)
    days = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    mid = np.cumsum(days) - days / 2
    PETm = []
    for k in range(12):
        J = mid[k]
        dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
        dec = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
        ws = np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1, 1))
        Ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(dec) +
                                              np.cos(phi) * np.cos(dec) * np.sin(ws))
        Rs = m["srad"][k] / 1000.0                     # kJ -> MJ m-2 day-1
        Rso = np.maximum((0.75 + 2e-5 * z) * Ra, 1e-6)
        tx, tn, Tm = m["tmax"][k], m["tmin"][k], m["tavg"][k]
        es = (cw.esat(tx) + cw.esat(tn)) / 2
        ea = np.minimum(m["vapr"][k], es)
        D = 4098 * cw.esat(Tm) / (Tm + 237.3) ** 2
        Rnl = 4.903e-9 * ((tx + 273.16) ** 4 + (tn + 273.16) ** 4) / 2 * \
            (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * np.clip(Rs / Rso, 0, 1) - 0.35)
        Rn = (1 - 0.23) * Rs - Rnl
        et = (0.408 * D * Rn + gam * 900 / (Tm + 273) * u2[k] * (es - ea)) / \
            (D + gam * (1 + 0.34 * u2[k]))
        PETm.append(np.where(Tm > 0, np.clip(et, 0, None), 0.0) * days[k] / 1000.0)
    PETm = np.array(PETm)
    PET = PETm.sum(0)
    good = land & np.isfinite(T) & np.isfinite(P) & np.isfinite(PET)
    s = cw.PARAMS["S_MAX"]
    Pf, Ef = np.nan_to_num(Pmon), np.nan_to_num(PETm)
    a_real = cw.bucket(Pf, Ef, s)
    a_even = cw.bucket(np.broadcast_to(Pf.sum(0) / 12, Pf.shape), Ef, s)
    season = np.where(a_even > 1e-3, a_real / np.maximum(a_even, 1e-3), 1.0)
    arid = P / np.maximum(PET, 1e-3)
    # warm half-year by the sun's phase, as the model defines it:
    # Apr-Aug and half of Mar and Sep in the north, Oct-Feb and half of
    # Sep and Mar in the south
    w_n = np.array([0, 0, .5, 1, 1, 1, 1, 1, .5, 0, 0, 0])
    w = np.where(cw.lat_grid() >= 0, 1, 0)[None] * w_n[:, None, None] + \
        np.where(cw.lat_grid() < 0, 1, 0)[None] * (1 - w_n)[:, None, None]
    warm = (Pf * w).sum(0) / np.maximum(P, 1e-9)
    return dict(temp_c=T, temp_range_c=2 * A, gdd=cw.degree_days(T, A, cw.GDD_BASE),
                precip_m_yr=P, pet_m_yr=PET, aridity=arid,
                aridity_season=arid * season, season_factor=season,
                warm_rain_share=warm, precip_jul=Pmon[6] * 12,
                precip_jan=Pmon[0] * 12), good


def stats(a, b, w):
    """Area-weighted bias (a - b), RMSE and correlation."""
    ok = np.isfinite(a) & np.isfinite(b)
    a, b, w = a[ok], b[ok], w[ok]
    w = w / w.sum()
    ma, mb = (w * a).sum(), (w * b).sum()
    cov = (w * (a - ma) * (b - mb)).sum()
    r = cov / np.sqrt((w * (a - ma) ** 2).sum() * (w * (b - mb) ** 2).sum())
    return dict(model=round(float(ma), 3), observed=round(float(mb), 3),
                bias=round(float(ma - mb), 3),
                rmse=round(float(np.sqrt((w * (a - b) ** 2).sum())), 3),
                r=round(float(r), 3))


def box(name, la0, la1, lo0, lo1):
    lat = cw.lat_grid()
    lon = -180 + RES * (np.arange(NX) + 0.5)
    return (lat >= la0) & (lat <= la1) & (lon[None, :] >= lo0) & (lon[None, :] <= lo1)


def figures(f, o, pm, po, good, land):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, TwoSlopeNorm
    from matplotlib.patches import Patch
    ext = (-180, 180, -90, 90)
    sea = np.array([205, 220, 235], np.uint8)

    def rgb(cls, mask):
        img = np.broadcast_to(sea, (NY, NX, 3)).copy()
        img[mask] = cw.BIOME_RGB[cls[mask]]
        img[land & ~mask] = (160, 160, 160)
        return img

    fig, ax = plt.subplots(2, 1, figsize=(11, 11))
    for a, cls, t in ((ax[0], pm, "Model: climate_world.py on Earth's land and elevation"),
                      (ax[1], po, "Observed climate (WorldClim 2.1) through the same biome rule")):
        a.imshow(rgb(cls, good), extent=ext, interpolation="nearest")
        a.set_title(t, loc="left", fontsize=11)
        a.set_xticks(range(-180, 181, 60))
        a.set_yticks(range(-90, 91, 30))
        a.tick_params(labelsize=8, colors="#555")
    ax[1].legend(handles=[Patch(color=cw.BIOME_RGB[k] / 255, label=b)
                          for k, b in enumerate(cw.BIOMES)],
                 loc="lower left", fontsize=8, frameon=True)
    fig.tight_layout()
    fig.savefig(os.path.join(QA, f"earth_climate{TAG}_biomes.png"), dpi=110)
    plt.close(fig)

    # fields: model, observed, difference
    rows = [("Annual mean temperature (degC)", "temp_c", "RdYlBu_r", (-30, 30), "diff", 10),
            ("Precipitation (m/yr)", "precip_m_yr", "YlGnBu", (0, 3), "ratio", None),
            ("Aridity with rain timing (P/PET x timing)", "aridity_season", "BrBG", (0, 1.5), "ratio", None)]
    fig, ax = plt.subplots(3, 3, figsize=(16, 9.5))
    for i, (t, k, cm, (lo, hi), kind, dmax) in enumerate(rows):
        a, b = np.where(good, f[k], np.nan), np.where(good, o[k], np.nan)
        for j, (v, sub) in enumerate(((a, "model"), (b, "observed"))):
            im = ax[i, j].imshow(v, extent=ext, cmap=cm, vmin=lo, vmax=hi, interpolation="nearest")
            ax[i, j].set_title(f"{t}: {sub}", loc="left", fontsize=9)
            fig.colorbar(im, ax=ax[i, j], shrink=0.7)
        if kind == "diff":
            d, lab, nrm = a - b, "model - observed", TwoSlopeNorm(0, -dmax, dmax)
            cmd = "RdBu_r"
        else:
            d = np.log2(np.maximum(a, 1e-3) / np.maximum(b, 1e-3))
            lab, nrm, cmd = "log2(model / observed)", TwoSlopeNorm(0, -2, 2), "BrBG"
        im = ax[i, 2].imshow(d, extent=ext, cmap=cmd, norm=nrm, interpolation="nearest")
        ax[i, 2].set_title(f"{t}: {lab}", loc="left", fontsize=9)
        fig.colorbar(im, ax=ax[i, 2], shrink=0.7)
    for a in ax.ravel():
        a.set_facecolor("#dde6ee")
        a.tick_params(labelsize=7, colors="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(QA, f"earth_climate{TAG}_fields.png"), dpi=100)
    plt.close(fig)

    # zonal means over land
    lat = cw.lat_grid()[:, 0]
    area = np.cos(np.radians(cw.lat_grid()))
    fig, ax = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    for a, (t, k, scale) in zip(ax, (("Temperature (degC)", "temp_c", 1),
                                     ("Precipitation (m/yr)", "precip_m_yr", 1),
                                     ("Warm half-year's share of rain", "warm_rain_share", 1))):
        for src, col, lab in ((f, "#2a6fbb", "model"), (o, "#c0582b", "observed")):
            v = np.where(good, src[k], np.nan)
            with np.errstate(invalid="ignore"):
                z = np.nansum(v * area, 1) / np.nansum(np.where(np.isfinite(v), area, 0), 1)
            z[good.sum(1) < 5] = np.nan
            a.plot(z * scale, lat, color=col, lw=2, label=lab)
        a.set_title(t, loc="left", fontsize=10)
        a.grid(color="#e5e5e5", lw=0.8)
        a.tick_params(labelsize=8, colors="#555")
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    ax[0].set_ylabel("latitude")
    ax[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Land zonal means, Earth", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(QA, f"earth_climate{TAG}_zonal.png"), dpi=100)
    plt.close(fig)

    # monsoon: July and January rain
    fig, ax = plt.subplots(2, 2, figsize=(14, 7.5))
    for i, k in enumerate(("precip_jul", "precip_jan")):
        for j, (src, sub) in enumerate(((f, "model"), (o, "observed"))):
            v = np.where(good, src[k], np.nan)
            im = ax[i, j].imshow(v, extent=ext, cmap="YlGnBu", vmin=0, vmax=4, interpolation="nearest")
            ax[i, j].set_title(f"{'July' if i == 0 else 'January'} rain, m/yr rate: {sub}",
                               loc="left", fontsize=9)
            ax[i, j].set_facecolor("#dde6ee")
            ax[i, j].tick_params(labelsize=7, colors="#555")
            fig.colorbar(im, ax=ax[i, j], shrink=0.7)
    fig.tight_layout()
    fig.savefig(os.path.join(QA, f"earth_climate{TAG}_monsoon.png"), dpi=100)
    plt.close(fig)


def main():
    elev, frac = read("elev")
    land = frac >= 0.5
    elev_km = np.where(land, np.nan_to_num(elev) / 1000.0, 0.0)
    inp = dict(land=land, elev_km=elev_km, dcoast_km=coast_km(land),
               upwelling=np.zeros((NY, NX)))
    lat = cw.lat_grid()
    area = (RES * 111.2) ** 2 * np.cos(np.radians(lat))
    p = cw.calibrate(inp, area)
    f = cw.fields(inp, p)
    o, good = observed(land, elev_km)
    pm, po = cw.biome_rule(f), cw.biome_rule(o)
    w = np.where(good, area, 0.0)
    rec, mean_rec, overall = cw.agreement(pm, np.where(good, po, -1), good, area)
    conf = cw.confusion(pm, np.where(good, po, -1), good, area)
    conf = conf.rename(columns={"drawn": "observed"})
    fields = {k: stats(f[k][good], o[k][good], w[good])
              for k in ("temp_c", "temp_range_c", "gdd", "precip_m_yr", "pet_m_yr",
                        "aridity_season", "season_factor", "warm_rain_share")}
    for k in ("precip_m_yr", "aridity_season"):
        fields[k + " (log10)"] = stats(np.log10(np.maximum(f[k][good], 1e-3)),
                                       np.log10(np.maximum(o[k][good], 1e-3)), w[good])
    regions = []
    for name, *b in REGIONS:
        m = box(name, *b) & good
        a = area[m]

        def mean(x):
            return float((x[m] * a).sum() / a.sum())

        def share(cls):
            return {cw.BIOMES[k]: round(float(a[cls[m] == k].sum() / a.sum()), 2)
                    for k in range(5) if a[cls[m] == k].sum() / a.sum() >= 0.05}
        regions.append(dict(
            region=name, cells=int(m.sum()),
            T_model=round(mean(f["temp_c"]), 1), T_obs=round(mean(o["temp_c"]), 1),
            P_model=round(mean(f["precip_m_yr"]), 2), P_obs=round(mean(o["precip_m_yr"]), 2),
            jul_jan_model=round(mean(f["precip_jul"]) / max(mean(f["precip_jan"]), 1e-3), 2),
            jul_jan_obs=round(mean(o["precip_jul"]) / max(mean(o["precip_jan"]), 1e-3), 2),
            biome_model=share(pm), biome_obs=share(po)))
    record = dict(
        source="WorldClim 2.1, 10 arc-minute, 1970-2000; averaged to 0.5 degrees",
        P0_earth=round(float(p["P0"]), 3),
        land_cells=int(good.sum()),
        biome_area_mkm2={sub: {b: round(float(area[good & (cls == k)].sum()) / 1e6, 1)
                               for k, b in enumerate(cw.BIOMES)}
                         for sub, cls in (("model", pm), ("observed", po))},
        recall_by_observed_biome={k: round(v, 3) for k, v in rec.items()},
        mean_recall=round(mean_rec, 3), overall=round(overall, 3),
        confusion=conf.round(3).to_dict(orient="records"),
        fields=fields, regions=regions)
    with open(os.path.join(QA, f"earth_climate{TAG}.json"), "w") as fh:
        json.dump(record, fh, indent=1)
    figures(f, o, pm, po, good, land)
    print(json.dumps({k: v for k, v in record.items() if k != "confusion"}, indent=1))
    print(conf.round(2).to_string(index=False))


if __name__ == "__main__":
    import sys
    if "--tag" in sys.argv:
        TAG = "_" + sys.argv[sys.argv.index("--tag") + 1]
    main()
