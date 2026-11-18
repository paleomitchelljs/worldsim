"""Records and the Price decomposition."""
import numpy as np

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
                         "gone",
                         peoples=[self.P[c]['key']])
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
               "flip_other", "ext_food", "war_tributary", "war_sack",
               "ff_rent", "ff_tax", "ff_trade"] + \
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
        # urban population (records): see urban()
        N = self.W.N
        cc = np.fromiter(self.cities.keys(), int) if self.cities else \
            np.zeros(0, int)
        okh = self.cell_city >= 0
        hint = np.bincount(self.cell_city[okh], weights=self.pop[okh],
                           minlength=N)
        hcells = np.bincount(self.cell_city[okh], minlength=N)
        U = self.urban(cc)
        fe_all = float((self.pop * self.peat[np.maximum(self.cul, 0)] *
                        (self.cul >= 0)).sum())
        self.ts[-1].update(
            urban_fe=round(float(U["urban"].sum())),
            urban_share=round(float(U["urban"].sum()) / max(fe_all, 1), 4),
            largest_city_fe=round(float(U["urban"].max()) if len(cc)
                                  else 0.0),
            cities_low_urban=int((U["urban"] < URBAN_MIN).sum()))
        food_now = self.year % CITY_TS_EVERY == 0
        for i, cell in enumerate(self.cities):
            hinter = hint[cell]
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
            # size until 2026-11-09: a fixed share of the city cell and
            # its hinterland; kept for comparison
            rec["size_old"] = (0.08 * self.pop[cell] + 0.04 * hinter) * \
                self.peat[self.cities[cell]["culture"]]
            size = float(U["urban"][i])
            self.city_size[cell] = size
            if food_now:
                src = {"land": U["k_rural"][i], "trade": U["trade"][i],
                       "rent": U["rent"][i], "provincial tax": U["prov"][i],
                       "capital": U["cap"][i]}
                P = self.polities.get(rec["polity"])
                self.food_rows.append(dict(
                    year=self.year, city_id=rec["id"], cell=int(cell),
                    people=self.keys[rec["culture"]], polity=rec["polity"],
                    capital=int(P is not None and P["capital"] == cell),
                    coastal=int(self.W.coastal[cell]),
                    river=int(self.W.river[cell]),
                    cell_pop=round(float(self.pop[cell])),
                    hinter_pop=round(float(hinter)),
                    hinter_cells=int(hcells[cell]),
                    k_rural=round(float(U["k_rural"][i])),
                    urban=round(size),
                    from_trade=round(float(U["trade"][i])),
                    from_rent=round(float(U["rent"][i])),
                    from_prov=round(float(U["prov"][i])),
                    from_capital=round(float(U["cap"][i])),
                    main_source=max(src, key=src.get)))
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
                    else "", round(rec.get("min_share", 0.0), 3),
                    round(rec.get("size_old", 0.0))))
            for cell, rec in self.ruins.items():
                c = self.cul[cell]
                self.city_ts.append((
                    self.year, rec["id"], cell,
                    "ruin, empty" if c < 0 else "ruin, settled", 0,
                    round(float(self.pop[cell])),
                    self.keys[c] if c >= 0 else "", -1, "", 0, 0))
        if self.year % 100 == 0 and self.ff_on:
            self.food_rows_flush()
        if self.year % 100 == 0:
            self.growth_flush()
        if self.year % 100 == 0 and self.deaths:
            for cause, v in self.deaths.items():
                for i in np.nonzero(v > 0)[0]:
                    self.death_rows.append(dict(
                        year=self.year, people=self.keys[i], cause=cause,
                        deaths=round(float(v[i]))))
            self.deaths = {}

    def dead(self, cause, cells, lost, minority=False):
        """Records: deaths by cause and people, summed per century into
        deaths.csv. cells None: lost is a whole-grid array."""
        cul = self.mcul if minority else self.cul
        c = np.atleast_1d(cul if cells is None else cul[cells])
        lost = np.atleast_1d(lost)
        ok = (c >= 0) & (lost > 0)
        if not ok.any():
            return
        acc = self.deaths.get(cause)
        if acc is None:
            acc = self.deaths[cause] = np.zeros(self.nP)
        v = np.bincount(c[ok], weights=lost[ok], minlength=self.nP)
        acc += v
        self.ac_dead += v

    def forgone(self, cells, lost, minority=False):
        """Records (WP4 stage C): growth that dragons' cut in the growth
        rate prevented, per people, summed per century into growth.csv.
        Not deaths: nobody was removed."""
        c = (self.mcul if minority else self.cul)[cells]
        ok = (c >= 0) & (lost > 0)
        self.ac["forgone_dragon"] += np.bincount(
            c[ok], weights=lost[ok], minlength=self.nP)

    # phases of a step, in order, for the growth account (WP4 stage C)
    PHASES = ["arrivals", "famine", "dragons", "grow", "migrate", "raids",
              "states", "minorities", "diplomacy", "wars", "rebellions",
              "culture", "disasters", "tidy"]

    def heads(self):
        """Heads per people, cell majorities and minorities."""
        n = self.nP
        a = self.cul >= 0
        b = self.mlin >= 0
        return np.bincount(self.cul[a], weights=self.pop[a], minlength=n) + \
            np.bincount(self.mcul[b], weights=self.mpop[b], minlength=n)

    def acct_mark(self, phase):
        """Records (WP4 stage C): the change in heads per people since the
        last mark, plus what was recorded as removed in between, is the
        phase's net change before removals. For `grow` that is natural
        increase; for any other phase it is people moving between peoples
        (conversion, assimilation) or, if it does not net to zero for the
        world, heads made or lost without a record. Heads added from no
        cell (`made`: merchant quarters, posts, garrisons) are taken out
        of the phase's net and shown on their own. Reads state only."""
        h = self.heads()
        if self.ac_last is not None:
            dm = self.ac_made - self.ac_mlast
            self.ac[phase] += h - self.ac_last + self.ac_dead - \
                self.ac_dlast - dm
            self.ac["made"] += dm
        else:
            # a branched state may hold deaths from before this mark
            self.ac["pop_start"] = h.copy()
            self.ac["d0"] = {c: v.copy() for c, v in self.deaths.items()}
        self.ac_last, self.ac_dlast = h, self.ac_dead.copy()
        self.ac_mlast = self.ac_made.copy()

    def growth_flush(self):
        """Records: growth.csv rows for the century just ended, per people
        and for the world (heads): start, end, natural increase, removals
        by cause, growth forgone under dragons, and each other phase's net
        change; `residual` = change - (natural - removals + the nets),
        which closes by construction up to rounding."""
        ac = self.ac
        if ac.get("pop_start") is None:
            return
        end = self.ac_last
        causes = sorted(self.deaths)
        rows = []
        for i, key in list(enumerate(self.keys)) + [(None, "ALL")]:
            def g(v):
                return float(v.sum() if i is None else v[i])
            r = dict(year=self.year, people=key,
                     pop_start=g(ac["pop_start"]), pop_end=g(end))
            r["change"] = r["pop_end"] - r["pop_start"]
            r["natural"] = g(ac["grow"])
            d0 = ac.get("d0", {})
            dd = {c: g(self.deaths[c] - d0.get(c, 0)) for c in causes}
            r["removals"] = sum(dd.values())
            nets = {f"net_{ph}": g(ac[ph]) for ph in self.PHASES
                    if ph != "grow"}
            r["made"] = g(ac["made"])
            r["residual"] = r["change"] - (r["natural"] - r["removals"] +
                                           r["made"] + sum(nets.values()))
            r["forgone_dragon"] = g(ac["forgone_dragon"])
            r.update(nets)
            for c in ("hunger", "feud", "raid", "war levies", "siege",
                      "sack", "clearance", "plague", "dragon attack",
                      "displaced", "expelled", "dwindled"):
                r[f"dead_{c.replace(' ', '_')}"] = dd.get(c, 0.0)
            if i is not None and r["pop_start"] <= 0 and r["pop_end"] <= 0:
                continue
            rows.append({k: (round(v) if isinstance(v, float) else v)
                         for k, v in r.items()})
        self.growth_rows += rows
        self.ac_new()
        self.ac["pop_start"] = end.copy()

    def ac_new(self):
        """A fresh growth-account accumulator for the century."""
        z = np.zeros(self.nP)
        self.ac = {ph: z.copy() for ph in self.PHASES}
        self.ac["forgone_dragon"] = z.copy()
        self.ac["made"] = z.copy()
        self.ac["pop_start"] = None

    # food ledger lines (WP4 stage A): per-cell lines, then per-state ones
    FL_CELL = ["produced", "produced_land", "produced_boost", "eaten",
               "taken_rent", "taken_tax", "taken_tribute", "lost_eff",
               "received_local", "received_capital", "created_trade",
               "city_food", "cap_unused", "received_smoothed",
               "taken_capacity", "trade_out", "trade_in"]
    FL_STATE = ["lost_vassal", "received_vassal", "unplaced", "lost_trade"]

    def food_ledger(self, f):
        """Records (WP4 stage A): one tick's food account, in
        food-equivalents, from food_flows' unsmoothed flows (f), summed
        for the world, per people and per state into fl_acc; record()
        writes the century means to food.csv. Produced is the raw
        capacity of every occupied cell (the main lineage's), split into
        land and the city boost; eaten is what its people and minority
        need; taken is rent, tax and tribute; lost is the 1 - EXT_EFF
        share and a vassal's carriage to its lord; received is what
        reaches cities and capitals; unplaced is a capital's take that
        has no city to arrive in. Reads state only."""
        W, N, n = self.W, self.W.N, self.next_pid
        pol, eat = self.cell_pol, self.peat
        occ = self.lin >= 0
        Q = f["Q"].copy()
        un = np.nonzero(occ & (pol < 0))[0]
        if len(un):
            Q[un] = self.Kf(self.lin[un], un, raw=True) * eat[self.cul[un]]
        boost = Q * (1 - 1 / self.cboost)
        fe = self.pop * eat[np.maximum(self.cul, 0)] * occ
        mok = self.mlin >= 0
        mfe = self.mpop * eat[np.maximum(self.mcul, 0)] * mok
        T = f["rent"] + f["tax"] + f["trib"]
        cc = f["cc"]
        city = np.zeros(N, bool)
        city[cc] = True
        recv = f["loc"] + f["cap"]
        made = 0 * Q if self.td_on else f["trade"]
        cols = [Q, Q - boost, boost, fe + mfe, f["rent"], f["tax"],
                f["trib"], (1 - EXT_EFF) * T, f["loc"], f["cap"],
                made, (Q + recv + f["trade"]) * city,
                f["cap"] * (self.cul != self.rul_c),
                self.ext_in + self.loc_in]
        # what the rates Kf applies remove from capacity: the main
        # lineage pays the ruling or the subject rate in full, not the
        # blend that T is worked out with; a minority pays on its own K
        m = pol >= 0
        own = self.cul == self.rul_c
        tc = Q * (np.where(own, self.ff_xo, self.ext_x) + self.tr_x) * m
        mo = np.nonzero(mok & m)[0]
        if len(mo):
            Km = self.Kf(self.mlin[mo], mo, raw=True) * eat[self.mcul[mo]]
            tc[mo] += Km * np.where(self.mcul[mo] == self.rul_c[mo],
                                    self.ff_xo[mo], self.ext_x[mo])
        cols += [tc, f["give"], f["trade"] - made]
        C = np.vstack(cols)
        pc = np.maximum(self.ptab()[1], 0)
        placed = np.bincount(np.maximum(pol[cc], 0), weights=f["cap"][cc],
                             minlength=n) if len(cc) else np.zeros(n)
        S = np.vstack([f["vs"] - f["va"], f["va"],
                       np.maximum(f["to_cap"] - placed, 0), f["tlost"]])
        nP = self.nP
        # world
        w = np.concatenate([C.sum(1), S.sum(1)])
        # per people: a cell's lines go to its people, a minority's
        # needs to the minority's, a state's lines to its ruling people
        c = np.maximum(self.cul, 0)
        Pp = np.vstack([np.bincount(c, weights=v * occ, minlength=nP)
                        for v in C])
        i = self.FL_CELL.index("eaten")
        Pp[i] = np.bincount(c, weights=fe, minlength=nP) + \
            np.bincount(np.maximum(self.mcul, 0), weights=mfe, minlength=nP)
        i = self.FL_CELL.index("received_smoothed")
        Pp[i] = np.bincount(c, weights=C[i] * occ, minlength=nP)
        Sp = np.vstack([np.bincount(pc[:n], weights=v, minlength=nP)
                        for v in S])
        # per state: cells it rules
        Ps = np.vstack([np.bincount(pol[m], weights=v[m], minlength=n)
                        for v in C])
        acc = self.fl_acc
        acc["ticks"] += 1
        acc["world"] += w
        acc["people"] += np.vstack([Pp, Sp])
        st = acc["state"]
        if st.shape[1] < n:
            st = acc["state"] = np.pad(st, ((0, 0), (0, n - st.shape[1])))
        st[:, :n] += np.vstack([Ps, S])

    def food_rows_flush(self):
        """Records: food.csv rows for the century just ended (mean per
        tick, food-equivalents), world, each people and each state that
        produced or received food, then a fresh accumulator."""
        acc = self.fl_acc
        k = acc["ticks"]
        if not k:
            return
        names = self.FL_CELL + self.FL_STATE

        def row(scope, key, v):
            d = dict(zip(names, v / k))
            taken = d["taken_rent"] + d["taken_tax"] + d["taken_tribute"]
            lost = d["lost_eff"] + d["lost_vassal"]
            recv = d["received_local"] + d["received_capital"]
            made = d["created_trade"] + d["produced_boost"]
            out = dict(year=self.year, scope=scope, key=key)
            out.update({x: round(d[x]) for x in names})
            out.update(taken=round(taken), lost=round(lost),
                       received=round(recv), created=round(made),
                       gap=round(taken - recv - lost),
                       gap_trade=round(d["trade_out"] - d["trade_in"] -
                                       d["lost_trade"]),
                       created_share=round(made / max(d["produced"], 1e-9),
                                           5),
                       created_share_city=round(
                           made / max(d["city_food"], 1e-9), 5))
            return out

        rows = self.fl_rows
        rows.append(row("world", "ALL", acc["world"]))
        for i, key in enumerate(self.keys):
            v = acc["people"][:, i]
            if v[0] > 0:
                rows.append(row("people", key, v))
        st = acc["state"]
        for pid in np.nonzero((st[0] > 0) | (st[8] + st[9] > 0))[0]:
            rows.append(row("state", int(pid), st[:, pid]))
        self.fl_new()

    def fl_new(self):
        """A fresh food-ledger accumulator."""
        m = len(self.FL_CELL) + len(self.FL_STATE)
        self.fl_acc = dict(ticks=0, world=np.zeros(m),
                           people=np.zeros((m, self.nP)),
                           state=np.zeros((m, 0)))

    def urban(self, cc):
        """Urban population of city cells cc, in food-equivalents
        (records; U 2026-11-09): the share of a city cell's people fed
        by what is brought in (trade, rent, tax, tribute) rather than by
        its own land at the base boost (1.5 x development), as a share of
        its capacity, capped at what that food feeds. With its
        parts: k_rural (the cell's own land, boosted), and the food
        arriving from trade, rent, provincial tax spending and the
        capital's take (`food_flow`; without it, the old trade term of the
        boost and `dominion`'s tribute)."""
        n = len(cc)
        out = {k: np.zeros(n) for k in ("urban", "k_rural", "trade",
                                        "rent", "prov", "cap")}
        if not n:
            return out
        L = self.lin[cc]
        ok = L >= 0
        c, Lc = cc[ok], L[ok]
        p = self.Lpeople[Lc]
        eat = self.peat[p]
        K = self.Kf(Lc, c)
        recv = np.zeros(len(c))
        if self.dom_on:
            recv = (p == self.rul_c[c]) * self.ext_in[c]
            if self.ff_on:
                recv = recv + (p == self.city_c[c]) * self.loc_in[c]
        base = np.maximum(K - recv / eat, 0)
        rural = base * self.cb0[c] / self.cboost[c]
        # urban share of the cell's people = share of its capacity that is
        # brought in, so a plague or a sack takes town and country alike;
        # at most what the food brought in feeds
        sh = np.clip((K - rural) / np.maximum(K, 1e-9), 0, 1)
        out["urban"][ok] = np.minimum(self.pop[c] * sh,
                                      np.maximum(K - rural, 0)) * eat
        out["k_rural"][ok] = rural * eat
        if self.ff_on:
            for k in ("rent", "prov", "cap", "trade"):
                out[k][ok] = self.ff_rec[k][c]
        else:
            out["trade"][ok] = (base - rural) * eat
            out["cap"][ok] = recv
        return out

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
