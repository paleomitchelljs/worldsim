"""Maps and plots."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


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


def render(sim, scale=2):
    W = sim.W
    r0, r1 = W.r0, W.r1
    occ = sim.cul >= 0
    dens = np.where(occ, sim.pop / W.area, 0)
    a = np.clip(np.log10(1 + dens) / np.log10(1 + 60), 0.4, 1)

    # political map
    pol = W.base.astype(float).copy()
    pid = sim.cell_pol
    pc = np.zeros((sim.next_pid, 3))
    for k, p in sim.polities.items():
        pc[k] = p["col"]
    m = pid >= 0
    rr, cc = W.row, W.col
    tribal = occ & ~m
    col_t = sim.colors[np.maximum(sim.cul, 0)].astype(float)
    pol[rr[tribal], cc[tribal]] = 0.6 * pol[rr[tribal], cc[tribal]] + \
        0.4 * col_t[tribal]
    pol[rr[m], cc[m]] = 0.15 * pol[rr[m], cc[m]] + 0.85 * pc[pid[m]]
    lab = -np.ones((NY, NX), int)
    lab[rr, cc] = np.where(m, pid, -2)
    lab[~W.land2] = -3
    bm = borders_mask(lab) & W.land2 & (lab >= 0)
    pol[bm] = pol[bm] * 0.25

    # peoples map
    eth = W.base.astype(float).copy()
    eth[rr[occ], cc[occ]] = (1 - a[occ, None]) * eth[rr[occ], cc[occ]] + \
        a[occ, None] * col_t[occ]

    def panel(img):
        im = img[r0:r1].clip(0, 255).astype(np.uint8)
        im = np.repeat(np.repeat(im, scale, 0), scale, 1)
        return Image.fromarray(im)

    P1, P2 = panel(pol), panel(eth)
    for P, dots in ((P1, True), (P2, True)):
        d = ImageDraw.Draw(P)
        for cell, rec in sim.cities.items():
            s = sim.city_size.get(cell, 0)
            rad = 1 + 1.2 * math.log10(1 + s / 2000)
            x = (W.col[cell] + 0.5) * scale
            y = (W.row[cell] - r0 + 0.5) * scale
            p = sim.polities.get(rec["polity"])
            cap = p is not None and p["capital"] == cell
            d.ellipse([x - rad, y - rad, x + rad, y + rad],
                      fill=(255, 255, 255) if cap else (235, 230, 215),
                      outline=(0, 0, 0))
            if cap and p["n_cells"] > 250:
                d.ellipse([x - rad - 3, y - rad - 3, x + rad + 3, y + rad + 3],
                          outline=(255, 255, 255), width=2)
    d = ImageDraw.Draw(P2)
    for h, al in zip(sim.dhome, sim.dally):
        x = (W.col[h] + 0.5) * scale
        y = (W.row[h] - r0 + 0.5) * scale
        d.rectangle([x - 1, y - 1, x + 1, y + 1],
                    fill=(255, 215, 0) if al >= 0 else (120, 0, 0))
    d = ImageDraw.Draw(P1)
    f = font(13)
    live = sorted([p for p in sim.polities.values() if p["ended"] is None],
                  key=lambda p: -p["n_cells"])[:10]
    for p in live:
        if p["n_cells"] < 150:
            break
        c = p["capital"]
        x = (W.col[c] + 0.5) * scale + 6
        y = (W.row[c] - r0 + 0.5) * scale - 6
        d.text((x, y), sim.pname(p["id"]), fill=(255, 255, 255), font=f,
               stroke_width=2, stroke_fill=(0, 0, 0))

    w, h = P1.size
    rows = (sim.nP + 4) // 5
    hdr = 14 + 38 * rows
    out = Image.new("RGB", (w, 2 * h + hdr + 6), (16, 18, 24))
    out.paste(P1, (0, hdr))
    out.paste(P2, (0, hdr + h + 6))
    d = ImageDraw.Draw(out)
    d.text((12, 8), f"Year {sim.year}", fill=(240, 240, 240), font=font(24))
    ps = sim.people_summary()
    for i, k in enumerate(sim.keys):
        x = 150 + 225 * (i % 5)
        y0 = 38 * (i // 5)
        d.rectangle([x, 12 + y0, x + 14, 26 + y0], fill=tuple(sim.colors[i]))
        d.text((x + 20, 8 + y0), f"{sim.P[i]['label']}",
               fill=(230, 230, 230), font=font(13))
        d.text((x + 20, 26 + y0), f"{ps[i]['pop']/1e6:5.2f}M "
               f"{ps[i]['nlin']} lin {ps[i]['stage']}",
               fill=(170, 170, 170), font=font(12))
    nl = sum(1 for p in sim.polities.values() if p["ended"] is None)
    d.text((12, 40), f"states {nl}", fill=(230, 230, 230), font=font(13))
    d.text((12, 58), f"wars {len(sim.wars)}", fill=(230, 230, 230),
           font=font(13))
    return out


def legacy_map(sim, scale=2):
    """Where cities stood and how far the great states once reached."""
    W = sim.W
    r0, r1 = W.r0, W.r1
    img = W.base.astype(float) * 0.55
    im = Image.fromarray(np.repeat(np.repeat(
        img[r0:r1].astype(np.uint8), scale, 0), scale, 1))
    d = ImageDraw.Draw(im, "RGBA")
    greats = sorted([p for p in sim.polities.values()
                     if p["peak_mask"] is not None],
                    key=lambda p: -p["peak_cells"])[:14]
    f = font(13)
    for p in greats:
        msk = np.zeros((NY, NX), bool)
        msk[W.row[p["peak_mask"]], W.col[p["peak_mask"]]] = True
        edge = msk & ~ndimage.binary_erosion(msk)
        col = tuple(int(v) for v in sim.colors[p["culture"]])
        ys, xs = np.nonzero(msk[r0:r1])
        for y, x in zip(ys, xs):
            d.rectangle([x * scale, y * scale, x * scale + scale - 1,
                         y * scale + scale - 1], fill=col + (38,))
        ys, xs = np.nonzero(edge[r0:r1])
        for y, x in zip(ys, xs):
            d.rectangle([x * scale, y * scale, x * scale + scale - 1,
                         y * scale + scale - 1], fill=col + (230,))
    order = np.argsort(sim.city_years)
    for cell in order[sim.city_years[order] > 0]:
        yrs = sim.city_years[cell]
        rad = 1 + 1.3 * math.log10(1 + sim.city_peak[cell] / 2000)
        al = int(np.clip(70 + yrs / 8, 70, 255))
        x = (W.col[cell] + 0.5) * scale
        y = (W.row[cell] - r0 + 0.5) * scale
        rc = [r for r in sim.city_hist if r["cell"] == cell]
        c = sim.colors[rc[-1]["culture"]] if rc else (255, 255, 255)
        d.ellipse([x - rad, y - rad, x + rad, y + rad],
                  fill=tuple(int(v) for v in c) + (al,),
                  outline=(255, 255, 255, al))
    placed = []
    for p in greats:
        msk_cells = p["peak_mask"]
        cy = (np.median(W.row[msk_cells]) - r0) * scale
        cx = np.median(W.col[msk_cells]) * scale
        if any(abs(cx - x) < 150 and abs(cy - y) < 18 for x, y in placed):
            continue
        placed.append((cx, cy))
        end = p["ended"] if p["ended"] is not None else "now"
        d.text((cx, cy),
               f"{sim.pname(p['id'])} {p['founded']}-{end}",
               fill=(255, 255, 255, 255), font=f, stroke_width=2,
               stroke_fill=(0, 0, 0, 255))
    hdr = Image.new("RGB", (im.size[0], im.size[1] + 40), (16, 18, 24))
    hdr.paste(im, (0, 40))
    dd = ImageDraw.Draw(hdr)
    dd.text((12, 8), f"Legacy after {sim.year} years: cities (size = peak, "
            f"opacity = years inhabited) and the peak extent of the "
            f"{len(greats)} largest states", fill=(235, 235, 235),
            font=font(16))
    return hdr


def population_plot(sim, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = [s["year"] for s in sim.ts]
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    ys = [[s[f"pop_{k}"] / 1e6 for s in sim.ts] for k in sim.keys]
    cols = sim.colors / 255
    ax[0].stackplot(yrs, ys, colors=cols,
                    labels=[f"{k} {p['label']}" for k, p in
                            zip(sim.keys, sim.P)])
    ax[0].set_ylabel("population (M)")
    ax[0].legend(loc="upper left", fontsize=8, frameon=False)
    for i, k in enumerate(sim.keys):
        ax[1].plot(yrs, [s[f"cities_{k}"] for s in sim.ts], color=cols[i])
    ax[1].set_ylabel("cities")
    ax[2].plot(yrs, [s["n_polities"] for s in sim.ts], color="k",
               label="states")
    ax2 = ax[2].twinx()
    ax2.plot(yrs, [s["largest_polity_Mkm2"] for s in sim.ts],
             color="tab:red", label="largest state")
    ax[2].set_ylabel("number of states")
    ax2.set_ylabel("largest state (M km2)", color="tab:red")
    ax[2].set_xlabel("year")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def trait_plot(sim, path, traits=("violence", "tolerance")):
    """Population-weighted mean of each trait over time: world (black)
    and per people."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = np.array([s["year"] for s in sim.ts])
    cols = sim.colors / 255
    fig, ax = plt.subplots(len(traits), 1, figsize=(11, 4 * len(traits)),
                           sharex=True)
    for a, t in zip(np.atleast_1d(ax), traits):
        for i, k in enumerate(sim.keys):
            y = np.array([np.nan if s[f"{t}_{k}"] is None else s[f"{t}_{k}"]
                          for s in sim.ts])
            a.plot(yrs, y, color=cols[i], lw=1.2, label=sim.P[i]["label"])
        a.plot(yrs, [s[f"{t}_world"] for s in sim.ts], color="k", lw=2.6,
               label="world")
        a.set_ylabel(f"mean {t}")
        a.set_ylim(0, 1)
        a.spines[["top", "right"]].set_visible(False)
    np.atleast_1d(ax)[0].legend(loc="upper left", fontsize=8, ncol=6,
                                frameon=False)
    np.atleast_1d(ax)[-1].set_xlabel("year")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def lineage_map(sim, scale=2):
    """Final map of living lineages: hue = people, shade = lineage; thin
    lines separate lineages, thick lines separate peoples."""
    W = sim.W
    r0, r1 = W.r0, W.r1
    img = W.base.astype(float).copy()
    occ = sim.lin >= 0
    rr, cc = W.row[occ], W.col[occ]
    img[rr, cc] = 0.2 * img[rr, cc] + 0.8 * sim.Lcol[sim.lin[occ]]
    lab = -np.ones((NY, NX), int)
    lab[W.row, W.col] = sim.lin
    peo = -np.ones((NY, NX), int)
    peo[W.row, W.col] = sim.cul
    bl = borders_mask(lab) & (lab >= 0)
    bp = borders_mask(peo) & (peo >= 0)
    img[bl] *= 0.6
    img[bp] *= 0.15
    im = img[r0:r1].clip(0, 255).astype(np.uint8)
    im = Image.fromarray(np.repeat(np.repeat(im, scale, 0), scale, 1))
    d = ImageDraw.Draw(im)
    occi = np.nonzero(occ)[0]
    Lpop = np.bincount(sim.lin[occi], weights=sim.pop[occi], minlength=sim.nL)
    for L in np.argsort(Lpop)[::-1][:40]:
        if Lpop[L] < 5e5:
            break
        cells = occi[sim.lin[occi] == L]
        y = (np.median(W.row[cells]) - r0) * scale
        x = np.median(W.col[cells]) * scale
        d.text((x, y), sim.lname(L), fill=(255, 255, 255), font=font(12),
               stroke_width=2, stroke_fill=(0, 0, 0))
    out = Image.new("RGB", (im.size[0], im.size[1] + 40), (16, 18, 24))
    out.paste(im, (0, 40))
    ImageDraw.Draw(out).text(
        (12, 8), f"Lineages in year {sim.year} ({int((Lpop > 0).sum())} "
        f"living): hue = people, shade = lineage", fill=(235, 235, 235),
        font=font(16))
    return out
