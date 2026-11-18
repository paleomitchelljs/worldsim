"""Founding groups, migration, budding, voyages, minorities."""
import math
import numpy as np
from scipy import ndimage

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class SettlementMixin:
    def wander_setup(self, groups):
        """Before the run, each founding group is dropped at a random
        habitable cell and wanders: every step it stays with probability
        min(0.95, suitability / the people's 95th-percentile suitability),
        otherwise it moves to a neighbouring cell chosen in proportion to
        the square of the surrounding land's suitability (biome preference
        x productivity, smoothed over ~3 cells), so groups can sense better
        land beyond their immediate neighbours."""
        W = self.W
        best = self.paff.max(1, keepdims=True)
        fit = best * (self.paff / best) ** BIOME_K
        dens = 0.75 * W.forage + 0.25 * W.farm
        wb = (1 + (FISH0 + FISH1 * FISH_START) * W.water)[None]
        suit = W.area[None] * dens[None] * fit[:, W.biome] * wb
        if self.homelands == "continents":
            big = 15e6 if self.nP <= 5 else 4e6
            small = W.landmass_area[W.landmass] < big
            for c, p in enumerate(self.P):
                if not p.get("anywhere"):
                    suit[c, small] = 0
        # regional starts (roster key `region`): founders start and wander
        # only within their people's homeland
        for c, p in enumerate(self.P):
            if p.get("region"):
                suit[c, ~self.region_mask(p["region"])] = 0
        ref = np.array([np.percentile(s[s > 0], 95) for s in suit])
        self.suit = suit
        look = np.zeros_like(suit)
        g = np.zeros((NY, NX))
        for c in range(self.nP):
            g[:] = 0
            g[W.row, W.col] = suit[c] / ref[c]
            look[c] = ndimage.gaussian_filter(g, 3, mode="wrap")[W.row, W.col]
        self.look = (look + 1e-6) ** 2
        self.pstay = np.minimum(0.95, suit / ref[:, None])
        self.wpos, self.wfrom = {}, {}
        for c, k in groups:
            ok = np.nonzero(suit[c] > 0)[0]
            self.wpos[(c, k)] = self.wfrom[(c, k)] = int(self.rng.choice(ok))
        self.wander(groups, self.wander_steps, avoid=False)

    def region_mask(self, region):
        """Cells of a homeland: a list of parts, each the landmass at a
        point (lon, lat), optionally only within radius_km of it."""
        W = self.W
        m = np.zeros(W.N, bool)
        for part in region:
            lon, lat = part["at"]
            i = int(np.argmin(np.linalg.norm(
                W.xyz - unit_xyz(np.array(lon), np.array(lat)), axis=1)))
            mm = W.landmass == W.landmass[i]
            if part.get("radius_km"):
                mm &= gc_km(W.xyz, i, np.arange(W.N)) <= part["radius_km"]
            m |= mm
        return m

    def wander(self, groups, steps, avoid):
        if not groups:
            return
        W = self.W
        cs = np.array([c for c, _ in groups])
        pos = np.array([self.wpos[g] for g in groups])
        for _ in range(steps):
            q = self.pstay[cs, pos]
            if avoid:
                q = np.where(self.lin[pos] >= 0, 0, q)
            move = self.rng.random(len(pos)) >= q
            if not move.any():
                continue
            nb = W.nb[pos[move]]
            w = np.where(nb >= 0, self.look[cs[move][:, None],
                                            np.maximum(nb, 0)], 0)
            if avoid:
                w = np.where((nb >= 0) & (self.lin[np.maximum(nb, 0)] < 0),
                             w, 0)
            w = np.where(w.sum(1, keepdims=True) > 0, w,
                         (nb >= 0).astype(float))
            tot = w.sum(1)
            pick = (w.cumsum(1) < (self.rng.random(len(nb)) * tot)[:, None]
                    ).sum(1)
            pick = np.minimum(pick, 7)
            new = nb[np.arange(len(nb)), pick]
            idx = np.nonzero(move)[0]
            good = (new >= 0) & (tot > 0)
            pos[idx[good]] = new[good]
        for g, p in zip(groups, pos):
            self.wpos[g] = int(p)

    def place_arrivals(self):
        while self.arrivals and self.arrivals[0][0] <= self.year:
            _, c, k = self.arrivals.pop(0)
            self.found_group(c, k)
        if self.start_mode == "wander" and self.arrivals:
            # groups not yet arrived keep wandering, avoiding settled land
            self.wander([(c, k) for _, c, k in self.arrivals], 3, avoid=True)

    def empty_near(self, i, c, rings=8):
        """Best empty cell within `rings` steps of i, or -1."""
        W = self.W
        seen, front = {i}, [i]
        for _ in range(rings):
            nxt = []
            for x in front:
                for j in W.nb[x]:
                    if j >= 0 and j not in seen:
                        seen.add(int(j))
                        nxt.append(int(j))
            front = nxt
            cand = [j for j in front if self.lin[j] < 0 and
                    self.suit[c, j] > 0]
            if cand:
                return max(cand, key=lambda j: self.suit[c, j])
        return -1

    def found_group(self, c, k):
        W = self.W
        p = self.P[c]
        i = -1
        if self.start_mode == "wander" and not (p.get("start") and k == 0):
            i = self.wpos[(c, k)]
            if self.lin[i] >= 0:
                i = self.empty_near(i, c)
        if i >= 0:
            pass
        elif p.get("start") and k == 0:
            lon, lat = p["start"]
            i = int(np.argmin(np.linalg.norm(
                W.xyz - unit_xyz(np.array(lon), np.array(lat)), axis=1)))
        else:
            s0 = self.site_score[c].copy()
            s0[self.lin >= 0] = 0
            if self.homelands == "continents":
                big = 15e6 if self.nP <= 5 else 4e6
                s0[W.landmass_area[W.landmass] < big] = 0
            if self.cluster_km > 0 and c in self.first_site:
                s0[gc_km(W.xyz, self.first_site[c], np.arange(W.N)) >
                   self.cluster_km] = 0
            sep_km = self.sep0
            while True:
                s = s0.copy()
                for j in self.chosen:
                    s[gc_km(W.xyz, j, np.arange(W.N)) < sep_km] = 0
                pos = np.nonzero(s > 0)[0]
                if len(pos) or sep_km < 100:
                    break
                sep_km *= 0.7
            if not len(pos):
                pos = np.nonzero(s0 > 0)[0]
                s = s0
            if not len(pos):
                self.log("origin", f"{p['label']} group {k + 1} finds no "
                         "empty land and never arrives")
                return
            n = max(60, int(self.start_pool * len(pos)))
            top = pos[np.argsort(s[pos])[-n:]]
            i = int(self.rng.choice(top, p=s[top] / s[top].sum()))
        self.first_site.setdefault(c, i)
        self.chosen.append(i)
        L = self.new_lineage(c, -1, "start", sd=self.start_vary)
        self.Lseen[L] = {W.landmass[i]}
        self.Pblk[c].add(int(self.blk[i]))
        self.cul[i], self.lin[i], self.pop[i] = c, L, \
            FOUND_FOOD / self.peat[c]
        moved = ""
        if (c, k) in getattr(self, "wfrom", {}):
            d = gc_km(W.xyz, self.wfrom[(c, k)], np.array([i]))[0]
            moved = f", after wandering from {self.place(self.wfrom[(c, k)])}" \
                f" ({d:.0f} km)"
        self.log("origin", f"{p['label']} group {k + 1} {self.lname(L)} "
                 f"founded at {self.place(i)} [{BIOMES[W.biome[i]]}]{moved}")

    def colon(self, j, L=None):
        """How readily settlers of lineages L take cells j: terrain, and
        (with `improvements`) land others have already cleared and worked.
        Wetland peoples do not mind wet ground."""
        c = self.W.colonize[j]
        if L is not None and self.pwet.any():
            w = self.pwet[self.Lpeople[L]]
            wt = self.W.wet[j]
            c = c * (1 - COL_WET * wt * (1 - w)) / (1 - COL_WET * wt)
        return np.minimum(1, c * (1 + IMP_SETTLE * self.imp[j]))

    def adjacency_by_people(self):
        """adj[c, i]: some neighbour of cell i is held by people c."""
        W = self.W
        adj = np.zeros((self.nP, W.N), bool)
        for k in range(8):
            i = np.nonzero(W.nb[:, k] >= 0)[0]
            cn = self.cul[W.nb[i, k]]
            ok = cn >= 0
            adj[cn[ok], i[ok]] = True
        return adj

    def migrate(self):
        """Within a lineage, people drift toward room; empty land is taken
        by budding, pioneer leaps and voyages."""
        W, N = self.W, self.W.N
        ar = np.arange(N)
        occ = self.lin >= 0
        was = occ.copy()
        L = np.where(occ, self.lin, 0)
        c = self.Lpeople[L]
        # capacity does not depend on population, so it is computed once
        # and redone below only where a cell's lineage changes
        Kown, prown = self.Kf(L, ar), self.pref(L, ar)
        press = self.pop / np.maximum(Kown * prown, 1e-3)
        adj = self.adjacency_by_people()
        nadj = adj.sum(0)
        expn, sep = self.expn[L], self.sep[L]
        sep = 1 - self.tol[L]       # keeping apart is intolerance now
        thr = 0.9 - 0.6 * expn
        frac = 0.04 + 0.3 * expn * np.clip(press - thr, 0, 1.5)
        E = np.where(occ, self.pop * frac, 0)
        w = np.zeros((N, 8))
        for k in range(8):
            j = W.nb[:, k]
            jj = np.maximum(j, 0)
            ok = occ & (j >= 0) & (self.lin[jj] == L)
            # where ok, the neighbour is of the same lineage: its own K
            Kt = np.maximum(Kown[jj], 1e-3)
            room = np.clip(1 - self.pop[jj] / (Kt * prown[jj]), 0, 1)
            foreign = (nadj[jj] - adj[c, jj]) > 0
            w[:, k] = ok * room * np.sqrt(Kt) / W.edgecost[:, k] * \
                (1 - 0.9 * sep * foreign)
        Wsum = w.sum(1)
        go = Wsum > 0
        E = np.where(go, E, 0)
        self.pop -= E
        F = (E[:, None] * w / np.where(go, Wsum, 1)[:, None]).ravel()
        tgt = W.nb.ravel()
        m = (tgt >= 0) & (F > 0)
        np.add.at(self.pop, tgt[m], F[m])
        for _ in range(2):
            occ = self.lin >= 0
            L1 = np.where(occ, self.lin, 0)
            ch = np.nonzero(L1 != L)[0]
            if len(ch):
                Kown[ch] = self.Kf(L1[ch], ch)
                prown[ch] = self.pref(L1[ch], ch)
            L = L1
            press = self.pop / np.maximum(Kown * prown, 1e-3)
            adj = self.adjacency_by_people()
            self.settle(*self.budding(press, adj, adj.sum(0), L, occ))
        self.settlers(press)
        self.pioneers(press)
        self.voyages(press)
        self.settler_lineages(np.nonzero((self.lin >= 0) & ~was)[0])

    def settlers(self, press):
        """`dominion`: crowded cells of a state's ruling people send
        settlers into the neighbouring cell of the same state, held by
        another people, where they would have the most room."""
        if not self.dom_on:
            return
        W, N = self.W, self.W.N
        pol = self.cell_pol
        src = np.nonzero((self.lin >= 0) & (pol >= 0) &
                         (self.cul == self.rul_c) & (press > SET_PRESS) &
                         (self.pop > 2 * FOUND_MIN))[0]
        if not len(src):
            return
        Ls, cs = self.lin[src], self.cul[src]
        best = np.zeros(len(src))
        tgt = -np.ones(len(src), int)
        for k in range(8):
            j = W.nb[src, k]
            jj = np.maximum(j, 0)
            ok = (j >= 0) & (pol[jj] == pol[src]) & (self.lin[jj] >= 0) & \
                (self.cul[jj] != cs) & ((self.mcul[jj] < 0) |
                                        ((self.mcul[jj] == cs) &
                                         ~self.mcap[jj]))
            if not ok.any():
                continue
            ws = self.comp_w(Ls, jj)
            wM = self.comp_w(self.lin[jj], jj)
            room = self.Kf(Ls, jj) - SHARE_ALPHA * wM / ws * \
                self.pop[jj] * self.peat[self.cul[jj]] / self.peat[cs] - \
                np.where(self.mcul[jj] == cs, self.mpop[jj], 0)
            room = np.where(ok, room, 0)
            better = room > best
            best = np.where(better, room, best)
            tgt = np.where(better, j, tgt)
        go = best > FOUND_MIN
        src, tgt, best, Ls, cs = src[go], tgt[go], best[go], Ls[go], cs[go]
        if not len(src):
            return
        mv = np.minimum(SET_FRAC * self.pop[src], 0.5 * best)
        self.pop[src] -= mv
        new = self.mcul[tgt] < 0
        self.mcul[tgt[new]], self.mlin[tgt[new]] = cs[new], Ls[new]
        self.mcap[tgt] = False
        np.add.at(self.mpop, tgt, mv)
        self.count("settler_heads", float(mv.sum()))

    def settler_lineages(self, new):
        """Settlers entering a region (BLOCK x BLOCK cells) their people
        has never held found a daughter lineage: the parent's traits with a
        small mutation."""
        if not len(new) or self.settle_drift <= 0:
            return
        new = new[self.Lfounded[self.lin[new]] != self.year]
        for L, cells in self.by_lineage(new):
            seen = self.Pblk[self.Lpeople[L]]
            b = self.blk[cells]
            for bb in np.unique(b):
                if int(bb) in seen:
                    continue
                seen.add(int(bb))
                D = self.new_lineage(self.Lpeople[L], L, "settler",
                                     sd=self.settle_drift)
                self.lin[cells[b == bb]] = D

    def budding(self, press, adj, nadj, L, occ):
        """A crowded cell splits off one band toward its best empty
        neighbour. Expansive lineages split before they are full."""
        W, N = self.W, self.W.N
        c = self.Lpeople[L]
        thr = 0.45 - 0.35 * self.expn[L]
        can = occ & (press > thr) & (self.pop > 2 * FOUND_MIN)
        noise = self.rng.uniform(0.6, 1.4, (N, 8))
        # only cells that can bud are scored (elsewhere every score is 0)
        R = np.nonzero(can)[0]
        LR, cR = L[R], c[R]
        best = np.zeros(len(R))
        tgt = -np.ones(len(R), int)
        for k in range(8):
            j = W.nb[R, k]
            jj = np.maximum(j, 0)
            # scored only where a band could go: an empty neighbour with
            # room for one (elsewhere the score is 0)
            ii = np.nonzero((j >= 0) & (self.lin[jj] < 0))[0]
            if not len(ii):
                continue
            Kt = self.Kf(LR[ii], jj[ii])
            q = Kt > 2 * FOUND_MIN
            ii, Kt = ii[q], Kt[q]
            if not len(ii):
                continue
            ji, Li, Ri = jj[ii], LR[ii], R[ii]
            foreign = (nadj[ji] - adj[cR[ii], ji]) > 0
            s = np.sqrt(np.maximum(Kt, 0)) / W.edgecost[Ri, k] * \
                self.colon(ji, Li) * \
                (1 + RIV_BUD * (W.river[Ri] & W.river[ji])) * \
                (1 - 0.95 * self.hostile(Li) * foreign) * noise[Ri, k]
            b = s > best[ii]
            best[ii[b]] = s[b]
            tgt[ii[b]] = j[ii[b]]
        go = tgt >= 0
        src, tgt = R[go], tgt[go]
        Ls = L[src]
        band = np.maximum(FOUND_MIN, (0.2 + 0.25 * self.expn[Ls]) *
                          self.pop[src])
        band = np.minimum(np.maximum(band, 0.15 * self.Kf(Ls, tgt)),
                          0.5 * self.pop[src])
        self.pop[src] -= band
        return src, tgt, band, Ls

    def settle(self, src, tgt, band, bl):
        """Bands claim empty cells; the largest claimant wins, the rest
        go home."""
        if not len(src):
            return
        order = np.lexsort((-band, tgt))
        src, tgt, band, bl = src[order], tgt[order], band[order], bl[order]
        first = np.ones(len(tgt), bool)
        first[1:] = tgt[1:] != tgt[:-1]
        win = first & (self.lin[tgt] < 0)
        self.lin[tgt[win]] = bl[win]
        self.cul[tgt[win]] = self.Lpeople[bl[win]]
        self.pop[tgt[win]] = band[win]
        np.add.at(self.pop, src[~win], band[~win])

    def by_lineage(self, cells):
        """Group cell indices by lineage: yields (L, cells of L)."""
        if not len(cells):
            return
        Ls = self.lin[cells]
        o = np.argsort(Ls, kind="stable")
        cells, Ls = cells[o], Ls[o]
        u, start = np.unique(Ls, return_index=True)
        ends = list(start[1:]) + [len(cells)]
        for L, a, b in zip(u, start, ends):
            yield int(L), cells[a:b]

    def pioneers(self, press):
        """Bands leap past the frontier into empty land 2-6 cells away."""
        W = self.W
        eat = self.peat[np.maximum(self.cul, 0)]
        cand = np.nonzero((self.lin >= 0) & (self.pop * eat > 300))[0]
        for L, cells in self.by_lineage(cand):
            lam = 3.0 * self.expn[L] ** 2 * (1 + math.log10(1 + len(cells)))
            n = self.rng.poisson(lam)
            if not n:
                continue
            wts = self.pop[cells] * np.clip(press[cells], 0.05, 2)
            for s in self.rng.choice(cells, n, p=wts / wts.sum()):
                if W.river[s] and self.rng.random() < RIV_LEAP:
                    self.river_leap(L, s)
                    continue
                dr, dc = self.rng.integers(-6, 7, 2)
                if max(abs(dr), abs(dc)) < 2:
                    continue
                r2, c2 = W.row[s] + dr, (W.col[s] + dc) % NX
                if not (0 <= r2 < NY):
                    continue
                t = W.idx2[r2, c2]
                if t < 0 or self.lin[t] >= 0 or \
                        self.rng.random() > self.colon(t, L) or \
                        W.landmass[t] != W.landmass[s] or \
                        self.Kf(L, t) * self.peat[self.Lpeople[L]] < 200:
                    continue
                mv = min(120.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
                self.pop[s] -= mv
                self.lin[t], self.cul[t], self.pop[t] = L, self.Lpeople[L], mv

    def river_leap(self, L, s):
        """A band travels along the river network from s and settles an
        empty cell on the way."""
        W = self.W
        n = int(RIV_STEPS[0] + RIV_STEPS[1] * self.sail[L])
        downstream = self.rng.random() < 0.5
        x, path = s, []
        for _ in range(n):
            if downstream:
                x = int(W.down[x])
            else:
                ups = W.up[x]
                if not ups:
                    break
                q = W.Q[ups] + 1
                x = int(self.rng.choice(ups, p=q / q.sum()))
            if x < 0:
                break
            path.append(x)
        cand = [t for t in path[1:] if self.lin[t] < 0]
        if not cand:
            return
        t = int(self.rng.choice(cand))
        if self.rng.random() > self.colon(t, L) or \
                self.Kf(L, t) * self.peat[self.Lpeople[L]] < 200:
            return
        mv = min(120.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
        self.pop[s] -= mv
        self.lin[t], self.cul[t], self.pop[t] = L, self.Lpeople[L], mv

    def sail_km(self, L):
        """Typical voyage distance (km) of lineage L."""
        return SAIL_D0 + SAIL_D1 * self.sail[L] ** 1.5

    def voyages(self, press):
        """Sea colonization from crowded coasts to empty coasts. Targets
        are weighted by exp(-distance / sail_km), so sailing sets how far
        colonists usually go rather than whether they can go at all.
        A colony on a landmass new to its lineage founds a daughter
        lineage (founder effect)."""
        W = self.W
        eat = self.peat[np.maximum(self.cul, 0)]
        cand = np.nonzero((self.lin >= 0) & W.coastal & (self.pop * eat > 400) &
                          (press > 0.5))[0]

        def kept(cnd, L):
            """The coast cells cnd colonists of L could take, and their
            natives (food-equivalents)."""
            nat = self.pop[cnd] * eat[cnd] * (self.lin[cnd] >= 0)
            keep = (self.lin[cnd] < 0) | (
                (self.cul[cnd] != self.Lpeople[L]) &
                (self.cell_city[cnd] != cnd) & (nat < COL_THIN))
            return cnd[keep], nat[keep]

        for L, src in self.by_lineage(cand):
            D = self.sail_km(L)
            sea = self.expn[L]
            lam = 2.5 * sea * (0.1 + self.sail[L]) * \
                math.sqrt(len(src))
            n = self.rng.poisson(lam)
            picks = self.rng.choice(src, min(n, 6))
            if not len(picks):
                continue
            rad = 2 * math.sin(min(4 * D, 9000) / R_EARTH / 2)
            balls = [W.coast_idx[W.coast_tree.query_ball_point(W.xyz[s], rad)]
                     for s in picks]
            # capacity once per lineage, on every cell any of its voyages
            # could take: a landing only ever removes a cell from the
            # candidates (it becomes the lineage's people's), so the cells
            # kept now cover each later voyage's (so each voyage re-tests
            # only those, in the ball's order)
            kb = [kept(b, L)[0] for b in balls]
            allc = np.unique(np.concatenate(kb))
            Kall = self.Kf(L, allc) if len(allc) else None
            for s, ball in zip(picks, kb):
                cnd, nat = kept(ball, L)
                if not len(cnd):
                    continue
                wt = Kall[np.searchsorted(allc, cnd)]
                ok = wt * self.peat[self.Lpeople[L]] > 300
                cnd, wt, nat = cnd[ok], wt[ok], nat[ok]
                if not len(cnd):
                    continue
                wt = wt * np.exp(-gc_km(W.xyz, s, cnd) / D) * self.colon(cnd, L)
                wt = np.where(np.isfinite(wt), wt, 0.0)
                empty = (nat <= 0) & (wt > 0)
                if empty.any():
                    # settlers take empty coast where they can
                    wt = np.where(empty, wt, 0.0)
                else:
                    if self.rng.random() >= COL_OCC:
                        continue
                    wt = wt * np.exp(-nat / COL_THIN)
                if wt.sum() <= 0:
                    continue
                t = int(self.rng.choice(cnd, p=wt / wt.sum()))
                mv = min(200.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
                self.pop[s] -= mv
                lm = W.landmass[t]
                Lt = L
                sp = int(self.cell_pol[s])
                if sp >= 0 and self.cell_pol[t] != sp and \
                        lm != W.landmass[s]:
                    Lc = self.colony_lin.get((sp, int(lm)), -1)
                    if Lc < 0 or self.Lended[Lc] >= 0:
                        Lc = self.new_lineage(self.Lpeople[L], L, "colony",
                                              sd=self.drift)
                        self.Lcolony[Lc] = sp
                        self.Lseen[Lc] = set(self.Lseen.get(L, set())) | {lm}
                        self.colony_lin[(sp, int(lm))] = Lc
                        self.count("colony_state")
                    Lt = Lc
                if self.lin[t] >= 0:
                    fe_n = self.pop[t] * eat[t]
                    if fe_n < mv * self.peat[self.Lpeople[L]]:
                        # thin natives pushed out
                        self.count("colony_displace")
                        self.lin[t], self.cul[t], self.pop[t] = \
                            Lt, self.Lpeople[Lt], mv
                    else:
                        self.count("colony_minority")
                        self.add_minority([t], int(self.Lpeople[Lt]), Lt, mv)
                    continue
                if Lt == L and lm not in self.Lseen[L]:
                    self.Lseen[L].add(lm)
                    if W.landmass_area[lm] > 2e5:
                        Lt = self.new_lineage(self.Lpeople[L], L, "colony",
                                              sd=self.drift)
                        self.Lseen[Lt] = {lm}
                        self.log("voyage", f"{self.lname(L)} sailors land "
                                 f"on a new landmass at {self.place(t)} "
                                 f"({W.landmass_area[lm]/1e6:.1f}M km2), "
                                 f"founding {self.lname(Lt)}")
                self.lin[t], self.cul[t], self.pop[t] = \
                    Lt, self.Lpeople[Lt], mv

    def tidy(self):
        self.tidy_minorities()
        dead = (self.pop < 5) & (self.lin >= 0)
        self.pop[dead] = 0
        self.cul[dead] = -1
        self.lin[dead] = -1

    def tidy_minorities(self):
        """A minority that outnumbers the majority (in food terms) becomes
        the majority; a minority of the majority's own people merges into
        it; tiny minorities vanish."""
        m = self.mlin >= 0
        gone = m & ((self.mpop < 5) | (self.lin < 0) & (self.mpop < 20))
        merge = m & ~gone & (self.mcul == self.cul)
        self.pop[merge] += self.mpop[merge]
        swap = m & ~gone & ~merge & \
            (self.mpop * self.peat[np.maximum(self.mcul, 0)] >
             self.pop * self.peat[np.maximum(self.cul, 0)])
        s = np.nonzero(swap)[0]
        if len(s):
            c0, l0, p0 = self.cul[s].copy(), self.lin[s].copy(), \
                self.pop[s].copy()
            self.cul[s], self.lin[s], self.pop[s] = \
                self.mcul[s], self.mlin[s], self.mpop[s]
            self.mcul[s], self.mlin[s], self.mpop[s] = c0, l0, p0
            # the old majority stays on the land it farms
            self.mcap[s] = False
            if self.dom_on:
                ruled = self.cul[s] == self.rul_c[s]
                self.count("flip_to_ruler", int(ruled.sum()))
                self.count("flip_other", int((~ruled).sum()))
            for x, old in zip(s, c0):
                if x in self.cities and old >= 0:
                    # the city carries on under its new majority
                    self.cities[x]["culture"] = int(self.cul[x])
                    self.cities[x]["flips"] = \
                        self.cities[x].get("flips", 0) + 1
                    self.log("minority", f"{self.keys[self.cul[x]]} come to "
                             f"outnumber {self.keys[old]} in the city at "
                             f"{self.place(x)}")
        clear = gone | merge | (self.mcul < 0)
        self.mcul[clear], self.mlin[clear], self.mpop[clear] = -1, -1, 0
        self.mcap[clear] = False

    def add_minority(self, cells, c, L, amount, capped=False):
        """Settle `amount` (per cell) of people c, lineage L, as the
        minority of cells, unless another minority is already there.
        `capped`: a merchant quarter, held at MIN_CAP of the cell's K."""
        cells = np.asarray(cells, int)
        ok = (self.cul[cells] != c) & ((self.mcul[cells] < 0) |
                                       (self.mcul[cells] == c))
        cells, amount = cells[ok], np.broadcast_to(amount, ok.shape)[ok]
        new = self.mcul[cells] < 0
        self.mcul[cells], self.mlin[cells] = c, np.where(new, L,
                                                         self.mlin[cells])
        self.mcap[cells[new]] = capped
        self.mpop[cells] += amount

    def minorities(self):
        """Merchant quarters along lasting trade between peoples; expulsion
        of foreign minorities by intolerant, separatist rulers."""
        rng = self.rng
        for (x, y), t in self.ties.items():
            if t < 0.5:
                continue
            X, Y = self.polities[x], self.polities[y]
            if X["culture"] == Y["culture"]:
                continue
            for host, guest in ((X, Y), (Y, X)):
                if rng.random() < DT * 0.01 * t:
                    cap, gc = host["capital"], guest["culture"]
                    self.add_minority([cap], gc, guest["lin"],
                                      MIN_MERCHANT * t * self.pop[cap] *
                                      self.peat[host["culture"]] /
                                      self.peat[gc], capped=True)
        m = np.nonzero((self.mlin >= 0) & (self.cell_pol >= 0))[0]
        if not len(m):
            return
        pl, pc = self.ptab()[:2]
        L = pl[self.cell_pol[m]]
        foreign = (L >= 0) & (self.mcul[m] != pc[self.cell_pol[m]])
        pr = DT * MIN_EXPEL * self.hostile(L) * self.tolf(L, 1.0)
        out = m[foreign & (rng.random(len(m)) < pr)]
        self.mcul[out], self.mlin[out], self.mpop[out] = -1, -1, 0
