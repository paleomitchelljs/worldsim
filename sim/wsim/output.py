"""Output files."""
import contextlib
import csv
import json
import os
import shutil
import time
import numpy as np

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403
from .render import *  # noqa: F401,F403


def write_checks(m, path):
    """checks.txt: a few measures from metrics.json beside rough historical
    regularities. The references are orders of magnitude, not targets
    (docs/diagnostics.md)."""
    L, S = m.get("lifespans", {}), m.get("states", {})
    C, Wt = m.get("city_hierarchy", {}), m.get("war_time", {})
    lines = ["Stylized-fact checks (references are rough; see "
             "docs/diagnostics.md)", ""]
    if L:
        lines += [f"State lifespans (states that held 3+ cities and ended; "
                  f"n={L['ended 3+ city states']}):",
                  f"  mean {L['lifespan mean (yr)']:.0f} yrs, median "
                  f"{L['lifespan median (yr)']:.0f}, CV {L['lifespan CV']:.2f}",
                  "  reference: mean ~200-250 yrs, roughly exponential "
                  "(CV ~1) [Arbesman 2011]", ""]
    if "peak cells, largest" in S:
        lines += [f"State sizes at peak (cells, states with 3+ cities; "
                  f"n={S['states with 3+ cities']}):",
                  f"  largest {S['peak cells, largest']:.0f}, 10th "
                  f"{S['peak cells, 10th']:.0f}, median "
                  f"{S['peak cells, median']:.0f}; skew of log size "
                  f"{S['skew of log peak cells']:+.2f}",
                  "  reference: heavy-tailed, roughly log-normal (skew of "
                  "log size near 0) [Taagepera 1978-97]", ""]
    if C.get("rank-size slope, end (top 200)") is not None:
        lines += [f"City rank-size (top 200 cities in the last "
                  f"city_sizes.csv year): slope "
                  f"{C['rank-size slope, end (top 200)']:.2f}",
                  "  reference: about -1 (Zipf); pre-modern systems often "
                  "flatter, -0.6 to -1", ""]
    if "at war, mean over run" in Wt:
        lines += [f"Share of states (2+ cities) at war, mean over run: "
                  f"{Wt['at war, mean over run']:.2f}",
                  "  reference: high in pre-modern state systems; great "
                  "powers at war in most years [Levy 1983]. Uncertain.", ""]
    P = m.get("price", {})
    if P:
        lines += ["Price decomposition, summed over the run (world, "
                  "lineages as units):",
                  f"  {'trait':12s} {'dz':>8s} {'selection':>10s} "
                  f"{'transmission':>13s}"]
        for t in TRAITS:
            if f"{t}: selection, world" in P:
                s_, tr = P[f"{t}: selection, world"], \
                    P[f"{t}: transmission, world"]
                lines.append(f"  {t:12s} {s_ + tr:+8.3f} {s_:+10.3f} "
                             f"{tr:+13.3f}")
        lines += ["", "  within peoples (mean over peoples of the summed "
                  "terms; selection | transmission):"]
        for t in TRAITS:
            if f"{t}: selection, mean over peoples" in P:
                lines.append(
                    f"  {t:12s} {P[f'{t}: selection, mean over peoples']:+.3f}"
                    f" | {P[f'{t}: transmission, mean over peoples']:+.3f}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def constants_used():
    """Every numeric constant in wsim.params as the run used it (after
    --set and the other command-line overrides), for run.json."""
    from . import params

    def numeric(v):
        if isinstance(v, (bool, int, float, np.number)):
            return True
        if isinstance(v, (list, tuple)):
            return len(v) > 0 and all(numeric(x) for x in v)
        if isinstance(v, dict):
            return len(v) > 0 and all(numeric(x) for x in v.values())
        return False
    return {k: v for k, v in sorted(vars(params).items())
            if k.isupper() and numeric(v)}


@contextlib.contextmanager
def atomic(path, mode="w", **kw):
    """Write `path` under a temporary name and rename it into place, so a
    reader never sees half a file."""
    tmp = path + ".tmp"
    with open(tmp, mode, **kw) as fh:
        yield fh
    os.replace(tmp, path)


WCOL = ["id", "start", "end", "years", "att", "dfn", "people_att",
        "people_dfn", "landmass_att", "landmass_dfn", "cities_att",
        "cities_dfn", "strength_att", "strength_dfn", "goal", "goal_city",
        "goal_met", "why", "sieges", "captures", "recaptures", "moved",
        "moved_back", "helpers", "sacks", "ravages"]

# Append-only tables: (Sim attribute, file, header). A header of None
# takes the columns from the first row (dict rows); the column set is the
# same on every row of a run.
APPEND = [
    ("ts", "timeseries.csv", None),
    ("city_ts", "city_sizes.csv",
     ["year", "city_id", "cell", "status", "size", "cell_pop", "people",
      "polity", "minority", "minority_share", "size_old"]),
    ("siege_log", "sieges.csv",
     ["year", "war", "side", "city", "city_fe", "capital", "besieger",
      "holder", "P_besieger", "P_holder", "odds", "taken", "terms",
      "cities_besieger", "cities_holder", "siege_years"]),
    ("revolt_log", "revolts.csv",
     ["year", "state", "new_state", "people_ruler", "people_rebels", "kind",
      "cities_taken", "cities_left", "landmass", "lon", "lat"]),
    ("rel", "relations.csv",
     ["year", "a", "b", "people_a", "people_b", "landmass_a", "landmass_b",
      "cities_a", "cities_b", "similarity", "enmity_ab", "enmity_ba",
      "faith_ab", "faith_ba", "tie", "war", "allied", "truce",
      "similarity_lin"]),
    ("price_rows", "price.csv", None),
    ("city_rows", "citylevel.csv", None),
    ("city_gap_rows", "citygaps.csv", None),
    ("city_trait_rows", "citytraits.csv", None),
    ("lin_events", "lineage_events.csv", None),
    ("lin_pairs", "lineage_pairs.csv", None),
    ("food_rows", "cityfood.csv", None),
    ("death_rows", "deaths.csv", None),
    ("fl_rows", "food.csv", None),
    ("growth_rows", "growth.csv", None),
]


class Stream:
    """Writes a run's output while it runs (2026-11-17, WP0 stage D).
    Append-only tables get their new rows at each flush; tables whose rows
    change later (wars, rulers, cities, polities, lineages, dragons, posts)
    are rewritten whole under a temporary name. The new map snapshots go
    into one more file in history_parts/, joined into history.npz at the
    end (WP3 stage A). Frames are saved as they are rendered. Reads the Sim only. Not stored on the Sim,
    so a saved state stays picklable."""

    def __init__(self, sim, out):
        self.sim, self.out = sim, out
        self.fdir = os.path.join(out, "frames")
        os.makedirs(self.fdir, exist_ok=True)
        for f in os.listdir(self.fdir):     # a previous run in this folder
            if f.startswith("f") and f.endswith(".png"):
                os.remove(os.path.join(self.fdir, f))
        shutil.rmtree(os.path.join(out, HIST_PARTS), ignore_errors=True)
        if os.path.exists(os.path.join(out, "history.npz")):
            os.remove(os.path.join(out, "history.npz"))
        self.done = {}                      # attribute -> rows written
        self.nframes = 0
        write_run_json(sim, out)

    def frame(self, img):
        img.save(os.path.join(self.fdir, f"f{self.nframes:04d}.png"))
        self.nframes += 1

    def flush(self):
        sim, out = self.sim, self.out
        n = self.done.get("events", 0)
        mode = "a" if n else "w"
        with open(os.path.join(out, "events.txt"), mode) as fh, \
                open(os.path.join(out, "events.jsonl"), mode) as fj:
            for e in sim.events[n:]:
                fh.write(f"{e['year']:5d}  {e['kind']:10s} {e['text']}\n")
                fj.write(json.dumps(event_row(sim, e)) + "\n")
        self.done["events"] = len(sim.events)
        for attr, name, head in APPEND:
            rows = getattr(sim, attr, [])
            n = self.done.get(attr, 0)
            if len(rows) <= n:
                continue
            with open(os.path.join(out, name), "a" if n else "w",
                      newline="") as fh:
                if head is None:
                    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                    if not n:
                        w.writeheader()
                else:
                    w = csv.writer(fh)
                    if not n:
                        w.writerow(head)
                w.writerows(rows[n:])
            self.done[attr] = len(rows)
        self.flush_long()
        write_wars(sim, out)
        write_rulers(sim, out)
        write_lineages(sim, out)
        write_cities(sim, out)
        write_polities(sim, out)
        write_dragons(sim, out)
        write_posts(sim, out)
        write_history_part(sim, out, self.done.get("hist", 0))
        self.done["hist"] = len(sim.hist)
        write_run_json(sim, out)

    def flush_long(self):
        """timeseries.csv's new rows again as year, people, variable,
        value (WP2 stage C); people is ALL for a world column. Empty
        values are left out."""
        from .runio import split_col
        rows, n = self.sim.ts, self.done.get("ts_long", 0)
        if len(rows) <= n:
            return
        keys = set(self.sim.keys)
        with open(os.path.join(self.out, "timeseries_long.csv"),
                  "a" if n else "w", newline="") as fh:
            w = csv.writer(fh)
            if not n:
                w.writerow(["year", "people", "variable", "value"])
            for r in rows[n:]:
                for c, v in r.items():
                    if c != "year" and v is not None:
                        w.writerow([r["year"], *split_col(c, keys), v])
        self.done["ts_long"] = len(rows)


def event_row(sim, e):
    """An event as written to events.jsonl: its fields, plus lon, lat,
    landmass id and landmass code (landmasses.py) where it has a cell."""
    r = dict(e)
    c = e.get("cell")
    if c is not None and c >= 0:
        W = sim.W
        lm = int(W.landmass[c])
        r.update(lon=round(float(W.lon[c]), 2), lat=round(float(W.lat[c]), 2),
                 landmass=lm, landmass_code=LANDMASS_CODES.get(lm))
    return r


def _landmass_codes():
    try:
        from landmasses import CODES
        return CODES
    except ImportError:         # wsim used without the sim folder on path
        return {}


LANDMASS_CODES = _landmass_codes()


def write_run_json(sim, out):
    with atomic(os.path.join(out, "run.json")) as fh:
        json.dump(run_info(sim), fh, indent=1, default=str)


def run_info(sim):
    """run.json's contents: the run's settings, code, switches and
    constants as used, and, for a branched run, its branch record."""
    man = getattr(sim, "manifest", {})
    return dict(seed=sim.seed, stream_seed=getattr(sim, "rseed", sim.seed),
                years=sim.years, dt=DT,
                year_reached=sim.year,
                frame_every=sim.frame_every,
                hist_every=getattr(sim, "hist_every", HIST_EVERY),
                code=man.get("code"), command=man.get("command"),
                python=man.get("python"), numpy=man.get("numpy"),
                wall_seconds=round(time.time() - man["t0"], 1)
                if "t0" in man else None,
                overrides=getattr(sim, "overrides", []),
                peoples=sim.P, vary=sim.vary, starts=sim.starts,
                start_vary=sim.start_vary, drift=sim.drift,
                start_pool=sim.start_pool,
                cluster_km=sim.cluster_km,
                settle_drift=sim.settle_drift,
                size_food=sim.size_food, city_pop=CITY_POP,
                start_mode=sim.start_mode,
                wander_steps=sim.wander_steps,
                city_cap=(CITY_CAP0, CITY_CAP1) if CITY_CAP else None,
                dragon_penalty=DRAGON_PEN, dragon_shun=DRAGON_SHUN,
                features=sorted(sim.on),
                constants=constants_used(),
                branch=man.get("branch"))


def write_wars(sim, out):
    if not sim.war_log:
        return
    with atomic(os.path.join(out, "wars.csv"), newline="") as fh:
        w = csv.writer(fh)
        w.writerow(WCOL)
        for r in sim.war_log:
            w.writerow([r.get(c, "ongoing" if c == "why" else "")
                        for c in WCOL])


def write_rulers(sim, out):
    if not sim.ruler_log:
        return
    with atomic(os.path.join(out, "rulers.csv"), newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ruler", "state", "people", "start", "end", "years",
                    "cities", "succession"] + (
                        ["dynasty", "violence", "dominance", "expansion",
                         "statecraft", "w", "gap"] if sim.rt else []) +
                   ["offense"])
        w.writerows(sim.ruler_log)


