"""
Ten peoples, broad rebalance of 2026-10-29. Same peoples, colours, biome
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
  All values are a people's means; founding groups and daughter lineages
  vary around them (U).

Biomes (U, 2026-10-29): Frogloks tied to jungle (the world has no
separate swamp class) more tightly than any other people, and barely
seafaring; Lizardfolk and Snake folk all but shut out of tundra. Numbers
C: Frogloks G/F/J/D/T 0.15/0.35/1.6/0.02/0.02, seafaring 0.05, and a
wetland preference wet=1.0 (U, 2026-10-29: capacity x up to 3 on the
wettest ground, no settling penalty for wetness); Lizardfolk
and Snake folk tundra 0.02.

r for Frogloks and Goblins is C. 0.06 (first set) let them grow at the
human rate under a dragon, and they ran over everyone (U: tone down). Now
0.04: 1.7x the human rate, and still just above zero growth under one
dragon at the worst group size.

Run with:  worldsim.py --peoples peoples_balanced --starts 20 --years 6400
"""


def _b(key, label, color, r, violence, expansion, separation, cohesion,
       statecraft, innovation, seafaring, trade, tolerance, hierarchy,
       patience, aff, head, size, variance=1.0, conformity=0.5,
       proselytism=0.5, wet=0.0):
    g, f, j, d, t = aff
    return dict(key=key, label=label, color=color, r=r, violence=violence,
                expansion=expansion, separation=separation,
                cohesion=cohesion, statecraft=statecraft,
                innovation=innovation, seafaring=seafaring, trade=trade,
                tolerance=tolerance, hierarchy=hierarchy, patience=patience,
                conformity=conformity, proselytism=proselytism, wet=wet,
                affinity={"Grassland": g, "Temperate forest": f,
                          "Jungle": j, "Desert": d, "Tundra": t},
                start=None, head=head, size=size, variance=variance)


PEOPLES = [
    #      key    label         color            r      viol  expn  sep   coh   state innov sea   trade tol   hier  pati   G    F    J    D    T              head size
    _b("Hum", "Humans",     (235, 195, 70),  0.024, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, (1.2, 1.0, 0.9, 0.9, 0.7),    0,  1.0, variance=2.0, conformity=0.10, proselytism=0.75),
    _b("Gob", "Goblins",    (245, 135, 35),  0.040, 0.85, 0.70, 0.10, 0.40, 0.30, 0.10, 0.20, 0.30, 0.20, 0.50, 0.10, (0.9, 1.0, 1.1, 0.7, 0.5),    0,  0.35),
    _b("Liz", "Lizardfolk", (40, 190, 160),  0.020, 0.50, 0.50, 0.50, 0.75, 0.50, 0.50, 0.50, 0.75, 0.30, 0.50, 0.75, (0.8, 0.8, 1.4, 1.0, 0.02), 150,  1.0, proselytism=0.75),
    _b("Frg", "Frogloks",   (235, 110, 185), 0.040, 0.50, 0.35, 0.10, 0.40, 0.30, 0.10, 0.05, 0.30, 0.50, 0.50, 0.50, (0.15, 0.35, 1.6, 0.02, 0.02),  150,  0.5, wet=1.0),
    _b("Snk", "Snake folk", (150, 65, 195),  0.019, 0.50, 0.50, 0.50, 0.50, 0.75, 0.50, 0.50, 0.50, 0.30, 0.75, 0.75, (0.7, 0.6, 1.2, 1.3, 0.02), 400,  1.0, proselytism=0.10),
    _b("Elf", "Elves",      (130, 225, 120), 0.015, 0.25, 0.30, 0.50, 0.50, 0.70, 0.50, 0.50, 0.50, 0.10, 0.50, 0.75, (0.6, 1.4, 1.0, 0.4, 0.6),  400,  1.0, conformity=0.90, proselytism=0.10),
    _b("Trl", "Trolls",     (140, 90, 50),   0.019, 0.85, 0.18, 0.50, 0.65, 0.25, 0.20, 0.15, 0.20, 0.20, 0.80, 0.10, (0.7, 0.8, 1.4, 0.5, 0.3),    0, 10.0),
    _b("Ogr", "Ogres",      (210, 55, 45),   0.020, 0.85, 0.20, 0.50, 0.75, 0.35, 0.20, 0.10, 0.15, 0.20, 0.80, 0.10, (1.2, 0.8, 0.8, 0.8, 0.6),    0, 20.0),
    _b("Gnt", "Giants",     (190, 190, 225), 0.017, 0.80, 0.15, 0.70, 0.90, 0.55, 0.30, 0.20, 0.30, 0.30, 0.80, 0.10, (1.0, 1.0, 0.7, 0.6, 1.2),    0, 30.0),
    _b("Dwf", "Dwarves",    (55, 110, 215),  0.019, 0.40, 0.10, 0.05, 0.95, 0.80, 0.85, 0.10, 0.80, 0.20, 0.50, 0.50, (0.9, 1.0, 0.6, 0.8, 1.0),    0,  0.6, conformity=0.90),
]
