"""Output files."""
import contextlib
import csv
import json
import os
import re
import shutil
import time
import numpy as np
from PIL import Image

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403
from .render import *  # noqa: F401,F403


def write_checks(sim, path):
    """Compare a run with rough historical regularities. The references
    are orders of magnitude, not targets (docs/diagnostics.md)."""
    P = [p for p in sim.polities.values() if p["peak_cities"] >= 3]
    L = []
    for p in P:
        end = p["ended"] if p["ended"] is not None else sim.year
        if p["ended"] is not None:          # finished lives only
            L.append(end - p["founded"])
    L = np.array(L, float)
    lines = ["Stylized-fact checks (references are rough; see "
             "docs/diagnostics.md)", ""]
    if len(L):
        lines += [f"State lifespans (states that held 3+ cities and ended; "
                  f"n={len(L)}):",
                  f"  mean {L.mean():.0f} yrs, median {np.median(L):.0f}, "
                  f"CV {L.std() / max(L.mean(), 1):.2f}",
                  "  reference: mean ~200-250 yrs, roughly exponential "
                  "(CV ~1) [Arbesman 2011]", ""]
    sz = np.array(sorted((p["peak_cells"] for p in P), reverse=True), float)
    if len(sz) >= 10:
        lg = np.log(sz[sz > 0])
        sk = float(((lg - lg.mean()) ** 3).mean() / max(lg.std(), 1e-9) ** 3)
        lines += [f"State sizes at peak (cells, states with 3+ cities; "
                  f"n={len(sz)}):",
                  f"  largest {sz[0]:.0f}, 10th {sz[9]:.0f}, median "
                  f"{np.median(sz):.0f}; skew of log size {sk:+.2f}",
                  "  reference: heavy-tailed, roughly log-normal (skew of "
                  "log size near 0) [Taagepera 1978-97]", ""]
    cs = np.array(sorted(sim.city_size.values(), reverse=True), float)
    cs = cs[cs > 0][:200]
    if len(cs) >= 20:
        slope = np.polyfit(np.log(np.arange(1, len(cs) + 1)), np.log(cs), 1)[0]
        lines += [f"City rank-size (top {len(cs)} at the end): slope "
                  f"{slope:.2f}",
                  "  reference: about -1 (Zipf); pre-modern systems often "
                  "flatter, -0.6 to -1", ""]
    ws = [r["at_war_share"] for r in sim.ts if "at_war_share" in r]
    if ws:
        lines += [f"Share of states (2+ cities) at war, mean over run: "
                  f"{np.mean(ws):.2f}",
                  "  reference: high in pre-modern state systems; great "
                  "powers at war in most years [Levy 1983]. Uncertain.", ""]
    if sim.price_rows:
        lines += ["Price decomposition, summed over the run (ALL = world, "
                  "lineages as units):",
                  f"  {'trait':12s} {'dz':>8s} {'selection':>10s} "
                  f"{'transmission':>13s}"]
        for t in TRAITS:
            rows = [r for r in sim.price_rows
                    if r["people"] == "ALL" and r["trait"] == t]
            s = sum(r["selection"] for r in rows)
            tr = sum(r["transmission"] for r in rows)
            lines.append(f"  {t:12s} {s + tr:+8.3f} {s:+10.3f} {tr:+13.3f}")
        lines += ["", "  within peoples (mean over peoples of the summed "
                  "terms; selection | transmission):"]
        for t in TRAITS:
            ss, tt = [], []
            for k in sim.keys:
                rows = [r for r in sim.price_rows
                        if r["people"] == k and r["trait"] == t]
                if rows:
                    ss.append(sum(r["selection"] for r in rows))
                    tt.append(sum(r["transmission"] for r in rows))
            if ss:
                lines.append(f"  {t:12s} {np.mean(ss):+.3f} | "
                             f"{np.mean(tt):+.3f}")
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
        "moved_back", "helpers", "sacks"]

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
      "holder", "P_besieger", "P_holder", "odds", "taken", "terms"]),
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
]