def write_lineages(sim, out):
    with atomic(os.path.join(out, "lineages.csv"), newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "people", "parent", "parent2", "how", "founded",
                    "ended", "fate",
                    "peak_pop", "stage", "agri", "metal", "sail", "fishing",
                    "war_mem", "trade_mem", "hard_mem", "raid_mem", "admin",
                    "r"] + TRAITS + XTRAITS + ["partibility", "superiority"])
        for L in range(sim.nL):
            stage = ("steel" if sim.steel[L] else "iron" if sim.iron[L] else
                     "bronze" if sim.bronze[L] else "")
            w.writerow([L, sim.keys[sim.Lpeople[L]], sim.Lparent[L],
                        sim.Lparent2[L] if sim.Lparent2[L] >= 0 else "",
                        sim.Lhow[L], sim.Lfounded[L],
                        sim.Lended[L] if sim.Lended[L] >= 0 else "",
                        sim.Lfate.get(L, ""),
                        int(sim.Lpeak[L]), stage, round(sim.agri[L], 3),
                        round(sim.metal[L], 3), round(sim.sail[L], 3),
                        round(sim.fishing[L], 3), round(sim.Lwarm[L], 4),
                        round(sim.Ltradem[L], 4), round(sim.Lhardm[L], 4),
                        round(sim.Lraidm[L], 4),
                        round(sim.admin[L], 3), round(sim.Lr[L], 4)] +
                       [round(v, 3) for v in sim.LT[L]] +
                       [round(v, 3) for v in sim.LX[L]] +
                       [round(sim.Lpart[L], 3), round(sim.Lsup[L], 3)])


