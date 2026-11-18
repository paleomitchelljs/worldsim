"""
One self-contained HTML page per run, for reading its history
(WP3 stage D, U 2026-11-17).

    python viewer.py RUN [--every-years 25] [--scale 2]

Writes <run>/viewer.html: open it in a browser (no server, no network).
A time slider with play; layers states, peoples, years since a cell last
changed state, years since it last changed people; Mollweide or plate
carree. Click a city or a state to list its row from cities.csv /
polities.csv and its events from events.jsonl; click an event's year to
jump there. A view can be linked with a hash:
viewer.html#year=5000&layer=state_age&proj=platecarree&state=123.

The page draws the maps itself from per-cell data, by the same rules as
wsim/maps.py: each snapshot's state id and people (with a 16-level
density) per land cell, stored as the change from the previous snapshot
and gzipped (about 1.5 MB for 8,000 years at 25-year snapshots). Python
supplies what must match the offline renderer exactly: the projection's
pixel-to-cell table, city and label positions, the state colours
(wsim/colors.py) and the base map.
"""
import argparse
import base64
import gzip
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wsim.params import NX, NY  # noqa: E402
from wsim.runio import Run  # noqa: E402
from wsim import maps  # noqa: E402
import render_run  # noqa: E402


def b64gz(a):
    """An array (or bytes) as base64 of its gzip."""
    raw = a if isinstance(a, bytes) else np.ascontiguousarray(a).tobytes()
    return base64.b64encode(gzip.compress(raw, 6)).decode("ascii")


def delta(a):
    """Snapshot-to-snapshot differences (wrapping in the dtype): mostly
    zeros, which gzip packs tightly; the page sums them back."""
    d = np.diff(a.astype(np.int64), axis=0, prepend=0)
    return d.astype(a.dtype)


def plain(o):
    """numpy scalars for json.dumps."""
    return o.item() if hasattr(o, "item") else str(o)


def table(df, cols):
    """A DataFrame as {cols, rows} with NaN as null."""
    cols = [c for c in cols if c in df.columns]
    sub = df[cols].astype(object).where(df[cols].notna(), None)
    return dict(cols=cols, rows=sub.values.tolist())


