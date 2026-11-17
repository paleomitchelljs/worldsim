"""
Tectonic history and bedrock for the fictional world (called from
derive_world.py).

Tectonics follow Earth's real history up to the Silurian configuration the
world is drawn on (the fictional present = Earth ~430 Ma, tectonically),
reaching back one to two Wilson cycles (to ~1.1 Ga). Events are placed on
each paleocontinent by geometry -- the margin facing the right neighbour,
detected trenches, interior basins -- not by copying modern maps.

Bedrock is a rock column per cell. Each event deposits, intrudes or
metamorphoses units; a deposited unit's lithology follows its environment,
its paleolatitude (from approximate real latitude tracks), and the biotic
clock. Erosion depth (elevation, relief, setting) decides what is exposed.

The biotic clock: the fictional present has a modern biota on Silurian
geography, so by default life runs BIOTIC_OFFSET_MYR ahead of Earth's at the
same tectonic moment. Skeletal carbonate factories, land plants (coal) and
chalk-forming plankton all appear that much earlier.

Ages are Earth-equivalent Ma; *_bp fields give years before the fictional
present (= Earth-equivalent age - PRESENT_MA).
"""
import numpy as np
from scipy import ndimage

NY, NX, RES = 360, 720, 0.5
PRESENT_MA = 430
BIOTIC_OFFSET_MYR = 430
EARTH_ONSET_MA = {"skeletal_carbonate": 540, "land_plants": 470, "forests": 385,
                  "pelagic_calcifiers": 220}


def onset(k):
    return EARTH_ONSET_MA[k] + BIOTIC_OFFSET_MYR


# Paleocontinent labels (lon, lat) read off topography.jpg
BLOCK_LABELS = {"Arctic Alaska-Chukotka": (-83.6, 26.8), "Kolyma-Omolon": (-49.5, 15.5),
                "Siberia": (-18.1, 14.8), "Tarim": (19.5, 25.9), "North China": (24.7, 8.3),
                "South China": (61.1, 13.0), "Annamia": (51.3, -11.3),
                "Laurentia": (-90.0, -4.9), "Baltica": (-44.2, -21.8),
                "Avalonia": (-75.1, -39.1), "Gondwana": (93.3, -75.4)}
CRUST_KM = -1.0  # paleo elevation above this = continental crust (land + shelf)

# Approximate centroid paleolatitude (deg) by Earth-equivalent age, from
# published reconstructions; uncertain by ~10-15 deg, worse for small blocks.
AGES = [1100, 750, 600, 540, 485, 445, 430]
PALEOLAT = {
    "Laurentia":              [-10, 0, -15, -10, -10, -5, -5],
    "Baltica":                [-30, -45, -50, -55, -50, -30, -20],
    "Avalonia":               [-50, -60, -65, -60, -55, -35, -30],
    "Siberia":                [5, 10, 0, 5, 10, 15, 20],
    "Gondwana":               [-30, -30, -40, -35, -40, -50, -50],
    "North China":            [10, 10, 0, -5, -5, 0, 5],
    "South China":            [10, 15, 0, -5, -10, -5, 0],
    "Tarim":                  [10, 10, 0, -5, -10, 0, 5],
    "Annamia":                [-10, -10, -15, -15, -15, -10, -10],
    "Kolyma-Omolon":          [20, 20, 15, 15, 15, 20, 20],
    "Arctic Alaska-Chukotka": [20, 20, 15, 15, 15, 20, 25],
}

BASEMENT_LITH = {"archean": "granite-gneiss", "paleoproterozoic": "schist-gneiss",
                 "grenville": "granulite-gneiss", "neoproterozoic": "granite-gneiss",
                 "arc": "granodiorite", "orogen": "schist-gneiss"}


# ---- geometry helpers --------------------------------------------------------
def gc_dist(mask, LAT, LON):
    from scipy.spatial import cKDTree

    def xyz(lo, la):
        lo, la = np.radians(lo), np.radians(la)
        return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    if not mask.any():
        return np.full(mask.shape, np.inf)
    t = cKDTree(xyz(LON[mask], LAT[mask]))
    d = t.query(xyz(LON.ravel(), LAT.ravel()))[0]
    return (2 * 6371.0 * np.arcsin(np.clip(d / 2, 0, 1))).reshape(mask.shape)


