"""
Map drawing from one snapshot (WP3 stage B, 2026-11-17).

The live `render(sim)` (final_maps.png and the run's frames) and the
offline renderer (`render_run.py`, from history.npz) both draw through
these functions, so they agree. Nothing here imports the simulation step.

    snap = Snap(...)                        # one moment of a run
    proj = Proj(W, "mollweide", scale=2)    # how grid cells reach pixels
    img = frame(snap, proj, ("states", "peoples"))

A projection is an index array: for each output pixel, the grid cell
(row * NX + col) it shows, or -1 for background. Every layer is drawn on
the 360 x 720 grid and then reaches the output by one fancy-index, so a
projection costs nothing per frame. Borders are found on the projected
label image, at output resolution, so they stay one pixel wide. Points
(cities, labels) go through the forward projection.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .params import NY, NX

BG = (16, 18, 24)              # background outside the map and header
SQ2 = math.sqrt(2)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def borders_mask(lab2):
    b = np.zeros(lab2.shape, bool)
    b[:, :-1] |= lab2[:, :-1] != lab2[:, 1:]
    b[:-1, :] |= lab2[:-1, :] != lab2[1:, :]
    return b


# ------------------------------------------------------------ projections

class Proj:
    """Grid-to-pixel mapping. `platecarree`: the raw grid, `scale` pixels
    per cell, cropped to the rows with land (W.r0 to W.r1), as the maps
    were drawn before. `mollweide`: equal-area, the same width, cropped to
    the same latitudes; the inverse is closed-form, the forward solves
    2 theta + sin 2 theta = pi sin(lat) by Newton steps."""

    def __init__(self, W, kind="platecarree", scale=2):
        self.kind, self.scale = kind, scale
        self.r0, self.r1 = W.r0, W.r1
        width = NX * scale
        if kind == "platecarree":
            h = (W.r1 - W.r0) * scale
            y, x = np.mgrid[0:h, 0:width]
            self.idx = (W.r0 + y // scale) * NX + x // scale
            self.size = (width, h)
            return
        if kind != "mollweide":
            raise ValueError(kind)
        self.R = width / (4 * SQ2)              # x spans +-2 sqrt2 R
        lat_top = 90 - 0.5 * W.r0
        lat_bot = 90 - 0.5 * W.r1
        self.y0 = self._fy(lat_top)             # map y of the top edge
        h = int(math.ceil(self.y0 - self._fy(lat_bot)))
        py, px = np.mgrid[0:h, 0:width]
        xm = px + 0.5 - width / 2
        ym = self.y0 - (py + 0.5)
        s = np.clip(ym / (SQ2 * self.R), -1, 1)
        th = np.arcsin(s)
        lat = np.degrees(np.arcsin(np.clip(
            (2 * th + np.sin(2 * th)) / math.pi, -1, 1)))
        with np.errstate(divide="ignore", invalid="ignore"):
            lon = np.degrees(math.pi * xm / (2 * SQ2 * self.R * np.cos(th)))
        ok = np.isfinite(lon) & (np.abs(lon) <= 180)
        row = np.clip(((90 - lat) / 0.5).astype(int), 0, NY - 1)
        col = np.clip(((lon + 180) / 0.5).astype(int), 0, NX - 1)
        self.idx = np.where(ok, row * NX + col, -1)
        self.size = (width, h)

    def _theta(self, lat):
        """Mollweide's auxiliary angle for latitudes (degrees)."""
        phi = np.radians(np.asarray(lat, float))
        th = phi.copy()
        target = math.pi * np.sin(phi)
        for _ in range(8):
            f = 2 * th + np.sin(2 * th) - target
            d = 2 + 2 * np.cos(2 * th)
            th = th - np.where(d > 1e-9, f / np.maximum(d, 1e-9), 0)
        return th

    def _fy(self, lat):
        return float(SQ2 * self.R * np.sin(self._theta(lat)))

    def fwd(self, lon, lat):
        """Pixel (x, y) of points (degrees)."""
        lon, lat = np.asarray(lon, float), np.asarray(lat, float)
        if self.kind == "platecarree":
            x = (lon + 180) / 0.5 * self.scale
            y = ((90 - lat) / 0.5 - self.r0) * self.scale
            return x, y
        th = self._theta(lat)
        x = 2 * SQ2 / math.pi * self.R * np.radians(lon) * np.cos(th) + \
            self.size[0] / 2
        y = self.y0 - SQ2 * self.R * np.sin(th)
        return x, y

    def apply(self, grid, bg):
        """A (NY, NX, ...) grid image as the output image."""
        flat = grid.reshape((NY * NX,) + grid.shape[2:])
        out = flat[np.maximum(self.idx, 0)]
        out[self.idx < 0] = bg
        return out

    def labels(self, lab):
        """A (NY, NX) label grid at output resolution (-9 background)."""
        out = lab.reshape(-1)[np.maximum(self.idx, 0)]
        return np.where(self.idx < 0, -9, out)


