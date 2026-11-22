"""Cities, states, diplomacy, roads, rulers, revolts."""
import math
import numpy as np
from scipy import ndimage
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403
from .cities import CITY_COLS

RT_IDX = {a: k for k, a in enumerate(RT_TRAITS)}   # eff(): trait -> column


class StatesMixin:
    def ptab(self):
        """Live polities as arrays by id: rows ruling lineage, people,
        capital; -1 for ended ids. Rebuilt only when pver has moved: every
        write to a polity's lin, culture, capital or ended bumps it.
        Read-only."""
        key = (self.pver, self.next_pid)
        if self._ptab_key != key:
            t = np.full((3, self.next_pid), -1, int)
            for pid, P in self.polities.items():
                if P["ended"] is None:
                    t[0, pid], t[1, pid] = P["lin"], P["culture"]
                    t[2, pid] = -1 if P["capital"] is None else P["capital"]
            t.setflags(write=False)
            self._ptab, self._ptab_key = t, key
        return self._ptab

    def padm(self):
        """Administration of each live polity's ruling lineage by id, 0
        for ended ids (read now: administration changes within a tick)."""
        pl = self.ptab()[0]
        return np.where(pl >= 0, self.admin[np.maximum(pl, 0)], 0.0)

    def new_polity(self, L, capital, cohesion=0.6, parent=None,
                   origin="", camp=False):
        """A new state of lineage L seated at `capital`. origin (a record,
        WP2 stage C): city_outside, city_inside (founded inside a state it
        did not join), colony (a colonist lineage's city that did not join
        its home state), revolt_<kind>, partition or shatter."""
        pid = self.next_pid
        self.next_pid += 1
        self.pver += 1
        c = int(self.Lpeople[L])
        self.polities[pid] = dict(id=pid, culture=c, lin=int(L),
                                  capital=capital, founded=self.year,
                                  ended=None, cohesion=cohesion, trade=0.0,
                                  fed=1.0, crowd=0.5, elite=1.0, stress=0.0,
                                  herd=0.0, vassal_years=0,
                                  next_succ=self.year + SUCC_GEN * (
                                      self.plife[c] if "rulers" in self.on
                                      else 1),
                                  cities=set() if camp else {capital},
                                  camp=capital if camp else None,
                                  peak_cells=0,
                                  peak_year=self.year,
                                  peak_cities=0 if camp else 1,
                                  peak_pop=0, peak_mask=None, peoples=set(),
                                  parent=parent, origin=origin,
                                  end_reason="", ended_by=None,
                                  n_cells=0, strength=0,
                                  pop=0, col=self.polity_color(c))
        self.polities[pid]["gen"] = self.draw_general()
        self.polities[pid]["gen_legacy"] = 0.0
        if self.rt:
            x, dyn = self.draw_ruler(pid, self.polities[pid])
            self.polities[pid]["ruler"] = dict(id=-1, start=self.year, x=x,
                                               dyn=dyn)
        return pid

    def polity_color(self, c):
        base = self.colors[c].astype(float)
        wide = self.nP <= 5
        j = self.R("colour").uniform(0.55, 1.25) if wide else \
            self.R("colour").uniform(0.7, 1.15)
        h = self.R("colour").uniform(-28, 28, 3) if wide else \
            self.R("colour").uniform(-15, 15, 3)
        return np.clip(base * j + h, 20, 245).astype(np.uint8)

    def end_city(self, cell, why):
        rec = self.cities.pop(cell)
        rec["ended"] = self.year
        rec["end_reason"] = why
        rec["cause"] = self.end_cause(rec)
        rec["end_pop"] = float(self.pop[cell])
        self.ruins[cell] = rec
        p = self.polities.get(rec["polity"])
        if p:
            p["cities"].discard(cell)
            if p["capital"] == cell:
                self.recapital(p)

    def recapital(self, p):
        if not p["cities"]:
            self.kill_polity(p["id"], "lost its last city",
                             code="lost_last_city")
            return
        p["capital"] = max(p["cities"], key=self.city_weight)
        self.pver += 1

    def kill_polity(self, pid, why, by=None, code=""):
        """End state pid; why: the reason, for the log; by: the state
        that ended it, if any (the event's second polity); code: the
        reason as one word, for polities.csv (WP2 stage C)."""
        p = self.polities.get(pid)
        if p is None or p["ended"] is not None:
            return
        p["ended"] = self.year
        p["end_reason"], p["ended_by"] = code, by
        self.pver += 1
        self.vassal.pop(pid, None)
        for v in [v for v, o in self.vassal.items() if o == pid]:
            del self.vassal[v]
            self.count("vassal_freed")
        if p["peak_cities"] >= 3 or p["peak_cells"] >= 150:
            self.log("fall", f"{self.pname(pid)} falls ({why}); "
                     f"{self.year - p['founded']} yrs, peak "
                     f"{p['peak_cities']} cities / {p['peak_cells']} cells",
                     polities=[pid] + ([by] if by is not None else []),
                     n=p['peak_cities'])
        for key in [k for k in self.wars if pid in k]:
            w = self.wars.pop(key)
            side = "defender" if w.get("dfn") == pid else "attacker"
            self.war_close(w, f"{side} fell ({why})")
        for d in (self.ties, self.allies):
            for key in [k for k in d if pid in k]:
                del d[key]
        for c in list(p["cities"]):
            self.cities.get(c, {}).update(polity=-1)
        p["cities"] = set()

    def city_weight(self, c):
        """A city's size as the state's choices read it: the city cell's
        people, or under `urban_city` its urban population."""
        if self.uc_on:
            return self.city_size.get(c, 0.0)
        return self.pop[c]

    def update_cities(self):
        W = self.W
        for cell in list(self.cities):
            rec = self.cities[cell]
            if self.cul[cell] != rec["culture"]:
                self.end_city(cell, "people replaced")
            elif self.pop[cell] < CITY_KEEP * self.pcity[rec["culture"]]:
                self.end_city(cell, "depopulated")
            elif self.uc_on:
                # `urban_city`: a town that cannot feed townspeople ends
                low = self.city_size.get(cell, 0.0) < URBAN_MIN
                rec["low_years"] = rec.get("low_years", 0) + DT if low \
                    else 0
                if rec["low_years"] >= URBAN_YEARS and \
                        self.year - rec["founded"] >= URBAN_GRACE:
                    self.end_city(cell, "abandoned")
        pot2 = np.zeros((NY, NX))
        occ = self.lin >= 0
        fpop = np.where(occ, self.pop * self.peat[np.maximum(self.cul, 0)], 0)
        pot = fpop * W.locus
        # herders rarely found cities: their camps move
        fpop = np.where(self.herding, 0.3 * fpop, fpop)
        pot = fpop * W.locus
        pot2[W.row, W.col] = pot
        mx = ndimage.maximum_filter(pot2, size=5, mode="wrap")
        taken = np.zeros((NY, NX), bool)
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            taken[W.row[cc], W.col[cc]] = True
        if self.uc_on:
            # `urban_city`: not beside a town just abandoned
            ab = [x for x, r in self.ruins.items()
                  if r["end_reason"] == "abandoned" and
                  self.year - r["ended"] < URBAN_REFOUND]
            if ab:
                ab = np.array(ab, int)
                taken[W.row[ab], W.col[ab]] = True
        if taken.any():
            taken = ndimage.binary_dilation(taken, np.ones((5, 5)))
        settled = np.where(self.herding, 0.3, 1.0) * self.pop
        cand = np.nonzero(occ & (settled > self.pcity[np.maximum(
            self.cul, 0)]) &
                          (pot >= mx[W.row, W.col]) &
                          ~taken[W.row, W.col])[0]
        if self.uc_on and len(cand):
            # `urban_city`: no town is founded in famine
            cand = cand[self.pop[cand] <= 1.05 * self.Kf(self.lin[cand],
                                                          cand)]
        for cell in cand:
            c, L = int(self.cul[cell]), int(self.lin[cell])
            owner = int(self.cell_pol[cell])
            op = self.polities.get(owner)
            join = False
            origin = "city_outside"
            if op is not None and op["ended"] is None:
                origin = "city_inside"
                if op["culture"] == c:
                    join = self.R("cities").random() < \
                        0.3 + 0.7 * self.eff(op, "state")
                else:
                    join = self.R("cities").random() < 0.7
            elif self.Lcolony[L] >= 0:
                op = self.polities.get(int(self.Lcolony[L]))
                if op is not None and op["ended"] is None and \
                        op["culture"] == c:
                    owner = op["id"]
                    origin = "colony"
                    join = self.R("cities").random() < \
                        0.3 + 0.7 * self.eff(op, "state")
                    if join:
                        self.count("colony_city")
            rec = dict(cell=int(cell), culture=c, founded=self.year,
                       ended=None, end_reason="", peak=0.0, polity=-1,
                       lon=float(W.lon[cell]), lat=float(W.lat[cell]),
                       owners=[], id=len(self.city_hist), shocks=[],
                       peak_year=self.year, cause="", end_pop=0.0,
                       refounded=None, successor=None, ruin_empty=0,
                       ruin_years=0, n_sacks=0, prev=None)
            # a city founded near a ruin ends that ruin
            r0, c0 = W.row[cell], W.col[cell]
            for rc in [x for x in self.ruins
                       if abs(int(W.row[x]) - r0) <= 2 and
                       min(abs(int(W.col[x]) - c0),
                           NX - abs(int(W.col[x]) - c0)) <= 2]:
                old = self.ruins.pop(rc)
                old["refounded"] = self.year
                old["successor"] = rec["id"]
                if rec["prev"] is None:
                    rec["prev"] = old["id"]
            self.cities[cell] = rec
            self.city_hist.append(rec)
            if self.cc_on:
                self.city_found(rec, op if join else None)
            if join:
                rec["polity"] = owner
                op["cities"].add(cell)
            else:
                rec["polity"] = self.new_polity(L, cell, origin=origin)
            rec["owners"].append(rec["polity"])
            self.first(("city", c), "city", f"first city of {self.keys[c]} "
                       f"at {self.place(cell)}",
                       cell=cell, peoples=[self.keys[c]], cities=[rec['id']])

    def territory(self):
        W = self.W
        self.cell_pol[:] = -1
        self.cell_city[:] = -1
        # `camps`: camp seats rule land too, but are no city
        camps = {P["camp"]: P for P in self.polities.values()
                 if P.get("camp") is not None and P["ended"] is None and
                 P["camp"] not in self.cities}
        if not self.cities and not camps:
            return
        cc = np.array(list(self.cities.keys()) + list(camps), int)
        creach = np.zeros(W.N)
        creach[cc] = [self.reach(self.polities[self.cities[c]["polity"]])
                      if self.cities[c]["polity"] in self.polities else REACH0
                      for c in self.cities] + \
            [self.reach(P) for P in camps.values()]
        dist, _, src = dijkstra(W.G, indices=cc, min_only=True,
                                return_predecessors=True,
                                limit=max(1.5 * (REACH0 + REACH1),
                                          creach.max()) + 1)
        ok = src >= 0
        si = np.where(ok, src, 0)
        cpol = np.full(W.N, -1)
        cpol[cc] = [self.cities[c]["polity"] for c in self.cities] + \
            [P["id"] for P in camps.values()]
        iscity = np.zeros(W.N, bool)
        iscity[list(self.cities)] = True
        ok &= dist <= creach[si]
        self.cell_pol[ok] = cpol[src[ok]]
        ok &= iscity[si]
        self.cell_city[ok] = src[ok]
        # travel cost from each ruled cell to its city (`food_flow`)
        self.cdist = np.where(ok, dist, np.inf)

    def polity_stats(self):
        W = self.W
        n = self.next_pid
        pol = self.cell_pol
        m = pol >= 0
        Lpop = np.bincount(self.lin[self.lin >= 0],
                           weights=self.pop[self.lin >= 0], minlength=self.nL)
        pc = np.full(n, -1)
        pl = np.zeros(n, int)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                # a ruling lineage that has died out passes to the capital's
                cap = p["capital"]
                if Lpop[p["lin"]] <= 0 and self.lin[cap] >= 0:
                    p["lin"] = int(self.lin[cap])
                    p["dyn"] = self.year
                    p["culture"] = int(self.cul[cap])
                    self.pver += 1
                pc[pid], pl[pid] = p["culture"], p["lin"]
        own = m & (self.cul == pc[np.maximum(pol, 0)])
        # records: share of each state's people (food-equivalents) not of
        # its ruler's people, as majorities or minorities
        fe = self.pop * self.peat[np.maximum(self.cul, 0)] * (self.lin >= 0)
        mfe = self.mpop * self.peat[np.maximum(self.mcul, 0)] * \
            (self.mlin >= 0)
        pcm = pc[np.maximum(pol, 0)]
        # further peoples in a cell (WP7 C) count as minorities do
        x = self.xrows()
        xc, xp = self.rc[x], self.rp[x]
        xfe = self.rh[x] * self.peat[xp]
        xall = np.bincount(xc, weights=xfe, minlength=len(pol))
        xfor = np.bincount(xc, weights=xfe * (xp != pcm[xc]),
                           minlength=len(pol))
        tot_fe = np.bincount(pol[m], weights=(fe + mfe + xall)[m],
                             minlength=n)
        for_fe = np.bincount(pol[m], weights=(fe * (self.cul != pcm) +
                                              mfe * (self.mcul != pcm) +
                                              xfor)[m],
                             minlength=n)
        foreign = for_fe / np.maximum(tot_fe, 1e-9)
        tolp = self.tol[pl[np.maximum(pol, 0)]]
        popw = np.where(own, self.pop, (0.4 + 0.5 * tolp) * self.pop) * \
            self.psize[np.maximum(self.cul, 0)]
        popw = popw * np.where(self.herding, MOUNT, 1)
        mown = self.mcul == pc[np.maximum(pol, 0)]
        popw = popw + (self.mlin >= 0) * self.mpop * \
            self.psize[np.maximum(self.mcul, 0)] * \
            np.where(mown, 1, 0.4 + 0.5 * tolp)
        popw = popw + np.bincount(
            xc, minlength=len(pol), weights=self.rh[x] * self.psize[xp] *
            np.where(xp == pcm[xc], 1, 0.4 + 0.5 * tolp[xc]))
        pop_by = np.bincount(pol[m], weights=self.pop[m], minlength=n)
        str_by = np.bincount(pol[m], weights=popw[m], minlength=n)
        self._popw = popw               # for pol_refresh
        # fed share and crowding of each state's people, and its
        # herding share
        mo = np.nonzero(m & (self.lin >= 0))[0]
        K = np.maximum(self.Kf(self.lin[mo], mo), 1e-3)
        pw = self.pop[mo]
        fed_by = np.bincount(pol[mo], weights=np.minimum(pw, K),
                             minlength=n) / np.maximum(pop_by, 1)
        crowd_by = np.bincount(pol[mo], weights=pw * pw / K,
                               minlength=n) / np.maximum(pop_by, 1)
        herd_by = np.bincount(pol[mo], weights=pw * self.herding[mo],
                              minlength=n) / np.maximum(pop_by, 1)
        kown_by = np.bincount(pol[mo], weights=K * (
            self.cul[mo] == pc[pol[mo]]), minlength=n)
        kd_by = np.bincount(pol[mo], weights=K * self.peat[
            self.cul[mo]], minlength=n) / np.maximum(
            np.bincount(pol[mo], weights=W.area[mo], minlength=n), 1)
        churn_by = np.bincount(pol[mo], weights=pw *
                               self.Lchurn[self.lin[mo]],
                               minlength=n) / np.maximum(pop_by, 1)
        cells_by = np.bincount(pol[m], minlength=n)
        area_by = np.bincount(pol[m], weights=W.area[m], minlength=n)
        # assimilation: kin under a ruling lineage slowly take it on
        rl = pl[np.maximum(pol, 0)]
        kin = m & own & (self.lin >= 0) & (self.lin != rl)
        pk = (0.5 + self.pros[rl]) if "proselytism" in self.on else 1.0
        conv = kin & (self.R("polity").random(W.N) <
                      DT * 0.008 * (0.5 + self.state[rl]) * pk)
        self.lin[conv] = rl[conv]
        # borders
        pa, pb = pol[W.E1], pol[W.E2]
        frontier = np.zeros(n)
        border = np.zeros(n)
        for x, y, ex, ey in ((pa, pb, W.E1, W.E2), (pb, pa, W.E2, W.E1)):
            cy = self.cul[ey]
            b = (x >= 0) & (x != y)
            np.add.at(border, x[b], 1)
            f = b & (cy >= 0) & (cy != pc[np.maximum(x, 0)])
            # the steppe-sown border is a frontier too
            f |= b & (cy >= 0) & (self.herding[ex] != self.herding[ey])
            np.add.at(frontier, x[f], 1)
        adjm = (pa >= 0) & (pb >= 0) & (pa != pb)
        lo, hi = np.minimum(pa[adjm], pb[adjm]), np.maximum(pa[adjm],
                                                           pb[adjm])
        keys = np.unique(lo.astype(np.int64) * 10_000_000 + hi)
        self.adj = {(int(k // 10_000_000), int(k % 10_000_000))
                    for k in keys}
        land_adj = set(self.adj)
        self.adj |= self.sea_adjacency()
        self.neighbour_record(land_adj)
        self.state_room(n)
        for pid, p in self.polities.items():
            if p["ended"] is not None:
                continue
            L = p["lin"]
            mil = (0.5 + self.eff(p, "viol")) * (1 + METAL_MIL[0] * self.bronze[L] +
                                         METAL_MIL[1] * self.iron[L] +
                                         METAL_MIL[2] * self.steel[L])
            p["pop"] = pop_by[pid]
            p["n_cells"] = int(cells_by[pid])
            p["km2"] = float(area_by[pid])
            p["strength"] = str_by[pid] * mil * (0.3 + 0.7 * p["cohesion"])
            p["str_raw"] = float(str_by[pid])
            if pid in self.p_output:
                # gold and silver pay soldiers
                p["strength"] *= 1 + PREC_STR * min(
                    1.0, float(self.p_output[pid].sum()))
            if pop_by[pid] > 0:
                p["fed"] += over(FISC_EMA) * (fed_by[pid] - p["fed"])
                p["crowd"] += over(FISC_EMA) * (crowd_by[pid] - p["crowd"])
                p["herd"] = float(herd_by[pid])
                p["kdens"] = float(kd_by[pid])
                p["K_own"] = float(kown_by[pid])
            # armies are paid from the harvest, not from head count
            p["strength"] *= 0.4 + 0.6 * p["fed"]
            nd = self.d_by_pid.get(pid, 0)
            p["strength"] *= HIER_MIL0 + HIER_MIL1 * self.eff(p, "hier")
            if nd:
                # allied dragons fight for the state
                p["strength"] *= 1 + DRAGON_WAR * math.sqrt(nd)
            # elites multiply when land is crowded (cheap labour, high
            # rents) and thin out otherwise; stress = crowding x elite
            # load, worse when an extractive state goes hungry
            e = p["elite"]
            eg = ELITE_G * (0.5 + self.eff(p, "hier"))
            p["elite"] = float(np.clip(
                e + DT * eg * e * (p["crowd"] - ELITE_CROWD) /
                (1 - ELITE_CROWD), 0.3, 4))
            hunger = 1 - p["fed"]
            ext = self.eff(p, "hier")
            cost = 1 + COST_STATE * ext * hunger
            p["stress"] = max(0.0, p["crowd"] ** 2 * p["elite"] - 0.6) * \
                cost * (1 + 4 * hunger)
            if "mission" in self.on:
                # customs changing fast unsettle a state
                p["churn"] = float(churn_by[pid])
                p["stress"] += MIS_UNREST * p["churn"]
            ff = frontier[pid] / max(border[pid], 1)
            S = p["cohesion"]
            nc = len(p["cities"])
            age = self.year - p.get("dyn", p["founded"])
            dS = 0.04 * self.eff(p, "coh") * S * (1 - S) * (0.3 + ff) - \
                COH_DECAY * S * (1 + 0.5 * math.log1p(nc)) * (1 + age / 600)
            p["cohesion"] = float(np.clip(S + DT * dS, 0.02, 1))
            if p["n_cells"] > p["peak_cells"]:
                p["peak_cells"] = p["n_cells"]
                p["peak_year"] = self.year
                p["peak_km2"] = p["km2"]
                if p["n_cells"] >= 120:
                    p["peak_mask"] = np.nonzero(pol == pid)[0]
            p["peak_cities"] = max(p["peak_cities"], nc)
            if p.get("camp") is not None:
                p["camp_years"] = p.get("camp_years", 0) + DT
            p["peak_pop"] = max(p["peak_pop"], p["pop"])
            p["peak_foreign"] = max(p.get("peak_foreign", 0.0),
                                    float(foreign[pid]))
            for x in p["cities"]:
                p["peoples"].add(self.cities[x]["culture"])
        self.state_assets()
        # tribute: a share of each vassal's strength serves its lord
        for v, o in list(self.vassal.items()):
            V, O = self.polities.get(v), self.polities.get(o)
            if not V or not O or V["ended"] is not None or \
                    O["ended"] is not None:
                self.vassal.pop(v, None)
                continue
            t = VASSAL_TRIB * V["strength"]
            V["strength"] -= t
            O["strength"] += t
            V["vassal_years"] += DT

    def seated(self, P):
        """A state that can wage war: it holds a city or a camp."""
        return bool(P["cities"]) or P.get("camp") is not None

    def decamp(self):
        """`camps`: a camp polity that holds a city becomes an ordinary
        state, its largest city the capital."""
        for P in self.polities.values():
            if P.get("camp") is not None and P["ended"] is None and \
                    P["cities"]:
                P["camp"] = None
                P["capital"] = max(P["cities"], key=self.city_weight)
                self.pver += 1
                self.count("camp_city")
                self.log("camp", f"{self.pname(P['id'])}, a camp polity, "
                         f"takes its first city at "
                         f"{self.place(P['capital'])}",
                         cell=P["capital"], polities=[P["id"]])

    def camp_score(self, L, cells):
        """Heads x cohesion trait x (0.5 + hierarchy) of lineage L in
        cells."""
        return float(self.pop[cells].sum()) * float(self.coh[L]) * \
            (0.5 + float(self.hier[L]))

    def camps_step(self):
        """`camps`: camp polities form on stateless land, move their seat,
        and disperse (WP5 stage F)."""
        if "camps" not in self.on:
            return
        self.decamp()
        W, pol, lin = self.W, self.cell_pol, self.lin
        if self.year % CAMP_MOVE == 0:
            for P in self.polities.values():
                if P.get("camp") is None or P["ended"] is not None:
                    continue
                m = np.nonzero((pol == P["id"]) & (lin == P["lin"]))[0]
                m = m[~np.isin(m, list(self.cities))] if self.cities else m
                if len(m):
                    s = int(m[np.argmax(self.pop[m])])
                    if s != P["camp"]:
                        P["camp"] = P["capital"] = s
                        self.pver += 1
        if self.year % CAMP_EVERY:
            return
        rng = self.R("camps")
        for P in list(self.polities.values()):
            if P.get("camp") is None or P["ended"] is not None:
                continue
            m = np.nonzero((pol == P["id"]) & (lin == P["lin"]))[0]
            if self.camp_score(P["lin"], m) < CAMP_N * CAMP_END:
                self.count("camp_dispersed")
                self.kill_polity(P["id"], "dispersed", code="dispersed")
        st = np.nonzero((pol < 0) & (lin >= 0))[0]
        if not len(st):
            return
        if self.cities:
            st = st[~np.isin(st, list(self.cities))]
        order = np.lexsort((-self.pop[st], lin[st]))
        st = st[order]
        Ls, first = np.unique(lin[st], return_index=True)
        bounds = list(first[1:]) + [len(st)]
        taken = np.zeros(W.N, bool)
        for L, a, b in zip(Ls, first, bounds):
            c = st[a:b]
            top = int(c[0])                 # densest (sorted)
            if taken[top]:
                continue
            near = c[gc_km(W.xyz, top, c) <= CAMP_R]
            if self.camp_score(L, near) < CAMP_N or \
                    rng.random() >= CAMP_P:
                continue
            # the land the camp would rule: its lineage's stateless cells
            # within a new camp's reach (cohesion 0.6) of the seat
            r = CAMP_REACH * 0.6 * (1 + CAMP_HERD *
                                    float(self.herding[near].mean()))
            d = dijkstra(W.G, indices=top, limit=r)
            near = near[d[near] <= r]
            if self.camp_score(L, near) < CAMP_N:
                continue
            taken[near] = True
            pid = self.new_polity(int(L), top, cohesion=0.6, origin="camp",
                                  camp=True)
            self.count("camp_formed")
            self.log("camp", f"{self.lname(int(L))} gathers under a camp "
                     f"polity {self.pname(pid)} at {self.place(top)}",
                     cell=top, polities=[pid])

    def pol_refresh(self):
        """`pol_step`: after a political sub-step in which cities changed
        hands, redraw territory and scale each state's strength by the
        change in its weighted people (the tick's per-cell weights).
        A state founded in the tick takes its parent's strength per
        weighted head (else the median's). Smoothed values, cohesion and
        adjacency wait for the next tick."""
        self.territory()
        self._pt = {}
        popw = getattr(self, "_popw", None)
        if popw is None or len(popw) != self.W.N:
            return
        pol, n = self.cell_pol, self.next_pid
        m = pol >= 0
        str_by = np.bincount(pol[m], weights=popw[m], minlength=n)
        pop_by = np.bincount(pol[m], weights=self.pop[m], minlength=n)
        cells_by = np.bincount(pol[m], minlength=n)
        live = [p for p in self.polities.values() if p["ended"] is None]
        ratio = [p["strength"] / p["str_raw"] for p in live
                 if p.get("str_raw", 0) > 0]
        med = float(np.median(ratio)) if ratio else 1.0
        for p in live:
            r, new = p.get("str_raw", 0.0), float(str_by[p["id"]])
            if r > 0:
                p["strength"] *= new / r
            elif new > 0:
                q = self.polities.get(p.get("parent"))
                f = q["strength"] / q["str_raw"] if q and \
                    q.get("str_raw", 0) > 0 else med
                p["strength"] = new * f
            p["str_raw"] = new
            p["pop"] = float(pop_by[p["id"]])
            p["n_cells"] = int(cells_by[p["id"]])

    def extraction(self):
        """`dominion`: each state takes part of its subjects' harvest
        (more from cities) and feeds its ruling people in its cities with
        what reaches them. Sets the per-cell ruling people, establishment,
        rate and food received that capacity and shared cells read."""
        if not self.dom_on:
            return
        n, pol = self.next_pid, self.cell_pol
        m = pol >= 0
        pl, pc = self.ptab()[:2]
        pl = np.maximum(pl, 0)              # ended ids: lineage 0, unread
        xr = np.zeros(n)
        for pid, P in self.polities.items():
            if P["ended"] is None:
                xr[pid] = EXT_SUBJ * (0.5 + self.eff(P, "hier"))
        pp = np.maximum(pol, 0)
        self.rul_c = np.where(m, pc[pp], -1)
        Lr = pl[pp]
        self.rul_est = np.where(m, np.clip(
            self.admin[Lr] * (0.5 + self.state[Lr]), 0, 1), 0)
        if self.ff_on:
            self.food_flows()
            return
        city = self.cell_city == np.arange(self.W.N)
        x = np.where(m, xr[pp], 0) * np.where(city, EXT_CITY, 1)
        self.ext_x = np.minimum(x, EXT_MAX)
        fe = self.pop * self.peat[np.maximum(self.cul, 0)] * \
            (self.lin >= 0)
        mfe = self.mpop * self.peat[np.maximum(self.mcul, 0)] * \
            (self.mlin >= 0)
        subj = fe * (self.cul != self.rul_c) + mfe * (self.mcul != self.rul_c)
        own = fe * (self.cul == self.rul_c) + mfe * (self.mcul == self.rul_c)
        x = self.xrows()
        if len(x):
            # further peoples in a cell (WP7 C)
            xc, xp = self.rc[x], self.rp[x]
            xfe = self.rh[x] * self.peat[xp]
            xo = xp == self.rul_c[xc]
            subj = subj + np.bincount(xc, weights=xfe * ~xo,
                                      minlength=len(subj))
            own = own + np.bincount(xc, weights=xfe * xo,
                                    minlength=len(own))
        take = np.bincount(pol[m], weights=(self.ext_x * subj)[m],
                           minlength=n) * EXT_EFF
        cc = np.fromiter(self.cities.keys(), int) if self.cities else \
            np.zeros(0, int)
        cc = cc[pol[cc] >= 0]
        w = own[cc]
        wsum = np.bincount(pol[cc], weights=w, minlength=n)
        new = np.zeros(self.W.N)
        new[cc] = take[pol[cc]] * w / np.maximum(wsum[pol[cc]], 1e-9)
        # a state with none of its people in a city feeds its capital
        for pid, P in self.polities.items():
            if P["ended"] is None and take[pid] > 0 and wsum[pid] <= 0 \
                    and P.get("capital", -1) >= 0:
                new[P["capital"]] += take[pid]
            if P["ended"] is None:
                P["extract"] = float(take[pid])
        self.ext_in += over(FISC_EMA) * (new - self.ext_in)
        self.count("ext_food", float(take.sum()))

    def city_cells(self, pid):
        """Cells of state pid's cities."""
        return np.array([c for c in self.polities[pid]["cities"]
                         if c in self.cities], dtype=int)

    def trade_dist(self, pid):
        """`trade_debit`: food distance (cost-km) from the nearest of
        state pid's cities to every cell, over the food graph; inf beyond
        FF_LIMIT x FF_CAP_KM. Cached on the cities and the graph's
        version."""
        W = self.W
        cs = self.city_cells(pid)
        key = (tuple(sorted(cs.tolist())), W.fver)
        c = self.fdist.get((pid, "cities"))
        if c is None or c[0] != key:
            if len(cs):
                d = dijkstra(W.Gf, indices=cs, min_only=True,
                             limit=FF_LIMIT * FF_CAP_KM).astype(np.float32)
            else:
                d = np.full(W.N, np.inf, np.float32)
            c = (key, d)
            self.fdist[(pid, "cities")] = c
        return c[1]

    def food_dist(self, P):
        """`food_flow`: food distance (cost-km) from state P's capital to
        every cell, over the food graph; inf beyond FF_LIMIT x FF_CAP_KM.
        Cached on the capital and the graph's version; a graph change that
        touches no cell within the limit leaves it as it was (as in
        `power_dist`)."""
        W = self.W
        c = self.fdist.get(P["id"])
        key = (P["capital"], W.fver)
        if c is not None and c[0][0] == key[0] and c[0][1] != key[1]:
            ch = W.changed_since(c[0][1], "f")
            if ch is not None and np.isinf(c[1][ch]).all():
                c = self.fdist[P["id"]] = (key, c[1])
        if c is None or c[0] != key:
            d = dijkstra(W.Gf, indices=P["capital"],
                         limit=FF_LIMIT * FF_CAP_KM).astype(np.float32)
            c = (key, d)
            self.fdist[P["id"]] = c
        return c[1]

    def food_flows(self):
        """`food_flow`: rent, tax, tribute and trade food. Sets the rates
        each people pays (ext_x for others, ff_xo for the ruling people),
        the food the ruling people receive at the capital (ext_in) and the
        food a city's people receive in their city (loc_in)."""
        W, N, pol = self.W, self.W.N, self.cell_pol
        n = self.next_pid
        m = pol >= 0
        pp = np.maximum(pol, 0)
        hp = np.zeros(n)
        live = [pid for pid, P in self.polities.items()
                if P["ended"] is None]
        for pid in live:
            # `camps`: a camp has no city to take food to
            if self.polities[pid].get("camp") is None:
                hp[pid] = 0.5 + self.eff(self.polities[pid], "hier")
        h = np.where(m, hp[pp], 0.0)
        cc = np.fromiter(self.cities.keys(), int) if self.cities else \
            np.zeros(0, int)
        city = np.zeros(N, bool)
        city[cc] = True
        # nominal rates: rent (what can be carted to town), tax, tribute
        eloc = np.exp(-self.cdist / FF_KM)
        xr = FF_RENT * h * eloc * ~city * (self.cell_city >= 0)
        xo = np.where(city, 0.0, FF_TAX * h)
        xs = EXT_SUBJ * h * np.where(city, EXT_CITY, 1)
        xo_n = np.minimum(xr + xo, EXT_MAX) * m
        xs_n = np.minimum(xr + xs, EXT_MAX) * m
        ro = xr / np.maximum(xr + xo, 1e-12)      # rent's share of each
        rs = xr / np.maximum(xr + xs, 1e-12)
        # what the land yields and what its people eat (food-equivalents)
        eat = self.peat
        o = np.nonzero(m & (self.lin >= 0))[0]
        Qa = np.zeros(N)                          # main lineage
        Qa[o] = self.Kf(self.lin[o], o, raw=True) * eat[self.cul[o]]
        Qb = np.zeros(N)                          # minority
        mo = np.nonzero(m & (self.mlin >= 0))[0]
        Qb[mo] = self.Kf(self.mlin[mo], mo, raw=True) * eat[self.mcul[mo]]
        Q = Qa + Qb
        fe = self.pop * eat[np.maximum(self.cul, 0)] * (self.lin >= 0)
        mfe = self.mpop * eat[np.maximum(self.mcul, 0)] * (self.mlin >= 0)
        own_a = self.cul == self.rul_c
        own_b = self.mcul == self.rul_c
        own_fe = fe * own_a + mfe * own_b
        need = fe + mfe
        # each lineage pays its own people's rate on its own capacity
        # (WP4 D: before, one blended rate on the main lineage's capacity
        # alone, and a minority's payment was lost)
        Qo = Qa * own_a + Qb * own_b
        x = self.xrows()
        x = x[m[self.rc[x]]]
        if len(x):
            # further peoples in a cell (WP7 C), as the minority
            xc, xp = self.rc[x], self.rp[x]
            xo = xp == self.rul_c[xc]
            Qx = self.Kf(self.rl[x], xc, raw=True) * eat[xp]
            xfe = self.rh[x] * eat[xp]
            Q = Q + np.bincount(xc, weights=Qx, minlength=N)
            Qo = Qo + np.bincount(xc, weights=Qx * xo, minlength=N)
            need = need + np.bincount(xc, weights=xfe, minlength=N)
            own_fe = own_fe + np.bincount(xc, weights=xfe * xo, minlength=N)
        sub_fe = need - own_fe
        Qs = Q - Qo
        # peasants eat first: FF_FORCE of the nominal take comes whatever
        # the harvest, the rest only from what is left after they eat
        nom_o, nom_s = xo_n * Qo, xs_n * Qs
        To = FF_FORCE * nom_o + (1 - FF_FORCE) * \
            np.clip(Qo - own_fe, 0, nom_o)
        Ts = FF_FORCE * nom_s + (1 - FF_FORCE) * \
            np.clip(Qs - sub_fe, 0, nom_s)
        T = To + Ts
        self.ff_xo = np.where(nom_o > 0, To / np.maximum(Qo, 1e-12), xo_n)
        self.ext_x = np.where(nom_s > 0, Ts / np.maximum(Qs, 1e-12), xs_n)
        rent = To * ro + Ts * rs
        tax = T - rent
        # absentee landlords: part of the ruling people's rent goes to the
        # capital with the tax
        absent = FF_ABS * To * ro
        rent = rent - absent
        tax = tax + absent
        # tax reaches the capital as far as it can be carried; the rest
        # is spent in the cell's own city
        ecap = np.ones(N)
        if len(o):
            srt = o[np.argsort(pol[o], kind="stable")]
            ps = pol[srt]
            lo = np.searchsorted(ps, live, "left")
            hi = np.searchsorted(ps, live, "right")
            for i, pid in enumerate(live):
                P = self.polities[pid]
                if len(P["cities"]) < 2 or hi[i] == lo[i]:
                    continue          # one city: capital and town are one
                cells = srt[lo[i]:hi[i]]
                ecap[cells] = np.exp(-self.food_dist(P)[cells] / FF_CAP_KM)
        loc = (rent + tax * (1 - ecap)) * EXT_EFF
        to_cap = np.bincount(pol[m], weights=(tax * ecap)[m],
                             minlength=n) * EXT_EFF
        # a vassal sends part of its capital's take to its lord
        vs, va = np.zeros(n), np.zeros(n)          # records: sent, arrived
        for v, lord in self.vassal.items():
            V, O = self.polities.get(v), self.polities.get(lord)
            if V is None or O is None or V["ended"] is not None or \
                    O["ended"] is not None or to_cap[v] <= 0:
                continue
            d = self.food_dist(O)[V["capital"]]
            sent = FF_VASSAL * to_cap[v]
            got = sent * math.exp(-float(d) / FF_CAP_KM)
            to_cap[v] -= sent
            to_cap[lord] += got
            vs[v] += sent
            va[lord] += got
        new_cap = np.zeros(N)
        for pid in live:
            cap = self.polities[pid]["capital"]
            if cap in self.cities:
                new_cap[cap] += to_cap[pid]
        cs = self.cell_city
        ok = m & (cs >= 0)
        new_loc = np.bincount(cs[ok], weights=loc[ok], minlength=N)
        new_rent = np.bincount(cs[ok], weights=(rent * EXT_EFF)[ok],
                               minlength=N)
        # trade: a gravity form over trade ties, into each state's cities
        # by size and waterside
        FE = np.bincount(pol[m], weights=need[m], minlength=n)
        new_trade = np.zeros(N)
        ws = np.zeros(n)
        if len(cc):
            cp = np.array([self.cities[c]["polity"] for c in cc])
            okc = cp >= 0
            c2, p2 = cc[okc], cp[okc]
            wc = (0.5 + 0.5 * np.maximum(W.coastal[c2], W.river[c2])) * \
                need[c2]
            ws = np.bincount(p2, weights=wc, minlength=n)
        give, tlost = np.zeros(N), np.zeros(n)
        if self.td_on:
            give, V, tlost = self.debit_trade(Q, need, T, FE, ws, n)
        else:
            V = np.zeros(n)
            for (a, b), t in self.ties.items():
                if t > 0 and FE[a] > 0 and FE[b] > 0 and self.live((a, b)):
                    g = FF_TRADE * t * math.sqrt(FE[a] * FE[b])
                    V[a] += g
                    V[b] += g
        if len(cc):
            new_trade[c2] = V[p2] * wc / np.maximum(ws[p2], 1e-9)
        a = over(FISC_EMA)
        if self.td_on:
            tr = give / np.maximum(Q, 1e-9)     # on both lineages
            self.tr_x += a * (tr - self.tr_x)
        self.ext_in += a * (new_cap - self.ext_in)
        self.loc_in += a * (new_loc + new_trade - self.loc_in)
        # records
        fr = self.ff_rec
        fr["rent"] += a * (new_rent - fr["rent"])
        fr["prov"] += a * (new_loc - new_rent - fr["prov"])
        fr["cap"] += a * (new_cap - fr["cap"])
        fr["trade"] += a * (new_trade - fr["trade"])
        self.city_c[:] = -1
        self.city_c[cc] = self.cul[cc]
        trib = Ts * (1 - rs)
        self.food_ledger(dict(
            Q=Q, rent=rent, tax=tax - trib, trib=trib, to_cap=to_cap,
            vs=vs, va=va, loc=new_loc, cap=new_cap, trade=new_trade, cc=cc,
            give=give, tlost=tlost))
        for pid in live:
            self.polities[pid]["extract"] = float(to_cap[pid])
        self.count("ext_food", float(T.sum()))
        self.count("ff_rent", float(rent.sum()))
        self.count("ff_tax", float(tax.sum()))
        self.count("ff_trade", float(new_trade.sum()))

    def debit_trade(self, Q, need, T, FE, ws, n):
        """`trade_debit` (WP4 stage B; C): trade food that some cell grew.
        Each tie carries today's gravity flow, FF_TRADE x tie x
        sqrt(FE_a x FE_b), one way: from the state with more marketable
        surplus per head (TRADE_SURPLUS of what its cells grow beyond
        what their people eat and the state takes) to the one with less.
        An exporter's flows are scaled down together to its surplus, and
        debited from its cells in proportion to their surplus, so selling
        cannot make the sellers hungry. What leaves arrives at the
        importer, less carriage over the food graph between the nearest
        pair of their cities (exp(-d / FF_CAP_KM), as tax; WP4 D, U: port
        to port, where before it was capital to capital). Over water the
        nearest pair are ports, since the food graph's sea edges are
        cheap. A pair beyond the food graph's reach does not trade food. Returns the debit per cell,
        the food arriving per state and the food lost per exporter."""
        pol = self.cell_pol
        m = pol >= 0
        for k in [k for k in self.fdist if isinstance(k, tuple) and
                  self.polities.get(k[0], {}).get("ended", 1) is not None]:
            del self.fdist[k]
        s = np.maximum(Q - need - T, 0) * TRADE_SURPLUS * m
        S = np.bincount(pol[m], weights=s[m], minlength=n)
        per = S / np.maximum(FE, 1e-9)
        flows, want = [], np.zeros(n)
        for (a, b), t in self.ties.items():
            if t <= 0 or FE[a] <= 0 or FE[b] <= 0 or per[a] == per[b] or \
                    not self.live((a, b)):
                continue
            x, y = (a, b) if per[a] > per[b] else (b, a)
            if ws[y] <= 0:
                continue                  # no city to arrive in
            yc = self.city_cells(y)
            if not len(yc):
                continue
            d = float(self.trade_dist(x)[yc].min())
            if not math.isfinite(d):
                continue
            g = FF_TRADE * t * math.sqrt(FE[a] * FE[b])
            flows.append((x, y, g, math.exp(-d / FF_CAP_KM)))
            want[x] += g
        scale = np.minimum(1.0, S / np.maximum(want, 1e-12))
        out, arr, lost = np.zeros(n), np.zeros(n), np.zeros(n)
        for x, y, g, e in flows:
            f = g * scale[x]
            out[x] += f
            arr[y] += f * e
            lost[x] += f * (1 - e)
        give = s * (out / np.maximum(S, 1e-12))[np.maximum(pol, 0)] * m
        return give, arr, lost

    def state_room(self, n):
        """Room of each state: settleable empty cells along its edge."""
        W, pol = self.W, self.cell_pol
        P, Cc, Lc = [], [], []
        for x, y in ((W.E1, W.E2), (W.E2, W.E1)):
            m = (pol[x] >= 0) & (self.lin[x] >= 0) & (self.lin[y] < 0)
            P.append(pol[x][m])
            Cc.append(y[m])
            Lc.append(self.lin[x][m])
        P, Cc, Lc = np.concatenate(P), np.concatenate(Cc), np.concatenate(Lc)
        empty = np.zeros(n)
        if len(P):
            _, ix = np.unique(P.astype(np.int64) * W.N + Cc, return_index=True)
            P, Cc, Lc = P[ix], Cc[ix], Lc[ix]
            ok = self.Kf(Lc, Cc) * self.peat[self.Lpeople[Lc]] > 200
            empty = np.bincount(P[ok], minlength=n).astype(float)
        cells = np.bincount(pol[pol >= 0], minlength=n)
        room = np.clip(empty / np.maximum(LP_ROOM * cells, 1), 0, 1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                p["room"] = float(room[pid])

    def pressure(self, P):
        """Land pressure of state P (0-1)."""
        d = self.eff(P, "dom")
        th = LP_HI - LP_SPAN * d
        return float(np.clip((P["crowd"] - th) / (1 - th), 0, 1)) * \
            (1 - P.get("room", 0.0))

    def sea_adjacency(self):
        """Polities whose coastal cities lie within a sailor's range."""
        W = self.W
        if self.tick % max(1, round(SEA_ADJ_EVERY / DT)) and \
                hasattr(self, "_sea_adj"):
            return {k for k in self._sea_adj
                    if all(self.polities.get(x, {}).get("ended", 1) is None
                           for x in k)}
        out = set()
        cc = [c for c in self.cities if W.coastal[c] and
              self.cities[c]["polity"] in self.polities]
        if len(cc) > 1:
            cc = np.array(cc)
            tree = cKDTree(W.xyz[cc])
            for c in cc:
                pid = self.cities[c]["polity"]
                rng_km = 2 * self.sail_km(self.polities[pid]["lin"])
                for j in tree.query_ball_point(
                        W.xyz[c], 2 * math.sin(rng_km / R_EARTH / 2)):
                    q = self.cities[cc[j]]["polity"]
                    if q != pid and q in self.polities:
                        out.add((min(pid, q), max(pid, q)))
        self._sea_adj = out
        return out

    def neighbour_record(self, land_adj):
        """Records only (WP5 stage A): each live state's neighbours this
        tick, by land border and by sea only, summed over its life, with
        its most and the years it had none (polities.csv)."""
        nl, ns = {}, {}
        for k in self.adj:
            d = nl if k in land_adj else ns
            for x in k:
                d[x] = d.get(x, 0) + 1
        for pid, p in self.polities.items():
            if p["ended"] is not None:
                continue
            a, b = nl.get(pid, 0), ns.get(pid, 0)
            p["nb_ticks"] = p.get("nb_ticks", 0) + 1
            p["nb_land"] = p.get("nb_land", 0) + a
            p["nb_sea"] = p.get("nb_sea", 0) + b
            p["nb_max"] = max(p.get("nb_max", 0), a + b)
            if a + b == 0:
                p["nb_none_years"] = p.get("nb_none_years", 0) + DT

    def live(self, k):
        a, b = self.polities.get(k[0]), self.polities.get(k[1])
        if not a or not b or a["ended"] is not None or b["ended"] is not None:
            return None
        return a, b

    def diplomacy(self):
        """Alliances form between neighbours who tolerate each other; long
        alliances can fuse into one state. Within a people moderate
        tolerance suffices; across peoples both must be highly tolerant."""
        rng = self.R("diplomacy")
        self.vassal_politics()
        threat = self.threats()
        for k in list(self.allies):
            ab = self.live(k)
            if not ab or k in self.wars:
                self.allies.pop(k, None)
                continue
            if rng.random() < self.dtp * 0.004 * (
                    1 - self.saccept(ab[0], ab[1], TOL_ALLY)) * \
                    (1 - threat.get(k, 0.0)):
                self.allies.pop(k, None)
                self.ally_kind.pop(k, None)
                self.count("ally_break")
                continue
            if rng.random() < self.dtp * ALLY_LAPSE:
                self.allies.pop(k, None)
                self.ally_kind.pop(k, None)
                self.count("ally_lapse")
                continue
            sa, sb = ab[0]["strength"], ab[1]["strength"]
            ratio = max(sa, sb) / max(min(sa, sb), 1e-9)
            pb = ALLY_OUTGROW * min(1.0, max(0.0, (ratio - 3) / 3))
            if self.ally_kind.get(k) == "balance" and \
                    threat.get(k, 0.0) <= 0:
                pb += ALLY_GONE
            if pb > 0 and rng.random() < self.dtp * pb:
                self.allies.pop(k, None)
                self.ally_kind.pop(k, None)
                self.count("ally_outgrown")
        for k in self.adj:
            if k in self.wars or k in self.allies or self.is_vassal_pair(k):
                continue
            ab = self.live(k)
            if not ab:
                continue
            a, b = ab
            p = self.dtp * 0.005 * self.saccept(a, b, TOL_ALLY) * \
                (0.3 + self.ties.get(k, 0.0))
            p_aff = p
            th = threat.get(k, 0.0)
            if th > 0:
                # a common strong neighbour makes allies of the unlike
                p += self.dtp * 0.005 * BALANCE * th * \
                    self.saccept(a, b, TOL_TRADE)
            r = rng.random()
            if r < p:
                self.allies[k] = self.year
                self.ally_kind[k] = "balance" if r >= p_aff else "affinity"
                cross = a["culture"] != b["culture"]
                self.count(f"ally_{'cross' if cross else 'same'}")
                if r >= p_aff:
                    self.count("ally_balance")
                if cross or len(a["cities"]) + len(b["cities"]) >= 8:
                    self.log("alliance", f"{self.pname(k[0])} and "
                             f"{self.pname(k[1])} ally",
                             polities=list(k))
        for k in list(self.allies):
            ab = self.live(k)
            if not ab or self.ties.get(k, 0) < 0.3:
                continue
            a, b = ab
            p = self.dtp * 0.0025 * self.saccept(a, b, TOL_FUSE) * \
                0.5 * (self.eff(a, "state") + self.eff(b, "state"))
            if rng.random() < p:
                self.count("fusion" if a["culture"] != b["culture"]
                           else "union")
                self.fuse(a, b)

    def is_vassal_pair(self, k):
        return self.vassal.get(k[0]) == k[1] or self.vassal.get(k[1]) == k[0]

    def threats(self):
        """For each neighbouring pair: 0-1, how far a neighbour of both
        outweighs the two together (1 at three times their strength)."""
        nbrs = {}
        for x, y in self.adj:
            nbrs.setdefault(x, set()).add(y)
            nbrs.setdefault(y, set()).add(x)
        out = {}
        for k in self.adj:
            ab = self.live(k)
            if not ab:
                continue
            common = (nbrs.get(k[0], set()) & nbrs.get(k[1], set()))
            both = ab[0]["strength"] + ab[1]["strength"] + 1
            worst = 0.0
            for c in common:
                C = self.polities.get(c)
                if C is None or C["ended"] is not None:
                    continue
                worst = max(worst, C["strength"] / both)
            if worst > 1:
                out[k] = min(1.0, (worst - 1) / 2)
        return out

    def annex_w(self, V, O):
        """How readily lord O annexes vassal V, against a kin vassal (1):
        a vassal of another people only under `vassal_annex_cross`, x (1 -
        its tolerance) x O's dominance."""
        if V["culture"] == O["culture"]:
            return 1.0
        if "vassal_annex_cross" not in self.on:
            return 0.0
        return (1 - self.eff(V, "tol")) * self.eff(O, "dom")

    def vassal_politics(self):
        """Vassals throw off weak lords; lords annex small kin vassals."""
        rng = self.R("diplomacy")
        for v, o in list(self.vassal.items()):
            V, O = self.polities.get(v), self.polities.get(o)
            if not V or not O or V["ended"] is not None or \
                    O["ended"] is not None:
                self.vassal.pop(v, None)
                continue
            rel = min(2.0, 2 * V["strength"] / max(O["strength"], 1))
            alien = 1.5 if V["culture"] != O["culture"] else 1.0
            if rng.random() < self.dtp * VASSAL_DEFECT * rel * \
                    (1.5 - O["cohesion"]) * alien:
                del self.vassal[v]
                self.count("vassal_defect")
                k = (min(v, o), max(v, o))
                self.truce[k] = self.year + TRUCE_VASSAL
                if len(V["cities"]) + len(O["cities"]) >= 6:
                    self.log("vassal", f"{self.pname(v)} throws off "
                             f"{self.pname(o)}",
                             polities=[v, o])
            elif len(V["cities"]) <= 3 and V["vassal_years"] >= 50 and \
                    not self.camp_trib(O) and rng.random() < \
                    self.dtp * VASSAL_ANNEX * (0.5 + self.eff(O, "state")) * \
                    self.annex_w(V, O):
                for c in list(V["cities"]):
                    self.cities[c]["polity"] = o
                    self.cities[c]["owners"].append(o)
                    O["cities"].add(c)
                V["cities"] = set()
                self.count("vassal_annex")
                if V["culture"] != O["culture"]:
                    self.count("vassal_annex_cross")
                self.kill_polity(v, f"annexed by its lord {self.pname(o)}",
                                 by=o, code="annexed")

    def submit(self, v, o):
        """State v becomes the tributary vassal of state o."""
        for key in [k for k in self.allies if v in k]:
            del self.allies[key]
        self.vassal[v] = o
        if self.polities[v]["culture"] != self.polities[o]["culture"]:
            self.sup_win[o] = min(1.0, self.sup_win.get(o, 0.0) + len(
                self.polities[v]["cities"]) / max(len(
                    self.polities[o]["cities"]), 1))
            self.sup_loss[v] = 1.0
        self.count("vassal_submit_" + ("same" if self.polities[v]["culture"]
                                       == self.polities[o]["culture"]
                                       else "cross"))
        self.polities[v]["vassal_years"] = 0
        V, O = self.polities[v], self.polities[o]
        if len(V["cities"]) + len(O["cities"]) >= 6:
            self.log("vassal", f"{self.pname(v)} submits to "
                     f"{self.pname(o)} and pays tribute",
                     polities=[v, o])

    def fuse(self, a, b):
        big, small = (a, b) if a["pop"] >= b["pop"] else (b, a)
        for x in small["cities"]:
            self.cities[x]["polity"] = big["id"]
            self.cities[x]["owners"].append(big["id"])
        big["cities"] |= small["cities"]
        big["peoples"] |= small["peoples"]
        small["cities"] = set()
        big["cohesion"] = max(big["cohesion"], small["cohesion"])
        cross = a["culture"] != b["culture"]
        self.blend(big, small)
        if cross:
            self.log("fusion", f"{self.pname(small['id'])} and "
                     f"{self.pname(big['id'])} fuse into one state "
                     f"({self.keys[small['culture']]} + "
                     f"{self.keys[big['culture']]}) under "
                     f"{self.lname(big['lin'])}",
                     polities=[small['id'], big['id']],
                     peoples=[self.keys[small['culture']],
                              self.keys[big['culture']]],
                     lineages=[big['lin']])
        elif len(big["cities"]) >= 5:
            self.log("union", f"{self.pname(small['id'])} joins "
                     f"{self.pname(big['id'])} by treaty",
                     polities=[small['id'], big['id']])
        self.kill_polity(small["id"], f"{'fusion' if cross else 'union'} "
                         f"with {self.pname(big['id'])}", by=big["id"],
                         code="fusion" if cross else "union")

    def blend(self, big, small):
        """A merged state takes one culture: its ruling lineages are
        replaced, inside its territory, by new lineages whose cultural
        traits are the population-weighted average of the two (technology:
        the better of the two). Growth rate, biome fit and body size stay
        with each people."""
        La, Lb = big["lin"], small["lin"]
        if La == Lb:
            return
        ids = (big["id"], small["id"])
        cells = np.nonzero(np.isin(self.cell_pol, ids) &
                           np.isin(self.lin, (La, Lb)))[0]
        wa = self.pop[cells][self.lin[cells] == La].sum() + 1
        wb = self.pop[cells][self.lin[cells] == Lb].sum() + 1
        T = (wa * self.LT[La] + wb * self.LT[Lb]) / (wa + wb)
        X = (wa * self.LX[La] + wb * self.LX[Lb]) / (wa + wb)
        how = "fusion" if big["culture"] != small["culture"] else "union"
        new = {}
        for Lo in (La, Lb):
            c = int(self.Lpeople[Lo])
            if c in new:
                continue
            D = self.new_lineage(c, Lo, how)
            if D == Lo:
                return
            self.LT[D] = T
            self.LX[D] = X
            for t in ("agri", "metal", "sail", "fishing", "admin", "craft",
                      "roadt"):
                v = getattr(self, t)
                v[D] = max(v[La], v[Lb])
            self.domlv[D] = np.maximum(self.domlv[La], self.domlv[Lb])
            self.lver += 1                  # agri, metal, domlv: ltab()
            self.guard[D] = self.guard[La] | self.guard[Lb]
            for t in ("bronze", "iron", "steel"):
                v = getattr(self, t)
                v[D] = v[La] or v[Lb]
            self.known[D] = self.known[La] | self.known[Lb]
            self.lack[D] = np.minimum(self.lack[La], self.lack[Lb])
            self.Lseen[D] = self.Lseen[La] | self.Lseen[Lb]
            new[c] = D
        for Lo in (La, Lb):
            self.lin[cells[self.lin[cells] == Lo]] = new[int(self.Lpeople[Lo])]
        big["lin"] = new[int(big["culture"])]
        self.pver += 1
        big["dyn"] = self.year

    def city_dist(self, a, b):
        return float(gc_km(self.W.xyz, a, np.array([b]))[0])

    def roads(self):
        """States build roads along the cheapest routes from capital to
        each of their cities; roads decay, slowly where a state keeps them
        up. Travel costs and the travel graph are then rebuilt."""
        W = self.W
        kept = self.cell_pol >= 0
        life = np.where(kept, ROAD_LIFE, ROAD_LIFE_WILD)
        self.road *= np.exp(-ROAD_EVERY / life)
        for pid, p in self.polities.items():
            if p["ended"] is not None or len(p["cities"]) < 2:
                continue
            add = ROAD_BUILD * self.admin[p["lin"]]
            add *= 0.5 + self.eff(p, "pati")
            if add <= 0:
                continue
            q = (ROAD_Q0 + (1 - ROAD_Q0) * self.roadt[p["lin"]] * (
                0.8 + 0.2 * self.admin[p["lin"]]))
            src = self.sources(p)
            others = [c for c in p["cities"] if c not in src]
            if len(src) > 1 and others:
                # each city is reached from its nearest seat
                near = np.argmin([gc_km(W.xyz, s, np.array(others))
                                  for s in src], 0)
            else:
                near = np.zeros(len(others), int)
            for i, cap in enumerate(src):
                mine = [c for c, j in zip(others, near) if j == i]
                if not mine:
                    continue
                dist, pred = dijkstra(W.G, indices=cap,
                                      return_predecessors=True,
                                      limit=1.5 * self.reach(p))
                path = set()
                for c in mine:
                    x = c
                    if pred[x] < 0:
                        continue
                    while x >= 0 and x != cap and x not in path:
                        path.add(x)
                        x = pred[x]
                if path:
                    idx = np.fromiter(path, int)
                    if q is not None:
                        # quality blends by stock
                        for ix in (idx, cap):
                            r0 = self.road[ix]
                            r1 = r0 + add * (1 - r0)
                            self.roadq[ix] = (r0 * self.roadq[ix] +
                                              (r1 - r0) * q) / \
                                np.maximum(r1, 1e-12)
                    self.road[idx] += add * (1 - self.road[idx])
                    self.road[cap] += add * (1 - self.road[cap])
        W.road = 1 - ROAD_EFFECT * self.road * (
            self.roadq)
        W.travel()

    def reach(self, P):
        """Administrative reach (cost-km) of a state: its lineage's
        administration, cut when the state is underfed (fiscal) and
        lengthened by a mounted herding population (pastoral)."""
        if P.get("camp") is not None:
            # `camps`: a camp's reach is its people's cohesion, carried
            # far by horses, not administration
            return CAMP_REACH * P["cohesion"] * (1 + CAMP_HERD * P["herd"])
        r = REACH0 + REACH1 * self.admin[P["lin"]]
        r *= 0.6 + 0.4 * P["fed"]
        r *= 1 + 0.5 * P["herd"]
        nd = self.d_by_pid.get(P["id"], 0)
        if nd:
            # allied dragons carry word and enforce it
            r *= 1 + DRAGON_ADMIN * math.sqrt(nd)
        return r

    def projected(self, P, t):
        reach = self.reach(P)
        reach *= 1 + LOG_REACH * self.logi(P)
        d = self.power_dist(P)[t]
        return P["strength"] * math.exp(-d / (1.5 * reach))

    def sources(self, P):
        """The capital and the provincial seats still held."""
        return [P["capital"]] + [c for c in self.seats.get(P["id"], ())
                                 if c in P["cities"] and c != P["capital"]]

    def power_dist(self, P):
        """travel_reach: km-equivalent distance from the state's seats of
        power to every cell (see PROV_CR, SEA_F0). A function of the seats,
        the travel graph and, for coastal seats, the ruler's sailing only:
        cached on those, so it never depends on when it was last asked.
        A graph change touching no cell the search reached leaves every
        distance as it was (a path through a changed edge would already
        be past the limit at its first end), so the arrays are kept."""
        W = self.W
        src = self.sources(P)
        c = self.pdist.get(P["id"])
        ci = W.coast_idx
        if c is not None and c[0] == src and c[1] != W.gver and len(c) > 7:
            ch = W.changed_since(c[1])
            if ch is not None and not c[7][ch].any():
                c[1] = W.gver
        if c is None or c[0] != src or c[1] != W.gver:
            # land distances, and great-circle km to the coast from each
            # coastal seat
            D = dijkstra(W.G, indices=src, limit=PROV_CR * 5000) / PROV_CR
            reached = np.isfinite(D).any(0)
            gco = []
            for i, s in enumerate(src):
                g = gc_km(W.xyz, s)
                D[i] = np.where(np.isinf(D[i]), 1.5 * g, D[i])
                gco.append(g[ci] if W.coastal[s] else None)
            sea = any(g is not None for g in gco)
            c = [src, W.gver, D, gco, sea, None, None, reached]
            self.pdist[P["id"]] = c
        _, _, D, gco, sea, f0, d = c[:7]
        f = SEA_F0 - SEA_F1 * self.sail[P["lin"]] if sea else None
        if d is not None and f == f0:
            return d
        if len(src) == 1:
            d = D[0].astype(np.float32)
            if sea:
                d[ci] = np.minimum(D[0, ci], f * gco[0])
        else:
            if sea:
                D = D.copy()
                for i, g in enumerate(gco):
                    if g is not None:
                        D[i, ci] = np.minimum(D[i, ci], f * g)
            link = PROV_LINK * D[0, src]
            link[0] = 0.0
            d = (D + link[:, None]).min(0).astype(np.float32)
        c[5], c[6] = f, d
        return d

    def name_seats(self):
        """provinces: every ROAD_EVERY years each state of 4+ cities names
        its provincial seats."""
        xyz = self.W.xyz
        for c, rec in self.cities.items():
            h = self.held.get(c)
            if h is None or h[0] != rec["polity"]:
                self.held[c] = (rec["polity"], self.year)
        for pid in [q for q in self.seats if q not in self.polities or
                    self.polities[q]["ended"] is not None]:
            del self.seats[pid]
        for pid in [q for q in self.pdist if q not in self.polities or
                    self.polities[q]["ended"] is not None]:
            del self.pdist[pid]
        for pid, p in self.polities.items():
            if p["ended"] is not None or len(p["cities"]) < 4:
                self.seats.pop(pid, None)
                continue
            n = int(PROV_N * self.admin[p["lin"]] *
                    math.sqrt(len(p["cities"])))
            seats = [x for x in self.seats.get(pid, ())
                     if x in p["cities"] and x != p["capital"]][:n]
            cand = [x for x in p["cities"] if x != p["capital"] and
                    x not in seats and
                    self.year - self.held.get(x, (pid, self.year))[1] >=
                    PROV_HOLD]
            while len(seats) < n and cand:
                src = [p["capital"]] + seats
                d = np.min([gc_km(xyz, s, np.array(cand)) for s in src], 0)
                k = int(np.argmax(d * np.sqrt(np.maximum(self.pop[cand], 1))))
                seats.append(cand.pop(k))
                self.count("prov_seat")
            if seats:
                self.seats[pid] = seats
            else:
                self.seats.pop(pid, None)

    def logi(self, P):
        """Logistics of a state: administration x (0.5 + statecraft)."""
        L = P["lin"]
        return self.admin[L] * (0.5 + self.eff(P, "state"))

    def spike(self, pid):
        """A major event touches state pid (spiky cultural change); at
        most one spike per state per tick."""
        self.pevent[pid] = SPIKE_EVENT

    def rebellions(self):
        rng = self.R("revolt")
        for pid in list(self.polities):
            p = self.polities[pid]
            if p["ended"] is not None or len(p["cities"]) < 2:
                continue
            L = p["lin"]
            reach = self.reach(p)
            cities = [x for x in p["cities"] if x != p["capital"]]
            d = self.power_dist(p)[cities]
            nc = len(p["cities"])
            for x, dx in zip(cities, d):
                if x not in p["cities"] or self.lin[x] < 0:
                    continue
                Lx = int(self.lin[x])
                alien = 1 + 3 * (1 - self.similarity(L, Lx)) * \
                    (1 - 0.6 * self.tol[L])
                pr = self.dtp * REVOLT_BASE * (dx / reach) ** 2 * \
                    (1.5 - p["cohesion"]) * alien * (1 + 0.2 * math.log(nc))
                pr *= 1 + UNREST * p["stress"]
                if p.get("acc_until", -1) > self.year:
                    pr *= 1 + ACC_K
                ci = self.cities[x]["id"] if self.cc_on else None
                if "revolt_viol" in self.on:
                    pr *= 0.5 + (self.CM[ci, self.city_cols()["viol"]]
                                 if self.cc_on else self.viol[Lx])
                if self.rt and self.Lpeople[Lx] == p["culture"]:
                    # his own people chafe at a ruler unlike them
                    cf = self.CM[ci, self.city_cols()["conf"]] \
                        if self.cc_on else self.conf[Lx]
                    pr *= 1 + RT_REVOLT * cf * self.rt_gap(p, Lx, ci)
                if self.dom_on and self.Lpeople[Lx] != p["culture"]:
                    # subjects stripped of their harvest rise sooner
                    pr *= 1 + EXT_REVOLT * self.ext_x[x]
                if rng.random() < pr:
                    self.revolt(pid, x)
                    # a revolt thins the elite
                    p["elite"] = max(0.3, 0.8 * p["elite"])
        # reigns end in states of SUCC_MIN_CITIES or more cities (U
        # 2026-11-18: small states too, so a talented ruler can arise in
        # one)
        for pid in list(self.polities):
            p = self.polities[pid]
            if p["ended"] is None and (
                    len(p["cities"]) >= SUCC_MIN_CITIES or
                    p.get("camp") is not None) and \
                    self.year >= p["next_succ"]:
                self.succession(pid, p)

    def rt_vals(self, L):
        """The ruler traits (RT_TRAITS) of lineage(s) L, 0-1."""
        return np.stack([getattr(self, a)[L] for a in RT_TRAITS], -1)

    def eff(self, P, a):
        """Trait `a` (attribute name) of state P as its decisions read it:
        the ruling lineage's, or under `ruler_traits` moved toward the
        ruler's by w = min(1, hierarchy x (1.5 - conformity)) (the elite
        pull the other way)."""
        L = P["lin"]
        if self.cc_on:
            v = self.state_vec(P)
            x = v[CITY_COLS[a]]
            h, cf = v[CITY_COLS["hier"]], v[CITY_COLS["conf"]]
        else:
            x = getattr(self, a)[L]
            h, cf = self.hier[L], self.conf[L]
        r = P.get("ruler")
        k = RT_IDX.get(a)
        if not self.rt or not r or "x" not in r or k is None:
            return x
        w = min(1.0, h * (1.5 - cf))
        return float(x + w * (r["x"][k] - x))

    def rt_gap(self, P, L, ci=None):
        """RMS distance between state P's ruler and lineage L (or, with
        `city_culture`, the commons of city ci)."""
        r = P.get("ruler")
        if not r or "x" not in r:
            return 0.0
        if ci is not None:
            cols = self.city_cols()
            v = self.CM[ci, [cols[a] for a in RT_TRAITS]]
        else:
            v = self.rt_vals(L)
        return float(np.sqrt(np.mean((r["x"] - v) ** 2)))

    def draw_ruler(self, pid, P, prev=None):
        """A ruler's traits and dynasty: around his predecessor's within a
        dynasty, else around the culture's mean (a new dynasty, starting
        now); Student-t, scale RT_SD x (1.5 - conformity), in trait units
        reflected into [0.01, 0.99] as drift is."""
        L = P["lin"]
        if prev is not None and "x" in prev:
            c, dyn = prev["x"], prev["dyn"]
        elif self.cc_on and P["capital"] in self.cities:
            cols = self.city_cols()
            c = self.CE[self.cities[P["capital"]]["id"],
                        [cols[a] for a in RT_TRAITS]]
            self.n_dyn += 1
            dyn = self.n_dyn
            P["dyn"] = self.year
        else:
            c = None
            m = (self.cell_pol == pid) & (self.cul == P["culture"]) & \
                (self.lin >= 0)
            if m.any():
                w = self.pop[m]
                if w.sum() > 0:
                    c = (w[:, None] * self.rt_vals(self.lin[m])).sum(0) / \
                        w.sum()
            if c is None:
                c = self.rt_vals(L)
            self.n_dyn += 1
            dyn = self.n_dyn
            P["dyn"] = self.year
        s = RT_SD * (1.5 - self.conf[L])
        y = c + s * self.R("rulers").standard_t(RT_DF, len(RT_TRAITS))
        for _ in range(3):
            y = np.where(y < 0.01, 0.02 - y, np.where(y > 0.99, 1.98 - y, y))
        return np.clip(y, 0.01, 0.99), dyn

    def ruler_pull(self):
        """`ruler_traits`: the state's lineages of the ruler's people move
        toward him (RT_PULL x hierarchy x administration per year),
        and a ruler less able than his culture lets administration slide."""
        nL = self.nL
        occ = self.lin >= 0
        P = [p for p in self.polities.values() if p["ended"] is None and
             "x" in p.get("ruler", {})]
        if not P:
            return
        if self.cc_on:
            # the ruler pulls the elites of his cities; incompetence
            # lets administration slide
            cols = self.city_cols()
            rc = [cols[a] for a in RT_TRAITS]
            for p in P:
                L = p["lin"]
                x = p["ruler"]["x"]
                v = self.state_vec(p)
                rate = min(1.0, DT * RT_PULL * v[cols["hier"]] *
                           self.admin[L])
                # under `city_influence` he holds court in the capital
                # only, and his ways spread from there
                for c in ([p["capital"]] if "city_influence" in self.on
                          else p["cities"]):
                    if c in self.cities:
                        i = self.cities[c]["id"]
                        self.CE[i, rc] += rate * (x - self.CE[i, rc])
                short = v[cols["state"]] - x[3]
                if short > 0:
                    if self.ca_on:
                        for c in p["cities"]:
                            if c in self.cities:
                                i = self.cities[c]["id"]
                                self.Cadm[i] = max(0.0, self.Cadm[i] -
                                                   DT * RT_ADMIN * short)
                    else:
                        self.admin[L] = max(0.0, self.admin[L] -
                                            DT * RT_ADMIN * short)
            self._pt = {}
            return
        k = -np.ones(self.next_pid, int)
        Z = np.zeros((len(P), len(RT_TRAITS)))
        rate = np.zeros(len(P))
        peo = np.zeros(len(P), int)
        for i, p in enumerate(P):
            L = p["lin"]
            k[p["id"]] = i
            Z[i] = p["ruler"]["x"]
            rate[i] = min(1.0, DT * RT_PULL * self.hier[L] * self.admin[L])
            peo[i] = p["culture"]
            short = self.state[L] - Z[i, 3]
            if short > 0:
                self.admin[L] = max(0.0, self.admin[L] - DT * RT_ADMIN * short)
        c = np.nonzero(occ & (self.cell_pol >= 0))[0]
        i = k[self.cell_pol[c]]
        ok = i >= 0
        c, i = c[ok], i[ok]
        ok = self.Lpeople[self.lin[c]] == peo[i]
        c, i = c[ok], i[ok]
        if not len(c):
            return
        Lc = self.lin[c]
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        acc = np.zeros((nL, len(RT_TRAITS)))
        np.add.at(acc, Lc, (self.pop[c] * rate[i])[:, None] *
                  (Z[i] - self.rt_vals(Lc)))
        Ls = np.unique(Lc)
        x = self.rt_vals(Ls) + acc[Ls] / np.maximum(Lpop[Ls], 1e-9)[:, None]
        nT = len(TRAITS)
        cols = {a: TI[t] for t, a in TRAIT_ATTR.items()}
        cols["dom"] = nT + XTRAITS.index("dominance")
        for j, a in enumerate(RT_TRAITS):
            arr = getattr(self, a)
            self.Lrul[Ls, cols[a]] += x[:, j] - arr[Ls]
            arr[Ls] = x[:, j]

    def turmoil(self, P, loss):
        """`turmoil`: losses wear down the ruling lineage's
        administration, by the fraction `loss`."""
        if "turmoil" in self.on and loss > 0 and not self.ca_on:
            L = P["lin"]
            self.admin[L] *= 1 - min(1.0, loss)

    def succession(self, pid, p):
        """A reign ends. Violent peoples and weak administrations risk a
        disputed succession: cohesion falls, and a pretender may take the
        largest provincial city out of the state."""
        if "rulers" in self.on:
            return self.reign_end(pid, p)
        rng = self.R("succession")
        p["next_succ"] = self.year + max(
            self.dtp, rng.exponential(SUCC_GEN))
        L = p["lin"]
        q = SUCC_P * (1.3 - 0.6 * self.eff(p, "state"))
        q *= 0.5 + self.eff(p, "viol")
        if rng.random() >= q:
            return
        self.disputed(pid, p)

    def reign_end(self, pid, p):
        """A ruler dies (`rulers`): inheritance, the new ruler's testing
        time, alliances and vassals up for renewal, union of crowns."""
        rng = self.R("succession")
        L = p["lin"]
        exp_reign = SUCC_GEN * self.plife[self.Lpeople[L]]
        r = p.get("ruler") or dict(id=-1, start=p["founded"])
        reign = self.year - r["start"]
        p["next_succ"] = self.year + max(
            self.dtp, rng.exponential(exp_reign))
        nc = len(p["cities"])
        outcome = "peaceful"
        if nc >= 4 and rng.random() < self.Lpart[L] * min(1.0, nc / PART_N):
            outcome = f"partition {self.partition(pid, p)}"
        else:
            q = SUCC_P * (1.3 - 0.6 * self.eff(p, "state"))
            q *= 0.5 + self.eff(p, "viol")
            q *= 1 + LONG_K * max(0.0, reign / exp_reign - 1)
            if rng.random() < q:
                n0 = len(p["cities"])
                self.disputed(pid, p)
                outcome = "disputed" if len(p["cities"]) == n0 \
                    else "pretender"
        p["acc_until"] = self.year + ACC_YEARS
        for kk in [kk for kk in self.allies if pid in kk]:
            if rng.random() < ALLY_RENEW * (1 - self.ties.get(kk, 0.0)):
                self.allies.pop(kk, None)
                self.ally_kind.pop(kk, None)
                self.count("ally_lapse_death")
        for v in [v for v, o in self.vassal.items() if o == pid]:
            V = self.polities.get(v)
            alien = 1.5 if V and V["culture"] != p["culture"] else 1.0
            if rng.random() < VASSAL_ACC * alien:
                del self.vassal[v]
                self.count("vassal_defect")
                self.truce[(min(v, pid), max(v, pid))] = \
                    self.year + TRUCE_VASSAL
        if p["ended"] is None and p["cities"]:
            for kk in [kk for kk in self.allies if pid in kk]:
                ab = self.live(kk)
                if not ab:
                    continue
                if rng.random() < UNION_CROWN * self.saccept(
                        ab[0], ab[1], TOL_FUSE):
                    self.count("union_crowns")
                    other = ab[1] if ab[0]["id"] == pid else ab[0]
                    if nc + len(other["cities"]) >= 6:
                        self.log("succession", f"union of crowns: "
                                 f"{self.pname(pid)} and "
                                 f"{self.pname(other['id'])} pass to one "
                                 "ruler",
                                 polities=[pid, other['id']])
                    outcome += " union"
                    self.fuse(ab[0], ab[1])
                    break
        rec = (r["id"], pid, self.keys[p["culture"]], r["start"], self.year,
               reign, nc, outcome)
        if self.rt and "x" in r:
            x = r["x"]
            L = p["lin"]
            rec += (r["dyn"],) + tuple(round(float(v), 3) for v in x) + (
                round(min(1.0, self.hier[L] * (1.5 - self.conf[L])), 3),
                round(self.rt_gap(p, L), 3))
        self.ruler_log.append(rec + (round(p.get("gen", 0.0), 3),))
        # the new ruler's own talent; the old one's lives on, fading
        p["gen_legacy"] = RULER_MIL_DECAY * (p.get("gen_legacy", 0.0) +
                                             p.get("gen", 0.0))
        p["gen"] = self.draw_general()
        self.n_ruler += 1
        p["ruler"] = dict(id=self.n_ruler, start=self.year)
        if self.rt:
            # a disputed succession ends the dynasty
            heir = not outcome.startswith(("disputed", "pretender"))
            p["ruler"]["x"], p["ruler"]["dyn"] = self.draw_ruler(
                pid, p, r if heir else None)

    def partition(self, pid, p):
        """The realm is divided among heirs: 2-4 seats (the capital and the
        largest cities far from the others); every city goes to the
        nearest seat; each seat but the capital becomes a state of the
        same lineage. Returns the number of heirs."""
        rng = self.R("revolt")
        cc = list(p["cities"])
        nh = int(min(2 + rng.integers(0, 3), max(2, len(cc) // 2)))
        seats = [p["capital"]]
        xyz = self.W.xyz
        while len(seats) < nh:
            rest = [c for c in cc if c not in seats]
            if not rest:
                break
            d = np.min([gc_km(xyz, s, np.array(rest)) for s in seats], 0)
            score = d * np.sqrt(np.maximum(self.pop[rest], 1))
            seats.append(rest[int(np.argmax(score))])
        D = np.array([gc_km(xyz, s, np.array(cc)) for s in seats])
        near = D.argmin(0)
        heirs = [pid]
        for i, s in enumerate(seats[1:], 1):
            group = [c for c, j in zip(cc, near) if j == i]
            new = self.new_polity(p["lin"], s, p["cohesion"], parent=pid,
                                  origin="partition")
            if self.rt:
                q = self.polities[new]
                q["ruler"]["x"], q["ruler"]["dyn"] = self.draw_ruler(
                    new, q, p.get("ruler"))
            for c in group:
                p["cities"].discard(c)
                self.cities[c]["polity"] = new
                self.cities[c]["owners"].append(new)
                self.cities[c].setdefault("lost", {})[pid] = self.year
                self.polities[new]["cities"].add(c)
            heirs.append(new)
        for a in heirs:
            self.spike(a)
            for b in heirs:
                if a < b:
                    self.truce[(a, b)] = self.year + TRUCE_HEIRS
        self.count("partition")
        if len(cc) >= 6:
            self.log("succession", f"partition: {self.pname(pid)} is "
                     f"divided among {len(heirs)} heirs (" + ", ".join(
                         f"{self.pname(h)} {len(self.polities[h]['cities'])}"
                         for h in heirs) + " cities)",
                     polities=[pid] + list(heirs), n=len(heirs))
        return len(heirs)

    def disputed(self, pid, p):
        """A disputed succession."""
        rng = self.R("diplomacy")
        p["cohesion"] *= 0.8
        p["elite"] = max(0.3, 0.85 * p["elite"])
        p["dyn"] = self.year
        self.spike(pid)
        civil = rng.random() < min(0.9, 0.3 + 0.3 * p["stress"])
        rest = [x for x in p["cities"] if x != p["capital"] and
                self.lin[x] >= 0]
        if civil and rest:
            x = max(rest, key=self.city_weight)
            if len(p["cities"]) >= 5:
                self.log("succession", f"disputed succession in "
                         f"{self.pname(pid)}: a pretender holds "
                         f"{self.place(x)}",
                         cell=x, polities=[pid])
            self._pretender = True
            self.revolt(pid, x)
            self._pretender = False
        elif len(p["cities"]) >= 8:
            self.log("succession", f"disputed succession weakens "
                     f"{self.pname(pid)}",
                     polities=[pid])

    def revolt(self, pid, x):
        """A province breaks away. Rebels of the ruling lineage found a
        daughter lineage (they drift apart from here); rebels of another
        lineage or people restore their own."""
        p = self.polities[pid]
        self.n_revolts += 1
        cx, Lx = self.cities[x]["culture"], int(self.lin[x])
        same = Lx == p["lin"]
        Lnew = self.new_lineage(cx, Lx, "secession", sd=self.drift) \
            if same else Lx
        kind = ("ethnic revolt" if cx != p["culture"] else
                "secession" if same else "kin revolt")
        key = "pretender" if self._pretender else kind.split()[0]
        new = self.new_polity(Lnew, x, 0.75, parent=pid,
                              origin="revolt_" + key)
        self.cities[x].setdefault("lost", {})[pid] = self.year
        p["cities"].discard(x)
        self.cities[x]["polity"] = new
        self.cities[x]["owners"].append(new)
        group = [x]
        others = [y for y in p["cities"] if y != p["capital"] and
                  self.cities[y]["culture"] == cx]
        seat = x in self.seats.get(pid, ())
        if seat:
            self.seats[pid].remove(x)
            self.count("prov_seat_revolt")
        if others:
            dn = gc_km(self.W.xyz, x, np.array(others))
            dc = gc_km(self.W.xyz, p["capital"], np.array(others))
            if seat:
                # the province follows its governor
                for s in self.seats.get(pid, ()):
                    dc = np.minimum(dc, gc_km(self.W.xyz, s,
                                              np.array(others)))
            for y, a, b in zip(others, dn, dc):
                if (a < 400 or seat) and a < b and \
                        self.R("revolt").random() < 0.6:
                    self.cities[y].setdefault("lost", {})[pid] = self.year
                    p["cities"].discard(y)
                    self.cities[y]["polity"] = new
                    self.cities[y]["owners"].append(new)
                    self.polities[new]["cities"].add(y)
                    group.append(y)
        if same:
            hint = np.isin(self.cell_city, group) & (self.lin == Lx)
            self.lin[hint] = Lnew
        taken = len(group)
        share = taken / max(taken + len(p["cities"]), 1)
        self.turmoil(p, ADM_LOSS * share)
        if share >= SPIKE_REVOLT:
            self.spike(pid)
            self.spike(new)
        if "revolt_exp" in self.on:
            # weighted by the share of the state's cities lost this tick
            m = self.cell_pol == pid
            self.revolted[m] = np.minimum(1.0, self.revolted[m] + share)
            for c in group:
                hc = self.cell_city == c
                self.revolted[hc] = np.minimum(1.0, self.revolted[hc] + share)
        self.revolt_log.append((
            self.year, pid, new, self.keys[p["culture"]], self.keys[cx], key,
            taken, len(p["cities"]), int(self.W.landmass[x]),
            round(float(self.W.lon[x]), 2), round(float(self.W.lat[x]), 2)))
        self.count(f"revolt_{key}")
        self.count(f"revolt_{key}_cities", taken)
        if taken >= 3 or (taken >= 2 and len(p["cities"]) >= 6):
            extra = f", new lineage {self.lname(Lnew)}" if same else ""
            self.log("revolt", f"{kind}: {self.pname(new)} breaks from "
                     f"{self.pname(pid)} at {self.place(x)} "
                     f"with {taken} cities{extra}",
                     cell=x, polities=[new, pid],
                     lineages=[Lnew] if same else [], n=taken)
        p["cohesion"] *= 0.9
