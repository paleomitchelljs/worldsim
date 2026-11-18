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

## 2026-11-02: streamlining (no behaviour change)

Switches folded per docs/switch-inventory.md (82 -> 17) and the code
split into `wsim/` (worldsim.py is now the command line). Check: seed
101, 4,000 years, all on, every csv/txt output byte-identical to the
unsplit v1 code (`archive/v1_2026-11-02/worldsim.py`). Old run scripts
that pass `--off` with a removed switch no longer run on this code.

## 2026-11-02: city batch (`runs/cities.sh`)

`c_seed101-106`: streamlined `wsim/` code, city build stages 1-3 with
city life and option (c) rates (U). 8,000 years. Controls `p_` and `r_`
(v1). Code copy: `runs/snap_cities_wsim/`.

| Runs | Largest ever (M km²) | Pop yr 8000 (M) | Violence yr 8000 | Goblin share | Lineages | Road cells |
|---|---|---|---|---|---|---|
| c 101-106 | 8.0, 7.7, 5.4, 7.2, 5.9, 8.9 | 136-182 | 0.48-0.56 | 17-24% | 1135-1482 | 3044-4458 |
| r 101-106 | 2.4, 2.5, 2.0, 3.8, 2.9, 3.4 | 79-132 | 0.73-0.87 | 25-31% | 1312-1497 | 1080-1912 |
| p 101-106 | 12.6, 9.3, 11.3, 10.7, 14.4, 23.8 | 238-295 | 0.45-0.62 | 39-54% | 1333-1602 | 5355-8851 |

- **Empires partly back; violence back to the control.** Moving
  administration to cities (turmoil off under city_admin) undoes most of
  the r collapse. Population ~60% of p.
- **Cities within a lineage are still near-identical.** Variance of
  commons between cities of one lineage 0.0002-0.0003 against 0.005
  between lineages of a people, all through the run; option (c) did not
  move it (stage tests 0.0003). Noise alone predicts ~1e-4 (CITY_NOISE
  0.002/sqrt(yr) against ~0.026/yr of restoring pulls). Divergent cities
  speciate out (40-56 per run), so the within-lineage measure is
  truncated by design: differentiation shows up as new lineages.
- **The rural-urban gap is a shared urban shift**, mean 0.06, largest in
  violence (0.13) and conformity (0.11). It does not grow with city size
  (slightly falls) or port. The trade column is capped at 1.5 for ~3/4
  of cities, so the trade test is not informative: needs per-city trade.
- **World conformity falls** 0.70 -> 0.40 (p 0.63, r 0.70); tolerance
  ends 0.50 (p 0.59). The urban conformity push reaches lineages via
  CITY_DOWN; the tolerance push does not show. Unexplained asymmetry.
- **Elite-commons gap** 0.15-0.18 on violence, dominance, expansion,
  statecraft (ruler traits), ~0.05 on the rest.
- City events per run: 1457-2101 city revolts (a third take the
  capital, a third secede), 410-510 lineage merges, 4652-8789 new elites
  by conquest; fortress tolls 144-2618, tracking Dwarf population
  (2.8-29.5M).

### 2026-11-02 ct batch: per-city trait record (runs/citytraits.sh)

Rerun of the c batch with `citytraits.csv` (each city's commons and elite
values every snapshot). All six seeds reproduce c exactly (citygaps.csv
identical), so `--frame-every` does not alter the simulation.

SD of commons values between cities, years 2000-8000, mean over traits
(scale 0-1). Pooled over seeds; 117,935 city-snapshots, 3,559 cities living
1000+ years.

| Between cities in | SD |
|---|---|
| the world | 0.110 |
| one people | 0.049 |
| one state | 0.013 |
| one lineage | 0.013 |

| One city over its life (1000+ yr cities) | |
|---|---|
| SD over lifetime | 0.041 (tolerance 0.073, violence 0.060; cohesion, innovation ~0.027) |
| mean change over 500 yr | 0.027 |
| r of its deviation from its people, t vs t+1000 | 0.65 (conformity 0.47) |
| SD over lifetime of its deviation from its own lineage | 0.012 |

- **States are culturally uniform.** States of 3+ cities hold ~4 lineages
  and ~1.5 peoples, yet same-people cities in a state differ by 0.012-0.013
  and cities of different peoples in one state by only 0.017-0.023 (against
  0.049 within a people world-wide). Larger mixed states are slightly more
  uniform, not less (0.017 at 10+ cities). Sister lineages in one state
  converge; the state/capital pull homogenises across peoples too.
- **Cities change over time only as their lineage does.** Lifetime SD 0.041
  is three times the between-sister SD; the city's own departure from its
  lineage stays at 0.012. Cities have no history of their own.
- Supports proposal 3 (per-city memory of experience) as the needed lever,
  and suggests the state-level pull is the other one to examine.

### 2026-11-02 Do big cities recur in the same places? (ct batch; `bigcities.py`)

Share of one run's big-city sites with a big-city site in another run within
150 km, against a null of the same number of sites drawn from all cells that
ever held a city of those peoples (30 run pairs).