class Stream:
    """Writes a run's output while it runs (2026-11-17, WP0 stage D).
    Append-only tables get their new rows at each flush; tables whose rows
    change later (wars, rulers, cities, polities, lineages, dragons, posts)
    and history.npz are rewritten whole under a temporary name. Frames are
    saved as they are rendered. Reads the Sim only. Not stored on the Sim,
    so a saved state stays picklable."""

    def __init__(self, sim, out):
        self.sim, self.out = sim, out
        self.fdir = os.path.join(out, "frames")
        os.makedirs(self.fdir, exist_ok=True)
        for f in os.listdir(self.fdir):     # a previous run in this folder
            if f.startswith("f") and f.endswith(".png"):
                os.remove(os.path.join(self.fdir, f))
        self.done = {}                      # attribute -> rows written
        self.nframes = 0
        write_run_json(sim, out)

    def frame(self, img):
        img.save(os.path.join(self.fdir, f"f{self.nframes:04d}.png"))
        self.nframes += 1

    def flush(self):
        sim, out = self.sim, self.out
        n = self.done.get("events", 0)
        with open(os.path.join(out, "events.txt"), "a" if n else "w") as fh:
            for y, k, t in sim.events[n:]:
                fh.write(f"{y:5d}  {k:10s} {t}\n")
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
        write_wars(sim, out)
        write_rulers(sim, out)
        write_lineages(sim, out)
        write_cities(sim, out)
        write_polities(sim, out)
        write_dragons(sim, out)
        write_posts(sim, out)
        write_history(sim, out)
        write_run_json(sim, out)


def write_run_json(sim, out):
    man = getattr(sim, "manifest", {})
    with atomic(os.path.join(out, "run.json")) as fh:
        json.dump(dict(seed=sim.seed, years=sim.years, dt=DT,
                       year_reached=sim.year,
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
                       constants=constants_used()), fh, indent=1,
                  default=str)


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
                         "statecraft", "w", "gap"] if sim.rt else []))
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
                    "capital_lat", "peak_foreign_share"])
        for p in sim.polities.values():
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
                        round(p.get("peak_foreign", 0.0), 3)])


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


def write_history(sim, out):
    H = sim.hist
    if not H:
        return
    cat = lambda k: np.concatenate([h[k] for h in H])
    idx = lambda k: np.concatenate([np.full(len(h[k]), t)
                                    for t, h in enumerate(H)])
    S, T = cat(4), cat(5)
    with atomic(os.path.join(out, "history.npz"), "wb") as fh:
        np.savez_compressed(
            fh,
            year=np.array([h[0] for h in H]), people=np.stack([h[1] for h in H]),
            pop=np.stack([h[2] for h in H]), polity=np.stack([h[3] for h in H]),
            st_t=idx(4), st_id=S[:, 0], st_cap=S[:, 1], st_people=S[:, 2],
            st_cities=S[:, 3], tie_t=idx(5), tie_a=T[:, 0].astype(int),
            tie_b=T[:, 1].astype(int), tie=T[:, 2])


def write_outputs(sim, out):
    """What needs the finished run. The tables and frames were written by
    Stream during Sim.run()."""
    fdir = os.path.join(out, "frames")
    files = sorted(f for f in os.listdir(fdir)
                   if f.startswith("f") and f.endswith(".png"))
    if files:
        pal = []
        for f in files:
            with Image.open(os.path.join(fdir, f)) as im:
                im = im.convert("RGB")
                small = im.resize((im.size[0] * 3 // 4, im.size[1] * 3 // 4),
                                  Image.LANCZOS)
                pal.append(small.quantize(colors=200,
                                          method=Image.Quantize.MEDIANCUT))
        pal[0].save(os.path.join(out, "history.gif"), save_all=True,
                    append_images=pal[1:], duration=140, loop=0,
                    optimize=False)
        shutil.copyfile(os.path.join(fdir, files[-1]),
                        os.path.join(out, "final_maps.png"))
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
        for y, k, t in sim.events:
            ids = {int(x) for x in re.findall(r"P(\d+)\(", t)}
            if k in always or (ids & great) or \
                    (k in ("plague", "drought") and "M" in t and
                     float(re.findall(r"([\d.]+)M", t)[0]) >= 2):
                fh.write(f"{y:5d}  {k:10s} {t}\n")
    if "diagnostics" in sim.on:
        write_checks(sim, os.path.join(out, "checks.txt"))
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
    if files:
        # 2x2 final.png and wars.png (figures.py); a failure there must
        # not lose the run's other outputs
        try:
            import figures
            figures.compose(out)
        except Exception as e:  # noqa: BLE001
            print(f"figures.py failed ({e!r}); final_maps.png kept")