# --------------------------------------------------------------- snapshot

class Snap:
    """One moment of a run, as the drawing needs it. Per land cell:
    people, polity, pop (heads), lineage (or None). cities: (cell, size
    in urban fe, polity, capital flag) arrays. states: {pid: (capital,
    people, cities)}. pcol: (max pid + 1, 3) state colours. colors:
    people colours; keys, labels: per people. dragons: (home cells,
    allied flags) or None. title, lines: header text."""

    def __init__(self, year, people, polity, pop, colors, keys, labels,
                 pcol, cities=None, states=None, lineage=None,
                 lcol=None, dragons=None, lines=(), legend=None,
                 since_state=None, since_people=None, strip=None):
        self.year, self.people, self.polity, self.pop = \
            year, people, polity, pop
        self.colors, self.keys, self.labels = colors, keys, labels
        self.pcol, self.lineage, self.lcol = pcol, lineage, lcol
        e = np.zeros(0, int)
        self.cities = cities or dict(cell=e, size=e, polity=e, capital=e)
        self.states = states or {}
        self.dragons = dragons
        self.lines = lines
        self.legend = legend
        # years since each cell last changed state / people (from the
        # snapshots before this one; render_run.py), and the turnover
        # strip under the map: (years, {group: shares}) or None
        self.since_state, self.since_people = since_state, since_people
        self.strip = strip


def pname(snap, pid):
    s = snap.states.get(pid)
    return f"P{pid}({snap.keys[s[1]]})" if s else f"P{pid}"


# ----------------------------------------------------------------- layers

def layer_states(W, snap):
    """States in their colours over a faint people tint for land outside
    any state; returns the grid image and the label grid for borders."""
    img = W.base.astype(float).copy()
    occ = snap.people >= 0
    m = snap.polity >= 0
    rr, cc = W.row, W.col
    tribal = occ & ~m
    col_t = snap.colors[np.maximum(snap.people, 0)].astype(float)
    img[rr[tribal], cc[tribal]] = 0.6 * img[rr[tribal], cc[tribal]] + \
        0.4 * col_t[tribal]
    img[rr[m], cc[m]] = 0.15 * img[rr[m], cc[m]] + \
        0.85 * snap.pcol[snap.polity[m]]
    lab = -np.ones((NY, NX), int)
    lab[rr, cc] = np.where(m, snap.polity, -2)
    lab[~W.land2] = -3
    return img, lab


def _density(W, snap):
    occ = snap.people >= 0
    return occ, np.where(occ, snap.pop / W.area, 0)


def layer_peoples(W, snap):
    """Peoples in their colours, more opaque where denser."""
    img = W.base.astype(float).copy()
    occ, dens = _density(W, snap)
    a = np.clip(np.log10(1 + dens) / np.log10(1 + 60), 0.4, 1)
    col_t = snap.colors[np.maximum(snap.people, 0)].astype(float)
    rr, cc = W.row[occ], W.col[occ]
    img[rr, cc] = (1 - a[occ, None]) * img[rr, cc] + a[occ, None] * col_t[occ]
    return img, None


def layer_density(W, snap):
    """Population density (heads per km2), log scale, 0.1 to 1,000."""
    from matplotlib import colormaps
    img = W.base.astype(float).copy() * 0.5
    occ, dens = _density(W, snap)
    v = np.clip((np.log10(np.maximum(dens, 1e-3)) + 1) / 4, 0, 1)
    lut = colormaps["magma"](np.linspace(0, 1, 256))[:, :3] * 255
    rgb = lut[(v * 255).astype(int)]
    img[W.row[occ], W.col[occ]] = rgb[occ]
    return img, None


def layer_lineages(W, snap):
    """Hue = people, shade = lineage; thin lines between lineages."""
    img = W.base.astype(float).copy()
    L = snap.lineage
    occ = L >= 0
    if snap.lcol is not None:
        col = snap.lcol[np.maximum(L, 0)].astype(float)
    else:
        col = snap.colors[np.maximum(snap.people, 0)].astype(float) * \
            shade(L)[:, None]
    rr, cc = W.row[occ], W.col[occ]
    img[rr, cc] = 0.2 * img[rr, cc] + 0.8 * np.clip(col[occ], 0, 255)
    lab = -np.ones((NY, NX), int)
    lab[W.row, W.col] = L
    return img, lab


AGE_MAX = 2000      # years: the age layers' darkest shade (C)


