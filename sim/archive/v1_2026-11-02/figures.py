"""
Summary figures built from a run's output files.

final.png (2x2): political map | peoples by density (with dragons)
                 peoples in flat colours, trading posts, trade flows | major
                 wars over time by landmass group
wars.png:        major wars over time on each landmass, by the peoples who
                 fought them, with large states that collapsed in revolt

The first two panels are the simulator's own render (final_maps.png). The
rest is drawn here from final_state.npz, relations.csv, wars.csv,
revolts.csv, polities.csv and posts.csv (or, for runs made before
posts.csv existed, the trading-post events still standing at the end).

Run on finished runs:
  ~/.venvs/worldsim/bin/python figures.py runs/batch1_seed10[1-7]
"""
import collections
import csv
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import landmasses as LM  # noqa: E402

SCALE = 2
BG = (16, 18, 24)
BGF = tuple(v / 255 for v in BG)
INK, INK2, GRID = "#e6e6e6", "#a8a8a8", "#2c2f38"
# categorical slots, dark-surface steps (dataviz reference palette)
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181",
          "#008300", "#9085e9", "#e66767"]
GROUP_ORDER = ["S", "W", "N", "E"]
PANELS = [("S", ["S"]), ("W1", ["W1"]), ("W2", ["W2"]),
          ("W3-W5", ["W3", "W4", "W5"]), ("N1", ["N1"]),
          ("N2-N4", ["N2", "N3", "N4"]), ("E1", ["E1"])]
BIN = 250
# major war (C, 2026-11-01): both sides held 5+ cities at the start and
# 2+ cities were taken, or a side that held 10+ cities fell. A revolt
# collapse: one state loses 5+ cities and 40%+ of its cities to revolts
# in one tick.
MAJOR_MIN, MAJOR_CAPS, MAJOR_FELL = 5, 2, 10
COLLAPSE_N, COLLAPSE_SHARE = 5, 0.4
TOP_FLOWS = 12

_W = None


def world():
    global _W
    if _W is None:
        import worldsim
        _W = worldsim.World()
    return _W


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


class Run:
    def __init__(self, run):
        self.dir = run
        self.W = W = world()
        meta = json.load(open(os.path.join(run, "run.json")))
        self.P = meta["peoples"]
        self.keys = [p["key"] for p in self.P]
        self.col = {p["key"]: tuple(p["color"]) for p in self.P}
        self.years = meta["years"]
        F = np.load(os.path.join(run, "final_state.npz"))
        self.pop, self.ppl, self.pol = F["pop"], F["people"], F["polity"]
        self.mppl = F["minority_people"]
        self.pols = {int(r["id"]): r for r in rows(os.path.join(run, "polities.csv"))}
        self.cell_at = lambda lon, lat: int(np.argmin((W.lon - lon) ** 2 +
                                                      (W.lat - lat) ** 2))

    def lm_of_state(self, i):
        r = self.pols.get(int(i))
        if r is None:
            return -1
        return int(self.W.landmass[self.cell_at(float(r["capital_lon"]),
                                                float(r["capital_lat"]))])

    def xy(self, cell):
        W = self.W
        return (W.col[cell] + 0.5) * SCALE, (W.row[cell] - W.r0 + 0.5) * SCALE


# ---------------------------------------------------------------- trade

POST_EV = re.compile(r"\s*(\d+)\s+trade\s+P(\d+)\((\w+)\) plants a trading "
                     r"post at ([-+\d.]+),([-+\d.]+) in P(\d+)\((\w+)\)")


def live_posts(R):
    """(planter state, host state, city cell) for posts standing at the end."""
    p = os.path.join(R.dir, "posts.csv")
    if os.path.exists(p):
        return [(int(r["planter"]), int(r["host"]), int(r["city"]))
                for r in rows(p)]
    posts = {}
    for line in open(os.path.join(R.dir, "events.txt")):
        m = POST_EV.match(line)
        if m:
            o, h = int(m.group(2)), int(m.group(6))
            c = R.cell_at(float(m.group(4)), float(m.group(5)))
            posts[(min(o, h), max(o, h))] = (o, h, c)
    out = []
    for o, h, c in posts.values():
        po = R.pols.get(o)
        if po is None or po["ended"] or int(R.pol[c]) != h:
            continue
        if R.mppl[c] < 0 or R.keys[R.mppl[c]] != po["people"]:
            continue
        out.append((o, h, c))
    return out


