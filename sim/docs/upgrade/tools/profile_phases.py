"""Phase timing per era, plus cProfile of the last era. Read-only on the sim."""
import cProfile
import io
import os
import pstats
import sys
import time
from collections import defaultdict

SIM = sys.argv[1]
YEARS = int(sys.argv[2])
OUT = sys.argv[3]
sys.path.insert(0, SIM)
os.chdir(SIM)
import worldsim  # noqa: E402
from wsim import sim as simmod  # noqa: E402
from wsim.params import DT  # noqa: E402

PH = ["place_arrivals", "technology", "city_admin", "prepare_capacity",
      "famine", "dragons", "grow", "migrate", "raids", "tidy",
      "update_cities", "territory", "name_seats", "roads", "polity_stats",
      "extraction", "trade_posts", "trade_ties", "pref_spread", "minorities",
      "diplomacy", "wars_step", "rebellions", "ruler_pull", "city_culture",
      "city_record", "disasters", "record", "Kf"]
acc = defaultdict(lambda: defaultdict(float))
ncall = defaultdict(lambda: defaultdict(int))
era = [0]


def wrap(name):
    f = getattr(simmod.Sim, name)

    def g(self, *a, **k):
        t = time.perf_counter()
        try:
            return f(self, *a, **k)
        finally:
            acc[era[0]][name] += time.perf_counter() - t
            ncall[era[0]][name] += 1
    setattr(simmod.Sim, name, g)


for p in PH:
    wrap(p)

sim, out, t0 = worldsim.make_sim([
    "--peoples", "peoples_regional", "--starts", "20", "--start-vary", "0.1",
    "--vary", "0", "--sites", "sites_v2.json", "--seed", "101",
    "--years", str(YEARS), "--frame-every", "100", "--out", OUT])
print("setup", round(time.time() - t0, 1), flush=True)
nt = YEARS // DT
pr = cProfile.Profile()
tot = defaultdict(float)
rend = 0.0
for i in range(nt):
    era[0] = sim.year // 1000
    last = sim.year >= YEARS - 500
    t = time.perf_counter()
    if last:
        pr.enable()
    sim.step()
    if last:
        pr.disable()
    tot[era[0]] += time.perf_counter() - t
    if sim.tick % sim.frame_every == 0:
        t = time.perf_counter()
        simmod.render(sim)
        rend += time.perf_counter() - t
    if sim.tick % 100 == 0:
        print("yr", sim.year, "cities", len(sim.cities), "states",
              sum(p["ended"] is None for p in sim.polities.values()),
              "nL", sim.nL, round(time.time() - t0), flush=True)

with open(os.path.join(OUT, "phases.txt"), "w") as fh:
    eras = sorted(tot)
    fh.write("phase " + " ".join(f"{e:>8d}k" for e in eras) + "\n")
    fh.write("TOTAL " + " ".join(f"{tot[e]:9.1f}" for e in eras) + "\n")
    for p in sorted(PH, key=lambda p: -sum(acc[e][p] for e in eras)):
        fh.write(f"{p:18s}" + " ".join(f"{acc[e][p]:9.1f}" for e in eras) +
                 "   calls/tick(last) " +
                 f"{ncall[eras[-1]][p] / (1000 / DT):.1f}\n")
    fh.write(f"render per frame {rend / max(len(range(0, nt, sim.frame_every)), 1):.2f}s\n")
    fh.write(f"final: cities {len(sim.cities)} polities_total {len(sim.polities)} nL {sim.nL}\n")
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(45)
    fh.write(s.getvalue())
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(60)
    fh.write(s.getvalue())
t = time.perf_counter()
from wsim.output import write_outputs  # noqa: E402
write_outputs(sim, OUT)
with open(os.path.join(OUT, "phases.txt"), "a") as fh:
    fh.write(f"write_outputs {time.perf_counter() - t:.1f}s\n")
print("done", round(time.time() - t0))
