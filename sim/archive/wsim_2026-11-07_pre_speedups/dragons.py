"""Dragons."""
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


class DragonsMixin:
    D_ARR = ("dhome", "dage", "dally", "did", "dtol", "dviol", "dstr")

    def dragon_setup(self):
        """Neighbour lists for territories and spacing, and the year-0
        dragons: a random packing of homes DRAGON_SPACE_KM apart, of which
        DRAGON_START are held. Each dragon has its own tolerance, violence
        and strength."""
        W, rng = self.W, self.drng
        self.d_tree = cKDTree(W.xyz)

        def csr(km):
            nb = self.d_tree.query_ball_point(
                W.xyz, 2 * math.sin(km / (2 * R_EARTH)))
            ptr = np.zeros(W.N + 1, int)
            ptr[1:] = np.cumsum([len(x) for x in nb])
            return ptr, np.concatenate([np.asarray(x, int) for x in nb])
        self.d_tptr, self.d_tidx = csr(DRAGON_TERR_KM)
        self.d_sptr, self.d_sidx = csr(DRAGON_SPACE_KM)
        blocked = np.zeros(W.N, bool)
        homes = []
        for c in rng.permutation(W.N):
            if not blocked[c]:
                homes.append(c)
                blocked[self.d_sidx[self.d_sptr[c]:self.d_sptr[c + 1]]] = True
        homes = np.array(homes)
        homes = homes[rng.random(len(homes)) < DRAGON_START]
        n = len(homes)
        self.dhome = homes
        self.dage = rng.uniform(0, DRAGON_LIFE, n)
        self.dally = -np.ones(n, int)
        self.did = np.arange(n)
        lg = lambda p: math.log(p / (1 - p))
        self.dtol = dsig(lg(DRAGON_TOL_MEAN) +
                            DRAGON_TRAIT_SD * rng.standard_normal(n))
        self.dviol = dsig(lg(DRAGON_VIOL_MEAN) +
                             DRAGON_TRAIT_SD * rng.standard_normal(n))
        self.dstr = np.exp(DRAGON_STR_SD * rng.standard_normal(n))
        self.dhaz = np.zeros(W.N)
        self.dsmean = np.ones(W.N)
        self.dragon_hist = []
        for i in range(n):
            self.d_hist_add(i, None, homes[i], self.dtol[i], self.dviol[i],
                            self.dstr[i])

    def d_hist_add(self, i, born, home, tol, viol, strength, parent=None):
        self.dragon_hist.append(dict(
            id=i, born=born, parent=parent, home0=int(home),
            tolerance=round(float(tol), 3), violence=round(float(viol), 3),
            strength=round(float(strength), 3), ended=None, fate=None,
            ally=None, ally_people=None, ally_year=None, moves=0))

    def dseff(self, idx=slice(None)):
        """Strength as grown: x min(1, age / DRAGON_GROW), at least 0.05."""
        return self.dstr[idx] * np.clip(self.dage[idx] / DRAGON_GROW,
                                        0.05, 1)

    def d_keep(self, keep):
        for a in self.D_ARR:
            setattr(self, a, getattr(self, a)[keep])

    def terr(self, homes):
        """(cells, owner index) of the territories of homes."""
        a, b = self.d_tptr[homes], self.d_tptr[homes + 1]
        n = b - a
        own = np.repeat(np.arange(len(homes)), n)
        off = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
        return self.d_tidx[np.repeat(a, n) + off], own

    def ward(self, j):
        """Heads that ward off a dragon of strength 1 in cells j: fewer for
        big bodies, metal, and the organization of a state."""
        L = np.maximum(self.lin[j], 0)
        mil = 1 + METAL_MIL[0] * self.bronze[L] + \
            METAL_MIL[1] * self.iron[L] + METAL_MIL[2] * self.steel[L]
        org = 1 + WARD_STATE * self.admin[L] * (self.cell_pol[j] >= 0)
        body = self.psize[np.maximum(self.cul[j], 0)] ** WARD_SIZE_EXP
        wd = WARD0 / (body * mil * org)
        if self.phost.any():
            host = self.phost[np.maximum(self.cul[j], 0)] & (self.cul[j] >= 0)
            wd = np.where(host, np.inf, wd)
        return wd

    def dragon_pen(self, j):
        """Cut in the yearly growth rate of cells j from the wild dragons
        hunting there: DRAGON_PEN x hazard x g(n)."""
        haz = self.dhaz[j]
        out = np.zeros(len(j))
        k = haz > 0
        if k.any():
            jj = j[k]
            n = self.pop[jj] + self.mpop[jj]
            wd = self.ward(jj) * self.dsmean[jj]
            find = DRAGON_FIND
            find = DRAGON_FIND / self.peat[np.maximum(self.cul[jj], 0)]
            g = n / (n + find) / (1 + (n / wd) ** 4)
            out[k] = DRAGON_PEN * haz[k] * g
        return out

    def dragon_site(self, c0, warded, taken):
        """A free home for a dragon leaving c0: no other home within
        DRAGON_SPACE_KM, no warded cell in reach. -1 if none found."""
        W, rng = self.W, self.drng
        la1, lo1 = math.radians(W.lat[c0]), math.radians(W.lon[c0])
        for _ in range(12):
            dk = DRAGON_SPACE_KM + DRAGON_DISP_KM * rng.exponential()
            dl, th = dk / R_EARTH, rng.uniform(0, 2 * math.pi)
            la2 = math.asin(math.sin(la1) * math.cos(dl) +
                            math.cos(la1) * math.sin(dl) * math.cos(th))
            lo2 = lo1 + math.atan2(math.sin(th) * math.sin(dl) *
                                   math.cos(la1),
                                   math.cos(dl) - math.sin(la1) *
                                   math.sin(la2))
            c = int(self.d_tree.query(unit_xyz(math.degrees(lo2),
                                               math.degrees(la2)))[1])
            if taken[self.d_sidx[self.d_sptr[c]:self.d_sptr[c + 1]]].any():
                continue
            if warded[self.d_tidx[self.d_tptr[c]:self.d_tptr[c + 1]]].any():
                continue
            return c
        return -1

    def dragons(self):
        """Dragons hunt, age, breed, and are slain, driven off or taken as
        allies where people have grown too many for them."""
        W, rng, N = self.W, self.drng, self.W.N
        # ageing and other deaths (allied dragons are kept from the latter)
        self.dage += DT
        old = self.dage >= DRAGON_LIFE
        other = (rng.random(len(self.dage)) < DRAGON_MORT * DT) & \
            (self.dally < 0)
        self.count("dragon_died", int((old | other).sum()))
        for d in np.nonzero(old | other)[0]:
            h = self.dragon_hist[self.did[d]]
            h["ended"] = self.year
            h["fate"] = "old age" if old[d] else "died"
        self.d_keep(~old & ~other)
        # allies follow their state, or go wild when it falls
        for d in np.nonzero(self.dally >= 0)[0]:
            P = self.polities.get(int(self.dally[d]))
            if P is None or P["ended"] is not None:
                self.dally[d] = -1
                self.count("dragon_freed")
            elif self.cell_pol[self.dhome[d]] != P["id"]:
                self.dhome[d] = P["capital"]
                self.dragon_hist[self.did[d]]["moves"] += 1
        wild = np.nonzero(self.dally < 0)[0]
        # hunting: each wild dragon covering a cell adds its hunting weight
        # (strength x (0.5 + violence) x (1.3 - 0.6 tolerance)); the ward
        # size scales with the mean strength of the dragons there
        cw, own = self.terr(self.dhome[wild])
        se = self.dseff(wild)
        hw = se * (0.5 + self.dviol[wild]) * \
            (1.3 - 0.6 * self.dtol[wild])
        haz = np.bincount(cw, weights=hw[own], minlength=N)
        sw = np.bincount(cw, weights=(hw * se)[own],
                         minlength=N)
        smean = np.where(haz > 0, sw / np.maximum(haz, 1e-9), 1.0)
        if (self.dally >= 0).any():
            ca, _ = self.terr(self.dhome[self.dally >= 0])
            haz[ca] *= 1 - DRAGON_GUARD
        # the hazard and mean strength feed this tick's growth (grow)
        self.dhaz, self.dsmean = haz, smean
        occ = np.nonzero(self.lin >= 0)[0]
        wd = self.ward(occ) * smean[occ]
        n = self.pop[occ] + self.mpop[occ]
        warded = np.zeros(N, bool)
        warded[occ] = n >= wd
        self.d_warded = warded
        nest = warded.copy()
        nest[occ] |= n >= DRAGON_NEST * wd
        avoid = warded
        if DRAGON_SHUN > 0:
            avoid = warded.copy()
            avoid[occ] |= n >= DRAGON_SHUN * wd
        if self.phost.any():
            # the refuge is only where the hosts live: young and driven-off
            # dragons settle among host peoples or in empty land, never
            # within reach of anyone else's settled cells
            other = np.zeros(N, bool)
            other[occ] = ~self.phost[self.cul[occ]]
            nest = nest | other
            avoid = avoid | other
        # confrontations, one per warded cell per 1/CONFRONT years; a
        # stronger dragon counts a cell as warded only past its own ward
        base = np.zeros(N)
        base[occ] = n / self.ward(occ)
        wi = np.nonzero(self.dally < 0)[0]
        cells, own = self.terr(self.dhome[wi])
        sew = self.dseff(wi)
        nw = np.bincount(own, weights=base[cells] >= sew[own],
                         minlength=len(wi))
        hit = wi[rng.random(len(wi)) < 1 - np.exp(-CONFRONT * DT * nw)]
        keep = np.ones(len(self.dhome), bool)
        taken = np.zeros(N, bool)
        taken[self.dhome] = True
        for d in hit:
            tc, _ = self.terr(self.dhome[d:d + 1])
            sd_ = float(self.dseff(d))
            tc = tc[base[tc] >= sd_]
            c = int(tc[np.argmax(self.pop[tc])])
            L, pid = self.lin[c], int(self.cell_pol[c])
            s, v, dt = sd_, self.dviol[d], self.dtol[d]
            self.pop[c] *= 1 - min(0.5, DRAGON_FIGHT * s * (0.5 + v))
            joint = (self.tol[L] + dt) / 2
            h = self.dragon_hist[self.did[d]]
            who = self.pname(pid) if pid >= 0 else self.lname(L)
            if pid >= 0 and joint >= DRAGON_TOL and rng.random() < \
                    (joint - DRAGON_TOL) / (1 - DRAGON_TOL):
                self.dally[d] = pid
                taken[self.dhome[d]] = False
                self.dhome[d] = c
                taken[c] = True
                h["ally"], h["ally_year"] = pid, self.year
                h["ally_people"] = self.keys[self.cul[c]]
                self.count("dragon_ally")
                self.first(("dragon_ally", self.cul[c]), "dragon",
                           f"{who} takes a dragon as ally at {self.place(c)}")
            elif rng.random() < min(0.95, (DRAGON_SLAY0 + DRAGON_SLAY1 *
                                           self.viol[L]) *
                                    (0.5 + v) / s):
                # a violent dragon stands and fights; a strong one survives
                keep[d] = False
                h["ended"], h["fate"] = self.year, "slain"
                self.count("dragon_slain")
                self.first(("dragon_slain", self.cul[c]), "dragon",
                           f"{who} slays a dragon at {self.place(c)}")
            else:
                taken[self.dhome[d]] = False
                site = self.dragon_site(self.dhome[d], avoid, taken)
                if site < 0:
                    keep[d] = False
                    self.count("dragon_lost")
                    h["ended"], h["fate"] = self.year, "driven off, no land"
                else:
                    self.dhome[d] = site
                    taken[site] = True
                    h["moves"] += 1
                    self.count("dragon_pushed")
        self.d_keep(keep)
        if self.phost.any():
            self.host_alliances(taken)
        # breeding into free sites; young take after their parent
        ad = np.nonzero((self.dage >= DRAGON_ADULT) &
                        (rng.random(len(self.dage)) < DRAGON_BREED * DT))[0]
        new, par = [], []
        for d in ad:
            site = self.dragon_site(self.dhome[d], nest, taken)
            if site >= 0:
                taken[site] = True
                new.append(site)
                par.append(d)
        if new:
            m, par = len(new), np.array(par)
            z = rng.standard_normal((3, m)) * DRAGON_DRIFT
            lt = lambda p: np.log(p / (1 - p))
            tol = dsig(lt(self.dtol[par]) + z[0])
            viol = dsig(lt(self.dviol[par]) + z[1])
            st = self.dstr[par] * np.exp(z[2])
            ids = np.arange(len(self.dragon_hist), len(self.dragon_hist) + m)
            for i in range(m):
                self.d_hist_add(int(ids[i]), self.year, new[i], tol[i],
                                viol[i], st[i],
                                parent=int(self.did[par[i]]))
            for a, x in (("dhome", new), ("dage", np.zeros(m)),
                         ("dally", -np.ones(m, int)), ("did", ids),
                         ("dtol", tol), ("dviol", viol), ("dstr", st)):
                setattr(self, a, np.concatenate([getattr(self, a), x]))
            self.count("dragon_born", m)
        self.d_by_pid = {}
        for d in np.nonzero(self.dally >= 0)[0]:
            pid = int(self.dally[d])
            self.d_by_pid[pid] = self.d_by_pid.get(pid, 0) + \
                float(self.dseff(d))

    def host_alliances(self, taken):
        """Wild dragons among dragon-host peoples inside a state may be
        taken as allies (no fight)."""
        rng = self.drng
        hostc = (self.lin >= 0) & (self.cell_pol >= 0) & \
            self.phost[np.maximum(self.cul, 0)]
        wi = np.nonzero(self.dally < 0)[0]
        if not len(wi) or not hostc.any():
            return
        cells, own = self.terr(self.dhome[wi])
        nh = np.bincount(own, weights=hostc[cells], minlength=len(wi))
        for d in wi[(nh > 0) & (rng.random(len(wi)) < CONFRONT * DT)]:
            tc, _ = self.terr(self.dhome[d:d + 1])
            tc = tc[hostc[tc]]
            c = int(tc[np.argmax(self.pop[tc])])
            L, pid = self.lin[c], int(self.cell_pol[c])
            joint = (self.tol[L] + self.dtol[d]) / 2
            if joint >= DRAGON_TOL and rng.random() < \
                    (joint - DRAGON_TOL) / (1 - DRAGON_TOL):
                h = self.dragon_hist[self.did[d]]
                self.dally[d] = pid
                taken[self.dhome[d]] = False
                self.dhome[d] = c
                taken[c] = True
                h["ally"], h["ally_year"] = pid, self.year
                h["ally_people"] = self.keys[self.cul[c]]
                self.count("dragon_ally")
                self.first(("dragon_ally", self.cul[c]), "dragon",
                           f"{self.pname(pid)} takes a dragon as ally at "
                           f"{self.place(c)}")

    def dragon_record(self):
        al = self.dally >= 0
        occ = self.lin >= 0
        fd = np.zeros(self.W.N)
        fd[occ] = self.pop[occ] * self.peat[self.cul[occ]] / \
            self.W.area[occ]
        wl = ~al
        st = dict(dragons_wild=int(wl.sum()), dragons_allied=int(al.sum()),
                  dragon_kills=round(float(self.dragon_kills.sum())),
                  dragon_land=round(float((self.dhaz > 0).mean()), 3),
                  warded_cells=int(self.d_warded.sum()),
                  near_empty=round(float((fd < 0.02).mean()), 3),
                  dragon_tol=round(float(self.dtol[wl].mean()), 3)
                  if wl.any() else None,
                  dragon_viol=round(float(self.dviol[wl].mean()), 3)
                  if wl.any() else None,
                  dragon_str=round(float(self.dstr[wl].mean()), 3)
                  if wl.any() else None)
        apc = np.zeros(self.nP, int)
        for d in np.nonzero(al)[0]:
            P = self.polities.get(int(self.dally[d]))
            if P:
                apc[P["culture"]] += 1
        for i, k in enumerate(self.keys):
            st[f"dragon_kills_{k}"] = round(float(self.dragon_kills[i]))
            st[f"dragons_allied_{k}"] = int(apc[i])
        return st