def trade_flows(R, posts):
    """Strongest trade links between (landmass, people) groups at the last
    frame, with the direction merchants travel where posts show one."""
    rel = rows(os.path.join(R.dir, "relations.csv"))
    if not rel:
        return {}, []
    yl = max(int(r["year"]) for r in rel)
    flow = collections.defaultdict(float)
    for r in rel:
        if int(r["year"]) != yl or num(r["tie"]) <= 0:
            continue
        a = (int(r["landmass_a"]), r["people_a"])
        b = (int(r["landmass_b"]), r["people_b"])
        if a != b:
            flow[tuple(sorted((a, b)))] += num(r["tie"])
    dirn = collections.Counter()
    for o, h, c in posts:
        a = (R.lm_of_state(o), R.pols[o]["people"])
        b = (int(R.W.landmass[c]), R.keys[R.ppl[c]] if R.ppl[c] >= 0 else "")
        dirn[(a, b)] += 1
    top = sorted(flow.items(), key=lambda x: -x[1])[:TOP_FLOWS]
    nodes = {}
    W = R.W
    for (a, b), _ in top:
        for lm, k in (a, b):
            if (lm, k) in nodes or k not in R.keys:
                continue
            m = (W.landmass == lm) & (R.ppl == R.keys.index(k)) & (R.pop > 0)
            if not m.any():
                continue
            idx = np.nonzero(m)[0]
            c = (W.xyz[idx] * R.pop[idx, None]).sum(0)
            nodes[(lm, k)] = int(idx[np.argmax(W.xyz[idx] @ c)])
    out = []
    for (a, b), t in top:
        if a in nodes and b in nodes:
            out.append((a, b, t, dirn[(a, b)], dirn[(b, a)]))
    return nodes, out


def flat_peoples(R):
    W = R.W
    from worldsim import NY, NX
    img = W.base.astype(float).copy()
    land = W.land2
    img[land] = 0.35 * img[land] + 0.65 * np.array([92, 92, 88])
    occ = (R.ppl >= 0) & (R.pop > 0)
    lab = -np.ones((NY, NX), int)
    lab[W.row[occ], W.col[occ]] = R.ppl[occ]
    cols = np.array([R.col[k] for k in R.keys], float)
    img[W.row[occ], W.col[occ]] = cols[R.ppl[occ]]
    edge = np.zeros_like(land)
    edge[:-1] |= (lab[:-1] != lab[1:]) & (lab[:-1] >= 0) & (lab[1:] >= 0)
    edge[:, :-1] |= (lab[:, :-1] != lab[:, 1:]) & (lab[:, :-1] >= 0) & \
        (lab[:, 1:] >= 0)
    img[edge] *= 0.55
    im = img[W.r0:W.r1].clip(0, 255).astype(np.uint8)
    return np.repeat(np.repeat(im, SCALE, 0), SCALE, 1)


