# Run log

Run folders are in `../runs/`. Older runs used older code; their settings
are in each folder's `run.json`, but rerunning them with the current code
gives a different history.

| Runs | Roster | What changed | Main result |
|---|---|---|---|
| `_v1_highpop/` seeds 1–3 | archetypes | first model | population about 460M; densities cut 3.5x afterwards |
| seed11–14 | archetypes, vary 0.3 | lower densities, steel stage | 130–170M; tech diffusion fixed after |
| fantasy_seed21–24 | fantasy | 10 peoples | Trolls reached steel by summing contacts; changed to best contact only |
| lineage_seed31–34 | fantasy | lineages, 3 groups per people, tolerance | Human–Froglok and Froglok–Goblin fusions; more kin wars |
| headstart_seed41–44 | headstart (6 peoples) | head starts 1500/500 | Snake folk largest in 3 of 4 |
| size_seed51–54 | headstart (10), 20 groups | size in war, settler lineages, fusion blending | head start filled the world; latecomers stranded on tundra |
| sizefood_seed51–52 | same | plus food ∝ size^0.75 | Trolls and Ogres went extinct in seed 52 |
| buckets_seed61–64 | headstart | intrinsic traits fixed; head starts 400/150; food on | all peoples survive; Snake folk about half the population |
| biome_seed71–74 | headstart | sharpened biomes, tech adaptation, sailing kernel, bigger tech | Giants confined to tundra, no cities |
| city_seed81–84 | headstart | food-based city threshold, admin cap | Ogres founded 340–510 cities and dominated conquest |
| terrain_seed91–94 | headstart | wandering starts, terrain in war and colonization, rivers | conquest in jungle and desert down 45–65%; Giants back with 42–94 cities |
| structural_v1_seed91–92 | headstart | all ten structural mechanics, first draft ([structural.md](structural.md)) | land only declined (mean 0.46 by the end) and population fell to a third of baseline; technology decay hit city-states, so no iron. Both rules rewritten. |
| structural_seed91–92 | headstart | structural mechanics, land and decay fixed | population 70–77M against about 100M baseline; Snake folk share 37%/22% against 50%/32%; largest states about half baseline size; standing alliances 5–16x baseline; bronze about 1,000 years later than baseline, iron late, no steel; state lifespans *longer* (mean 770–810 against about 600 years) |
| nocap_seed91–92, nocap_nobal_seed91–92, nocap_base_seed91–92 | headstart | city cap dropped (U); all mechanics / `--off balance` / `--off all`; full event counters | rank-size unchanged by the cap (slope −0.26 to −0.33 in every set); vassal submissions about 3% of captures; balancing doubles standing alliances but leaves wars, captures and lifespans unchanged; with the mechanics, captures fall from about 8,500 to 2,600–3,000, states double (about 500 against 260), and breakaways are single cities |
| cities_seed91–92, cities_base_seed91–92 | headstart, no cap | city histories (`city_sizes.csv`) and end causes; all on / all off | every city end is war-related (92–98% clearance); sites never empty; 80–93% re-founded nearby, median gap 110–140 yrs; with the mechanics on, only 27–29% of cities ever end (71–78% with them off) |
| climate_off_seed91–92, climate_seed91–92, landscape_seed91–92 | headstart, no cap | structured climate and river changes; then roads and improvements | climate: wars and captures up about 40%, revolts up 20–30%, 100–120M famine moves, 170–190 river changes (only 1–4 city ends from them); a world-wide dry spell in seed 91 cut population 25% in a century. Roads and improvements: re-founding slower (median gap 175–215 against 125–135 years), long ruins up (76–91 against 44–61); population density on road cells about 7x the mean; land still 96–97% occupied, ruin sites never empty |
| dragons_seed91–92, dragons_half_seed91–92 | headstart, no cap, all mechanics; dragon kill 0.02 and 0.01 (`runs/dragons.sh`) | dragons (first draft) | population at year 6000 is 45–60% of the no-dragon runs (33–42M against 67–72M; half kill 48–51M); the first cities come 500–1,000 years later; bronze 600–1,200 years later, no steel, and no iron in seed 92. Dragons fall from about 6,500 to 2,500, holding 88% then 52% of the land: about 3,300 slain, 1,500 driven off with nowhere to go, 12,000 born. Allies: 1 in total across the four runs. Big-bodied peoples gain: Ogres and Giants hold 350–480 cities at year 6000 (against 250–300); Elves fall to 0.2–0.9M (against 8–12M) and Goblins and Dwarves fall. Near-empty land (below 0.02 food-equivalent people/km²) 8–20% (against 3–11%); occupied land 86–95%; ruin sites still never empty. Remaining dragons are on the polar fringe, deserts and interior wild land |
| sep_nodragon_seed91–92, sep_seed91–92 | as dragons_*, plus separation as spacing; without and with dragons (first draft) (`runs/separation.sh`) | separation becomes preferred density; hostility moves to (1 − tolerance) | separation alone: population at year 6000 about the same (59–72M against 67–72M), but 18–37% fewer cities and 30–57% fewer wars; captures fall by 55–66%; near-empty land 9–23% (against 3–11%); Giants shrink to 0.3–0.5M. With dragons too: no city before year 1000; 32–65 cities at year 2000; wars 1.7–2.6k against 11–13k with neither; near-empty land 18–36%; dragons keep 61–64% of the land at the end (52% without separation); 0–2 alliances |
| dragons2_seed91–92, dragons2_half_seed91–92 | as sep_*, with varied, heritable dragons and the ward size divided by body size^0.75; kill 0.02 and 0.01 (`runs/dragons2.sh`) | dragons, second draft | dragons are much harder to remove: they still hold 79% of the land at year 6000 (73% at half kill), against 61–64% in the first draft. About 1,600–1,700 slain against 2,500–2,600. Dragons evolve stronger (mean strength 1.04 to 1.16–1.22) while their tolerance and violence stay flat. At kill 0.02: 30–36M people and 321–330 cities at year 6000; fewer than 1,200 wars; near-empty land 21–40%. At half kill: 46–49M people, 464–499 cities. Allies: 1 in four runs (Humans, with a dragon of tolerance 0.91). Big-bodied peoples lose their advantage (Giants 0.3–0.5M) |
| bal_seed91–92, bal_r04_seed91–92 | `peoples_balanced` (r 0.06 for Frogloks and Goblins) and `peoples_balanced_r04` (0.04); hierarchy and patience on, conformity and proselytism not yet in; `--vary 0.12` (`runs/balanced.sh`) | broad rebalance of the roster | Frogloks dominate at both rates: 20–41M people and 118–227 of 395–507 cities at year 6000. Goblins are second at 11–17M. Humans collapse to 0.7–2.8M with 6–25 cities. Total population 47–62M against 30–36M with the old roster; 2.0–2.9 billion killed by dragons over the run, mostly Frogloks and Goblins, who keep growing (they live with dragons, as intended). Wars 3.8–8.3k against fewer than 1,200. Dragons keep 77–84% of the land; no alliances |
| bal3_seed91–94 | `peoples_balanced` with all four new traits, biome limits, wetland Frogloks, dragons as a growth-rate cut (0.036); `--vary 0` (`runs/balanced3.sh`) | the rebalance as specified (U) | Frogloks and Goblins hold 85–93% of all people at year 6000 (Frogloks 23–43M, Goblins 25–52M, of 67–83M) and 65–75% of cities. Humans 0.4–2.2M, Lizardfolk 0–0.5M, Elves 0–0.5M, Dwarves 0.1–0.9M. No people ever casts bronze in any seed. Dragons fall only from about 6,400 to 4,500–4,700; no alliances. Cities now end often: 2,200–3,100 founded, 70–80% ended, mostly "decline", "dry climate" and "dragon"; ruin sites empty 1% of ruin-years, the first time above 0 |
| bal4_seed91–92, bal4_shun_seed91–92 | Frogloks and Goblins r 0.04; dragons start at 50% of sites, breed at 1/1,500, grow to full strength over 300 years, nest only in very sparse land; with and without `--dragon-shun 0.2` (`runs/balanced4.sh`) | tone down fast breeders and dragons (U) | much more balanced. At year 6000, of 72–80M people: Frogloks 23–29M, Goblins 12–13M, Elves 10–16M, Snake folk 7M, Humans 5–7M, Lizardfolk 2–9M, Dwarves 1–3M. Cities spread across all peoples except Dwarves (Frogloks 128–156; Elves, Ogres, Giants, Lizardfolk, Humans 50–130 each). Dragons decline from about 3,700 to 630–780 (land covered 59% to 26–28%): about 3,500 born against about 5,500 dead of age and about 800 slain. Wars 6–10k. Refuges (`--dragon-shun`) change little once young dragons nest only in sparse land. Still no alliances. Metal almost absent: one bronze (Dwarves, year 5050, one run) |