def write_cities(sim, out):
    with atomic(os.path.join(out, "cities.csv"), newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "cell", "lon", "lat", "people", "founded", "ended",
                    "end_reason", "cause", "years", "peak_size", "peak_year",
                    "n_sacks", "n_rulers", "prev_city", "refounded",
                    "ruin_years", "ruin_empty_years", "successor", "rulers",
                    "minority_peoples", "minority_peak_share",
                    "minority_years", "majority_changes"])
        for r in sim.city_hist:
            end = r["ended"] if r["ended"] is not None else sim.year
            w.writerow([r["id"], r["cell"], f"{r['lon']:.2f}",
                        f"{r['lat']:.2f}", sim.keys[r["culture"]],
                        r["founded"], r["ended"], r["end_reason"],
                        r["cause"], end - r["founded"], int(r["peak"]),
                        r["peak_year"], r["n_sacks"], len(set(r["owners"])),
                        "" if r["prev"] is None else r["prev"],
                        "" if r["refounded"] is None else r["refounded"],
                        r["ruin_years"] if r["ended"] is not None else "",
                        r["ruin_empty"] if r["ended"] is not None else "",
                        "" if r["successor"] is None else r["successor"],
                        " ".join(f"P{x}" for x in dict.fromkeys(r["owners"])),
                        " ".join(sim.keys[c] for c in
                                 sorted(r.get("min_peoples", ()))),
                        round(r.get("min_peak", 0.0), 3),
                        r.get("min_years", 0), r.get("flips", 0)])