def build(run, every_years=25, scale=2):
    W = run.W
    hist = render_run.History(run)
    H = hist.H
    y = hist.year
    sel = np.array([t for t in range(len(y))
                    if y[t] % every_years == 0 or t == len(y) - 1])
    years = y[sel].astype(int)
    T, N = len(sel), W.N
    pol = H["polity"][sel].astype(np.int32)
    npid = int(max(pol.max(), H["st_id"].max() if len(H["st_id"]) else 0))
    pol_dt = np.int16 if npid < 32000 else np.int32
    occ = H["people"][sel] >= 0
    dens = np.where(occ, H["pop"][sel] / W.area, 0)
    a = np.clip(np.log10(1 + dens) / np.log10(1 + 60), 0, 1)
    pe = (H["people"][sel] + 1).astype(np.uint8) | \
        (np.round(a * 15).astype(np.uint8) << 4)
    # population per people per snapshot (header)
    nP = len(hist.keys)
    pops = [np.bincount(H["people"][t][H["people"][t] >= 0],
                        weights=H["pop"][t][H["people"][t] >= 0],
                        minlength=nP).round().tolist() for t in sel]

    # projections: output pixel -> base-map index (rows r0 .. r1)
    r0 = W.r0
    nrow = min(W.r1 + 1, NY) - r0
    projs = {}
    for kind in ("mollweide", "platecarree"):
        P = maps.Proj(W, kind, scale)
        idx = np.where(P.idx >= 0, P.idx - r0 * NX, -1).astype(np.int32)
        idx = np.where(idx < nrow * NX, idx, -1)
        projs[kind] = dict(P=P, w=P.size[0], h=P.size[1],
                           idx=b64gz(np.diff(idx.ravel(), prepend=0)
                                     .astype(np.int32)))
    gridcell = np.full(nrow * NX, -1, np.int32)
    gridcell[(W.row - r0) * NX + W.col] = np.arange(N)

    # cities: per snapshot (id, size, capital); positions per projection
    C = run.cities
    cid = C["id"].to_numpy()
    cpos = {}
    for kind, pr in projs.items():
        x, yy = pr["P"].fwd(C["lon"].to_numpy(), C["lat"].to_numpy())
        cpos[kind] = np.stack([x, yy], 1).round(1).ravel().tolist()
    city_rows = []
    if hist.has_cities:
        for t in sel:
            r = hist.rows(hist._city, t)
            city_rows.append(np.stack(
                [H["city_id"][r], np.round(H["city_size"][r]),
                 H["city_capital"][r]], 1).astype(int).ravel().tolist())
    else:
        f = C["founded"].to_numpy()
        e = C["ended"].fillna(10 ** 9).to_numpy()
        for yr in years:
            m = (f <= yr) & (e > yr)
            city_rows.append(np.stack(
                [cid[m], np.round(C["peak_size"].to_numpy()[m]),
                 np.zeros(m.sum())], 1).astype(int).ravel().tolist())

    # labels: the ten largest states at their largest piece's centre
    labels = []
    for i, t in enumerate(sel):
        s = maps.Snap(int(y[t]), H["people"][t], H["polity"][t].astype(int),
                      H["pop"][t], hist.colors, hist.keys, hist.labels,
                      hist.pcol)
        row = []
        for pid, _ in maps.big_states(s):
            c = maps.piece_centre(W, np.nonzero(s.polity == pid)[0])
            xy = [pid]
            for kind in ("mollweide", "platecarree"):
                x, yy = projs[kind]["P"].fwd(W.lon[c], W.lat[c])
                xy += [round(float(x), 1), round(float(yy), 1)]
            row.append(xy)
        labels.append(row)

    # states alive per snapshot, from the state table
    alive = []
    for t in sel:
        r = hist.rows(hist._st, t)
        alive.append(len(r))

    from matplotlib import colormaps
    inferno = (colormaps["inferno"](np.linspace(0, 1, 256))[:, :3] * 255)
    ev = run.events if run.has("events") else None
    events = []
    if ev is not None:
        for e in ev.itertuples(index=False):
            d = e._asdict()
            lst = lambda k: [int(v) for v in d.get(k)] \
                if isinstance(d.get(k), list) else []
            events.append([int(d["year"]), d["kind"], d["text"],
                           lst("polities"), lst("cities")])
    pcols = ["id", "people", "lineage", "peoples_ruled", "founded", "ended",
             "years", "parent", "peak_cells", "peak_km2", "peak_year",
             "peak_cities", "peak_pop", "origin", "end_reason", "ended_by",
             "capital_lon", "capital_lat"]
    ccols = ["id", "people", "founded", "ended", "end_reason", "cause",
             "years", "peak_size", "peak_year", "n_sacks", "rulers",
             "prev_city", "successor", "lon", "lat"]
    meta = dict(
        run=run.name, years=years.tolist(), N=N, T=T, nrow=nrow, nx=NX,
        scale=scale, pol16=pol_dt == np.int16,
        keys=hist.keys, labels=hist.labels,
        colors=hist.colors.astype(int).tolist(),
        pcol=np.round(hist.pcol).astype(int).ravel().tolist(),
        pops=pops, alive=alive, inferno=inferno.round().astype(int)
        .ravel().tolist(),
        proj={k: dict(w=v["w"], h=v["h"]) for k, v in projs.items()},
        cityid=cid.astype(int).tolist(), citypos=cpos, cities_t=city_rows,
        labels_t=labels, has_cities=hist.has_cities)
    blobs = dict(
        pol=b64gz(delta(pol.astype(pol_dt))),
        pe=b64gz(delta(pe)),
        base=b64gz(W.base[r0:r0 + nrow].astype(np.uint8)),
        grid=b64gz(gridcell),
        idx_mollweide=projs["mollweide"]["idx"],
        idx_platecarree=projs["platecarree"]["idx"],
        tables=b64gz(json.dumps(dict(
            polities=table(run.polities, pcols) if run.has("polities")
            else None,
            cities=table(C, ccols), events=events),
            default=plain).encode()))
    return meta, blobs


def write(run, path, every_years=25, scale=2):
    meta, blobs = build(run, every_years, scale)
    html = PAGE.replace("__TITLE__", f"{run.name}") \
        .replace("__META__", json.dumps(meta, separators=(",", ":"),
                                        default=plain)) \
        .replace("__BLOBS__", json.dumps(blobs, separators=(",", ":")))
    with open(path, "w") as fh:
        fh.write(html)
    return os.path.getsize(path)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ viewer</title>