## bal5 and metal tests (2026-10-29)

- **bal5** (`runs/balanced5.sh`, seeds 91/92): as bal4, dragons start at
  62.5% of sites and breed at 1/1,200. Wild dragons ~4,750 at 500 →
  790–840 at 6000 (bal4: 630–780). People 61–74M at 6000; Frogloks
  20–35M. No alliances, no metal.
- **metal_noacc_seed91** (`--off acculturation`): innovation holds near
  roster means (Humans 0.51, Dwarves 0.84), a few Human and Dwarf
  lineages reach the pre-bronze cap of 1.2, but still no bronze.
- **metal_nosupply_seed91** (`--off supply`): metallurgy no longer
  decays; median at the 1.2 cap for Dwarves, 0.3–0.6 for most others.
  Still no bronze.
- **Diagnosis (C).** Two blockers, not acculturation alone:
  1. **Ore.** No land cell has both copper and tin within 120 km (cu
     1.3% of land, tin 1.0%, both 0.0%; within 400 km, both 1.9%).
     Bronze needs a lineage with one ore on its own land and the other
     through a contact stronger than 0.4. That almost never happens.
  2. **Idle decay under `supply`.** Metallurgy decays at 0.0004 x the
     share outside any state, against invention at 0.0005 x innovation²
     (0.00008 at innovation 0.4). Stateless lineages lose more than they
     invent.
- **bal6** (`runs/balanced6.sh`): bal5 plus slow acculturation (fast
  under foreign rule), skill dispositions falling at 1/4 the rising rate,
  `dispersal`, `fishing`, Frogloks expansion 0.35. Running.

## bal6 (2026-10-29)

`runs/balanced6.sh`, seeds 91/92: bal5 plus slow acculturation (0.001;
0.01 under foreign rule), skill dispositions falling at 1/4 rate,
`dispersal`, `fishing`, Frogloks expansion 0.35. No dominance, no ore
trade.

- People at 6000: 108–112M (bal5 61–74M). Goblins 33–45M (bal5 ~12M),
  Frogloks 20–29M, Lizardfolk 10–14M, Elves 9–10M, Snake folk 8–12M,
  Humans 6–7M.
- States ~700 at 6000 (bal5 510–580); wars 16,600–20,200 (bal5
  5,700–7,900); captures 1,600–1,900.
- First bronze at 4490 and 5925: the first metal in any balanced run.
- Dragons as bal5 (wild 727–800 at 6000); still no alliances.

## bal7 (2026-10-29)

`runs/balanced7.sh`: bal6 plus `dominance`, `ore_trade`, all added
traits acculturating, sailing from innovation × fishing, loss of farming,
fishing and sailing by disuse. Running.

bal7 results (seeds 91/92): people 104–106M at 6000. Bronze at 3710 and
4145, iron at 5080 and 6385: the first iron in a balanced run. Goblins
back to 16–17M (bal6 33–45M); Lizardfolk 13–26M; Humans 7M and 22M;
Frogloks 28–31M. Wars 12,800–15,000, captures 1,700–2,700. Still no
dragon alliances.

## ens1 (2026-10-29)

`runs/ensemble1.sh`: 20 seeds (101–120) with dragons and 20 with `--off
dragons`, all other switches on, after the review fixes (`food_units`,
`shuffle`, `dynasty`, `logistics`, tolerance counted once). Running.

ens1 results (2026-10-30), year 6000, median [10th–90th percentile] over
20 seeds:

| | dragons | no dragons |
|---|---|---|
| people (heads) | 162M [151–178] | 139M [118–153] |
| food-equivalents | 131M [112–144] | 146M [127–154] |
| wars / captures | 16,600 / 5,400 | 19,100 / 6,800 |
| bronze / iron | 20/20 (median 4120) / 16/20 | 20/20 (median 3668) / 14/20 |

Share of food-equivalents by people, median [10–90%] (runs led):

| | dragons | no dragons |
|---|---|---|
| Humans | 12.8 [3.9–23.4] (4) | 5.5 [2.7–12.7] (0) |
| Goblins | 19.6 [15.0–26.9] (9) | 6.8 [5.2–10.9] (0) |
| Lizardfolk | 7.1 [3.4–14.6] (0) | 8.3 [5.4–12.7] (0) |
| Frogloks | 17.8 [12.5–22.5] (5) | 10.2 [6.6–16.7] (1) |
| Snake folk | 12.8 [8.2–17.7] (1) | 22.0 [13.9–29.7] (13) |
| Elves | 5.9 [3.4–13.8] (1) | 17.9 [11.1–27.7] (5) |
| Trolls | 1.1 [0.7–2.8] | 1.4 [0.8–2.8] |
| Ogres | 11.6 [7.5–16.3] | 15.3 [12.6–22.8] (1) |
| Giants | 3.4 [1.4–5.5] | 5.6 [2.7–7.8] |
| Dwarves | 1.8 [0.9–4.6] | 1.7 [0.9–4.0] |

Dragons decide the order: with them the fast breeders lead; without
them the high-statecraft peoples (Snake folk, Elves) do. Seeds spread
widely (Humans 4–23%). No dragon alliance in any of the 20 runs.
Dwarves stay under 5% everywhere.

## Tuning the economy (2026-10-30, `worldsim_dev.py`, seed 91)

`runs/tune/`. Round 1 crashed (trade ties could overshoot 1 and go
negative; fixed with an exact update). Round 2 (`tune2.sh`), people at
6000 and wars over the run:

| variant | people | wars | first bronze / iron / steel |
|---|---|---|---|
| all on, defaults | 579M | 6,017 | 3180 / 3785 / 4165 |
| `--off development` | 136M | 1,259 | 3870 / 4660 / 5170 |
| `--off scale` | 303M | 5,097 | 3850 / 5705 / – |
| `--off development,scale` | 89M | 1,702 | – |
| scale 0.2/3, dev 0.5, city 0.3 | 295M | 4,207 | 3255 / 3925 / 4380 |
| `--off trade_assets` | 514M | 8,615 | 3250 / 3820 / 4320 |
| all new mechanics off | 157M | 21,565 | 3375 / 4895 / 6250 |