def smooth_noise(seed, sigma):
    """Low-frequency noise in [0, 1] for lateral variation (wraps in longitude)."""
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((NY, NX))
    ext = np.concatenate([a[:, -3 * sigma:], a, a[:, :3 * sigma]], axis=1)
    f = ndimage.gaussian_filter(ext, sigma)[:, 3 * sigma:-3 * sigma]
    f = (f - f.min()) / (f.max() - f.min())
    return f


# ---- blocks ---------------------------------------------------------------------
def assign_blocks(paleo_E, land, LAT, LON):
    """Continental blocks = connected paleo continental crust; each fictional
    land cell takes the block of its nearest paleo crust cell; blocks fused in
    the paleo data are split between their labels by nearest label."""
    crust = np.nan_to_num(paleo_E, nan=-9) > CRUST_KM
    ext = np.concatenate([crust, crust], 1)
    lab, _ = ndimage.label(ext, np.ones((3, 3)))
    lab = np.where(lab[:, :NX] > 0, lab[:, :NX], lab[:, NX:])
    idx = ndimage.distance_transform_edt(~crust, return_distances=False, return_indices=True)
    comp = lab[idx[0], idx[1]]  # every cell -> nearest crust component
    names = np.array(list(BLOCK_LABELS))
    label_comp = {}
    for n, (lo, la) in BLOCK_LABELS.items():
        r, c = int((90 - la) / RES), int((lo + 180) / RES)
        label_comp[n] = comp[r, c]
    block = np.full((NY, NX), "", object)
    for cid in set(label_comp.values()):
        members = [n for n in names if label_comp[n] == cid]
        cells = (comp == cid) & (land | crust)
        if len(members) == 1:
            block[cells] = members[0]
        else:
            pts = [BLOCK_LABELS[n] for n in members]
            d = np.stack([gc_dist(_point_mask(lo, la), LAT, LON) for lo, la in pts])
            block[cells] = np.array(members, object)[d.argmin(0)][cells]
    # land not attached to any labelled block: nearest labelled block cell
    orphan = land & (block == "")
    if orphan.any():
        known = block != ""
        ii = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
        block[orphan] = block[ii[0], ii[1]][orphan]
    return block, crust


def _point_mask(lo, la):
    m = np.zeros((NY, NX), bool)
    m[int(np.clip((90 - la) / RES, 0, NY - 1)), int(np.clip((lo + 180) / RES, 0, NX - 1))] = True
    return m


def paleolat(block, LAT, age):
    """Cell paleolatitude at an Earth-equivalent age: present latitude shifted
    by the block centroid's latitude change (translation only)."""
    out = LAT.astype(float).copy()
    for n, track in PALEOLAT.items():
        m = block == n
        if m.any():
            shift = np.interp(age, AGES[::-1], track[::-1]) - track[-1]
            out[m] = LAT[m] + shift
    return np.clip(out, -90, 90)


# ---- lithology rules ---------------------------------------------------------
def shelf_lith(plat, age, deep, noise):
    """Marine shelf lithology from paleolatitude, water depth proxy and biota."""
    a = abs(plat)
    skeletal = age <= onset("skeletal_carbonate")
    chalk_ok = age <= onset("pelagic_calcifiers")
    if a > 60:
        return "glacial diamictite" if noise > 0.5 else "sandstone"
    if a > 40:
        if skeletal and a < 50 and noise > 0.6:
            return "limestone"  # cool-water skeletal carbonate
        return "shale" if deep or noise > 0.5 else "sandstone"
    if deep:
        if chalk_ok and a < 40:
            return "chalk" if noise > 0.4 else "marl"
        return "shale"
    if a < 30:
        if not skeletal:
            return "dolostone" if noise > 0.4 else "shale"  # microbial carbonate only
        if 15 < a < 30 and noise > 0.55:
            return "dolostone"  # restricted, evaporative inner platform
        return "limestone"
    return "limestone" if (skeletal and noise > 0.5) else "shale"