def write_polities(sim, out):
    with atomic(os.path.join(out, "polities.csv"), newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "people", "lineage", "peoples_ruled", "founded",
                    "ended", "years", "parent", "peak_cells", "peak_km2",
                    "peak_year", "peak_cities", "peak_pop", "capital_lon",
                    "capital_lat", "peak_foreign_share", "capital_cell",
                    "origin", "end_reason", "ended_by", "nb_land_mean",
                    "nb_sea_mean", "nb_max", "nb_none_years"])
        for p in sim.polities.values():
            nt = p.get("nb_ticks", 0)
            end = p["ended"] if p["ended"] is not None else sim.year
            cap = p["capital"]
            km2 = p.get("peak_km2", "")
            w.writerow([p["id"], sim.keys[p["culture"]], f"L{p['lin']}",
                        " ".join(sim.keys[c] for c in sorted(p["peoples"])),
                        p["founded"],
                        p["ended"], end - p["founded"], p["parent"],
                        p["peak_cells"], km2 and int(km2), p["peak_year"],
                        p["peak_cities"], int(p["peak_pop"]),
                        f"{sim.W.lon[cap]:.2f}", f"{sim.W.lat[cap]:.2f}",
                        round(p.get("peak_foreign", 0.0), 3), cap,
                        p.get("origin", ""), p.get("end_reason", ""),
                        "" if p.get("ended_by") is None else p["ended_by"],
                        round(p.get("nb_land", 0) / nt, 2) if nt else "",
                        round(p.get("nb_sea", 0) / nt, 2) if nt else "",
                        p.get("nb_max", "") if nt else "",
                        p.get("nb_none_years", 0) if nt else ""])