<style>
:root { --bg:#101218; --panel:#181b23; --line:#2a2e3a; --text:#e6e6e6;
        --dim:#9aa0ad; --accent:#8fd3c7; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text);
       font:14px/1.4 system-ui, -apple-system, Segoe UI, sans-serif; }
header { display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center;
         padding:10px 16px; border-bottom:1px solid var(--line); }
header h1 { font-size:16px; margin:0 8px 0 0; font-weight:600; }
#year { font-size:22px; font-variant-numeric:tabular-nums; min-width:5.5em; }
#slider { flex:1 1 260px; accent-color:var(--accent); }
button, select { background:var(--panel); color:var(--text);
  border:1px solid var(--line); border-radius:6px; padding:5px 10px;
  font:inherit; cursor:pointer; }
main { display:flex; flex-wrap:wrap; gap:0; }
#mapwrap { flex:1 1 700px; min-width:0; padding:12px 16px; }
#stack { position:relative; width:100%; }
canvas { display:block; width:100%; height:auto; image-rendering:auto; }
#over { position:absolute; left:0; top:0; cursor:crosshair; }
#legend { display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:10px;
          color:var(--dim); font-size:13px; }
#legend span.sw { display:inline-block; width:12px; height:12px;
  border-radius:2px; margin-right:6px; vertical-align:-1px; }
#side { flex:0 1 380px; min-width:280px; max-height:calc(100vh - 60px);
        overflow:auto; padding:12px 16px; border-left:1px solid var(--line);
        background:var(--panel); }
#side h2 { font-size:15px; margin:4px 0 8px; }
#side table { border-collapse:collapse; width:100%; font-size:13px; }
#side td { padding:2px 6px 2px 0; vertical-align:top; }
#side td:first-child { color:var(--dim); white-space:nowrap; }
.ev { font-size:13px; padding:3px 0; border-top:1px solid var(--line); }
.ev a { color:var(--accent); cursor:pointer; text-decoration:none;
        font-variant-numeric:tabular-nums; }
.ev .k { color:var(--dim); }
.hint { color:var(--dim); font-size:13px; }
#loading { padding:40px; color:var(--dim); }
@media (max-width:800px) { #side { border-left:0; max-height:none; } }
</style></head><body>
<header>
  <h1>__TITLE__</h1>
  <div id="year">Year</div>
  <button id="play" aria-label="Play">Play</button>
  <input id="slider" type="range" min="0" value="0" step="1"
         aria-label="Snapshot">
  <select id="layer" aria-label="Layer">
    <option value="states">States</option>
    <option value="peoples">Peoples</option>
    <option value="state_age">Years since state changed</option>
    <option value="people_age">Years since people changed</option>
  </select>
  <select id="proj" aria-label="Projection">
    <option value="mollweide">Mollweide (equal-area)</option>
    <option value="platecarree">Plate carree</option>
  </select>
  <select id="speed" aria-label="Speed">
    <option value="250">4 / s</option>
    <option value="125" selected>8 / s</option>
    <option value="60">16 / s</option>
  </select>
</header>
<main>
  <div id="mapwrap">
    <div id="loading">Unpacking the run...</div>
    <div id="stack" hidden><canvas id="map"></canvas>
      <canvas id="over"></canvas></div>
    <div id="legend"></div>
    <div class="hint" id="stats"></div>
  </div>
  <aside id="side"><h2>Click a city or a state</h2>
    <p class="hint">Cities are the dots; capitals are white. The panel
    lists the record and every logged event; click a year to go there.
    Events are logged only for larger states, so a small state may have
    none.</p></aside>
</main>
<script>
const META = __META__;
const BLOBS = __BLOBS__;

async function unpack(name) {
  const bin = Uint8Array.from(atob(BLOBS[name]), c => c.charCodeAt(0));
  const s = new Blob([bin]).stream()
    .pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(s).arrayBuffer());
}
function cumsum(arr, T, N) {      // undo the per-snapshot differences
  for (let t = 1; t < T; t++) {
    const o = t * N, p = o - N;
    for (let i = 0; i < N; i++) arr[o + i] += arr[p + i];
  }
  return arr;
}

