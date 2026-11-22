"""Several peoples in a cell (WP7 C, `shared_cells`) and flight
(WP7 D, `displacement`), on the presence table of WP7 B.

Rows 0..N-1 of the table hold each cell's plurality people and rows
N..2N-1 the second; under `shared_cells` further peoples get rows from 2N
on ("extra rows"). New rows are queued (`rows_put`) and written at the
next phase boundary (`rows_flush`, from `acct_mark` and `tidy`), so the
table is never reallocated while a routine holds a view of it."""
import numpy as np

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class SharedMixin:

    # ---- the table -----------------------------------------------------

    def xrows(self):
        """Live extra rows (from 2N on)."""
        n2 = 2 * self.W.N
        return np.nonzero(self.rp[n2:] >= 0)[0] + n2

    def xsum(self, w):
        """Per cell, the sum of w (one value per extra row) over the
        cell's extra rows; w = None sums heads."""
        x = self.xrows()
        if w is None:
            w = self.rh[x]
        return np.bincount(self.rc[x], weights=w, minlength=self.W.N), x

    def rows_find(self, cells, people):
        """Row of people[k] in cells[k], or -1: the main row, the minority
        row or an extra row (pending rows are not looked at)."""
        N = self.W.N
        cells, people = np.asarray(cells, int), np.asarray(people, int)
        r = np.where(self.rp[cells] == people, cells, -1)
        r = np.where((r < 0) & (self.rp[N + cells] == people), N + cells, r)
        x = self.xrows()
        if len(x) and (r < 0).any():
            key = self.rc[x].astype(np.int64) * self.nP + self.rp[x]
            o = np.argsort(key)
            key, x = key[o], x[o]
            q = cells.astype(np.int64) * self.nP + people
            i = np.minimum(np.searchsorted(key, q), len(key) - 1)
            hit = (key[i] == q) & (r < 0)
            r = np.where(hit, x[i], r)
        return r

    def rows_put(self, cells, people, lin, heads, capped=False):
        """Add heads of people (lineage lin) to cells: to that people's
        row if it has one, else the empty main or minority row, else (under
        `shared_cells`) a new extra row, queued until the next phase
        boundary. Returns the heads that found no place (without
        `shared_cells`, a cell whose two rows hold other peoples)."""
        N = self.W.N
        cells = np.atleast_1d(np.asarray(cells, int))
        k = len(cells)
        people = np.broadcast_to(np.asarray(people, int), (k,)).copy()
        lin = np.broadcast_to(np.asarray(lin, int), (k,)).copy()
        heads = np.broadcast_to(np.asarray(heads, float), (k,)).copy()
        left = np.zeros(k)
        r = self.rows_find(cells, people)
        has = r >= 0
        np.add.at(self.rh, r[has], heads[has])
        # (cell, people) -> row taken in this call, "q" (queued) or None
        # (no place)
        put = {}
        for i in np.nonzero(~has)[0]:
            c, p = int(cells[i]), int(people[i])
            if (c, p) not in put:
                if self.rp[c] < 0:
                    put[(c, p)] = c
                elif self.rp[N + c] < 0:
                    put[(c, p)] = N + c
                else:
                    put[(c, p)] = "q" if self.sh_on else None
                rr = put[(c, p)]
                if isinstance(rr, (int, np.integer)):
                    self.rp[rr], self.rl[rr], self.rh[rr] = p, lin[i], 0.0
                    self.rm[rr] = capped and rr >= N
            rr = put[(c, p)]
            if rr is None:
                left[i] = heads[i]
            elif rr == "q":
                self.rows_pending.append((c, p, int(lin[i]),
                                          float(heads[i]), capped))
            else:
                self.rh[rr] += heads[i]
        return left

    def rows_flush(self):
        """Write queued rows to the table: one new row per (cell, people),
        or onto that people's row if one has appeared since."""
        if not self.rows_pending:
            return
        q = {}
        for c, p, L, h, cap in self.rows_pending:
            if (c, p) in q:
                q[(c, p)][1] += h
            else:
                q[(c, p)] = [L, h, cap]
        self.rows_pending = []
        cells = np.array([c for c, _ in q], int)
        people = np.array([p for _, p in q], int)
        r = self.rows_find(cells, people)
        vals = list(q.values())
        new = []
        for i, (L, h, cap) in enumerate(vals):
            if r[i] >= 0:
                self.rh[r[i]] += h
            else:
                new.append(i)
        if not new:
            return
        new = np.array(new)
        self.rc = np.concatenate([self.rc, cells[new]])
        self.rp = np.concatenate([self.rp, people[new]])
        self.rl = np.concatenate([self.rl, [vals[i][0] for i in new]])
        self.rh = np.concatenate([self.rh, [vals[i][1] for i in new]])
        self.rm = np.concatenate([self.rm, [vals[i][2] for i in new]])
        self.rows_bind()

    def rows_compact(self):
        """Drop empty extra rows (the table is reallocated: views rebound)."""
        n2 = 2 * self.W.N
        keep = np.concatenate([np.arange(n2),
                               np.nonzero(self.rp[n2:] >= 0)[0] + n2])
        if len(keep) == len(self.rp):
            return
        for a in ("rc", "rp", "rl", "rh", "rm"):
            setattr(self, a, getattr(self, a)[keep])
        self.rows_bind()

    def rows_scale(self, cells, keep, cause, viol=None):
        """Extra rows in cells lose (1 - keep) of their heads (keep: one
        value per cell, or a scalar): the damage the minority row takes at
        the same site. viol: the attacker's violence, for flight."""
        x = self.xrows()
        if not len(x):
            return
        cells = np.atleast_1d(np.asarray(cells, int))
        f = np.ones(self.W.N)
        f[cells] = keep
        x = x[f[self.rc[x]] < 1]
        if len(x):
            b = self.rh[x].copy()
            self.rh[x] *= f[self.rc[x]]
            if viol is not None:
                # one value per cell (or a scalar): to each row's cell
                v = np.zeros(self.W.N)
                v[cells] = viol
                viol = v[self.rc[x]]
            self.lost_rows(x, b - self.rh[x], viol, cause)

    # ---- competition (`shared_cells`) ----------------------------------

    def overlap(self, La, Lb, ha, hb):
        """Niche overlap of lineages La and Lb (U 2026-11-18: what lets
        peoples share land): 1 - 0.5 x the difference in herding (ha, hb:
        whether each lives by herding there) - 0.5 x the distance between
        their biome affinities (half the summed absolute difference of the
        normalised affinity vectors)."""
        a = self.Laff[La] / self.Laff[La].sum(-1, keepdims=True)
        b = self.Laff[Lb] / self.Laff[Lb].sum(-1, keepdims=True)
        tv = 0.5 * np.abs(a - b).sum(-1)
        return np.clip(1 - 0.5 * np.abs(ha - hb) - 0.5 * tv, 0, 1)

    def row_terms(self, r):
        """For rows r: capacity K, competitive weight w, food per head e,
        food-equivalents f and whether they herd there."""
        L, c = self.rl[r], self.rc[r]
        K, Kc, Kh = self.Kf(L, c, parts=True)
        herd = np.zeros(len(r)) if Kh is None else (Kh > Kc).astype(float)
        e = self.peat[self.rp[r]]
        return K, self.comp_w(L, c), e, self.rh[r] * e, herd

    def rows_pairs(self, r):
        """Every ordered pair (i, j), i != j, of rows r that share a cell,
        as positions into r."""
        o = np.argsort(self.rc[r], kind="stable")
        rc = self.rc[r][o]
        I, J = [], []
        for d in range(1, len(o)):
            same = rc[d:] == rc[:-d]
            if not same.any():
                break
            a, b = o[:-d][same], o[d:][same]
            I += [a, b]
            J += [b, a]
        if not I:
            return np.zeros(0, int), np.zeros(0, int)
        return np.concatenate(I), np.concatenate(J)

    def grow_shared(self, occ, k):
        """`shared_cells`: every row other than a cell's main one grows
        logistically toward its own capacity less what the others eat,
        weighted: K_i - sum_j alpha_ij (w_j / w_i) f_j / e_i, alpha_ij =
        SHARE_ALPHA x niche overlap (WP7 design note, section 3). The
        main row's capacity k (cells occ) loses the same sum, returned.
        For two rows with overlap 1 this is `dominion`'s rule."""
        N = self.W.N
        o = np.nonzero(self.rp[N:] >= 0)[0] + N
        if not len(o):
            return k
        cells = np.unique(self.rc[o])
        r = np.concatenate([cells[self.rp[cells] >= 0], o])
        K, w, e, f, herd = self.row_terms(r)
        I, J = self.rows_pairs(r)
        a = SHARE_ALPHA * self.overlap(self.rl[r[I]], self.rl[r[J]],
                                       herd[I], herd[J])
        press = np.zeros(len(r))          # food the others take from i
        np.add.at(press, I, a * w[J] / w[I] * f[J])
        main = r < N
        # the main row: subtract from grow's k
        pos = np.full(N, -1)
        pos[occ] = np.arange(len(occ))
        km = pos[r[main]]
        ok = km >= 0
        k = k.copy()
        k[km[ok]] = np.maximum(k[km[ok]] - press[main][ok] / e[main][ok],
                               1e-3)
        # the others grow here
        oo = ~main
        ro = r[oo]
        Lo = self.rl[ro]
        kk = np.maximum(K[oo] - press[oo] / e[oo], 1e-3)
        kk = np.where(self.rm[ro], np.maximum(MIN_CAP * K[oo], 1e-3), kk)
        p = self.rh[ro]
        rr = R_SCALE * self.Lr[Lo]
        if "tech_costs" in self.on:
            rr = rr * (1 - COST_INN * self.innov[Lo])   # WP14 B
        am = 0.6 + 0.4 * self.agri[Lo]
        p0 = logistic(p, kk, self.rcap(rr * am))
        rr = rr - self.dragon_pen(self.rc[ro])
        self.rh[ro] = logistic(p, kk, self.rcap(rr * am))
        self.dead("hunger", ro, np.maximum(p - p0, 0), rows=True)
        self.forgone(ro, np.maximum(p0 - self.rh[ro], 0), rows=True)
        return k

    # ---- movement into held cells (`shared_cells`) --------------------

    def infiltrate(self):
        """Crowded rows send a share of their people into the
        neighbouring cell held by another people where they would have
        the most room (WP7 design note, section 4): weight room x
        sqrt(K) / edge cost x (1 - INF_RES x (1 - holders' tolerance) x
        min(1, holders' weight / movers' weight)). Settlers of a state's
        ruling people meet no resistance inside their state."""
        W, N = self.W, self.W.N
        r = np.nonzero(self.rp >= 0)[0]
        r = r[self.rh[r] > 2 * FOUND_MIN]
        if not len(r):
            return
        L, c, p = self.rl[r], self.rc[r], self.rp[r]
        # crowding as `migrate` reads it: against the share of capacity
        # the people choose to fill
        K = np.maximum(self.Kf(L, c) * self.pref(L, c), 1e-3)
        press = self.rh[r] / K
        thr = 0.9 - 0.6 * self.expn[L]
        go = press > thr
        r, L, c, p, press, thr = r[go], L[go], c[go], p[go], press[go], \
            thr[go]
        if not len(r):
            return
        ws = self.comp_w(L, c)
        # what the rows of each cell weigh, by food-equivalents
        allr = np.nonzero(self.rp >= 0)[0]
        wf = np.bincount(self.rc[allr], minlength=N,
                         weights=self.comp_w(self.rl[allr], self.rc[allr]) *
                         self.rh[allr] * self.peat[self.rp[allr]])
        best = np.zeros(len(r))
        tgt = -np.ones(len(r), int)
        for kk in range(8):
            j = W.nb[c, kk]
            jj = np.maximum(j, 0)
            hold = self.cul[jj]
            ok = (j >= 0) & (hold >= 0) & (hold != p)
            if not ok.any():
                continue
            Lh = np.maximum(self.lin[jj], 0)
            Kt = self.Kf(L, jj)
            mine = self.rows_find(jj, p)
            have = np.where(mine >= 0, self.rh[np.maximum(mine, 0)], 0)
            # others' food, less one's own, weighted against the movers
            mf = have * self.peat[p] * ws
            herd_m = np.zeros(len(r))
            ov = self.overlap(L, Lh, herd_m, self.herding[jj].astype(float))
            room = Kt - SHARE_ALPHA * ov * (wf[jj] - mf) / ws / \
                self.peat[p] - have
            wh = self.comp_w(Lh, jj)
            res = INF_RES * (1 - self.tol[Lh]) * np.minimum(1, wh / ws)
            ruled = (self.cell_pol[jj] >= 0) & \
                (self.cell_pol[jj] == self.cell_pol[c]) & \
                (p == self.rul_c[jj])
            res = np.where(ruled, 0, res)
            wgt = np.clip(room, 0, None) * np.sqrt(np.maximum(Kt, 0)) / \
                W.edgecost[c, kk] * (1 - res)
            wgt = np.where(ok & (room > FOUND_MIN), wgt, 0)
            better = wgt > best
            best = np.where(better, wgt, best)
            tgt = np.where(better, j, tgt)
        go = tgt >= 0
        if not go.any():
            return
        r, L, p, tgt, press, thr = r[go], L[go], p[go], tgt[go], \
            press[go], thr[go]
        # movers take at most half the room their own people has there
        mine = self.rows_find(tgt, p)
        have = np.where(mine >= 0, self.rh[np.maximum(mine, 0)], 0)
        Kt = self.Kf(L, tgt)
        room_t = np.clip(Kt - have, 0, None)
        frac = INF_FRAC * self.expn[L] * np.clip(press - thr, 0, 1.5)
        mv = np.minimum(frac * self.rh[r], 0.5 * room_t)
        m = mv > 1
        r, L, p, tgt, mv = r[m], L[m], p[m], tgt[m], mv[m]
        if not len(r):
            return
        np.subtract.at(self.rh, r, mv)
        left = self.rows_put(tgt, p, L, mv)
        np.add.at(self.rh, r, left)       # no place: they stay
        self.count("infiltrate_heads", float((mv - left).sum()))

    # ---- raids inside a cell (`shared_cells`) -------------------------

    def inner_raids(self):
        """Peoples sharing a cell raid each other (U 2026-11-18), by the
        rule of raids between neighbouring cells: chance DT x 0.02 x
        violence x (0.5 + crowding) x (1 + hostility), x 0.2 inside a
        state; damage 0.12 x violence x sqrt(size ratio) / defence x the
        victims' hardiness, at most 0.6; raiders lose 1% x hardiness."""
        N = self.W.N
        o = np.nonzero(self.rp[N:] >= 0)[0] + N
        if not len(o):
            return
        cells = np.unique(self.rc[o])
        r = np.concatenate([cells[self.rp[cells] >= 0], o])
        I, J = self.rows_pairs(r)
        a, b = r[I], r[J]
        diff = self.rp[a] != self.rp[b]
        a, b = a[diff], b[diff]
        if not len(a):
            return
        La, c = self.rl[a], self.rc[a]
        pa = self.rh[a] / np.maximum(self.Kf(La, c), 1e-3)
        p = DT * 0.02 * self.viol[La] * (0.5 + pa) * \
            (1 + self.hostile(La)) * np.where(self.cell_pol[c] >= 0, 0.2, 1)
        hit = self.R("raid").random(len(a)) < np.clip(p, 0, 0.9)
        a, b, La, c = a[hit], b[hit], La[hit], c[hit]
        if not len(a):
            return
        self.count("raid_inner", int(len(a)))
        rel = np.sqrt(self.psize[self.rp[a]] / self.psize[self.rp[b]])
        dmg = 0.12 * self.viol[La] * rel / self.W.defence[c] * \
            self.phardy[self.rp[b]]
        loss = np.clip(dmg, 0, 0.6)
        bb, first = np.unique(b, return_index=True)
        before = self.rh[bb].copy()
        self.rh[bb] *= 1 - loss[first]
        self.dead("raid", bb, before - self.rh[bb], rows=True)
        aa, first = np.unique(a, return_index=True)
        before = self.rh[aa].copy()
        self.rh[aa] *= 1 - 0.01 * self.phardy[self.rp[aa]]
        self.dead("raid", aa, before - self.rh[aa], rows=True)
        self.raided[c] = 1

    # ---- order within a cell ------------------------------------------

    def rows_sort(self):
        """`shared_cells`: in each cell the plurality people (by
        food-equivalents) takes the main row and the next the minority
        row; the rest keep extra rows. Rows of one people merge; rows
        under 5 heads, or under 20 in a cell with no main people, vanish.
        A city follows its new plurality, as `tidy_minorities` did."""
        N = self.W.N
        r = np.nonzero(self.rp >= 0)[0]
        small = (r >= N) & ((self.rh[r] < 5) |
                            ((self.rp[self.rc[r]] < 0) & (self.rh[r] < 20)))
        g = r[small]
        self.dead("dwindled", g, self.rh[g], rows=True)
        self.rp[g], self.rl[g], self.rh[g] = -1, -1, 0
        self.rm[g] = False
        r = r[~small]
        # merge rows of one people in one cell into the first
        key = self.rc[r].astype(np.int64) * self.nP + self.rp[r]
        u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        if (cnt > 1).any():
            first = np.full(len(u), -1)
            order = np.argsort(r)                      # main rows first
            for i in order:
                if first[inv[i]] < 0:
                    first[inv[i]] = r[i]
                else:
                    self.rh[first[inv[i]]] += self.rh[r[i]]
                    self.rp[r[i]], self.rl[r[i]], self.rh[r[i]] = -1, -1, 0
            r = r[self.rp[r] >= 0]
        # cells to order: more than one row, or a row off the main one
        n = np.bincount(self.rc[r], minlength=N)
        todo = (n > 1)
        todo[self.rc[r[r >= N]]] = True
        rs = r[todo[self.rc[r]]]
        if not len(rs):
            return
        fe = self.rh[rs] * self.peat[self.rp[rs]]
        o = np.lexsort((-fe, self.rc[rs]))
        src = rs[o]
        cells = np.unique(self.rc[src])
        # places: main, minority, then the cell's extra rows
        x = np.nonzero((np.arange(len(self.rp)) >= 2 * N))[0]
        x = x[todo[self.rc[x]]]
        pc = np.concatenate([cells, cells, self.rc[x]])
        pr = np.concatenate([cells, N + cells, x])
        rank = np.concatenate([np.zeros(len(cells)), np.ones(len(cells)),
                               2 + np.arange(len(x)) / max(len(x), 1)])
        po = np.lexsort((rank, pc))
        pr, pc = pr[po], pc[po]
        # the k-th row of a cell goes to its k-th place
        start = np.searchsorted(pc, self.rc[src])
        kth = np.arange(len(src)) - np.searchsorted(self.rc[src],
                                                    self.rc[src])
        dst = pr[start + kth]
        old_main = self.rp[cells].copy()
        vals = [a[src].copy() for a in (self.rp, self.rl, self.rh, self.rm)]
        for a in (self.rp, self.rl):
            a[pr] = -1
        self.rh[pr], self.rm[pr] = 0, False
        for a, v in zip((self.rp, self.rl, self.rh, self.rm), vals):
            a[dst] = v
        self.rm[cells] = False
        ch = cells[(self.rp[cells] != old_main) & (old_main >= 0)]
        if self.dom_on and len(ch):
            ruled = self.rp[ch] == self.rul_c[ch]
            self.count("flip_to_ruler", int(ruled.sum()))
            self.count("flip_other", int((~ruled).sum()))
        for c in ch:
            c = int(c)
            if c in self.cities:
                old = int(old_main[cells == c][0])
                self.cities[c]["culture"] = int(self.cul[c])
                self.cities[c]["flips"] = self.cities[c].get("flips", 0) + 1
                self.log("minority", f"{self.keys[self.cul[c]]} come to "
                         f"outnumber {self.keys[old]} in the city at "
                         f"{self.place(c)}", cell=c,
                         peoples=[self.keys[self.cul[c]], self.keys[old]])

    # ---- flight (`displacement`) ---------------------------------------

    def flee(self, cells, people, lin, heads, viol, cause):
        """`displacement` (WP7 D): of `heads` removed from cells (people,
        lineage per entry), a share 1 - viol (the attacker's violence; U
        2026-11-18) flees up to FLEE_RINGS cells, to the cell with most
        room among 16 drawn on the same landmass where its people already
        live or the land is empty. Those who find no room, and the rest,
        die (recorded by the caller as `cause`). Returns the heads that
        fled, per entry."""
        W = self.W
        cells = np.atleast_1d(np.asarray(cells, int))
        k = len(cells)
        people = np.broadcast_to(np.asarray(people, int), (k,))
        lin = np.broadcast_to(np.asarray(lin, int), (k,))
        heads = np.broadcast_to(np.asarray(heads, float), (k,))
        viol = np.broadcast_to(np.asarray(viol, float), (k,))
        want = heads * np.clip(1 - viol, 0, 1)
        out = np.zeros(k)
        m = (want > 1) & (people >= 0) & (lin >= 0)
        if not m.any():
            return out
        i = np.nonzero(m)[0]
        src, P, L = cells[i], people[i], lin[i]
        rng, R = self.R("migrate"), FLEE_RINGS
        dr = rng.integers(-R, R + 1, (len(i), 16))
        dc = rng.integers(-R, R + 1, (len(i), 16))
        r2 = W.row[src][:, None] + dr
        ok = (r2 >= 0) & (r2 < NY)
        t = W.idx2[np.clip(r2, 0, NY - 1), (W.col[src][:, None] + dc) % NX]
        ok &= (t >= 0)
        t = np.where(ok, t, src[:, None])
        ok &= (t != src[:, None]) & (W.landmass[t] == W.landmass[src][:, None])
        Pt = P[:, None] * np.ones((1, 16), int)
        Lt = L[:, None] * np.ones((1, 16), int)
        row = self.rows_find(t.ravel(), Pt.ravel()).reshape(t.shape)
        empty = self.cul[t] < 0
        ok &= (row >= 0) | empty
        Kt = self.Kf(Lt, t)
        have = np.where(row >= 0, self.rh[np.maximum(row, 0)], 0)
        room = np.where(ok, (Kt - have) * np.where(empty, self.colon(t, Lt),
                                                   1), 0)
        b = np.argmax(room, 1)
        tgt = t[np.arange(len(i)), b]
        rb = np.clip(room[np.arange(len(i)), b], 0, None)
        mv = np.minimum(want[i], rb)
        g = mv > 1
        if not g.any():
            return out
        left = self.rows_put(tgt[g], P[g], L[g], mv[g])
        out[i[g]] = mv[g] - left
        self.count("refugees", float(out.sum()))
        # refugees.csv (WP10 stage A, records only): where each group went
        self.flee_rows.extend(zip(
            [self.year] * int(g.sum()), src[g].tolist(), tgt[g].tolist(),
            P[g].tolist(), np.round(out[i[g]], 1).tolist(),
            empty[np.arange(len(i)), b][g].astype(int).tolist(),
            [cause] * int(g.sum())))
        return out

    def lost_rows(self, rows, lost, viol, cause):
        """Heads `lost` (already taken off) from table rows: under
        `displacement`, the share 1 - viol flees (`flee`); the rest are
        recorded as deaths by `cause`."""
        rows = np.atleast_1d(np.asarray(rows, int))
        lost = np.broadcast_to(np.asarray(lost, float), rows.shape)
        fled = 0
        if self.dp_on and viol is not None:
            fled = self.flee(self.rc[rows], self.rp[rows], self.rl[rows],
                             lost, viol, cause)
        self.dead(cause, rows, lost - fled, rows=True)
