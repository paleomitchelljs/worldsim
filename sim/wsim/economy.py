"""Resource sites, goods and trade."""
import json
import math
import os
import numpy as np

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403


class EconomyMixin:
    def sites_setup(self):
        """Unique resources and domestication hearths (sites.json, or
        drawn from the run seed with --shuffle-sites)."""
        W = self.W
        if self.shuffle_sites:
            from make_sites import place_sites, place_sites_v2
            S = place_sites(W, 90_000 + self.seed)
            if self.sites_file != "sites.json":
                S = place_sites_v2(W, 90_000 + self.seed, S["hearths"])
        else:
            with open(os.path.join(HERE, self.sites_file)) as fh:
                S = json.load(fh)
        self.sites = S
        R, H = S["resources"], S["hearths"]
        self.res_cell = np.array([W.idx2[x["row"], x["col"]] for x in R],
                                 int)
        self.res_kinds = sorted({x["kind"] for x in R})
        self.res_kind = np.array([self.res_kinds.index(x["kind"])
                                  for x in R], int)
        nk = len(self.res_kinds)
        self.res_prec = np.array([bool(x.get("precious")) for x in R], bool)
        self.res_lode = np.array([x["kind"] in ("lode gold", "silver")
                                  for x in R], bool)
        self.res_reserve = np.ones(len(R))
        self.kind_prec = np.array([any(self.res_prec[self.res_kind == k])
                                   for k in range(nk)], bool)
        grng = np.random.default_rng(87_000 + self.seed)
        self.ppref = np.exp(grng.normal(0, PREF_SD, (self.nP, nk)))
        for c, key in enumerate(self.keys):
            b = PREF_BIAS.get(key, {})
            for k, kind in enumerate(self.res_kinds):
                grp = {g for g, kinds in PREF_GROUPS.items() if kind in kinds}
                if grp & b.get("fav", set()):
                    self.ppref[c, k] *= PREF_FAV
                elif grp & b.get("dis", set()):
                    self.ppref[c, k] *= PREF_DIS
        self.Lpref = np.ones((MAXL, nk))
        for L in range(self.nL):
            self.Lpref[L] = self.ppref[self.Lpeople[L]]
        self.h_cell = np.array([W.idx2[x["row"], x["col"]] for x in H], int)
        self.h_crop = np.array([x["kind"] == "crop" for x in H], bool)
        self.h_biome = np.array([BIOMES.index(x["biome"]) for x in H], int)
        self.h_name = [f"{x['biome'].lower()} {x['kind']}s" for x in H]
        nh, nb = len(H), len(BIOMES)
        # weight of each package in each biome: 1 at home, DOM_OFF elsewhere
        own = self.h_biome[:, None] == np.arange(nb)[None, :]
        w = np.where(own, 1.0, DOM_OFF)
        self.h_wc = np.where(self.h_crop[:, None], w, 0.0)
        self.h_wa = np.where(~self.h_crop[:, None], w, 0.0)
        self.h_near = [np.nonzero(gc_km(W.xyz, c, np.arange(W.N)) <
                                  HEARTH_KM)[0] for c in self.h_cell]
        self.domlv = np.zeros((MAXL, nh))
        self.guard = np.zeros((MAXL, GUARD_MAX), bool)
        self.n_guard = 0
        self.passets = {}

    def state_assets(self):
        """Kinds of resource, ores, craft and guarded techniques of each
        living state."""
        kinds = {}
        if len(self.res_cell):
            rc = self.res_cell
            pol = self.cell_pol[rc]
            ok = (pol >= 0) & (self.lin[rc] >= 0)
            for pid, k in zip(pol[ok], self.res_kind[ok]):
                kinds.setdefault(int(pid), set()).add(int(k))
            if self.res_prec.any():
                outp = {}
                for i in np.nonzero(ok & self.res_prec)[0]:
                    pid = int(pol[i])
                    Lr = self.polities[pid]["lin"] \
                        if pid in self.polities else -1
                    if self.res_lode[i] and (Lr < 0 or not self.bronze[Lr]):
                        continue
                    o = outp.setdefault(pid, np.zeros(len(self.res_kinds)))
                    o[self.res_kind[i]] += self.res_reserve[i]
                    rate = MINE_RATE * (1 if self.res_lode[i] else 2)
                    self.res_reserve[i] = max(0.0, self.res_reserve[i] -
                                              DT * rate)
                self.p_output = outp
        terr = {}
        W = self.W
        for i, d in enumerate((W.d_cu, W.d_sn, W.d_fe)):
            near = (self.lin >= 0) & (self.cell_pol >= 0) & (d < 120) & \
                (self.pop * self.peat[np.maximum(self.cul, 0)] > 1000)
            for pid in np.unique(self.cell_pol[near]):
                terr.setdefault(int(pid), set()).add(i)
        out = {}
        for pid, p in self.polities.items():
            if p["ended"] is not None:
                continue
            L = p["lin"]
            out[pid] = dict(
                ores_terr=terr.get(pid, set()),
                kinds=kinds.get(pid, set()),
                ores={i for i in range(3) if self.ore_has[L, i]},
                craft=float(self.craft[L]),
                tech=set(np.nonzero(self.guard[L])[0].tolist()))
            p["n_kinds"] = len(out[pid]["kinds"])
        self.passets = out

    def kind_value(self, pid):
        """Value of each kind of resource to the ruling lineage of pid."""
        L = self.polities[pid]["lin"]
        return (0.5 + self.crafts[L]) * self.Lpref[L] * self.Lapp[L]

    def goods_worth(self, a, b, prize=False):
        """Worth to state b of what state a holds and b lacks (valued by
        b's culture), plus precious-metal output (`precious`)."""
        x, y = self.passets[a], self.passets[b]
        v = self.kind_value(b)
        out = sum(v[k] for k in x["kinds"] - y["kinds"]
                  if not (self.kind_prec[k]))
        oa = self.p_output.get(a)
        if oa is not None:
            ob = self.p_output.get(b, np.zeros(len(oa)))
            out += float((v * (oa if prize else oa / (1 + ob))).sum())
        return out

    def offer(self, a, b):
        """What state a has that state b lacks."""
        x, y = self.passets.get(a), self.passets.get(b)
        if x is None or y is None:
            return 0.0
        return self.goods_worth(a, b) + \
            ORE_VALUE * len(x["ores"] - y["ores"]) + \
            max(0.0, x["craft"] - y["craft"]) + len(x["tech"] - y["tech"])

    def start_sites(self):
        """Place founding groups. A people's `head` (years) is its head
        start: groups of the people with the largest head start found at
        year 0, the rest arrive `max_head - head` years later, each on an
        empty site."""
        W = self.W
        dens = W.forage[None] * 0.5 + W.farm[None] * 0.5
        # founders settle only in their people's best biome(s)
        best = self.paff.max(1, keepdims=True)
        fit = best * (self.paff / best) ** BIOME_K
        fit = np.where(self.paff >= 0.9 * best, fit, 0)
        self.site_score = W.area[None] * dens * fit[:, W.biome]
        groups = [(c, k) for c in range(self.nP)
                  for k in range(self.P[c].get("starts", self.starts))]
        groups = [groups[i] for i in self.rng.permutation(len(groups))]
        self.chosen, self.first_site = [], {}
        self.sep0 = float(np.clip(3500 / math.sqrt(len(groups)), 500, 1800))
        H = max(p.get("head", 0) for p in self.P)
        self.arrivals = sorted(
            ((H - self.P[c].get("head", 0), c, k) for c, k in groups),
            key=lambda x: x[0])
        if self.start_mode == "wander":
            self.wander_setup(groups)
        self.place_arrivals()

    def pref_spread(self):
        """Tastes spread: subjects toward their ruler, trading rulers
        toward each other (`goods_value`)."""
        rl = self.ptab()[0]
        m = (self.lin >= 0) & (self.cell_pol >= 0)
        key = np.unique(self.cell_pol[m].astype(np.int64) * MAXL +
                        self.lin[m])
        pol, lin = key // MAXL, key % MAXL
        ru = rl[pol]
        ok = (ru >= 0) & (ru != lin)
        lin, ru = lin[ok], ru[ok]
        if len(lin):
            d = PREF_RULE * (self.Lpref[ru] - self.Lpref[lin])
            np.add.at(self.Lpref, lin, d)
        for (x, y), t in self.ties.items():
            a, b = rl[x], rl[y]
            if a >= 0 and b >= 0 and a != b:
                d = PREF_TRADE * t * (self.Lpref[b] - self.Lpref[a])
                self.Lpref[a] += d
                self.Lpref[b] -= d

    def trade_posts(self):
        """Merchant states plant posts in distant foreign ports
        (`trade_posts`); posts lapse when their merchants are gone."""
        W, rng = self.W, self.rng
        for k, (o, c, y) in list(self.posts.items()):
            h = k[1] if k[0] == o else k[0]
            rec = self.cities.get(c)
            O = self.polities.get(o)
            if rec is None or rec["polity"] != h or O is None or \
                    O["ended"] is not None or self.mcul[c] != O["culture"]:
                del self.posts[k]
        cc = [c for c in self.cities if W.coastal[c] and
              self.cities[c]["polity"] in self.polities and
              self.polities[self.cities[c]["polity"]]["ended"] is None]
        if len(cc) < 2:
            return
        cc = np.array(cc)
        cpol = np.array([self.cities[c]["polity"] for c in cc])
        for pid in sorted(set(cpol.tolist())):
            P = self.polities[pid]
            L = P["lin"]
            if rng.random() >= DT * POST_K * self.trade[L] * self.sail[L]:
                continue
            D = self.sail_km(L)
            src = cc[cpol == pid]
            d = np.min([gc_km(W.xyz, x, cc) for x in src], 0)
            ok = (cpol != pid) & (d < 4 * D)
            ok &= np.array([(min(pid, q), max(pid, q)) not in self.adj
                            for q in cpol])
            ok &= self.cul[cc] != P["culture"]
            if not ok.any():
                continue
            fe = self.pop[cc] * self.peat[np.maximum(self.cul[cc], 0)]
            wt = np.where(ok, fe * np.exp(-d / (2 * D)), 0)
            if wt.sum() <= 0:
                continue
            i = int(rng.choice(len(cc), p=wt / wt.sum()))
            c, h = int(cc[i]), int(cpol[i])
            self.add_minority([c], P["culture"], L, MIN_POST * self.pop[c] *
                              self.peat[self.cul[c]] / self.peat[P["culture"]],
                              capped=True)
            if self.mcul[c] == P["culture"]:
                k = (min(pid, h), max(pid, h))
                if k not in self.posts:
                    self.count("trade_post")
                    if len(P["cities"]) + len(self.polities[h]["cities"]) \
                            >= 8:
                        self.log("trade", f"{self.pname(pid)} plants a "
                                 f"trading post at {self.place(c)} in "
                                 f"{self.pname(h)}")
                self.posts[k] = (pid, c, self.year)

    def trade_ties(self):
        """Trade grows with both sides' trade drive and tolerance, gated by
        whether each tolerates the other's difference."""
        pairs = self.adj
        if self.posts:
            pairs = self.adj | set(self.posts)
        for k in list(self.ties):
            if k not in pairs or k in self.wars or not self.live(k):
                self.ties[k] *= 0.9
                if self.ties[k] < 0.02:
                    del self.ties[k]
        W = self.W
        riv = {}
        for pid, p in self.polities.items():
            if p["ended"] is None and p["cities"]:
                cc = np.fromiter(p["cities"], int)
                rc = cc[W.river[cc]]
                riv[pid] = (len(rc) / len(cc), set(W.basin[rc].tolist()))
        for k in (sorted(pairs) if pairs is not self.adj else self.adj):
            if k in self.wars:
                continue
            ab = self.live(k)
            if not ab:
                continue
            La, Lb = ab[0]["lin"], ab[1]["lin"]
            ra, ba = riv.get(k[0], (0.0, set()))
            rb, bb = riv.get(k[1], (0.0, set()))
            # goods one side has and the other wants can carry trade
            # past intolerance
            X = math.sqrt(self.offer(k[0], k[1]) * self.offer(k[1], k[0]))
            acc = self.saccept(ab[0], ab[1], TOL_TRADE2)
            acc = TRADE_FLOOR + (1 - TRADE_FLOOR) * acc
            acc = acc + (1 - acc) * min(1.0, X / ASSET_X0)
            rate, xb = TRADE_RATE2, 1 + min(X, ASSET_XMAX)
            g = self.eff(ab[0], "trade") * self.eff(ab[1], "trade") * \
                (0.4 + 0.3 * (self.eff(ab[0], "tol") +
                              self.eff(ab[1], "tol"))) * acc * \
                (1 + RIV_TRADE * (ra + rb) / 2) * \
                (1 + BASIN_TRADE * bool(ba & bb)) * xb
            g *= 1 + DEV_TRADE * (self.dev(La) + self.dev(Lb)) / 2
            g *= 1.25 - 0.25 * (self.eff(ab[0], "dom") +
                                self.eff(ab[1], "dom"))
            t = self.ties.get(k, 0.0)
            # exact over the tick, so a tie never passes 1
            self.ties[k] = 1 - (1 - t) * math.exp(-DT * rate * g)
        for (x, y), t in self.ties.items():
            cx, cy = self.polities[x]["culture"], self.polities[y]["culture"]
            if cx != cy and t > 0.5 and not self.trade_seen[cx, cy]:
                self.trade_seen[cx, cy] = self.trade_seen[cy, cx] = True
                self.log("trade", f"lasting trade between {self.keys[cx]} "
                         f"and {self.keys[cy]}: {self.pname(x)} and "
                         f"{self.pname(y)}")
        tot = {}
        for (x, y), t in self.ties.items():
            tot[x] = tot.get(x, 0) + t
            tot[y] = tot.get(y, 0) + t
        for pid, p in self.polities.items():
            p["trade"] = tot.get(pid, 0.0)
            p["trade"] += RES_VOLUME * p.get("n_kinds", 0)

    def ore_by_trade(self, near, nL):
        """Lineages that get an ore by trade: those living in a state
        joined, by a chain of ties >= ORE_TIE, to a state whose territory
        holds a worked deposit (`near`)."""
        pol = self.cell_pol
        src = set(np.unique(pol[near & (pol >= 0)]).tolist())
        out = np.zeros(nL, bool)
        if not src:
            return out
        nbr = {}
        for (x, y), t in self.ties.items():
            if t >= ORE_TIE:
                nbr.setdefault(x, []).append(y)
                nbr.setdefault(y, []).append(x)
        reach, front = set(src), list(src)
        while front:
            x = front.pop()
            for y in nbr.get(x, ()):
                if y not in reach:
                    reach.add(y)
                    front.append(y)
        occ = (self.lin >= 0) & (pol >= 0)
        inr = np.zeros(self.next_pid, bool)
        inr[list(reach)] = True
        m = occ & inr[np.maximum(pol, 0)]
        out[np.unique(self.lin[m])] = True
        return out
