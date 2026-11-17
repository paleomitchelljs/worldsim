"""
Summary figures built from a run's output files.

final.png (2x2): political map | peoples by density (with dragons)
                 peoples in flat colours, trading posts, trade flows | major
                 wars over time by landmass group
wars.png:        major wars over time on each landmass, by the peoples who
                 fought them, with large states that collapsed in revolt
trade.png:       the peoples-and-trade panel alone, full size
war01.png ...:   the most important wars, one map each (needs history.npz)
tradewars.gif:   trade links and wars every 100 years (needs history.npz)

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
import math
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


def flat_peoples(R, ppl=None, pop=None, outline=()):
    """Peoples in flat colours (the final state, or the given arrays);
    outline: (cell mask, rgb) pairs drawn as state borders."""
    W = R.W
    from worldsim import NY, NX
    ppl = R.ppl if ppl is None else ppl
    pop = R.pop if pop is None else pop
    img = W.base.astype(float).copy()
    land = W.land2
    img[land] = 0.35 * img[land] + 0.65 * np.array([92, 92, 88])
    occ = (ppl >= 0) & (pop > 0)
    lab = -np.ones((NY, NX), int)
    lab[W.row[occ], W.col[occ]] = ppl[occ]
    cols = np.array([R.col[k] for k in R.keys], float)
    img[W.row[occ], W.col[occ]] = cols[ppl[occ]]
    edge = np.zeros_like(land)
    edge[:-1] |= (lab[:-1] != lab[1:]) & (lab[:-1] >= 0) & (lab[1:] >= 0)
    edge[:, :-1] |= (lab[:, :-1] != lab[:, 1:]) & (lab[:, :-1] >= 0) & \
        (lab[:, 1:] >= 0)
    img[edge] *= 0.55
    im = img[W.r0:W.r1].clip(0, 255).astype(np.uint8)
    im = np.repeat(np.repeat(im, SCALE, 0), SCALE, 1)
    for m, rgb in outline:
        g = np.zeros((NY, NX), bool)
        g[W.row[m], W.col[m]] = True
        g = np.repeat(np.repeat(g[W.r0:W.r1], SCALE, 0), SCALE, 1)
        nb = [np.roll(g, 1, 0), np.roll(g, -1, 0), np.roll(g, 1, 1),
              np.roll(g, -1, 1)]
        # the mask's rim in colour, the ring just outside it in black
        im[~g & (nb[0] | nb[1] | nb[2] | nb[3])] = 0
        im[g & ~(nb[0] & nb[1] & nb[2] & nb[3])] = rgb
    return im


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


# --------------------------------------------------- war and trade history
# From history.npz (a map snapshot every HIST_EVERY ticks; runs from
# 2026-11-04 on). war01.png ...: the WAR_MAPS most important wars, each on
# the peoples map at the snapshot nearest its start, the two states
# outlined, a line between the capitals in two halves whose widths follow
# each side's cities, and a zoomed inset when the war is small. tradewars.gif: every snapshot, the TOP_FLOWS_GIF strongest trade
# links and every war fought since the previous snapshot, one line per pair
# of states: the GIF_MAJOR most important pairs as in the war maps (borders
# and start years for the GIF_OUTLINE first), the rest as faint lines.
# Importance (C): (cities of the smaller side at the start) x (1 + cities
# captured), so a clash of powers outranks an empire swallowing a city;
# ties broken by both sides' cities.
WAR_MAPS, TOP_FLOWS_GIF, GIF_OUTLINE, GIF_MAJOR = 24, 16, 8, 20
ATT, DFN = (255, 77, 77), (255, 200, 51)


class Hist:
    def __init__(self, run):
        H = np.load(os.path.join(run, "history.npz"))
        self.year = H["year"]
        self.ppl, self.pop, self.pol = H["people"], H["pop"], H["polity"]
        self.st = {}
        for t, i, c, p, n in zip(H["st_t"], H["st_id"], H["st_cap"],
                                 H["st_people"], H["st_cities"]):
            self.st.setdefault(int(t), {})[int(i)] = (int(c), int(p), int(n))
        self.ties = collections.defaultdict(list)
        for t, a, b, v in zip(H["tie_t"], H["tie_a"], H["tie_b"], H["tie"]):
            self.ties[int(t)].append((int(a), int(b), float(v)))

    def before(self, year):
        """Index of the last snapshot at or before year (else the first)."""
        return max(int(np.searchsorted(self.year, year, "right")) - 1, 0)

    def capital(self, t, pid):
        """A state's capital at snapshot t, else at the nearest one."""
        for d in range(len(self.year)):
            for u in (t - d, t + d):
                if 0 <= u < len(self.year) and pid in self.st.get(u, {}):
                    return self.st[u][pid][0]
        return None

    def cells(self, t, pid):
        """A state's cells at snapshot t, else at the nearest one."""
        for d in range(len(self.year)):
            for u in (t - d, t + d):
                if 0 <= u < len(self.year):
                    m = self.pol[u] == pid
                    if m.any():
                        return m
        return None


