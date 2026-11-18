"""Raids and wars."""
import math
import numpy as np

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class WarMixin:
    def devastate(self, t, holder):
        """A siege at city t may lay waste one cell (`devastation`)."""
        if self.R("raid").random() >= WASTE_P:
            return
        c = [t] + [int(x) for x in self.W.nb[t]
                   if x >= 0 and self.cell_pol[x] == holder]
        x = c[int(self.R("raid").integers(len(c)))]
        self.waste[x] = 0.0
        self.count("devastation")
        if x in self.cities:
            self.count("devastation_city")
            P = self.polities.get(self.cities[x]["polity"])
            if P is not None and len(P["cities"]) >= 8:
                self.log("war", f"the land around the city at "
                         f"{self.place(x)} in {self.pname(P['id'])} is "
                         f"laid waste")

    def war_prize(self, b, a):
        """What conquering state b would give state a."""
        x, y = self.passets.get(b), self.passets.get(a)
        if x is None or y is None:
            return 0.0
        return self.goods_worth(b, a, prize=True) + \
            ORE_VALUE * len(x["ores_terr"] - y["ores"]) + \
            max(0.0, x["craft"] - y["craft"]) + len(x["tech"] - y["tech"])

    def deter(self, A, B, allies):
        """Strength A projects to B's city nearest A's capital over B's
        defence there (with allies, terrain and walls); and that city."""
        cc = list(B["cities"])
        t = cc[int(np.argmin(gc_km(self.W.xyz, A["capital"], np.array(cc))))]
        PA = self.projected(A, t)
        PB = self.projected(B, t)
        for q in allies.get(B["id"], ()):
            Q = self.polities.get(q)
            if q != A["id"] and Q and Q["ended"] is None:
                PB += 0.35 * self.projected(Q, t)
        PB *= 1.4 * self.W.defence[t] * (1.25 if t == B["capital"] else 1)
        PB *= 1 + DEV_WALL * self.dev(B["lin"])
        return PA / max(PB, 1e-9), t

    def hardy(self, c):
        """war_hardy: share of the usual war losses that the people of
        cell(s) c suffer."""
        return self.phardy[np.maximum(self.cul[c], 0)]

    def feud(self, occ, L):
        """Violence costs lives where no ordered state keeps the peace."""
        f = np.clip((self.viol[L] - FEUD_PIVOT) / (1 - FEUD_PIVOT), 0, 1)
        pol = self.cell_pol[occ]
        ordv = self.padm()
        order = np.where(pol >= 0, ordv[np.maximum(pol, 0)], 0)
        lost = DT * FEUD_K * f * (1 - order)
        b_pop = self.pop[occ]
        self.pop[occ] *= 1 - lost
        self.dead("feud", occ, b_pop - self.pop[occ])
        self.count("feud_dead", float((self.pop[occ] * lost).sum()))

    def raid_K(self, a, b, Ka, Kb, cells):
        """Refresh the raid sides' capacities at cells that changed."""
        if not len(cells):
            return
        for X, K in ((a, Ka), (b, Kb)):
            m = np.isin(X, cells)
            if m.any():
                K[m] = self.Kf(self.lin[X[m]], X[m])

    def raids(self):
        """Cell-scale violence where peoples touch outside state control."""
        W = self.W
        a, b = W.E1, W.E2
        ca, cb = self.cul[a], self.cul[b]
        mix = (ca >= 0) & (cb >= 0) & (ca != cb)
        mix |= (ca >= 0) & (ca == cb) & (self.lin[a] != self.lin[b])
        a, b, ca, cb = a[mix], b[mix], ca[mix], cb[mix]
        if not len(a):
            return
        # raids between lineages of one people, less often the more
        # alike they are
        kin = ca == cb
        kinf = np.ones(len(a))
        if kin.any():
            la, lb = self.lin[a[kin]], self.lin[b[kin]]
            # each unordered pair as one integer (sorts as the pairs do)
            key, inv = np.unique(np.minimum(la, lb).astype(np.int64) * MAXL +
                                 np.maximum(la, lb), return_inverse=True)
            sm = np.array([self.similarity(int(x), int(y)) for x, y in
                           zip((key // MAXL).tolist(), (key % MAXL).tolist())])
            kinf[kin] = KIN_RAID * (0.5 + 0.5 * (1 - sm[inv]))
        xc = ca != cb
        new = xc.any() and not self.contact_seen[ca[xc], cb[xc]].all()
        for x, y in (set(zip(ca[xc].tolist(), cb[xc].tolist())) if new
                     else ()):
            if not self.contact_seen[x, y]:
                self.contact_seen[x, y] = self.contact_seen[y, x] = True
                self.log("contact", f"first contact: {self.keys[x]} meets "
                         f"{self.keys[y]}")
        suffered = []
        # capacity does not depend on population: computed once for each
        # side, redone only where a raid or takeover changes a cell
        # (worked out once per cell: a cell borders several others)
        u, inv = np.unique(np.concatenate([a, b]), return_inverse=True)
        Ku = self.Kf(self.lin[u], u)
        Ka, Kb = Ku[inv[:len(a)]], Ku[inv[len(a):]]
        for att, dfn in ((a, b), (b, a)):
            Kt, Kd = (Ka, Kb) if att is a else (Kb, Ka)
            La, Ld = self.lin[att], self.lin[dfn]
            pa = self.pop[att] / np.maximum(Kt, 1e-3)
            same_state = (self.cell_pol[att] >= 0) & \
                (self.cell_pol[att] == self.cell_pol[dfn])
            p = DT * 0.02 * self.viol[La] * (0.5 + pa) * \
                (1 + self.hostile(La)) * self.tolf(La, 0.5) * \
                np.where(same_state, 0.2, 1) * kinf
            p = p * self.raid_order(att, dfn, same_state)
            # mounted herders raid more often
            p = p * np.where(self.herding[att], 1.5, 1)
            # and so do the hungry
            p = p * (1 + HUNGER_RAID * np.clip(pa - 1, 0, 1))
            hit = self.R("raid").random(len(att)) < np.clip(p, 0, 0.9)
            self.count("raid", int(hit.sum()))
            rel = np.sqrt(self.psize[self.cul[att]] / self.psize[self.cul[dfn]])
            dmg = 0.12 * self.viol[La] * rel / W.defence[dfn]
            dmg = dmg * np.where(self.herding[att], MOUNT, 1)
            # expansive peoples leave thin, exposed frontier cells
            pdn = self.pop[dfn] / np.maximum(Kd, 1e-3)
            dmg = dmg * (1 + COST_EXPN * self.expn[Ld] *
                         np.clip(1 - 2 * pdn, 0, 1))
            dmg = dmg * self.phardy[self.cul[dfn]]
            loss = 1 - np.clip(dmg[hit], 0, 0.6)
            # (a cell raided twice in one tick loses once; count it once)
            dh = np.unique(dfn[hit])
            b_pop = self.pop[dh]
            self.pop[dfn[hit]] *= loss
            self.dead("raid", dh, b_pop - self.pop[dh])
            self.imp[dfn[hit]] *= 1 - 0.3 * (1 - loss)
            # capacity reads improvements: redo it where they fell
            self.raid_K(a, b, Ka, Kb, dfn[hit])
            if self.cities:
                self.shock(dfn[hit][np.isin(dfn[hit], list(self.cities))],
                           "raid")
            b_pop = self.mpop[dh]
            self.mpop[dfn[hit]] *= loss
            self.dead("raid", dh, b_pop - self.mpop[dh], minority=True)
            self.raided[dfn[hit]] = 1
            self.raided[att[hit]] = 1
            ah = np.unique(att[hit])
            b_pop = self.pop[ah]
            if "fortress" in self.on:
                # raiders of a fortress people pay dearly
                self.pop[att[hit]] *= 1 - 0.01 * self.hardy(att[hit]) * (
                    1 + FORT_RAID * self.pfort[np.maximum(self.cul[dfn[hit]],
                                                          0)])
            else:
                self.pop[att[hit]] *= 1 - 0.01 * self.hardy(att[hit])
            self.dead("raid", ah, b_pop - self.pop[ah])
            suffered.append(dfn[hit])
            pd = self.pop[dfn] / np.maximum(Kd, 1e-3)
            take = hit & (pd < 0.15) & (pa > 0.6) & \
                (self.R("raid").random(len(att)) < self.viol[La])
            ti, first = np.unique(dfn[take], return_index=True)
            if self.cities:
                self.shock(ti[np.isin(ti, list(self.cities))],
                           "raid takeover")
            si = att[take][first]
            mv = 0.25 * self.pop[si]
            self.pop[si] -= mv
            # the old people stays on as an underclass
            self.mcul[ti], self.mlin[ti] = self.cul[ti], self.lin[ti]
            self.mpop[ti] = 0.5 * self.pop[ti]
            self.mcap[ti] = False
            self.lin[ti] = self.lin[si]
            self.cul[ti] = self.cul[si]
            self.pop[ti] = mv
            self.raid_K(a, b, Ka, Kb, ti)
        if "turmoil" in self.on and suffered:
            # raids wear down the administration of the state they hit
            hc = np.unique(np.concatenate(suffered))
            hp = self.cell_pol[hc]
            hp = hp[hp >= 0]
            if len(hp):
                n = np.bincount(hp)
                for pid in np.nonzero(n)[0]:
                    P = self.polities.get(int(pid))
                    if P is not None and P["ended"] is None:
                        self.turmoil(P, ADM_RAID * n[pid] /
                                     max(P.get("n_cells", 0), n[pid]))

    def raid_order(self, att, dfn, same_state):
        """How far states and peace hold raids back on these edges."""
        pl = self.ptab()[0]
        f = np.ones(len(att))
        for c in (att, dfn):
            pc = self.cell_pol[c]
            L = pl[np.maximum(pc, 0)]
            ok = (pc >= 0) & (L >= 0)
            f = f * np.where(ok, 1 - RAID_ADMIN *
                             self.admin[np.maximum(L, 0)], 1)
        pa, pb = self.cell_pol[att], self.cell_pol[dfn]
        two = (pa >= 0) & (pb >= 0) & (pa != pb)
        if two.any():
            lo, hi = np.minimum(pa[two], pb[two]), np.maximum(pa[two], pb[two])
            keys = lo.astype(np.int64) * 10_000_000 + hi
            uk, inv = np.unique(keys, return_inverse=True)
            g = np.ones(len(uk))
            for i, kk in enumerate(uk):
                k = (int(kk // 10_000_000), int(kk % 10_000_000))
                g[i] = 1 - self.ties.get(k, 0.0)
                if k in self.allies or self.truce.get(k, -1) > self.tick:
                    g[i] *= RAID_PEACE
            f[two] = f[two] * g[inv]
        return f

    def war_bound(self, A, B, k):
        """An upper bound on war_chance's p, cheap enough to rule most
        pairs out: deterrence at its full 1 and the motive term at its cap
        (WAR_GAIN_CAP; every motive is >= 0). A hair above, so rounding
        can never put p over it."""
        if not A["cities"] or not B["cities"]:
            return 0.0
        if DET_K < 0:
            return math.inf
        d = self.eff(A, "dom")
        opp = 1 + OPP_K * d if B.get("acc_until", -1) > self.year else 1.0
        return DT * WAR_BASE * A["cohesion"] * (0.5 + self.eff(A, "viol")) * \
            (1 - self.ties.get(k, 0.0)) * WAR_GAIN_CAP * opp * (1 + 1e-9)

    def war_chance(self, A, B, k, allies):
        """Chance per tick that A declares war on B (`war_v2`), and its
        motives with the motivated share."""
        La, Lb = A["lin"], B["lin"]
        if not A["cities"] or not B["cities"]:
            return 0.0, None
        R, _ = self.deter(A, B, allies)
        d = self.eff(A, "dom")
        crowd = A.get("crowd", 0.5)
        g = {}
        land = 0.0
        land += HUNGER_WAR * (1 - A["fed"])
        land += LP_K * self.pressure(A)
        lv = min(2.0, max(0.5, B.get("kdens", 1) / max(A.get("kdens", 1),
                                                       1e-9)))
        g["land"] = land * lv
        g["prey"] = PREY_K * d * min(1.2, crowd) * \
            min(1.0, max(0.0, (R - 1) / (PREY_R - 1)))
        g["rule"] = d * min(2.0, B["pop"] / max(A["pop"], 1))
        g["resource"] = self.war_prize(B["id"], A["id"]) * (0.5 + d)
        sim = self.ssim(A, B)
        g["enmity"] = ENM_K * (1 - sim) * (1 - self.eff(A, "tol"))
        if "mission" in self.on:
            g["faith"] = (1 - sim) * (MIS_HOLY * self.eff(A, "pros") +
                                      MIS_BACKLASH * self.eff(B, "pros") *
                                      (1 - self.eff(A, "tol")))
        lost = [c for c in B["cities"] if A["id"] in
                self.cities[c]["owners"][:-1]]
        if "life_memory" in self.on:
            # a grievance fades with the generations that remember it
            span = IRR_MEM * self.memf(np.array([La]))[0]
            lost = [c for c in lost if self.year - self.cities[c].get(
                "lost", {}).get(A["id"], -1e9) < span]
        g["irredentism"] = IRR_K * min(1.0, len(lost) / 2)
        m = sum(g.values())
        x = WAR_EPS + m
        opp = 1 + OPP_K * d if B.get("acc_until", -1) > self.year else 1.0
        p = DT * WAR_BASE * A["cohesion"] * (0.5 + self.eff(A, "viol")) * \
            (1 - self.ties.get(k, 0.0)) * \
            min(1.0, 2 * R * R / (1 + R * R)) ** DET_K * \
            x / (1 + x / WAR_GAIN_CAP) * opp
        return p, (g, m / x)

    def wars_step(self):
        rng = self.R("war")
        pairs = self.adj
        allies = {}
        for x, y in self.allies:
            allies.setdefault(x, []).append(y)
            allies.setdefault(y, []).append(x)
        # war is costly: levies, lost harvests
        at = {x for kk in self.wars for x in kk}
        at |= {q for w in self.wars.values()
               for q in w.get("joined", ())}
        if at:
            wc = np.nonzero(np.isin(self.cell_pol, list(at)))[0]
            b_pop = self.pop[wc]
            self.pop[wc] *= 1 - WAR_COST * self.hardy(wc)
            self.dead("war levies", wc, b_pop - self.pop[wc])
        pairs = sorted(pairs)
        pairs = [pairs[i] for i in rng.permutation(len(pairs))]
        for k in pairs:
            if k in self.wars or \
                    self.truce.get(k, -1) > self.tick or \
                    self.is_vassal_pair(k):
                continue
            ab = self.live(k)
            if not ab:
                continue
            sides = (k, k[::-1])
            if rng.random() < 0.5:
                sides = sides[::-1]
            for att, dfn in sides:
                A, B = self.polities[att], self.polities[dfn]
                # the draw comes first (war_chance draws nothing), so p is
                # worked out in full only when its upper bound could beat
                # the draw; most pairs are ruled out on the bound alone
                u = rng.random()
                bf = BETRAY_K if k in self.allies else 1.0
                if u >= min(bf * self.war_bound(A, B, k), 0.5):
                    continue
                p, motive = self.war_chance(A, B, k, allies)
                p *= bf
                if u < min(p, 0.5):
                    if k in self.allies:
                        self.allies.pop(k, None)
                        self.ally_kind.pop(k, None)
                        self.count("ally_betray")
                        if len(A["cities"]) + len(B["cities"]) >= 8:
                            self.log("alliance", f"{self.pname(att)} "
                                     f"betrays its ally {self.pname(dfn)}")
                    self.count("war_" + ("same" if A["culture"] ==
                                         B["culture"] else "cross"))
                    self.wars[k] = dict(att=att, dfn=dfn, start=self.tick,
                                        caps=0, goal=None, kind="idle",
                                        done=False)
                    if motive is not None and \
                            rng.random() < motive[1]:
                        self.set_goal(self.wars[k], A, B, motive[0])
                    self.war_open(self.wars[k], A, B)
                    self.spike(att)
                    self.spike(dfn)
                    self.call_allies(self.wars[k], A, B)
                    self.ties.pop(k, None)
                    if len(A["cities"]) + len(B["cities"]) >= 8:
                        self.log("war", f"{self.pname(att)} attacks "
                                 f"{self.pname(dfn)}")
                    break
        for k in list(self.wars):
            w = self.wars.get(k)
            if w is None:
                continue
            A, B = self.polities.get(w["att"]), self.polities.get(w["dfn"])
            if not A or not B or A["ended"] is not None or \
                    B["ended"] is not None or not B["cities"] \
                    or not A["cities"]:
                self.war_close(self.wars.pop(k, None), "side ended")
                continue
            if w["goal"] is not None and \
                    not w["done"] and w["kind"] in (
                        "land", "prey", "resource", "irredentism") and \
                    w["goal"] in B["cities"]:
                # a weaker defender may cede the goal rather than fight
                g = w["goal"]
                ra = self.projected(A, g) / max(1.4 * self.W.defence[g] *
                                               self.projected(B, g), 1e-9)
                if rng.random() < WAR_CEDE * min(1.0, max(0.0, ra - 1)):
                    w["moved"] = w.get("moved", 0.0) + self.city_fe(g)
                    self.cede(w["att"], w["dfn"], g)
                    self.war_close(self.wars.pop(k, None), "ceded")
                    self.truce[k] = self.tick + 6
                    continue
            # logistics: a well-run state keeps more sieges going at once
            ns = 1 + int(LOG_SIEGE * self.logi(A))
            for _ in range(ns):
                if not B["cities"] or B["ended"] is not None or \
                        k not in self.wars:
                    break
                targets = list(B["cities"])
                dists = gc_km(self.W.xyz, A["capital"], np.array(targets))
                t = targets[int(np.argmin(dists))]
                if w.get("goal") in B["cities"] and not w.get("done"):
                    t = w["goal"]
                PA = self.projected(A, t)
                PB = self.projected(B, t)
                # defensive allies send help (not against their own allies)
                for kk in self.allies:
                    if w["dfn"] in kk:
                        q = kk[1] if kk[0] == w["dfn"] else kk[0]
                        Q = self.polities.get(q)
                        if q != w["att"] and Q and Q["ended"] is None and \
                                (min(q, w["att"]), max(q, w["att"])) \
                                not in self.allies and \
                                (q in w.get("joined", ())):
                            PB += 0.35 * self.projected(Q, t)
                            w.setdefault("helpers", set()).add(q)
                # a lord defends its vassals; vassals send levies to a lord
                o = self.vassal.get(w["dfn"])
                if o is not None and o != w["att"] and o in self.polities:
                    PB += 0.5 * self.projected(self.polities[o], t)
                for v, lord in self.vassal.items():
                    if lord == w["dfn"] and v != w["att"] and \
                            v in self.polities:
                        PB += 0.35 * self.projected(self.polities[v], t)
                PB *= 1.4 * self.W.defence[t] * \
                    (1.25 if t == B["capital"] else 1)
                # walls and works
                PB *= 1 + DEV_WALL * self.dev(B["lin"])
                if w["dfn"] not in self.vassal and \
                        PA > VASSAL_RATIO * PB and \
                        rng.random() < 0.5 * (1.2 - B["cohesion"]) * \
                        (0.5 + self.eff(A, "dom")):
                    # the weaker side submits rather than be besieged
                    self.submit(w["dfn"], w["att"])
                    self.war_close(self.wars.pop(k, None), "submitted")
                    self.truce[k] = self.tick + 6
                    w["submitted"] = True
                    break
                pw = PA ** 2 / (PA ** 2 + PB ** 2 + 1e-9)
                b_pop = self.pop[t]
                self.pop[t] *= 1 - 0.03 * self.hardy(t)
                self.dead("siege", t, b_pop - self.pop[t])
                self.fort_toll(A, t)
                self.shock(t, "siege")
                self.devastate(t, w["dfn"])
                fe = self.city_fe(t)
                cap_t = t == B["capital"]
                won = rng.random() < pw
                w["sieges"] = w.get("sieges", 0) + 1
                self.siege_log.append((
                    self.year, w.get("id", -1), "att", int(t), round(fe),
                    int(cap_t), w["att"], w["dfn"], round(PA, 1),
                    round(PB, 1), round(pw, 4), int(won)))
                terms = self.siege_terms(w, A, B, t) if won else ""
                self.siege_log[-1] += (terms,)
                if terms == "tributary":
                    # the defender sues for terms and pays tribute
                    self.count("war_tributary")
                    self.submit(w["dfn"], w["att"])
                    self.war_close(self.wars.pop(k, None), "tributary")
                    self.truce[k] = self.tick + 6
                    w["submitted"] = True
                    break
                if terms == "sack":
                    # one sack a tick: the army goes home with the loot
                    self.sack(w, A, B, t)
                    break
                if won:
                    w["moved"] = w.get("moved", 0.0) + fe
                    w["caps"] += 1
                    if t == w.get("goal"):
                        w["done"] = True
                        self.count("war_goal_met")
                    self.capture(w["att"], w["dfn"], t)
                else:
                    A["cohesion"] *= 1 - 0.02 * (
                        1.5 - self.logi(A) / 1.5)
            if w.get("submitted"):
                continue
            if k in self.wars and \
                    A["ended"] is None and B["ended"] is None and \
                    A["cities"] and B["cities"]:
                self.counteroffensive(k, w, A, B)
                if k not in self.wars:
                    continue
            dur = self.tick - w["start"]
            pend = WAR_END0 + 0.03 * dur
            # supply lines let a campaign go on
            pend *= 1 - LOG_END * self.logi(A) / 1.5
            if w.get("done"):
                pend = max(pend, WAR_DONE)
            rep = w.get("recaps", 0) > w["caps"]
            if rep:
                pend = max(pend, WAR_DONE)
            if rng.random() < pend or \
                    self.polities[w["dfn"]]["ended"] is not None:
                self.war_close(self.wars.pop(k, None),
                               "defender fell" if self.polities[w["dfn"]][
                                   "ended"] is not None else
                               "goal met" if w.get("done") else
                               "repulsed" if rep else "peace")
                self.truce[k] = self.tick + 6

    def call_allies(self, w, A, B):
        """Defender B's allies are called against attacker A: each joins
        or refuses (and the alliance ends)."""
        b, a = B["id"], A["id"]
        w["joined"] = set()
        for kk in [kk for kk in self.allies if b in kk]:
            q = kk[1] if kk[0] == b else kk[0]
            Q = self.polities.get(q)
            if q == a or not Q or Q["ended"] is not None or \
                    (min(q, a), max(q, a)) in self.allies:
                continue
            j = ALLY_J0 + (1 - ALLY_J0) * min(
                1.0, (Q["strength"] + B["strength"]) /
                max(A["strength"], 1e-9))
            if self.R("war").random() < j:
                w["joined"].add(q)
                self.count("ally_join")
            else:
                self.allies.pop(kk, None)
                self.ally_kind.pop(kk, None)
                self.count("ally_refuse")
                if len(Q["cities"]) + len(B["cities"]) >= 8:
                    self.log("alliance", f"{self.pname(q)} refuses the "
                             f"call of {self.pname(b)}; the alliance ends")

    def defence_at(self, D, O, t):
        """What state D brings to bear holding its city t against O:
        its own projected strength, allies not allied to O, lord and
        vassals, times terrain, capital and walls."""
        PD = self.projected(D, t)
        d, o = D["id"], O["id"]
        for kk in self.allies:
            if d in kk:
                q = kk[1] if kk[0] == d else kk[0]
                Q = self.polities.get(q)
                # (the add was missing until 2026-11-07: D's allies never
                # helped it hold its cities)
                if q != o and Q and Q["ended"] is None and \
                        (min(q, o), max(q, o)) not in self.allies:
                    PD += 0.35 * self.projected(Q, t)
        lord = self.vassal.get(d)
        if lord is not None and lord != o and lord in self.polities:
            PD += 0.5 * self.projected(self.polities[lord], t)
        for v, lo in self.vassal.items():
            if lo == d and v != o and v in self.polities:
                PD += 0.35 * self.projected(self.polities[v], t)
        PD *= 1.4 * self.W.defence[t] * (1.25 if t == D["capital"] else 1)
        PD *= 1 + DEV_WALL * self.dev(D["lin"])
        return PD

    def counteroffensive(self, k, w, A, B):
        """The defender B strikes back at the attacker A (two_sided)."""
        rng = self.R("war")
        R = B.get("strength", 0.0) / max(A.get("strength", 0.0), 1e-9)
        if rng.random() >= COUNTER_K * R * R / (1 + R * R):
            return
        ns = 1 + int(LOG_SIEGE * self.logi(B))
        for _ in range(ns):
            if not A["cities"] or A["ended"] is not None or \
                    k not in self.wars:
                break
            lost = [c for c in A["cities"]
                    if w["dfn"] in self.cities[c]["owners"][:-1]]
            pool = lost or list(A["cities"])
            t = pool[int(np.argmin(gc_km(self.W.xyz, B["capital"],
                                         np.array(pool))))]
            PB = self.projected(B, t)
            PA = self.defence_at(A, B, t)
            pw = PB ** 2 / (PB ** 2 + PA ** 2 + 1e-9)
            b_pop = self.pop[t]
            self.pop[t] *= 1 - 0.03 * self.hardy(t)
            self.dead("siege", t, b_pop - self.pop[t])
            self.fort_toll(B, t)
            self.shock(t, "siege")
            self.devastate(t, w["att"])
            fe = self.city_fe(t)
            won = rng.random() < pw
            w["sieges"] = w.get("sieges", 0) + 1
            self.siege_log.append((
                self.year, w.get("id", -1), "dfn", int(t), round(fe),
                int(t == A["capital"]), w["dfn"], w["att"], round(PB, 1),
                round(PA, 1), round(pw, 4), int(won),
                "annex" if won else ""))
            if won:
                w["moved_back"] = w.get("moved_back", 0.0) + fe
                w["recaps"] = w.get("recaps", 0) + 1
                self.count("war_counter_capture")
                self.capture(w["dfn"], w["att"], t)
                if k not in self.wars:
                    break
            else:
                B["cohesion"] *= 1 - 0.02 * (
                    1.5 - self.logi(B) / 1.5)

    def city_fe(self, c):
        """Food-equivalents in a city cell (records)."""
        return float(self.pop[c] * self.peat[max(int(self.cul[c]), 0)])

    def war_open(self, w, A, B):
        """Start a war's record (wars.csv; no draws)."""
        w["id"] = len(self.war_log)
        w["rec"] = dict(
            id=w["id"], start=self.year, att=A["id"], dfn=B["id"],
            people_att=self.keys[A["culture"]],
            people_dfn=self.keys[B["culture"]],
            landmass_att=int(self.W.landmass[A["capital"]]),
            landmass_dfn=int(self.W.landmass[B["capital"]]),
            cities_att=len(A["cities"]), cities_dfn=len(B["cities"]),
            strength_att=round(A.get("strength", 0.0), 1),
            strength_dfn=round(B.get("strength", 0.0), 1))
        self.war_log.append(w["rec"])

    def war_close(self, w, why):
        """Finish a war's record."""
        if not w or "rec" not in w:
            return
        r = w["rec"]
        r.update(end=self.year, years=self.year - r["start"], why=why,
                 goal=w.get("kind") if w.get("goal") is not None else "",
                 goal_city=w.get("goal", ""), goal_met=int(bool(w.get("done"))),
                 sieges=w.get("sieges", 0), captures=w.get("caps", 0),
                 recaptures=w.get("recaps", 0),
                 moved=round(w.get("moved", 0.0)),
                 moved_back=round(w.get("moved_back", 0.0)),
                 helpers=" ".join(str(x) for x in
                                  sorted(w.get("helpers", ()))),
                 sacks=w.get("sacks", 0))

    def set_goal(self, w, A, B, gains):
        """The goal of a motivated war: its largest motive."""
        kind = max(gains, key=gains.get)
        goal = B["capital"]
        if kind == "irredentism":
            lost = [c for c in B["cities"] if A["id"] in
                    self.cities[c]["owners"][:-1]]
            if lost:
                goal = lost[0]
        elif kind in ("land", "prey", "enmity"):
            cc = list(B["cities"])
            goal = cc[int(np.argmin(gc_km(self.W.xyz, A["capital"],
                                          np.array(cc))))]
        elif kind == "resource":
            have = self.passets.get(A["id"], {}).get("kinds", set())
            for c, kd in zip(self.res_cell, self.res_kind):
                cc = int(self.cell_city[c])
                if kd not in have and self.cell_pol[c] == B["id"] and \
                        cc in B["cities"]:
                    goal = cc
                    break
        w["goal"], w["kind"] = int(goal), kind
        self.count(f"war_goal_{kind}")

    def cede(self, att, dfn, t):
        """State dfn hands city t to state att to end a war."""
        A, B = self.polities[att], self.polities[dfn]
        rec = self.cities[t]
        rec.setdefault("lost", {})[dfn] = self.year
        self.turmoil(B, ADM_LOSS / max(len(B["cities"]), 1))
        B["cities"].discard(t)
        A["cities"].add(t)
        rec["polity"] = att
        rec["owners"].append(att)
        self.count("war_ceded")
        self.city_elite_to(A, t)
        if len(A["cities"]) + len(B["cities"]) >= 6:
            self.log("war", f"{self.pname(dfn)} cedes the city at "
                     f"{self.place(t)} to {self.pname(att)}")
        if not B["cities"]:
            self.kill_polity(dfn, f"ceded its last city to "
                             f"{self.pname(att)}")
        elif B["capital"] == t:
            self.recapital(B)

    def capture(self, att, dfn, t):
        A, B = self.polities[att], self.polities[dfn]
        ca, La = A["culture"], A["lin"]
        rec = self.cities[t]
        was_cap = B["capital"] == t
        self.city_elite_to(A, t)
        rec.setdefault("lost", {})[dfn] = self.year
        if A["culture"] != B["culture"]:
            self.sup_win[att] = min(1.0, self.sup_win.get(att, 0.0) +
                                    1 / max(len(A["cities"]), 1))
            self.sup_loss[dfn] = min(1.0, self.sup_loss.get(dfn, 0.0) +
                                     1 / max(len(B["cities"]), 1))
        self.count("capture_" + ("same" if rec["culture"] == ca else "cross"))
        self.shock(t, "sack")
        rec["n_sacks"] = rec.get("n_sacks", 0) + 1
        # the canals and fields of the city and its land are wrecked
        hint = self.cell_city == t
        self.imp[hint] *= 1 - 0.5 * IMP_SACK * self.eff(A, "viol")
        self.imp[t] *= 1 - IMP_SACK * self.eff(A, "viol")
        # a conqueror may carry off the secret
        take = self.guard[B["lin"]] & ~self.guard[La]
        for g in np.nonzero(take)[0]:
            if self.R("war").random() < GUARD_TAKE * (2 if was_cap else 1):
                self.guard[La, g] = True
                self.log("craft", f"{self.pname(att)} takes the secret "
                         f"of {GUARD_NAMES[g]} from {self.pname(dfn)}")
        self.turmoil(B, ADM_LOSS / max(len(B["cities"]), 1))
        B["cities"].discard(t)
        A["cities"].add(t)
        rec["polity"] = att
        rec["owners"].append(att)
        spare = 1 - DOM_SPARE * self.eff(A, "dom")
        b_pop, b_mpop = self.pop[t], self.mpop[t]
        self.pop[t] *= 1 - (0.1 + 0.4 * self.eff(A, "viol")) * spare * \
            self.hardy(t)
        self.mpop[t] *= 1 - (0.1 + 0.4 * self.eff(A, "viol")) * spare
        self.dead("sack", t, b_pop - self.pop[t])
        self.dead("sack", t, b_mpop - self.mpop[t], minority=True)
        A["cohesion"] = min(1, A["cohesion"] + 0.03)
        if rec["culture"] != ca and self.R("war").random() < \
                (1 - self.eff(A, "tol")) * self.eff(A, "viol") * \
                (1 - self.eff(A, "dom")):
            hint = (self.cell_city == t) & (self.cul == rec["culture"])
            hc = np.nonzero(hint)[0]
            b_pop = self.pop[hc]
            self.pop[hint] *= 1 - 0.85 * self.hardy(np.nonzero(hint)[0])
            self.dead("clearance", hc, b_pop - self.pop[hc])
            b_pop = self.pop[t]
            self.pop[t] *= 1 - 0.7 * self.hardy(t)
            self.dead("clearance", t, b_pop - self.pop[t])
            self.shock(t, "clearance")
            self.imp[hint] *= 0.5
            if len(A["cities"]) + len(B["cities"]) >= 5:
                self.log("clearance", f"{self.pname(att)} clears "
                         f"{self.keys[rec['culture']]} from the city at "
                         f"{self.place(t)}")
        if rec["culture"] != ca:
            # a garrison and settlers of the conqueror's people stay on
            self.add_minority([t], ca, La, MIN_GARRISON * self.pop[t] *
                              self.peat[rec["culture"]] / self.peat[ca])
        if was_cap:
            B["cohesion"] *= 0.6
            self.spike(dfn)
            if len(B["cities"]) + 1 >= 4:
                self.log("conquest", f"{self.pname(att)} takes the capital "
                         f"of {self.pname(dfn)} at {self.place(t)}")
            if not B["cities"]:
                self.kill_polity(dfn, f"conquered by {self.pname(att)}")
            elif B["culture"] == ca and len(B["cities"]) <= 3:
                for c in list(B["cities"]):
                    self.cities[c]["polity"] = att
                    self.cities[c]["owners"].append(att)
                    A["cities"].add(c)
                B["cities"] = set()
                self.kill_polity(dfn, f"absorbed by {self.pname(att)}")
            elif self.R("war").random() < SHATTER_P:
                rest = list(B["cities"])
                B["cities"] = set()
                self.kill_polity(dfn, "shattered after its capital fell")
                for c in rest:
                    Lc = self.lin[c] if self.lin[c] >= 0 else B["lin"]
                    self.cities[c]["polity"] = self.new_polity(
                        Lc, c, 0.5, parent=dfn)
                    self.cities[c]["owners"].append(self.cities[c]["polity"])
            else:
                self.recapital(B)

    def siege_terms(self, w, A, B, t):
        """What the winner of a siege at city t does (`war_terms`):
        "annex", "tributary" or "sack". Without the switch, annex."""
        if "war_terms" not in self.on:
            return "annex"
        # can A govern t? the share of its strength it projects there
        gov = self.projected(A, t) / max(A["strength"], 1e-9)
        d = self.eff(A, "dom")
        wa = gov * (0.5 + d)
        wt = (1 - gov) * (0.5 + d) if B["id"] not in self.vassal else 0.0
        ws = TERMS_SACK * self.eff(A, "viol") * (1.5 - d)
        kind = w.get("kind") if w.get("goal") is not None else None
        if kind in ("land", "resource", "irredentism"):
            wa *= TERMS_GOAL
        elif kind == "prey":
            ws *= TERMS_GOAL
        elif kind == "rule":
            wa *= TERMS_GOAL
            wt *= TERMS_GOAL
        u = self.R("war").random() * (wa + wt + ws)
        return "annex" if u < wa else "tributary" if u < wa + wt \
            else "sack"

    def sack(self, w, A, B, t):
        """`war_terms`: A plunders city t and leaves it to B."""
        att, dfn = A["id"], B["id"]
        rec = self.cities[t]
        was_cap = B["capital"] == t
        self.count("war_sack")
        w["sacks"] = w.get("sacks", 0) + 1
        if A["culture"] != B["culture"]:
            self.sup_win[att] = min(1.0, self.sup_win.get(att, 0.0) +
                                    1 / max(len(A["cities"]), 1))
            self.sup_loss[dfn] = min(1.0, self.sup_loss.get(dfn, 0.0) +
                                     1 / max(len(B["cities"]), 1))
        self.shock(t, "sack")
        rec["n_sacks"] = rec.get("n_sacks", 0) + 1
        hint = self.cell_city == t
        self.imp[hint] *= 1 - 0.5 * IMP_SACK * self.eff(A, "viol")
        self.imp[t] *= 1 - IMP_SACK * self.eff(A, "viol")
        take = self.guard[B["lin"]] & ~self.guard[A["lin"]]
        for g in np.nonzero(take)[0]:
            if self.R("war").random() < GUARD_TAKE * (2 if was_cap else 1):
                self.guard[A["lin"], g] = True
                self.log("craft", f"{self.pname(att)} takes the secret "
                         f"of {GUARD_NAMES[g]} from {self.pname(dfn)}")
        self.turmoil(B, ADM_LOSS / max(len(B["cities"]), 1))
        spare = 1 - DOM_SPARE * self.eff(A, "dom")
        b_pop, b_mpop = self.pop[t], self.mpop[t]
        self.pop[t] *= 1 - (0.1 + 0.4 * self.eff(A, "viol")) * spare * \
            self.hardy(t)
        self.mpop[t] *= 1 - (0.1 + 0.4 * self.eff(A, "viol")) * spare
        self.dead("sack", t, b_pop - self.pop[t])
        self.dead("sack", t, b_mpop - self.mpop[t], minority=True)
        A["cohesion"] = min(1, A["cohesion"] + 0.03)
        if was_cap:
            B["cohesion"] *= 0.8
            self.spike(dfn)
        if w.get("kind") == "prey" and w.get("goal") is not None:
            # plunder was the point
            w["done"] = True
            self.count("war_goal_met")
        if len(A["cities"]) + len(B["cities"]) >= 6:
            self.log("war", f"{self.pname(att)} sacks the city at "
                     f"{self.place(t)} and leaves it to {self.pname(dfn)}")

    def fort_toll(self, P, t):
        """`fortress`: a state besieging a fortress people's city loses
        FORT_SIEGE x f x the city's people, across its cells."""
        if "fortress" not in self.on or t not in self.cities:
            return
        f = self.pfort[self.cities[t]["culture"]]
        if f <= 0:
            return
        m = np.nonzero((self.cell_pol == P["id"]) & (self.lin >= 0))[0]
        tot = self.pop[m].sum()
        if tot <= 0:
            return
        loss = min(0.5, FORT_SIEGE * f * self.pop[t] / tot)
        b_pop = self.pop[m]
        self.pop[m] *= 1 - loss * self.hardy(m)
        self.dead("siege", m, b_pop - self.pop[m])
        self.count("fortress_toll")
        self.count("fortress_heads", int(loss * tot))