def trade_panel(R):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import patheffects as pe
    from matplotlib.patches import FancyArrowPatch
    from matplotlib.lines import Line2D
    img = flat_peoples(R)
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=(0, w, h, 0), interpolation="nearest")
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    posts = live_posts(R)
    nodes, flows = trade_flows(R, posts)
    tmax = max([f[2] for f in flows], default=1)
    halo = [pe.withStroke(linewidth=4.5, foreground="black")]
    for a, b, t, ab, ba in flows:
        pa, pb = R.xy(nodes[a]), R.xy(nodes[b])
        if ab >= 2 * max(ba, 1) or (ab and not ba):
            st, p0, p1 = "-|>", pa, pb
        elif ba >= 2 * max(ab, 1) or (ba and not ab):
            st, p0, p1 = "-|>", pb, pa
        elif ab or ba:
            st, p0, p1 = "<|-|>", pa, pb
        else:
            st, p0, p1 = "-", pa, pb
        lw = 1.2 + 4.5 * t / tmax
        ax.add_patch(FancyArrowPatch(
            p0, p1, arrowstyle=st, mutation_scale=10 + 2 * lw,
            connectionstyle="arc3,rad=0.18", color="white", lw=lw,
            shrinkA=4, shrinkB=4, path_effects=halo, zorder=4, alpha=0.95))
    for (lm, k), c in nodes.items():
        x, y = R.xy(c)
        ax.scatter([x], [y], s=46, c=[np.array(R.col[k]) / 255],
                   edgecolors="black", linewidths=1.2, zorder=6)
    if posts:
        xs, ys, cs = [], [], []
        for o, hh, c in posts:
            x, y = R.xy(c)
            xs.append(x)
            ys.append(y)
            cs.append(np.array(R.col[R.pols[o]["people"]]) / 255)
        ax.scatter(xs, ys, marker="*", s=95, c=cs, edgecolors="black",
                   linewidths=0.8, zorder=5)
    leg = [Line2D([], [], marker="*", ls="", ms=11, mfc="#dddddd",
                  mec="black", label=f"trading post ({len(posts)}), "
                  "coloured by merchants' people"),
           Line2D([], [], color="white", lw=3, label=f"{len(flows)} strongest "
                  "trade links between peoples or landmasses; width = trade"),
           Line2D([], [], color="white", lw=1.5, marker=">", ms=7,
                  label="arrowhead: where merchants' posts point")]
    lg = ax.legend(handles=leg, loc="lower left", fontsize=9.5,
                   facecolor=BGF, edgecolor="#555555",
                   labelcolor=INK, framealpha=0.9)
    lg.set_zorder(10)
    fig.canvas.draw()
    out = Image.frombuffer("RGBA", fig.canvas.get_width_height(),
                           fig.canvas.buffer_rgba()).convert("RGB")
    plt.close(fig)
    return out


# ----------------------------------------------------------------- wars

def pair_label(R, a, b):
    order = {k: i for i, k in enumerate(R.keys)}
    a, b = sorted((a, b), key=lambda k: order.get(k, 99))
    return f"{a}-{b}"


def major_wars(R):
    out = []
    for r in rows(os.path.join(R.dir, "wars.csv")):
        ca, cd = num(r["cities_att"]), num(r["cities_dfn"])
        why = r["why"]
        fell = ("defender fell" in why and cd >= MAJOR_FELL) or \
               ("attacker fell" in why and ca >= MAJOR_FELL)
        if (min(ca, cd) >= MAJOR_MIN and num(r["captures"]) >= MAJOR_CAPS) \
                or fell:
            out.append(dict(year=int(r["start"]),
                            lm=LM.code(r["landmass_dfn"]),
                            pair=pair_label(R, r["people_att"], r["people_dfn"])))
    return out


def collapses(R):
    g = collections.defaultdict(list)
    for r in rows(os.path.join(R.dir, "revolts.csv")):
        g[(r["state"], r["year"])].append(r)
    out = []
    for (s, y), rr in g.items():
        n = sum(int(r["cities_taken"]) for r in rr)
        left = min(int(r["cities_left"]) for r in rr)
        if n >= COLLAPSE_N and n / max(n + left, 1) >= COLLAPSE_SHARE:
            reb = collections.Counter(r["people_rebels"] for r in rr).most_common(1)[0][0]
            out.append(dict(year=int(y), lm=LM.code(rr[0]["landmass"]),
                            pair=pair_label(R, rr[0]["people_ruler"], reb), n=n))
    return out


