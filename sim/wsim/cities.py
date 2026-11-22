"""Cities as a nested unit of culture (`city_culture`, 2026-11-02).

Each city carries two value sets over every cultural trait (TRAITS +
XTRAITS, trait units): an elite and a commons. The commons are pulled
toward the lineages living around the city (rural inflow, x conformity),
toward nearby similar cities, and toward their trade partners; the
elite toward the capital's elite under rule and toward the ruler.
Hierarchy weights elite against commons; a conformist commons reins in
a divergent elite by revolt. A state reads its capital's culture.
Cities feed back into their lineages; a city that strays far founds a
new lineage; close lineages of a people in contact merge.
See docs/open-questions.md, "Cities as a nested unit of culture".
"""
import math

import numpy as np
from scipy.spatial import cKDTree

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


def city_km(xyz):
    """Great-circle km between all pairs of unit vectors xyz."""
    c = np.clip(2 - 2 * (xyz @ xyz.T), 0, 4)
    return 2 * R_EARTH * np.arcsin(np.clip(np.sqrt(c) / 2, 0, 1))


def city_sim(M, same):
    """Similarity of all pairs of cities' commons (TRAITS), as
    similarity(): same people exp(-d / SIM_SAME_SCALE), else SIM_OTHER."""
    X = M[:, :len(TRAITS)]
    q = (X * X).sum(1)
    dv = np.sqrt(np.maximum(q[:, None] + q[None, :] - 2 * (X @ X.T), 0))
    return np.where(same, np.exp(-dv / SIM_SAME_SCALE),
                    SIM_OTHER[0] + SIM_OTHER[1] * np.exp(-dv / 0.8))


CITY_COLS = {TRAIT_ATTR[t]: TI[t] for t in TRAITS}
CITY_COLS.update({a: len(TRAITS) + i for i, a in enumerate(XATTR)})


