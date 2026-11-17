# Batch of 2026-10-30 (agreed; built 2026-10-30, untested at scale)

Provenance: U = user's decision, C = Claude's proposal or numbers. All
new mechanics get a switch; records-only changes leave runs unchanged.

## Settlement and contact

1. **Trading posts** (U, form C): a state with strong trade and long
   sailing range plants a merchant minority in a foreign port city.
2. **Colonies on occupied coast** (U, form C): sea settlers may land on
   thinly held coast; chance falls as the local population rises. A colony
   founded from inside a state stays in that state (may later revolt).

## Trade, tolerance, alliances

3. **Trade experience from mean tie** (U): tolerance and trade experience
   use a state's mean tie strength (or a saturating v/(1+v)) instead of
   the sum over neighbours.
4. **Path-dependent tolerance** (U): contact softens tolerant cultures,
   hardens intolerant ones (two stable states).
5. **Alliance obligations** (U): a defending ally joins the war (war
   exposure, war cost); may refuse, and refusal ends the alliance.
6. **Alliances lapse** (U): a baseline break chance, and renewal at a
   ruler's death.
7. **Balance reversal** (U): balance alliances end when the threat is
   gone or one ally outgrows the other.
8. **Betrayal** (U): allies may attack each other at a reduced chance
   when war motives are strong.

## War

9. **Two-sided wars** (U): defenders counterattack and can retake or take
   cities during a war.

## Records (runs unchanged)

10. `relations.csv` (built), `wars.csv` (one row per war: dates, sides,
    peoples, landmasses, strengths, goal, end reason, sieges, captures,
    population moved, helping allies), `sieges.csv` (one row per siege:
    city, size, capital, PA, PB, odds, outcome), every revolt logged,
    single-tick breakups grouped, and a timeline tool (`--people`,
    `--landmass`, `--seed`, importance score).

## Rulers and generations

11. **Rulers** (U): a record per reign (state, accession, reign length,
    heirs, dynasty), `rulers.csv`. Reign length = 25 yrs x lifespan
    (biological roster trait, U). A ruler's death is a moment of risk:
    pretender war, provinces testing the new ruler, alliance lapse,
    vassal defection, opportunistic attacks, union of crowns. Crisis
    chance per death rises modestly with reign length (C, proposed).
12. **Inheritance** (U): single heirs as a rule; a drifting cultural
    trait `partibility` (0-1) gives the chance that rule is split among
    2-4 heirs, the state dividing around their seats.
13. **Memory scales with lifespan** (U), interacting with patience (U):
    memory length = base x lifespan x f(patience) for experience, war,
    churn and grievance (irredentism) memories.
14. **Spiky cultural change** (U): background change per year, plus
    spikes at generation turnover (every 25 yrs x lifespan per lineage)
    and after major events (wars, conquest, revolt, plague, famine,
    succession crisis).

## Revolts as experience

15. **Revolts harden** (U, 2026-10-30): lineages in a state that loses
    cities to revolt (and the rebels) get pushes like raids: violence up,
    tolerance down, separation and conformity up. Rates C.

## Resources and sites (`make_sites.py`)

16. **Landmass quotas** (U): every landmass of 0.1M km2 or more gets at
    least one unique-resource site; the rest are shared by area (largest
    remainder). 45 unique sites (U): South 20, W isle 6, E isle 3, Elf 3,
    Snake 2, the two 2M km2 islands 2 each, the rest 1 each.
17. **More kinds** (U: rare woods, useful plant fibres, a unique clay,
    etc.; kinds and rules C). Each kind 3-5 sites; a landmass's quota is
    filled with kinds whose rule fits there, favouring the rarest so far.
18. **Gold and silver** (U): rare commodities on the list, with somewhat
    more sites than other kinds, in types with their own placement and
    technology (C): placer gold (rivers draining relief, from the start),
    lode gold and silver (high relief, need bronze tools or better).
    Holdings stack; give trade value, strength (pay soldiers), a resource
    war motive, and run down with working over centuries (all U).
19. **Cultural value of goods** (U): craft-minded cultures value every
    kind more (x (0.5 + craftsmanship)); each culture also values kinds
    differently (a preference per kind). Value weights trade offers and
    the resource war motive. Preferences (U): drawn at random per people
    each run, inherited by lineages with drift, spread by trade and rule;
    kept out of cultural similarity (C). Editable later.
    Starting biases on the random draws (U, 2026-10-30; factors C:
    favoured x2, disdained x0.25): Elves favour rare plant materials
    (incense, spice, woods, fibres) and gems (lapis, jade, obsidian,
    pearls); Lizardfolk favour amber; Dwarves favour gems and metals
    (electrum, gold, silver); Goblins and Frogloks disdain plant
    materials (spice, incense, woods, fibres) and favour gems and animal
    goods (ivory, pearls, purple dye); Giants, Ogres and Trolls favour
    ivory, metals and gems. Humans and Snake folk: random only. Biases
    apply at the start; preferences then drift and spread.
20. Hearths unchanged (U).
21. Gold and silver sites are on top of the 45 (U): about 16 (5 placer
    gold, 5 lode gold, 6 silver; C), also under landmass quotas by area,
    so the Elf continent gets about one (U: few precious metals there,
    though its relief would otherwise give it many; trade for them is
    meant to pull on Elf culture).