def terrestrial_lith(plat, age, noise):
    a = abs(plat)
    if 15 < a < 35:
        return "red-bed sandstone"
    if a > 60:
        return "glacial diamictite"
    if age <= onset("forests") and (a < 12 or 35 < a < 60) and noise > 0.5:
        return "coal measures"
    return "sandstone" if noise > 0.35 else "conglomerate"


def basin_lith(plat, age, noise):
    a = abs(plat)
    if 15 < a < 35:
        return "evaporite" if noise > 0.5 else "dolostone"
    return shelf_lith(plat, age, False, noise)


# metamorphic equivalents when a collision overprints a column
METAMORPHOSE = {"limestone": "marble", "dolostone": "marble", "chalk": "marble",
                "marl": "schist", "shale": "slate-phyllite", "black shale": "slate-phyllite",
                "sandstone": "quartzite", "red-bed sandstone": "quartzite",
                "conglomerate": "quartzite", "greywacke": "schist",
                "evaporite": "marble", "coal measures": "slate-phyllite",
                "basalt": "amphibolite", "andesite": "greenschist",
                "glacial diamictite": "schist", "oolitic ironstone": "schist",
                "melange": "blueschist-melange"}


# ---- history ------------------------------------------------------------------
class Columns:
    """Per-cell rock columns: basement plus a stack of units (oldest first)."""

    def __init__(self, cells):
        self.cells = cells  # flat indices of land cells
        self.basement = {}  # idx -> (lithology, age_ma, province)
        self.units = {i: [] for i in cells}  # idx -> [dict(unit, lith, age, thick, event)]

    def set_basement(self, idx, lith, age, province):
        for i in idx:
            self.basement[i] = (lith, age, province)

    def deposit(self, idx, unit, age, thick, lith_fn, event):
        for i in idx:
            t = thick(i) if callable(thick) else thick
            if t > 0:
                self.units[i].append(dict(unit=unit, lith=lith_fn(i), age=age, thick=t, event=event))

    def metamorphose(self, idx, age, province):
        for i in idx:
            for u in self.units[i]:
                u["lith"] = METAMORPHOSE.get(u["lith"], u["lith"])
            lith, _, _ = self.basement.get(i, ("granite-gneiss", age, province))
            self.basement[i] = ("schist-gneiss" if lith != "granite" else lith, age, province)

    def intrude(self, idx, lith, age, province):
        """Plutons replace basement and cut the cover; exposed where unroofed."""
        for i in idx:
            self.basement[i] = (lith, age, province)


