"""Records and the Price decomposition."""
import argparse
import importlib
import csv
import json
import math
import os
import sqlite3
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage, signal, sparse
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class DiagnosticsMixin:
    def people_summary(self):
        """Per people: population, living lineages, best tech stage, best
        farming level."""
        nP, nL = self.nP, self.nL
        occ = self.lin >= 0
        popc = np.bincount(self.cul[occ], weights=self.pop[occ], minlength=nP)
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        out = []
        for c in range(nP):
            Ls = np.nonzero((self.Lpeople[:nL] == c) & (Lpop > 0))[0]
            stage = ("St" if self.steel[Ls].any() else
                     "Fe" if self.iron[Ls].any() else
                     "Br" if self.bronze[Ls].any() else "")
            out.append(dict(pop=popc[c], nlin=len(Ls), stage=stage,
                            agri=float(self.agri[Ls].max()) if len(Ls) else 0,
                            metal=float(self.metal[Ls].max())
                            if len(Ls) else 0))
        return out

    def record(self):
        nP = self.nP
        occ = self.cul >= 0
        cells = np.bincount(self.cul[occ], minlength=nP)
        ncity = np.zeros(nP, int)
        for r in self.cities.values():
            ncity[r["culture"]] += 1
        live = [p for p in self.polities.values() if p["ended"] is None]
        big = max((p["n_cells"] for p in live), default=0)
        bigkm = max((p.get("km2", 0) for p in live), default=0)
        ps = self.people_summary()
        for c in range(nP):
            if ps[c]["pop"] > 0:
                self.p_seen[c] = True
            elif self.p_seen[c] and not self.p_extinct[c]:
                self.p_extinct[c] = True
                self.log("extinction", f"the last {self.P[c]['label']} are "
                         "gone")
        # population-weighted mean traits, world and per people
        o = np.nonzero(self.lin >= 0)[0]
        w, Lo, co = self.pop[o], self.lin[o], self.cul[o]
        tr = {}
        ZX = np.hstack([self.LT, self.LX])
        for t in ("violence", "tolerance", "expansion", "cohesion",
                  "conformity", "hierarchy", "trade"):
            v = ZX[Lo, (TRAITS + XTRAITS).index(t)]
            tr[f"{t}_world"] = float((w * v).sum() / max(w.sum(), 1))
            s = np.bincount(co, weights=w * v, minlength=nP)
            n = np.bincount(co, weights=w, minlength=nP)
            for i, k in enumerate(self.keys):
                tr[f"{t}_{k}"] = float(s[i] / n[i]) if n[i] > 0 else None
        v = self.Lsup[Lo]
        tr["superiority_world"] = float((w * v).sum() / max(w.sum(), 1))
        s = np.bincount(co, weights=w * v, minlength=nP)
        n = np.bincount(co, weights=w, minlength=nP)
        for i, k in enumerate(self.keys):
            tr[f"superiority_{k}"] = float(s[i] / n[i]) if n[i] > 0 \
                else None
        # structural measures
        live2 = [p for p in live if len(p["cities"]) >= 2]
        at_war = {x for k in self.wars for x in k}
        farmed = occ & ~self.herding
        st = dict(
            at_war_share=round(sum(p["id"] in at_war for p in live2) /
                               max(len(live2), 1), 3),
            revolts=self.n_revolts,
            vassals=len(self.vassal),
            herd_share=round(float((self.pop * self.herding).sum() /
                                   max(self.pop.sum(), 1)), 3),
            land_mean=round(float((self.land * self.pop * farmed).sum() /
                                  max((self.pop * farmed).sum(), 1)), 3),
            moisture=round(float((self.moist * self.pop).sum() /
                                 max(self.pop.sum(), 1)), 3),
            dry_pop_share=round(float(self.pop[self.moist < -1.5].sum() /
                                      max(self.pop.sum(), 1)), 3),
            famine_movers=round(self.famine_movers),
            avulsions=self.n_avulsions,
            road_cells=int((self.road > 0.3).sum()),
            improvements=round(float((self.imp * self.pop).sum() /
                                     max(self.pop.sum(), 1)), 3),
            minority_pop=float(self.mpop.sum()),
            stress_mean=round(float(np.mean([p["stress"] for p in live2]))
                              if live2 else 0.0, 3),
            bronze_users=int(self.bronze[:self.nL].sum()),
            cities_mixed_share=round(float(np.mean([
                r.get("min_share", 0.0) > 0.1 for r in self.cities.values()]))
                if self.cities else 0.0, 3))
        # the same columns every tick, empty before there are states
        st["crowd_mean"] = round(float(np.mean([p["crowd"]
                                                for p in live2])), 3) \
            if live2 else None
        st["room_mean"] = round(float(np.mean([p.get("room", 0)
                                               for p in live2])), 3) \
            if live2 else None
        st["pressured_share"] = round(float(np.mean(
            [self.pressure(p) > 0 for p in live2])), 3) \
            if live2 else None
        if "mission" in self.on:
            o3 = self.lin >= 0
            st["churn_mean"] = round(float(
                (self.Lchurn[self.lin[o3]] * self.pop[o3]).sum() /
                max(self.pop[o3].sum(), 1)), 4)
        irr = (self.lin >= 0) & (self.W.irr_share > 0.3)
        st["salt_irrigated"] = round(float(
            (self.salt * self.pop)[irr].sum() /
            max(self.pop[irr].sum(), 1)), 3)
        o2 = np.nonzero(self.lin >= 0)[0]
        w2 = self.pop[o2] / max(self.pop[o2].sum(), 1)
        L2 = self.lin[o2]
        st.update(
            craft_mean=round(float(w2 @ self.craft[L2]), 3),
            guarded=int(self.n_guard),
            res_held=int(sum(len(a["kinds"])
                             for a in self.passets.values())),
            dev_mean=round(float(w2 @ self.dev(L2)), 3),
            dom_mean=round(float(w2 @ self.domlv[L2].max(1)), 3)
            if len(self.h_cell) else 0.0,
            ties_cross=int(sum(1 for (x, y), t in self.ties.items()
                               if t > 0.3 and self.polities[x]["culture"]
                               != self.polities[y]["culture"])))
        st.update(self.dragon_record())
        self.n_revolts = 0
        CNT = ["city_revolt", "city_revolt_capital", "city_revolt_secede",
               "city_speciation", "lineage_absorb", "lineage_absorb_whole", "lineage_fuse",
               "lineage_fuse_whole", "city_new_elite",
               "fortress_toll", "fortress_heads",
               "ally_same", "ally_cross", "ally_balance", "ally_break",
               "union", "fusion", "vassal_submit_same", "vassal_submit_cross",
               "vassal_defect", "vassal_annex", "vassal_freed", "war_same",
               "war_cross", "capture_same", "capture_cross", "war_goal_met",
               "war_goal_resource", "war_goal_rule", "war_goal_land",
               "war_ceded", "war_goal_faith", "war_goal_prey",
               "war_goal_enmity", "war_goal_irredentism", "raid",
               "war_counter_capture", "ally_join", "ally_refuse",
               "ally_lapse", "ally_outgrown", "ally_betray",
               "ally_lapse_death", "partition", "union_crowns",
               "colony_state", "colony_displace", "colony_minority",
               "colony_city", "trade_post", "devastation",
               "devastation_city", "settler_heads", "flip_to_ruler",
               "flip_other", "ext_food"] + \
            [f"revolt_{k}{c}" for k in ("secession", "kin", "ethnic",
                                         "pretender")
             for c in ("", "_cities")] + \
            [f"dragon_{k}" for k in ("slain", "pushed", "lost", "ally",
                                     "freed", "born", "died")]
        st.update({f"n_{k}": self.cnt.get(k, 0) for k in CNT})
        self.cnt = {}
        st["city_years"] = len(self.cities) * DT
        # within-people structure: states, cities per state, and cultural
        # spread of lineages (pop-weighted mean distance from the people's
        # mean traits)
        nst = np.zeros(nP)
        ncs = np.zeros(nP)
        for p in live:
            nst[p["culture"]] += 1
            ncs[p["culture"]] += len(p["cities"])
        Lp = np.bincount(Lo, weights=w, minlength=self.nL)
        Ls = np.nonzero(Lp > 0)[0]
        for i, k in enumerate(self.keys):
            st[f"states_{k}"] = int(nst[i])
            st[f"cities_per_state_{k}"] = round(ncs[i] / nst[i], 2) \
                if nst[i] else None
            g = Ls[self.Lpeople[Ls] == i]
            if len(g):
                pw = Lp[g] / Lp[g].sum()
                mu = pw @ self.LT[g]
                st[f"spread_{k}"] = round(float(
                    pw @ np.linalg.norm(self.LT[g] - mu, axis=1)), 4)
            else:
                st[f"spread_{k}"] = None
        if "diagnostics" in self.on and self.year % PRICE_EVERY == 0:
            self.price()
        self.ts.append(dict(year=self.year, **st, **tr, **{
            f"pop_{k}": float(ps[i]["pop"]) for i, k in enumerate(self.keys)},
            **{f"cells_{k}": int(cells[i]) for i, k in enumerate(self.keys)},
            **{f"cities_{k}": int(ncity[i]) for i, k in enumerate(self.keys)},
            **{f"lineages_{k}": ps[i]["nlin"] for i, k in
               enumerate(self.keys)},
            n_polities=len(live), largest_polity_cells=int(big),
            largest_polity_Mkm2=round(bigkm / 1e6, 3),
            wars=len(self.wars), alliances=len(self.allies),
            multi_people_states=sum(1 for p in live
                                    if len(p["peoples"]) > 1),
            **{f"agri_{k}": ps[i]["agri"] for i, k in enumerate(self.keys)},
            **{f"metal_{k}": ps[i]["metal"] for i, k in
               enumerate(self.keys)}))
        for cell in self.cities:
            hinter = self.pop[self.cell_city == cell].sum()
            rec = self.cities[cell]
            ms = 0.0
            if self.mlin[cell] >= 0:
                a = self.pop[cell] * self.peat[self.cul[cell]]
                b = self.mpop[cell] * self.peat[self.mcul[cell]]
                ms = b / max(a + b, 1e-9)
                rec.setdefault("min_peoples", set()).add(int(self.mcul[cell]))
            rec["min_share"] = ms
            rec["min_peak"] = max(rec.get("min_peak", 0.0), ms)
            if ms > 0.1:
                rec["min_years"] = rec.get("min_years", 0) + DT
            size = 0.08 * self.pop[cell] + 0.04 * hinter
            size *= self.peat[self.cities[cell]["culture"]]
            self.city_size[cell] = size
            rec = self.cities[cell]
            if size > rec["peak"]:
                rec["peak"], rec["peak_year"] = size, self.year
            self.city_years[cell] += DT
            self.city_peak[cell] = max(self.city_peak[cell], size)
        for cell, rec in self.ruins.items():
            rec["ruin_years"] += DT
            rec["ruin_empty"] += DT * (self.lin[cell] < 0)
        if self.year % CITY_TS_EVERY == 0:
            for cell, rec in self.cities.items():
                self.city_ts.append((
                    self.year, rec["id"], cell, "city",
                    round(self.city_size.get(cell, 0.0)),
                    round(float(self.pop[cell])), self.keys[rec["culture"]],
                    rec["polity"],
                    self.keys[self.mcul[cell]] if self.mlin[cell] >= 0
                    else "", round(rec.get("min_share", 0.0), 3)))
            for cell, rec in self.ruins.items():
                c = self.cul[cell]
                self.city_ts.append((
                    self.year, rec["id"], cell,
                    "ruin, empty" if c < 0 else "ruin, settled", 0,
                    round(float(self.pop[cell])),
                    self.keys[c] if c >= 0 else "", -1, "", 0))

    def price(self):
        """Price-equation decomposition of the change in each cultural
        trait over the last PRICE_EVERY years, per people and for the
        world, with the lineages alive at the last snapshot as units.
        A lineage's offspring are its own cells now plus those of its
        descendant lineages; cells assimilated into it count as its
        offspring too, since that is how a culture reproduces here.
            wbar dzbar = Cov(w, z) + E(w dz)     (weights: ancestor pop)
        selection = Cov/wbar, transmission = E(w dz)/wbar."""
        nL = self.nL
        occ = self.lin >= 0
        wts = self.pop[occ] * self.peat[self.cul[occ]]
        Lpop = np.bincount(self.lin[occ], weights=wts, minlength=nL)
        alive = np.nonzero(Lpop > 0)[0]
        snap = self.price_snap
        ZT = np.hstack([self.LT, self.LX])
        EX = self.Lexp.copy()
        self.Lexp[:] = 0
        RU = self.Lrul.copy()
        self.Lrul[:] = 0
        self.price_snap = dict(L=alive, pop=Lpop[alive],
                               T=ZT[alive].copy(), year=self.year)
        if snap is None:
            return
        S = snap["L"]
        pos = -np.ones(nL, int)
        pos[S] = np.arange(len(S))
        # nearest ancestor in the snapshot, for every lineage alive now
        anc = -np.ones(nL, int)
        for j in alive:
            x = j
            while x >= 0 and pos[x] < 0:
                x = self.Lparent[x]
            anc[j] = pos[x] if x >= 0 else -1
        a = anc[alive]
        ok = a >= 0
        names = TRAITS + XTRAITS
        nS, nT = len(S), len(names)
        off = np.bincount(a[ok], weights=Lpop[alive][ok], minlength=nS)
        zoff = np.zeros((nS, nT))
        for k in range(nT):
            zoff[:, k] = np.bincount(a[ok], weights=(Lpop[alive] *
                                     ZT[alive, k])[ok], minlength=nS)
        z = snap["T"]
        zp = np.where(off[:, None] > 0, zoff / np.maximum(off, 1e-9)[:, None],
                      z)
        # the experience-driven part of each offspring group's change
        eoff = np.zeros((nS, nT))
        for k in range(nT):
            eoff[:, k] = np.bincount(a[ok], weights=(Lpop[alive] *
                                     EX[alive, k])[ok], minlength=nS)
        ze = np.where(off[:, None] > 0, eoff / np.maximum(off, 1e-9)[:, None],
                      0)
        roff = np.zeros((nS, nT))
        for k in range(nT):
            roff[:, k] = np.bincount(a[ok], weights=(Lpop[alive] *
                                     RU[alive, k])[ok], minlength=nS)
        zr = np.where(off[:, None] > 0, roff / np.maximum(off, 1e-9)[:, None],
                      0)
        p0 = snap["pop"]
        w = off / np.maximum(p0, 1e-9)
        peo = self.Lpeople[S]
        immig = Lpop[alive][~ok].sum() / max(Lpop.sum(), 1)
        groups = [(self.keys[c], peo == c) for c in range(self.nP)] + \
            [("ALL", np.ones(nS, bool))]
        for name, g in groups:
            if g.sum() < 2 or p0[g].sum() <= 0:
                continue
            pw = p0[g] / p0[g].sum()
            wg, zg, zpg, zeg, zrg = w[g], z[g], zp[g], ze[g], zr[g]
            wbar = float(pw @ wg)
            if wbar <= 0:
                continue
            zbar = pw @ zg
            cov = pw @ ((wg - wbar)[:, None] * (zg - zbar))
            trans = pw @ (wg[:, None] * (zpg - zg))
            expc = pw @ (wg[:, None] * zeg)
            rulc = pw @ (wg[:, None] * zrg)
            for k, t in enumerate(names):
                row = dict(
                    year=self.year, people=name, trait=t,
                    zbar=round(float(zbar[k]), 4),
                    dz=round(float((cov[k] + trans[k]) / wbar), 5),
                    selection=round(float(cov[k] / wbar), 5),
                    transmission=round(float(trans[k] / wbar), 5),
                    experience=round(float(expc[k] / wbar), 5),
                    wbar=round(wbar, 4), n_lineages=int(g.sum()),
                    immigrant_share=round(float(immig), 4))
                if self.rt:
                    row["ruler"] = round(float(rulc[k] / wbar), 5)
                self.price_rows.append(row)

    def relations(self):
        """Snapshot of every pair of neighbouring live states (by land or
        sea): similarity, each side's enmity and faith motives, trade tie,
        war, alliance, truce. Similarity and motives are the ones
        war_chance reads (the states' cultures with `city_culture`; until
        2026-11-07 they were the ruling lineages' whatever the switch);
        the last column is the ruling lineages' similarity. Reads state
        only (no draws)."""
        W = self.W

        def motives(A, B, sim):
            ta = self.eff(A, "tol")
            enm = ENM_K * (1 - sim) * (1 - ta)
            faith = (1 - sim) * (MIS_HOLY * self.eff(A, "pros") +
                                 MIS_BACKLASH * self.eff(B, "pros") *
                                 (1 - ta)) if "mission" in self.on else 0.0
            return enm, faith

        for k in sorted(self.adj | set(self.posts)):
            ab = self.live(k)
            if not ab:
                continue
            A, B = ab
            sim = self.ssim(A, B)
            ea, fa = motives(A, B, sim)
            eb, fb = motives(B, A, sim)
            self.rel.append((
                self.year, k[0], k[1], self.keys[A["culture"]],
                self.keys[B["culture"]], int(W.landmass[A["capital"]]),
                int(W.landmass[B["capital"]]), len(A["cities"]),
                len(B["cities"]), round(sim, 4), round(ea, 4), round(eb, 4),
                round(fa, 4), round(fb, 4), round(self.ties.get(k, 0.0), 4),
                int(k in self.wars), int(k in self.allies),
                int(self.truce.get(k, -1) > self.tick),
                round(self.similarity(A["lin"], B["lin"]), 4)))
