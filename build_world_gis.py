"""
Build a single GeoPackage (world.gpkg) from the world maps in this folder:
the published paleogeography (topography.jpg, oceanography.jpg), the fictional
world redrawn from it (biomes, soil, ore), and fields that carry the paleo data
onto the fiction or compare the two -- one row per grid cell, all together.

All maps are Robinson-projection images. Each is registered by fitting the
projection to its drawn graticule/outline, then resampled onto a regular
lat/lon grid so every layer shares one cell lattice.

Sources
  ore.jpeg          elevation/bathymetry base (colorbar -4..2 km) + ore markers
  soil.jpeg         soil class (12-band colorbar) + rivers
  biomes.jpeg       biome class (6 classes)
  topography.jpg    original GCM topography (24 bands, 0.25 km)
  oceanography.jpg  5 ocean-model panels (productivity, PO4, PAR, upwelling, O2)

Outputs (in OUT_DIR)
  world.gpkg        cells: one row per grid cell with every field, prefixed
                      paleo_ (reconstruction, its own coastline), fic_ (the
                      fictional world), syn_ (paleo carried onto / compared
                      with the fiction); see the field_dictionary table
                    ore_deposits (points), rivers (routed), rivers_drawn
                    (traced from soil.jpeg), landmass /
                    biome_regions / soil_regions (polygons), legend_* tables
  previews/         one PNG per field, for looking without GIS software
  qa/               overlays for checking registration and extraction

Requires: numpy scipy pillow opencv-python-headless rasterio geopandas
          shapely pyogrio scikit-image
Run:  python build_world_gis.py
"""
import json
import os
import sqlite3

import cv2
import geopandas as gpd
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from rasterio.features import shapes
from rasterio.transform import from_origin
from scipy import ndimage, optimize
from scipy.spatial import cKDTree
from shapely.geometry import LineString, box, shape
from skimage.morphology import skeletonize

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "gis")
RES = 0.5            # grid cell size, degrees
SUPER = 4            # sub-samples per cell edge when reading the images
CRS = "EPSG:4326"    # paleo-latitude/longitude; not modern Earth coordinates
R_EARTH = 6371.0
SHELF_KM = 250.0     # radius for the syn_reach_* fields (offshore reach of a cell)

# --------------------------------------------------------------------------
# Robinson projection
# --------------------------------------------------------------------------
_LAT = np.arange(0, 91, 5)
_RX = np.array([1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427,
                0.9216, 0.8962, 0.8679, 0.8350, 0.7986, 0.7597, 0.7186, 0.6732,
                0.6213, 0.5722, 0.5322])
_RY = np.array([0.0000, 0.0620, 0.1240, 0.1860, 0.2480, 0.3100, 0.3720, 0.4340,
                0.4958, 0.5571, 0.6176, 0.6769, 0.7346, 0.7903, 0.8435, 0.8936,
                0.9394, 0.9761, 1.0000])


def robinson(lon, lat):
    a = np.abs(lat)
    x = 0.8487 * np.interp(a, _LAT, _RX) * np.radians(lon)
    y = 1.3523 * np.interp(a, _LAT, _RY) * np.sign(lat)
    return x, y


def to_pixel(p, lon, lat):
    """p = (cx, cy, sx, sy): pixel centre of the map and scale per Robinson unit."""
    cx, cy, sx, sy = p
    x, y = robinson(lon, lat)
    return cx + sx * x, cy - sy * y


def fit_projection(img, p0, masks=(), free=(0, 1, 2, 3)):
    """Fit (cx, cy, sx, sy) so the outline, equator, +-30/60 parallels and
    the central meridian fall on dark pixels. Separate sx/sy because the
    AI-redrawn maps are not uniformly scaled."""
    dark = (img.astype(float).sum(2) < 200).astype(float)
    for x0, y0, x1, y1 in masks:
        dark[y0:y1, x0:x1] = 0
    D = ndimage.gaussian_filter(dark, 1.2)
    n = 400
    t, s = np.linspace(-90, 90, n), np.linspace(-180, 180, n)
    lon = np.concatenate([np.full(n, -180), np.full(n, 180), np.zeros(n)]
                         + [s] * 7)
    lat = np.concatenate([t, t, t] + [np.full(n, v) for v in (-90, -60, -30, 0, 30, 60, 90)])

    def obj(p):
        x, y = to_pixel(p, lon, lat)
        return -ndimage.map_coordinates(D, [y, x], order=1).mean()

    p = np.array(p0, float)
    free = list(free)

    def obj_free(q):
        pp = p.copy()
        pp[free] = q
        return obj(pp)

    for _ in range(3):
        if len(free) == 1:  # Nelder-Mead is unreliable in 1-D; scan then refine
            grid = p[free[0]] + np.arange(-15, 15.5, 0.5)
            p[free[0]] = grid[np.argmin([obj_free([g]) for g in grid])]
            break
        p[free] = optimize.minimize(obj_free, p[free], method="Nelder-Mead",
                                    options={"xatol": 0.05, "fatol": 1e-6, "maxiter": 4000}).x
    return p, -obj(p)


# --------------------------------------------------------------------------
# Grid
# --------------------------------------------------------------------------
NX, NY = int(360 / RES), int(180 / RES)
LONS = -180 + RES * (np.arange(NX) + 0.5)
LATS = 90 - RES * (np.arange(NY) + 0.5)
TRANSFORM = from_origin(-180, 90, RES, RES)


def subsample_coords():
    off = (np.arange(SUPER) + 0.5) / SUPER * RES - RES / 2
    lon = LONS[None, :, None, None] + off[None, None, None, :]
    lat = LATS[:, None, None, None] - off[None, None, :, None]
    lon, lat = np.broadcast_arrays(lon, lat)
    return lon, lat  # (NY, NX, SUPER, SUPER)