def flows_at(R, H, t, top):
    """The strongest trade links at snapshot t between (landmass, people)
    groups, placed at each group's population centre."""
    st, W = H.st.get(t, {}), R.W
    flow = collections.defaultdict(float)
    for a, b, v in H.ties.get(t, []):
        if a not in st or b not in st:
            continue
        ga = (int(W.landmass[st[a][0]]), st[a][1])
        gb = (int(W.landmass[st[b][0]]), st[b][1])
        if ga != gb:
            flow[tuple(sorted((ga, gb)))] += v
    best = sorted(flow.items(), key=lambda x: -x[1])[:top]
    ppl, pop = H.ppl[t], H.pop[t]
    nodes = {}
    for (a, b), _ in best:
        for lm, k in (a, b):
            if (lm, k) in nodes:
                continue
            m = (W.landmass == lm) & (ppl == k) & (pop > 0)
            if m.any():
                idx = np.nonzero(m)[0]
                c = (W.xyz[idx] * pop[idx, None]).sum(0)
                nodes[(lm, k)] = int(idx[np.argmax(W.xyz[idx] @ c)])
    return nodes, [(a, b, v) for (a, b), v in best
                   if a in nodes and b in nodes]


def war_rows(R):
    out = []
    for r in rows(os.path.join(R.dir, "wars.csv")):
        ca, cd = num(r["cities_att"]), num(r["cities_dfn"])
        out.append(dict(r, start=int(r["start"]),
                        end=int(r["end"]) if r["end"] else R.years,
                        ca=int(ca), cd=int(cd), att=int(r["att"]),
                        dfn=int(r["dfn"]),
                        score=min(ca, cd) * (1 + num(r["captures"])) +
                        0.001 * (ca + cd)))
    return out


def side_width(n):
    return min(0.8 + 0.6 * math.sqrt(max(n, 1)), 7.0)


def seg(ax, p, q, lw, rgb, w, z=5):
    """A line p -> q the short way round the map (it wraps east-west)."""
    from matplotlib import patheffects as pe
    (x0, y0), (x1, y1) = p, q
    if x1 - x0 > w / 2:
        x1 -= w
    elif x0 - x1 > w / 2:
        x1 += w
    halo = [pe.withStroke(linewidth=lw + 2.5, foreground="black")]
    for sh in (0, -w, w):
        ax.plot([x0 + sh, x1 + sh], [y0, y1], color=np.array(rgb) / 255,
                lw=lw, solid_capstyle="round", path_effects=halo, zorder=z)
    return x1


def faint(ax, p, q, w):
    """A minor war: a thin line between the capitals, the short way."""
    (x0, y0), (x1, y1) = p, q
    if x1 - x0 > w / 2:
        x1 -= w
    elif x0 - x1 > w / 2:
        x1 += w
    for sh in (0, -w, w):
        ax.plot([x0 + sh, x1 + sh], [y0, y1], color="#ff8c8c", lw=0.8,
                alpha=0.55, zorder=3)


ATT_WON = ("defender fell", "submitted", "goal met", "ceded", "tributary")
DFN_WON = ("attacker fell", "repulsed")


