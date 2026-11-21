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
                         f"laid waste",
                         cell=x, polities=[P['id']])

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
        cc = list(B["cities"]) or [B["capital"]]     # a camp: its seat
        t = cc[int(np.argmin(gc_km(self.W.xyz, A["capital"], np.array(cc))))]
        PA = self.projected(A, t)
        PB = self.projected(B, t)
        for q in allies.get(B["id"], ()):
            Q = self.polities.get(q)
            if q != A["id"] and Q and Q["ended"] is None:
                PB += 0.35 * self.projected(Q, t)
        PB *= 1.4 * self.city_def(t) * (1.25 if t == B["capital"] else 1)
        PB *= 1 + DEV_WALL * self.dev(B["lin"])
        return PA / max(PB, 1e-9), t

    def offense(self, P):
        """`ruler_mil`: what state P's rulers add to its strength when it
        attacks: the ruler's own talent plus what earlier reigns left."""
        if "ruler_mil" not in self.on:
            return 1.0
        return 1.0 + P.get("gen", 0.0) + P.get("gen_legacy", 0.0)

    def draw_general(self):
        """A ruler's talent for offense (`ruler_mil`): exponential, mean
        RULER_MIL_MEAN, capped at RULER_MIL_CAP."""
        return min(RULER_MIL_CAP,
                   float(self.R("ruler_mil").exponential(RULER_MIL_MEAN)))

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
                         f"{self.keys[y]}",
                         peoples=[self.keys[x], self.keys[y]])
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
            p = DT * RAID_RATE * self.viol[La] * (0.5 + pa) * \
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
            self.rows_scale(dfn[hit], loss, "raid")
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
            # one cell may send two takeover bands: debit each
            np.subtract.at(self.pop, si, mv)
            # the old people stays on as an underclass; the other half
            # and any old minority are lost (records)
            vt = self.viol[self.lin[si]]
            self.lost_rows(ti, 0.5 * self.pop[ti], vt, "raid")
            self.lost_rows(W.N + ti, np.where(self.mlin[ti] >= 0,
                                              self.mpop[ti], 0), vt, "raid")
            self.rows_scale(ti, 0.0, "raid", vt)
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
                if k in self.allies or self.truce.get(k, -1) > self.year:
                    g[i] *= RAID_PEACE
            f[two] = f[two] * g[inv]
        return f

    def war_bound(self, A, B, k):
        """An upper bound on war_chance's p, cheap enough to rule most
        pairs out: deterrence at its full 1 and the motive term at its cap
        (WAR_GAIN_CAP; every motive is >= 0). A hair above, so rounding
        can never put p over it."""
        if not self.seated(A) or not self.seated(B):
            return 0.0
        if DET_K < 0:
            return math.inf
        d = self.eff(A, "dom")
        opp = 1 + OPP_K * d if B.get("acc_until", -1) > self.year else 1.0
        return self.dtp * WAR_BASE * A["cohesion"] * \
            (0.5 + self.eff(A, "viol")) * \
            (1 - self.ties.get(k, 0.0)) * WAR_GAIN_CAP * opp * (1 + 1e-9)

    def war_chance(self, A, B, k, allies):
        """Chance per political step that A declares war on B (`war_v2`),
        and its motives with the motivated share."""
        La, Lb = A["lin"], B["lin"]
        if not self.seated(A) or not self.seated(B):
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
        if "war_odds" in self.on:
            # a steep gate on the odds; desperation, hatred and faith keep
            # a floor under it that falls with the odds, so it never opens
            # wars the old rule would not (at most 1: war_bound holds)
            fl = ODDS_FLOOR * min(1.0, R / ODDS_MID) * min(
                1.0, max(0.0, 1 - A["fed"]) + g["enmity"] +
                g.get("faith", 0.0))
            z = (math.log(max(R, 1e-12)) - math.log(ODDS_MID)) / ODDS_W
            det = fl + (1 - fl) / (1 + math.exp(-max(-50.0, min(50.0, z))))
        else:
            det = min(1.0, 2 * R * R / (1 + R * R)) ** DET_K
        p = self.dtp * WAR_BASE * A["cohesion"] * \
            (0.5 + self.eff(A, "viol")) * \
            (1 - self.ties.get(k, 0.0)) * det * \
            x / (1 + x / WAR_GAIN_CAP) * opp
        return p, (g, m / x)

    def wars_step(self):
        rng = self.R("war")
        pairs = self.adj
        allies = {}
        for x, y in self.allies:
            allies.setdefault(x, []).append(y)
            allies.setdefault(y, []).append(x)
        odds = "war_odds" in self.on
        # war is costly: levies, lost harvests
        at = {x for kk in self.wars for x in kk}
        at |= {q for w in self.wars.values()
               for q in w.get("joined", ())}
        if "army" in self.on:
            self.army_step(at)
        elif at:
            wc = np.nonzero(np.isin(self.cell_pol, list(at)))[0]
            b_pop = self.pop[wc]
            self.pop[wc] *= 1 - self.dtp * WAR_COST * self.hardy(wc)
            self.dead("war levies", wc, b_pop - self.pop[wc])
        pairs = sorted(pairs)
        pairs = [pairs[i] for i in rng.permutation(len(pairs))]
        for k in pairs:
            if k in self.wars or \
                    self.truce.get(k, -1) > self.year or \
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
                if u >= min(bf * self.war_bound(A, B, k),
                            self.dtp * WAR_P_CAP):
                    continue
                p, motive = self.war_chance(A, B, k, allies)
                p *= bf
                if u < min(p, self.dtp * WAR_P_CAP):
                    if k in self.allies:
                        self.allies.pop(k, None)
                        self.ally_kind.pop(k, None)
                        self.count("ally_betray")
                        if len(A["cities"]) + len(B["cities"]) >= 8:
                            self.log("alliance", f"{self.pname(att)} "
                                     f"betrays its ally {self.pname(dfn)}",
                                     polities=[att, dfn])
                    self.count("war_" + ("same" if A["culture"] ==
                                         B["culture"] else "cross"))
                    self.wars[k] = dict(att=att, dfn=dfn, start=self.year,
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
                                 f"{self.pname(dfn)}",
                                 polities=[att, dfn])
                    break
        for k in list(self.wars):
            w = self.wars.get(k)
            if w is None:
                continue
            A, B = self.polities.get(w["att"]), self.polities.get(w["dfn"])
            if not A or not B or A["ended"] is not None or \
                    B["ended"] is not None or not self.seated(B) \
                    or not self.seated(A):
                self.war_close(self.wars.pop(k, None), "side ended")
                continue
            if w["goal"] is not None and \
                    not w["done"] and w["kind"] in (
                        "land", "prey", "resource", "irredentism") and \
                    w["goal"] in B["cities"] and not (
                        odds and len(B["cities"]) == 1):
                # a weaker defender may cede the goal rather than fight
                # (`war_odds`: but not its last city, which would end it)
                g = w["goal"]
                ra = self.projected(A, g) * self.offense(A) * \
                    self.field(A) / max(
                    1.4 * self.city_def(g) * self.projected(B, g), 1e-9)
                if rng.random() < over(WAR_CEDE * min(
                        1.0, max(0.0, ra - 1)), self.dtp):
                    w["moved"] = w.get("moved", 0.0) + self.city_fe(g)
                    # closed first: ceding a last city ends the defender,
                    # and its end would close the war as "defender fell"
                    self.war_close(self.wars.pop(k, None), "ceded")
                    self.cede(w["att"], w["dfn"], g)
                    self.truce[k] = self.year + TRUCE_WAR
                    continue
            w.setdefault("last_siege", w["start"])
            w.setdefault("on", [])
            # sieges under way (`pol_step`) go on or are decided
            self.sieges_run(k, w, A, B)
            if k in self.wars and not w.get("submitted"):
                self.sieges_open(k, w, A, B)
            if w.get("submitted") or k not in self.wars:
                continue
            if A["ended"] is None and B["ended"] is None and \
                    self.seated(A) and self.seated(B):
                self.counteroffensive(k, w, A, B)
                if k not in self.wars:
                    continue
            if w["on"]:
                w["last_siege"] = self.year
            if odds and self.year - w["last_siege"] >= WAR_STALL:
                # no siege for years: the war peters out
                self.war_close(self.wars.pop(k, None), "abandoned")
                self.truce[k] = self.year + TRUCE_WAR
                continue
            # (the chance per SPAN years, made the chance this step below)
            if "army" in self.on:
                # `army`: worn out by the soldiers lost, not by time
                ls = w.get("lost", {})
                pend = WAR_END0 + EXH_K * max(
                    ls.get(P["id"], 0.0) / max(P.get("pop", 0.0), 1.0)
                    for P in (A, B))
            else:
                pend = WAR_END0 + WAR_END_K * (self.year - w["start"])
            # supply lines let a campaign go on
            pend *= 1 - LOG_END * self.logi(A) / 1.5
            if w.get("done"):
                pend = max(pend, WAR_DONE)
            rep = w.get("recaps", 0) > w["caps"]
            if rep:
                pend = max(pend, WAR_DONE)
            if rng.random() < over(pend, self.dtp) or \
                    self.polities[w["dfn"]]["ended"] is not None:
                self.war_close(self.wars.pop(k, None),
                               "defender fell" if self.polities[w["dfn"]][
                                   "ended"] is not None else
                               "goal met" if w.get("done") else
                               "repulsed" if rep else "peace")
                self.truce[k] = self.year + TRUCE_WAR

    def siege_odds(self, w, A, B, t):
        """Attacker A's projected strength at B's city t (with its
        ruler's offense), B's defence there (allies who joined, lord,
        vassals, terrain, capital, walls), and A's chance of taking it."""
        PA = self.projected(A, t) * self.offense(A)
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
        PB *= 1.4 * self.city_def(t) * \
            (1.25 if t == B["capital"] else 1)
        # walls and works
        PB *= 1 + DEV_WALL * self.dev(B["lin"])
        PA *= self.field(A)
        PB *= self.garrison(B)
        return PA, PB, PA ** 2 / (PA ** 2 + PB ** 2 + 1e-9)

    def sieges_open(self, k, w, A, B):
        """The attacker lays sieges in the slots its logistics allow and
        no siege fills: at the goal city, else the defender's city nearest
        its capital. A defender that would likely lose may submit first;
        at too long odds the attacker ravages or sits."""
        rng = self.R("war")
        odds = "war_odds" in self.on
        if not B["cities"]:
            # `camps`: a camp cannot be besieged; it is brought to battle
            self.camp_battle(k, w, A, B)
            return
        # logistics: a well-run state keeps more sieges going at once
        ns = 1 + int(LOG_SIEGE * self.logi(A))
        free = ns - sum(1 for s in w["on"] if s["side"] == "att")
        for _ in range(free):
            if not B["cities"] or B["ended"] is not None or \
                    k not in self.wars:
                break
            busy = {s["t"] for s in w["on"]}
            targets = [c for c in B["cities"] if c not in busy]
            if not targets:
                break
            dists = gc_km(self.W.xyz, A["capital"], np.array(targets))
            t = targets[int(np.argmin(dists))]
            if w.get("goal") in targets and not w.get("done"):
                t = w["goal"]
            PA, PB, pw = self.siege_odds(w, A, B, t)
            if odds:
                # `war_odds`: a defender that would likely lose sues
                # for terms before the siege
                sub = SUBMIT_K * min(1.0, max(0.0, (pw - SUBMIT_ODDS) /
                                              (1 - SUBMIT_ODDS)))
            else:
                sub = 0.5 if PA > VASSAL_RATIO * PB else 0.0
            if w["dfn"] not in self.vassal and sub > 0 and \
                    rng.random() < sub * (1.2 - B["cohesion"]) * \
                    (0.5 + self.eff(A, "dom")):
                # the weaker side submits rather than be besieged
                self.submit(w["dfn"], w["att"])
                self.war_close(self.wars.pop(k, None), "submitted")
                self.truce[k] = self.year + TRUCE_WAR
                w["submitted"] = True
                return
            if odds and pw < SIEGE_MIN:
                # too long odds to besiege: ravage the land or sit
                if rng.random() < over(self.eff(A, "viol"), self.dtp):
                    self.ravage(w, A, B, t)
                return
            if self.siege_start(k, w, "att", t, A, B) == "stop":
                return

    def siege_start(self, k, w, side, t, X, Y):
        """X lays siege to Y's city t. Under `pol_step` the siege lasts
        L years (SIEGE_YEARS x the city's defence, exponential, 1 to
        SIEGE_MAX) and is decided at its end; otherwise at once."""
        w["last_siege"] = self.year
        s = dict(side=side, t=int(t), start=self.year, end=self.year)
        if "pol_step" not in self.on:
            return self.siege_end(k, w, s, X, Y, toll=True)
        deff = 1.4 * self.city_def(t) * (1.25 if t == Y["capital"] else 1) \
            * (1 + DEV_WALL * self.dev(Y["lin"]))
        L = math.ceil(self.R("war").exponential(SIEGE_YEARS * deff))
        s["end"] = self.year + int(min(SIEGE_MAX, max(1, L)))
        w["on"].append(s)
        return None

    def sieges_run(self, k, w, A, B):
        """Sieges under way: a city that changed hands is no longer
        besieged; the rest lose their share of SIEGE_TOLL for this step,
        and those whose time is up are decided."""
        for s in list(w["on"]):
            if k not in self.wars:
                return
            X, Y = (A, B) if s["side"] == "att" else (B, A)
            t = s["t"]
            if t not in Y["cities"] or X["ended"] is not None:
                w["on"].remove(s)
                continue
            b_pop = self.pop[t]
            self.pop[t] *= 1 - over(SIEGE_TOLL, self.dtp,
                                    s["end"] - s["start"]) * self.hardy(t)
            self.dead("siege", t, b_pop - self.pop[t])
            if self.year >= s["end"]:
                w["on"].remove(s)
                if self.siege_end(k, w, s, X, Y) == "stop":
                    return

    def siege_end(self, k, w, s, X, Y, toll=False):
        """A siege is decided on the odds now: the attacker's sieges
        (terms, sack, capture, or a failure), or the defender's
        counter-offensive (recapture or failure). Returns "stop" when
        the war ended or the army went home with loot."""
        rng = self.R("war")
        t = s["t"]
        att = s["side"] == "att"
        if att:
            A, B = X, Y
            PX, PY, pw = self.siege_odds(w, A, B, t)
        else:
            PX = self.projected(X, t) * self.offense(X) * self.field(X)
            PY = self.defence_at(Y, X, t) * self.garrison(Y)
            pw = PX ** 2 / (PX ** 2 + PY ** 2 + 1e-9)
        if toll:
            b_pop = self.pop[t]
            self.pop[t] *= 1 - SIEGE_TOLL * self.hardy(t)
            self.dead("siege", t, b_pop - self.pop[t])
        self.fort_toll(X, t)
        self.shock(t, "siege")
        self.devastate(t, Y["id"])
        fe = self.city_fe(t)
        won = rng.random() < pw
        if "army" in self.on:
            self.army_loss(w, X, ARMY_WON if won else ARMY_LOST)
            self.army_loss(w, Y, ARMY_LOST if won else ARMY_WON)
        w["sieges"] = w.get("sieges", 0) + 1
        cap_t = int(t == Y["capital"])
        rec = (self.year, w.get("id", -1), s["side"], int(t), round(fe),
               cap_t, X["id"], Y["id"], round(PX, 1), round(PY, 1),
               round(pw, 4), int(won))
        if not att:
            self.siege_log.append(rec + (
                "annex" if won else "", len(X["cities"]), len(Y["cities"]),
                s["end"] - s["start"]))
            if won:
                w["moved_back"] = w.get("moved_back", 0.0) + fe
                w["recaps"] = w.get("recaps", 0) + 1
                self.count("war_counter_capture")
                self.capture(w["dfn"], w["att"], t)
                if k not in self.wars:
                    return "stop"
            else:
                X["cohesion"] *= 1 - SIEGE_COH * (1.5 - self.logi(X) / 1.5)
            return None
        terms = self.siege_terms(w, A, B, t) if won else ""
        self.siege_log.append(rec + (terms, len(A["cities"]),
                                     len(B["cities"]),
                                     s["end"] - s["start"]))
        if terms == "tributary":
            # the defender sues for terms and pays tribute
            self.count("war_tributary")
            self.submit(w["dfn"], w["att"])
            self.war_close(self.wars.pop(k, None), "tributary")
            self.truce[k] = self.year + TRUCE_WAR
            w["submitted"] = True
            return "stop"
        if terms == "sack":
            # one sack a step: the army goes home with the loot
            self.sack(w, A, B, t)
            return "stop"
        if won:
            w["moved"] = w.get("moved", 0.0) + fe
            w["caps"] += 1
            if t == w.get("goal"):
                w["done"] = True
                self.count("war_goal_met")
            self.capture(w["att"], w["dfn"], t)
            if k not in self.wars:
                return "stop"
        else:
            A["cohesion"] *= 1 - SIEGE_COH * (1.5 - self.logi(A) / 1.5)
        return None

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
                             f"call of {self.pname(b)}; the alliance ends",
                             polities=[q, b])

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
        PD *= 1.4 * self.city_def(t) * (1.25 if t == D["capital"] else 1)
        PD *= 1 + DEV_WALL * self.dev(D["lin"])
        return PD

    def counteroffensive(self, k, w, A, B):
        """The defender B strikes back at the attacker A (two_sided):
        sieges in the slots its logistics allow, at A's cities it lost in
        this war first, nearest its capital first."""
        rng = self.R("war")
        R = B.get("strength", 0.0) / max(A.get("strength", 0.0), 1e-9)
        if rng.random() >= over(COUNTER_K * R * R / (1 + R * R),
                                self.dtp):
            return
        if not A["cities"]:
            # `camps`: the defender brings a camp attacker to battle
            self.camp_battle(k, w, B, A)
            return
        ns = 1 + int(LOG_SIEGE * self.logi(B))
        free = ns - sum(1 for s in w["on"] if s["side"] == "dfn")
        for _ in range(free):
            if not A["cities"] or A["ended"] is not None or \
                    k not in self.wars:
                break
            busy = {s["t"] for s in w["on"]}
            pool = [c for c in A["cities"] if c not in busy]
            if not pool:
                break
            lost = [c for c in pool
                    if w["dfn"] in self.cities[c]["owners"][:-1]]
            pool = lost or pool
            t = pool[int(np.argmin(gc_km(self.W.xyz, B["capital"],
                                         np.array(pool))))]
            PB = self.projected(B, t) * self.offense(B) * self.field(B)
            PA = self.defence_at(A, B, t) * self.garrison(A)
            pw = PB ** 2 / (PB ** 2 + PA ** 2 + 1e-9)
            if "war_odds" in self.on and pw < SIEGE_MIN:
                break               # too long odds: no siege
            if self.siege_start(k, w, "dfn", t, B, A) == "stop":
                break

    def camp_battle(self, k, w, X, Y):
        """`camps`: X brings camp polity Y to battle at its seat, at most
        once a step, at odds >= SIEGE_MIN: Y's strength there x
        CAMP_EVADE (it can melt away). Won: Y submits with chance (0.5 +
        X's dominance) / 2, else scatters (ends); the war ends. Lost: X
        loses cohesion as after a failed siege. Under `army` losses are
        as in a decided siege."""
        if w.get("battle_year") == self.year:
            return
        w["battle_year"] = self.year
        rng = self.R("war")
        t = Y["capital"]
        PX = self.projected(X, t) * self.offense(X) * self.field(X)
        PY = self.projected(Y, t) * CAMP_EVADE * self.garrison(Y)
        pw = PX ** 2 / (PX ** 2 + PY ** 2 + 1e-9)
        if "war_odds" in self.on and pw < SIEGE_MIN:
            return
        w["last_siege"] = self.year
        w["battles"] = w.get("battles", 0) + 1
        won = rng.random() < pw
        if "army" in self.on:
            self.army_loss(w, X, ARMY_WON if won else ARMY_LOST)
            self.army_loss(w, Y, ARMY_LOST if won else ARMY_WON)
        if not won:
            X["cohesion"] *= 1 - SIEGE_COH * (1.5 - self.logi(X) / 1.5)
            return
        x, y = X["id"], Y["id"]
        if y not in self.vassal and \
                rng.random() < (0.5 + self.eff(X, "dom")) / 2:
            self.count("camp_vassal")
            self.submit(y, x)
            self.war_close(self.wars.pop(k, None), "submitted")
            self.truce[k] = self.year + TRUCE_WAR
            w["submitted"] = True
        else:
            self.count("camp_scattered")
            self.war_close(self.wars.pop(k, None), "camp scattered")
            self.kill_polity(y, f"scattered by {self.pname(x)}", by=x,
                             code="scattered")

    def field(self, P):
        """`army`: the share of its full levy (ARMY_SHARE x its people)
        that state P has in the field, 0-1; 1 without the switch."""
        if "army" not in self.on:
            return 1.0
        full = ARMY_SHARE * P.get("pop", 0.0)
        return min(1.0, P.get("army", 0.0) / full) if full > 0 else 0.0

    def garrison(self, P):
        """`army`: what P's field army adds to the defence of its cities
        (walls and townsmen hold ARMY_GARRISON without one)."""
        if "army" not in self.on:
            return 1.0
        return ARMY_GARRISON + (1 - ARMY_GARRISON) * self.field(P)

    def army_dead(self, P, heads):
        """Records soldiers of state P killed (cause "battle")."""
        c = P["culture"]
        acc = self.deaths.get("battle")
        if acc is None:
            acc = self.deaths["battle"] = np.zeros(self.nP)
        acc[c] += heads
        self.ac_dead[c] += heads

    def army_loss(self, w, P, share):
        """State P loses `share` of its army in a decided siege; the war
        keeps the count for exhaustion."""
        a = P.get("army", 0.0)
        if a <= 0 or share <= 0:
            return
        heads = a * share
        P["army"] = a - heads
        self.army_dead(P, heads)
        ls = w.setdefault("lost", {})
        ls[P["id"]] = ls.get(P["id"], 0.0) + heads

    def army_step(self, at):
        """`army`: states at war (set `at`) raise toward ARMY_SHARE of
        their people, closing dtp / ARMY_RAISE of the gap, from their own
        people's cells; the rest send their soldiers home to those cells.
        An ended state's army is lost. Sets army_x, the share of each
        own-people cell's capacity the army eats (read by Kf)."""
        N, n = self.W.N, self.next_pid
        pol, pc = self.cell_pol, self.ptab()[1]
        own = (pol >= 0) & (self.cul >= 0) & \
            (self.cul == pc[np.maximum(pol, 0)])
        oc = np.nonzero(own)[0]
        opop = np.bincount(pol[oc], weights=self.pop[oc], minlength=n)
        rate = min(1.0, self.dtp / ARMY_RAISE)
        delta = np.zeros(n)
        share = np.zeros(n)
        for pid, P in self.polities.items():
            a = P.get("army", 0.0)
            if P["ended"] is not None:
                if a > 0:
                    self.army_dead(P, a)
                    P["army"] = 0.0
                continue
            want = ARMY_SHARE * P.get("pop", 0.0) if pid in at else 0.0
            if want <= 0 and a <= 0:
                continue
            d = (want - a) * rate if want > a else want - a
            if d > 0:
                d = min(d, 0.5 * opop[pid])
            elif opop[pid] <= 0:
                # no home cells left: the soldiers stay under arms
                d = 0.0
            P["army"] = a + d
            delta[pid] = d
            if P["army"] > 0:
                share[pid] = P["army"] / max(P.get("K_own", 0.0), 1.0)
        f = delta[pol[oc]] / np.maximum(opop[pol[oc]], 1e-9)
        # raising takes a share of every own cell; going home returns
        # the soldiers in proportion to the cells' people
        self.pop[oc] *= 1 - np.minimum(f, 0.5)
        self.army_x = np.zeros(N)
        self.army_x[oc] = np.minimum(ARMY_X_MAX, share[pol[oc]])

    def ravage(self, w, A, B, t):
        """`war_odds`: A, too weak to besiege city t, lays waste B's land
        around it, as a raid does: RAVAGE_K x A's violence of the people
        there die (less for hardy peoples), and as many improvements fall
        as in a raid."""
        h = np.nonzero((self.cell_city == t) & (self.cell_pol == B["id"]) &
                       (self.cul >= 0))[0]
        if not len(h):
            return
        dmg = min(0.6, RAVAGE_K * self.eff(A, "viol"))
        b_pop, b_mpop = self.pop[h], self.mpop[h]
        self.pop[h] *= 1 - dmg * self.hardy(h)
        self.mpop[h] *= 1 - dmg
        self.dead("ravage", h, b_pop - self.pop[h])
        self.dead("ravage", h, b_mpop - self.mpop[h], minority=True)
        self.rows_scale(h, 1 - dmg, "ravage")
        self.imp[h] *= 1 - 0.3 * dmg
        self.raided[h] = 1
        self.shock(t, "ravage")
        w["ravages"] = w.get("ravages", 0) + 1
        self.count("war_ravage")

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
                 sacks=w.get("sacks", 0), ravages=w.get("ravages", 0),
                 battles=w.get("battles", 0))

    def set_goal(self, w, A, B, gains):
        """The goal of a motivated war: its largest motive."""
        kind = max(gains, key=gains.get)
        goal = B["capital"]
        if kind == "irredentism":
            lost = [c for c in B["cities"] if A["id"] in
                    self.cities[c]["owners"][:-1]]
            if lost:
                goal = lost[0]
        elif kind in ("land", "prey", "enmity") and B["cities"]:
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
                     f"{self.place(t)} to {self.pname(att)}",
                     cell=t, polities=[dfn, att])
        if not B["cities"]:
            self.kill_polity(dfn, f"ceded its last city to "
                             f"{self.pname(att)}", by=att, code="ceded")
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
                         f"of {GUARD_NAMES[g]} from {self.pname(dfn)}",
                         polities=[att, dfn])
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
        v = self.eff(A, "viol")
        self.lost_rows(t, b_pop - self.pop[t], v, "sack")
        self.lost_rows(self.W.N + t, b_mpop - self.mpop[t], v, "sack")
        self.rows_scale(t, 1 - (0.1 + 0.4 * v) * spare, "sack", v)
        A["cohesion"] = min(1, A["cohesion"] + 0.03)
        if rec["culture"] != ca and self.R("war").random() < \
                (1 - self.eff(A, "tol")) * self.eff(A, "viol") * \
                (1 - self.eff(A, "dom")):
            hint = (self.cell_city == t) & (self.cul == rec["culture"])
            hc = np.nonzero(hint)[0]
            b_pop = self.pop[hc]
            self.pop[hint] *= 1 - 0.85 * self.hardy(np.nonzero(hint)[0])
            v = self.eff(A, "viol")
            self.lost_rows(hc, b_pop - self.pop[hc], v, "clearance")
            b_pop = self.pop[t]
            self.pop[t] *= 1 - 0.7 * self.hardy(t)
            self.lost_rows(t, b_pop - self.pop[t], v, "clearance")
            self.shock(t, "clearance")
            self.imp[hint] *= 0.5
            if len(A["cities"]) + len(B["cities"]) >= 5:
                self.log("clearance", f"{self.pname(att)} clears "
                         f"{self.keys[rec['culture']]} from the city at "
                         f"{self.place(t)}",
                         cell=t, polities=[att],
                         peoples=[self.keys[rec['culture']]],
                         cities=[rec['id']])
        if rec["culture"] != ca:
            # a garrison and settlers of the conqueror's people stay on
            self.add_minority([t], ca, La, MIN_GARRISON * self.pop[t] *
                              self.peat[rec["culture"]] / self.peat[ca])
            if "conquest_settle" in self.on:
                self.conquest_settle(A, t, rec["culture"])
        if was_cap:
            B["cohesion"] *= 0.6
            self.spike(dfn)
            if len(B["cities"]) + 1 >= 4:
                self.log("conquest", f"{self.pname(att)} takes the capital "
                         f"of {self.pname(dfn)} at {self.place(t)}",
                         cell=t, polities=[att, dfn], cities=[rec['id']])
            if not B["cities"]:
                self.kill_polity(dfn, f"conquered by {self.pname(att)}",
                                 by=att, code="conquered")
            elif B["culture"] == ca and len(B["cities"]) <= 3:
                for c in list(B["cities"]):
                    self.cities[c]["polity"] = att
                    self.cities[c]["owners"].append(att)
                    A["cities"].add(c)
                B["cities"] = set()
                self.kill_polity(dfn, f"absorbed by {self.pname(att)}",
                                 by=att, code="absorbed")
            elif self.R("war").random() < SHATTER_P:
                rest = list(B["cities"])
                B["cities"] = set()
                self.kill_polity(dfn, "shattered after its capital fell",
                                 code="shattered")
                for c in rest:
                    Lc = self.lin[c] if self.lin[c] >= 0 else B["lin"]
                    self.cities[c]["polity"] = self.new_polity(
                        Lc, c, 0.5, parent=dfn, origin="shatter")
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
                         f"of {GUARD_NAMES[g]} from {self.pname(dfn)}",
                         polities=[att, dfn])
        self.turmoil(B, ADM_LOSS / max(len(B["cities"]), 1))
        spare = 1 - DOM_SPARE * self.eff(A, "dom")
        b_pop, b_mpop = self.pop[t], self.mpop[t]
        self.pop[t] *= 1 - (0.1 + 0.4 * self.eff(A, "viol")) * spare * \
            self.hardy(t)
        self.mpop[t] *= 1 - (0.1 + 0.4 * self.eff(A, "viol")) * spare
        v = self.eff(A, "viol")
        self.lost_rows(t, b_pop - self.pop[t], v, "sack")
        self.lost_rows(self.W.N + t, b_mpop - self.mpop[t], v, "sack")
        self.rows_scale(t, 1 - (0.1 + 0.4 * v) * spare, "sack", v)
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
                     f"{self.place(t)} and leaves it to {self.pname(dfn)}",
                     cell=t, polities=[att, dfn])

    def fort_toll(self, P, t):
        """`fortress`: a state besieging a fortress people's city loses
        FORT_SIEGE x f x the city's people, across its cells."""
        if "fortress" not in self.on or t not in self.cities:
            return
        f = self.pfort[self.cities[t]["culture"]]
        if f <= 0:
            return
        if "army" in self.on:
            # `army`: the besiegers who fall are soldiers
            heads = min(P.get("army", 0.0), FORT_SIEGE * f * self.pop[t])
            if heads > 0:
                P["army"] -= heads
                self.army_dead(P, heads)
                self.count("fortress_toll")
                self.count("fortress_heads", int(heads))
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