class CitiesMixin:
    # ---- the city table
    def city_sizes(self, cells):
        """Sizes of city cells as city culture reads them: the cell's
        people, or under `urban_city` the urban population."""
        if self.uc_on:
            return np.array([self.city_size.get(int(c), 0.0)
                             for c in cells])
        return self.pop[cells]

    def city_cols(self):
        """Column of each trait attribute in a city's value vector (one
        shared dict: read it, do not change it)."""
        return CITY_COLS

    def lin_vals(self, L):
        """Cultural values (TRAITS + XTRAITS) of lineage(s) L."""
        return np.concatenate([self.LT[L], self.LX[L]], -1)

    def city_xrows(self, pos):
        """Live extra rows in city hinterlands, and their city's position
        (pos: position by city cell, -1 for others)."""
        x = self.xrows()
        x = x[(self.rl[x] >= 0) & (self.cell_city[self.rc[x]] >= 0)]
        kx = pos[self.cell_city[self.rc[x]]]
        return x[kx >= 0], kx[kx >= 0]

    def city_found(self, rec, op):
        """A new city's culture: its mother city's (the capital of the
        state it joins, or the nearest live city of its lineage), else its
        lineage's."""
        i, cell = rec["id"], rec["cell"]
        L = int(self.lin[cell])
        mother = None
        if op is not None and op.get("capital") in self.cities and \
                op["culture"] == rec["culture"]:
            mother = self.cities[op["capital"]]
        else:
            kin = [c for c, r in self.cities.items()
                   if c != cell and self.lin[c] == L]
            if kin:
                d = gc_km(self.W.xyz, cell, np.array(kin))
                j = int(np.argmin(d))
                if d[j] < CITY_MOTHER_KM:
                    mother = self.cities[kin[j]]
        if mother is not None:
            m = mother["id"]
            self.CM[i] = self.CM[m]
            self.CE[i] = self.CE[m]
            self.CH[i] = self.CH[m]
            if op is not None and mother["polity"] == op["id"]:
                self.Cadm[i] = self.Cadm[m]
        else:
            self.CM[i] = self.CE[i] = self.lin_vals(L)
            self.CH[i] = 0.0
        self.Chome[i] = L
        rec["mother"] = mother["id"] if mother is not None else None

    def city_vec(self, i):
        """A city's effective culture: elite and commons weighted by
        hierarchy (the mean of the two's hierarchy)."""
        hc = self.city_cols()["hier"]
        h = 0.5 * (self.CE[i, hc] + self.CM[i, hc])
        return h * self.CE[i] + (1 - h) * self.CM[i]

    def state_vec(self, P):
        """State P's culture: its capital's effective culture (cached per
        tick), or its ruling lineage's when the capital has no record."""
        pid = P["id"]
        v = self._pt.get(pid)
        if v is None:
            rec = self.cities.get(P["capital"])
            v = self.city_vec(rec["id"]) if rec is not None else \
                self.lin_vals(P["lin"])
            self._pt[pid] = v
        return v

    def ssim(self, A, B):
        """Similarity of two states, as similarity() of their cultures
        (of their ruling lineages without `city_culture`)."""
        if not self.cc_on:
            return self.similarity(A["lin"], B["lin"])
        return self.vsim(self.state_vec(A), self.state_vec(B), A["lin"],
                         B["lin"], A["culture"] == B["culture"])

    def vsim(self, va, vb, La, Lb, same):
        """similarity() of two value vectors, with the affinities of
        lineages La and Lb; `same`: of one people."""
        nT = len(TRAITS)
        d = float(np.linalg.norm(va[:nT] - vb[:nT]) + 0.3 * np.linalg.norm(
            np.log(self.Laff[La]) - np.log(self.Laff[Lb])))
        if same:
            return math.exp(-d / SIM_SAME_SCALE)
        return SIM_OTHER[0] + SIM_OTHER[1] * math.exp(-d / 0.8)

    def sview(self, P):
        """State P's view (`state_view`): its ruling lineage's values moved
        toward the state's culture by the lineage's tolerance; the
        lineage's alone without the switch."""
        L = P["lin"]
        r = self.lin_vals(L)
        if not self.sv_on:
            return r
        return r + self.tol[L] * (self.state_vec(P) - r)

    def stol(self):
        """Tolerance of each live state's view by id (0 for ended ids)."""
        pl = self.ptab()[0]
        if not self.sv_on:
            return np.where(pl >= 0, self.tol[np.maximum(pl, 0)], 0.0)
        t = np.zeros(self.next_pid)
        k = CITY_COLS["tol"]
        for pid, P in self.polities.items():
            if P["ended"] is None:
                t[pid] = self.sview(P)[k]
        return t

    def saccept(self, A, B, level):
        """accept() for two states, on their cultures."""
        if not self.cc_on:
            return self.accept(A["lin"], B["lin"], level)
        need, width = level
        need = need * (1 - self.ssim(A, B))
        return sigmoid((self.eff(A, "tol") - need) / width) * \
            sigmoid((self.eff(B, "tol") - need) / width)

    def city_elite_to(self, A, t):
        """`city_culture`: a conquered or ceded city takes its new
        master's elite (the capital's); its commons stay."""
        if not self.cc_on or t not in self.cities or \
                A["capital"] not in self.cities:
            return
        self.CE[self.cities[t]["id"]] = self.CE[self.cities[A["capital"]]["id"]]
        self.count("city_new_elite")

    # ---- the yearly step
    def city_culture(self):
        """Commons and elites move; elites may be overthrown; cities feed
        their lineages, may found new ones; close lineages merge."""
        recs = list(self.cities.values())
        if not recs:
            return
        W, nL = self.W, self.nL
        cells = np.array([r["cell"] for r in recs])
        ids = np.array([r["id"] for r in recs])
        n, K = len(recs), self.CM.shape[1]
        cols = self.city_cols()
        ct, cc = cols["tol"], cols["conf"]
        M, E = self.CM[ids], self.CE[ids]
        occ = self.lin >= 0
        self.Chome[ids] = self.lin[cells]
        # residents around each city: hinterland cells, main and minority
        pos = -np.ones(W.N, int)
        pos[cells] = np.arange(n)
        hc = np.nonzero(occ & (self.cell_city >= 0))[0]
        k = pos[self.cell_city[hc]]
        ok = k >= 0
        hc, k = hc[ok], k[ok]
        RV = np.zeros((n, K))
        Rw = np.zeros(n)
        np.add.at(RV, k, self.pop[hc, None] * self.lin_vals(self.lin[hc]))
        np.add.at(Rw, k, self.pop[hc])
        mm = self.mlin[hc] >= 0
        if mm.any():
            np.add.at(RV, k[mm], self.mpop[hc[mm], None] *
                      self.lin_vals(self.mlin[hc[mm]]))
            np.add.at(Rw, k[mm], self.mpop[hc[mm]])
        # further peoples (WP15)
        x, kx = self.city_xrows(pos)
        if len(x):
            np.add.at(RV, kx, self.rh[x, None] * self.lin_vals(self.rl[x]))
            np.add.at(Rw, kx, self.rh[x])
        RV = np.where(Rw[:, None] > 0, RV / np.maximum(Rw, 1e-9)[:, None], M)
        conf, tol = M[:, cc], M[:, ct]
        open_ = (0.5 + tol) * (1.5 - conf)
        # the pulls below work on the commons less their own history
        hist = "city_history" in self.on
        H = self.CH[ids] if hist else np.zeros_like(M)
        B = M - H
        # rural inflow pulls the commons home, the more conformist the more
        dM = CITY_RURAL * (0.5 + RV[:, cc])[:, None] * (RV - B)
        xyz = W.xyz[cells]
        dkm = city_km(xyz)
        size = np.sqrt(np.maximum(self.city_sizes(cells), 1))
        port = 0.5 + 0.5 * np.maximum(W.coastal[cells], W.river[cells])
        pol = np.array([r["polity"] for r in recs])
        if "city_influence" in self.on:
            # one pull: every city on every other, weighted by contact,
            # trade and administration x the source's size
            Wt = self.city_weights(recs, ids, cells, pol, M, dkm, size, port)
            tot = Wt.sum(1)
            sat = np.minimum(1, tot / CITY_INF_W)
            den = np.maximum(tot, 1e-12)[:, None]
            has = (tot > 0)[:, None]
            tM = np.where(has, (Wt @ M) / den, B)
            tE = np.where(has, (Wt @ E) / den, E)
            openE = (0.5 + E[:, ct]) * (1.5 - E[:, cc])
            dM += CITY_INF * (sat * open_)[:, None] * (tM - B)
            dE = CITY_INF * (sat * openE)[:, None] * (tE - E)
        else:
            # nearby, similar cities
            same = np.array([r["culture"] for r in recs])
            sim = city_sim(M, same[:, None] == same[None, :])
            Wn = np.exp(-dkm / CITY_NEAR_KM) * sim * size[None, :]
            np.fill_diagonal(Wn, 0)
            tot = Wn.sum(1)
            has = tot > 0
            tgt = np.where(has[:, None], (Wn @ M) / np.maximum(tot, 1e-12)[:, None],
                           M)
            dM += CITY_NEAR * np.minimum(1, tot / CITY_NEAR_W)[:, None] * \
                open_[:, None] * (tgt - B)
            # trade partners: the capitals of states its state trades with;
            # ports and river towns trade most
            cap_of = {}
            for pid, P in self.polities.items():
                if P["ended"] is None and P["capital"] in self.cities:
                    cap_of[pid] = self.cities[P["capital"]]["id"]
            tr = {}
            for (x, y), t in self.ties.items():
                if t > 0 and x in cap_of and y in cap_of:
                    tr.setdefault(x, []).append((cap_of[y], t))
                    tr.setdefault(y, []).append((cap_of[x], t))
            if "trade_local" in self.on:
                # each city trades most with the partner state's cities nearest
                # it: a partner counts its tie x the nearness of its nearest
                # city, and lends the commons of its cities weighted by
                # nearness x sqrt(size)
                near = np.exp(-dkm / CITY_TRADE_KM)
                self.Ctnear[ids] = 0.0
                by_pol = {}
                for j in range(n):
                    by_pol.setdefault(int(pol[j]), []).append(j)
                ptr = {}
                for (x, y), t in self.ties.items():
                    if t > 0 and x in by_pol and y in by_pol:
                        ptr.setdefault(x, []).append((y, t))
                        ptr.setdefault(y, []).append((x, t))
                for x, q in ptr.items():
                    js = np.array(by_pol[x])
                    wt, tg = np.zeros(len(js)), np.zeros((len(js), K))
                    for y, t in q:
                        ms = np.array(by_pol[y])
                        a = near[np.ix_(js, ms)]
                        wa = a * size[None, ms]
                        T = (wa @ M[ms]) / np.maximum(wa.sum(1), 1e-12)[:, None]
                        g = t * a.max(1)
                        wt += g
                        tg += g[:, None] * T
                    vol = np.minimum(1.0, wt)
                    self.Ctnear[ids[js]] = vol
                    ok = wt > 0
                    jj = js[ok]
                    f = vol[ok] * port[jj] * open_[jj]
                    dM[jj] += CITY_TRADE * f[:, None] * (
                        tg[ok] / wt[ok][:, None] - B[jj])
            else:
                for j in range(n):
                    q = tr.get(int(pol[j]))
                    if not q:
                        continue
                    w = np.array([t for _, t in q])
                    T = self.CM[[m for m, _ in q]]
                    vol = min(1.0, float(w.sum()))
                    dM[j] += CITY_TRADE * vol * port[j] * open_[j] * (
                        (w[:, None] * T).sum(0) / w.sum() - B[j])
            # elites: a subject city's elite moves toward its capital's
            dE = np.zeros((n, K))
            hcol = cols["hier"]
            for j in range(n):
                P = self.polities.get(int(pol[j]))
                if P is None or P["ended"] is not None or \
                        P["capital"] == cells[j] or int(pol[j]) not in cap_of:
                    continue
                dE[j] = CITY_RULE * E[j, hcol] * (self.CE[cap_of[int(pol[j])]] -
                                                   E[j])
        # experience lands on the commons that live it
        if "experience" in self.on:
            dX = self.city_experience(ids, cells, pol, M, cols)
            if hist:
                # experience is remembered: it builds the city's history,
                # which fades over CITY_HIST years
                dH = dX - H / CITY_HIST
                self.CH[ids] = H + DT * dH
                dM += dH
            else:
                dM += dX
        noise = self.R("city_culture").normal(
            0, CITY_NOISE * math.sqrt(DT), (n, K))
        M = np.clip(M + DT * dM + noise, 0.01, 0.99)
        E = np.clip(E + DT * dE + self.R("city_culture").normal(
            0, CITY_NOISE * math.sqrt(DT), (n, K)), 0.01, 0.99)
        self.CM[ids], self.CE[ids] = M, E
        self.city_revolts(recs, ids, cells, pol)
        self.city_feedback(recs, ids, cells)
        if self.year % FUSE_EVERY == 0:
            self.lineage_fusion()
        self._pt = {}

    def city_weights(self, recs, ids, cells, pol, M, dkm, size, port):
        """`city_influence`: the weight of city j on city i,
        size_j x (contact + CITY_INF_TRADE x trade x asymmetry +
        CITY_INF_ADM x administration). Contact: exp(-km / CITY_NEAR_KM)
        x similarity. Trade: the tie of their states (CITY_TIE_IN inside
        one state) x exp(-km / CITY_TRADE_KM) x both ports. Asymmetry:
        2 x j's share of the pair's market reach (sum of trade x size),
        so a hub sways its partners more than they sway it.
        Administration: i's capital only, its administration x
        exp(-km / CITY_ADM_KM); with `adm_reach`, x exp(-travel distance /
        (ADM_REACH_F x the state's reach)) at weight ADM_REACH_W instead.
        Records each city's capital and own-state shares of the weight."""
        n = len(ids)
        cul = np.array([r["culture"] for r in recs])
        Wc = np.exp(-dkm / CITY_NEAR_KM) * city_sim(M, cul[:, None] ==
                                                     cul[None, :])
        # state ties as a matrix over the states that hold cities
        up, pix = np.unique(pol, return_inverse=True)
        Tp = np.zeros((len(up), len(up)))
        if self.ties:
            kk = np.array(list(self.ties.keys()))
            tt = np.array(list(self.ties.values()))
            a = np.minimum(np.searchsorted(up, kk[:, 0]), len(up) - 1)
            b = np.minimum(np.searchsorted(up, kk[:, 1]), len(up) - 1)
            ok = (up[a] == kk[:, 0]) & (up[b] == kk[:, 1])
            Tp[a[ok], b[ok]] = tt[ok]
            Tp[b[ok], a[ok]] = tt[ok]
        live = np.array([int(p) in self.polities and
                         self.polities[int(p)]["ended"] is None for p in up])
        Tp[np.diag_indices(len(up))] = np.where(live, CITY_TIE_IN, 0.0)
        V = Tp[pix[:, None], pix[None, :]] * np.exp(-dkm / CITY_TRADE_KM) * \
            port[:, None] * port[None, :]
        np.fill_diagonal(V, 0)
        reach = V @ size
        A = 2 * reach[None, :] / np.maximum(reach[:, None] + reach[None, :],
                                            1e-12)
        # each city's capital
        pos = {int(c): j for j, c in enumerate(cells)}
        cap = -np.ones(n, int)
        for j in range(n):
            P = self.polities.get(int(pol[j]))
            if P is not None and P["ended"] is None:
                cap[j] = pos.get(int(P["capital"]), -1)
        R = np.zeros((n, n))
        sub = np.nonzero((cap >= 0) & (cap != np.arange(n)))[0]
        a = self.Cadm[ids[cap[sub]]]
        if "adm_reach" in self.on:
            # the capital reaches its cities over the state's own travel
            # distance (roads, sailing, provincial seats) at a scale set
            # by its administrative reach
            dd, sc = dkm[sub, cap[sub]].copy(), np.ones(len(sub))
            for p in np.unique(pol[sub]):
                P = self.polities[int(p)]
                m = pol[sub] == p
                dd[m] = self.power_dist(P)[cells[sub[m]]]
                sc[m] = ADM_REACH_F * self.reach(P)
            R[sub, cap[sub]] = a * np.exp(-dd / sc)
            wa = ADM_REACH_W
        else:
            R[sub, cap[sub]] = a * np.exp(-dkm[sub, cap[sub]] / CITY_ADM_KM)
            wa = CITY_INF_ADM
        Wt = size[None, :] * (Wc + CITY_INF_TRADE * V * A + wa * R)
        np.fill_diagonal(Wt, 0)
        tot = np.maximum(Wt.sum(1), 1e-12)
        self.Cwcap[ids] = 0.0
        self.Cwcap[ids[sub]] = Wt[sub, cap[sub]] / tot[sub]
        self.Cwown[ids] = (Wt * (pol[:, None] == pol[None, :])).sum(1) / tot
        return Wt

    def city_revolts(self, recs, ids, cells, pol):
        """A conformist commons reins in a divergent elite: chance ∝
        conformity x (gap / CITY_GAP0)^2; the elite falls most of the way
        back to the commons; in a subject city the province may break
        away, in a capital the dynasty ends."""
        cc = self.city_cols()["conf"]
        M, E = self.CM[ids], self.CE[ids]
        gap = np.sqrt(np.mean((E - M) ** 2, 1))
        pr = DT * CITY_REVOLT * M[:, cc] * (gap / CITY_GAP0) ** 2
        hit = np.nonzero(self.R("city_culture").random(len(ids)) <
                         np.minimum(pr, 0.9))[0]
        for j in hit:
            i, cell = ids[j], int(cells[j])
            self.CE[i] = self.CM[i] + CITY_REVOLT_KEEP * (self.CE[i] -
                                                          self.CM[i])
            self.count("city_revolt")
            self._pt.pop(int(pol[j]), None)
            P = self.polities.get(int(pol[j]))
            if P is None or P["ended"] is not None:
                continue
            self.revolted[self.cell_city == cell] = 1.0
            if P["capital"] == cell:
                self.count("city_revolt_capital")
                P["cohesion"] *= 0.9
                if self.rt and "x" in P.get("ruler", {}):
                    P["ruler"]["x"], P["ruler"]["dyn"] = \
                        self.draw_ruler(P["id"], P)
                if len(P["cities"]) >= 5:
                    self.log("revolt", f"the people of {self.place(cell)} "
                             f"overthrow the court of {self.pname(P['id'])}",
                             cell=cell, polities=[P['id']])
            elif cell in P["cities"] and self.R("city_culture").random() < \
                    CITY_REVOLT_SECEDE:
                self.count("city_revolt_secede")
                self.revolt(P["id"], cell)

    def city_feedback(self, recs, ids, cells):
        """Downstream: lineages living in a city move toward its commons
        by their share of it x city size / lineage size; a city whose
        commons stray far from its home lineage founds a new one."""
        nL = self.nL
        occ = self.lin >= 0
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ],
                           minlength=nL)
        Lc = self.lin[cells]
        ok = Lc >= 0
        acc = np.zeros((nL, self.CM.shape[1]))
        wsum = np.zeros(nL)
        u = self.city_sizes(cells)
        V = self.lin_vals(np.maximum(Lc, 0))
        np.add.at(acc, Lc[ok], (u[ok, None] * (self.CM[ids[ok]] - V[ok])))
        np.add.at(wsum, Lc[ok], u[ok])
        Ls = np.nonzero(wsum > 0)[0]
        d = DT * CITY_DOWN * acc[Ls] / np.maximum(Lpop[Ls], 1)[:, None]
        nT = len(TRAITS)
        self.LT[Ls] = np.clip(self.LT[Ls] + d[:, :nT], 0.01, 0.99)
        self.LX[Ls] = np.clip(self.LX[Ls] + d[:, nT:], 0.01, 0.99)
        # speciation
        dist = np.sqrt(np.mean((self.CM[ids] - V) ** 2, 1))
        for j in np.nonzero(ok & (dist > CITY_SPEC))[0]:
            cell, L = int(cells[j]), int(Lc[j])
            rec = recs[j]
            D = self.new_lineage(int(self.Lpeople[L]), L, "city")
            if D == L:
                continue
            self.LT[D] = self.CM[ids[j], :nT]
            self.LX[D] = self.CM[ids[j], nT:]
            self.CH[ids[j]] = 0.0
            m = (self.cell_city == cell) & (self.lin == L)
            m[cell] = True
            self.lin[m] = D
            mm = (self.cell_city == cell) & (self.mlin == L)
            self.mlin[mm] = D
            self.Chome[ids[j]] = D
            for P in self.polities.values():
                if P["ended"] is None and P["lin"] == L and \
                        P["capital"] == cell:
                    P["lin"] = D
                    self.pver += 1
            self.count("city_speciation")
            if self.pop[cell] > 0 and len(self.cities) >= 1:
                self.first(("city_spec", int(self.Lpeople[L])), "culture",
                           f"the city at {self.place(cell)} grows apart from "
                           f"{self.lname(L)}: a new lineage, "
                           f"{self.lname(D)}",
                           cell=cell, lineages=[L, D],
                           peoples=[self.keys[self.Lpeople[L]]])

    def lineage_fusion(self):
        """Lineages of one people that live side by side under one state
        fuse where they meet. Every FUSE_EVERY years, each pair touching
        inside a state ages by FUSE_EVERY (conquest or parting resets it);
        the contact zone is each one's cells in that state within FUSE_KM
        of the other's. Chance per year FUSE_K x min(1, age / FUSE_T) x
        (1 - mean separation) x (0.5 + the larger's tolerance) x
        exp(-distance / FUSE_D): distance slows fusion, never bars it. A
        zone minority under FUSE_SHARE is absorbed into the local lineage;
        otherwise both zones become a new lineage with two parents. The
        rest of each lineage carries on. Recorded in lineage_events."""
        W = self.W
        la, lb = self.lin[W.E1], self.lin[W.E2]
        pa, pb = self.cell_pol[W.E1], self.cell_pol[W.E2]
        m = (la >= 0) & (lb >= 0) & (la != lb) & (pa >= 0) & (pa == pb)
        m &= self.Lpeople[np.maximum(la, 0)] == self.Lpeople[np.maximum(lb, 0)]
        keys = set()
        if m.any():
            t = np.unique(np.stack([pa[m], np.minimum(la[m], lb[m]),
                                    np.maximum(la[m], lb[m])], 1), axis=0)
            keys = {tuple(int(v) for v in k) for k in t}
        age = {k: self.fuse_age.get(k, 0) + FUSE_EVERY for k in keys}
        self.fuse_age = age
        if not keys:
            return
        occ = self.lin >= 0
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ],
                           minlength=self.nL)
        sep, tol = TI["separation"], TI["tolerance"]
        rng = self.R("city_culture")
        cos_km = math.cos(FUSE_KM / 6371.0)
        busy = set()
        for k in sorted(keys):
            S, A, B = k
            if A in busy or B in busy:
                continue
            d = float(np.sqrt(np.mean((self.lin_vals(A) -
                                       self.lin_vals(B)) ** 2)))
            host = A if Lpop[A] >= Lpop[B] else B
            h = FUSE_K * min(1.0, age[k] / FUSE_T) * \
                (1 - 0.5 * (self.LT[A, sep] + self.LT[B, sep])) * \
                (0.5 + self.LT[host, tol]) * math.exp(-d / FUSE_D)
            if self.year % 500 == 0:
                # every pair at risk, fused or not (lineage_pairs.csv)
                self.lin_pairs.append(dict(
                    year=self.year, people=self.keys[int(self.Lpeople[A])],
                    a=A, b=B, state=S, years_together=age[k],
                    pop_a=round(float(Lpop[A])), pop_b=round(float(Lpop[B])),
                    distance=round(d, 4), hazard=round(h, 6)))
            if rng.random() >= 1 - math.exp(-h * FUSE_EVERY):
                continue
            inS = self.cell_pol == S
            ca = np.nonzero(inS & (self.lin == A))[0]
            cb = np.nonzero(inS & (self.lin == B))[0]
            if not len(ca) or not len(cb):
                continue
            # contact zone: each side's cells within FUSE_KM of the other
            za = ca[cKDTree(W.xyz[cb]).query(W.xyz[ca])[0] <=
                    math.sqrt(2 - 2 * cos_km)]
            zb = cb[cKDTree(W.xyz[ca]).query(W.xyz[cb])[0] <=
                    math.sqrt(2 - 2 * cos_km)]
            pa_, pb_ = float(self.pop[za].sum()), float(self.pop[zb].sum())
            if pa_ + pb_ <= 0:
                continue
            big, small = (A, B) if pa_ >= pb_ else (B, A)
            zbig, zsmall = (za, zb) if big == A else (zb, za)
            pbig, psmall = max(pa_, pb_), min(pa_, pb_)
            share = psmall / (pbig + psmall)
            if share < FUSE_SHARE:
                kind, to, moved = "absorb", big, zsmall
                w1, w2 = Lpop[big] + 1, psmall + 1
                self.LT[big] = (w1 * self.LT[big] + w2 * self.LT[small]) / \
                    (w1 + w2)
                self.LX[big] = (w1 * self.LX[big] + w2 * self.LX[small]) / \
                    (w1 + w2)
            else:
                kind, moved = "fuse", np.concatenate([zbig, zsmall])
                to = self.new_lineage(int(self.Lpeople[big]), big, "fusion")
                if to == big:
                    continue
                self.Lparent2[to] = small
                w1, w2 = pbig + 1, psmall + 1
                self.LT[to] = (w1 * self.LT[big] + w2 * self.LT[small]) / \
                    (w1 + w2)
                self.LX[to] = (w1 * self.LX[big] + w2 * self.LX[small]) / \
                    (w1 + w2)
            for t in ("agri", "metal", "sail", "fishing", "craft", "roadt",
                      "bronze", "iron", "steel"):
                v = getattr(self, t)
                v[to] = max(v[A], v[B])
            self.lver += 1                  # agri, metal: ltab()
            olds = (small,) if kind == "absorb" else (A, B)
            mv = np.zeros(len(self.lin), bool)
            mv[moved] = True
            for L in olds:
                self.mlin[inS & (self.mlin == L)] = to
            self.lin[mv] = to
            for cell in moved:
                rec = self.cities.get(int(cell))
                if rec is not None and self.Chome[rec["id"]] in olds:
                    self.Chome[rec["id"]] = to
            left = {L: float(self.pop[self.lin == L].sum()) for L in olds}
            for L in olds:
                if left[L] <= 0:
                    self.Lfate[L] = f"{kind}:{to}"
            for P in self.polities.values():
                if P["ended"] is None and P["lin"] in olds and \
                        (P["id"] == S or left[P["lin"]] <= 0):
                    P["lin"] = to
                    self.pver += 1
            self.lin_events.append(dict(
                year=self.year, kind=kind, people=self.keys[self.Lpeople[A]],
                a=big, b=small, to=to, state=S, years_together=age[k],
                pop_a=round(pbig), pop_b=round(psmall),
                share=round(share, 3), distance=round(d, 4),
                a_whole=int(big in olds and left[big] <= 0),
                b_whole=int(left[small] <= 0)))
            self.count("lineage_" + kind)
            if all(left[L] <= 0 for L in olds):
                self.count("lineage_" + kind + "_whole")
            self.first((kind, int(self.Lpeople[A])), "culture",
                       f"{self.lname(small)} and {self.lname(big)}, long "
                       f"under one rule, " +
                       ("become one people: " + self.lname(to)
                        if kind == "fuse" else
                        f"merge where they meet; {self.lname(big)} absorbs "
                        f"the newcomers"),
                       lineages=[small, big],
                       peoples=[self.keys[self.Lpeople[A]]])
            busy.update((A, B, to))

    def city_experience(self, ids, cells, pol, M, cols):
        """What a city's commons live through, as yearly pushes on their
        traits: the lineage experience forms (war, trade, hardship, raids,
        revolt; order = its state's administration) without path
        dependence or generation spikes (C), on exposures aggregated over
        its hinterland this tick and smoothed over EXP_MEM years."""
        n = len(ids)
        W = self.W
        atwar = np.zeros(self.next_pid)
        for k in self.wars:
            atwar[list(k)] = 1
        tsum = np.zeros(self.next_pid)
        nn = np.zeros(self.next_pid)
        for x, y in self.adj:
            t = self.ties.get((x, y), 0.0)
            tsum[x] += t
            tsum[y] += t
            nn[x] += 1
            nn[y] += 1
        vol = np.minimum(1.5, TRADE_MEAN_K * tsum / np.maximum(nn, 1))
        pos = -np.ones(W.N, int)
        pos[cells] = np.arange(n)
        hc = np.nonzero((self.lin >= 0) & (self.cell_city >= 0))[0]
        k = pos[self.cell_city[hc]]
        ok = k >= 0
        hc, k = hc[ok], k[ok]
        w = self.pop[hc]
        den = np.maximum(np.bincount(k, weights=w, minlength=n), 1)
        agg = lambda x: np.bincount(k, weights=w * x, minlength=n) / den
        pc = np.maximum(self.cell_pol[hc], 0)
        now = np.stack([agg(atwar[pc]), agg(vol[pc]), agg(self.hard[hc]),
                        agg(self.raided[hc]), agg(self.revolted[hc])], 1)
        a = min(1.0, DT / EXP_MEM)
        self.Cmem[ids] += a * (now - self.Cmem[ids])
        s, v, q, r, u = self.Cmem[ids].T
        if "city_trade" in self.on:
            # ports and river towns live the state's trade most
            v = v * (0.5 + 0.5 * np.maximum(W.coastal[cells], W.river[cells]))
        v1 = np.minimum(v, 1)
        order = np.array([self.admin[self.polities[int(x)]["lin"]]
                          if int(x) in self.polities else 0.0 for x in pol])
        safe = (1 - s) * (1 - q)
        # city life: diversity and size
        peo = np.array([self.cities[int(c)]["culture"] for c in cells])
        if self.uc_on:
            # `urban_city`: 0 at URBAN_MIN townspeople, 1 at ten times it
            size = np.clip(np.log10(np.maximum(self.city_sizes(cells), 1) /
                                    URBAN_MIN), 0, 1)
        else:
            size = np.clip(np.log10(np.maximum(self.pop[cells], 1) /
                                    self.pcity[peo]), 0, 1)
        mm = self.mlin[hc] >= 0
        x, kx = self.city_xrows(pos)
        key = np.concatenate([k * self.nL + self.lin[hc],
                              k[mm] * self.nL + self.mlin[hc[mm]],
                              kx * self.nL + self.rl[x]])
        kw = np.concatenate([w, self.mpop[hc[mm]], self.rh[x]])
        uk, inv = np.unique(key, return_inverse=True)
        lw = np.bincount(inv, weights=kw)
        top = np.zeros(n)
        np.maximum.at(top, uk // self.nL, lw)
        div = 1 - top / np.maximum(np.bincount(
            np.concatenate([k, k[mm], kx]), weights=kw, minlength=n), 1)
        d = np.zeros_like(M)

        def push(a_, up, down):
            j = cols[a_]
            x = M[:, j]
            d[:, j] = EXP_SCALE * (up * (1 - x) - down * x)
        push("tol", EXP_TRADE * v + URB_TOL * div, EXP_WAR * s +
             EXP_HARD * q + EXP_RAID / 2 * r + EXP_REVOLT / 2 * u)
        push("trade", EXP_TRADE / 2 * v, EXP_DISRUPT * (s + r))
        push("viol", EXP_WAR * s + EXP_RAID * r + EXP_REVOLT * u,
             EXP_TRADE_V * v + EXP_PEACE * order * (1 - s) +
             URB_VIOL * size * order)
        push("sep", EXP_REVOLT / 2 * u, EXP_CALM * v1)
        push("coh", EXP_WAR / 2 * s, EXP_LUX * v1 + EXP_CALM * order *
             (1 - s))
        push("hier", EXP_WAR / 2 * s, 0.0)
        push("conf", EXP_WAR / 2 * s + EXP_HARD * q + EXP_REVOLT / 2 * u,
             EXP_TRADE / 2 * v1 + EXP_LOOSE * order * safe +
             URB_CONF * size)
        return d

    # ---- diagnostics
    def city_record(self):
        """Every PRICE_EVERY years: variance of each trait by level
        (between peoples, between lineages within a people, between
        cities within a lineage), the rural-urban gap (commons vs home
        lineage) and the elite-commons gap, per people and trait; and per
        city its gaps against its state's trade volume."""
        recs = list(self.cities.values())
        if not recs:
            return
        occ = self.lin >= 0
        nL = self.nL
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        names = TRAITS + XTRAITS
        ids = np.array([r["id"] for r in recs])
        cells = np.array([r["cell"] for r in recs])
        home = np.maximum(self.lin[cells], 0)
        peo = self.Lpeople[home]
        M, E = self.CM[ids], self.CE[ids]
        V = self.lin_vals(home)
        alive = np.nonzero(Lpop > 0)[0]
        LV = self.lin_vals(alive)
        Lp = self.Lpeople[alive]
        w = Lpop[alive]

        def wvar(x, wt):
            if wt.sum() <= 0 or len(x) < 2:
                return np.full(x.shape[1], np.nan)
            m = (wt[:, None] * x).sum(0) / wt.sum()
            return (wt[:, None] * (x - m) ** 2).sum(0) / wt.sum()
        pm = np.array([(w[Lp == c, None] * LV[Lp == c]).sum(0) /
                       max(w[Lp == c].sum(), 1e-9) for c in range(self.nP)])
        pw = np.array([w[Lp == c].sum() for c in range(self.nP)])
        between = wvar(pm, pw)
        for c in list(range(self.nP)) + [-1]:
            gl = (Lp == c) if c >= 0 else np.ones(len(alive), bool)
            gc = (peo == c) if c >= 0 else np.ones(len(ids), bool)
            wl = wvar(LV[gl], w[gl]) if gl.sum() > 1 else \
                np.full(len(names), np.nan)
            # cities within lineage: pooled over lineages with 2+ cities
            num = np.zeros(len(names))
            den = 0.0
            for L in np.unique(home[gc]):
                k = gc & (home == L)
                if k.sum() >= 2:
                    num += k.sum() * M[k].var(0)
                    den += k.sum()
            wc = num / den if den else np.full(len(names), np.nan)
            ru = np.abs(M[gc] - V[gc]).mean(0) if gc.any() else \
                np.full(len(names), np.nan)
            rs = (M[gc] - V[gc]).mean(0) if gc.any() else \
                np.full(len(names), np.nan)
            ec = np.abs(E[gc] - M[gc]).mean(0) if gc.any() else \
                np.full(len(names), np.nan)
            for j, t in enumerate(names):
                self.city_rows.append(dict(
                    year=self.year, people=self.keys[c] if c >= 0 else "ALL",
                    trait=t, n_cities=int(gc.sum()),
                    var_peoples=round(float(between[j]), 5) if c < 0 else "",
                    var_lineages=round(float(wl[j]), 5),
                    var_cities=round(float(wc[j]), 5),
                    rural_urban=round(float(ru[j]), 4),
                    rural_urban_signed=round(float(rs[j]), 4),
                    elite_commons=round(float(ec[j]), 4)))
        tsum, nn = {}, {}
        for (x, y), t in self.ties.items():
            for a in (x, y):
                tsum[a] = tsum.get(a, 0.0) + t
                nn[a] = nn.get(a, 0) + 1
        for j, r in enumerate(recs):
            pid = r["polity"]
            vol = min(1.5, TRADE_MEAN_K * tsum.get(pid, 0.0) /
                      max(nn.get(pid, 0), 1))
            self.city_gap_rows.append(dict(
                year=self.year, city=int(r["id"]), people=self.keys[peo[j]],
                pop=round(float(self.pop[cells[j]])), trade=round(vol, 4),
                trade_city=round(float(self.Cmem[int(r["id"]), 1] * (
                    0.5 + 0.5 * max(self.W.coastal[cells[j]],
                                    self.W.river[cells[j]]))
                    if "city_trade" in self.on else
                    self.Cmem[int(r["id"]), 1]), 4),
                trade_near=round(float(self.Ctnear[int(r["id"])]), 4),
                adm=round(float(self.Cadm[int(r["id"])]), 4),
                w_capital=round(float(self.Cwcap[int(r["id"])]), 4),
                w_state=round(float(self.Cwown[int(r["id"])]), 4),
                port=int(self.W.coastal[cells[j]] or self.W.river[cells[j]]),
                rural_urban=round(float(np.sqrt(np.mean((M[j] - V[j]) ** 2))),
                                  4),
                elite_commons=round(float(np.sqrt(np.mean(
                    (E[j] - M[j]) ** 2))), 4)))
            row = dict(year=self.year, city=int(r["id"]), lineage=int(home[j]),
                       polity=int(pid), people=self.keys[peo[j]],
                       pop=round(float(self.pop[cells[j]])))
            row.update({"m_" + t: round(float(M[j, k]), 3)
                        for k, t in enumerate(names)})
            row.update({"e_" + t: round(float(E[j, k]), 3)
                        for k, t in enumerate(names)})
            row["h_rms"] = round(float(np.sqrt(np.mean(
                self.CH[int(r["id"])] ** 2))), 4)
            self.city_trait_rows.append(row)

    # ---- administration (`city_admin`)
    def city_admin(self):
        """Administration is built in cities: invented at the city's own
        statecraft (x the realm-size factor), borrowed from nearby cities
        of other states and from trade partners' capitals, and spread
        inside a state from its best-run city at ADM_UP x hierarchy x
        (1.5 - conformity) (the state learns from its best and deploys
        their bureaucrats). A state's administration is its capital's;
        it is written onto the ruling lineage, where the rest of the model
        reads it. Other lineages' administration lapses at DECAY_ADMIN."""
        recs = list(self.cities.values())
        if not recs:
            return
        W = self.W
        cols = self.city_cols()
        ids = np.array([r["id"] for r in recs])
        cells = np.array([r["cell"] for r in recs])
        pol = np.array([r["polity"] for r in recs])
        n = len(ids)
        a = self.Cadm[ids].copy()
        hc = cols["hier"]
        h = 0.5 * (self.CE[ids, hc] + self.CM[ids, hc])
        V = h[:, None] * self.CE[ids] + (1 - h)[:, None] * self.CM[ids]
        nc = np.array([len(self.polities[int(x)]["cities"])
                       if int(x) in self.polities else 1 for x in pol])
        inv = ADM_INV * V[:, cols["state"]] * (1 - a) * \
            np.sqrt(np.clip(nc / 5, 0, 1))
        # borrowing from cities of other states, by distance, and from
        # trade partners' capitals, by tie
        dkm = city_km(W.xyz[cells])
        other = pol[:, None] != pol[None, :]
        gap = np.clip(a[None, :] - a[:, None], 0, None) * \
            np.exp(-dkm / CITY_NEAR_KM) * other
        g = gap.max(1) if n > 1 else np.zeros(n)
        cap_of = {pid: self.cities[P["capital"]]["id"]
                  for pid, P in self.polities.items()
                  if P["ended"] is None and P["capital"] in self.cities}
        if self.ties and cap_of:
            # partner capitals' administration x tie, as a city x partner
            # matrix
            up, pix = np.unique(pol, return_inverse=True)
            ks = sorted(cap_of)
            ci = {o: m for m, o in enumerate(ks)}
            capadm = self.Cadm[[cap_of[o] for o in ks]]
            T = np.zeros((len(up), len(ks)))
            for (x, y), t in self.ties.items():
                if t <= 0:
                    continue
                for u, o in ((x, y), (y, x)):
                    r = np.searchsorted(up, u)
                    if r < len(up) and up[r] == u and o in ci:
                        T[r, ci[o]] = t
            Tj = T[pix]
            has = Tj > 0
            cand = np.where(has, Tj * (capadm[None, :] - a[:, None]), -np.inf)
            g = np.maximum(g, cand.max(1))
        bor = ADM_BORROW * g * (0.3 + V[:, cols["innov"]]) * \
            (1 - COST_COH * V[:, cols["coh"]])
        a = np.clip(a + DT * (inv + bor), 0, 1)
        # inside a state, toward its best-run city
        best = {}
        for j in range(n):
            p = int(pol[j])
            best[p] = max(best.get(p, 0.0), a[j])
        for j in range(n):
            P = self.polities.get(int(pol[j]))
            if P is None or P["ended"] is not None:
                continue
            v = self.state_vec(P)
            r = min(1.0, DT * ADM_UP * v[cols["hier"]] *
                    (1.5 - v[cols["conf"]]))
            a[j] += r * (best[int(pol[j])] - a[j])
        self.Cadm[ids] = a
        # the state's administration is its capital's
        ruling = set()
        for P in sorted((P for P in self.polities.values()
                         if P["ended"] is None and
                         P["capital"] in self.cities),
                        key=lambda P: len(P["cities"])):
            self.admin[P["lin"]] = self.Cadm[self.cities[P["capital"]]["id"]]
            ruling.add(P["lin"])
        occ = self.lin >= 0
        A = np.unique(self.lin[occ])
        rest = np.array([L for L in A if L not in ruling], int)
        if len(rest):
            self.admin[rest] = np.maximum(
                0.0, self.admin[rest] - DT * DECAY_ADMIN)