def build_history(df, land, LAT, LON, setting_name, trench_mask, seed=7):
    """Returns block map, Columns, event log, and present-day collision zone."""
    paleo_E = np.full((NY, NX), np.nan)
    r, c = df["row"].values, df["col"].values
    paleo_E[r, c] = df["paleo_elev_km"].values
    block, crust = assign_blocks(paleo_E, land, LAT, LON)
    cont = land | crust
    flat = np.nonzero(land.ravel())[0]
    col = Columns(flat)
    events = []
    noise = {k: smooth_noise(seed + k, s).ravel() for k, s in
             ((0, 6), (1, 3), (2, 10), (3, 4), (4, 2))}
    sea = ~cont
    d_coast = gc_dist(sea, LAT, LON)  # distance to open ocean (off continental crust)
    d_trench = gc_dist(trench_mask, LAT, LON)

    def blk(n):
        return block == n

    def cells(m):
        return np.nonzero((m & land).ravel())[0]

    nb8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    sea_any = np.zeros((NY, NX), bool)
    for dy, dx in nb8:
        sea_any |= np.roll(np.roll(~land, dy, 0), dx, 1)
    coast_all = land & sea_any

    # outward normal of every coast: down the gradient of distance-to-sea
    d_sea_in = ndimage.gaussian_filter(gc_dist(~land, LAT, LON), 1.5)
    ny_out, nx_out = np.gradient(-d_sea_in)
    coslat = np.maximum(np.cos(np.radians(LAT)), 0.2)

    def margin(n, targets, width, toward=True, reach=2500, max_angle=60):
        """Belt of width km inland of the stretch of block n's coast whose
        outward normal points toward (or away from) the target blocks."""
        tm = np.isin(block, targets) & cont
        bl = blk(n) & land
        if not tm.any() or not bl.any():
            return np.zeros((NY, NX), bool)
        d = ndimage.gaussian_filter(gc_dist(tm, LAT, LON), 1.5)
        ty, tx = np.gradient(-d)  # direction toward the target
        if not toward:
            ty, tx = -ty, -tx
        # compare directions in km-space (x shrinks with latitude)
        ax, ay = nx_out / coslat, ny_out
        bx, by = tx / coslat, ty
        cosang = (ax * bx + ay * by) / (np.hypot(ax, ay) * np.hypot(bx, by) + 1e-12)
        face = bl & coast_all & (cosang > np.cos(np.radians(max_angle)))
        if toward:
            dn = np.where(face, gc_dist(tm, LAT, LON), np.inf)
            face &= dn < dn.min() + reach
        if not face.any():
            return face
        return bl & (gc_dist(face, LAT, LON) < width)

    def facing(n, targets, width):
        return margin(n, targets, width, toward=True)

    def far_side(n, targets, width):
        return margin(n, targets, width, toward=False)

    def log(age, n, event, kind, basis, mask):
        events.append(dict(age_ma=age, age_bp=age - PRESENT_MA, block=n, event=event,
                           kind=kind, basis=basis, cells=int((mask & land).sum())))

    def plat_at(age):
        return paleolat(block, LAT, age).ravel()

    # -- basement mosaics: cratonic nuclei and the belts that weld them --------
    rng = np.random.default_rng(seed)
    craton_spec = {
        # block: (nucleus ages, juvenile-terrane ages, welding-belt age, belt
        #         province, nucleus fraction, km2 per domain, belt half-width cells)
        "Laurentia": ((2700, 3000), (1800, 1900), 1850, "paleoproterozoic", 0.5, 7e5, 2),
        "Baltica": ((2700, 2900), (1850, 1950), 1900, "paleoproterozoic", 0.35, 6e5, 2),
        "Siberia": ((2600, 3000), (1850, 2000), 1900, "paleoproterozoic", 0.5, 6e5, 2),
        "North China": ((2500, 2800), (1900, 2100), 1850, "paleoproterozoic", 0.5, 4e5, 1),
        "Tarim": ((2400, 2600), (1800, 2000), 1900, "paleoproterozoic", 0.4, 4e5, 1),
        "South China": ((2000, 2500), (900, 1000), 850, "neoproterozoic", 0.3, 4e5, 1),
        "Gondwana": ((2500, 3200), (1800, 2200), 580, "neoproterozoic", 0.45, 2.0e6, 2),
        "Annamia": ((1800, 2200), (900, 1100), 600, "neoproterozoic", 0.2, 4e5, 1),
        "Avalonia": ((620, 620), (600, 650), 620, "arc", 0.0, 4e5, 1),
        "Kolyma-Omolon": ((1800, 2000), (900, 1100), 700, "neoproterozoic", 0.3, 4e5, 1),
        "Arctic Alaska-Chukotka": ((1000, 1200), (700, 900), 700, "neoproterozoic", 0.2, 4e5, 1),
    }
    from scipy.spatial import cKDTree

    def xyz(lo, la):
        lo, la = np.radians(lo), np.radians(la)
        return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    cell_area = (6371.0 ** 2) * np.radians(RES) * np.abs(
        np.sin(np.radians(LAT + RES / 2)) - np.sin(np.radians(LAT - RES / 2)))
    warp_y = (smooth_noise(seed + 20, 4) - 0.5) * 8.0  # degrees
    warp_x = (smooth_noise(seed + 21, 4) - 0.5) * 8.0
    for n, (nuc_age, juv_age, belt_age, belt_prov, frac, dom_km2, belt_hw) in craton_spec.items():
        belt_km = 75.0 * belt_hw  # nominal half-width
        m = blk(n) & land
        if not m.any():
            continue
        # domains on the sphere (great-circle Voronoi), with boundaries warped
        # by smooth noise so sutures meander, and belts whose width varies
        rr, cc = np.nonzero(m)
        area = float((m * cell_area).sum())
        k = max(1, int(area / dom_km2))
        pick = rng.choice(len(rr), size=min(k, len(rr)), replace=False)
        wlat = LAT[rr, cc] + warp_y[rr, cc]
        wlon = LON[rr, cc] + warp_x[rr, cc] / np.maximum(np.cos(np.radians(LAT[rr, cc])), 0.2)
        P = xyz(wlon, wlat)
        S = xyz(LON[rr[pick], cc[pick]], LAT[rr[pick], cc[pick]])
        dd, ii = cKDTree(S).query(P, k=min(2, len(pick)))
        if dd.ndim == 1:
            dd, ii = dd[:, None], ii[:, None]
        dom = np.zeros((NY, NX), int)
        dom[rr, cc] = ii[:, 0] + 1
        gap_km = (dd[:, -1] - dd[:, 0]) * 6371.0 if dd.shape[1] > 1 else np.full(len(rr), 1e9)
        half_w = belt_km * (0.5 + noise[1].reshape(NY, NX)[rr, cc])  # 50-150% of nominal
        belt = np.zeros((NY, NX), bool)
        belt[rr, cc] = gap_km < half_w
        nucleus_ids = rng.random(len(pick) + 1) < frac
        nuc = m & nucleus_ids[dom] & ~belt
        nuc_age_cell = rng.uniform(*nuc_age, size=len(pick) + 1)[dom]
        for i in cells(nuc):
            col.basement[i] = (BASEMENT_LITH["archean"] if nuc_age[0] >= 2500 else "granite-gneiss",
                               float(round(nuc_age_cell.flat[i], -1)),
                               "archean craton" if nuc_age[0] >= 2500 else "proterozoic craton")
        juv = m & ~nucleus_ids[dom] & ~belt
        juv_age_cell = rng.uniform(*juv_age, size=len(pick) + 1)[dom]
        for i in cells(juv):
            col.basement[i] = ("granite-gneiss" if noise[4][i] > 0.5 else "schist-gneiss",
                               float(round(juv_age_cell.flat[i], -1)), "proterozoic terrane")
        prov = {"paleoproterozoic": "paleoproterozoic belt", "neoproterozoic":
                ("pan-african belt" if n == "Gondwana" else "neoproterozoic belt"),
                "arc": "neoproterozoic arc terrane"}[belt_prov]
        for i in cells(m & belt):
            col.basement[i] = (BASEMENT_LITH[belt_prov], float(belt_age), prov)
        log(belt_age, n, f"basement assembly ({prov} welding older nuclei)", "basement",
            "real history; mosaic geometry generated", m)

    # -- Grenville / Sveconorwegian (~1.1-1.0 Ga): Rodinia assembly ------------
    g = facing("Laurentia", ["Baltica", "Avalonia"], 600)
    col.set_basement(cells(g), "granulite-gneiss", 1080.0, "grenville belt")
    log(1080, "Laurentia", "Grenville orogeny on the Iapetan margin", "collision", "real history", g)
    sv = facing("Baltica", ["Laurentia"], 400)
    col.set_basement(cells(sv), "granulite-gneiss", 1000.0, "sveconorwegian belt")
    log(1000, "Baltica", "Sveconorwegian orogeny on the Laurentia-facing margin", "collision",
        "real history", sv)

    # Midcontinent-type failed rift across Laurentia's interior (~1.1 Ga)
    L = blk("Laurentia") & land
    if L.any():
        dg = gc_dist(g, LAT, LON)
        interior = L & ~g & (d_coast > 500)
        # line through the interior running away from the Grenville front
        rr, cc = np.nonzero(interior)
        if len(rr):
            centre = (rr.mean(), cc.mean())
            gy, gx = np.gradient(np.where(L, dg, np.nan))
            ang = np.arctan2(np.nanmean(gy[interior]), np.nanmean(gx[interior]))
            yy, xx = np.mgrid[0:NY, 0:NX]
            along = (yy - centre[0]) * np.sin(ang) + (xx - centre[1]) * np.cos(ang)
            across = -(yy - centre[0]) * np.cos(ang) + (xx - centre[1]) * np.sin(ang)
            wiggle = 2 * np.sin(along / 6.0)
            rift = L & (np.abs(across - wiggle) < 1.5) & (np.abs(along) < 24) & ~g
            p = plat_at(1100)
            col.deposit(cells(rift), "rift volcanics", 1100, 4.0, lambda i: "basalt",
                        "midcontinent rift")
            col.deposit(cells(rift), "rift fill", 1090, 2.0,
                        lambda i: terrestrial_lith(p[i], 1090, noise[1][i]), "midcontinent rift")
            log(1100, "Laurentia", "Midcontinent-type failed rift (basalt, red beds; Cu host)",
                "rift", "real history; trace generated", rift)

    # -- Rodinia breakup and Iapetus opening (750-570 Ma) ----------------------
    rift_spec = [("Laurentia", ["Baltica", "Avalonia"], False, 750, "Panthalassic rifted margin"),
                 ("Laurentia", ["Baltica", "Avalonia"], True, 600, "Iapetan rifted margin"),
                 ("Baltica", ["Laurentia"], True, 600, "Iapetan rifted margin"),
                 ("Siberia", ["Laurentia"], True, 750, "rifted margin"),
                 ("Siberia", ["Laurentia"], False, 750, "rifted margin")]
    for n, tg, face, age, name in rift_spec:
        m = (facing(n, tg, 200) if face else far_side(n, tg, 200)) & land
        p = plat_at(age)
        col.deposit(cells(m), "rift volcanics", age, 1.0, lambda i: "basalt", name)
        col.deposit(cells(m), "rift fill", age - 10, 2.0,
                    lambda i: terrestrial_lith(p[i], age - 10, noise[1][i]), name)
        log(age, n, name, "rift", "real history", m)
    tim = far_side("Baltica", ["Laurentia"], 300) & land
    col.set_basement(cells(tim), "schist-gneiss", 600.0, "timanide belt")
    log(600, "Baltica", "Timanide orogen on the margin away from Laurentia", "collision",
        "real history", tim)

    # -- passive margins and platforms (Ediacaran-Ordovician, 580-460 Ma) -------
    # basal transgressive sand, then a shelf sequence whose lithology follows
    # paleolatitude and the biotic clock; thicker toward the open ocean
    for n in PALEOLAT:
        m = blk(n) & land
        if not m.any():
            continue
        idx = cells(m)
        dc = d_coast.ravel()
        sag = noise[2]  # long-wavelength basins (high) and arches (low)
        wedge = lambda i: (0.2 + 2.2 * sag[i] ** 1.5) + 3.0 * np.exp(-dc[i] / 250.0)
        p540, p500, p470 = plat_at(540), plat_at(500), plat_at(470)
        col.deposit(idx, "basal sandstone", 545, 0.3,
                    lambda i: "sandstone" if abs(p540[i]) < 60 else "glacial diamictite",
                    "marine transgression")
        col.deposit(idx, "lower shelf sequence", 515, wedge,
                    lambda i: shelf_lith(p500[i], 515, dc[i] < 120, noise[0][i]),
                    "passive margin / platform")
        col.deposit(idx, "upper shelf sequence", 475, lambda i: 0.6 * wedge(i),
                    lambda i: shelf_lith(p470[i], 475, dc[i] < 120, noise[3][i]),
                    "passive margin / platform")
        log(530, n, "passive-margin wedge and platform cover", "platform",
            "real history; facies from paleolatitude + biotic clock", m)

    # Ordovician-Silurian oolitic ironstones on mid-latitude shelves
    p460 = plat_at(460)
    iron = land & (np.abs(p460.reshape(NY, NX)) > 25) & (np.abs(p460.reshape(NY, NX)) < 60) \
        & (noise[2].reshape(NY, NX) > 0.7) & ~np.isin(block, ["Gondwana"]) | \
        (land & blk("Gondwana") & (noise[2].reshape(NY, NX) > 0.85)
         & (np.abs(p460.reshape(NY, NX)) > 25))
    col.deposit(cells(iron), "ironstone", 460, 0.05, lambda i: "oolitic ironstone",
                "high-stand ironstone")
    log(460, "several", "oolitic ironstones on mid-latitude shelves", "platform",
        "sedimentology; placement generated", iron)

    # -- Iapetus closure: arcs, docking, Caledonian collision ------------------
    tac = facing("Laurentia", ["Baltica", "Avalonia"], 200) & land
    col.deposit(cells(tac), "accreted arc", 465, 2.0,
                lambda i: "andesite" if noise[4][i] > 0.4 else "melange", "Taconic arc")
    col.intrude(cells(tac & (noise[4].reshape(NY, NX) > 0.6)), "granodiorite", 455.0,
                "accreted arc terrane")
    log(465, "Laurentia", "Taconic arc accreted to the Iapetan margin", "arc", "real history", tac)
    fl = facing("Laurentia", ["Baltica", "Avalonia"], 500) & ~tac & land
    col.deposit(cells(fl), "Taconic flysch", 450, 1.5,
                lambda i: "black shale" if noise[1][i] > 0.5 else "greywacke", "foreland basin")
    log(450, "Laurentia", "Taconic foreland basin (flysch)", "foreland", "real history", fl)

    av = blk("Avalonia") & land
    col.deposit(cells(av), "Ordovician arc", 460, 1.5, lambda i: "andesite", "Avalonian arc")
    dock = facing("Baltica", ["Avalonia"], 150) & land | facing("Avalonia", ["Baltica"], 150) & land
    col.metamorphose(cells(dock), 445.0, "avalonia-baltica suture")
    log(445, "Baltica/Avalonia", "Avalonia docks against Baltica (Tornquist suture)", "collision",
        "real history", dock)

    # Hirnantian glaciation where a block sat near the pole (~445 Ma)
    p445 = plat_at(445).reshape(NY, NX)
    glac = land & (p445 < -60)
    col.deposit(cells(glac), "glacial deposits", 445, 0.2, lambda i: "glacial diamictite",
                "Late Ordovician glaciation")
    log(445, "Gondwana", "Late Ordovician glaciation near the pole", "glacial",
        "real history; extent from paleolatitude", glac)

    # Caledonian collision: active at the fictional present
    cal = ((facing("Laurentia", ["Baltica", "Avalonia"], 300)
            | facing("Baltica", ["Laurentia"], 300)
            | facing("Avalonia", ["Laurentia"], 300)) & land)
    col.metamorphose(cells(cal), 430.0, "caledonian orogen")
    col.intrude(cells(cal & (noise[4].reshape(NY, NX) > 0.65)), "S-type granite", 425.0,
                "caledonian orogen")
    log(430, "Laurentia/Baltica/Avalonia", "Caledonian collision (ongoing at present)", "collision",
        "real history", cal)
    mol = (facing("Laurentia", ["Baltica", "Avalonia"], 650)
           | facing("Baltica", ["Laurentia"], 600)) & ~cal & land
    p430 = plat_at(430)
    col.deposit(cells(mol), "molasse", 432, 1.5,
                lambda i: terrestrial_lith(p430[i], 432, noise[1][i]), "Caledonian foreland")
    log(432, "Laurentia/Baltica", "Caledonian foreland molasse", "foreland", "real history", mol)

    # Gondwana's Panthalassic margin: Ross-Delamerian orogen then active arc
    act = land & (d_trench < 600)
    gpm = act & blk("Gondwana")
    col.metamorphose(cells(gpm), 500.0, "ross-delamerian belt")
    log(500, "Gondwana", "Ross-Delamerian orogen on the Panthalassic margin", "collision",
        "real history; placed on the trench-facing margin", gpm)
    col.deposit(cells(act), "accretionary complex", 440, 2.0,
                lambda i: "melange" if noise[4][i] > 0.5 else "greywacke", "active margin")
    col.intrude(cells(act & (noise[4].reshape(NY, NX) > 0.55)), "granodiorite", 435.0,
                "active arc")
    log(440, "all", "active-margin accretion and arc plutons next to trenches", "arc",
        "present trenches", act)

    # Silurian intracratonic basins: reefs and evaporites
    ib = land & (setting_name == "interior basin")
    col.deposit(cells(ib), "basin fill", 425, 2.0,
                lambda i: basin_lith(p430[i], 425, noise[3][i]), "intracratonic basin")
    log(425, "all", "intracratonic basin fill (reefs, evaporites where subtropical)", "basin",
        "present setting + paleolatitude", ib)

    collision_now = cal
    return block, col, events, collision_now, crust