Development (capacity and city boost × (1 + dev)) drives the overshoot.
Motivated war as first set cuts wars 3–17×. Round 3 (`tune3.sh`):
development 0.15–0.25, wars without motive × 0.5, motive × 2–3.

Round 3 (`tune3.sh`), people at 6000, wars over the run:

| variant | seed | people | wars | captures | bronze / iron / steel |
|---|---|---|---|---|---|
| A: dev 0.25/0.25, idle 0.5, motive ×2 | 91 | 196M | 3,579 | 535 | 3810 / 4595 / 5080 |
| A | 92 | 162M | 2,944 | 391 | 4105 / 5195 / 5935 |
| B: dev 0.15/0.15, idle 0.5, motive ×2 | 91 | 206M | 4,947 | 754 | 3965 / 4690 / 5320 |
| B | 92 | 213M | 5,995 | 946 | 3550 / 3820 / 4075 |
| C: A + scale 0.2/3 | 91 | 225M | 5,057 | 882 | 3480 / 4340 / 4850 |
| D: dev 0.25/0.25, idle 0.4, motive ×3 | 91 | 168M | 6,290 | 907 | 4280 / 4925 / 5530 |
| E: dev 0.25/0, idle 0.5, motive ×2 | 91 | 177M | 3,717 | 556 | 3940 / 4855 / 5580 |

Chosen (C): development 0.25 (capacity and city boost), wars without
motive × 0.5, motive × 3, motive saturating at 2. Ogres, Trolls and
Giants fall to under 1M people in every economy run (ens1 Ogres 7–16% of
food-equivalents): low innovation slows their domestication, and their
farms stay at half yield. Open.

`worldsim_dev.py` swapped into `worldsim.py`; the previous model is
`archive/worldsim_2026-10-30_pre_economy.py`. With `--off all` the model
still matches the old one draw for draw (2,500 years).

## econ1 (2026-10-30)

`runs/econ1.sh`: seeds 101–107, all switches on vs the economy, growth
and experience switches off. Running.

econ1 results, year 6000, median [min–max] over seeds 101–107:

| | all on | economy, growth, experience off |
|---|---|---|
| people (heads) | 173M [118–328] | 158M [128–174] |
| food-equivalents | 121M [82–205] | 123M [107–145] |
| wars / captures | 3,930 / 645 | 13,400 / 4,324 |
| largest state (cells) | 602 | 1,227 |
| bronze / iron / steel | 7/7 (3735) / 7/7 (4840) / 5/7 | 7/7 (4710) / 4/7 / 1/7 |
| world tolerance / violence | 0.69 / 0.12 | 0.31 / 0.59 |
| Goblins / Ogres share | 33% / 1.3% | 19% / 15% |

Experience flattened culture: every people ended near tolerance 0.7,
violence 0.1, conformity 0.9 (Humans from 0.1). In `price.csv`, summed
over the run (world): experience made almost all of the transmission
term for violence (−0.57 of −0.54), trade (+0.35 of +0.39), conformity
(+0.39 of +0.42) and tolerance (+0.21 of +0.24). Trade, peace and plague
reach every people, so with the first rates every trait ran to its
bound. Rates cut 2–4× (`econ2`).

## econ2 (2026-10-30)

`runs/econ2.sh`: seeds 101–107, all on, experience rates cut 2–4×.
Year 6000, median [min–max]:

- People 137M [114–283] (food-equivalents 99M [80–172]); states 399;
  largest state 705 cells.
- Wars 8,436 [4,208–15,154] (econ1 off: 13,400); captures 1,443. Goals:
  resource 2,992, rule 3,200, land 324; met 869; cities ceded 169.
- Bronze 7/7 (median 3465), iron 7/7 (4155), steel 6/7 (4763).
- Share of food-equivalents: Goblins 28.7% (led 5/7), Humans 14.8, Snake
  folk 14.9, Frogloks 14.7, Lizardfolk 6.7, Elves 5.9, Ogres 3.7, Dwarves
  1.6, Trolls 1.0, Giants 0.4.
- Culture still converges, less: every people's tolerance 0.52–0.68,
  violence 0.19–0.29, conformity 0.70–0.81 (econ1 off: tolerance
  0.24–0.39, violence 0.46–0.68, conformity 0.39–0.73). Experience is
  still most of the transmission term for those traits.

## exp2 (2026-10-30)

`runs/exp2.sh`: experience with forces both ways on every trait it moves,
conformity no longer slowing experience (U); seeds 101–107, all on
(`exp2_on`) and with `--off acculturation` (`exp2_noacc`). Analysis:
scratchpad `stable.py`.

- World means at 6000 (on): tolerance 0.57, violence 0.26, conformity
  0.37 (econ2: 0.78), cohesion 0.40. Food-equivalents 91M; wars 5,784.
