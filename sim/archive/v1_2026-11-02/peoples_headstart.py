"""
Ten peoples, head-start scenario. Same trait meanings as peoples.py.

head: years of head start. Elves and Snake folk found first; Lizardfolk and
Frogloks arrive 250 years later; everyone else 400 years after the Elves
and Snake folk, into whatever land is still empty. (With 20 founding groups
per people, the earlier 1500-year head start filled the world before the
latecomers arrived.)

size: combat worth per head relative to a human (war strength and raids).
Giants 30, Ogres 20, Trolls 10; Humans, Lizardfolk, Snake folk and Elves 1;
Dwarves, Frogloks and Goblins below 1. Each head also eats size**0.75
humans' food (--size-food kleiber, the default), so the land carries fewer
large bodies.

Humans and Goblins have the highest growth; Humans the highest tolerance.
Goblins: low tech, low tolerance, high violence. Lizardfolk: close to Humans
but less tolerant. Snake folk: more violent and less tolerant than
Lizardfolk. Elves: low on everything. Frogloks: Goblins with less violence.
Trolls, Ogres, Giants, Dwarves: as in peoples_fantasy, but with the lowest
expansion. Biome affinities are kept from peoples_fantasy.

Run with:  worldsim.py --peoples peoples_headstart --starts 20 --years 6400
"""
from peoples_fantasy import _p


def _h(p, head, size):
    p["head"] = head
    p["size"] = size
    return p


PEOPLES = [
    #      key    label         color            r      viol  expn  sep   coh   state innov sea   trade  tol   G    F    J    D    T                head  size
    _h(_p("Hum", "Humans",     (235, 195, 70),  0.024, 0.40, 0.60, 0.35, 0.55, 0.75, 0.85, 0.50, 0.75, 0.85, (1.2, 1.0, 0.9, 0.9, 0.7)),    0,  1.0),
    _h(_p("Gob", "Goblins",    (245, 135, 35),  0.024, 0.85, 0.70, 0.55, 0.40, 0.30, 0.20, 0.20, 0.30, 0.15, (0.9, 1.0, 1.1, 0.7, 0.5)),    0,  0.35),
    _h(_p("Liz", "Lizardfolk", (40, 190, 160),  0.020, 0.45, 0.60, 0.45, 0.60, 0.75, 0.80, 0.45, 0.65, 0.45, (0.8, 0.8, 1.4, 1.0, 0.3)),  150,  1.0),
    _h(_p("Frg", "Frogloks",   (235, 110, 185), 0.021, 0.55, 0.65, 0.55, 0.40, 0.30, 0.20, 0.40, 0.30, 0.15, (0.5, 0.9, 1.5, 0.2, 0.2)),  150,  0.5),
    _h(_p("Snk", "Snake folk", (150, 65, 195),  0.019, 0.70, 0.60, 0.70, 0.65, 0.80, 0.75, 0.35, 0.50, 0.25, (0.7, 0.6, 1.2, 1.3, 0.2)),  400,  1.0),
    _h(_p("Elf", "Elves",      (130, 225, 120), 0.015, 0.20, 0.25, 0.30, 0.30, 0.25, 0.25, 0.20, 0.25, 0.25, (0.6, 1.4, 1.0, 0.4, 0.6)),  400,  1.0),
    _h(_p("Trl", "Trolls",     (140, 90, 50),   0.019, 0.80, 0.18, 0.80, 0.65, 0.25, 0.20, 0.15, 0.20, 0.15, (0.7, 0.8, 1.4, 0.5, 0.3)),    0, 10.0),
    _h(_p("Ogr", "Ogres",      (210, 55, 45),   0.020, 0.90, 0.20, 0.75, 0.75, 0.35, 0.25, 0.10, 0.15, 0.10, (1.2, 0.8, 0.8, 0.8, 0.6)),    0, 20.0),
    _h(_p("Gnt", "Giants",     (190, 190, 225), 0.017, 0.70, 0.15, 0.85, 0.65, 0.55, 0.45, 0.20, 0.30, 0.20, (1.0, 1.0, 0.7, 0.6, 1.2)),    0, 30.0),
    _h(_p("Dwf", "Dwarves",    (55, 110, 215),  0.019, 0.40, 0.15, 0.65, 0.85, 0.80, 0.85, 0.35, 0.65, 0.40, (0.9, 1.0, 0.6, 0.8, 1.0)),    0,  0.6),
]