def outcome(wr):
    """(winner 'att' / 'dfn' / None for a draw or unfinished war, net
    cities to the attacker, short text). Net = captures + a ceded city -
    recaptures."""
    why = wr.get("why", "")
    net = int(num(wr.get("captures"))) - int(num(wr.get("recaptures"))) + \
        (1 if why.startswith("ceded") else 0)
    if why.startswith(ATT_WON):
        win = "att"
    elif why.startswith(DFN_WON):
        win = "dfn"
    else:
        win = None
    if win is None:
        txt = "draw" if why.startswith("peace") else "unfinished"
        if net:
            txt += f", attacker {net:+d}"
    else:
        n = net if win == "att" else -net
        txt = f"{'attacker' if win == 'att' else 'defender'} won" + \
            (f", {n:+d} {'city' if abs(n) == 1 else 'cities'}" if n else "")
    return win, net, txt


def unwrap(x0, x1, w):
    if x1 - x0 > w / 2:
        return x1 - w
    if x0 - x1 > w / 2:
        return x1 + w
    return x1


def draw_war(R, H, ax, t, wr, w, label=None, shift=0):
    """Half-lines from each capital to the midpoint (width = that side's
    cities); an arrowhead at the loser's capital in the winner's colour and
    a white star on the winner's; none for a draw."""
    from matplotlib import patheffects as pe
    ca, cd = H.capital(t, wr["att"]), H.capital(t, wr["dfn"])
    if ca is None or cd is None:
        return
    (ax_, ay), (bx, by) = R.xy(ca), R.xy(cd)
    pa, pb = (ax_ + shift, ay), (bx + shift, by)
    pb_ = (unwrap(pa[0], pb[0], w), pb[1])
    mid = ((pa[0] + pb_[0]) / 2, (pa[1] + pb[1]) / 2)
    seg(ax, pa, mid, side_width(wr["ca"]), ATT, w)
    seg(ax, pb, mid, side_width(wr["cd"]), DFN, w)
    for p, rgb in ((pa, ATT), (pb, DFN)):
        ax.scatter([p[0]], [p[1]], s=30, c=[np.array(rgb) / 255],
                   edgecolors="black", linewidths=1, zorder=7)
    win, _, _ = outcome(wr)
    if win is not None:
        wp, lp, rgb, lw = (pa, pb_, ATT, wr["ca"]) if win == "att" else \
            (pb_, pa, DFN, wr["cd"])
        tail = (lp[0] + 0.35 * (mid[0] - lp[0]), lp[1] + 0.35 *
                (mid[1] - lp[1]))
        for sh in (0, -w, w):
            ax.annotate("", xy=(lp[0] + sh, lp[1]),
                        xytext=(tail[0] + sh, tail[1]), zorder=8,
                        arrowprops=dict(arrowstyle="-|>", lw=1.0,
                                        color=np.array(rgb) / 255,
                                        mutation_scale=10 + 2.2 *
                                        side_width(lw), shrinkA=0,
                                        shrinkB=3, ec="black"))
            ax.scatter([wp[0] % w + sh], [wp[1]], marker="*", s=150,
                       c="white", edgecolors="black", linewidths=1,
                       zorder=9)
    if label:
        ax.text(mid[0] % w, mid[1] - 6, label, color="white", fontsize=8,
                ha="center", va="bottom", zorder=10,
                path_effects=[pe.withStroke(linewidth=2.5,
                                            foreground="black")])


def map_figure(R, img):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=(0, w, h, 0), interpolation="nearest")
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    return fig, ax, w


def finish(fig):
    import matplotlib.pyplot as plt
    fig.canvas.draw()
    out = Image.frombuffer("RGBA", fig.canvas.get_width_height(),
                           fig.canvas.buffer_rgba()).convert("RGB")
    plt.close(fig)
    return out


def header(fig, ax, text, sub=None):
    from matplotlib import patheffects as pe
    halo = [pe.withStroke(linewidth=3.5, foreground="black")]
    ax.text(0.012, 0.975, text, transform=ax.transAxes, color="white",
            fontsize=15, fontweight="bold", va="top", path_effects=halo,
            zorder=12)
    if sub:
        ax.text(0.012, 0.915, sub, transform=ax.transAxes, color=INK,
                fontsize=10, va="top", path_effects=halo, zorder=12)


