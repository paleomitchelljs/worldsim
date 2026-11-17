"""Lineages, drift, similarity, experience."""
import math
import numpy as np

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class CultureMixin:
    def drift_trait(self, x, sd, rng, n=None):
        """Trait(s) x after drift sd at a lineage split."""
        y = x + rng.normal(0, DRIFT_UNIT * sd, n)
        y = np.where(y < 0.01, 0.02 - y, y)
        y = np.where(y > 0.99, 1.98 - y, y)
        y = np.clip(y, 0.01, 0.99)
        return float(y) if n is None else y

    def new_lineage(self, people, parent, how, sd=0.0):
        """A new lineage: a founding group of a people, or a daughter of an
        existing lineage (secession, settlers, colony). Intrinsic traits
        (growth rate, biome affinity) and technology pass on unchanged;
        cultural traits mutate by `sd` on the logit scale."""
        if self.nL >= MAXL:
            return parent if parent >= 0 else 0
        L = self.nL
        self.nL += 1
        rng = self.rng
        sd = sd * self.pvar[people]       # a people's own variability
        if "conformity" in self.on and sd > 0:
            # faithful transmission: conformist parents pass customs on
            # nearly unchanged
            c0 = self.conf[parent] if parent >= 0 else \
                self.pX[people, XTRAITS.index("conformity")]
            sd = sd * (1.5 - c0)
        if parent >= 0:
            self.LX[L] = self.LX[parent]
            self.Lpart[L] = self.Lpart[parent]
            self.Lsup[L] = self.Lsup[parent]
        else:
            self.LX[L] = self.pX[people]
            self.Lpart[L] = PART0
            self.Lsup[L] = self.psup[people]
        if sd > 0:
            self.Lsup[L] = self.drift_trait(self.Lsup[L], sd, self.srng)
        if hasattr(self, "Lpref"):
            self.Lpref[L] = self.Lpref[parent] if parent >= 0 else \
                self.ppref[people]
            if sd > 0:
                e = self.prng.normal(0, sd, self.Lpref.shape[1])
                e = e - sd * sd / 2
                self.Lpref[L] = self.Lpref[L] * np.exp(e)
        if sd > 0 and "rulers" in self.on:
            self.Lpart[L] = self.drift_trait(self.Lpart[L], sd, self.prng)
        if sd > 0:
            self.LX[L] = self.drift_trait(self.LX[L], sd, self.xrng, len(XTRAITS))
        if parent >= 0:
            T, r, aff = self.LT[parent], self.Lr[parent], self.Laff[parent]
            for a in ("agri", "metal", "sail", "fishing", "admin", "bronze", "iron",
                      "steel", "known", "lack", "craft", "domlv", "guard",
                      "Lwarm", "Lhardm", "Ltradem", "Lexp", "Lchurn",
                      "Lraidm", "Lapp", "roadt"):
                getattr(self, a)[L] = getattr(self, a)[parent]
        else:
            T, r, aff = self.pT[people], self.pr[people], self.paff[people]
            self.agri[L] = 0.25
            self.fishing[L] = FISH_START
        if sd > 0:
            T = self.drift_trait(T, sd, rng, len(T))
        self.LT[L], self.Lr[L], self.Laff[L] = T, r, aff
        self.Lbest[L] = aff.max()
        if parent < 0:
            self.sail[L] = SAIL_START
        self.Lpeople[L] = people
        self.Lparent[L] = parent
        self.Lfounded[L] = self.year
        self.Lhow.append(how)
        base = self.colors[people].astype(float)
        self.Lcol[L] = np.clip(base * rng.uniform(0.6, 1.2) +
                               rng.uniform(-30, 30, 3), 15, 245)
        self.Lseen[L] = set(self.Lseen.get(parent, set()))
        return L

    def similarity(self, a, b):
        """1 for identical lineages; within a people it falls with trait
        distance; between peoples it is capped low (SIM_OTHER)."""
        if a == b:
            return 1.0
        key = (a, b) if a < b else (b, a)
        s = self._sim.get(key)
        if s is None:
            dv = self.LT[a] - self.LT[b]
            d = float(np.linalg.norm(dv) + 0.3 *
                      np.linalg.norm(np.log(self.Laff[a]) -
                                     np.log(self.Laff[b])))
            if self.Lpeople[a] == self.Lpeople[b]:
                s = math.exp(-d / SIM_SAME_SCALE)
            else:
                s = SIM_OTHER[0] + SIM_OTHER[1] * math.exp(-d / 0.8)
            self._sim[key] = s
        return s

    def sim_pairs(self, a, b):
        """similarity() of the lineage pairs (a[k], b[k])."""
        d = np.linalg.norm(self.LT[a] - self.LT[b], axis=1) + 0.3 * \
            np.linalg.norm(np.log(self.Laff[a]) - np.log(self.Laff[b]),
                           axis=1)
        same = self.Lpeople[a] == self.Lpeople[b]
        return np.where(same, np.exp(-d / SIM_SAME_SCALE),
                        SIM_OTHER[0] + SIM_OTHER[1] * np.exp(-d / 0.8))

    def accept(self, a, b, level):
        """Both sides must tolerate `level` x their dissimilarity."""
        need, width = level
        need = need * (1 - self.similarity(a, b))
        return sigmoid((self.tol[a] - need) / width) * \
            sigmoid((self.tol[b] - need) / width)

    def hostile(self, L):
        """What used to be separation's hostile side: separation itself, or
        (1 - tolerance) with `separation` on."""
        return 1 - self.tol[L]

    def tolf(self, L, k):
        """The separate tolerance term (1 - k x tolerance) of raids, war,
        clearance and expulsion; 1 with `separation` on, where hostility
        is already 1 - tolerance."""
        return 1.0

    def pref(self, L, j):
        """Share of capacity lineages L choose to fill in cells j
        (`separation`); 1 in cities and with the switch off."""
        p = 1 - SEP_DENS * self.sep[L] ** 2
        return np.where(self.cell_city[j] >= 0, 1.0, p)

    def exposure(self, occ, Lpop, A):
        """Per living lineage: share of its people in states at war, the
        trade volume of the states they live in, and their hardship."""
        nL = self.nL
        atwar = np.zeros(self.next_pid, bool)
        vol = np.zeros(self.next_pid)
        for k in self.wars:
            atwar[list(k)] = True
        for w in self.wars.values():
            for q in w.get("joined", ()):
                if q < len(atwar):
                    atwar[q] = True
        tsum = np.zeros(self.next_pid)
        nn = np.zeros(self.next_pid)
        for x, y in self.adj:
            t = self.ties.get((x, y), 0.0)
            tsum[x] += t
            tsum[y] += t
            nn[x] += 1
            nn[y] += 1
        vol = np.minimum(1.5, TRADE_MEAN_K * tsum / np.maximum(nn, 1))
        pol = np.maximum(self.cell_pol, 0)
        inst = occ & (self.cell_pol >= 0)
        w = self.pop * inst
        L = self.lin[occ]
        den = np.maximum(Lpop, 1)
        s = np.bincount(L, weights=(w * atwar[pol])[occ], minlength=nL) / den
        v = np.bincount(L, weights=(w * vol[pol])[occ], minlength=nL) / den
        q = np.bincount(L, weights=(self.pop * self.hard)[occ],
                        minlength=nL) / den
        r = np.bincount(L, weights=(self.pop * self.raided)[occ],
                        minlength=nL) / den
        u = np.bincount(L, weights=(self.pop * self.revolted)[occ],
                        minlength=nL) / den
        ev = np.zeros(self.next_pid)
        for pid, y in self.pevent.items():
            if pid < len(ev):
                ev[pid] = y
        yev = np.bincount(L, weights=(w * ev[pol])[occ], minlength=nL) / den
        self.hard[:] = 0
        self.raided[:] = 0
        self.revolted[:] = 0
        self.pevent = {}
        out = dict(s=s[A], v=v[A], q=q[A], r=r[A], u=u[A], yev=yev[A])
        ordv = np.zeros(self.next_pid)
        for pid, P in self.polities.items():
            if P["ended"] is None:
                ordv[pid] = self.admin[P["lin"]]
        out["order"] = (np.bincount(L, weights=(w * ordv[pol])[occ],
                                    minlength=nL) / den)[A]
        out["instate"] = (np.bincount(L, weights=w[occ], minlength=nL)
                          / den)[A]
        wn = np.zeros(self.next_pid)
        ls = np.zeros(self.next_pid)
        for pid, x in self.sup_win.items():
            if pid < len(wn):
                wn[pid] = x
        for pid, x in self.sup_loss.items():
            if pid < len(ls):
                ls[pid] = x
        adv = np.zeros(self.next_pid)
        dis = np.zeros(self.next_pid)
        nn = np.zeros(self.next_pid)
        for (x, y), t in self.ties.items():
            X, Y = self.polities.get(x), self.polities.get(y)
            if X is None or Y is None or X["ended"] is not None or \
                    Y["ended"] is not None or \
                    X["culture"] == Y["culture"]:
                continue
            Lx, Ly = X["lin"], Y["lin"]
            dx, dy = float(self.dev(Lx)), float(self.dev(Ly))
            cx = float(self.craft[Lx])
            cy = float(self.craft[Ly])
            gx = max(0, dx - dy) + max(0, cx - cy)
            gy = max(0, dy - dx) + max(0, cy - cx)
            adv[x] += t * gx
            adv[y] += t * gy
            dis[x] += t * gy
            dis[y] += t * gx
            nn[x] += 1
            nn[y] += 1
        adv = np.minimum(1, 3 * adv / np.maximum(nn, 1))
        dis = np.minimum(1, 3 * dis / np.maximum(nn, 1))
        for nm, f in (("win", wn), ("loss", ls), ("adv", adv),
                      ("dis", dis)):
            out[nm] = np.bincount(L, weights=(w * f[pol])[occ],
                                  minlength=nL)[A] / den[A]
        self.sup_win, self.sup_loss = {}, {}
        return out

    def memf(self, A):
        """Memory span factor of lineages A: lifespan x (0.5 + patience)
        with `life_memory`, else 1."""
        if "life_memory" not in self.on:
            return 1.0
        return self.plife[self.Lpeople[A]] * (0.5 + self.pati[A])

    def experience(self, A, s, v, q, r, u=0.0, yev=0.0, win=0.0, loss=0.0,
                   adv=0.0, order=1.0, instate=0.0, dis=0.0):
        """Traits shaped by what a lineage lives through."""
        a = np.minimum(1.0, DT / (EXP_MEM * self.memf(A)))
        self.Lwarm[A] += a * (s - self.Lwarm[A])
        self.Lhardm[A] += a * (q - self.Lhardm[A])
        self.Ltradem[A] += a * (v - self.Ltradem[A])
        self.Lraidm[A] += a * (r - self.Lraidm[A])
        m, h = self.Lwarm[A], self.Lhardm[A]
        v1 = np.minimum(v, 1)
        safe = (1 - m) * (1 - h)
        nT = len(TRAITS)
        mult = 1.0
        if "spiky" in self.on:
            gen = GEN_LEN * self.plife[self.Lpeople[A]]
            nxt = self.Lgen_next[A]
            unset = nxt <= 0
            nxt[unset] = self.year + ((A[unset] * 7919) % 1000) / 1000 * \
                gen[unset]
            due = self.year >= nxt
            nxt[due] += gen[due]
            self.Lgen_next[A] = nxt
            mult = EXP_BG + (GEN_YEARS * due + yev) / DT
        rv = "revolt_exp" in self.on

        def push(arr, col, up, down, piv=PATH_PIVOT, path=True):
            x = arr[A]
            if path:
                g = 1 / (1 + np.exp(-(x - piv) / PATH_PW))
                up = up * 2 * (PATH_MIN + (1 - PATH_MIN) * g) / (1 + PATH_MIN)
                down = down * 2 * (PATH_MIN + (1 - PATH_MIN) * (1 - g)) / \
                    (1 + PATH_MIN)
            d = DT * mult * EXP_SCALE * (up * (1 - x) - down * x)
            if "spiky" in self.on:
                # no overshoot past the balance point
                d = d / np.maximum(1, DT * mult * EXP_SCALE * (up + down) /
                                   0.5)
            new = np.clip(x + d, 0.01, 0.99)
            if col is not None:
                self.Lexp[A, col] += new - x
            arr[A] = new
        phi = PHI_MIN + (1 - PHI_MIN) / (
            1 + np.exp(-(self.tol[A] - TOL_PIVOT) / TOL_PW))
        push(self.tol, TI["tolerance"], EXP_TRADE * v * phi,
             EXP_WAR * s + EXP_HARD * q + EXP_RAID / 2 * r +
             EXP_TRADE * v * (1 - phi) + rv * EXP_REVOLT / 2 * u,
             TOL_PIVOT, PATH_TOL > 0)
        push(self.trade, TI["trade"], EXP_TRADE / 2 * v,
             EXP_DISRUPT * (s + r))
        # wars and frontier raids harden; trade and peace soften
        push(self.viol, TI["violence"], EXP_WAR * s + EXP_RAID * r +
             rv * EXP_REVOLT * u,
             EXP_TRADE_V * v + EXP_PEACE * order * (1 - m))
        if rv:
            push(self.sep, TI["separation"], EXP_REVOLT / 2 * u,
                 EXP_CALM * v1)
        # war binds a people; wealth and long peace loosen the bond
        push(self.coh, TI["cohesion"], EXP_WAR / 2 * s,
             EXP_LUX * v1 + EXP_CALM * order * (1 - m))
        push(self.hier, nT + XTRAITS.index("hierarchy"), EXP_WAR / 2 * s,
             EXP_CALM * (1 - instate))
        cr = self.craft[A]
        tgt = APP0 + APP_K * (cr + self.dev(A) + self.admin[A] +
                              self.viol[A] + v1) / 5
        self.Lapp[A] += a * (tgt - self.Lapp[A])
        # victory and trade with the less advanced breed a sense of
        # superiority; defeat erodes it
        push(self.Lsup, None, EXP_SUP_WAR * win + EXP_SUP_TRADE * adv,
             EXP_SUP_WAR * loss + EXP_SUP_TRADE * dis)
        # threat tightens norms; trade and safety loosen them
        push(self.conf, nT + XTRAITS.index("conformity"),
             EXP_WAR / 2 * s + EXP_HARD * q + rv * EXP_REVOLT / 2 * u,
             EXP_TRADE / 2 * v1 + EXP_LOOSE * order * safe)
