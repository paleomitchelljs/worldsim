"""Carrying capacity, climate, land and disasters."""
import math
import numpy as np
from scipy import ndimage, signal

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class LandMixin:
    def prepare_capacity(self):
        self.Kcell = self.drought.copy()
        self.climate()
        self.Kcap[:] = np.inf
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            boost = np.array([1.5 + 2.0 * min(1.5, self.polities[
                self.cities[c]["polity"]]["trade"])
                if self.cities[c]["polity"] in self.polities else 1.5
                for c in cc])
            rl = np.array([self.polities[self.cities[c]["polity"]]["lin"]
                           if self.cities[c]["polity"] in self.polities
                           else max(self.lin[c], 0) for c in cc])
            dv = 1 + DEV_CITY * self.dev(rl)
            boost = boost * dv
            # records (urban population): the base boost, without trade
            self.cb0[:] = 1.0
            self.cb0[cc] = 1.5 * dv
            if self.ff_on:
                # `food_flow`: trade food arrives as a flow instead
                boost = self.cb0[cc]
            self.cboost[:] = 1.0
            self.cboost[cc] = boost
            self.Kcell[cc] *= boost
            adm = np.array([self.admin[self.polities[
                self.cities[c]["polity"]]["lin"]]
                if self.cities[c]["polity"] in self.polities
                else self.admin[max(self.lin[c], 0)] for c in cc])
            if CITY_CAP:
                self.Kcap[cc] = CITY_POP * (CITY_CAP0 + CITY_CAP1 * adm ** 2)
        self.waste = np.minimum(1.0, self.waste + DT / WASTE_YEARS)
        self.Kcell *= self.waste

    def dev(self, L):
        """Development (0-1) of lineages L: their technologies' mean."""
        parts = [np.clip((self.agri[L] - 0.25) / 0.75, 0, 1),
                 np.clip(self.metal[L] / 3.5, 0, 1), self.sail[L],
                 np.clip((self.fishing[L] - FISH_START) / (1 - FISH_START),
                         0, 1), self.admin[L]]
        parts.append(self.craft[L])
        if len(self.h_cell):
            parts.append(self.domlv[L].max(-1))
        return sum(parts) / len(parts)

    def adapt(self, L):
        """0..1: how far farming and metallurgy free a lineage from its
        preferred biomes."""
        return 0.5 * np.clip((self.agri[L] - 0.25) / 0.75, 0, 1) + \
            0.5 * np.clip(self.metal[L] / 2.6, 0, 1)

    def ltab(self):
        """Per-lineage tables for K2, (MAXL, biomes) each, rows below nL
        valid: effective biome affinity (fit), and the best crop and animal
        package weights the lineage holds in each biome. A full rebuild
        when lver moves (every write to agri, metal or domlv of an existing
        lineage bumps it; Laff and Lbest are set only by new_lineage), else
        only the rows of lineages added since."""
        n0 = 0 if self._ltab_ver != self.lver else self._ltab_n
        if n0 < self.nL:
            if n0 == 0:
                nb = len(BIOMES)
                self._ltab = (np.ones((MAXL, nb)), np.zeros((MAXL, nb)),
                              np.zeros((MAXL, nb)))
            fit, cr, an = self._ltab
            L = np.arange(n0, self.nL)
            best = self.Lbest[L][:, None]
            k = BIOME_K * (1 - BIOME_ADAPT * self.adapt(L))
            fit[L] = best * (self.Laff[L] / best) ** k[:, None]
            lv = self.domlv[L][:, :, None]
            cr[L] = (lv * self.h_wc[None]).max(1)
            an[L] = (lv * self.h_wa[None]).max(1)
            self._ltab_ver, self._ltab_n = self.lver, self.nL
        return self._ltab

    def Kf(self, L, j, parts=False, raw=False):
        """Carrying capacity of cells j for lineages L (broadcast): the
        better of farming (blended with foraging) and, if on, herding.
        parts: also return K2's (farming K, herding K). raw: before
        what the state takes and sends (`dominion`)."""
        Kc, Kh = self.K2(L, j)
        K = Kc if Kh is None else np.maximum(Kc, Kh)
        if self.dom_on and not raw and self.ff_on:
            # `food_flow`: the ruling people pay rent and tax outside the
            # cities, others rent and tribute; the ruling people receive
            # the state's take at its capital, a city's people the rent,
            # local spending and trade food that reach their city
            c = self.Lpeople[L]
            own = c == self.rul_c[j]
            x = np.where(own, self.ff_xo[j], self.ext_x[j])
            if self.td_on:
                # `trade_debit`: the cell's lineages sell part of their
                # surplus, each in proportion to its capacity
                x = x + self.tr_x[j]
            K = K * (1 - x) + \
                (own * self.ext_in[j] + (c == self.city_c[j]) *
                 self.loc_in[j]) / self.peat[c]
        elif self.dom_on and not raw:
            # `dominion`: subjects lose the state's take; the ruling
            # people gain what reaches them
            c = self.Lpeople[L]
            K = np.where(c == self.rul_c[j],
                         K + self.ext_in[j] / self.peat[c],
                         K * (1 - self.ext_x[j]))
        return (K, Kc, Kh) if parts else K

    def comp_w(self, L, j):
        """`dominion`: competitive weight of lineages L in cells j, from
        technology and, for the state's ruling people, the state's
        establishment."""
        tech = (self.agri[L] + self.bronze[L] + self.iron[L] +
                self.steel[L]) / 4
        est = np.where(self.Lpeople[L] == self.rul_c[j], self.rul_est[j], 0)
        return (1 + SH_TECH * tech) * (1 + SH_STATE * est)

    def lterms(self, L):
        """K2's factors that depend on the lineage alone: agri, tools, sod
        factor, food per head, fishing, wetland skill, development and
        herding share. For a long L (one entry per cell) they are worked
        out once per lineage and gathered, which gives the same values."""
        big = np.ndim(L) > 0 and np.size(L) > self.nL
        X = np.arange(self.nL) if big else L
        a = self.agri[X]
        tools = 1 + TOOLS[0] * self.iron[X] + TOOLS[1] * self.steel[X]
        sf = np.where(self.iron[X], 1.0,
                      np.where(self.bronze[X], SOD_BR, SOD0))
        c = self.Lpeople[X]
        eat = self.peat[c]
        fk = FISH0 + FISH1 * self.fishing[X]
        pw = WET_K * self.pwet[c]
        dv = 1 + DEV_K * self.dev(X)
        h = np.clip((a - HERD_AGRI[0]) / (HERD_AGRI[1] - HERD_AGRI[0]), 0, 1)
        out = (a, tools, sf, eat, fk, pw, dv, h)
        return tuple(v[L] for v in out) if big else out

    def K2(self, L, j):
        """(farming K, herding K or None) of cells j for lineages L."""
        W = self.W
        a, tools, sf, eat, fk, pw, dv, h = self.lterms(L)
        cm = self.cm
        rain = W.rain_ws[j]
        forage = W.forage[j] * cm[2, j]
        herd = W.herd[j] * cm[3, j]
        # canals carry irrigation; clearance and terraces help rain-fed
        cm0, cm1 = cm[0, j], cm[1, j]
        imp = self.imp[j]
        farm = rain * cm0 * (1 + IMP_RAIN * imp) + \
            W.irr_w[j] * cm1 * (IMP_IRR0 + (1 - IMP_IRR0) * imp) + \
            W.fish[j]
        rainc = rain * cm0 * (1 + IMP_RAIN * imp)
        # grassland sod resists the plough until bronze, then iron
        grass = W.biome[j] == BIOMES.index("Grassland")
        farm = farm - grass * (1 - sf) * rainc
        farm = farm * self.land[j]
        farm = farm * (1 - SALT_MAX * self.salt[j] * W.irr_share[j])
        # what there is to farm and herd: the packages a lineage holds
        b = W.biome[j]
        FIT, CR, AN = self.ltab()
        cr, an = CR[L, b], AN[L, b]
        farm = farm * (DOM_FLOOR + (1 - DOM_FLOOR) * cr)
        herd = herd * (DOM_HFLOOR + (1 - DOM_HFLOOR) * an)
        dens = forage * (1 - a) + farm * a * tools
        fit = FIT[L, b]
        # near a biome edge, a dry or wet spell moves the edge
        f = self.eco_f[j]
        fit = fit + f * (FIT[L, np.maximum(self.eco_tgt[j], 0)] - fit)
        coast = 1 + fk * W.water[j]
        if self.pwet.any():
            fit = fit * (1 + pw * W.wet[j])
        cap = self.Kcap[j] / eat
        coast = coast * dv
        Kc = np.minimum(W.area[j] * dens * fit * self.Kcell[j] * coast / eat,
                        cap)
        # herders forage too; animals make the difference
        hd = forage * (1 - h) + herd * h
        Kh = np.minimum(W.area[j] * hd * fit * self.Kcell[j] * coast / eat,
                        cap)
        return Kc, Kh

    def climate_setup(self):
        """Fixed patterns, their time series for the whole run, and the
        abrupt events, all from the climate's own random stream."""
        W, rng = self.W, self.R("climate")
        span = max(self.years, CLIM_YEARS)     # not the run's own length
        nt = span // DT + 2

        def series():
            out = np.zeros(nt)
            for kind, P, tau, share in CLIM_PARTS:
                burn = int(3 * max(tau, P, 50) / DT) + 10
                e = rng.normal(size=nt + burn)
                if kind == "white":
                    x = e
                elif kind == "red":
                    x = signal.lfilter([1], [1, -math.exp(-DT / tau)], e)
                else:
                    r = math.exp(-DT / tau)
                    x = signal.lfilter([1], [1, -2 * r * math.cos(
                        2 * math.pi * DT / P), r * r], e)
                x = x[burn:]
                out += math.sqrt(share) * x / x.std()
            return out / out.std()

        def std(v):
            return (v - v.mean()) / max(v.std(), 1e-9)

        def field(sigma):
            g = ndimage.gaussian_filter(rng.normal(size=(NY, NX)), sigma,
                                        mode="wrap")
            return std(g[W.row, W.col])

        pats = [np.ones(W.N), std(np.cos(4 * np.radians(W.lat))),
                std(W.dcoast)] + [field(CLIM_REG_SIGMA)
                                  for _ in range(CLIM_REGIONAL)]
        w = np.array([CLIM_W["world"], CLIM_W["latitude"], CLIM_W["inland"]]
                     + [CLIM_W["regional"]] * CLIM_REGIONAL)
        norm = math.sqrt((w ** 2).sum() + CLIM_W["local"] ** 2)
        self.clim_pat = np.array(pats) * (w / norm)[:, None]
        self.clim_loc = CLIM_W["local"] / norm
        self.clim_ser = np.array([series() for _ in pats])
        # abrupt dry events: a smooth regional footprint (or, one time in
        # four, the whole world), setting in fast and lifting slowly
        t = rng.exponential(1 / ABRUPT_RATE)
        while t < span:
            if rng.random() < 0.25:
                fp, where = np.ones(W.N), "the whole world"
            else:
                g = np.clip(field(25), 0, None)
                fp = g / max(g.max(), 1e-9)
                k = int(np.argmax(fp))
                where = f"lands around {W.lon[k]:+.0f},{W.lat[k]:+.0f}"
            self.events_abrupt.append(dict(
                start=t, years=rng.uniform(*ABRUPT_YEARS),
                amp=rng.uniform(*ABRUPT_AMP), fp=fp, where=where,
                logged=False, ended=False))
            t += rng.exponential(1 / ABRUPT_RATE)

    def local_field(self, rng):
        """The climate's local field at the land cells: white noise on a
        grid CLIM_LOCAL_COARSE times coarser on each axis, smoothed with
        the same sigma in km (CLIM_LOCAL_SIGMA fine cells), and read off
        bilinearly (wrapping in longitude). The smoothing costs about a
        sixteenth of doing it on the full grid; the field's scale is the
        same."""
        W, f = self.W, CLIM_LOCAL_COARSE
        ny, nx = NY // f, NX // f
        g = ndimage.gaussian_filter(rng.normal(size=(ny, nx)),
                                    CLIM_LOCAL_SIGMA / f, mode="wrap")
        if f == 1:
            return g[W.row, W.col]
        # fine cell centres in coarse cell coordinates
        y = np.clip((W.row + 0.5) / f - 0.5, 0, ny - 1)
        x = (W.col + 0.5) / f - 0.5
        y0, x0 = np.minimum(y.astype(int), ny - 2), np.floor(x).astype(int)
        wy, wx = y - y0, x - x0
        x0, x1 = x0 % nx, (x0 + 1) % nx
        return (1 - wy) * ((1 - wx) * g[y0, x0] + wx * g[y0, x1]) + \
            wy * ((1 - wx) * g[y0 + 1, x0] + wx * g[y0 + 1, x1])

    def climate(self):
        """This tick's moisture anomaly and what it does: rain-fed yields,
        foraging and herding, river discharge (from the whole catchment),
        biome edges, granaries, and rivers changing course."""
        W, rng = self.W, self.R("climate")
        tick = min(self.tick, self.clim_ser.shape[1] - 1)
        m = self.clim_pat.T @ self.clim_ser[:, tick]
        g = self.local_field(rng)
        m += self.clim_loc * g / max(g.std(), 1e-9)
        for ev in self.events_abrupt:
            dt = self.year - ev["start"]
            if dt < 0 or ev["ended"]:
                continue
            if dt > ev["years"] + ABRUPT_RAMP[1]:
                ev["ended"] = True
                self.log("climate", f"the long dry spell over {ev['where']}"
                         " lifts")
                continue
            env = min(1, dt / ABRUPT_RAMP[0]) if dt <= ev["years"] else \
                1 - (dt - ev["years"]) / ABRUPT_RAMP[1]
            m -= ev["amp"] * env * ev["fp"]
            if not ev["logged"]:
                ev["logged"] = True
                self.log("climate", f"a long dry spell sets in over "
                         f"{ev['where']} (~{ev['years']:.0f} yrs)",
                         n=ev['years'])
        self.moist = m
        pa = np.clip((PREC_SD[0] + PREC_SD[1] * W.dryness) * m, -0.7, 0.7)
        el = 1 + W.dryness
        rain = np.clip(1 + el * pa, 0.1, 1.6)
        forage = np.clip(1 + 0.8 * el * pa, 0.2, 1.5)
        Qt = W.accumulate(W.yield_ * np.clip(1 + RUNOFF_EL * pa, 0.05, None))
        ratio = Qt / np.maximum(W.Q, 1e-9)
        irr = np.sqrt(np.clip(ratio, 0.2, 2.0))
        # biome edges move: blend toward the drier or wetter neighbour biome
        dry = m < 0
        tgt = np.where(dry, W.eco_dry, W.eco_wet)
        f = np.clip(ECO_W * (np.abs(m) - 0.5), 0, ECO_MAX) * \
            np.where(dry, W.eco_dry_prox, W.eco_wet_prox) * (tgt >= 0)
        self.eco_tgt, self.eco_f = tgt, f
        b, t2 = W.biome, np.maximum(tgt, 0)
        mix = []
        for table in (FARM, FORAGE, HERD):
            v = np.array([table[x] for x in BIOMES])
            mix.append(1 - f + f * v[t2] / v[b])
        raw = np.array([rain * mix[0], irr, forage * mix[1], forage * mix[2]])
        # granaries: states smooth short swings, more so with good offices
        pl = self.ptab()[0]
        rl = np.where(self.cell_pol >= 0, pl[np.maximum(self.cell_pol, 0)],
                      -1)
        tau = np.where(rl >= 0, STORE_YEARS * self.admin[np.maximum(rl, 0)],
                       0)
        tau = tau * (0.5 + self.pati[np.maximum(rl, 0)])
        alpha = DT / (DT + tau)
        self.cm += alpha * (raw - self.cm)
        # a great drought, for the log (records only): 30%+ of people
        # below -1.5 sd, at least 200 years after the last one logged
        # (U 2026-11-01: about 10 per run; was 8% below -2 sd, 50 years,
        # which logged 42-65 per run)
        dry_pop = self.pop[m < -1.5].sum()
        if dry_pop > 0.3 * max(self.pop.sum(), 1) and dry_pop > 1e6 and \
                self.year - self._great_dry >= 200:
            self._great_dry = self.year
            k = int(np.argmin(np.where(self.pop > 0, m, 9)))
            self.log("drought", f"great drought, worst near {self.place(k)}"
                     f" ({dry_pop / 1e6:.1f}M people under drought)",
                     cell=k, n=dry_pop)
        # rivers change course, mostly in high water
        prone = np.nonzero(W.river & W.alluvial & (W.relief < 0.3) &
                           (W.elev < 0.3) & (W.Q > 1000))[0]
        if len(prone):
            pr = DT * AVULSE_RATE * np.clip(ratio[prone], 0.3, 3) ** 2
            for i in prone[rng.random(len(prone)) < pr][:3]:
                if W.river[i]:
                    self.avulse(int(i))

    def avulse(self, i):
        """The river at cell i breaks its banks and takes a new course to a
        lower (or nearly as low) neighbour, or straight to the sea."""
        W, rng = self.W, self.R("climate")
        old = int(W.flow[i])
        cand, el = [], []
        for k in range(8):
            j = int(W.nb[i, k])
            if j < 0 or j == old or W.flow[j] == i or W.lake[j] or \
                    W.elev[j] > W.elev[i] + AVULSE_TOL:
                continue
            x, ok = j, True
            for _ in range(5000):           # no loops back through i
                if x == i:
                    ok = False
                    break
                x = int(W.flow[x])
                if x < 0:
                    break
            if ok:
                cand.append(j)
                el.append(W.elev[j])
        if W.coastal[i] and old >= 0:
            cand.append(-1)
            el.append(0.0)
        if not cand:
            return
        el = np.array(el)
        wt = np.exp(-(el - el.min()) / 0.01)
        j = int(cand[rng.choice(len(cand), p=wt / wt.sum())])
        before = W.river.copy()
        W.reroute(i, j)
        self.n_avulsions += 1
        lost = np.nonzero(before & ~W.river)[0]
        hit = [c for c in lost if c in self.cities]
        self.shock(hit, "river lost")
        if hit or len(lost) >= 5:
            names = ", ".join(self.place(c) for c in hit[:4])
            self.log("river", f"the river at {self.place(i)} changes course"
                     f" ({len(lost)} cells lose it"
                     + (f"; cities left dry: {names}" if hit else "") + ")",
                     cell=i, cities=[self.cities[c]['id'] for c in hit],
                     n=len(lost))

    def grow(self):
        occ = np.nonzero(self.lin >= 0)[0]
        L = self.lin[occ]
        K, Kc, Kh = self.Kf(L, occ, parts=True)
        k = np.maximum(K, 1e-3)
        # a minority eats from the same land
        mo = occ[self.mlin[occ] >= 0]
        if len(mo):
            Lm = self.mlin[mo]
            Km = self.Kf(Lm, mo)
            km = np.maximum(MIN_CAP * Km, 1e-3)
            coef = np.ones(len(mo))
            if self.dom_on:
                # `dominion`: the two peoples share the land, each held
                # back by the other in proportion to their weights
                full = ~self.mcap[mo]
                wm, wM = self.comp_w(Lm, mo), self.comp_w(self.lin[mo], mo)
                fM = self.pop[mo] * self.peat[self.cul[mo]]
                km = np.where(full, np.maximum(
                    Km - SHARE_ALPHA * wM / wm * fM /
                    self.peat[self.mcul[mo]], 1e-3), km)
                coef = np.where(full, SHARE_ALPHA * wm / wM, 1.0)
            pm = self.mpop[mo]
            rm = self.Lr[Lm]
            am = 0.6 + 0.4 * self.agri[Lm]
            pm0 = logistic(pm, km, rm * am)     # records: without dragons
            rm = rm - self.dragon_pen(mo)
            self.mpop[mo] = logistic(pm, km, rm * am)
            self.dead("hunger", mo, np.maximum(pm - pm0, 0), minority=True)
            self.forgone(mo, np.maximum(pm0 - self.mpop[mo], 0),
                         minority=True)
            food = np.zeros(self.W.N)
            food[mo] = coef * self.mpop[mo] * self.peat[self.mcul[mo]]
            k = np.maximum(k - food[occ] / self.peat[self.cul[occ]], 1e-3)
        k = k * self.pref(L, occ)
        p = self.pop[occ]
        # frontier fecundity: thinly settled land grows fastest
        front = 1 + 1.5 * np.clip(1 - 2 * p / k, 0, 1)
        r = self.Lr[L] * (0.6 + 0.4 * self.agri[L]) * front
        # dragons: a cut in the growth rate, the same for everyone;
        # only fast breeders stay above zero under a dragon
        pen = self.dragon_pen(occ)
        rb = self.Lr[L] - pen
        r_d = rb * (0.6 + 0.4 * self.agri[L]) * np.where(rb > 0, front, 1)
        e0 = np.exp(-r * DT)
        p0 = k * p / (p + (k - p) * e0)
        r = r_d
        self.pop[occ] = logistic(p, k, r)
        lost = np.maximum(p0 - self.pop[occ], 0)
        self.dragon_kills = np.bincount(self.cul[occ], weights=lost,
                                        minlength=self.nP)
        # records: a crowd above what the land feeds dies back; what
        # dragons cut is growth that did not happen, not deaths
        self.dead("hunger", occ, np.maximum(p - p0, 0))
        self.forgone(occ, lost)
        if self.cities:
            hc = occ[lost > 0.05 * np.maximum(p0, 1)]
            self.shock(hc[np.isin(hc, list(self.cities))], "dragon")
        self.feud(occ, L)
        # capacity does not depend on population: grow's is still current
        self.land_use(occ, L, Kc, Kh)

    def famine(self):
        """When a cell holds more people than its land now feeds, part of
        the surplus leaves: up to FAMINE_RANGE cells away, to empty land
        or kin with room. The rest dies back as the land allows."""
        W, rng = self.W, self.R("famine")
        occ = np.nonzero(self.lin >= 0)[0]
        K = self.Kf(self.lin[occ], occ)
        ex = self.pop[occ] - 1.05 * K
        h = ex > np.maximum(FOUND_MIN, 0.05 * K)
        src, ex = occ[h], ex[h]
        self.famine_movers = 0.0
        if not len(src):
            return
        o = np.argsort(-ex)[:FAMINE_MAX]
        src, ex = src[o], ex[o]
        n, R = len(src), FAMINE_RANGE
        dr = rng.integers(-R, R + 1, (n, 16))
        dc = rng.integers(-R, R + 1, (n, 16))
        r2 = W.row[src][:, None] + dr
        ok = (r2 >= 0) & (r2 < NY)
        t = W.idx2[np.clip(r2, 0, NY - 1), (W.col[src][:, None] + dc) % NX]
        ok &= t >= 0
        t = np.where(ok, t, src[:, None])
        L = self.lin[src][:, None] * np.ones((1, 16), int)
        ok &= W.landmass[t] == W.landmass[src][:, None]
        ok &= (self.lin[t] < 0) | (self.lin[t] == L)
        Kt = self.Kf(L, t)
        room = np.where(ok, Kt - self.pop[t], 0) * \
            np.where(self.lin[t] < 0, self.colon(t, L), 1)
        k = np.argmax(room, 1)
        best = t[np.arange(n), k]
        rb = room[np.arange(n), k]
        go = rb > FOUND_MIN
        src, best, ex, rb = src[go], best[go], ex[go], rb[go]
        _, first = np.unique(best, return_index=True)   # one band per target
        src, best = src[first], best[first]
        mv = np.minimum(FAMINE_MOVE * ex[first], rb[first])
        self.pop[src] -= mv
        new = self.lin[best] < 0
        self.lin[best[new]] = self.lin[src[new]]
        self.cul[best[new]] = self.cul[src[new]]
        self.pop[best] += mv
        self.famine_movers = float(mv.sum())
        self.hard[src] = 1

    def land_use(self, occ, L, Kc=None, Kh=None):
        """Herding or farming per cell, and the land condition that farming
        wears down (salinization fastest on irrigated land). Kc, Kh: K2 of
        (L, occ), if already computed."""
        W = self.W
        if Kc is None:
            Kc, Kh = self.K2(L, occ)
        h = np.clip((self.agri[L] - HERD_AGRI[0]) /
                    (HERD_AGRI[1] - HERD_AGRI[0]), 0, 1)
        self.herding[:] = False
        self.herding[occ] = (Kh > Kc) & (h > 0)
        inten = np.zeros(W.N)
        farmed = ~self.herding[occ]
        inten[occ] = farmed * self.agri[L] * \
            np.clip(self.pop[occ] / np.maximum(Kc, 1e-3), 0, 1)
        # wear is proportional to what is left; recovery (fallow,
        # flushing) runs regardless, so each cell settles at
        # REC / (REC + DEG x intensity x (1 + IRR x irrigated))
        deg = LAND_DEG * inten * (1 + LAND_IRR * W.irr_share) * self.land
        deg[occ] *= 1.5 - self.pati[L]
        rec = LAND_REC * (1 - self.land)
        self.land = np.clip(self.land + DT * (rec - deg), LAND_MIN, 1)
        # irrigation brings salt up; fallow and abandonment leach it
        it = np.zeros(W.N)
        it[occ] = ~self.herding[occ] * self.agri[L] * \
            np.clip(self.pop[occ] / np.maximum(Kc, 1e-3), 0, 1)
        gain = SALT_GAIN * it * W.irr_share * (1 - self.salt)
        gain[occ] *= 1.5 - self.pati[L]
        self.salt = np.clip(self.salt + DT * (
            gain - SALT_REC * (1 - it) * self.salt), 0, 1)
        # farmers build; capable states build faster; unused works
        # silt up and fall in
        pl = self.ptab()[0]
        rl = pl[np.maximum(self.cell_pol[occ], 0)]
        adm = np.where((self.cell_pol[occ] >= 0) & (rl >= 0),
                       self.admin[np.maximum(rl, 0)], 0)
        use = np.zeros(W.N)
        use[occ] = ~self.herding[occ] * self.agri[L] * \
            np.clip(self.pop[occ] / np.maximum(Kc, 1e-3), 0, 1)
        build = np.zeros(W.N)
        build[occ] = IMP_BUILD * use[occ] * (0.5 + adm)
        build[occ] *= 0.5 + self.pati[L]
        self.imp += DT * (build * (1 - self.imp) -
                          IMP_DECAY * (1 - use) * self.imp)
        np.clip(self.imp, 0, 1, out=self.imp)

    def disasters(self):
        rng = self.R("disasters")
        self.drought += (1 - self.drought) * over(DROUGHT_REC)
        self.imm *= math.exp(-IMM_DECAY * DT)
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            big = cc[self.pop[cc] > 5 * self.pcity[np.maximum(
                self.cul[cc], 0)]]
            self.imm[big] = np.maximum(self.imm[big], IMM_ENDEMIC)
        urban = sum(self.pop[c] * (self.peat[self.cul[c]] if self.cul[c] >= 0 else 1)
                    for c in self.cities)
        if self.cities and self.year >= getattr(self, "_plague_next", 0) \
                and rng.random() < DT * PLAGUE_P * min(1, urban / 3e6):
            self._plague_next = self.year + PLAGUE_GAP
            cc = np.fromiter(self.cities.keys(), int)
            wt = self.pop[cc]
            o = int(rng.choice(cc, p=wt / wt.sum()))
            start = self.cities[o]["polity"]
            if start not in self.polities:
                return
            host = int(self.cul[o])
            hit = {start}
            frontier = [start]
            for _ in range(4):
                nxt = []
                for x in frontier:
                    for k in self.adj:
                        if x in k:
                            y = k[1] if k[0] == x else k[0]
                            if y in hit:
                                continue
                            pr = 0.25 + 0.6 * self.ties.get(k, 0)
                            if self.polities[y]["culture"] != host:
                                pr *= PLAGUE_CROSS + 0.4
                            if rng.random() < pr:
                                hit.add(y)
                                nxt.append(y)
                frontier = nxt
            mort = rng.uniform(0.15, 0.35)
            mask = np.isin(self.cell_pol, list(hit))
            self.hard[mask] = 1
            for x in hit:
                self.shock(list(self.polities[x]["cities"]), "plague")
                self.spike(x)
            # the host people dies at full rate, others at a fraction;
            # survivors of a recent plague, and the people of large
            # cities where it is endemic, are partly immune
            f = mort * (1 - IMM_PROTECT * self.imm) * mask
            fm = f * np.where(self.mcul == host, 1, PLAGUE_CROSS)
            f = f * np.where(self.cul == host, 1, PLAGUE_CROSS)
            dead = (self.pop * f).sum() + (self.mpop * fm).sum()
            b_pop, b_mpop = self.pop.copy(), self.mpop.copy()
            self.pop *= 1 - f
            self.mpop *= 1 - fm
            for x in hit:
                for c in self.polities[x]["cities"]:
                    self.pop[c] *= 1 - 0.3 * f[c]
            self.dead("plague", None, b_pop - self.pop)
            self.dead("plague", None, b_mpop - self.mpop, minority=True)
            self.imm[mask] = np.maximum(self.imm[mask], IMM_HIT)
            if dead > 2e5:
                self.log("plague", f"plague from {self.place(o)} through "
                         f"{len(hit)} states, ~{dead/1e6:.2f}M dead"
                         f" (host: {self.keys[host]})",
                         cell=o, polities=sorted(hit),
                         peoples=[self.keys[host]], n=dead)
