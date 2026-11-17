"""
Ten peoples, broad rebalance of 2026-10-29. Colours (U, 2026-10-30):
ColorBrewer Set3, in roster order. Same peoples, biome
affinities, body sizes and head starts as peoples_headstart; cultural
traits reset from the user's descriptions (U→C: the user's words, Claude's
numbers), plus hierarchy, patience and per-people variability.

Words to numbers (C): very low 0.10, low 0.20-0.25, moderate 0.50,
higher/high 0.70-0.80, very/extremely high 0.90-0.95. Traits the user did
not mention keep their peoples_headstart value (marked "kept" below) or,
for the new traits, 0.5.

  Humans      moderate across the board, high variance (variance 2.0)
  Lizardfolk  like Humans, lower tolerance, higher cohesion and trade
  Snake folk  like Humans, lower tolerance, higher hierarchy and statecraft
  Elves       like Humans, very low tolerance, low violence, higher
              statecraft, lower expansion
  Frogloks    high growth (live with dragons), moderate tolerance and
              violence, very low separation and innovation
  Goblins     high growth (live with dragons), low tolerance, high
              violence, very low separation and innovation
  Ogres,      high violence, moderate separation, low tolerance, high
  Trolls      hierarchy, low innovation, high strength (size kept)
  Giants      like Ogres/Trolls; slightly higher innovation and tolerance,
              much higher cohesion, higher separation
  Dwarves     extremely high cohesion, low tolerance, high trade, low
              seafaring and expansion, high innovation, very low separation
  patience    high: Elves, Lizardfolk, Snake folk; very low: Ogres, Trolls,
              Giants, Goblins; moderate: Frogloks, Humans, Dwarves
  conformity  very high: Elves, Dwarves; very low: Humans; else moderate
  proselytism high: Humans, Lizardfolk; very low: Elves, Snake folk; else
              moderate
  dominance   (U, 2026-10-29, from Claude's proposal; numbers C) high:
              Snake folk, Humans; moderate: Lizardfolk, Giants, Dwarves;
              low: Elves, Goblins, Frogloks, Ogres, Trolls
  craftsmanship (U, 2026-10-29; numbers U→C) very high: Elves, Dwarves;
              average: Humans, Lizardfolk, Snake folk; low: Frogloks,
              Goblins; very low: Ogres, Trolls, Giants
  dragon hosts (U, 2026-10-30): Goblins and Frogloks never ward off a
              dragon
  lifespan    (U, 2026-10-30; a biological trait, multiple of a human
              life): Humans 1.0; Goblins 0.43 (a 30-year-old goblin is
              like a 70-year-old human); Frogloks 0.71 (50 ~ 70); Lizardfolk
              and Snake folk 1.15; Ogres 0.9; Giants 1.5; Trolls 2.0;
              Dwarves 2.5; Elves 10. Fixed per people (not inherited
              culture). Not yet used by the model (planned: reign length).
  All values are a people's means; founding groups and daughter lineages
  vary around them (U).

Biomes (U, 2026-10-29): Frogloks tied to jungle (the world has no
separate swamp class) more tightly than any other people, and barely
seafaring; Lizardfolk and Snake folk all but shut out of tundra. Lizardfolk temperate forest
0.8 -> 1.1 (U, 2026-10-30: their homeland island is half temperate
forest; number C). Numbers
C: Frogloks G/F/J/D/T 0.15/0.35/1.6/0.02/0.02, seafaring 0.05, and a
wetland preference wet=1.0 (U, 2026-10-29: capacity x up to 3 on the
wettest ground, no settling penalty for wetness); Lizardfolk
and Snake folk tundra 0.02.

r for Frogloks and Goblins is C. 0.06 (first set) let them grow at the
human rate under a dragon, and they ran over everyone (U: tone down). Now
0.04: 1.7x the human rate, and still just above zero growth under one
dragon at the worst group size.

superiority (U, 2026-11-01; numbers U→C): how far a culture rejects
  influence from other peoples. High across the board (0.75); Humans and
  Lizardfolk lower (0.50); Elves loath to adapt (0.90).

Run with:  worldsim.py --peoples peoples_balanced --starts 20 --years 6400
"""


