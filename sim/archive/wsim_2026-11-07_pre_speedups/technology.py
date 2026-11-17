"""Technology."""
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
        # contact between lineages
        M = np.zeros((nA, nA))
        la, lb = self.lin[W.E1], self.lin[W.E2]
        m = (la >= 0) & (lb >= 0) & (la != lb)
        np.add.at(M, (amap[la[m]], amap[lb[m]]), 1)
        Mb = M.copy()
        pl = np.full(self.next_pid, -1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                pl[pid] = p["lin"]
        rl = np.where(self.cell_pol >= 0, pl[np.maximum(self.cell_pol, 0)],
                      -1)
        m = occ & (rl >= 0) & (rl != self.lin)
        m &= amap[np.maximum(rl, 0)] >= 0
        np.add.at(M, (amap[self.lin[m]], amap[rl[m]]), 0.5)
        Mr = np.zeros((nA, nA))
        np.add.at(Mr, (amap[self.lin[m]], amap[rl[m]]), 0.5)
        Mr = Mr + Mr.T
        # a minority lives among its hosts
        m = occ & (self.mlin >= 0) & (self.mlin != self.lin)
        m &= amap[np.maximum(self.mlin, 0)] >= 0
        np.add.at(M, (amap[self.lin[m]], amap[self.mlin[m]]), 2.0)
        np.add.at(Mb, (amap[self.lin[m]], amap[self.mlin[m]]), 2.0)
        M = M + M.T
        Mb = Mb + Mb.T
        for (x, y), t in self.ties.items():
            a, b = pl[x], pl[y]
            if a >= 0 and b >= 0 and a != b and amap[a] >= 0 and amap[b] >= 0:
                M[amap[a], amap[b]] += 30 * t
                M[amap[b], amap[a]] += 30 * t
        C = np.clip(M / 60, 0, 1)
        Cb = np.clip(Mb / 60, 0, 1)
        Ct = np.clip((M - Mb) / 60, 0, 1)
        if "rule_weak" in self.on:
            # rule apart from trade, for the movement of customs
            Cr = np.clip(Mr / 60, 0, 1)
            Ctt = np.clip((M - Mb - Mr) / 60, 0, 1)
        inn = self.innov[A]
        # closed, cohesive societies borrow less from outsiders
        openness = 1 - COST_COH * self.coh[A]

        def diffuse(v, rate):
            gap = np.clip(v[None, :] - v[:, None], 0, None)
            return rate * (C * gap).max(1) * (0.3 + inn) * openness

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
        sup = True
        kb, ki = (self.known[A, 0], self.known[A, 1]) if sup else \
            (self.bronze[A], self.iron[A])
        cap = np.where(~kb, 1.2, np.where(~ki, 2.0, 3.5))
        if sup:
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
        if sup:
            self.metal[A] = np.maximum(self.metal[A], 0)
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
        if sup:
            rt2 = rt2 - DT * DECAY_ADMIN * (1 - ins)
        self.roadt[A] = np.clip(rt2, 0, 1)
        # settled specialists make prized goods
        cr = self.craft[A]
        cr2 = cr + DT * (CRAFT_INV * F * self.crafts[A] *
                         (0.5 + self.pati[A]) *
                         np.sqrt(np.clip(nc / 3, 0, 1)) * (1 - cr) +
                         diffuse(cr, CRAFT_BORROW))
        if sup:
            cr2 = cr2 - DT * CRAFT_DECAY * idle * cr2
        self.craft[A] = np.clip(cr2, 0, 1)
        self.domesticate(A, occ, Lpop, inn * F, diffuse)
        self.guarded(A, C, nc)
        # ore access: own land near ores, or close contact with a holder
        has = {}
        for nm, d in (("cu", W.d_cu), ("sn", W.d_sn), ("fe", W.d_fe)):
            near = occ & (d < 120) & \
                (self.pop * self.peat[np.maximum(self.cul, 0)] > 1000)
            h = (np.bincount(self.lin[near], minlength=nL) > 0)[A]
            has[nm] = h | ((C * h[None, :]).max(1) > 0.4)
            if nm in ("cu", "sn"):
                has[nm] = has[nm] | self.ore_by_trade(near, nL)[A]
        self.ore_has[A] = np.stack([has["cu"], has["sn"], has["fe"]], 1)
        # a stage needs the lineage's own metallurgy plus the ore in hand
        if sup:
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
        else:
            br = self.bronze[A] | ((self.metal[A] >= 1.0) & has["cu"] &
                                   has["sn"])
            fe = self.iron[A] | (br & (self.metal[A] >= 1.8) & has["fe"])
            st = self.steel[A] | (fe & (self.metal[A] >= 2.6) & (nc >= 6))
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
            Wm = C * np.sqrt(LpopF[A])[None, :]
            pa = self.Lpeople[A]
            same = pa[:, None] == pa[None, :]
            xf = ACC_CROSS if "acc_cross" in self.on else 1.0
            xf = xf * (1 - self.Lsup[A])[:, None]
            xp = np.where(same, 1.0, xf)
            # the pull's strength falls with the foreign share of
            # contact, not only its direction
            xs = (Wm * xp).sum(1) / np.maximum(Wm.sum(1), 1e-12)
            Wm = Wm * xp
            Wm = Wm * (1 + self.craft[A])[None, :]
            if "proselytism" in self.on:
                Wm = Wm * (0.5 + self.pros[A])[None, :]
            np.fill_diagonal(Wm, 0)
            tot = Wm.sum(1)
            has_c = tot > 0
            nT = len(TRAITS)
            if "mission" in self.on:
                # proselytizers push their neighbours; trade and rule carry
                # customs both ways; like cultures move each other most
                has_c[:] = False
                S = self.sim_matrix(A)
                pj = self.pros[A]
                Sb = S + MIS_REACH * pj[None, :] * (1 - S)
                if "rule_weak" in self.on:
                    Wt = MIS_TRADE * Ctt + MIS_RULE * Cr
                else:
                    Wt = MIS_TRADE * Ct
                Wx = MIS_BORDER * Cb * pj[None, :] * Sb + \
                    Wt * self.tol[A][:, None] * S
                Wx = Wx * xp
                np.fill_diagonal(Wx, 0)
                T = np.hstack([self.LT[A], self.LX[A]])
                norm = np.maximum(1, (Cb + Ct).sum(1) - np.diag(Cb + Ct))
                # superiority itself moves only toward kin's
                Ws = Wx * same
                sA = self.Lsup[A]
                self.Lsup[A] = np.clip(sA + DT * (Ws @ sA - Ws.sum(1) *
                                                  sA) / norm, 0.01, 0.99)
                dT = DT * (Wx @ T - Wx.sum(1)[:, None] * T) / norm[:, None]
                if "conformity" in self.on:
                    dT = dT * (1.5 - self.conf[A])[:, None]
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                self.LT[A] += dT[:, :nT]
                self.LX[A] += dT[:, nT:]
                churn[A] += np.abs(dT).sum(1)
            if has_c.any():
                T = np.hstack([self.LT[A], self.LX[A]])
                target = (Wm @ T) / np.maximum(tot, 1e-9)[:, None]
                open_ = self.tol[A]
                if "proselytism" in self.on:
                    open_ = open_ + PROS_PUSH * (Wm @ self.pros[A]) / \
                        np.maximum(tot, 1e-9)
                rate = DT * ACC * open_ * np.minimum(1, C.sum(1))
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
        for k in range(nh):
            got = (new[:, k] >= 0.5) & (lv[:, k] < 0.5)
            for L in A[got][:1]:
                self.first(("domesticate", k), "tech",
                           f"{self.lname(L)} domesticates {self.h_name[k]}"
                           f" (hearth at {self.place(self.h_cell[k])})")

    def guarded(self, A, C, nc):
        """Guarded techniques: invented by skilled rulers of large states,
        leaking slowly to contacts."""
        rng = self.rng
        G = self.guard[A]
        if G.any():
            hw = (1.5 - self.coh[A]) * (1.5 - self.conf[A])
            P = DT * GUARD_LEAK * C * hw[None, :]
            for g in np.nonzero(G.any(0))[0]:
                h = G[:, g]
                pr = 1 - np.prod(1 - P[:, h], axis=1)
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