# ---- erosion and the present surface ----------------------------------------
def unroof(col, land, elev, relief, setting_name, emerged, alluvial, river, endorheic,
           volcanic, LAT, block, seed=11, strahler=None):
    """Strip cover by erosion depth; add present-day surface units."""
    ero_noise = smooth_noise(seed, 5).ravel()
    e = elev.ravel()
    rf = relief.ravel()
    st = setting_name.ravel()
    out = {k: np.full(NY * NX, None, object) for k in
           ("surface_lith", "surface_unit", "basement_lith", "basement_province", "surface_event")}
    num = {k: np.full(NY * NX, np.nan) for k in
           ("surface_age", "basement_age", "cover_km", "erosion_km")}
    strat = []
    for i in col.cells:
        depth = 1.0 * max(e[i], 0) + 3.0 * rf[i] + 0.8 * (ero_noise[i] - 0.5)
        if st[i] == "orogen":
            depth += 6.0
        elif st[i] == "volcanic arc":
            depth += 1.5
        uplifted = st[i] in ("orogen", "volcanic arc")
        if emerged.flat[i] and not uplifted:
            depth = min(depth, 0.1)  # newly emerged sea floor: barely touched
        depth = max(depth, 0.0)
        num["erosion_km"][i] = depth
        units = [dict(u) for u in col.units[i]]
        remaining = depth
        for u in reversed(units):  # top down
            take = min(u["thick"], remaining)
            u["eroded"] = take
            remaining -= take
        kept = [u for u in units if u["thick"] - u["eroded"] > 1e-6]
        cover = sum(u["thick"] - u["eroded"] for u in kept)
        top = []
        if emerged.flat[i] and not uplifted:
            top.append(dict(unit="emerged shelf deposits", age=PRESENT_MA, thick=0.05,
                            lith="limestone" if abs(LAT.flat[i]) < 30 else "shale",
                            event="present emergence", eroded=0.0))
        if volcanic.flat[i]:
            top.append(dict(unit="active volcanics", age=PRESENT_MA, thick=0.5,
                            lith="andesite", event="active arc", eroded=0.0))
        if endorheic.flat[i]:
            top.append(dict(unit="playa deposits", age=PRESENT_MA, thick=0.05,
                            lith="evaporite", event="closed basin", eroded=0.0))
        elif alluvial.flat[i] or (river.flat[i] and strahler is not None and strahler.flat[i] >= 2):
            top.append(dict(unit="alluvium", age=PRESENT_MA, thick=0.05, lith="alluvium",
                            event="river deposition", eroded=0.0))
        stack = kept + top
        b = col.basement.get(i, ("granite-gneiss", 2000.0, "undifferentiated basement"))
        out["basement_lith"][i], num["basement_age"][i], out["basement_province"][i] = b
        if stack:
            s = stack[-1]
            out["surface_lith"][i], out["surface_unit"][i] = s["lith"], s["unit"]
            num["surface_age"][i], out["surface_event"][i] = s["age"], s["event"]
        else:
            out["surface_lith"][i], out["surface_unit"][i] = b[0], "basement"
            num["surface_age"][i], out["surface_event"][i] = b[1], b[2]
        num["cover_km"][i] = cover + sum(u["thick"] for u in top)
        # record every unit, including those erosion removed entirely
        full = units + top
        for k, u in enumerate(reversed(full)):
            strat.append((int(i), k, u["unit"], u["lith"], float(u["age"]),
                          float(u["age"] - PRESENT_MA), round(float(u["thick"] - u["eroded"]), 3),
                          round(float(u["eroded"]), 3), u["event"]))
        strat.append((int(i), len(full), "basement", b[0], float(b[1]),
                      float(b[1] - PRESENT_MA), None, 0.0, b[2]))
    return out, num, strat