def _age(W, snap, since, occ):
    """Years since a change, log scale from 25 to AGE_MAX years: young
    (bright yellow) to old (dark purple); never changed in the run:
    darkest."""
    from matplotlib import colormaps
    img = W.base.astype(float).copy() * 0.5
    v = np.clip(np.log(np.maximum(since, 25) / 25) /
                np.log(AGE_MAX / 25), 0, 1)
    lut = colormaps["inferno"](np.linspace(0, 1, 256))[:, :3] * 255
    rgb = lut[((1 - v) * 230 + 20).astype(int)]
    img[W.row[occ], W.col[occ]] = rgb[occ]
    return img


def layer_state_age(W, snap):
    """Ruled cells by years since they last changed state (including
    from no state); borders between states."""
    occ = snap.polity >= 0
    img = _age(W, snap, snap.since_state, occ)
    lab = -np.ones((NY, NX), int)
    lab[W.row, W.col] = np.where(occ, snap.polity, -2)
    return img, lab


def layer_people_age(W, snap):
    """Occupied cells by years since their people last changed."""
    return _age(W, snap, snap.since_people, snap.people >= 0), None


def shade(ids):
    """A fixed brightness factor (0.6-1.3) per id, from the id alone."""
    h = (np.asarray(ids, np.int64) * 2654435761) % 1000
    return 0.6 + 0.7 * h / 1000


LAYERS = dict(states=layer_states, peoples=layer_peoples,
              density=layer_density, lineages=layer_lineages,
              state_age=layer_state_age, people_age=layer_people_age)


# ----------------------------------------------------------------- panels

def panel(W, snap, proj, layer, dots=True, labels=None):
    """One map panel. labels: True to name the ten largest states."""
    grid, lab = LAYERS[layer](W, snap)
    img = proj.apply(grid, BG)
    if lab is not None:
        lo = proj.labels(lab)
        bm = borders_mask(lo) & (lo >= 0)
        img[bm] *= 0.25 if layer == "states" else 0.6
    P = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(P)
    if layer == "peoples" and snap.dragons is not None:
        home, ally = snap.dragons
        x, y = proj.fwd(W.lon[home], W.lat[home])
        for xi, yi, al in zip(x, y, ally):
            d.rectangle([xi - 1, yi - 1, xi + 1, yi + 1],
                        fill=(255, 215, 0) if al >= 0 else (120, 0, 0))
    if dots:
        draw_cities(W, snap, proj, d)
    if labels is None:
        labels = layer in ("states", "state_age")
    if labels:
        draw_labels(W, snap, proj, d)
    return P


def big_states(snap, n=10, min_cells=150):
    """The n largest states by cells (at least min_cells)."""
    ids, cnt = np.unique(snap.polity[snap.polity >= 0], return_counts=True)
    o = np.argsort(-cnt)[:n]
    return [(int(ids[i]), int(cnt[i])) for i in o if cnt[i] >= min_cells]


def draw_cities(W, snap, proj, d):
    C = snap.cities
    if not len(C["cell"]):
        return
    cells = np.asarray(C["cell"], int)
    x, y = proj.fwd(W.lon[cells], W.lat[cells])
    big = {pid for pid, n in big_states(snap, n=10 ** 6, min_cells=251)}
    for xi, yi, s, pol, cap in zip(x, y, C["size"], C["polity"],
                                   C["capital"]):
        rad = 1 + 1.2 * math.log10(1 + max(float(s), 0) / 2000)
        d.ellipse([xi - rad, yi - rad, xi + rad, yi + rad],
                  fill=(255, 255, 255) if cap else (235, 230, 215),
                  outline=(0, 0, 0))
        if cap and int(pol) in big:
            d.ellipse([xi - rad - 3, yi - rad - 3, xi + rad + 3,
                       yi + rad + 3], outline=(255, 255, 255), width=2)


def piece_centre(W, cells):
    """The cell of a state's largest piece (8-connected on the grid,
    joined across the date line) nearest that piece's centre."""
    from scipy import ndimage
    g = np.zeros((NY, NX + 2), bool)
    g[W.row[cells], W.col[cells] + 1] = True
    g[:, 0], g[:, -1] = g[:, -2], g[:, 1]           # wrap one column
    lab, n = ndimage.label(g, structure=np.ones((3, 3)))
    if n > 1:
        # pieces that meet across the date line are one
        for a, b in zip(lab[:, 0], lab[:, -2]):
            if a and b and a != b:
                lab[lab == a] = b
        for a, b in zip(lab[:, -1], lab[:, 1]):
            if a and b and a != b:
                lab[lab == a] = b
    own = lab[W.row[cells], W.col[cells] + 1]
    big = np.bincount(own).argmax()
    piece = cells[own == big]
    xyz = W.xyz[piece]
    m = xyz.mean(0)
    return piece[np.argmax(xyz @ m)]