def legend(ax, items):
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=np.array(c) / 255 if isinstance(c, tuple)
                 else c, lw=lw, label=lab) for c, lw, lab in items]
    lg = ax.legend(handles=hs, loc="lower left", fontsize=9, facecolor=BGF,
                   edgecolor="#555555", labelcolor=INK, framealpha=0.9)
    lg.set_zorder(10)


def inset(R, H, fig, img, t, wr, ol):
    """A zoomed view of the two states and their capitals, top right,
    when they cover a small part of the map."""
    W = R.W
    pts = [R.xy(c) for m, _ in ol for c in np.nonzero(m)[0]]
    pts += [R.xy(c) for c in (H.capital(t, wr["att"]),
                              H.capital(t, wr["dfn"])) if c is not None]
    if not pts:
        return
    h, w = img.shape[:2]
    xs, ys = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
    if xs.max() - xs.min() > w / 2:          # across the date line
        xs = np.where(xs < w / 2, xs + w, xs)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    span = max(x1 - x0, (y1 - y0) * 2.0, 40) * 1.4
    if span > 0.45 * w:
        return
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    big = np.concatenate([img, img], 1)      # so a box may run past the edge
    ax = fig.add_axes([0.62, 0.40, 0.37, 0.58])
    ax.imshow(big, extent=(0, 2 * w, h, 0), interpolation="nearest")
    ax.set_xlim(cx - span / 2, cx + span / 2)
    ax.set_ylim(min(h, cy + span / 4), max(0, cy - span / 4))
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("white")
        sp.set_linewidth(1.5)
    for sh in (0, w):
        wr2 = dict(wr)
        draw_war(R, H, ax, t, wr2, 2 * w, shift=sh)


def war_maps(R, H, wars):
    best = sorted(wars, key=lambda x: -x["score"])[:WAR_MAPS]
    for k, wr in enumerate(sorted(best, key=lambda x: x["start"]), 1):
        t = int(np.argmin(np.abs(H.year - wr["start"])))
        ol = [(m, rgb) for m, rgb in ((H.cells(t, wr["att"]), ATT),
                                      (H.cells(t, wr["dfn"]), DFN))
              if m is not None]
        img = flat_peoples(R, H.ppl[t], H.pop[t], ol)
        fig, ax, w = map_figure(R, img)
        draw_war(R, H, ax, t, wr, w)
        inset(R, H, fig, img, t, wr, ol)
        yrs = (f"{wr['start']}" if wr["end"] == wr["start"] else
               f"{wr['start']}-{wr['end']}")
        cities = lambda n: f"{n} city" if n == 1 else f"{n} cities"
        header(fig, ax, f"year {yrs}",
               f"P{wr['att']} ({wr['people_att']}, {cities(wr['ca'])}) "
               f"attacks P{wr['dfn']} ({wr['people_dfn']}, "
               f"{cities(wr['cd'])}): {outcome(wr)[2]}; "
               f"{cities(int(num(wr['captures'])))} taken, "
               f"{int(num(wr['recaptures']))} retaken; {wr['why']}")
        legend(ax, [(ATT, 3, "attacker: border, capital, half-line"),
                    (DFN, 3, "defender; arrowhead at the loser, star on "
                     "the winner (none for a draw)"),
                    ("white", 1, f"map as of year {int(H.year[t])}; line "
                     "width = each side's cities")])
        finish(fig).save(os.path.join(R.dir, f"war{k:02d}.png"))
    return len(best)