| Sites | Observed | Null |
|---|---|---|
| top 25 by peak size | 0.50 (0.36-0.60) | 0.04 |
| top 25 alive, yr 2000 / 4000 / 6000 / 7000 | 0.31 / 0.50 / 0.48 / 0.44 | 0.04-0.05 |
| Elf / Snk / Dwf top 5 | 0.45 / 0.44 / 0.37 | 0.02 / 0.03 / 0.16 |
| Hum / Liz top 5 | 0.14 / 0.11 | 0.03 / 0.02 |
| Frg / Gob top 5 | 0.09 / 0.06 | 0.10 / 0.04 |

- Big-city sites recur strongly and in every era: 5 places are top-25 in all
  six runs, 4 in five, 6 in four (runs/ct_bigcities.csv). Geography (and
  the fixed regional homelands and resource sites) picks the great-city
  sites.
- The top 25 are almost all Elf cities peaking after yr 6000; the world's
  great cities are one people's. Frog and Goblin big cities do not recur
  (null level): their best sites are set by history, not land.
- Caveat: same peoples file and homelands in every run, start-vary 0.1;
  this measures recurrence given the same starting map, not a property of
  the land alone.

### 2026-11-02 f batch: lineage fusion (runs/fusion.sh)

Fusion replaces lineage merge; otherwise the ct code. Seeds 101-106.

| | ct (merge) | f (fusion) |
|---|---|---|
| Pop yr 8000 (M) | 128-182 | 127-191 |
| Lineages yr 8000 | 1135-1482 | 1430-1675 |
| SD between cities: world / people / state / lineage | 0.110 / 0.049 / 0.013 / 0.013 | 0.107 / 0.049 / 0.013 / 0.013 |
| City lifetime SD / 500-yr change / r1000 | 0.041 / 0.027 / 0.65 | 0.040 / 0.026 / 0.63 |
| Big-city sites recurring (top 25, 150 km; null 0.04) | 0.50 | 0.42 |

- Events per run: 745-1279 absorptions, 313-581 fusions (old merge:
  410-510 whole merges). 2,523 fused lineages in all; 46% alive at yr 8000.
  Absorbed zones are 6% of the pair's people (median); 28% of absorptions
  take the last of a lineage. Fusions are 27-48% splits.
- Every people fuses; Elf and Snake most (2,100+ events each).
- **Fusion comes too soon.** 21% of events at the first check (0-50 years
  under one state), 39% within 100; median 150. The ramp lowers the chance
  for young pairs, but most pairs at risk are young (conquest and parting
  reset the clock), so young pairs still give most events. Against the
  intent ("Lineages shouldn't fuse immediately due to proximity").
- Distance at the event: median 0.04, 90th percentile 0.10, max 0.35;
  pairs at risk were not recorded in this batch (lineage_pairs.csv from h).
- City diversity unchanged by fusion; lineage count rises, since an
  absorption ends a lineage only 28% of the time.

### 2026-11-03 h batch: city history + rule_weak + city_trade (runs/history.sh)

On top of fusion (f). Seeds 101-106.

| | ct | f | h |
|---|---|---|---|
| Pop yr 8000 (M) | 128-182 | 127-191 | 147-254 |
| Lineages yr 8000 | 1135-1482 | 1430-1675 | 1442-1780 |
| SD between cities: world / people / state / lineage | 0.110 / 0.049 / 0.013 / 0.013 | 0.107 / 0.049 / 0.013 / 0.013 | 0.106 / 0.058 / 0.013 / 0.014 |
| City lifetime SD / 500-yr change / r1000 | 0.041 / 0.027 / 0.65 | 0.040 / 0.026 / 0.63 | 0.042 / 0.028 / 0.57 |
| City revolts / secessions per run | 1457-2101 / 521-709 | 1284-2258 / 418-833 | 844-1329 / 273-442 |
| City speciations per run | 40-56 | 36-54 | 120-183 |

- **Within states, no change on average.** Experience traits loosened
  (state SD violence 0.016 -> 0.022, tolerance 0.014 -> 0.021, conformity
  0.013 -> 0.016); the others tightened slightly (0.012-0.013 -> 0.010).
  Within a people, violence 0.079 -> 0.118, tolerance 0.066 -> 0.106.
- **Divergence turns into new lineages.** City speciation tripled: cities
  that drift on their own history now cross CITY_SPEC and found lineages,
  so the within-lineage measure stays truncated.
- **Distant cities of one state are still alike.** Same-people pairs at
  1000-2000 km: same state 0.018, different states 0.031 (f 0.018 /
  0.027). rule_weak did not loosen states. Same-state pairs grow more
  alike with age (younger city <100 yr 0.027; >2000 yr 0.017), so an
  ongoing pull, not founding copies.
- **Suspect: CITY_TRADE.** It pulls every city of a state toward the same
  partner capitals at 0.01/yr, 3x the rural pull; 87-90% of city-snapshots
  are in states trading at the cap. Not testable from variation: ablation
  needed.
- **city_trade did almost nothing:** 94% of cities count as coastal or
  river, so the port factor is ~1 nearly everywhere.
