"""Peoples that move (WP10 stage C, U 2026-11-21, D13): conquest that
settles, deportation, and assimilation under long rule."""
import numpy as np

from .params import *  # noqa: F401,F403


class MovementMixin:
    def settle_from_core(self, P, cells, want):
        """Heads of state P's ruling people moved into `cells`, shared in
        proportion to `want` (heads of the ruling people, per cell): taken
        from the state's own cells of that people crowded above SET_PRESS
        of their capacity, never more than the excess. Returns the heads
        placed per cell."""
        cells = np.asarray(cells, int)
        want = np.asarray(want, float)
        placed = np.zeros(len(cells))
        if not len(cells) or want.sum() < 1:
            return placed
        ca, La = P["culture"], P["lin"]
        src = np.nonzero((self.cell_pol == P["id"]) & (self.cul == ca) &
                         (self.lin >= 0))[0]
        if not len(src):
            return placed
        K = self.Kf(self.lin[src], src)
        spare = np.clip(self.pop[src] - SET_PRESS * K, 0, None)
        tot = min(spare.sum(), want.sum())
        if tot < 1:
            return placed
        give = tot * want / want.sum()
        left = self.rows_put(cells, ca, La, give)
        placed = give - left
        take = placed.sum() * spare / spare.sum()
        self.pop[src] -= take
        return placed

    def evict(self, cells, settled, ca, viol):
        """Hosts (each cell's main row, of another people) pushed out by
        `settled` heads of people ca: the settlers' food in hosts' heads,
        at most half the hosts. Of those pushed, the share 1 - viol flees
        (`displacement`); the rest die, as `expelled`."""
        cells = np.asarray(cells, int)
        host = (self.cul[cells] >= 0) & (self.cul[cells] != ca)
        c, s = cells[host], np.asarray(settled)[host]
        if not len(c):
            return
        push = np.minimum(0.5 * self.pop[c],
                          s * self.peat[ca] / self.peat[self.cul[c]])
        self.pop[c] -= push
        self.lost_rows(c, push, viol, "expelled")

    def conquest_settle(self, A, t, host):
        """`conquest_settle`: after state A takes city t of people `host`,
        settlers of A's people move into the city and its land held by
        `host`: a share CQ_MAX x expansion x establishment of those
        cells' heads (in food), from A's crowded cells."""
        ca = A["culture"]
        hint = np.nonzero(((self.cell_city == t) | (np.arange(self.W.N) == t))
                          & (self.cul == host))[0]
        if not len(hint):
            return
        L = A["lin"]
        est = float(np.clip(self.admin[L] * (0.5 + self.state[L]), 0, 1))
        share = CQ_MAX * self.eff(A, "expn") * est
        want = share * self.pop[hint] * self.peat[host] / self.peat[ca]
        got = self.settle_from_core(A, hint, want)
        if got.sum() < 1:
            return
        self.count("cq_settlers", float(got.sum()))
        self.evict(hint, got, ca, self.eff(A, "viol"))

    def deport(self):
        """`deport`: each tick, a state may move part of a subject people
        out of one of its cities of that people (and the city's land) to
        cells of its own people near its capital, and send its own people
        in. Chance per foreign city DT x DEP_RATE x hierarchy x
        statecraft x (1 - tolerance) of the ruler."""
        rng = self.R("deport")
        for P in list(self.polities.values()):
            if P["ended"] is not None or len(P["cities"]) < DEP_MIN:
                continue
            ca = P["culture"]
            foreign = [c for c in P["cities"] if c != P["capital"]
                       and self.cul[c] >= 0 and self.cul[c] != ca]
            if not foreign:
                continue
            pr = DT * DEP_RATE * self.eff(P, "hier") * \
                self.eff(P, "state") * (1 - self.eff(P, "tol"))
            if rng.random() >= 1 - (1 - pr) ** len(foreign):
                continue
            t = max(foreign, key=lambda c: self.pop[c])
            host = self.cul[t]
            cells = np.nonzero(((self.cell_city == t) |
                                (np.arange(self.W.N) == t)) &
                               (self.cul == host))[0]
            core = np.nonzero((self.cell_pol == P["id"]) & (self.cul == ca) &
                              (self.cell_city == P["capital"]))[0]
            if not len(cells) or not len(core):
                continue
            moved = DEP_FRAC * self.pop[cells]
            room = np.clip(self.Kf(self.lin[core], core) - self.pop[core],
                           0, None) * self.peat[ca] / self.peat[host]
            if room.sum() < 1:
                continue
            k = min(1.0, room.sum() / moved.sum())
            moved = moved * k
            self.pop[cells] -= moved
            lin = int(self.lin[t]) if self.lin[t] >= 0 else int(
                self.lin[cells[0]])
            put = moved.sum() * room / room.sum()
            left = self.rows_put(core, host, lin, put)
            if left.sum() > 0:
                # no row free for them in the core: they die on the road
                self.dead("deported", np.array([t]),
                          np.array([left.sum()]))
            self.count("deported", float(moved.sum()))
            # the state's own people take the emptied land
            got = self.settle_from_core(
                P, cells, moved * self.peat[host] / self.peat[ca])
            self.count("cq_settlers", float(got.sum()))
            if len(P["cities"]) >= 5:
                self.log("deportation", f"{self.pname(P['id'])} deports "
                         f"{self.keys[host]} from the city at "
                         f"{self.place(t)}", cell=int(t),
                         polities=[P["id"]], peoples=[self.keys[host]])

    def assimilate(self):
        """`assimilate`: in a state's cells held by another people, a
        share of the main row joins the ruling people each year: ASSIM_RATE
        x clock x the subjects' tolerance x (0.5 + the ruler's
        proselytism), clock = ACC_RULE0 + (1 - ACC_RULE0) x sigmoid((g -
        ACC_GENS) / 0.5) over g generations under rule by that people (as
        `acc_cross`). Food is kept: heads convert at the peoples' eating
        rates."""
        m = (self.cell_pol >= 0) & (self.cul >= 0) & (self.rul_c >= 0) & \
            (self.cul != self.rul_c)
        key = np.where(m, self.rul_c * 1000 + self.cul, -1)
        new = m & (key != self.asm_key)
        self.asm_since[new] = self.year
        self.asm_key = key
        c = np.nonzero(m & (self.pop > 0))[0]
        if not len(c):
            return
        pl = self.ptab()[0]
        Lr = pl[self.cell_pol[c]]
        ok = Lr >= 0
        c, Lr = c[ok], Lr[ok]
        sub = self.cul[c]
        g = (self.year - self.asm_since[c]) / (GEN_LEN * self.plife[sub])
        clock = ACC_RULE0 + (1 - ACC_RULE0) / (1 + np.exp(-(g - ACC_GENS)
                                                          / 0.5))
        rate = DT * ASSIM_RATE * clock * self.tol[self.lin[c]] * \
            (0.5 + self.pros[Lr])
        mv = np.minimum(rate, 0.5) * self.pop[c]
        g = mv > 1
        c, Lr, sub, mv = c[g], Lr[g], sub[g], mv[g]
        if not len(c):
            return
        rc = self.rul_c[c]
        self.pop[c] -= mv
        left = self.rows_put(c, rc, Lr, mv * self.peat[sub] / self.peat[rc])
        # no row free: they stay as they were
        self.pop[c] += left * self.peat[rc] / self.peat[sub]
        self.count("assimilated", float((mv - left * self.peat[rc] /
                                         self.peat[sub]).sum()))