- Spread between peoples (SD of the peoples' mean traits), 1000 → 6000:

  | trait | on | mixing off | econ1 off (no experience) |
  |---|---|---|---|
  | violence | 0.175 → 0.054 | 0.189 → 0.070 | 0.193 → 0.087 |
  | tolerance | 0.116 → 0.081 | 0.128 → 0.125 | 0.112 → 0.055 |
  | cohesion | 0.176 → 0.050 | 0.191 → 0.126 | – |
  | conformity | 0.159 → 0.058 | 0.176 → 0.081 | – |
  | hierarchy | 0.126 → 0.043 | 0.139 → 0.101 | – |
  | trade | 0.185 → 0.081 | 0.202 → 0.182 | – |

  With mixing off, tolerance and trade keep their spread and cohesion
  and hierarchy lose little; with it on, all converge. Violence converges
  either way.
- Balance-point curves (lineages binned by trait; the trait's balance
  point under the bin's mean war, trade and hardship memory) rise with
  the trait, and cross it: violence tips at ~0.3–0.4 (below → near 0,
  above → ~0.6); trade at ~0.3 (below → 0, above → ~1); tolerance at
  ~0.2; cohesion at ~0.3–0.5 (→ ~0.6–0.7). Two stable states exist in
  principle. The lineage distributions are bimodal only for trade
  (bimodality coefficient 0.80 on, 0.67 off; > 0.555 suggests two
  modes).

## mis1 (2026-10-30)

`runs/mis1.sh`: seeds 101–107; `mis1_on` all on (mission, dragon hosts);
`mis1_nomis` with `--off mission` (hosts on). exp2_on (neither) for
comparison. Year 6000, median [min–max]:

| | exp2_on | mis1_nomis (hosts) | mis1_on (hosts + mission) |
|---|---|---|---|
| food-equivalents | 91M | 89M | 78M [46–130] |
| wild dragons | 1,181 | 3,116 | 3,128 |
| dragon land share | 0.35 | 0.56 | 0.55 |
| dragons ever allied | 0 | 16 [2–22] | 23 [1–38] |
| wars / captures | 5,784 / 898 | 2,871 / 724 | 4,558 / 1,256 |
| faith goals | – | – | 1,782 [1,140–3,263] |
| revolts | 1,956 | 1,611 | 2,150 |
| mean stress | 1.07 | 1.77 | 3.04 |
| mean churn (per century) | – | – | 0.052 |
| Goblins / Frogloks share | 24.1 / 14.6 | 20.5 / 11.7 | 21.6 / 12.6 |
| Elves share | 6.9 | 5.8 | 9.1 |

Spread between peoples at 6000 (SD of peoples' means), nomis → on:
violence 0.042 → 0.056, tolerance 0.078 → 0.089, cohesion 0.047 →
0.073, conformity 0.045 → 0.056, hierarchy 0.045 → 0.062, trade 0.087 →
0.107. Mission keeps cultures apart longer, but all still converge.
Churn at weight 30 raises stress to ~3 (revolt hazard ×10): likely too
strong.

## War, second form: base rate (2026-10-30, `tune4.sh`, seed 91)

| base | wars | captures | goals: land / faith / irredentism / enmity / rule / resource / prey | no goal | goal met | ceded |
|---|---|---|---|---|---|---|
| 0.018 | 454 | 296 | 250 / 83 / 29 / 27 / 34 / 20 / 8 | 3 | 286 | 53 |
| 0.05 | 1,306 | 795 | 637 / 198 / 146 / 164 / 75 / 57 / 27 | 2 | 762 | 196 |
| 0.12 | 3,480 | 1,926 | 1,769 / 518 / 433 / 308 / 212 / 155 / 77 | 8 | 1,851 | 502 |

Chosen 0.12. 84–89% of states under land pressure at 6000 (crowding
~0.93); thresholds raised (θ = 1 − 0.35 × dominance). Churn weight 10.
`war2.sh` running: seeds 101–107, all on vs `--off war_v2`.

## war2 (2026-10-30)

`runs/war2.sh`, seeds 101–107; `war2_on` all on, `war2_v1` with `--off
war_v2`. Year 6000, median [min–max]:

| | war_v2 off | war_v2 on |
|---|---|---|
| food-equivalents | 78M [45–139] | 84M [51–165] |
| wars | 4,413 [3,691–14,733] | 2,400 [996–6,759] |
| captures (per war) | 1,631 (0.37) | 1,344 (0.56) |
| wars with no goal | 440 | 7 |
| goals met / cities ceded | 1,444 / 371 | 1,284 / 351 |
| revolts / mean stress | 2,349 / 1.96 | 2,225 / 1.83 |
| largest state (cells) | 589 | 807 |
| world tolerance / violence | 0.54 / 0.21 | 0.58 / 0.14 |
| bronze / iron | 7/7 (3655) / 6/7 | 7/7 (3425) / 6/7 |

Goals under war_v2 (median per run): land 1,276 (53%), irredentism 416
(17%), enmity 316 (13%), rule 235 (10%), prey 179 (7%), faith 158 (7%),
resource 129 (5%).

Shares (war_v2 on): Goblins 20.6, Snake folk 17.0, Frogloks 12.2, Humans
11.6, Lizardfolk 8.6, Elves 5.8, Ogres 4.8, Dwarves 1.3, Trolls 1.2,
Giants 0.7. Leaders spread across five peoples.

Spread between peoples, 1000 → 6000: violence 0.189 → 0.031, conformity
0.179 → 0.036, hierarchy 0.136 → 0.046, cohesion 0.182 → 0.075,
tolerance 0.130 → 0.085, trade 0.197 → 0.081. Fewer wars mean more peace
everywhere, and violence and conformity converge most.

## raid1 (2026-10-30)

`runs/raid1.sh`: seeds 101–107, raids as experience at 0.01, peace and
trade pulls on violence halved; frames every 100 years. Year 6000,
median [min–max], against war2_on:

- World violence 0.68 [0.50–0.72] (war2_on 0.14); tolerance 0.42 (0.58).
  Every people 0.66–0.75, Elves (start 0.25) included.
- Wars 3,106, captures 1,951 (war2_on 2,400 / 1,344); food-equivalents
  75M (84M).
- Shares: Ogres 12.5% (4.8), Giants 2.7 (0.7), Trolls 2.5 (1.2),
  Lizardfolk 4.7 (8.6), Goblins 16.9 (20.6).
- Raid exposure (people-weighted, per lineage): median 0.011, 90th
  percentile 0.137, 10th 0; it correlates with violence (r = 0.61), so
  frontier lineages are harder than interior ones, but every people has
  both, and the peoples' means converge. Violence balance at 0.01: 0.18
  interior, 0.43 median, 0.87 frontier, and higher still through the
  raid → violence → raid loop.
- Rate cut to 0.004 (balance 0.18 / 0.30 / 0.73); `raid2` running.

## raid2 (2026-10-30)

`runs/raid2.sh`: as raid1 with raid experience 0.004. Year 6000: world
violence 0.54 [0.40–0.61], every people 0.46–0.66; tolerance 0.46; raid
exposure (people-weighted) 0.052; wars 3,312; food-equivalents 72M. The
raid → violence → raid loop keeps violence high even at the lower rate.
`raid3` (raid order, raid experience 0.01) running.

## raid3 (2026-10-30)

`runs/raid3.sh`: raid order on, raid experience 0.01; seeds 101–107.
Year 6000, median [min–max]:

- Raid exposure (people-weighted lineage mean) 0.022 (raid1 0.061);
  median lineage 0.0011 (raid1 0.011), 90th percentile 0.058 (0.137).
  Raids per tick (years 2000–6000) 3,914 [3,049–4,546].
- World violence still 0.57 [0.42–0.72]; peoples 0.55 (Goblins, Snake
  folk, Elves) to 0.68 (Ogres, Dwarves); spread between peoples 0.082
  (raid1 0.070, war2_on 0.031). Tolerance 0.49; Dwarves 0.20.
- Wars 3,148, captures 1,847, food-equivalents 87M. Shares close to
  raid1.
- Reading: order cuts raiding about tenfold in the median lineage, but
  violence was raised in the stateless first millennia (everyone raids
  before states exist) and falls only slowly afterwards, since the peace
  and trade pulls were halved with raid1 (timescale ~5,000 years).

## reg1 (2026-10-30): regional starts

`runs/reg1.sh`: `peoples_regional`, seeds 101–107, settings as raid3.
Year 6000, medians:

- Food-equivalents 124M (raid3, global starts: 87M); wars 6,971 (3,148);
  world violence 0.39 (0.57); multi-people states 37.
- Shares: Humans 25.5% (led 3), Goblins 22.8 (2), Elves 22.2 (2), Snake
  folk 19.8, Dwarves 2.7, Frogloks 1.5, Trolls 1.4, Lizardfolk 1.3,
  Ogres 0.3, Giants 0.3.
- By landmass (food-equivalents, mean of seeds): Human island 31M
  (Humans 85%, Goblins 14%); Elf island 25M (Elves 95%); Snake island 16M
  (Snake folk 96%); Lizardfolk/Froglok island only 4.3M (Frogloks 60%,
  Lizardfolk 31%); southern continent 36M (Goblins 64%, Snake folk 14%,
  Dwarves 14%, Trolls 6%); small islands 17M (Elves 44%, Snake folk 27%,
  Humans 19%).
- First landings on another landmass (median): Lizardfolk 1257 (4 of 7
  seeds), Snake folk 1370, Elves 1430, Humans 2390.
- First contact (median year): Frogloks–Lizardfolk 250 (same island),
  Dwarves–Ogres 942, Dwarves–Snake folk 1810, Humans–Lizardfolk 2055,
  Elves–Snake folk 2105, Elves–Lizardfolk 2160, Elves–Humans 2688,
  Frogloks–Humans 3580, Snake folk–Trolls 4565, Elves–Frogloks 4805,
  Humans–Snake folk 5598 (2 seeds).
- First bronze (median): Humans 3900, Snake folk 4020, Dwarves 4245,
  Elves 4455, Goblins 4850, Frogloks 5227, Lizardfolk 5250 (4 seeds),
  Trolls 5857 (2 seeds).

## reg2, reg3 (2026-10-30)

`runs/reg23.sh`: regional starts, seeds 101–107; reg2 = peace and trade
pulls on violence restored, `--off sod`; reg3 = the same with sod. Year
6000, medians (reg1 for comparison):

| | reg1 | reg2 | reg3 |
|---|---|---|---|
| food-equivalents | 124M | 127M | 124M |
| wars / captures | 6,971 / 3,564 | 6,324 / 3,373 | 5,248 / 2,809 |
| raids per tick (2000–6000) | 1,515 | 1,524 | 1,690 |
| world violence / tolerance | 0.39 / 0.52 | 0.24 / 0.56 | 0.25 / 0.55 |
| grassland share of people / cities | – | 0.22 / 0.24 | 0.20 / 0.20 |

Violence by people (reg2 / reg3): Elves 0.16 / 0.13, Snake folk 0.17 /
0.16, Humans 0.22 / 0.23, Frogloks 0.28 / 0.33, Goblins 0.29 / 0.32,
Trolls 0.37 / 0.38, Dwarves 0.43 / 0.53, Lizardfolk 0.48 / 0.46, Ogres
0.68 / 0.67, Giants 0.78 / 0.77. Ogres and Giants end near tolerance
0.05. With regional starts and state order, peoples now differ in
violence (spread ~0.2); with global starts they did not.

Herding share of people by year (reg2 / reg3): 1000 0.045 / 0.052, 2000
0.34 / 0.38, 3000 0.30 / 0.35, 4000 0.15 / 0.20, 5000 0.08 / 0.11, 6000
0.04 / 0.06: a pastoral age around 2000–3000, ending as farming spreads;
sod lengthens it.

Shares (reg3): Elves 23.3, Humans 21.8, Goblins 21.8, Snake folk 21.5,
Dwarves 1.8, Frogloks 1.3, Trolls 1.2, Lizardfolk 1.1, Ogres 0.4, Giants
0.3. `reg8k` (to year 8000, reg3 settings) queued.

## reg8k (2026-10-30)

`runs/reg8k.sh`: reg3 settings to year 8000, seeds 101–107. Medians:

| year | food-eq | states | largest state (cells) | violence | development |
|---|---|---|---|---|---|
| 6000 | 123M | 265 | 631 | 0.23 | 0.75 |
| 7000 | 169M | 364 | 990 | 0.20 | 0.86 |
| 8000 | 207M | 525 | 2,006 | 0.15 | 0.92 |

Shares at 8000: Goblins 31.4 (6000: 20.3), Humans 23.0, Elves 18.3, Snake
folk 12.5, Dwarves 3.8, Trolls 3.0, Lizardfolk 2.4, Frogloks 2.2, Giants
1.4, Ogres 0.3. Population does not level off: development nears its
ceiling, and the growth loop keeps going. Bronze 2775–4340, iron
3435–5190, steel 3890–5845 (all seeds).

## reg4 (2026-10-30)

Humans, Lizardfolk and Frogloks on both western islands; Lizardfolk
temperate forest 1.1; dragon refuge only among hosts. Seeds 101–107,
8000 years (restarted at 8000, U). Medians:

| year | food-eq | polities | largest state (cells) | violence | development | wild dragons |
|---|---|---|---|---|---|---|
| 4000 | 45M | 173 | 388 | 0.41 | 0.33 | 3,846 |
| 6000 | 112M | 284 | 712 | 0.24 | 0.74 | 3,708 |
| 8000 | 206M | 515 | 1,223 | 0.16 | 0.93 | 3,384 |

Shares at 8000 (reg8k in brackets): Goblins 34.9 (31.4), Elves 20.5
(18.3), Humans 13.2 (23.0), Snake folk 11.3 (12.5), Lizardfolk 5.5 (2.4;
range 3.4–16.1), Dwarves 3.8, Frogloks 3.4 (2.2), Trolls 2.9, Giants 1.6,
Ogres 0.5.

Western islands. In reg8k Humans held 75–90% of the larger (west) island,
with almost no Lizardfolk or Frogloks there, and almost no Humans on the
smaller (east) island. In reg4 all three peoples hold ground on both islands
in every seed. West island: Humans 38–70%, Lizardfolk 13–38%, Frogloks 5–10%,
Goblins 4–17%. East island: Froglok-led in 3 seeds, Lizardfolk-led in 1,
Human-led in 2, Goblin-led in 1. Dragons homed on the islands are about the
same as before (west 239–461, east 139–360). Human losses on the west island
make up most of the fall in the Human world share. Population still does not
level off (same trajectory as reg8k).

## Batch comparisons (2026-10-31)

New mechanics (see `next-batch.md`), sites v2, seed 101, 4000 years, one
switch group off per run (`scratchpad` runs `d_*`; tipping point 0.2,
trade floor on). Year 3995 (year 3000 in brackets):

| run | tolerance | alliances | wars | cross ties | violence | lineages |
|---|---|---|---|---|---|---|
| all on | 0.06 (0.12) | 7 (59) | 10 | 6 | 0.69 | 14,851 |
| no trade_mean | 0.12 (0.13) | 53 (54) | 15 | 36 | 0.64 | 20,277 |
| no tol_path | 0.07 (0.13) | 14 (54) | 8 | 16 | 0.76 | 18,392 |
| no revolt_exp | 0.10 (0.14) | 23 (30) | 11 | 24 | 0.53 | 15,320 |
| no spiky, life_memory | 0.11 (0.16) | 27 (81) | 11 | 12 | 0.70 | 26,421 |
| no alliance rules | 0.07 (0.13) | 22 (60) | 4 | 22 | 0.63 | 14,910 |
| no rulers, two_sided | 0.06 (0.12) | 12 (59) | 15 | 11 | 0.74 | 17,670 |
| no goods, colonies, posts | 0.06 (0.12) | 14 (28) | 9 | 15 | 0.66 | 1,211 |
| reg4 seed 101 (old) | 0.23 (0.16) | 240 (19) | | 80 | 0.42 | ~1,000 |

Pathologies found and fixed (C):
- **Colonies**: 13,000-25,000 colony lineages and ~60,000 minority
  landings in 4000 years. Settlers now take empty coast whenever any is in
  reach; thin occupied coast only when none is, at chance 0.2 per voyage;
  one tied colony lineage per state and landmass.
- **Revolt experience**: any revolt marked the whole state, and large
  states revolt almost every tick, so u sat near 1. Now weighted by the
  share of the state's cities lost.
- **Spikes**: events summed per state, and big states have events nearly
  every tick. Now one spike per state per tick, and a revolt counts only
  if it takes 20%+ of the state's cities.
- **trade_mean** was the largest single cause of the tolerance fall: the
  mean tie (~0.1-0.3) is far below the old sum (~1.4). Now v = min(1.5, 3
  x mean tie): a state well tied to all neighbours keeps the old scale,
  and neighbour count no longer inflates it.

Check after the fixes (seeds 101-103, 4000 years): tolerance 0.19-0.22
and rising at year 4000 (reg4: 0.23); peoples differ (Snake folk
0.33-0.42, Giants ~0.02); 55-158 alliances; 1,800-2,800 lineages;
7-22 partitions, 20-43 unions of crowns, 209-412 trading posts, 500-1,300
colony lineages, 10-45 cities retaken by defenders per run.

## batch1 (2026-10-31)

`runs/batch1.sh`: all mechanics on, sites v2, seeds 101-107, 8000 years.
All seven finished without errors (3,700–4,350 s each). State at year 8,000:

| seed | pop | cities | states | lineages | allies | wars |
|---|---|---|---|---|---|---|
| 101 | 238.78M | 1367 | 479 | 2570 | 495 | 24 |
| 102 | 235.53M | 1084 | 406 | 1939 | 360 | 6 |
| 103 | 221.59M | 1134 | 416 | 2018 | 358 | 27 |
| 104 | 204.62M | 951 | 364 | 2195 | 530 | 12 |
| 105 | 203.96M | 916 | 357 | 2049 | 616 | 20 |
| 106 | 161.15M | 801 | 335 | 1835 | 366 | 16 |
| 107 | 289.34M | 1329 | 516 | 2567 | 474 | 12 |

### Western islands (2026-11-01)

Landmass codes from `landmasses.py` (`docs/landmass_key.png`); figures
from `landmass_report.py --lm W`, set against reg4 on the same seeds.

- **Peoples.** Hum, Liz, Frg and Gob reach W1/W2 as before; Elves now
  hold W4 in every seed and are the largest people on W in seeds 104-105
  (W2, W3). Snake folk reach W in five of seven seeds but stay a trace (0.01-1.7M).
  Population on W is lower than in reg4 (41-74M against 58-91M).
- **States.** Median life of ended 3+ city states 25-100 yrs (reg4
  180-250). 5,400-7,700 states ever on W (reg4 2,500-4,300). Largest
  states peak at 40-56 cities and break up within decades; cross-landmass
  states at the end: Liz or Elf, spanning W1-W2 or N1-W4.
- **Wars.** 9,500-17,300 wars on W per run, doubling roughly every
  1,000 yrs from year 3000. About 70% are against one-city states and end
  in the tick they start: mopping up rebel city-states. Recaptures 111-299.
- **Revolts.** 4,600-6,700 on W per run; 2,000-3,000 in the last
  millennium alone (kin and ethnic revolts the most).
- **Culture: converged again, at the other pole.** All peoples on W end
  with nearly the same traits (violence 0.70-0.80, tolerance 0.2-0.4,
  separation 0.8-0.9, conformity 0.6-0.7, trade 0.9). Spread within a
  people equals spread between peoples. reg4 converged the same way
  towards peace (violence 0.15-0.25, tolerance 0.7). Elves go from
  violence 0.2 to 0.7 between 3000 and 5000, when they meet others. See
  open-questions.md, "Peoples converge again (batch1)".

## fix1101 (2026-11-01): growth fix, path dependence, devastation

`runs/fix1101.sh`, seeds 101-103, 5000 years, all mechanics on except:
fixA `--off trait_path,devastation` (growth fix only), fixB `--off
devastation`, fixC everything. Regression (`--off all`, 1500 yrs):
IDENTICAL_EVENTS, IDENTICAL_POLITIES. Figures are at year ~5000.

- **Spikes gone.** One-tick population spikes: 0 in all nine runs
  (batch1 had 10-17 per seed by year 5000).
- **Path dependence keeps peoples apart (fixB vs fixA).** Spread of
  people means (sd across peoples above 1% of population): violence
  0.15-0.18 against 0.09-0.12; tolerance 0.11-0.20 against 0.07-0.08;
  conformity 0.21-0.24 against 0.11-0.18. Elves' violence 0.37-0.56
  (fixA 0.53-0.62). Fewer wars in two seeds of three (1,771 v 3,307;
  1,366 v 5,125) and longer state lives (median of 3+ city states
  125-170 v 92-100 yrs). Population at 5000 is lower (76-92M v
  92-123M). The ordering is not the roster's: Goblins end the least
  violent (0.45-0.47, from 0.85).
- **Devastation (fixC)** at 1% per siege: 13 cells lying waste at year
  5000 in each seed; 1,100-1,400 sieges a millennium at year 3000-4000
  and 6,400-10,800 at 4000-5000, so ~10-110 devastations a millennium by
  then; batch1 reached 39,000 sieges in its last millennium (~390).
  Counts are now in timeseries.csv (`n_devastation`, `n_devastation_city`).

## batch2 (2026-11-01)

`runs/batch2.sh`: as batch1 plus the growth fix, `trait_path`,
`devastation` (3%), `acc_cross`, UNION_CROWN 0.01. Seeds 101-107, 8000
years. Regression (`--off all`, 1500 yrs) identical. All seven
finished (3,400-4,200 s).

Against batch1 at year 8000 (same seeds; climate series identical, as
run length is the same):
- **Tolerance converges high.** World tolerance 0.70-0.81 (batch1
  0.29-0.43), climbing from year ~4000; spread between peoples 0.03-0.10.
  Likely cause: `trait_path` on top of `tol_path` with the low tolerance
  pivot (0.2): once a people is above 0.2, its trade push is amplified
  twice over.
- **Alliances saturate again:** 924-1,336 at year 8000 (batch1 360-616),
  about 2.2-2.6 per state.
- **Violence splits in two.** Goblins (0.20-0.57), and in some seeds
  Giants, Trolls or Snake folk, end low; Humans, Lizardfolk, Frogloks,
  Elves and Dwarves 0.73-0.88. Spread between peoples 0.10-0.26 (batch1
  0.03-0.10). The split does not follow the roster (Goblins start 0.85,
  Elves 0.25).
- **Less churn.** Wars in the last millennium 2,900-8,700 (batch1
  8,000-17,200); revolts 3,000-5,300 (4,500-8,400). Median lives: states
  of 3-9 cities 75-130 yrs (45-75), 10+ cities 310-440 (255-315). Wars
  and revolts still rise each millennium.
- **Devastation:** 590-2,020 per run, 98-294 of them on city cells;
  21-62 cells lying waste at year 8000.
- Food-equivalent shares much as batch1 (Goblins 26-44%, Elves 12-43%).

## sup (2026-11-01): superiority, and tolerance out of trait_path

`runs/sup.sh`: batch2 settings plus `superiority` and `sup_exp`; supB
also PATH_TOL=0. Seeds 101-103, 8000 years. Regression (`--off all`)
identical. (A first launch without `sup_exp` was stopped.) A 3600-year
smoke run: superiority Humans 0.51 -> 0.42, Lizardfolk 0.48 -> 0.43,
Elves 0.89 -> 0.86, Snake folk 0.74 -> 0.80 by year 3600. Running.

## cau (2026-11-01): causal experience, kin raids, superiority

The sup runs (superiority, before and after `sup_exp`) were stopped
before finishing, superseded. Smoke runs, seed 107 to year 2500 (violence
by people): `kin_raids` at 0.5 (old peace pull kept) drove every people
but Elves to 0.91-0.96, tolerance 0.03; `causal_exp` alone kept Goblins
at 0.90 (batch2 0.6 by then) and Frogloks, Snake folk and Elves near
their starting values; KIN_RAID 0.1 and 0.03 both drift everyone up
slowly before states (0.1: Humans 0.88, Frogloks 0.89 at 2500). With
everything on, seed 107 had 76 cities and 65 states at year 3500
(batch2 142, 87).
`runs/causal.sh`: batch2 + `superiority`, `sup_exp`, `causal_exp`,
`kin_raids` (0.1); cauB also PATH_TOL=0. Seeds 101-103, 8000 years.
Regression (`--off all`) identical. All six finished.

Judged on spread (sd across peoples above 2% of food-equivalents; sd
across a people's living lineages, population-weighted):
- **cauA** (tolerance under trait_path): seeds 101 and 103 like batch2 --
  tolerance converges high (world 0.75-0.78, sd between peoples
  0.03-0.06), alliances 1,189 in 101; violence keeps its spread (sd
  0.12-0.15). Seed 102 goes the other way: violence at the ceiling for
  seven peoples (0.96-0.99, sd 0.09 only because of Snake folk and
  Elves), tolerance 0.19 with wide spread (0.26).
- **cauB** (tolerance out of trait_path): violence collapses to the
  ceiling in all three seeds (0.84-0.99, sd 0.02-0.05; within peoples
  0.03-0.04); tolerance 0.18-0.32 with real spread (0.05-0.12); trade
  and hierarchy spread wide (0.20-0.34 in 102-103).
- **Superiority saturates** in every run: 0.87-0.99 for most peoples by
  8000, Humans and Lizardfolk from 0.50 to 0.91-0.98 (Ogres, Giants
  0.73-0.82). Its causes are lopsided: trade with the less advanced only
  raises it, and a capture marks the whole winning state as winning
  (big states win more often, so most people live in winners).
- Mean spread between peoples falls in every run, from ~0.17 at year
  3000 to 0.07-0.21 at 8000.
- Raids 2-4x batch2 at the end (kin raids); administration is high
  late (pop-weighted 0.73-0.98), so ordered peace is available. Seeds
  102-103 end with 126-165M people and 157-204 states (batch2 ~260M,
  ~450 states).
- Reading: with only caused pushes, the push form settles at up / (up +
  down); where war and raids are everywhere and path dependence
  amplifies the leaning side, traits run to a bound. Tolerance and
  violence are coupled through war: tolerance high -> alliances -> peace
  -> violence keeps spread; tolerance low -> war -> violence ceiling.

## grid (2026-11-01): tuning path dependence and experience speed

`runs/grid.sh`: all mechanics on (adds `flat_drift`, `goods_appetite`,
symmetric `sup_exp` to the cau settings), PATH_TOL 1. PATH_MIN {0.6,
0.8} x EXP_SCALE {1, 0.5, 0.25}, seeds 101-102, 8000 years; runs
`g<PATH_MIN x10>_<EXP_SCALE x100>_seed<s>`. Regression identical; a
3800-yr smoke run (seed 102, defaults 0.6/0.5) gave superiority 0.50-0.91
by people (Humans 0.54, Lizardfolk 0.50, Elves 0.91).

Results. "Between" = SD of the people means, averaged over the 8 traits
(violence, tolerance, expansion, cohesion, conformity, hierarchy, trade,
superiority); "pinned" = people x trait at year 8000 above 0.92 or below
0.08; "within" = SD among living lineages (weighted by peak population)
of a people, averaged over peoples and traits.

| PATH_MIN / EXP_SCALE | between yr 2000 | yr 8000 (s101 / s102) | pinned | within |
|---|---|---|---|---|
| 0.6 / 1    | 0.17 | 0.18 / 0.18 | 8 / 12 | 0.08 / 0.07 |
| 0.6 / 0.5  | 0.17 | 0.12 / 0.14 | 5 / 5  | 0.07 / 0.07 |
| 0.6 / 0.25 | 0.17 | 0.11 / 0.14 | 0 / 9  | 0.07 / 0.05 |
| 0.8 / 1    | 0.17 | 0.10 / 0.16 | 3 / 12 | 0.10 / 0.06 |
| 0.8 / 0.5  | 0.17 | 0.10 / 0.14 | 2 / 8  | 0.09 / 0.06 |
| 0.8 / 0.25 | 0.17 | 0.10 / 0.11 | 2 / 4  | 0.07 / 0.06 |

- **Superiority no longer saturates**: range 0.42-0.93 at year 8000 in
  every run, within-people SD 0.06-0.15 (highest of any trait).
- **Spread between peoples falls after year 4000** in 10 of 12 runs.
  Slower experience falls faster: contact acculturation then outweighs
  the different histories that set peoples apart. Only 0.6 / 1 holds
  the spread, and it does so partly with peoples pinned at a bound.
- **Pinning is violence high with tolerance low, in the same peoples.**
  Ogres pass 0.95 violence by year 1200-2300 in 11 of 12 runs, Giants in
  most; both end with 0-1 states, so the order-driven peace pull never
  acts (consistent with the causal rule: stateless peoples under raids
  stay violent). In seed 102 Trolls, Dwarves and Goblins join them at
  faster experience. Humans and Goblins at 0.6 / 1 passed 0.95 around
  year 1500-2600 and came back down once they had states.
- Tolerance no longer converges high (PATH_TOL 1 with the weaker path
  dependence): ranges 0.01-0.69, world means 0.16-0.43.
- Population 128-216M, states 158-335, wars at year 8000 7-30. Seed
  matters more than either setting. Alliances per state 1.2-1.8 at
  EXP_SCALE 1 with PATH_MIN 0.6, 0.4-0.9 elsewhere.

Recommendation (C): keep the defaults PATH_MIN 0.6, EXP_SCALE 0.5.
Neither setting both holds spread and avoids pinning; the two problems
come from other mechanisms (cross-people acculturation; the stateless
violence loop) and are listed in open-questions.md.


## feud (2026-11-02): feuding cost, Troll hardiness, Giant and Goblin roster

`runs/feud.sh`: grid defaults (PATH_MIN 0.6, EXP_SCALE 0.5) plus
`feuding` and `war_hardy`; Giants violence 0.70 / tolerance 0.35 / craft
0.30, Goblins r 0.035. `f_seed101-104` all on; `nf_seed101-102` with
`--off feuding`, `nh_seed101-102` with `--off war_hardy` (same roster).
Regression identical.

Results (year 8000; "yrs > 0.95" = years the people's mean violence
spent above 0.95; "sd" = SD of violence among living lineages):

| Run | Ogres viol / sd / yrs > 0.95 | Giants viol / sd / yrs > 0.95 | Trolls heads, states | between | pinned |
|---|---|---|---|---|---|
| f 101 | 0.92 / 0.08 / 6125 | 0.79 / 0.07 / 3775 | 1.19M, 20 | 0.113 | 5 |
| f 102 | 0.88 / 0.06 / 4700 | 0.94 / 0.09 / 6220 | 0.46M, 5 | 0.103 | 1 |
| f 103 | 0.99 / 0.00 / 6100 | 0.99 / 0.01 / 6745 | 0.29M, 12 | 0.140 | 5 |
| f 104 | 0.69 / 0.07 / 3935 | 0.68 / 0.09 / 4985 | 1.62M, 22 | 0.094 | 0 |
| nf 101 | 0.85 / 0.20 / 5710 | 0.76 / 0.08 / 1945 | 1.77M, 29 | 0.140 | 6 |
| nf 102 | 0.98 / 0.02 / 5975 | 0.77 / 0.15 / 5935 | 1.10M, 20 | 0.130 | 3 |
| nh 101 | 0.61 / 0.03 / 5045 | 0.68 / 0.07 / 3645 | 0.46M, 3 | 0.151 | 7 |
| nh 102 | 0.70 / 0.03 / 2635 | 0.72 / 0.06 / 5355 | 0.19M, 3 | 0.103 | 0 |
| grid 0.6/0.5 101 | 0.99 / 0.00 / 6600 | 0.73 / 0.04 / 2790 | 0.92M, 8 | 0.118 | 5 |
| grid 0.6/0.5 102 | 0.99 / 0.00 / 6250 | 0.99 / 0.00 / 6740 | 0.40M, 6 | 0.144 | 5 |

- **Feuding is weak.** Ogres end pinned in 1 of 4 runs (2 of 2 in the
  grid, 1 of 2 without feuding) and still spend 3900-6100 of 8000 years
  above 0.95. The cost lowers density but cannot move a people whose
  lineages are all at 0.99: selection needs variance, and experience
  and path dependence push every lineage back up. Within-people spread
  at the end is 0.06-0.08 in 3 of 4 runs (0 in the grid).
- **Troll hardiness works.** Same seed, Trolls end with 2.5x the heads
  (101: 1.19M vs 0.46M; 102: 0.46M vs 0.19M) and 5-20 states against 3.
- **Humans in seed 101 sit at violence 0.94-0.97, tolerance 0.04-0.07 in
  every setting**, inside states, so neither the order pull nor
  feuding moves them. Lineage SD 0.03.
- Goblin growth cut: not detectable at 2 seeds (Goblins 40-82M heads
  with the cut, 43-54M in the grid at 0.04, 88-116M in nf/nh runs).
- Giants (new roster) still reach the ceiling in 2 of 4 runs.

## prov (2026-11-02): provincial seats and travel distance

`runs/prov.sh`: feud settings plus `travel_reach` and `provinces`.
`p_seed101-106` all on; `pt_seed101-102` with `--off provinces`
(travel distance from the capital only). Controls: `f_seed101-104`.
Regression identical. Runs take ~1.5x as long (6100-6800 s vs 4300-4550).

| Runs | Largest state ever (M km²) | Years with a state > 6M / > 10M | between | pinned | Goblin share of heads |
|---|---|---|---|---|---|
| p 101-106 | 12.6, 9.3, 11.3, 10.7, 14.4, 23.8 | 545-1740 / 0-705 | 0.08-0.12 | 0-1 | 39-54% |
| pt 101-102 | 10.1, 7.1 | 850, 220 / 5, 0 | 0.07, 0.15 | 0, 4 | 42, 23% |
| f 101-104 | 6.4, 6.5, 5.7, 5.6 | 0-20 / 0 | 0.09-0.14 | 0-5 | 25-37% |

- **Large empires now form.** 10M+ km² in 5 of 6 runs; seed 106 ends
  with a Goblin state of 23.3M km² (31% of S, Goblins ruling Snake folk,
  Trolls, Giants, Dwarves, 1,660 years old). The big states mostly
  appear after year 6000.
- **Most of the giants on S are Goblin states** (the largest state on S
  is Goblin in all 6 runs).
- **Maritime empires appear**: Elves from N1 with 62% of their land
  overseas on 11 landmasses (seed 102, 3,740 yrs old); Elves from W2
  20-39% overseas; Dwarves from E1 63% overseas (seed 106). Control:
  at most 5% overseas.
- **Travel distance alone** (pt) roughly doubles the 6M-years but reaches
  10M only briefly; the seats do most of the work.
- **Side effects:** population at year 8000 up ~40% (238-295M vs
  161-219M), wars at year 8000 fewer (2-15 vs 14-29). The spread between
  peoples is a little lower (multi-people empires mix their subjects),
  pinning is lower, and Ogres are no longer at the violence ceiling
  (0.29-0.63; they live under Goblin rule).
- Seat revolts are counted but not written to the timeseries; not
  reported here.

## 2026-11-02: rulers batch (`runs/rulers.sh`)

`r_seed101-106`: `p` settings plus `ruler_traits`, `turmoil`,
`revolt_viol`, `road_tech`, `fortress` (next-batch.md 22-32). Controls:
`p_seed101-106`. Regression identical (1500 yrs). Runs ~3000-3300 s.

| Runs | Largest state ever (M km²) | States peaking > 6M / > 10M | Pop yr 8000 (M) | World violence yr 8000 | Goblin share | Median life, states of 10+ cities (yrs) |
|---|---|---|---|---|---|---|
| r 101-106 | 2.4, 2.5, 2.0, 3.8, 2.9, 3.4 | 0 / 0 | 79-132 | 0.73-0.87 | 25-31% | 365-845 |
| p 101-106 | 12.6, 9.3, 11.3, 10.0, 14.4, 23.8 | 7-21 / 0-3 | 238-295 | 0.45-0.62 | 39-54% | 217-595 |

- **Empires gone.** No state passes 3.8M km²; population about a third
  of the control; violence climbs again after year 4000 (control falls);
  road cells at yr 7200 1,418 against 7,828 (seed 101).
- Rulers: 16,000 reigns; 82% peaceful successions; median dynasty 3
  reigns / 150 years, longest 54 reigns. Mean w 0.56, mean gap at death
  0.79 logits.
- Cause not yet known: one-switch-off ablations `ra_<switch>_seed101`
  (`runs/rulers_ablate.sh`) running.

Ablations, seed 101, all on except one (`runs/rulers_ablate.sh`):

| Run | Largest (M km²) | > 6M | Pop yr 8000 (M) | Violence yr 8000 | Road cells | Dwarves (M) |
|---|---|---|---|---|---|---|
| p (control) | 12.6 | 13 | 283 | 0.56 | 8,851 | 11.7 |
| r (all on) | 2.4 | 0 | 96 | 0.81 | 1,511 | 4.5 |
| off ruler_traits | 4.4 | 0 | 98 | 0.88 | 1,691 | 4.4 |
| off turmoil | 6.3 | 1 | 197 | 0.79 | 5,671 | 5.9 |
| off revolt_viol | 2.3 | 0 | 101 | 0.85 | 1,964 | 5.1 |
| off road_tech | 2.1 | 0 | 107 | 0.81 | 1,836 | 3.3 |
| off fortress | 2.3 | 0 | 92 | 0.88 | 1,568 | 3.1 |

- **Turmoil is the main cause** of the lost empires, people and roads;
  the others barely move them. Likely the raid part: ADM_RAID 0.05 x
  share raided is charged every tick, which can outrun administration's
  invention (~0.0004/yr at most). Unconfirmed.
- **The violence rise survives every single switch off**, turmoil
  included: more than one cause, or a cause shared by several.
- Round 2 (`runs/rulers_ablate2.sh`, `rb_*`): ADM_RAID=0; ADM_LOSS=0;
  turmoil only; turmoil and revolt_viol off; turmoil and ruler_traits
  off.

Round 2, seed 101 (`runs/rulers_ablate2.sh`):

| Run | Largest (M km²) | > 6M | Pop yr 8000 (M) | Violence yr 8000 | Road cells | Dwarves (M) |
|---|---|---|---|---|---|---|
| ADM_RAID=0 (raid part off) | 2.5 | 0 | 96 | 0.90 | 1,573 | 3.2 |
| ADM_LOSS=0 (city-loss part off) | 6.9 | 3 | 172 | 0.76 | 4,737 | 10.8 |
| turmoil only (other four off) | 4.5 | 0 | 94 | 0.86 | 2,051 | 3.9 |
| off turmoil + revolt_viol | 7.6 | 3 | 200 | 0.60 | 5,512 | 9.1 |
| off turmoil + ruler_traits | 10.3 | 13 | 274 | 0.72 | 8,926 | 16.0 |

- **The city-loss part of turmoil is the cause, not the raid part**
  (the guess in round 1 was wrong). Alone it is enough to collapse the
  world. Likely the spiral flagged in next-batch.md item 26: lost cities
  cut administration, which shortens reach, which raises provincial
  revolt ∝ (distance / reach)², which loses more cities.
- **Violence comes from revolt_viol, with ruler_traits adding to it.**
  With turmoil and revolt_viol both off, violence at 8000 is 0.60
  (control 0.56); with turmoil and ruler_traits off, 0.72.
- **ruler_traits also shrinks empires** somewhat: with turmoil off,
  largest 6.3M with rulers, 10.3M without.