const M = META, N = M.N, T = M.T;
let POL, PE, BASE, GRID, IDX = {}, TAB, cur = 0, sel = null, timer = null;
const lastState = {t: -1, a: null}, lastPeople = {t: -1, a: null};

function ageArrays(t) {     // year each cell last changed (cached forward)
  for (const [c, arr, sh] of [[lastState, POL, 0], [lastPeople, PE, 1]]) {
    if (c.t > t || c.a === null) {
      c.a = new Float32Array(N).fill(M.years[0]); c.t = 0;
    }
    for (let u = c.t + 1; u <= t; u++) {
      const o = u * N, p = o - N, y = M.years[u];
      for (let i = 0; i < N; i++) {
        const a = sh ? (arr[o + i] & 15) : arr[o + i];
        const b = sh ? (arr[p + i] & 15) : arr[p + i];
        if (a !== b) c.a[i] = y;
      }
    }
    c.t = t;
  }
}

function draw() {
  const kind = document.getElementById("proj").value;
  const layer = document.getElementById("layer").value;
  const P = M.proj[kind], w = P.w, h = P.h, idx = IDX[kind];
  const cv = document.getElementById("map"), ov = document.getElementById("over");
  if (cv.width !== w || cv.height !== h) {
    cv.width = ov.width = w; cv.height = ov.height = h;
  }
  const ctx = cv.getContext("2d"), img = ctx.createImageData(w, h);
  const px = img.data, o = cur * N, year = M.years[cur];
  const lab = new Int32Array(w * h);
  const age = layer === "state_age" || layer === "people_age";
  if (age) ageArrays(cur);
  const last = layer === "state_age" ? lastState.a : lastPeople.a;
  for (let p = 0; p < w * h; p++) {
    const g = idx[p], q = 4 * p;
    if (g < 0) { px[q] = 16; px[q+1] = 18; px[q+2] = 24; px[q+3] = 255;
                 lab[p] = -9; continue; }
    let r = BASE[3*g], gg = BASE[3*g+1], b = BASE[3*g+2];
    if (age) { r *= .5; gg *= .5; b *= .5; }
    const c = GRID[g];
    let L = -3;
    if (c >= 0) {
      const pid = POL[o + c], pe = PE[o + c], pp = (pe & 15) - 1;
      L = -2;
      if (layer === "states") {
        if (pid >= 0) {
          const k = 3 * pid;
          r = .15*r + .85*M.pcol[k]; gg = .15*gg + .85*M.pcol[k+1];
          b = .15*b + .85*M.pcol[k+2]; L = pid;
        } else if (pp >= 0) {
          const k = M.colors[pp];
          r = .6*r + .4*k[0]; gg = .6*gg + .4*k[1]; b = .6*b + .4*k[2];
        }
      } else if (layer === "peoples") {
        if (pp >= 0) {
          const a = Math.max(.4, (pe >> 4) / 15), k = M.colors[pp];
          r = (1-a)*r + a*k[0]; gg = (1-a)*gg + a*k[1]; b = (1-a)*b + a*k[2];
        }
      } else {
        const on = layer === "state_age" ? pid >= 0 : pp >= 0;
        if (layer === "state_age" && pid >= 0) L = pid;
        if (on) {
          const s = Math.max(year - last[c], 25);
          const v = Math.min(1, Math.max(0, Math.log(s / 25) / Math.log(80)));
          const k = 3 * Math.floor((1 - v) * 230 + 20);
          r = M.inferno[k]; gg = M.inferno[k+1]; b = M.inferno[k+2];
        }
      }
      if (sel && sel.type === "state" && pid === sel.id) {
        r = .55*r + .45*255; gg = .55*gg + .45*255; b = .55*b + .45*255;
      }
    }
    lab[p] = L;
    px[q] = r; px[q+1] = gg; px[q+2] = b; px[q+3] = 255;
  }
  if (layer === "states" || layer === "state_age") {
    const f = layer === "states" ? .25 : .6;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const p = y * w + x, a = lab[p];
      if (a < 0) continue;
      if ((x < w-1 && a !== lab[p+1]) || (y < h-1 && a !== lab[p+w])) {
        const q = 4 * p; px[q] *= f; px[q+1] *= f; px[q+2] *= f;
      }
    }
  }
  ctx.putImageData(img, 0, 0);
  overlay(kind);
  document.getElementById("year").textContent = "Year " + year;
  const pops = M.pops[cur];
  document.getElementById("legend").innerHTML = M.keys.map((k, i) =>
    `<span><span class="sw" style="background:rgb(${M.colors[i]})"></span>` +
    `${M.labels[i]} ${(pops[i] / 1e6).toFixed(2)}M</span>`).join("");
  document.getElementById("stats").textContent =
    `${M.alive[cur]} states, ${M.cities_t[cur].length / 3} cities`;
}