- City history is small: h_rms mean 0.013 (90th pct 0.020).
- Fusion: 5,567 absorptions, 2,275 fusions; still 21% at 0-50 years.
  Pairs at risk (lineage_pairs.csv, 38,675 rows): distance median 0.055,
  90th pct 0.26, 18% beyond 0.2. Far pairs have a quarter of the hazard
  of close ones; they are there, and fuse slower, as intended.
- Population up a third, with fewer revolts and secessions; not
  investigated.

### 2026-11-03 tl batch: local trade pull (runs/tradelocal.sh)

h plus `trade_local`: each city's trade pull goes to the partner
state's cities nearest it (CITY_TRADE_KM 500), not the partner capital.
Seeds 101-106.

| | h | tl |
|---|---|---|
| Pop yr 8000 (M) | 147-254 | 152-220 |
| Lineages yr 8000 | 1442-1780 | 1445-1696 |
| SD between cities: world / people / state / lineage | 0.107 / 0.057 / 0.013 / 0.014 | 0.128 / 0.059 / 0.016 / 0.016 |
| City lifetime SD / 500-yr change / r1000 | 0.038 / 0.028 / 0.57 | 0.041 / 0.030 / 0.73 |
| City revolts / secessions per run | 844-1329 / 273-442 | 834-1363 / 251-450 |
| City speciations per run | 120-183 | 94-164 |
| Run time (s) | 3465-4345 | 6217-7069 |

(SD rows recomputed with ctan_t.py on both batches; h's world/people
differ slightly from the h entry above.)

- **Frontier cities now lean toward their foreign neighbour.** lean =
  RMS(state mean - f) - RMS(city - f), f the nearest other-state city,
  states of 3+ cities, every 500 yrs from 2000. <300 km: h -0.001, tl
  +0.013; 300-600: -0.003 -> +0.008; 600-1k: -0.005 -> +0.002. Stronger
  where the neighbour is another people (<300 km: +0.018 vs +0.012).
- **But the heartland moves too.** Deviation from the state mean doubled
  in every band (all: 0.014 -> 0.029) and no longer rises with distance
  to the frontier (corr(km, dev) 0.16 -> 0.06). trade_near saturates:
  77% of city-snapshots at 1.0; mean 0.98 at <300 km, 0.93 at 300-600,
  0.67 at 600-1k. Only 3% of cities in 3+ city states are over 600 km
  from a foreign city, so there is little heartland to protect. Interior
  cities still differ from each other because each is pulled toward a
  different nearest partner.
- **Distant same-state cities less alike.** Same-people pairs, border2.py
  (same state / different state): h 0.014 / 0.024, tl 0.023 / 0.033.
- **World SD up a fifth** (0.107 -> 0.128), most in proselytism,
  dominance, craftsmanship (0.13-0.16 -> 0.18-0.20): partner capitals no
  longer blend distant peoples. Persistence up (r1000 0.57 -> 0.73).
- Speciation slightly down (ranges overlap). Untested guess: cities
  are held near a neighbour rather than drifting past CITY_SPEC.
- **Cost:** the per-partner loop scales with cities x ties; yrs 6000-8000
  took 3257 s vs 1602 s in h (seed 101). Needs vectorising.