def end_labels(ax, items, x, ymax, gap=0.075):
    """Direct labels at line ends, pushed apart so they do not overlap."""
    items = sorted(items, key=lambda t: t[0])
    d = gap * max(ymax, 1)
    ys = []
    for y, _ in items:
        ys.append(max(y, ys[-1] + d) if ys else y)
    for (_, t), y in zip(items, ys):
        ax.text(x, y, t, color=INK, fontsize=8.5, va="center")


def x_start(evs):
    """Start plots a little before the first major war (to the 1000)."""
    if not evs:
        return 0
    return max(0, (min(e["year"] for e in evs) - 250) // 1000 * 1000)


def binned(evs, years):
    edges = np.arange(0, years + BIN, BIN)
    h, _ = np.histogram([e["year"] for e in evs], bins=edges)
    return edges[:-1] + BIN / 2, h


def style(ax, fig_dark=True):
    ax.set_facecolor(BGF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#555555")
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def war_panel(R, size=(1440, 504)):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    mw = major_wars(R)
    fig = plt.figure(figsize=(size[0] / 100, size[1] / 100), dpi=100,
                     facecolor=BGF)
    ax = fig.add_axes([0.06, 0.12, 0.84, 0.74])
    style(ax)
    ymax, ends = 0, []
    for i, g in enumerate(GROUP_ORDER):
        ev = [e for e in mw if e["lm"].startswith(g)]
        x, h = binned(ev, R.years)
        ymax = max(ymax, h.max(initial=0))
        ax.plot(x, h, color=SERIES[i], lw=2, label=f"{g} ({len(ev)})")
        ends.append((h[-1], g))
    end_labels(ax, ends, x[-1] + 60, ymax)
    ax.set_xlim(x_start(mw), R.years + 250)
    ax.set_ylim(0, max(ymax * 1.1, 1))
    ax.set_xlabel("year", color=INK2, fontsize=10)
    ax.set_ylabel(f"major wars started per {BIN} yrs", color=INK2, fontsize=10)
    fig.text(0.06, 0.93, f"Major wars by landmass group ({len(mw)} in all)",
             color=INK, fontsize=14)
    fig.text(0.06, 0.885, f"both sides {MAJOR_MIN}+ cities and "
             f"{MAJOR_CAPS}+ taken, or a {MAJOR_FELL}+ city state fell; "
             "placed where the defender's capital stood. "
             "S south, W west, N north, E east (landmass key)",
             color=INK2, fontsize=9.5)
    lg = ax.legend(loc="upper left", fontsize=10, frameon=False,
                   labelcolor=INK)
    fig.canvas.draw()
    out = Image.frombuffer("RGBA", fig.canvas.get_width_height(),
                           fig.canvas.buffer_rgba()).convert("RGB")
    plt.close(fig)
    return out


def wars_figure(R, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    mw, cl = major_wars(R), collapses(R)
    x0 = x_start(mw + cl)
    # pairs shown: the top 4 on each panel; colours fixed per pair by
    # overall count, so a pair has one colour on every panel
    top = {}
    for name, codes in PANELS:
        c = collections.Counter(e["pair"] for e in mw if e["lm"] in codes)
        top[name] = [p for p, _ in c.most_common(4)]
    allc = collections.Counter(e["pair"] for e in mw)
    shown = sorted({p for v in top.values() for p in v}, key=lambda p: -allc[p])
    sty = {p: (SERIES[i % 8], "-" if i < 8 else "--")
           for i, p in enumerate(shown)}
    fig, axs = plt.subplots(4, 2, figsize=(14, 13), dpi=100,
                            facecolor=BGF, sharex=True)
    axs = axs.ravel()
    for ax, (name, codes) in zip(axs, PANELS):
        style(ax)
        ev = [e for e in mw if e["lm"] in codes]
        x, tot = binned(ev, R.years)
        ax.plot(x, tot, color="#777777", lw=1.2, label="all major wars")
        top_y = tot.max(initial=0)
        ends = []
        for p in top[name]:
            _, h = binned([e for e in ev if e["pair"] == p], R.years)
            c, ls = sty[p]
            ax.plot(x, h, color=c, ls=ls, lw=2)
            ends.append((h[-1], p))
        end_labels(ax, ends, x[-1] + 60, top_y)
        cc = [e for e in cl if e["lm"] in codes]
        if cc:
            ax.scatter([e["year"] for e in cc], [-0.06 * max(top_y, 1)] * len(cc),
                       marker="^", s=[10 + 3 * e["n"] for e in cc],
                       c="#dddddd", edgecolors="none", alpha=0.7, clip_on=False)
        pc = collections.Counter(e["pair"] for e in ev).most_common(3)
        sub = ", ".join(f"{p} {n}" for p, n in pc)
        ax.set_title(f"{name}: {len(ev)} major wars ({sub}); "
                     f"{len(cc)} revolt collapses", color=INK, fontsize=10.5,
                     loc="left")
        ax.set_ylim(-0.1 * max(top_y, 1), max(top_y * 1.12, 1))
        ax.set_xlim(x0, R.years + 700)
    ax = axs[len(PANELS)]
    ax.axis("off")
    hand = [Line2D([], [], color=sty[p][0], ls=sty[p][1], lw=2,
                   label=f"{p} ({allc[p]})") for p in shown]
    hand += [Line2D([], [], color="#777777", lw=1.2, label="all major wars"),
             Line2D([], [], marker="^", ls="", color="#dddddd", ms=8,
                    label="large state collapses in revolt (size = cities lost)")]
    ax.legend(handles=hand, loc="center", ncol=2, fontsize=9.5, frameon=False,
              labelcolor=INK, title="pairs of peoples (major wars in run)",
              title_fontproperties={"size": 10.5}).get_title().set_color(INK)
    for a in axs[-2:]:
        a.set_xlabel("year", color=INK2)
    fig.suptitle(f"{os.path.basename(R.dir)}: major wars per {BIN} yrs by "
                 "landmass and peoples fighting (both sides "
                 f"{MAJOR_MIN}+ cities and {MAJOR_CAPS}+ taken, or a "
                 f"{MAJOR_FELL}+ city state fell)", color=INK, fontsize=12,
                 x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


# -------------------------------------------------------------- compose

def compose(run):
    """Rewrite final.png as the 2x2 figure and write wars.png."""
    R = Run(run)
    W = R.W
    src = os.path.join(run, "final_maps.png")
    if not os.path.exists(src):
        os.replace(os.path.join(run, "final.png"), src)
    im = Image.open(src).convert("RGB")
    ph = (W.r1 - W.r0) * SCALE
    hdr = im.size[1] - 2 * ph - 6
    w = im.size[0]
    P1 = im.crop((0, hdr, w, hdr + ph))
    P2 = im.crop((0, hdr + ph + 6, w, hdr + 2 * ph + 6))
    P3 = trade_panel(R).resize((w, ph))
    P4 = war_panel(R, (w, ph))
    out = Image.new("RGB", (2 * w + 6, hdr + 2 * ph + 6), BG)
    out.paste(im.crop((0, 0, w, hdr)), (0, 0))
    out.paste(P1, (0, hdr))
    out.paste(P2, (w + 6, hdr))
    out.paste(P3, (0, hdr + ph + 6))
    out.paste(P4, (w + 6, hdr + ph + 6))
    from PIL import ImageDraw
    import worldsim
    d = ImageDraw.Draw(out)
    f = worldsim.font(15)
    for (x, y), t in (((w - 12, hdr + 8), "states"),
                      ((2 * w - 6, hdr + 8), "peoples by density; red: dragons"),
                      ((w - 12, hdr + ph + 14), "peoples and trade")):
        d.text((x, y), t, fill=(240, 240, 240), font=f, anchor="ra",
               stroke_width=3, stroke_fill=(0, 0, 0))
    out.save(os.path.join(run, "final.png"))
    wars_figure(R, os.path.join(run, "wars.png"))


if __name__ == "__main__":
    for r in sys.argv[1:]:
        compose(r)
        print("wrote", os.path.join(r, "final.png"), "and wars.png")