function cityXY(kind) {
  const pos = M.citypos[kind], at = {};
  M.cityid.forEach((id, i) => { at[id] = [pos[2*i], pos[2*i+1]]; });
  return at;
}
const XY = {};

function overlay(kind) {
  const ov = document.getElementById("over"), d = ov.getContext("2d");
  d.clearRect(0, 0, ov.width, ov.height);
  XY[kind] = XY[kind] || cityXY(kind);
  const xy = XY[kind], cs = M.cities_t[cur];
  for (let i = 0; i < cs.length; i += 3) {
    const p = xy[cs[i]]; if (!p) continue;
    const rad = 1 + 1.2 * Math.log10(1 + Math.max(cs[i+1], 0) / 2000);
    d.beginPath(); d.arc(p[0], p[1], rad, 0, 2 * Math.PI);
    d.fillStyle = cs[i+2] ? "#fff" : "#ebe6d7"; d.fill();
    d.lineWidth = 1; d.strokeStyle = "#000"; d.stroke();
    if (sel && sel.type === "city" && sel.id === cs[i]) {
      d.beginPath(); d.arc(p[0], p[1], rad + 4, 0, 2 * Math.PI);
      d.strokeStyle = "#ffd84d"; d.lineWidth = 2; d.stroke();
    }
  }
  const off = kind === "mollweide" ? 1 : 3;
  d.font = "13px system-ui, sans-serif"; d.textAlign = "center";
  d.lineWidth = 3; d.strokeStyle = "#000"; d.fillStyle = "#fff";
  const layer = document.getElementById("layer").value;
  if (layer === "states" || layer === "state_age") {
    for (const l of M.labels_t[cur]) {
      const t = "P" + l[0], x = l[off], y = l[off+1] + 4;
      d.strokeText(t, x, y); d.fillText(t, x, y);
    }
  }
}