# Batch of 2026-11-02 (built 2026-11-02, untested at scale)

## Rulers with traits (`ruler_traits`)

22. **The draw** (U): at accession a ruler gets violence, dominance,
    expansion and statecraft (as competence), drawn on the logit scale
    around the culture's mean (U; read as the population-weighted mean
    of the state's lineages of the ruler's people, C), from a fat-tailed
    distribution (Student-t, df 3, C), traits independent (C). Spread x
    (1.5 − conformity) (U): conformist cultures rarely produce deviant
    rulers. No mean correction (U): on the 0-1 scale rulers of extreme
    cultures are on average a little less extreme than their culture.
23. **The ruler is the state** (U): every state-level decision (war
    declaration and motives, administration progress, succession risk,
    statecraft-driven unrest) reads effective = culture + w x (ruler −
    culture). Elite pushback toward the prevailing culture (U): w rises
    with hierarchy (the king's influence) and falls with conformity
    (comfort with change); w = min(1, hierarchy x (1.5 − conformity))
    (C). Population-level behaviour (raids, migration, budding,
    acculturation) stays on the lineage (C).
24. **Pull on the populace** (U): the state's lineages of the ruler's
    people move toward the ruler's traits on the logit scale at a rate ∝
    hierarchy x administration (form of the product C): hierarchical,
    well-administered cultures move wholesale. Not scaled by the reign's
    success (U), so persistence of a ruler's mark rests on selection
    among states. Foreign subjects keep the existing foreign-rule path
    (C). The pull does not take acculturation's x (1.5 − conformity)
    (U, for now). Logged as its own term in `price.csv` (C).
25. **Mismatch revolts** (U): revolt chance rises with the ruler-culture
    gap (logit distance over the drawn traits, C), x conformity (U).
    The pull shrinks the gap during the reign, so each reign is a race
    between convergence and revolt.
26. **Administration falls** (U): (a) under a ruler less competent than
    his culture, at a rate ∝ the statecraft shortfall (C; a ruler equal
    to his culture changes nothing, so baseline runs are unchanged); (b)
    with turmoil: cities lost (war or revolt), raids suffered, internal
    revolts, each loss ∝ the share of the state affected (U), on the
    scale of the existing decay outside states (0.002 per year). Watch
    (C): lower administration shortens reach and raises provincial
    revolt, a positive feedback; judge by the variance of state
    lifetimes, add damping only if every run collapses.
27. **Violent peoples revolt more** (U): provincial revolt chance x (0.5
    + violence of the city's lineage) (form C). Today revolt chance has
    no violence term (`rebellions`). With `revolt_exp` (revolts push
    violence up), item 26 (turmoil lowers administration) and
    `RAID_ADMIN` (low administration lets raids in), this closes the
    loop: violence -> revolt -> lower administration -> raids and revolt
    experience -> more violence.
28. **Dynasties** (U): an heir draws around his predecessor's traits
    (same t-distribution and spread), not the culture's mean, so
    dynasties carry a character. A revolt ends the dynasty (U): the next
    ruler draws from the culture's mean after a disputed succession or
    pretender, and in a state founded by revolt (U); provincial revolts
    end it only if they take the capital (U).
    Partition heirs each continue the dynasty; union of crowns keeps the
    surviving ruler's (C). Note (C): heir-from-predecessor is a random
    walk on the logit, so a long dynasty drifts from its culture; the
    growing gap raises mismatch revolt (item 25) x conformity, so
    conformist cultures reset dynasties sooner. The dynastic cycle is
    the mechanism, not a side effect; check reign-gap and dynasty-length
    distributions in runs.
29. **Records** (C): ruler traits, w, deviance and dynasty id in
    `rulers.csv`, so a collapse can be traced to the reign that began
    it.

## Roads as technology (`road_tech`)

30. **Road engineering** (U): a technology, 0-1 per lineage, inherited
    and borrowed like the others. Invention ∝ innovation x (1 − level),
    only for lineages in a state (C); starts at 0 (C). Rates C.
31. **Efficacy = engineering x planning** (U): each cell keeps the
    quality of its road, set when built to ROAD_Q0 + (1 − ROAD_Q0) x
    the builder's engineering x (0.8 + 0.2 x administration) (form C),
    with a low floor (U) ROAD_Q0 = 0.15 (C): early roads are tracks,
    cutting travel cost by at most 7.5%. Blended by stock on rebuild
    (C). Travel cost x (1 − ROAD_EFFECT x stock x quality). Build
    amount per round stays 0.6 x administration x (1 − stock):
    administration mostly sets how much is built, with a small effect on
    quality (U). Without `road_tech`, quality = 1.

## Fortresses (`fortress`)

32. **Dwarven fortresses** (U, 2026-11-02: "an anti-hardiness: when
    they're attacked, they impose extra casualties on the attackers").
    A roster trait `fortress` (Dwarves 1, others 0, C). Raiders of a
    fortress people lose 5% of their people instead of 1%; a state
    besieging a fortress city loses 0.1 x the city's people across its
    cells (C), against the city's own 3% loss.

Switches: `ruler_traits` (22-26, 28-29; needs `rulers`), `turmoil` (26b),
`revolt_viol` (27), `road_tech` (30-31), `fortress` (32). With all five
off the model is unchanged (regression identical, 1500 yrs, seed 101,
both `--off all` and all others on).
