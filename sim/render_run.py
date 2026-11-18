"""
Draw a finished run's maps from its snapshots, without rerunning it
(WP3 stage B, 2026-11-17).

    python render_run.py RUN [--layer states,peoples] [--every 1]
                             [--proj mollweide|platecarree]
                             [--format mp4|gif|png] [--scale 2] [--fps 8]

Reads history.npz (snapshots every 25 years from WP3 stage A; 100 years
before), run.json and the cached world, and never imports the simulation
step. One frame per kept snapshot (`--every N`: every Nth); `--layer`
takes one or more of states, peoples, density, lineages, state_age
(years since each cell last changed state), people_age (years since its
people last changed), stacked top to bottom. With states or state_age,
a strip under the map shows turnover by landmass group (--no-strip). Writes <run>/render/<layers>_<proj>.<format>; png writes the
frames into a folder of that name.

Runs before WP3 stage A have no city or lineage snapshots: their frames
have no city dots, and the lineages layer is not available.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wsim.runio import Run  # noqa: E402
from wsim import maps  # noqa: E402
from wsim.colors import state_colors  # noqa: E402


class History:
    """history.npz as snapshots for maps.Snap."""

    def __init__(self, run):
        self.run = run
        H = self.H = run.history
        cfg = run.config
        P = cfg["peoples"]
        self.keys = [p["key"] for p in P]
        self.labels = [p["label"] for p in P]
        self.colors = np.array([p["color"] for p in P], np.uint8)
        self.year = H["year"]
        self.has_cities = "city_t" in H
        self.has_lineage = "lineage" in H and (H["lineage"] >= 0).any()
        parents = None
        if run.has("polities"):
            p = run.polities
            parents = dict(zip(p["id"], p["parent"].fillna(-1).astype(int)))
        self.pcol = state_colors(run.W, H, self.colors, parents)
        self.wars = None
        if run.has("wars"):
            w = run.wars
            self.wars = (w["start"].to_numpy(),
                         w["end"].fillna(10 ** 9).to_numpy())
        self._st = self._split("st")
        self._city = self._split("city") if self.has_cities else None
        self.strip = None
        # years each cell last changed state and people (advance())
        self._t = -1
        self._ls = self._lp = None

    def advance(self, t):
        """Bring the last-change years up to snapshot t (in order)."""
        H = self.H
        while self._t < t:
            self._t += 1
            u, y = self._t, self.year[self._t]
            if u == 0:
                self._ls = np.full(H["polity"].shape[1], float(y))
                self._lp = self._ls.copy()
                continue
            self._ls[H["polity"][u] != H["polity"][u - 1]] = y
            self._lp[H["people"][u] != H["people"][u - 1]] = y

    def turnover(self, W, lag_years=100):
        """Per landmass group, per snapshot: the share of ruled cells
        whose state differs from lag_years before (NaN before then or
        with no ruled cells)."""
        import landmasses as LM
        y, pol = self.year, self.H["polity"]
        step = float(y[1] - y[0]) if len(y) > 1 else lag_years
        k = max(1, int(round(lag_years / step)))
        out = {}
        for g, codes in LM.GROUPS.items():
            m = np.isin(W.landmass, [LM.IDS[c] for c in codes])
            v = np.full(len(y), np.nan)
            for t in range(k, len(y)):
                a, b = pol[t][m], pol[t - k][m]
                r = a >= 0
                if r.any():
                    v[t] = float((a[r] != b[r]).mean())
            out[g] = v
        self.strip = (y.astype(float), out)

    def _split(self, name):
        """Row ranges of a flat per-snapshot table, by snapshot."""
        t = self.H[f"{name}_t"]
        o = np.argsort(t, kind="stable")
        b = np.searchsorted(t[o], np.arange(len(self.year) + 1))
        return o, b

    def rows(self, split, t):
        o, b = split
        return o[b[t]:b[t + 1]]

    def snap(self, t):
        H = self.H
        r = self.rows(self._st, t)
        states = {int(i): (int(c), int(p), int(n)) for i, c, p, n in
                  zip(H["st_id"][r], H["st_cap"][r], H["st_people"][r],
                      H["st_cities"][r])}
        cities = None
        if self._city is not None:
            r = self.rows(self._city, t)
            cities = dict(cell=H["city_cell"][r], size=H["city_size"][r],
                          polity=H["city_polity"][r],
                          capital=H["city_capital"][r])
        y = int(self.year[t])
        lines = [f"states {len(states)}"]
        if self.wars is not None:
            s, e = self.wars
            lines.append(f"wars {int(((s <= y) & (e > y)).sum())}")
        return maps.Snap(
            y, H["people"][t].astype(int), H["polity"][t].astype(int),
            H["pop"][t], self.colors, self.keys, self.labels, self.pcol,
            cities=cities, states=states,
            lineage=H["lineage"][t].astype(int) if self.has_lineage
            else None, lines=lines,
            since_state=y - self._ls if self._t == t else None,
            since_people=y - self._lp if self._t == t else None,
            strip=self.strip)


def encode(frames_dir, n, path, fmt, fps):
    """Frames f00000.png ... as an MP4 (H.264, yuv420p) or a GIF."""
    if fmt == "mp4":
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
             "-i", os.path.join(frames_dir, "f%05d.png"),
             "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-crf", "20", path], check=True)
        return
    pal = []
    for i in range(n):
        with Image.open(os.path.join(frames_dir, f"f{i:05d}.png")) as im:
            pal.append(im.convert("RGB").quantize(
                colors=255, method=Image.Quantize.MEDIANCUT))
    pal[0].save(path, save_all=True, append_images=pal[1:],
                duration=int(1000 / fps), loop=0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run")
    ap.add_argument("--layer", default="states,peoples")
    ap.add_argument("--every", type=int, default=1,
                    help="snapshots between frames")
    ap.add_argument("--proj", default="mollweide",
                    choices=["mollweide", "platecarree"])
    ap.add_argument("--format", default="mp4", choices=["mp4", "gif", "png"])
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--fps", type=float, default=8)
    ap.add_argument("--from-year", type=int, default=None)
    ap.add_argument("--to-year", type=int, default=None)
    ap.add_argument("--no-strip", action="store_true",
                    help="leave out the turnover strip under the map")
    a = ap.parse_args()
    run = Run(a.run)
    hist = History(run)
    layers = a.layer.split(",")
    for ly in layers:
        if ly not in maps.LAYERS:
            ap.error(f"--layer: {ly} (one of {', '.join(maps.LAYERS)})")
    if "lineages" in layers and not hist.has_lineage:
        ap.error("--layer lineages: this run's history.npz has no lineages "
                 "(runs before WP3 stage A)")
    proj = maps.Proj(run.W, a.proj, a.scale)
    if not a.no_strip and {"states", "state_age"} & set(layers):
        hist.turnover(run.W)
    y = hist.year
    ts = [t for t in range(0, len(y), a.every)
          if (a.from_year is None or y[t] >= a.from_year) and
          (a.to_year is None or y[t] <= a.to_year)]
    name = f"{'+'.join(layers)}_{a.proj}"
    out = os.path.join(run.dir, "render")
    os.makedirs(out, exist_ok=True)
    fdir = os.path.join(out, name) if a.format == "png" else \
        tempfile.mkdtemp(prefix="frames_", dir=out)
    os.makedirs(fdir, exist_ok=True)
    for i, t in enumerate(ts):
        hist.advance(t)
        img = maps.frame(run.W, hist.snap(t), proj, layers)
        img.save(os.path.join(fdir, f"f{i:05d}.png"))
        if i % 50 == 0:
            print(f"  frame {i + 1}/{len(ts)}, year {int(y[t])}", flush=True)
    if a.format == "png":
        print(f"{len(ts)} frames -> {fdir}")
        return
    path = os.path.join(out, f"{name}.{a.format}")
    encode(fdir, len(ts), path, a.format, a.fps)
    shutil.rmtree(fdir)
    print(f"{len(ts)} frames -> {path}")


if __name__ == "__main__":
    main()