def sample_continuous(field, p):
    """field: float image with NaN = no data. Returns grid mean of valid subsamples."""
    lon, lat = subsample_coords()
    x, y = to_pixel(p, lon, lat)
    xi = np.clip(np.round(x).astype(int), 0, field.shape[1] - 1)
    yi = np.clip(np.round(y).astype(int), 0, field.shape[0] - 1)
    v = field[yi, xi].reshape(NY, NX, -1)
    with np.errstate(all="ignore"):
        return np.nanmean(v, axis=2)


def sample_categorical(field, p, n_classes):
    """field: int image, 0 = no data. Returns grid majority class (0 if none)."""
    lon, lat = subsample_coords()
    x, y = to_pixel(p, lon, lat)
    xi = np.clip(np.round(x).astype(int), 0, field.shape[1] - 1)
    yi = np.clip(np.round(y).astype(int), 0, field.shape[0] - 1)
    v = field[yi, xi].reshape(NY, NX, -1)
    counts = np.stack([(v == k).sum(2) for k in range(1, n_classes + 1)], axis=2)
    out = counts.argmax(2) + 1
    out[counts.max(2) == 0] = 0
    return out


def pixel_to_lonlat(p, px, py):
    """Invert to_pixel by table interpolation (Robinson has no closed-form inverse)."""
    cx, cy, sx, sy = p
    y = (cy - np.asarray(py, float)) / sy
    a = np.interp(np.abs(y) / 1.3523, _RY, _LAT) * np.sign(y)
    X = np.interp(np.abs(a), _LAT, _RX)
    lon = np.degrees((np.asarray(px, float) - cx) / sx / (0.8487 * X))
    return lon, a


# --------------------------------------------------------------------------
# Pixel-level helpers
# --------------------------------------------------------------------------
def load(name):
    return np.asarray(Image.open(os.path.join(HERE, name)).convert("RGB"))


def colorbar(img, x0, x1, y_top, y_bot, v_top, v_bot, n_bands=None):
    """Sample a vertical colorbar -> (colors[N,3], values[N]).
    n_bands: sample band centres of a discrete bar; else every pixel row."""
    col = np.median(img[:, x0:x1].astype(float), axis=1)
    if n_bands:
        h = (y_bot - y_top) / n_bands
        ys = (y_top + h * (np.arange(n_bands) + 0.5)).astype(int)
        cols = np.array([np.median(col[y - int(h / 4):y + int(h / 4) + 1], axis=0) for y in ys])
    else:
        ys = np.arange(y_top + 2, y_bot - 1)
        cols = col[ys]
    vals = v_top + (ys - y_top) / (y_bot - y_top) * (v_bot - v_top)
    return cols, vals


def nearest_color(img, cols, max_dist=None):
    """Index of the nearest colour for each pixel; -1 where farther than max_dist."""
    flat = img.reshape(-1, 3).astype(np.float32)
    tree = cKDTree(np.asarray(cols, np.float32))
    d, i = tree.query(flat, workers=-1)
    if max_dist is not None:
        i[d > max_dist] = -1
    return i.reshape(img.shape[:2]), d.reshape(img.shape[:2])


def thin_dark_lines(img, k=5, thresh=45):
    """Graticule, outlines, text strokes: pixels much darker than their surroundings."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT,
                          cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    return bh > thresh


def fill_nearest(arr, invalid):
    """Replace invalid pixels with the nearest valid pixel's value."""
    if not invalid.any():
        return arr
    idx = ndimage.distance_transform_edt(invalid, return_distances=False, return_indices=True)
    return arr[tuple(idx)]


def inside_map(shape_hw, p, pad=3):
    """Boolean mask of pixels inside the projected globe."""
    lat = np.linspace(-90, 90, 361)
    xl, yl = to_pixel(p, np.full_like(lat, -180), lat)
    xr, yr = to_pixel(p, np.full_like(lat, 180), lat)
    poly = np.concatenate([np.c_[xl, yl], np.c_[xr, yr][::-1]])
    m = np.zeros(shape_hw, np.uint8)
    cv2.fillPoly(m, [np.round(poly).astype(np.int32)], 1)
    return cv2.erode(m, np.ones((2 * pad + 1, 2 * pad + 1), np.uint8)).astype(bool)


def blueish(img):
    r, g, b = [img[..., i].astype(int) for i in range(3)]
    return (b > r + 15) & (b >= g - 10)


# --------------------------------------------------------------------------
# Per-source extraction
# --------------------------------------------------------------------------
QA = {}


def classify_marker(comp):
    """Square / triangle / circle from the row-width profile of a marker's
    interior (~7-10 px tall; JPEG blunts the triangle apex). Squares have
    near-constant width, triangles are widest near the base, circles are
    widest mid-height."""
    widths = comp.sum(1).astype(float)
    widths = widths[widths > 0]
    n = len(widths)
    if n < 3:
        return "circle"
    rel = widths / widths.max()
    widest = np.argmax(widths) / (n - 1)
    core = rel[int(0.15 * n):max(int(0.85 * n), int(0.15 * n) + 1)]
    top = rel[1]  # first row is often a partial anti-aliased edge
    if top > 0.8 and core.min() > 0.8:
        return "square"
    if (widest >= 0.6 and top < 0.65) or top < 0.45:
        return "triangle"
    return "circle"