- **Correction (2026-11-04):** measured from the state's largest city
  instead of from the border, tl does have a heartland gradient. Distance
  from the state mean rises 0.016 (<200 km) -> 0.021 (700-1000) -> 0.039
  (>1000); h 0.012 -> 0.014 -> 0.015. corr(km, distance to the largest
  city's culture): h 0.10, tl 0.67. The "heartland moves too" point
  above holds only by distance to the nearest foreign city.

### 2026-11-04 ci batch: unified city influence (runs/influence.sh)

h plus `city_influence` (trade_local moot). Seeds 101-106. Also the
first batch with the faster migrate (capacity computed once a tick and
redone only where a cell's lineage changes; output byte-identical on a
1,500-yr test, 203 s vs 356 s).

| | h | tl | ci |
|---|---|---|---|
| Pop yr 8000 (M) | 147-254 | 152-220 | 134-201 |
| Lineages yr 8000 | 1442-1780 | 1445-1696 | 1481-1665 |
| SD between cities: world / people / state / lineage | 0.107 / 0.057 / 0.013 / 0.014 | 0.128 / 0.059 / 0.016 / 0.016 | 0.121 / 0.053 / 0.013 / 0.012 |
| City lifetime SD / 500-yr change / r1000 | 0.038 / 0.028 / 0.57 | 0.041 / 0.030 / 0.73 | 0.036 / 0.027 / 0.73 |
| City revolts / secessions per run | 844-1329 / 273-442 | 834-1363 / 251-450 | 710-983 / 222-331 |
| City speciations per run | 120-183 | 94-164 | 124-179 |
| Frontier lean <300 km / dev, all bands | -0.001 / 0.014 | +0.013 / 0.029 | +0.013 / 0.027 |
| Same-people pairs same / different state | 0.014 / 0.024 | 0.023 / 0.033 | 0.022 / 0.029 |
| Run time (s) | 3465-4345 | 6217-7069 | 2507-2891 |

- **Heartlands, by distance to the true capital** (states of 3+ cities;
  capital = the state's one city with w_capital 0): distance from the
  state mean 0.014 (<200 km), 0.015 (200-400), 0.017 (400-700), 0.019
  (700-1000), 0.038 (>1000). Capital's share of a city's weight 0.25 ->
  0.04 over the same bands. corr(km to capital, distance to capital's
  culture) 0.67.
- **Interior cities listen to their own state:** own-state share of the
  weight 0.25 within 150 km of a foreign city, 0.34 at 150-300, 0.54 at
  300-600, 0.72 beyond. Frontier lean is near 0 within 700 km of the
  capital, +0.021 beyond 1000.
- **But ci is close to tl.** With the largest city standing in for the
  capital (it is the capital only 43% of the time in ci), the gradient is
  h 0.012 -> 0.015, tl 0.016 -> 0.039, ci 0.013 -> 0.039. Localising
  trade did most of it; ci adds a tighter core (0.013 vs 0.016 within
  200 km) and less spread overall.
- The capital's weight is modest (mean 0.12 of a subject city's; 90th
  pct 0.25): CITY_INF_ADM 2 does not make the capital dominant.
  Administration is high (median 0.75), so the admin term is not small
  for lack of administration.
- Fewer revolts and secessions (a quarter fewer than h). Untested guess:
  elites and commons now move on the same weights, so their gap stays
  smaller.
- Run time 30-35% below h, 60% below tl.

### 2026-11-04 ar batch: administration widens a capital's reach (runs/admreach.sh)

ci plus `adm_reach`: the capital's weight is administration x
exp(-travel distance / (2 x the state's reach)) at weight 6 (was 2 over a
fixed 1000 km); travel distance is power_dist (roads, sailing,
provincial seats). Seeds 101-106, every seed under cProfile
(ar_seed*.prof). arh_seed101: seed 101 again with history.npz (identical
timeseries to ar_seed101), for war01-24.png and tradewars.gif.

| | ci | ar |
|---|---|---|
| Pop yr 8000 (M) | 134-201 | 123-215 |
| Lineages yr 8000 | 1481-1665 | 1411-1657 |
| SD between cities: world / people / state / lineage | 0.121 / 0.053 / 0.013 / 0.012 | 0.118 / 0.053 / 0.012 / 0.012 |
| City lifetime SD / 500-yr change / r1000 | 0.036 / 0.027 / 0.73 | 0.039 / 0.029 / 0.69 |
| City revolts / secessions per run | 710-983 / 222-331 | 579-1009 / 177-341 |
| City speciations per run | 124-179 | 126-166 |
| Frontier lean <300 km / dev, all bands | +0.013 / 0.027 | +0.008 / 0.021 |
| Same-people pairs same / different state | 0.022 / 0.029 | 0.018 / 0.028 |
| Capital's share of a subject's weight, <200 km / >1000 km | 0.25 / 0.04 | 0.39 / 0.30 |
| Own state's share, mean | 0.40 | 0.54 |
| Distance from state mean, <200 km / >1000 km from capital | 0.014 / 0.038 | 0.013 / 0.030 |
| Run time (s), profiled + a 7th process | | 3197-3946 |

- **Stronger capitals flatten the gradient.** The capital now reaches
  its far provinces (0.30 of their weight beyond 1000 km travel, vs
  0.04), so the far provinces move toward the centre: spread beyond
  1000 km falls 0.038 -> 0.030, frontier lean 0.013 -> 0.008, distant
  same-state pairs grow more alike (0.022 -> 0.018). The core is
  unchanged (0.013-0.014). corr(km to capital, distance to its culture)
  0.67 -> 0.57.
- Revolts slightly fewer at the low end; speciation unchanged.

Profile (6 seeds, 21,720 s in sim.run): wars_step 27% (all but 2% of it
war_chance -> deter -> projected, 68M calls; the cost is power_dist's
recomputation every PROV_EVERY ticks: great-circle distances to every
cell per seat and the Dijkstra search), migrate 23% (voyages 12%:
2.7M small capacity calls), technology 15%, raids 13% (capacity 6%),
city code 2%.

Exact speed-ups after this batch (byte-identical timeseries, citytraits
and wars on a 3,500-yr test): power_dist reuses its last result when the
seats, the sailing factor and the travel graph (a version counter on
travel()) are unchanged, keeping the PROV_EVERY rule; raids compute each
side's capacity once and redo it only where a raid lowers improvements
or a takeover changes the lineage. Not yet measured on a full batch.
**Correction (2026-11-07):** the power_dist reuse never fired. The
sailing factor in its key moves a little every tick, so the key never
matched: 0 reuses in 15,924 recomputes to year 4,500 (seed 101), 58% of
them triggered by sailing alone. See the 2026-11-07 entry.

- **Wars (tradewars.gif, arh_seed101):** late in the run ~250-330 wars
  per century between almost as many distinct pairs of states (329 wars,
  325 pairs, 7000-7100), many between capitals thousands of km apart
  across the sea; one large state fights in all directions at once.
  Worth checking against how often real states fought several distant
  wars at the same time.

### 2026-11-06 dom batch: dominion (runs/dominion.sh) — running

`dominion` (extraction, shared cells, settlers; structural.md) on the
current code, seeds 101-106 (dom_), with a fresh baseline at --off
dominion (domoff_): the ar snapshot holds an older adm_reach and does not
match the current code (seed 101 at yr 1000: 14.15M ar, 12.99M off).
Compare with `turnover.py`.

Test before the batch (seed 101 to yr 5500, scratch): no errors, 543 s.
Against arh_seed101 (not a clean baseline), per 500 yr at 5000-5500:
cells changing people 0.046 (arh 0.008), rising from 0.021 at 4000; ruling
people changing 0.074 (0.129); ruled land held by a foreign people 0.12
(0.34), as settlers turn conquered cells to the rulers' people; 74% of
cells that changed people were in a state at the end. Largest cities at yr
4500 30k vs 35k. Heads by people about as in arh (no people runs away by
5500).

### 2026-11-06 sw sweep: stability to turnover (runs/sweep.sh) — running

Seed 101, `dominion` on, 8000 yr. One factor f scales every turnover lever
(f = 0.5, 0.75, 1.5, 2, 3 -> sw050 ... sw300; f = 1 is dom_seed101):
COH_DECAY, REVOLT_BASE, WAR_DECLARE, SHATTER_P (cap 0.9), UNREST, SUCC_P,
EXT_SUBJ, EXT_REVOLT, SH_STATE, SET_FRAC x f; WAR_END0 / f. COH_DECAY,
REVOLT_BASE, WAR_DECLARE, WAR_END0 and SHATTER_P were literals, named in
params.py at their old values for this sweep (no change at defaults). The
levers move together, so the sweep cannot say which of them matters;
single-lever runs would.
**Correction (2026-11-07):** WAR_DECLARE did nothing. Its only use was
the pre-`war_v2` declaration rule, whose result war_chance overwrote, so
the sweep did not scale war declarations (WAR_BASE sets them). The other
levers did move. WAR_DECLARE is removed, so `--set WAR_DECLARE=...` now
fails.

### 2026-11-07 code review: speed-ups and fixes

Requested by the user (U); forms and checks C. The code before is in
`archive/wsim_2026-11-07_pre_speedups/`. Old runs are no baseline for new
ones: the climate, power_dist and the fixes below change every history.

**Where the time went** (seed 101, sweep settings, `dominion` on):
cProfile over 6,000 years, and timers over 40 ticks from a year-5000
state (1.07 s/tick): wars_step 28% / 32% (power_dist recomputes 17% /
~22%: great-circle km to all 67k cells more than Dijkstra), migrate 23% /
21% (voyages 10% / 11%), technology 14% / 18%, raids 11% / 8%. The
~3,900 s matplotlib entry in each `ar_seed*.prof` is a profiler artifact
(it equals sim.run's time; totals are double the wall time).

**Exact speed-ups** (no draw touched). Checked byte-identical: every part
of the state after 20 ticks from the year-5000 state (`snapcheck.py`),
and every output file and npz array of a 5,000-year run from year 0
(wars.png differs only by the run folder named in its title).
- `gc_km` sums the chord per coordinate: bit-identical to
  `np.linalg.norm(axis=-1)`, 2.1x faster on the whole grid.
- power_dist keeps each state's land distances; when only the sailing
  factor moved, only the sea step is redone (was Dijkstra plus
  great-circle km to every cell).
- technology: borrowing (`diffuse`) over the lineage pairs in contact
  only (0.5% of pairs at year 5000): 2.9 -> 0.1 ms a call, 20 a tick.
- `city_cols` built once (about 32,000 calls a tick).
- voyages: capacity once per lineage, on the union of the coast its
  voyages could take (was once per voyage, about 6 per lineage).
- budding scores only the cells that can bud.
- Dead per-tick work removed: the pre-`war_v2` declaration rule in
  wars_step (overwritten by war_chance; WAR_DECLARE's only use), the
  contact-weighted acculturation matrices under `mission`, the second K2
  in land_use, two dead lines in K2.

Year 5000-5100: 1.15 -> 0.77 s/tick. 5,000-year run: 517 -> 403 s (part
of each alongside other runs).

**Changed results** (C unless marked):
- **power_dist is a function of its inputs** (the seats, the travel graph
  and, for a coastal seat, the ruler's sailing) and is recomputed when
  any changes. It was reused for up to PROV_EVERY = 2 ticks whatever
  changed, so distances could be a tick stale, and the result depended on
  when it was last asked for: any change that added or skipped a call
  shifted the history. PROV_EVERY is removed.
- **War declaration: draw first.** war_chance draws nothing, so the draw
  now comes first and war_chance runs only when an upper bound on p
  (deterrence 1, motive term at WAR_GAIN_CAP) could beat it. Identical,
  draw for draw, to the run without it (20 ticks from year 5000); the
  bound held on all 4,308 pairs tested (largest p / bound 0.71). Needs
  power_dist to be a pure function, above; it skips about 84% of the
  full calculations.
- **technology's contact as pairs.** Contact, borders, rule and trade are
  lists of lineage pairs, not nA x nA matrices; acculturation's
  similarity is computed per pair as similarity() does (the old matrix
  form, |x|² + |y|² - 2x·y, was off by up to 7.5e-9). One tick from year
  5000 against the dense code: traits within 3.5e-12, technology,
  guarded secrets, ores and the random stream identical; with `--off
  mission`, within 1e-16.
- **Counteroffensives: the attacker's allies defend** (bug fix to match
  model-description 13.2a, which already had them): allies of the
  original attacker not allied to the defender add 0.35 x their
  projected strength where it holds a city. The loop that found them
  added nothing.
- **Climate drawn for CLIM_YEARS = 20,000 years** whatever `--years` says,
  so a shorter run of a seed has the climate of the start of a longer one
  (checked: 3,000 vs 8,000 years, series and abrupt events). Every seed's
  climate differs from older runs'.
- **relations.csv** (records only): similarity, enmity and faith are those
  war_chance reads (the states' cultures under `city_culture`; they were
  the ruling lineages'), plus `similarity_lin`. Checked: runs unchanged.

**Speed, all of the above:** year 5000-5200 0.58 s/tick against 1.07
(timers, alone). Seed 101, 8,000 years, old and new code side by side:
1,378 -> 842 s (1.6x; years 5000-8000 886 -> 502 s, 1.8x). The old
code's run reproduces dom_seed101 exactly. The new run at year 8000 sits
inside the dom batch's seed-to-seed range: 238M people (dom 195-247M),
273 states (218-270), 7,783 wars (4,965-8,414), 4,235 captures
(2,793-4,637), 5,661 revolts (3,548-6,146), world violence 0.21
(0.21-0.25), tolerance 0.66 (0.63-0.68). One seed, so this says only
that nothing broke, not that the changes are neutral.

New tool: `snapcheck.py` (running.md). Not changed, now in
open-questions.md: three state decisions still read the ruling lineage's
traits, and counteroffensive helpers go unrecorded.

### 2026-11-09 realism review: food flows, terms after a siege, records

From the review in `../reviewdocs/` (open-questions.md, "Realism review").
Built: `food_flow`, `war_terms` (structural.md, "2026-11-09"); urban
population as a city's size, `cityfood.csv`, `deaths.csv`, `peak_km2` for
every state; `realism.py`. The code before is in
`archive/wsim_2026-11-09_pre_foodflow/`.

**Check (records only).** With both switches off, 20 ticks from a
year-5000 state of seed 101 (saved by the old code) are identical to the
old code in every part of the state except the record fields (city size,
the new columns, death and food rows). A first attempt was not: a
temporary in `raids` reused the name of the edge array `b` that
`raid_K` reads; renamed.

**Test** (seed 101 to year 6000; t_off = both off, t_on = defaults then,
t_on2 = FF_RENT 0.12, FF_TRADE 0.003), all ~700-730 s side by side:

| | t_off | t_on | t_on2 |
|---|---|---|---|
| Pop yr 6000 (M) | 154 | 99 | 89 |
| Urban share (new measure) | 0.34 | 0.17 | 0.11 |
| Rank-size slope yr 6000 | -0.28 | -0.37 | -0.42 |
| Largest / 10th city | 1.7 | 1.5 | 2.2 |
| Food reaching cities: trade / rent / prov / capital | | 0.75 / 0.11 / 0.06 / 0.08 | 0.37 / 0.34 / 0.12 / 0.17 |
| War ends: defender fell / tributary / peace | 0.72 / 0 / 0.09 | 0.52 / 0.11 / 0.20 | 0.53 / 0.13 / 0.18 |
| Won sieges: annex / tributary / sack | 1 / 0 / 0 | 0.67 / 0.20 / 0.13 | 0.59 / 0.25 / 0.16 |
| Wars | 2523 | 1304 | 1756 |

t_on2's rent and trade became the defaults (structural.md gives the
reason). Deaths by cause in all three: dragons 57-64% (the growth cut
under dragon hazard), feuds 19-21%, raids 9-10%, hunger 3-7%, plague
2-6%, war levies, sieges, sacks and clearances together 1-3%.

### 2026-11-09 realism batch (runs/realism.sh)

base_ (both off), ff_ (`food_flow`), wt_ (`war_terms`), fw_ (both, the
defaults); seeds 101-106, 8000 yrs; `realism.py --group`. Ranges across
seeds. The first eight runs took ~10,500 s (machine busy), the rest
~2,000 s with eight side by side; neither switch costs time.

| | base | ff | wt | fw |
|---|---|---|---|---|
| Pop yr 8000 (M) | 209-262 | 144-195 | 213-277 | 150-177 |
| Urban share (measure of the day) | 0.33-0.39 | 0.10-0.11 | 0.34-0.38 | 0.11-0.12 |
| Rank-size slope yr 8000 | -0.22..-0.26 | -0.34..-0.40 | -0.22..-0.29 | -0.35..-0.41 |
| Largest / 10th city | 1.3-1.5 | 1.7-2.7 | 1.3-1.5 | 1.7-2.6 |
| Largest city, share of world | 0.11-0.15% | 0.07-0.10% | 0.12-0.16% | 0.08-0.10% |
| Largest state (M km², share of land) | 7.2-13.3 (6-11%) | 5.9-9.2 (5-8%) | 6.2-9.3 (5-8%) | 5.6-9.4 (5-8%) |
| Vassals standing, mean from yr 4000 | 8-12 | 7-10 | 19-27 | 15-24 |
| War ends: defender fell / tributary / peace | 0.68-0.71 / 0 / 0.06-0.08 | 0.68-0.72 / 0 / 0.07-0.09 | 0.53-0.56 / 0.12-0.13 / 0.10-0.12 | 0.53-0.56 / 0.11-0.14 / 0.09-0.12 |
| One-city defenders that fall | 0.85 | 0.83-0.86 | 0.67-0.70 | 0.67-0.70 |
| Won sieges: annex / tributary / sack | 1 / 0 / 0 | 1 / 0 / 0 | 0.58-0.60 / 0.21-0.23 / 0.17-0.20 | 0.56-0.63 / 0.20-0.23 / 0.17-0.21 |
| Wars settled within a tick | 0.79-0.83 | 0.77-0.82 | 0.69-0.73 | 0.68-0.73 |
| Deaths: hunger | 0.12-0.20 | 0.04-0.09 | 0.11-0.19 | 0.04-0.09 |

- **Cities.** Food flows steepen the hierarchy and bring urban share to
  0.10-0.12, but the slope (-0.34 to -0.41) stays flatter than pre-modern
  systems (-0.6 to -1) and the largest city is 0.07-0.10% of the world
  (reference 0.2-0.5%). City food in fw at the end: trade 0.36-0.41,
  rent 0.32-0.35, provincial spending 0.14-0.15, the capital's take
  0.12-0.15, the same in every seed; 9-10 of the 10 largest cities are
  capitals, all 10 on a coast or river. States at the end spread more
  (largest / 10th by cells 2.5-7.0) than their capitals (1.7-2.6): little
  of a large inland state's tax reaches its capital over land.
- **Crises.** The worst 300-yr population fall after year 3000, per run:
  seeds 103 and 104 have slow falls of 24-38% over 200-300 yrs; the other
  seeds' worst are one-tick plagues of 13-22%. In the slow falls, under
  ff and fw the cities whose urban population is below URBAN_MIN rise
  from 24-40 to 85-92 (a quarter to a half of all cities), against 28-29
  to 37 under base; urban population falls 29-42%. The number of cities
  still rises through every fall (+0 to +14%): founding reads the cell's
  people. Plagues barely moved the urban measure of the day, which put
  a city cell's losses on its rural part first; urban() was made
  proportional after the batch (diagnostics.md).
- **Wars.** `war_terms` does what it was built for: a fifth of won
  sieges end in tribute and a fifth in a sack, two to three times as
  many vassals stand, and fewer one-city states vanish. The largest
  states shrink a little (base 7.2-13.3M km², fw 5.6-9.4M).
- **Population** falls by a quarter with `food_flow` (the trade term of
  the old boost made food). Hunger deaths fall from 12-20% to 4-9% of
  recorded deaths.
- **Deaths by cause** (fw): dragons 0.51-0.60 (the growth cut under
  dragon hazard), feuds 0.18-0.19, raids 0.08-0.10, plague 0.06-0.09,
  hunger 0.04-0.09, war levies, sieges, sacks and clearances together
  0.03-0.05.

### 2026-11-09 urban batch: `urban_city` and capital levers (runs/urban.sh) — ub_, al_ done; tx_, km_, ab_ rerunning

ub_ (defaults: food_flow, war_terms, urban_city), tx_ (FF_TAX 0.10),
km_ (FF_CAP_KM 500), ab_ (FF_ABS 0.5), al_ (all three); seeds 101-106.
Compare with the realism batch's fw_ (urban_city not yet built). The
urban measure became proportional between the batches (records only),
so urban numbers in fw_ and ub_ differ slightly in form.

Test before the batch (seed 101 from a year-5000 state, all three
switches turned on there, 40 ticks): no errors; 25 cities abandoned in
200 years (partly the switch-on transient), causes decline 10, salted
land 7, sack 3, raid 2, dry climate, dragon, clearance 1 each.

Launch: 19 of the 30 jobs (al 106, all tx, km, ab) exited at launch with
empty logs from 20:57 on, while the jobs already running finished; no
cause found (nothing in the system log; a short rerun of tx 101 ran).
Rerun by `runs/urban_rerun.sh`, same code. Dropbox is turning finished
run files into online-only placeholders (the disk is 93% full) and some
do not download: `realism.py` now skips a run whose files it reads are
online-only and names it. Below, n = 5 per group (fw 106 and ub 102
skipped).

Results so far (`realism.py --group`, ranges over seeds):

| | fw (before 2B) | ub (2B) | al (2B + 3 levers) |
|---|---|---|---|
| largest city, k fe | 119-163 | 96-141 | 239-456 |
| largest city, share of world | 0.08-0.10% | 0.06-0.09% | 0.19-0.29% |
| largest / 10th city | 1.7-2.6 | 1.7-2.2 | 2.1-3.9 |
| rank-size slope, end | -0.36..-0.41 | -0.33..-0.39 | -0.55..-0.62 |
| rank-size slope, yr 4000 | -0.60..-0.80 | -1.06..-1.30 | -0.97..-1.12 |
| urban share, end | 0.11-0.12 | 0.09 | 0.11-0.12 |
| largest state, M km2 | 6.2-9.4 | 4.9-6.7 | 5.2-9.2 |
| population end, M | 150-177 | 124-160 | 120-178 |
| cities founded | 924-1172 | 1549-2577 | 1586-1993 |
| cities ended, share | 0.06-0.08 | 0.50-0.64 | 0.50-0.57 |
| cities, change over worst fall | 0..+0.10 | -0.27..+0.05 | -0.27..+0.06 |

Wars, war endings, siege terms and deaths by cause barely move between
the three.

- **The three levers together put the largest city in the reference
  range** (0.2-0.5% of the world) and steepen the end slope. Which lever
  does it waits for tx_, km_, ab_.
- **2B's city turnover is mostly an artifact** (C, all six ub seeds):
  7,508 cities abandoned; 93% at age 100-150 (median exactly 100, the
  first tick URBAN_GRACE allows), 91% never reaching URBAN_MIN; 98%
  refounded, 73% within 5 years of URBAN_REFOUND running out; 679 cells
  abandoned 4+ times, one 22 times. al: 87%, 84%, 69%. A town is founded
  on the cell's people (above the founding size, the local best site)
  but kept on its urban food, so a dense cell with too little hinterland
  rent is founded, starves, is abandoned and is founded again: a 200-year
  cycle. URBAN_REFOUND only lengthens it. Few such towns stand at any
  moment (cities below URBAN_MIN at the end are 0.1-1.8% of cities), so
  the standing hierarchy and largest city are little affected; city
  counts, endings and the city change over falls are. Polity counts
  barely change (fw 4,418-6,637, ub 4,452-6,353): most of these towns
  join the state that holds the cell.

### 2026-11-17 WP1 stage F: new baseline on named random streams (`wp1f_base_`, `wp1f_fullclim_`)

What it tested: the model after WP1 (speed refactors, the climate's local
field at half resolution, every draw from a named stream; D12, U). Seeds
101-104 and 106, sweep settings, 8,000 years, defaults. `wp1f_base_`: as
committed (668ac79). `wp1f_fullclim_`: the same with
`--set CLIM_LOCAL_COARSE=1`, the full-resolution local field, to separate
the climate change from the stream split. Compared with `ub_` (seeds 101-104
and 106, 2026-11-09 code, the same settings; in the old Dropbox runs
folder). Up to year 5,000, seed 101 under the pre-stream code still matched
`ub_seed101` exactly (`wp1_ref_6000`), so the gap below is from stage F and
the climate field, not from earlier drift. Saved states for branching:
`runs/wp1f_s101_y3000.pkl`, `wp1f_s101_y5000.pkl`, `wp1f_s103_y3000.pkl`,
`wp1f_s103_y5000.pkl` (260-290 MB each).

| measure | ub (old) | wp1f_base | wp1f_fullclim |
|---|---|---|---|
| population end, M (by seed 101/102/103/104/106) | 137/125/159/160/124 | 86/164/120/110/116 | 140/147/165/178/108 |
| population end, median | 137 | 116 | 147 |
| population yr 6000, median | 79 | 61 | 76 |
| urban share, end | 0.089-0.093 | 0.061-0.093 | - |
| largest city (k fe) | 96-131 | 75-123 | - |
| largest state, M km2 | 4.9-6.7 | 2.7-8.7 | - |
| wars | 4,690-8,557 | 2,666-8,300 | - |
| wars settled within a tick | 0.66-0.72 | 0.61-0.68 | - |
| cities founded | 1,549-2,577 | 1,761-2,244 | - |
| cities ended, share | 0.50-0.64 | 0.62-0.76 | - |
| deaths: dragon | 0.53-0.61 | 0.60-0.64 | - |
| deaths: feud | 0.20-0.22 | 0.18-0.21 | - |

(`-`: not run through `realism.py`.) War endings, siege terms and the other
death causes overlap between `ub` and `wp1f_base`.

- **The spread across seeds is wider than before** (end population 86-164M
  against 124-160M), and the median is lower. With five seeds a side
  that is not distinguishable from chance (rank-sum p about 0.1).
- **The half-resolution climate field may lower population, but the
  evidence is weak.** With the full-resolution field the median comes
  back to 147M (p about 0.15 against `wp1f_base`). The field's own
  statistics are the same in both batches: moisture sd 0.551 against
  0.546, mean share of people under drought 0.092 against 0.091, ticks
  with over 30% of people under drought 0.051 against 0.049, 7-10 against
  6-12 great droughts per run. Spatial correlation at lags of 1-12 cells
  matched to within 0.015 (stage D check). No mechanism is apparent, so I
  read it as seed noise (C), and kept the faster field. Recheck when WP2's
  metrics give a larger batch; `CLIM_LOCAL_COARSE=1` restores the old
  field exactly.
- 8,000 years now take 7.5-8.5 minutes on a lightly loaded machine (the
  guide's figure was about 14).