def write_dragons(sim, out):
    rows = sim.dragon_hist
    if not rows:
        return
    with atomic(os.path.join(out, "dragons.csv"), newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_posts(sim, out):
    with atomic(os.path.join(out, "posts.csv"), newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["planter", "host", "city", "lon", "lat", "year",
                    "people_planter", "people_host"])
        for k, (o, c, y) in sorted(sim.posts.items()):
            h = k[1] if k[0] == o else k[0]
            if o not in sim.polities or h not in sim.polities:
                continue
            w.writerow([o, h, c, f"{sim.W.lon[c]:.2f}", f"{sim.W.lat[c]:.2f}",
                        y, sim.keys[sim.polities[o]["culture"]],
                        sim.keys[sim.polities[h]["culture"]]])


HIST_PARTS = "history_parts"


def history_arrays(H, t0=0):
    """Snapshots H (dicts from Sim.snapshot) as history.npz's arrays.
    Per-cell layers are stacked (snapshot, cell); the per-snapshot tables
    are flat, each row with its snapshot index (t0 + position)."""
    def flat(k):
        rows = np.concatenate([h[k] for h in H])
        t = np.concatenate([np.full(len(h[k]), t0 + i)
                            for i, h in enumerate(H)])
        return rows, t
    S, st_t = flat("st")
    T, tie_t = flat("tie")
    C, city_t = flat("city")
    out = {k: np.stack([h[k] for h in H]) for k in
           ("people", "lineage", "polity", "minority", "pop_log1p",
            "herding")}
    out.update(
        year=np.array([h["year"] for h in H]),
        st_t=st_t, st_id=S[:, 0], st_cap=S[:, 1], st_people=S[:, 2],
        st_cities=S[:, 3], tie_t=tie_t, tie_a=T[:, 0].astype(int),
        tie_b=T[:, 1].astype(int), tie=T[:, 2], city_t=city_t,
        city_cell=C[:, 0].astype(np.int32), city_id=C[:, 1].astype(np.int32),
        city_size=C[:, 2].astype(np.float32),
        city_polity=C[:, 3].astype(np.int32), city_capital=C[:, 4] > 0)
    return out


def write_history_part(sim, out, n):
    """Snapshots from index n on, as one more part (a killed run keeps
    them; write_history joins the parts at the end)."""
    H = sim.hist[n:]
    if not H:
        return
    d = os.path.join(out, HIST_PARTS)
    os.makedirs(d, exist_ok=True)
    with atomic(os.path.join(d, f"h{n:05d}.npz"), "wb") as fh:
        np.savez_compressed(fh, **history_arrays(H, n))


def write_history(sim, out):
    """The whole history.npz, at the end of the run; the parts go."""
    if not sim.hist:
        return
    with atomic(os.path.join(out, "history.npz"), "wb") as fh:
        np.savez_compressed(fh, **history_arrays(sim.hist))
    shutil.rmtree(os.path.join(out, HIST_PARTS), ignore_errors=True)


def write_outputs(sim, out):
    """What needs the finished run. The tables and frames were written by
    Stream during Sim.run()."""
    fdir = os.path.join(out, "frames")
    files = sorted(f for f in os.listdir(fdir)
                   if f.startswith("f") and f.endswith(".png"))
    if files:
        # history.gif is gone (U, 2026-11-17): history.mp4 replaces it
        shutil.copyfile(os.path.join(fdir, files[-1]),
                        os.path.join(out, "final_maps.png"))
    write_history(sim, out)
    legacy_map(sim).save(os.path.join(out, "legacy.png"))
    lineage_map(sim).save(os.path.join(out, "lineages.png"))
    population_plot(sim, os.path.join(out, "population.png"))
    trait_plot(sim, os.path.join(out, "violence.png"))
    with open(os.path.join(out, "traits.txt"), "w") as fh:
        fh.write(f"seed {sim.seed}, people variation {sim.vary}, start-group "
                 f"variation {sim.start_vary}, lineage drift {sim.drift}\n\n")
        for c, p in enumerate(sim.P):
            fh.write(f"{p['key']} {p['label']}\n  r={p['r']:.4f}  " +
                     "  ".join(f"{t}={p.get(t, 0.5):.2f}" for t in TRAITS) +
                     "\n  affinity " + "  ".join(
                         f"{b}={v:.2f}" for b, v in p["affinity"].items()) +
                     (f"\n  head start {p['head']} yrs" if p.get("head")
                      else "") +
                     f"\n  size {sim.psize[c]:g}  food/head {sim.peat[c]:.2f}"
                     + "\n")
            for L in range(sim.nL):
                if sim.Lpeople[L] == c and sim.Lhow[L] == "start":
                    fh.write(f"    start {sim.lname(L)} r={sim.Lr[L]:.4f}  " +
                             "  ".join(f"{t[:4]}={sim.LT[L, k]:.2f}"
                                       for k, t in enumerate(TRAITS)) + "\n")
            fh.write("\n")
    great = {p["id"] for p in sorted(sim.polities.values(),
                                     key=lambda p: -p["peak_cells"])[:15]}
    always = {"origin", "contact", "trade", "tech", "voyage", "city",
              "fusion", "extinction"}
    with open(os.path.join(out, "chronicle.txt"), "w") as fh:
        fh.write("Major events only: world-firsts, great plagues and "
                 "droughts, and events touching the 15 largest states.\n\n")
        for e in sim.events:
            k = e["kind"]
            if k in always or (set(e.get("polities", ())) & great) or \
                    (k in ("plague", "drought") and e.get("n", 0) >= 2e6):
                fh.write(f"{e['year']:5d}  {k:10s} {e['text']}\n")
    np.savez_compressed(os.path.join(out, "final_state.npz"),
                        row=sim.W.row, col=sim.W.col, pop=sim.pop,
                        people=sim.cul, lineage=sim.lin, polity=sim.cell_pol,
                        city_years=sim.city_years, city_peak=sim.city_peak,
                        road=sim.road, improvements=sim.imp, land=sim.land,
                        minority_people=sim.mcul, minority_lineage=sim.mlin,
                        minority_pop=sim.mpop, waste=sim.waste,
                        salt=sim.salt,
                        river=sim.W.river, flow_to=sim.W.flow,
                        **((dict(
                            dragon_home=sim.dhome, dragon_ally=sim.dally,
                            dragon_age=sim.dage, dragon_tol=sim.dtol,
                            dragon_viol=sim.dviol, dragon_str=sim.dstr))))
    write_run_json(sim, out)
    # metrics.json from the files just written (WP2 stage B); a failure
    # there must not lose the run's other outputs
    try:
        from .runio import Run
        from . import metrics
        m = metrics.write(Run(out, W=sim.W))
        if "diagnostics" in sim.on:
            write_checks(m, os.path.join(out, "checks.txt"))
    except Exception as e:  # noqa: BLE001
        print(f"metrics failed ({e!r})")
    if getattr(sim, "video", True) and sim.hist:
        # history.mp4 (WP3 stage D): states above peoples, one frame per
        # snapshot, Mollweide; a failure must not lose the other outputs
        try:
            import render_run
            from .runio import Run
            render_run.make(Run(out, W=sim.W),
                            path=os.path.join(out, "history.mp4"),
                            verbose=False)
        except Exception as e:  # noqa: BLE001
            print(f"history.mp4 failed ({e!r})")
    if sim.hist:
        # viewer.html (WP3 stage D, U 2026-11-17): about 2 s
        try:
            import viewer
            from .runio import Run
            viewer.write(Run(out, W=sim.W), os.path.join(out, "viewer.html"))
        except Exception as e:  # noqa: BLE001
            print(f"viewer.html failed ({e!r})")
    if files:
        # 2x2 final.png and wars.png (figures.py); a failure there must
        # not lose the run's other outputs
        try:
            import figures
            figures.compose(out)
        except Exception as e:  # noqa: BLE001
            print(f"figures.py failed ({e!r}); final_maps.png kept")