def tradewars_gif(R, H, wars):
    from matplotlib.patches import FancyArrowPatch
    from matplotlib import patheffects as pe
    halo = [pe.withStroke(linewidth=4, foreground="black")]
    frames = []
    for t in range(len(H.year)):
        y = int(H.year[t])
        y0 = int(H.year[t - 1]) if t else 0
        now = [wr for wr in wars if wr["start"] <= y and wr["end"] > y0]
        # one line per pair of states: its most important war, and a count
        grp = {}
        for wr in now:
            k = (min(wr["att"], wr["dfn"]), max(wr["att"], wr["dfn"]))
            g = grp.setdefault(k, [wr, 0, 0.0])
            if wr["score"] > g[0]["score"]:
                g[0] = wr
            g[1] += 1
            g[2] += wr["score"]
        pairs = sorted(grp.values(), key=lambda g: -g[2])
        ol = []
        for wr, _, _ in pairs[:GIF_OUTLINE]:
            for pid, rgb in ((wr["att"], ATT), (wr["dfn"], DFN)):
                m = H.pol[t] == pid
                if m.any():
                    ol.append((m, rgb))
        fig, ax, w = map_figure(R, flat_peoples(R, H.ppl[t], H.pop[t], ol))
        nodes, flows = flows_at(R, H, t, TOP_FLOWS_GIF)
        vmax = max([f[2] for f in flows], default=1)
        for a, b, v in flows:
            pa, pb = R.xy(nodes[a]), R.xy(nodes[b])
            if abs(pa[0] - pb[0]) > w / 2:
                seg(ax, pa, pb, 1.2 + 4.5 * v / vmax, (255, 255, 255), w, z=4)
                continue
            lw = 1.2 + 4.5 * v / vmax
            ax.add_patch(FancyArrowPatch(
                pa, pb, arrowstyle="-", connectionstyle="arc3,rad=0.18",
                color="white", lw=lw, shrinkA=4, shrinkB=4, path_effects=halo,
                zorder=4, alpha=0.9))
        for (lm, k), c in nodes.items():
            x, yy = R.xy(c)
            ax.scatter([x], [yy], s=40, c=[np.array(R.col[R.keys[k]]) / 255],
                       edgecolors="black", linewidths=1.1, zorder=6)
        for wr, _, _ in pairs[GIF_MAJOR:]:
            ca, cd = H.capital(t, wr["att"]), H.capital(t, wr["dfn"])
            if ca is not None and cd is not None:
                faint(ax, R.xy(ca), R.xy(cd), w)
        for i in range(min(GIF_MAJOR, len(pairs)) - 1, -1, -1):
            wr, n, _ = pairs[i]
            lab = None
            if i < GIF_OUTLINE:
                win, net, _ = outcome(wr)
                res = "draw" if win is None else (
                    f"{net:+d}" if win == "att" else f"{-net:+d}")
                lab = f"{wr['start']} {res}" + (f" (x{n})" if n > 1 else "")
            draw_war(R, H, ax, t, wr, w, label=lab)
        header(fig, ax, f"year {y}",
               f"{len(now)} wars between {len(pairs)} pairs of states since "
               f"{y0}; {len(flows)} strongest trade links")
        legend(ax, [("white", 3, "trade link between peoples or landmasses; "
                     "width = trade"),
                    (ATT, 3, f"attacker capital and half-line, {GIF_MAJOR} "
                     "most important pairs; width = its cities"),
                    (DFN, 3, f"defender; arrowhead at the loser, star on "
                     f"the winner; top {GIF_OUTLINE}: borders, start year, "
                     "winner's net cities"),
                    ((255, 140, 140), 1, "other wars")])
        frames.append(finish(fig))
    small = [f.resize((f.size[0] * 3 // 4, f.size[1] * 3 // 4),
                      Image.LANCZOS) for f in frames]
    pal = [f.quantize(colors=200, method=Image.Quantize.MEDIANCUT)
           for f in small]
    pal[0].save(os.path.join(R.dir, "tradewars.gif"), save_all=True,
                append_images=pal[1:], duration=600, loop=0, optimize=False)
    return len(frames)


def history_figures(R):
    """war01.png ... and tradewars.gif, when the run has history.npz."""
    if not os.path.exists(os.path.join(R.dir, "history.npz")):
        return None
    H = Hist(R.dir)
    wars = war_rows(R)
    return war_maps(R, H, wars), tradewars_gif(R, H, wars)


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
    trade_panel(R).save(os.path.join(run, "trade.png"))
    wars_figure(R, os.path.join(run, "wars.png"))
    try:
        n = history_figures(R)
        if n:
            print(f"wrote war01-{n[0]:02d}.png and tradewars.gif "
                  f"({n[1]} frames)")
    except Exception as e:  # noqa: BLE001
        print(f"war and trade history failed ({e!r})")


if __name__ == "__main__":
    for r in sys.argv[1:]:
        compose(r)
        print("wrote", os.path.join(r, "final.png"), "and wars.png")
