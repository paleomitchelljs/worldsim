"""Technology."""
import numpy as np
from scipy import sparse

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class TechnologyMixin:
    def technology(self):
        """Per-lineage invention, plus borrowing from the most advanced
        lineage each one touches (borders, trade, rule)."""
        W, nL = self.W, self.nL
        occ = self.lin >= 0
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        self.Lpeak[:nL] = np.maximum(self.Lpeak[:nL], Lpop)
        dead = (Lpop <= 0) & (self.Lended[:nL] < 0) & (self.Lpeak[:nL] > 0)
        self.Lended[:nL][dead] = self.year
        A = np.nonzero(Lpop > 0)[0]
        if not len(A):
            return
        nA = len(A)
        amap = -np.ones(nL, int)
        amap[A] = np.arange(nA)
        ncity = np.zeros(nL)
        for cell in self.cities:
            if self.lin[cell] >= 0:
                ncity[self.lin[cell]] += 1
        coastal = np.bincount(self.lin[occ], weights=(self.pop * W.coastal)
                              [occ], minlength=nL) / np.maximum(Lpop, 1)
        waterside = np.bincount(self.lin[occ], weights=(self.pop * W.water)
                                [occ], minlength=nL) / np.maximum(Lpop, 1)
        # contact between lineages, both ways: shared borders (1 per edge),
        # rule (0.5 per ruled cell), minorities (2 per cell) and trade
        # between their states (30 x tie). Only ~0.5% of pairs are in
        # contact late in a run, so contact is kept as a list of pairs
        # (crow -> ccol, row-major) rather than an nA x nA matrix.
        parts = []      # (i, j, weight, kind): kind 0 border, 1 rule,
                        # 2 minority, 3 trade; each counts both ways

        def add(i, j, w, kind):
            parts.append((i, j, np.broadcast_to(w, i.shape), kind))

        la, lb = self.lin[W.E1], self.lin[W.E2]
        m = (la >= 0) & (lb >= 0) & (la != lb)
        add(amap[la[m]], amap[lb[m]], 1.0, 0)
        pl = self.ptab()[0]
        rl = np.where(self.cell_pol >= 0, pl[np.maximum(self.cell_pol, 0)],
                      -1)
        m = occ & (rl >= 0) & (rl != self.lin)
        m &= amap[np.maximum(rl, 0)] >= 0
        add(amap[self.lin[m]], amap[rl[m]], 0.5, 1)
        # a minority lives among its hosts
        m = occ & (self.mlin >= 0) & (self.mlin != self.lin)
        m &= amap[np.maximum(self.mlin, 0)] >= 0
        add(amap[self.lin[m]], amap[self.mlin[m]], 2.0, 2)
        tr = [(amap[pl[x]], amap[pl[y]], 30 * t)
              for (x, y), t in self.ties.items()
              if pl[x] >= 0 and pl[y] >= 0 and pl[x] != pl[y] and
              amap[pl[x]] >= 0 and amap[pl[y]] >= 0]
        tr = np.array(tr, float).reshape(-1, 3)
        add(tr[:, 0].astype(int), tr[:, 1].astype(int), tr[:, 2], 3)
        I = np.concatenate([x for i, j, _, _ in parts for x in (i, j)])
        J = np.concatenate([x for i, j, _, _ in parts for x in (j, i)])
        V = np.concatenate([w for _, _, w, _ in parts for _ in (0, 1)])
        kind = np.concatenate([np.full(2 * len(i), q)
                               for i, _, _, q in parts])
        key, inv = np.unique(I.astype(np.int64) * nA + J, return_inverse=True)
        crow, ccol = key // nA, key % nA
        Mk = np.array([np.bincount(inv, weights=V * (kind == q),
                                   minlength=len(key)) for q in range(4)])
        cval = np.clip(Mk.sum(0) / 60, 0, 1)            # all contact
        cb = np.clip((Mk[0] + Mk[2]) / 60, 0, 1)         # borders, minorities
        ct = np.clip((Mk[1] + Mk[3]) / 60, 0, 1)         # rule and trade
        # rule apart from trade, for the movement of customs (`rule_weak`)
        crr = np.clip(Mk[1] / 60, 0, 1)
        ctt = np.clip(Mk[3] / 60, 0, 1)
        inn = self.innov[A]
        # closed, cohesive societies borrow less from outsiders
        openness = 1 - COST_COH * self.coh[A]

        def rows(w):
            """Row sums of the pair weights w."""
            return np.bincount(crow, weights=w, minlength=nA)

        def pmat(w):
            """The pair weights w as a sparse nA x nA matrix."""
            return sparse.csr_matrix((w, (crow, ccol)), shape=(nA, nA))

        # borrowing: the largest contact x gap among the pairs in contact
        def diffuse(v, rate):
            g = np.zeros(nA)
            np.maximum.at(g, crow, cval * np.clip(v[ccol] - v[crow], 0, None))
            return rate * g * (0.3 + inn) * openness

        LpopF = Lpop * self.peat[np.maximum(self.Lpeople[:nL], 0)]
        g = 0.5 + 0.5 * np.clip(np.log10(1 + LpopF[A]) / 6, 0, 1)
        F = 1.0
        # big, connected, varied realms invent faster
        F = self.scale_factor(A, LpopF, occ)
        g = F
        ag, mt, sl, ad = (self.agri[A], self.metal[A], self.sail[A],
                          self.admin[A])
        nc = ncity[A]
        ag2 = ag + DT * (0.0009 * inn * g * (1 - ag) + diffuse(ag, 0.004))
        mt2 = mt + DT * (0.0005 * F * inn ** 2 * (ag > 0.5) *
                         (1 + np.log1p(nc) / 3) + diffuse(mt, 0.0008))
        # fishing grows with innovation where there is water to fish
        fs = self.fishing[A]
        fs2 = fs + DT * (0.001 * F * inn * (waterside[A] + 0.05) *
                         (1 - fs) +
                         diffuse(fs, 0.002))
        self.fishing[A] = np.clip(fs2, 0, 1)
        sea = inn * (0.5 + self.fishing[A])
        sl2 = sl + DT * (0.0012 * F * sea * (coastal[A] + 0.1) *
                         (1 - sl) + diffuse(sl, 0.001))
        ex = self.exposure(occ, Lpop, A) if "experience" in self.on else None
        Fad = F * (1 + EXP_ADMIN * ex["s"]) if ex is not None else F
        stA = self.state[A]
        if self.rt:
            # the ruler's competence, not his people's, drives the offices
            stA = stA.copy()
            for p in self.polities.values():
                if p["ended"] is None and amap[p["lin"]] >= 0 and \
                        "x" in p.get("ruler", {}):
                    stA[amap[p["lin"]]] = self.eff(p, "state")
        ad2 = ad + DT * (0.0008 * Fad * stA * (1 - ad) *
                         np.sqrt(np.clip(nc / 5, 0, 1)) + diffuse(ad, 0.002))
        kb, ki = self.known[A, 0], self.known[A, 1]
        cap = np.where(~kb, 1.2, np.where(~ki, 2.0, 3.5))
        # outside any state, offices and workshops lapse
        ruled = np.bincount(self.lin[occ], weights=(self.pop * (
            self.cell_pol >= 0))[occ], minlength=nL)[A]
        idle = 1 - ruled / np.maximum(Lpop[A], 1)
        ad2 = ad2 - DT * DECAY_ADMIN * idle
        mt2 = mt2 - DT * DECAY_METAL * idle
        # farming, fishing and sailing lapse where they are not used
        Kocc = np.maximum(self.Kf(self.lin[occ], np.nonzero(occ)[0]),
                          1e-3)
        unused = self.herding[occ] | (self.pop[occ] < AGRI_THIN * Kocc)
        nofarm = (np.bincount(self.lin[occ], weights=self.pop[occ] *
                              unused, minlength=nL) /
                  np.maximum(Lpop, 1))[A]
        ag2 = ag2 - DT * DECAY_AGRI * nofarm * np.maximum(ag2 - 0.25, 0)
        sl2 = sl2 - DT * DECAY_SAIL * (1 - coastal[A]) * \
            np.maximum(sl2 - SAIL_START, 0)
        fs2 = self.fishing[A]
        self.fishing[A] = fs2 - DT * DECAY_FISH * \
            (1 - waterside[A]) * np.maximum(fs2 - FISH_START, 0)
        self.agri[A] = np.clip(ag2, 0, 1)
        self.metal[A] = np.minimum(mt2, cap)
        self.metal[A] = np.maximum(self.metal[A], 0)
        self.lver += 1                      # agri, metal: ltab()
        ad2 = np.clip(ad2, 0, 1)
        self.sail[A] = sl2
        if not self.ca_on:
            self.admin[A] = ad2
        # road building is learned inside states
        ins = np.bincount(self.lin[occ], weights=(self.pop * (
            self.cell_pol >= 0))[occ], minlength=nL)[A] / \
            np.maximum(Lpop[A], 1)
        rt = self.roadt[A]
        rt2 = rt + DT * (ROADT_INV * F * inn * ins * (1 - rt) +
                         diffuse(rt, ROADT_BORROW))
        rt2 = rt2 - DT * DECAY_ADMIN * (1 - ins)
        self.roadt[A] = np.clip(rt2, 0, 1)
        # settled specialists make prized goods
        cr = self.craft[A]
        cr2 = cr + DT * (CRAFT_INV * F * self.crafts[A] *
                         (0.5 + self.pati[A]) *
                         np.sqrt(np.clip(nc / 3, 0, 1)) * (1 - cr) +
                         diffuse(cr, CRAFT_BORROW))
        cr2 = cr2 - DT * CRAFT_DECAY * idle * cr2
        self.craft[A] = np.clip(cr2, 0, 1)
        self.domesticate(A, occ, Lpop, inn * F, diffuse)
        self.guarded(A, crow, ccol, cval, nc)
        # ore access: own land near ores, or close contact with a holder
        has = {}
        for nm, d in (("cu", W.d_cu), ("sn", W.d_sn), ("fe", W.d_fe)):
            near = occ & (d < 120) & \
                (self.pop * self.peat[np.maximum(self.cul, 0)] > 1000)
            h = (np.bincount(self.lin[near], minlength=nL) > 0)[A]
            close = np.zeros(nA, bool)
            close[crow[(cval > 0.4) & h[ccol]]] = True
            has[nm] = h | close
            if nm in ("cu", "sn"):
                has[nm] = has[nm] | self.ore_by_trade(near, nL)[A]
        self.ore_has[A] = np.stack([has["cu"], has["sn"], has["fe"]], 1)
        # a stage needs the lineage's own metallurgy plus the ore in hand
        # ...and stays in use only while the ore (and, for steel, the
        # cities) remain; knowledge is kept, use lapses after a grace
        mtA = self.metal[A]
        okb = (mtA >= 1.0) & has["cu"] & has["sn"]
        oki = (mtA >= 1.8) & has["fe"] & (self.known[A, 0] | okb)
        oks = oki & (mtA >= 2.6) & (nc >= 6)
        stages = []
        for s, (arr, ok) in enumerate(((self.bronze, okb),
                                       (self.iron, oki),
                                       (self.steel, oks))):
            self.known[A, s] |= ok
            self.lack[A, s] = np.where(ok, 0, self.lack[A, s] + 1)
            stages.append(ok | (arr[A] & (self.lack[A, s] <= SUPPLY_GRACE)))
        br, fe, st = stages
        lost = self.bronze[A] & ~br & (Lpop[A] > 3e5)
        for L in A[lost]:
            self.log("tech", f"{self.lname(L)} can no longer get tin and "
                     "copper: bronze goes out of use")
        for arr, new, nm in ((self.bronze, br, "cast bronze"),
                             (self.iron, fe, "work iron"),
                             (self.steel, st, "forge steel")):
            for L in A[new & ~arr[A]]:
                c = self.Lpeople[L]
                self.first((nm, c), "tech", f"{self.keys[c]} {nm} "
                           f"(first: {self.lname(L)})")
            arr[A] = new
        if "acculturation" in self.on:
            # customs drift toward those of contacts, weighted by contact and
            # prestige (sqrt population), faster in tolerant lineages
            sk = [TI[t] for t in SKILLS]
            churn = np.zeros(nL)
            # (all weights below are per pair in contact, i <- j)
            pa = self.Lpeople[A]
            same = pa[crow] == pa[ccol]
            xf = ACC_CROSS if "acc_cross" in self.on else 1.0
            xf = xf * (1 - self.Lsup[A])
            xp = np.where(same, 1.0, xf[crow])
            mission = "mission" in self.on
            has_c = np.zeros(nA, bool)
            if not mission:
                # (the contact-weighted pull, which `mission` replaces)
                wm = cval * np.sqrt(LpopF[A])[ccol]
                # the pull's strength falls with the foreign share of
                # contact, not only its direction
                xs = rows(wm * xp) / np.maximum(rows(wm), 1e-12)
                wm = wm * xp * (1 + self.craft[A])[ccol]
                if "proselytism" in self.on:
                    wm = wm * (0.5 + self.pros[A])[ccol]
                tot = rows(wm)
                has_c = tot > 0
            nT = len(TRAITS)
            if mission:
                # proselytizers push their neighbours; trade and rule carry
                # customs both ways; like cultures move each other most
                S = self.sim_pairs(A[crow], A[ccol])
                pj = self.pros[A][ccol]
                Sb = S + MIS_REACH * pj * (1 - S)
                if "rule_weak" in self.on:
                    wt = MIS_TRADE * ctt + MIS_RULE * crr
                else:
                    wt = MIS_TRADE * ct
                wx = (MIS_BORDER * cb * pj * Sb +
                      wt * self.tol[A][crow] * S) * xp
                T = np.hstack([self.LT[A], self.LX[A]])
                norm = np.maximum(1, rows(cb + ct))
                # superiority itself moves only toward kin's
                ws = wx * same
                sA = self.Lsup[A]
                self.Lsup[A] = np.clip(sA + DT * (rows(ws * sA[ccol]) -
                                                  rows(ws) * sA) / norm,
                                       0.01, 0.99)
                dT = DT * (pmat(wx) @ T - rows(wx)[:, None] * T) / \
                    norm[:, None]
                if "conformity" in self.on:
                    dT = dT * (1.5 - self.conf[A])[:, None]
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                self.LT[A] += dT[:, :nT]
                self.LX[A] += dT[:, nT:]
                churn[A] += np.abs(dT).sum(1)
            if has_c.any():
                T = np.hstack([self.LT[A], self.LX[A]])
                target = (pmat(wm) @ T) / np.maximum(tot, 1e-9)[:, None]
                open_ = self.tol[A]
                if "proselytism" in self.on:
                    open_ = open_ + PROS_PUSH * rows(wm * self.pros[A][ccol]) \
                        / np.maximum(tot, 1e-9)
                rate = DT * ACC * open_ * np.minimum(1, rows(cval))
                rate = rate * xs
                if "conformity" in self.on:
                    rate = rate * (1.5 - self.conf[A])
                dT = rate[:, None] * (target - T)
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                self.LT[A[has_c]] += dT[has_c, :nT]
                self.LX[A[has_c]] += dT[has_c, nT:]
            # under foreign rule, customs move fast toward the ruler's
            fr = occ & (rl >= 0) & (self.cul != self.Lpeople[np.maximum(rl, 0)])
            if self.cc_on:
                # conquest replaces the elite instead (city_elite_to)
                fr = fr & False
            if "acc_cross" in self.on:
                key = np.where(fr, self.Lpeople[np.maximum(rl, 0)] * 1000 +
                               np.maximum(self.cul, 0), -1)
                new = fr & (key != self.rule_key)
                self.rule_since[new] = self.year
                self.rule_key = key
            if fr.any():
                sub, ru, w = self.lin[fr], rl[fr], self.pop[fr]
                if "acc_cross" in self.on:
                    g = (self.year - self.rule_since[fr]) / (
                        GEN_LEN * self.plife[self.cul[fr]])
                    w = w * (ACC_RULE0 + (1 - ACC_RULE0) /
                             (1 + np.exp(-(g - ACC_GENS) / 0.5)))
                w = w * (1 - self.Lsup[sub])
                wsum = np.bincount(sub, weights=w, minlength=nL)
                tg = np.zeros((nL, nT + len(XTRAITS)))
                np.add.at(tg, sub, w[:, None] *
                          np.hstack([self.LT[ru], self.LX[ru]]))
                ok = wsum[A] > 0
                Ak = A[ok]
                tgt = tg[Ak] / wsum[Ak][:, None]
                rc = DT * ACC_CONQ * wsum[Ak] / np.maximum(Lpop[Ak], 1)
                if "conformity" in self.on:
                    rc = rc * (1.5 - self.conf[Ak])
                dT = rc[:, None] * (tgt - np.hstack([self.LT[Ak],
                                                     self.LX[Ak]]))
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                self.LT[Ak] += dT[:, :nT]
                self.LX[Ak] += dT[:, nT:]
                churn[Ak] += np.abs(dT).sum(1)
            if "mission" in self.on:
                a = np.minimum(1.0, DT / (MIS_MEM * self.memf(A)))
                self.Lchurn[A] += a * (100 * churn[A] / DT - self.Lchurn[A])
        if ex is not None:
            self.experience(A, **ex)
        for nm, v, lv in (("adopt farming", self.agri, 0.5),
                          ("adopt open-sea sailing", self.sail, 0.4),
                          ("adopt net and weir fishing", self.fishing, 0.5),
                          ("adopt bureaucracy", self.admin, 0.5)):
            for L in A[v[A] >= lv]:
                c = self.Lpeople[L]
                self.first((nm, c), "tech", f"{self.keys[c]} {nm} "
                           f"(first: {self.lname(L)})")

    def scale_factor(self, A, LpopF, occ):
        """Invention multiplier F of living lineages A (see SCALE_*)."""
        W, nL = self.W, self.nL
        pool = LpopF[:nL].astype(float).copy()
        fe = self.pop * self.peat[np.maximum(self.cul, 0)]
        m = occ & (self.cell_pol >= 0)
        spop = np.bincount(self.cell_pol[m], weights=fe[m],
                           minlength=self.next_pid)
        nb = len(BIOMES)
        sb = np.zeros((self.next_pid, nb))
        np.add.at(sb, (self.cell_pol[m], W.biome[m]), 1)
        lb = np.zeros((nL, nb))
        np.add.at(lb, (self.lin[occ], W.biome[occ]), 1)
        D = (lb / np.maximum(lb.sum(1, keepdims=True), 1) >= 0.05).sum(1)
        D = D.astype(float)
        for pid, p in self.polities.items():
            L = p["lin"]
            if p["ended"] is not None or L >= nL:
                continue
            # the state's people (its ruling lineage's own among them)
            pool[L] = max(pool[L], spop[pid])
            sh = sb[pid] / max(sb[pid].sum(), 1)
            D[L] = max(D[L], float((sh >= 0.05).sum()) +
                       p.get("n_kinds", 0))
        for (x, y), t in self.ties.items():
            for a, b in ((x, y), (y, x)):
                P = self.polities.get(a)
                if P is not None and P["ended"] is None and P["lin"] < nL:
                    pool[P["lin"]] += SCALE_TIE * t * spop[b]
        for L in A:
            D[L] += len(self.Lseen.get(int(L), ())) - 1
        F = np.clip((np.maximum(pool[A], 0) / SCALE_P0) ** SCALE_EXP,
                    SCALE_MIN, SCALE_MAX)
        return F * (1 + SCALE_DIV * np.maximum(D[A] - 1, 0))

    def domesticate(self, A, occ, Lpop, inn, diffuse):
        """Crop and animal packages: developed near their hearths,
        borrowed elsewhere, most readily into their own biome."""
        W, nL = self.W, self.nL
        nh = len(self.h_cell)
        lv = self.domlv[A]
        inv = np.zeros_like(lv)
        for k in range(nh):
            c = self.h_near[k]
            c = c[(self.lin[c] >= 0) & (self.pop[c] * self.peat[
                np.maximum(self.cul[c], 0)] > 300)]
            if len(c):
                near = np.zeros(nL, bool)
                near[self.lin[c]] = True
                inv[:, k] = DOM_INV * inn * near[A]
        bs = np.zeros((nL, len(BIOMES)))
        np.add.at(bs, (self.lin[occ], W.biome[occ]), self.pop[occ])
        bs = bs[A] / np.maximum(Lpop[A], 1)[:, None]
        suit = 0.3 + 0.7 * bs[:, self.h_biome]
        bor = np.stack([diffuse(lv[:, k], DOM_BORROW) for k in range(nh)], 1)
        new = np.clip(lv + DT * (inv * (1 - lv) + bor * suit), 0, 1)
        self.domlv[A] = new
        self.lver += 1                      # ltab()
        for k in range(nh):
            got = (new[:, k] >= 0.5) & (lv[:, k] < 0.5)
            for L in A[got][:1]:
                self.first(("domesticate", k), "tech",
                           f"{self.lname(L)} domesticates {self.h_name[k]}"
                           f" (hearth at {self.place(self.h_cell[k])})")

    def guarded(self, A, crow, ccol, cval, nc):
        """Guarded techniques: invented by skilled rulers of large states,
        leaking slowly to contacts (pairs crow <- ccol at contact cval)."""
        rng = self.R("tech")
        G = self.guard[A]
        if G.any():
            hw = (1.5 - self.coh[A]) * (1.5 - self.conf[A])
            pv = DT * GUARD_LEAK * cval * hw[ccol]
            for g in np.nonzero(G.any(0))[0]:
                h = G[:, g]
                # chance a lineage is reached by none of its holder contacts
                miss = np.ones(len(A))
                sel = h[ccol]
                np.multiply.at(miss, crow[sel], 1 - pv[sel])
                pr = 1 - miss
                got = ~h & (rng.random(len(A)) < pr)
                self.guard[A[got], g] = True
                for L in A[got][:1]:
                    self.log("craft", f"the secret of {GUARD_NAMES[g]} "
                             f"reaches {self.lname(L)}")
        if self.n_guard >= GUARD_MAX:
            return
        for pid, p in self.polities.items():
            L = p["lin"]
            if p["ended"] is not None or len(p["cities"]) < GUARD_CITIES or \
                    self.craft[L] < GUARD_CRAFT:
                continue
            if rng.random() < DT * GUARD_P:
                g = self.n_guard
                self.n_guard += 1
                self.guard[L, g] = True
                self.log("craft", f"{self.pname(pid)} ({self.lname(L)}) "
                         f"masters {GUARD_NAMES[g]} and guards the secret")
                if self.n_guard >= GUARD_MAX:
                    return