def draw_labels(W, snap, proj, d):
    """The ten largest states (150+ cells), each named at the centre of
    its largest piece (C, WP3 stage C; was the capital); a label that
    would overlap one already placed is left out."""
    f = font(13)
    placed = []
    for pid, _ in big_states(snap):
        c = piece_centre(W, np.nonzero(snap.polity == pid)[0])
        x, y = proj.fwd(W.lon[c], W.lat[c])
        text = pname(snap, pid)
        w = 7 * len(text)                   # about 7 px a character
        cx, y0 = float(x), float(y) - 7
        if any(abs(cx - a) < (w + b) / 2 + 4 and abs(y0 - c2) < 15
               for a, c2, b in placed):
            continue
        placed.append((cx, y0, w))
        d.text((cx - w / 2, y0), text, fill=(255, 255, 255), font=f,
               stroke_width=2, stroke_fill=(0, 0, 0))


# ------------------------------------------------------------------ strip

STRIP_H = 110
STRIP_COLS = dict(S=(230, 159, 0), W=(86, 180, 233), N=(0, 158, 115),
                  E=(240, 228, 66), X=(204, 121, 167))


def draw_strip(snap, width):
    """Turnover by landmass group over the whole run, with the current
    year marked: the share of ruled cells whose state differs from 100
    years before (render_run.turnover)."""
    years, series = snap.strip
    im = Image.new("RGB", (width, STRIP_H), BG)
    d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = 60, width - 70, 10, STRIP_H - 22
    d.rectangle([x0, y0, x1, y1], outline=(70, 72, 80))
    for v in (0.25, 0.5, 0.75):
        y = y1 - v * (y1 - y0)
        d.line([x0, y, x1, y], fill=(40, 42, 50))
    d.text((6, y0 - 2), "1.0", fill=(150, 150, 150), font=font(11))
    d.text((6, y1 - 10), "0", fill=(150, 150, 150), font=font(11))
    span = max(float(years[-1] - years[0]), 1)
    X = x0 + (years - years[0]) / span * (x1 - x0)
    for g, v in series.items():
        ok = np.isfinite(v)
        pts = [(float(a), float(y1 - b * (y1 - y0)))
               for a, b in zip(X[ok], v[ok])]
        if len(pts) > 1:
            d.line(pts, fill=STRIP_COLS.get(g, (200, 200, 200)), width=2)
    for i, g in enumerate(series):
        d.text((x1 + 8, y0 + 14 * i), g,
               fill=STRIP_COLS.get(g, (200, 200, 200)), font=font(12))
    xc = x0 + (snap.year - years[0]) / span * (x1 - x0)
    d.line([xc, y0, xc, y1], fill=(255, 255, 255), width=1)
    d.text((x0, y1 + 4), "ruled cells that changed state in the last 100 "
           "years, by landmass group", fill=(170, 170, 170), font=font(12))
    return im


# ------------------------------------------------------------------ frame

def frame(W, snap, proj, layers=("states", "peoples")):
    """Panels stacked under a header: the year, each people's colour,
    name and line of figures (snap.legend, else its population), and
    snap.lines on the left; the turnover strip last, if snap has one."""
    panels = [panel(W, snap, proj, ly) for ly in layers]
    w = panels[0].size[0]
    nP = len(snap.keys)
    rows = (nP + 4) // 5
    hdr = 14 + 38 * rows
    if snap.strip is not None:
        panels.append(draw_strip(snap, w))
    out = Image.new("RGB", (w, hdr + sum(P.size[1] + 6 for P in panels)
                            - 6), BG)
    y = hdr
    for P in panels:
        out.paste(P, (0, y))
        y += P.size[1] + 6
    d = ImageDraw.Draw(out)
    d.text((12, 8), f"Year {snap.year}", fill=(240, 240, 240), font=font(24))
    legend = snap.legend
    if legend is None:
        occ = snap.people >= 0
        pp = np.bincount(snap.people[occ], weights=snap.pop[occ],
                         minlength=nP)
        legend = [f"{pp[i] / 1e6:5.2f}M" for i in range(nP)]
    for i in range(nP):
        x = 150 + 225 * (i % 5)
        y0 = 38 * (i // 5)
        d.rectangle([x, 12 + y0, x + 14, 26 + y0],
                    fill=tuple(int(v) for v in snap.colors[i]))
        d.text((x + 20, 8 + y0), snap.labels[i], fill=(230, 230, 230),
               font=font(13))
        d.text((x + 20, 26 + y0), legend[i], fill=(170, 170, 170),
               font=font(12))
    for k, line in enumerate(snap.lines):
        d.text((12, 40 + 18 * k), line, fill=(230, 230, 230), font=font(13))
    return out