def extract_ore_map():
    img = load("ore.jpeg")
    p, score = fit_projection(img, [681, 341, 240, 240], masks=[(1350, 0, 1505, 688)])
    QA["ore.jpeg"] = dict(params=p.round(2).tolist(), fit=round(score, 3))
    r, g, b = [img[..., i].astype(int) for i in range(3)]

    # ---- markers ----
    red = (r > 180) & (g < 120) & (b < 120)
    pur = (b > r) & (r > 70) & (g < 90) & (b > 100) & (b - g > 50)
    inside = inside_map(img.shape[:2], p)
    deposits = []
    for depth, m in (("surface", red), ("deep", pur)):
        m = m & inside
        n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        for k in range(1, n):
            x, y, w, h, area = st[k]
            if area < 15:
                continue  # fragments of occluded markers / JPEG noise
            comp = lab[y:y + h, x:x + w] == k
            shape_ = classify_marker(comp)
            # partial (occluded) markers get lower confidence
            conf = "high" if area >= 40 else "low"
            lon, lat = pixel_to_lonlat(p, cen[k][0], cen[k][1])
            deposits.append(dict(depth=depth, shape=shape_, px=float(cen[k][0]),
                                 py=float(cen[k][1]), lon=float(lon), lat=float(lat),
                                 marker_px=int(area), confidence=conf))
    metal = {"triangle": "iron", "square": "tin", "circle": "copper"}
    for d in deposits:
        d["metal"] = d["read_metal"] = metal[d["shape"]]
        d["ore_type"] = f"{d['depth']}_{d['metal']}"

    # ---- elevation base ----
    cols, vals = colorbar(img, 1366, 1383, 49, 667, 2.0, -4.0)
    marker_zone = cv2.dilate((red | pur).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    bad = marker_zone | thin_dark_lines(img, k=5, thresh=25) | ~inside
    # land = the AI map's own green/tan; sea = blue or pale-blue shelf
    sea = blueish(img) | ((img.astype(int).sum(2) > 690) & (b >= r))
    sea_val = vals < 0
    i_land, d_land = nearest_color(img, cols[~sea_val])
    i_sea, d_sea = nearest_color(img, cols[sea_val])
    elev = np.where(sea, vals[sea_val][i_sea], vals[~sea_val][i_land]).astype(np.float32)
    # the shelf is painted near-white, which the bar would read as +2 km
    shelf = sea & (img.astype(int).sum(2) > 650)
    elev[shelf] = -0.1
    elev = fill_nearest(elev, bad)
    land = fill_nearest(~sea, bad)
    elev[~inside] = np.nan
    return dict(p=p, img=img, elev=elev, land=land, inside=inside, deposits=deposits)


def sea_ghosts(img, sea):
    """Grey marker-shaped blobs drawn offshore on the soil map: small
    non-sea components fully surrounded by sea."""
    n, lab, st, _ = cv2.connectedComponentsWithStats((~sea).astype(np.uint8), 8)
    small = np.zeros(n, bool)
    small[1:] = st[1:, 4] < 150
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    return small[lab] & (hsv[..., 1] < 50)


SOIL_CLASSES = 12  # bands of the soil colorbar, top (value 2) to bottom (value -4)


def extract_soil_map():
    img = load("soil.jpeg")
    p, score = fit_projection(img, [688, 341, 243, 243], masks=[(1360, 0, 1505, 688)])
    QA["soil.jpeg"] = dict(params=p.round(2).tolist(), fit=round(score, 3))
    cols, vals = colorbar(img, 1380, 1398, 45, 672, 2.0, -4.0, n_bands=SOIL_CLASSES)
    r, g, b = [img[..., i].astype(int) for i in range(3)]
    inside = inside_map(img.shape[:2], p)

    lines = thin_dark_lines(img, k=7, thresh=30)
    s = img.astype(int).sum(2)
    sea = blueish(img) | ((s > 650) & (b >= r))  # pale shelf is near-white
    sea = cv2.morphologyEx(sea.astype(np.uint8), cv2.MORPH_OPEN,
                           np.ones((5, 5), np.uint8)).astype(bool)

    # Rivers are drawn in the same near-black as the graticule, so the
    # graticule is located first: parallels are rows that are dark across
    # the sea; meridians are fitted from their sea segments as
    # x = a + k * X(lat) and extrapolated across land.
    H, W = s.shape
    grat = np.zeros((H, W), bool)
    rowfrac = (lines & sea).sum(1) / np.maximum(sea.sum(1), 1)
    for y in np.where(rowfrac > 0.3)[0]:
        grat[max(0, y - 2):y + 3] = True

    def Xof(y):
        return np.interp(np.abs((p[1] - y) / p[3] / 1.3523), _RY, _RX)

    n, lab, st, _ = cv2.connectedComponentsWithStats((lines & sea & ~grat).astype(np.uint8), 8)
    yy = np.arange(H)
    for k in range(1, n):
        x, y, w, h, _ = st[k]
        if h < 35 or w > 0.8 * h:
            continue
        ys, xs = np.nonzero(lab[y:y + h, x:x + w] == k)
        ys, xs = ys + y, xs + x
        A = np.c_[np.ones_like(ys), Xof(ys)]
        c = np.linalg.lstsq(A, xs, rcond=None)[0]
        if np.sqrt(np.mean((A @ c - xs) ** 2)) >= 2.0:
            continue
        xx = np.round(c[0] + c[1] * Xof(yy)).astype(int)
        for dx in range(-3, 4):
            ok = (xx + dx >= 0) & (xx + dx < W)
            grat[yy[ok], xx[ok] + dx] = True
    # river strokes are darker than soil-polygon outlines (or blue-tinted);
    # outlines that survive are stair-steps, i.e. axis-aligned runs
    dark = lines & ((s < 150) | ((b > r + 15) & (s < 320)))
    d8 = dark.astype(np.uint8)
    axis = (cv2.morphologyEx(d8, cv2.MORPH_OPEN, np.ones((1, 11), np.uint8))
            | cv2.morphologyEx(d8, cv2.MORPH_OPEN, np.ones((11, 1), np.uint8)))
    grat |= cv2.dilate(axis, np.ones((3, 3), np.uint8)).astype(bool)
    land_core = cv2.erode((~sea).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    river = cv2.morphologyEx((dark & ~grat & land_core).astype(np.uint8), cv2.MORPH_CLOSE,
                             np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(river, 8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, 4] >= 15  # drop specks
    river = keep[lab] & inside_map(img.shape[:2], p, pad=6)

    sea = sea & ~river
    cls, dist = nearest_color(img, cols)
    cls = cls + 1
    # the soil map repeats the ore markers as grey ghosts; leave them to the fill
    bad = lines | river | ~inside | sea_ghosts(img, sea)
    sea = fill_nearest(sea, bad)
    cls = fill_nearest(cls, bad | (dist > 60) | sea)
    cls[sea] = 0
    cls[~inside] = 0
    QA["soil_bar_colors"] = cols.round().astype(int).tolist()
    return dict(p=p, img=img, cls=cls, land=~sea & inside, river=river,
                band_vals=vals, band_cols=cols)


BIOMES = ["Jungle", "Desert", "Grassland", "Temperate forest", "Tundra", "Ocean"]


def extract_biome_map():
    img = load("biomes.jpeg")
    legend = [(1165, 245, 1376, 505), (1200, 595, 1376, 768)]
    p, score = fit_projection(img, [687, 377, 254, 277], masks=legend)
    QA["biomes.jpeg"] = dict(params=p.round(2).tolist(), fit=round(score, 3))
    # swatch colours from the legend box (x 1180-1210)
    sw_y = [279, 318, 357, 397, 436, 476]
    sw = np.array([np.median(img[y - 8:y + 8, 1184:1208].reshape(-1, 3), axis=0) for y in sw_y])
    QA["biome_swatches"] = sw.round().astype(int).tolist()
    inside = inside_map(img.shape[:2], p)
    smooth = cv2.bilateralFilter(img, 9, 40, 5)
    smooth = cv2.blur(smooth, (5, 5))
    cls, _ = nearest_color(smooth, sw)
    cls = cls + 1
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    ocean = blueish(smooth)
    icy = (hsv[..., 1] < 40) & (hsv[..., 2] > 150)
    cls[ocean] = 6
    cls[icy & ~ocean] = 5
    # majority filter to suppress texture noise
    stack = np.stack([cv2.blur((cls == k).astype(np.float32), (7, 7)) for k in range(1, 7)])
    cls = stack.argmax(0) + 1
    bad = thin_dark_lines(img) | ~inside
    for x0, y0, x1, y1 in legend:
        bad[y0:y1, x0:x1] = True
    cls = fill_nearest(cls, bad)
    cls[~inside] = 0
    return dict(p=p, img=img, cls=cls, legend=legend)


def extract_topography_map():
    img = load("topography.jpg")
    p, score = fit_projection(img, [944, 483, 332, 331],
                              masks=[(1860, 0, 2128, 974), (0, 0, 50, 974)])
    QA["topography.jpg"] = dict(params=p.round(2).tolist(), fit=round(score, 3))
    cols, vals = colorbar(img, 1895, 1920, 78, 924, 2.0, -4.0, n_bands=24)
    inside = inside_map(img.shape[:2], p)
    idx, dist = nearest_color(img, cols)
    elev = vals[idx].astype(np.float32)
    r, g, b = [img[..., i].astype(int) for i in range(3)]
    above = (r > g + 30) & (r > b + 30) & (r > 90)  # brown/red cells: off the top of the bar
    elev[above] = 2.25
    bad = (((dist > 45) & ~above) | ~inside | (img.astype(int).sum(2) < 40)
           | thin_dark_lines(img, k=5, thresh=25))
    # white label boxes and their text
    white = cv2.dilate((img.astype(int).sum(2) > 700).astype(np.uint8), np.ones((9, 9), np.uint8))
    bad |= white.astype(bool)
    elev = fill_nearest(elev, bad)
    elev[~inside] = np.nan
    QA["topography_above_bar_px"] = int((above & inside).sum())
    return dict(p=p, img=img, elev=elev)


OCEAN_PANELS = [
    # name, units, bar rows (top, bottom), value at top, value at bottom
    ("ocean_productivity", "mol m-3 yr-1", (107, 888), 9.5e-4, 3.0e-4),
    ("ocean_po4_limitation", "fraction", (1051, 1832), 0.7262, 0.25),
    ("ocean_par_limitation", "fraction", (1954, 2735), 0.7268, 0.25),
    ("ocean_vertical_velocity", "m s-1 (+ = upwelling)", (2909, 3690), 1.5e-6, -1.5e-6),
    ("ocean_o2", "umol L-1", (3837, 4618), 350.0, 100.0),
]


# vertical centre of each panel's globe, from the extent of the panel's
# non-white pixels (D's is interpolated: its near-zero field renders white)
OCEAN_PANEL_CY = [527, 1438, 2336, 3261, 4186]


def extract_ocean_map():
    img = load("oceanography.jpg")
    out = {}
    panel_h = img.shape[0] / 5
    for i, (name, units, (yt, yb), vt, vb) in enumerate(OCEAN_PANELS):
        # fit on the whole figure; the objective only looks along this panel's lines
        sub = img
        # panels share one layout: fit panel A fully, then only its vertical offset
        if i == 0:
            p, score = fit_projection(sub, [870, 520, 307, 308],
                                      masks=[(1700, 0, 2014, img.shape[0])])
            pA = p
        else:
            p, score = fit_projection(sub, [pA[0], OCEAN_PANEL_CY[i], pA[2], pA[3]],
                                      masks=[(1700, 0, 2014, img.shape[0])], free=(1,))
        QA[f"oceanography.jpg:{name}"] = dict(params=p.round(2).tolist(), fit=round(score, 3))
        cols, vals = colorbar(img, 1755, 1790, yt, yb, vt, vb)
        inside = inside_map(sub.shape[:2], p)
        idx, dist = nearest_color(sub, cols)
        f = vals[idx].astype(np.float32)
        s = sub.astype(int).sum(2)
        r, g, b = [sub[..., k].astype(int) for k in range(3)]
        land = cv2.morphologyEx((s < 60).astype(np.uint8), cv2.MORPH_OPEN,
                                np.ones((5, 5), np.uint8)).astype(bool)
        # site markers (red/white dots, x's) and grid lines
        white = (s > 690)
        dots = cv2.dilate((white | (dist > 60)).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        lines = thin_dark_lines(sub, k=5, thresh=25)
        # site markers are outlined circles: small regions enclosed by lines
        n, lab, st, _ = cv2.connectedComponentsWithStats((~lines).astype(np.uint8), 4)
        enclosed = np.zeros(n, bool)
        enclosed[1:] = st[1:, 4] < 400
        markers = cv2.dilate(enclosed[lab].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        bad = dots | lines | markers | ~inside
        land_f = fill_nearest(land, bad & ~land)
        f = fill_nearest(f, bad | land)
        # the model fields are smooth: anything far from a local median is a
        # leftover marker or grid line
        med = ndimage.median_filter(f, size=21)
        outlier = np.abs(f - med) > 0.12 * abs(vt - vb)
        outlier = cv2.dilate(outlier.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        f = fill_nearest(f, bad | land | outlier)
        f[land_f] = np.nan
        f[~inside] = np.nan
        out[name] = dict(p=p, field=f, land=land_f & inside, units=units, img=sub)
    return out


# --------------------------------------------------------------------------
# Rivers -> lines
# --------------------------------------------------------------------------
def river_lines(river_mask, p):
    sk = skeletonize(river_mask)
    ys, xs = np.nonzero(sk)
    nodes = set(zip(ys.tolist(), xs.tolist()))
    nbrs = {}
    for y, x in nodes:
        nbrs[(y, x)] = [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                        if (dy or dx) and (y + dy, x + dx) in nodes]
    seen_edges = set()
    paths = []
    starts = [n for n in nodes if len(nbrs[n]) != 2] or list(nodes)[:1]
    for s in starts:
        for nb in nbrs[s]:
            if (s, nb) in seen_edges:
                continue
            path = [s, nb]
            seen_edges.update({(s, nb), (nb, s)})
            prev, cur = s, nb
            while len(nbrs[cur]) == 2:
                nxt = nbrs[cur][0] if nbrs[cur][0] != prev else nbrs[cur][1]
                if (cur, nxt) in seen_edges:
                    break
                seen_edges.update({(cur, nxt), (nxt, cur)})
                path.append(nxt)
                prev, cur = cur, nxt
            if len(path) >= 4:
                paths.append(path)
    geoms = []
    for path in paths:
        py, px = np.array(path).T
        lon, lat = pixel_to_lonlat(p, px, py)
        ls = LineString(np.c_[lon, lat]).simplify(0.05)
        if ls.length > 0.3:
            geoms.append(ls)
    return geoms


# --------------------------------------------------------------------------
# Assemble
# --------------------------------------------------------------------------
def nearest_fill_grid(arr, valid, mask):
    """Fill cells in `mask` that are not `valid` from the nearest valid cell."""
    need = mask & ~valid
    if not need.any() or not valid.any():
        return arr
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    out = arr.copy()
    out[need] = arr[tuple(idx)][need]
    return out


def unit_vectors(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def chord_to_km(c):
    return 2 * R_EARTH * np.arcsin(np.clip(c / 2, 0, 1))


def qa_overlay(img, p, name, extra=None):
    im = Image.fromarray(img).convert("RGB")
    d = ImageDraw.Draw(im)
    for lo in range(-180, 181, 30):
        t = np.linspace(-90, 90, 200)
        x, y = to_pixel(p, np.full(200, lo), t)
        d.line(list(zip(x, y)), fill=(255, 0, 255), width=1)
    for la in range(-90, 91, 30):
        s = np.linspace(-180, 180, 200)
        x, y = to_pixel(p, s, np.full(200, la))
        d.line(list(zip(x, y)), fill=(255, 0, 255), width=1)
    if extra:
        extra(d)
    im.save(os.path.join(OUT_DIR, "qa", name))


def colorize(cls, palette):
    out = np.zeros(cls.shape + (3,), np.uint8)
    for k, c in palette.items():
        out[cls == k] = c
    return out


def write_previews(F, folder):
    """One PNG per field so layers can be looked at without GIS software."""
    os.makedirs(folder, exist_ok=True)
    from PIL import ImageFont
    font = ImageFont.load_default()
    for k, (arr, group, _, units, _) in F.items():
        if k in ("lon", "lat"):
            continue
        a = np.asarray(arr, np.float32)
        ok = ~np.isnan(a)
        if not ok.any():
            continue
        lo, hi = np.nanpercentile(a, [1, 99]) if units not in ("0/1", "class", "count") else (np.nanmin(a), np.nanmax(a))
        hi = hi if hi > lo else lo + 1
        cmap = cv2.COLORMAP_TURBO if units in ("class",) else cv2.COLORMAP_VIRIDIS
        z = (np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
        rgb = cv2.applyColorMap(z, cmap)[..., ::-1].copy()
        rgb[~ok] = (200, 200, 200)
        im = Image.fromarray(rgb).resize((NX * 2, NY * 2), Image.NEAREST)
        canvas = Image.new("RGB", (NX * 2, NY * 2 + 22), "white")
        canvas.paste(im, (0, 22))
        ImageDraw.Draw(canvas).text((6, 5), f"{k}  [{group}]  {units}   range shown {lo:.3g} .. {hi:.3g}"
                                    "   (grey = no data)", fill="black", font=font)
        canvas.save(os.path.join(folder, f"{k}.png"))


def main():
    os.makedirs(os.path.join(OUT_DIR, "qa"), exist_ok=True)
    print("ore/elevation ...")
    ore = extract_ore_map()
    print("soil/rivers ...")
    soil = extract_soil_map()
    print("biomes ...")
    bio = extract_biome_map()
    print("topography ...")
    topo = extract_topography_map()
    print("oceanography ...")
    ocean = extract_ocean_map()

    # ---- sample everything onto the grid ----
    print("resampling to grid ...")
    globe = ~np.isnan(sample_continuous(ore["elev"], ore["p"]))
    elev = sample_continuous(ore["elev"], ore["p"])
    land_ore = sample_continuous(ore["land"].astype(np.float32), ore["p"]) > 0.5
    land_soil = sample_continuous(soil["land"].astype(np.float32), soil["p"]) > 0.5
    bio_cls = sample_categorical(bio["cls"], bio["p"], len(BIOMES))
    land_bio = (bio_cls >= 1) & (bio_cls <= 4)
    soil_cls = sample_categorical(soil["cls"], soil["p"], SOIL_CLASSES)
    river_frac = sample_continuous(soil["river"].astype(np.float32), soil["p"])
    elev_src = sample_continuous(topo["elev"], topo["p"])
    ocean_grid = {k: sample_continuous(v["field"], v["p"]) for k, v in ocean.items()}

    # Canonical land mask: majority of the three AI-drawn maps, which share
    # one coastline. Tundra on the biome map is ambiguous (ice sheet vs land)
    # so the biome map votes only through its non-tundra land classes.
    votes = land_ore.astype(int) + land_soil.astype(int) + land_bio.astype(int)
    land = votes >= 2
    # tundra-covered polar land: ore + soil agree
    land |= land_ore & land_soil
    QA["land_agreement"] = {
        "cells_land": int(land.sum()),
        "ore_vs_soil_agree_pct": round(100 * float((land_ore == land_soil).mean()), 2),
        "ore_vs_biome_agree_pct": round(100 * float((land_ore == (land_bio | (bio_cls == 5))).mean()), 2),
    }

    agree = np.zeros((NY, NX, 3), np.uint8)
    agree[..., 0] = land_ore * 255
    agree[..., 1] = land_soil * 255
    agree[..., 2] = land_bio * 255
    Image.fromarray(agree).save(os.path.join(OUT_DIR, "qa", "land_masks_rgb_ore_soil_biome.png"))

    # elevation consistent with land mask
    # cells at the +-180 seam can fall just outside the drawn globe
    for name in ("elev", "elev_src"):
        v = locals()[name]
        gap = np.isnan(v)
        v = nearest_fill_grid(np.nan_to_num(v), ~gap, gap)
        if name == "elev":
            elev = v
        else:
            elev_src = v
    elev = np.where(land, np.maximum(elev, 0.0), np.minimum(elev, -0.05))

    # biome: land cells keep a land biome; ocean cells -> Ocean, with sea ice flag
    is_land_biome = (bio_cls >= 1) & (bio_cls <= 5)
    biome = nearest_fill_grid(bio_cls, is_land_biome, land)
    biome[~land] = 6
    sea_ice = (~land) & (bio_cls == 5)

    # soil: land cells only, nearest-filled where the soil map shows sea
    soil_valid = soil_cls > 0
    soil_g = nearest_fill_grid(soil_cls, soil_valid, land)
    soil_g[~land] = 0

    river = land & (river_frac > 0.02)

    # paleo-native copies (source coastline) before remapping
    paleo_ocean = {k: v.copy() for k, v in ocean_grid.items()}
    paleo_land_model = sample_continuous(ocean["ocean_productivity"]["land"].astype(np.float32),
                                         ocean["ocean_productivity"]["p"]) > 0.5
    # ocean model fields are on the source paper's coastline; fill to the
    # canonical ocean and blank on canonical land
    for k, v in ocean_grid.items():
        valid = ~np.isnan(v)
        v = nearest_fill_grid(np.nan_to_num(v), valid, ~land)
        v[land] = np.nan
        ocean_grid[k] = v

    # ---- derived ----
    LON, LAT = np.meshgrid(LONS, LATS)
    area = (R_EARTH ** 2) * np.radians(RES) * (
        np.sin(np.radians(LAT + RES / 2)) - np.sin(np.radians(LAT - RES / 2)))
    xyz = unit_vectors(LON.ravel(), LAT.ravel())

    er = ndimage.binary_erosion(land, structure=np.ones((3, 3)), border_value=0)
    di = ndimage.binary_dilation(land, structure=np.ones((3, 3)))
    coast = (land & ~er) | (~land & di)
    coastal = land & ~er
    ctree = cKDTree(unit_vectors(LON[coastal], LAT[coastal]))
    dcoast = chord_to_km(ctree.query(xyz)[0]).reshape(NY, NX)
    dcoast = np.where(land, dcoast, -dcoast)  # negative offshore

    # ore deposits
    deps = pd.DataFrame(ore["deposits"])
    ore_counts = {}
    ore_dist = {}
    di_x = np.clip(((deps.lon + 180) / RES).astype(int), 0, NX - 1)
    di_y = np.clip(((90 - deps.lat) / RES).astype(int), 0, NY - 1)
    for ot in sorted(deps.ore_type.unique()):
        c = np.zeros((NY, NX), np.int16)
        sel = deps.ore_type == ot
        np.add.at(c, (di_y[sel], di_x[sel]), 1)
        ore_counts[f"n_{ot}"] = c
    for metal in ("copper", "tin", "iron"):
        sel = deps.metal == metal
        t = cKDTree(unit_vectors(deps.lon[sel].values, deps.lat[sel].values))
        ore_dist[f"dist_{metal}_km"] = chord_to_km(t.query(xyz)[0]).reshape(NY, NX)
    # river distance
    if river.any():
        rt = cKDTree(unit_vectors(LON[river], LAT[river]))
        drive = chord_to_km(rt.query(xyz)[0]).reshape(NY, NX)
    else:
        drive = np.full((NY, NX), np.nan)

    # what each cell can reach offshore: mean of the ocean fields over sea
    # cells within SHELF_KM; gives coastal land a fishery/upwelling signal
    sea_tree = cKDTree(unit_vectors(LON[~land], LAT[~land]))
    chord = 2 * np.sin(SHELF_KM / R_EARTH / 2)
    nbrs = sea_tree.query_ball_point(xyz, chord, workers=-1)
    reach = {}
    for k in ("ocean_productivity", "ocean_vertical_velocity", "ocean_o2"):
        vals = ocean_grid[k][~land]
        out = np.full(len(nbrs), np.nan, np.float32)
        for i, nb in enumerate(nbrs):
            if nb:
                out[i] = np.nanmean(vals[nb])
        reach[k] = out.reshape(NY, NX)

    # 0 sea in both, 1 land in both, 2 land only in the fiction, 3 land only in the paleo data
    paleo_land = elev_src >= 0
    coast_status = np.select([~land & ~paleo_land, land & paleo_land, land & ~paleo_land],
                             [0, 1, 2], default=3).astype(np.int8)

    soil_bands = soil["band_vals"]
    # name: (array, group, source, units, notes)
    # groups: paleo = the published Silurian-era reconstruction, on its own coastline;
    #         fic = the redrawn fictional world; syn = paleo data carried onto the
    #         fictional world, or fields that compare / combine the two
    F = {
        "lon": (LON, "grid", "", "deg", "cell centre, paleo-longitude"),
        "lat": (LAT, "grid", "", "deg", "cell centre, paleo-latitude"),
        "area_km2": (area, "grid", "", "km2", "spherical cell area"),

        "paleo_land": (paleo_land.astype(np.int8), "paleo", "topography.jpg", "0/1",
                       "land where paleo_elev_km >= 0"),
        "paleo_land_ocean_model": (paleo_land_model.astype(np.int8), "paleo", "oceanography.jpg", "0/1",
                                   "land mask of the ocean model grid (black cells)"),
        "paleo_elev_km": (elev_src, "paleo", "topography.jpg", "km",
                          "GCM topography/bathymetry, 0.25 km bands; >2 km cells set to 2.25"),
        **{f"paleo_{k}": (v, "paleo", "oceanography.jpg", ocean[k]["units"],
                          "native model field; NaN on paleo land")
           for k, v in paleo_ocean.items()},

        "fic_land": (land.astype(np.int8), "fic", "ore/soil/biomes", "0/1",
                     "majority vote of the three redrawn maps"),
        "fic_elev_km": (elev, "fic", "ore.jpeg", "km",
                        "colorbar -4..2 km; >=0 on land, <0 at sea; pale shelf set to -0.1"),
        "fic_biome_id": (biome.astype(np.int8), "fic", "biomes.jpeg", "class", "see legend_biome"),
        "fic_sea_ice": (sea_ice.astype(np.int8), "fic", "biomes.jpeg", "0/1", "tundra-white drawn over sea"),
        "fic_soil_id": (soil_g.astype(np.int8), "fic", "soil.jpeg", "class",
                        "12 colorbar bands; see legend_soil (names unassigned)"),
        "fic_soil_bar_value": (np.where(soil_g > 0, soil_bands[np.clip(soil_g - 1, 0, None)], np.nan),
                               "fic", "soil.jpeg", "bar units", "midpoint of the band on the -4..2 bar"),
        "fic_river": (river.astype(np.int8), "fic", "soil.jpeg", "0/1",
                      "river stroke in cell; incomplete extraction"),
        "fic_dist_river_km": (np.where(land, drive, np.nan), "fic", "derived", "km", "great-circle"),
        "fic_coast": (coast.astype(np.int8), "fic", "derived", "0/1", "land or sea cell touching the other"),
        "fic_dist_coast_km": (dcoast, "fic", "derived", "km", "negative offshore"),
        **{f"fic_{k}": (v, "fic", "ore.jpeg", "count", "markers in cell") for k, v in ore_counts.items()},
        **{f"fic_{k}": (v, "fic", "ore.jpeg", "km", "to nearest deposit, any depth")
           for k, v in ore_dist.items()},

        "syn_coast_status": (coast_status, "syn", "derived", "class",
                             "0 sea in both, 1 land in both, 2 land only in fiction, 3 land only in paleo"),
        "syn_elev_delta_km": (elev - elev_src, "syn", "derived", "km", "fic_elev_km - paleo_elev_km"),
        **{f"syn_{k}": (v, "syn", "oceanography.jpg", ocean[k]["units"],
                        "paleo field on the fictional ocean (nearest value where coastlines differ); NaN on fictional land")
           for k, v in ocean_grid.items()},
        "syn_reach_productivity": (reach["ocean_productivity"], "syn", "derived", "mol m-3 yr-1",
                                   f"mean syn_ocean_productivity of fictional sea within {SHELF_KM:.0f} km"),
        "syn_reach_upwelling": (reach["ocean_vertical_velocity"], "syn", "derived", "m s-1",
                                f"mean syn_ocean_vertical_velocity of fictional sea within {SHELF_KM:.0f} km"),
        "syn_reach_o2": (reach["ocean_o2"], "syn", "derived", "umol L-1",
                         f"mean syn_ocean_o2 of fictional sea within {SHELF_KM:.0f} km"),
    }
    fields = {k: v[0] for k, v in F.items()}
    print("writing GeoPackage ...")
    # assemble outside the synced folder; swapped in at the end
    import shutil
    import tempfile
    final_gpkg = os.path.join(OUT_DIR, "world.gpkg")
    gpkg = os.path.join(tempfile.mkdtemp(prefix="world_gis_"), "world.gpkg")
    df = pd.DataFrame({k: np.asarray(v).ravel() for k, v in fields.items()})
    df.insert(0, "row", np.repeat(np.arange(NY), NX))
    df.insert(1, "col", np.tile(np.arange(NX), NY))
    df["fic_biome"] = pd.Categorical.from_codes(df.fic_biome_id - 1, BIOMES).astype(str)
    h = RES / 2
    geom = [box(x - h, y - h, x + h, y + h) for x, y in zip(df.lon, df.lat)]
    gpd.GeoDataFrame(df, geometry=geom, crs=CRS).to_file(gpkg, layer="cells", driver="GPKG")

    deps_gdf = gpd.GeoDataFrame(deps, geometry=gpd.points_from_xy(deps.lon, deps.lat), crs=CRS)
    deps_gdf.to_file(gpkg, layer="ore_deposits", driver="GPKG")

    rl = river_lines(soil["river"], soil["p"])
    gpd.GeoDataFrame({"source": ["soil.jpeg"] * len(rl)}, geometry=rl, crs=CRS).to_file(
        gpkg, layer="rivers_drawn", driver="GPKG")

    def polygonize(arr, mask, name, labeler):
        recs = [(shape(g), int(v)) for g, v in shapes(arr.astype(np.int32), mask=mask, transform=TRANSFORM)]
        g = gpd.GeoDataFrame({"id": [v for _, v in recs]}, geometry=[s for s, _ in recs], crs=CRS)
        g = g.dissolve(by="id").reset_index()
        g["name"] = g.id.map(labeler)
        g.to_file(gpkg, layer=name, driver="GPKG")

    polygonize(land.astype(np.int32), land, "landmass", lambda v: "land")
    polygonize(biome, biome > 0, "biome_regions", lambda v: BIOMES[v - 1])
    polygonize(soil_g, soil_g > 0, "soil_regions", lambda v: f"soil_{v:02d}")

    # legend / metadata tables
    con = sqlite3.connect(gpkg)
    pd.DataFrame({"biome_id": range(1, 7), "biome": BIOMES}).to_sql("legend_biome", con, index=False)
    pd.DataFrame({"soil_id": range(1, SOIL_CLASSES + 1),
                  "bar_value_mid": soil_bands.round(2),
                  "bar_rgb": [",".join(map(str, c)) for c in soil["band_cols"].round().astype(int)],
                  "soil_name": [None] * SOIL_CLASSES}).to_sql("legend_soil", con, index=False)
    pd.DataFrame([(f"{d}_{m}", d, m, s, c) for d, c in (("surface", "red"), ("deep", "purple"))
                  for m, s in (("iron", "triangle"), ("tin", "square"), ("copper", "circle"))],
                 columns=["ore_type", "depth", "metal", "marker_shape", "marker_color"]
                 ).to_sql("legend_ore", con, index=False)
    pd.DataFrame([(k, g, src, u, n) for k, (_, g, src, u, n) in F.items()],
                 columns=["field", "group", "source", "units", "notes"]
                 ).to_sql("field_dictionary", con, index=False)
    pd.DataFrame([{"key": k, "value": json.dumps(v)} for k, v in QA.items()]).to_sql(
        "qa_registration", con, index=False)
    con.close()

    # ---- QA images ----
    print("QA images ...")
    def mark(d):
        for r in ore["deposits"]:
            c = (255, 255, 0) if r["depth"] == "surface" else (0, 255, 255)
            x, y = r["px"], r["py"]
            t = r["shape"][0].upper()
            d.text((x + 5, y - 6), t, fill=c)
    qa_overlay(ore["img"], ore["p"], "ore_registration_and_markers.png", mark)
    qa_overlay(soil["img"], soil["p"], "soil_registration.png")
    qa_overlay(bio["img"], bio["p"], "biomes_registration.png")
    qa_overlay(topo["img"], topo["p"], "topography_registration.png")
    for k, v in ocean.items():
        qa_overlay(v["img"], v["p"], f"{k}_registration.png")
    bio_pal = {1: (20, 90, 30), 2: (225, 200, 140), 3: (175, 200, 100), 4: (90, 140, 70),
               5: (235, 235, 235), 6: (40, 90, 160)}
    Image.fromarray(colorize(biome, bio_pal)).resize((NX * 2, NY * 2), Image.NEAREST).save(
        os.path.join(OUT_DIR, "qa", "grid_biome.png"))
    sp = {k + 1: tuple(int(x) for x in c) for k, c in enumerate(soil["band_cols"])}
    sp[0] = (40, 90, 160)
    sim = colorize(soil_g, sp)
    sim[river] = (0, 0, 120)
    Image.fromarray(sim).resize((NX * 2, NY * 2), Image.NEAREST).save(
        os.path.join(OUT_DIR, "qa", "grid_soil_rivers.png"))
    e = np.clip((elev + 4) / 6, 0, 1)
    ei = (np.stack([e, e, e], 2) * 255).astype(np.uint8)
    ei[land] = (np.stack([e, 0.6 + 0.4 * e, 0.3 * e], 2)[land] * 255).astype(np.uint8)
    for _, r in deps.iterrows():
        y, x = int((90 - r.lat) / RES), int((r.lon + 180) / RES)
        ei[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (255, 0, 0) if r.depth == "surface" else (160, 0, 255)
    Image.fromarray(ei).resize((NX * 2, NY * 2), Image.NEAREST).save(
        os.path.join(OUT_DIR, "qa", "grid_elev_ore.png"))
    oc = ocean_grid["ocean_productivity"]
    o = np.nan_to_num((oc - 3e-4) / 6.5e-4, nan=0)
    oi = (cv2.applyColorMap((np.clip(o, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_JET)[..., ::-1]).copy()
    oi[land] = 0
    Image.fromarray(oi).resize((NX * 2, NY * 2), Image.NEAREST).save(
        os.path.join(OUT_DIR, "qa", "grid_ocean_productivity.png"))

    write_previews(F, os.path.join(OUT_DIR, "previews"))

    with open(os.path.join(OUT_DIR, "qa", "registration.json"), "w") as f:
        json.dump(QA, f, indent=1)
    print(json.dumps({k: v for k, v in QA.items() if "bar" not in k and "swatch" not in k}, indent=1))
    print("deposits:", deps.groupby(["ore_type"]).size().to_dict(),
          "low-confidence:", int((deps.confidence == "low").sum()))
    print("rivers:", len(rl))
    # process-based layers: tectonic setting, history, bedrock, drainage,
    # soil orders, ore review
    import sys
    sys.path.insert(0, HERE)
    import derive_world
    derive_world.derive(gpkg, os.path.join(OUT_DIR, "previews"))
    shutil.move(gpkg, final_gpkg)
    print("wrote", final_gpkg)


if __name__ == "__main__":
    main()