function row(tab, id) {
  if (!tab) return null;
  const i = tab.cols.indexOf("id");
  const r = tab.rows.find(r => r[i] === id);
  return r ? Object.fromEntries(tab.cols.map((c, k) => [c, r[k]])) : null;
}
function esc(s) { return String(s).replace(/[&<>]/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function kv(o) {
  return "<table>" + Object.entries(o).filter(([k, v]) => v !== null &&
    v !== "").map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(
    typeof v === "number" && !Number.isInteger(v) ? v.toFixed(2) : v)}</td></tr>`)
    .join("") + "</table>";
}
function evlist(f) {
  const ev = TAB.events.filter(f);
  if (!ev.length) return "<p class='hint'>No logged events.</p>";
  return `<h2>Events (${ev.length})</h2>` + ev.slice(0, 400).map(e =>
    `<div class="ev"><a data-y="${e[0]}">${e[0]}</a> ` +
    `<span class="k">${esc(e[1])}</span> ${esc(e[2])}</div>`).join("") +
    (ev.length > 400 ? "<p class='hint'>First 400 shown.</p>" : "");
}
function show() {
  const side = document.getElementById("side");
  if (!sel) return;
  if (sel.type === "city") {
    const r = row(TAB.cities, sel.id);
    side.innerHTML = `<h2>City ${sel.id}</h2>` + (r ? kv(r) : "") +
      evlist(e => e[4].includes(sel.id));
  } else if (sel.type === "state") {
    const r = row(TAB.polities, sel.id);
    side.innerHTML = `<h2>State P${sel.id}</h2>` + (r ? kv(r) : "") +
      evlist(e => e[3].includes(sel.id));
  } else {
    side.innerHTML = `<h2>Cell ${sel.id}</h2>` + kv(sel.info);
  }
  side.querySelectorAll("a[data-y]").forEach(a => a.onclick = () => {
    const y = +a.dataset.y;
    let t = 0; while (t + 1 < T && M.years[t + 1] <= y) t++;
    go(t);
  });
}

function go(t) {
  cur = Math.max(0, Math.min(T - 1, t));
  document.getElementById("slider").value = cur;
  draw();
}

function click(ev) {
  const ov = document.getElementById("over"), r = ov.getBoundingClientRect();
  const x = (ev.clientX - r.left) * ov.width / r.width;
  const y = (ev.clientY - r.top) * ov.height / r.height;
  const kind = document.getElementById("proj").value;
  const xy = XY[kind], cs = M.cities_t[cur];
  let best = null, bd = 49;
  for (let i = 0; i < cs.length; i += 3) {
    const p = xy[cs[i]]; if (!p) continue;
    const d = (p[0]-x)**2 + (p[1]-y)**2;
    if (d < bd) { bd = d; best = cs[i]; }
  }
  if (best !== null) sel = {type: "city", id: best};
  else {
    const P = M.proj[kind], g = IDX[kind][Math.floor(y) * P.w + Math.floor(x)];
    const c = g >= 0 ? GRID[g] : -1;
    if (c < 0) { sel = null; draw(); return; }
    const pid = POL[cur * N + c], pp = (PE[cur * N + c] & 15) - 1;
    sel = pid >= 0 ? {type: "state", id: pid} :
      {type: "cell", id: c, info: {people: pp >= 0 ? M.labels[pp] : "empty",
                                   state: "none"}};
  }
  draw(); show();
}

(async () => {
  const pol = await unpack("pol"), pe = await unpack("pe");
  POL = cumsum(M.pol16 ? new Int16Array(pol.buffer) : new Int32Array(pol.buffer), T, N);
  PE = cumsum(pe, T, N);
  BASE = await unpack("base");
  GRID = new Int32Array((await unpack("grid")).buffer);
  for (const k of ["mollweide", "platecarree"]) {
    const d = new Int32Array((await unpack("idx_" + k)).buffer);
    for (let i = 1; i < d.length; i++) d[i] += d[i - 1];
    IDX[k] = d;
  }
  TAB = JSON.parse(new TextDecoder().decode(await unpack("tables")));
  document.getElementById("loading").remove();
  document.getElementById("stack").hidden = false;
  const s = document.getElementById("slider");
  s.max = T - 1; s.oninput = () => go(+s.value);
  for (const id of ["layer", "proj"])
    document.getElementById(id).onchange = draw;
  document.getElementById("over").onclick = click;
  document.getElementById("play").onclick = () => {
    const b = document.getElementById("play");
    if (timer) { clearInterval(timer); timer = null; b.textContent = "Play"; return; }
    if (cur >= T - 1) go(0);
    b.textContent = "Pause";
    timer = setInterval(() => {
      if (cur >= T - 1) { clearInterval(timer); timer = null;
                          b.textContent = "Play"; return; }
      go(cur + 1);
    }, +document.getElementById("speed").value);
  };
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT" && e.target.type !== "range") return;
    if (e.key === "ArrowRight") go(cur + 1);
    if (e.key === "ArrowLeft") go(cur - 1);
  });
  // a view can be linked: #year=5000&layer=state_age&proj=platecarree
  // &state=123 (or &city=45)
  const h = new URLSearchParams(location.hash.slice(1));
  for (const id of ["layer", "proj"])
    if (h.get(id)) document.getElementById(id).value = h.get(id);
  if (h.get("state")) sel = {type: "state", id: +h.get("state")};
  if (h.get("city")) sel = {type: "city", id: +h.get("city")};
  let t0 = T - 1;
  if (h.get("year")) {
    t0 = 0; while (t0 + 1 < T && M.years[t0 + 1] <= +h.get("year")) t0++;
  }
  go(t0);
  show();
})();
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--every-years", type=int, default=25,
                    help="years between snapshots in the page")
    ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()
    for name in a.runs:
        run = Run(name)
        path = os.path.join(run.dir, "viewer.html")
        n = write(run, path, a.every_years, a.scale)
        print(f"{run.name}: {n / 1e6:.1f} MB -> {path}")


if __name__ == "__main__":
    main()