def _b(key, label, color, r, violence, expansion, separation, cohesion,
       statecraft, innovation, seafaring, trade, tolerance, hierarchy,
       patience, aff, head, size, variance=1.0, conformity=0.5,
       proselytism=0.5, wet=0.0, dominance=0.5, craftsmanship=0.5,
       dragon_host=False, lifespan=1.0, superiority=0.75, hardy=1.0,
       fortress=0.0):
    g, f, j, d, t = aff
    return dict(key=key, label=label, color=color, r=r, violence=violence,
                expansion=expansion, separation=separation,
                cohesion=cohesion, statecraft=statecraft,
                innovation=innovation, seafaring=seafaring, trade=trade,
                tolerance=tolerance, hierarchy=hierarchy, patience=patience,
                conformity=conformity, proselytism=proselytism, wet=wet,
                dominance=dominance, craftsmanship=craftsmanship,
                dragon_host=dragon_host, lifespan=lifespan,
                superiority=superiority, hardy=hardy, fortress=fortress,
                affinity={"Grassland": g, "Temperate forest": f,
                          "Jungle": j, "Desert": d, "Tundra": t},
                start=None, head=head, size=size, variance=variance)


PEOPLES = [
    #      key    label         color            r      viol  expn  sep   coh   state innov sea   trade tol   hier  pati   G    F    J    D    T              head size
    _b("Hum", "Humans",     (141, 211, 199),  0.024, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, (1.2, 1.0, 0.9, 0.9, 0.7),    0,  1.0, variance=2.0, conformity=0.10, proselytism=0.75, dominance=0.75, craftsmanship=0.50, lifespan=1.0, superiority=0.50),
    _b("Gob", "Goblins",    (255, 255, 179),  0.035, 0.85, 0.70, 0.10, 0.40, 0.30, 0.10, 0.20, 0.30, 0.20, 0.50, 0.10, (0.9, 1.0, 1.1, 0.7, 0.5),    0,  0.35, dominance=0.20, craftsmanship=0.20, dragon_host=True, lifespan=0.43),
    _b("Liz", "Lizardfolk", (190, 186, 218),  0.020, 0.50, 0.50, 0.50, 0.75, 0.50, 0.50, 0.50, 0.75, 0.30, 0.50, 0.75, (0.8, 1.1, 1.4, 1.0, 0.02), 150,  1.0, proselytism=0.75, dominance=0.50, craftsmanship=0.50, lifespan=1.15, superiority=0.50),
    _b("Frg", "Frogloks",   (251, 128, 114), 0.040, 0.50, 0.35, 0.10, 0.40, 0.30, 0.10, 0.05, 0.30, 0.50, 0.50, 0.50, (0.15, 0.35, 1.6, 0.02, 0.02),  150,  0.5, wet=1.0, dominance=0.20, craftsmanship=0.20, dragon_host=True, lifespan=0.71),
    _b("Snk", "Snake folk", (128, 177, 211),  0.019, 0.50, 0.50, 0.50, 0.50, 0.75, 0.50, 0.50, 0.50, 0.30, 0.75, 0.75, (0.7, 0.6, 1.2, 1.3, 0.02), 400,  1.0, proselytism=0.10, dominance=0.80, craftsmanship=0.50, lifespan=1.15),
    _b("Elf", "Elves",      (253, 180, 98), 0.015, 0.25, 0.30, 0.50, 0.50, 0.70, 0.50, 0.50, 0.50, 0.10, 0.50, 0.75, (0.6, 1.4, 1.0, 0.4, 0.6),  400,  1.0, conformity=0.90, proselytism=0.10, dominance=0.25, craftsmanship=0.90, lifespan=10.0, superiority=0.90),
    _b("Trl", "Trolls",     (179, 222, 105),   0.019, 0.85, 0.18, 0.50, 0.65, 0.25, 0.20, 0.15, 0.20, 0.20, 0.80, 0.10, (0.7, 0.8, 1.4, 0.5, 0.3),    0, 10.0, dominance=0.20, craftsmanship=0.10, lifespan=2.0, hardy=0.3),
    _b("Ogr", "Ogres",      (252, 205, 229),   0.020, 0.85, 0.20, 0.50, 0.75, 0.35, 0.20, 0.10, 0.15, 0.20, 0.80, 0.10, (1.2, 0.8, 0.8, 0.8, 0.6),    0, 20.0, dominance=0.20, craftsmanship=0.10, lifespan=0.9),
    _b("Gnt", "Giants",     (217, 217, 217), 0.017, 0.70, 0.15, 0.70, 0.90, 0.55, 0.30, 0.20, 0.30, 0.35, 0.80, 0.10, (1.0, 1.0, 0.7, 0.6, 1.2),    0, 30.0, dominance=0.50, craftsmanship=0.30, lifespan=1.5),
    _b("Dwf", "Dwarves",    (188, 128, 189),  0.019, 0.40, 0.10, 0.05, 0.95, 0.80, 0.85, 0.10, 0.80, 0.20, 0.50, 0.50, (0.9, 1.0, 0.6, 0.8, 1.0),    0,  0.6, conformity=0.90, dominance=0.50, craftsmanship=0.90, lifespan=2.5, fortress=1.0),
]
