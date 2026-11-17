"""
Ten fantasy peoples. Same trait meanings as peoples.py.

tolerance: willingness to trade with, ally with and fuse into states of
groups unlike oneself. Within a people moderate tolerance suffices; across
peoples both sides need it high.

Run with:  worldsim.py --peoples peoples_fantasy
"""


def _p(key, label, color, r, violence, expansion, separation, cohesion,
       statecraft, innovation, seafaring, trade, tolerance, aff):
    g, f, j, d, t = aff
    return dict(key=key, label=label, color=color, r=r, violence=violence,
                expansion=expansion, separation=separation,
                cohesion=cohesion, statecraft=statecraft,
                innovation=innovation, seafaring=seafaring, trade=trade,
                tolerance=tolerance,
                affinity={"Grassland": g, "Temperate forest": f,
                          "Jungle": j, "Desert": d, "Tundra": t},
                start=None)


PEOPLES = [
    #   key    label         color            r      viol  expn  sep   coh   state innov sea   trade  tol   G    F    J    D    T
    _p("Hum", "Humans",     (235, 195, 70),  0.022, 0.40, 0.60, 0.35, 0.55, 0.75, 0.85, 0.50, 0.75, 0.70, (1.2, 1.0, 0.9, 0.9, 0.7)),
    _p("Liz", "Lizardfolk", (40, 190, 160),  0.019, 0.75, 0.65, 0.80, 0.80, 0.90, 0.65, 0.45, 0.35, 0.25, (0.8, 0.8, 1.4, 1.0, 0.3)),
    _p("Trl", "Trolls",     (140, 90, 50),   0.019, 0.80, 0.55, 0.80, 0.65, 0.25, 0.20, 0.15, 0.20, 0.15, (0.7, 0.8, 1.4, 0.5, 0.3)),
    _p("Ogr", "Ogres",      (210, 55, 45),   0.020, 0.90, 0.75, 0.75, 0.75, 0.35, 0.25, 0.10, 0.15, 0.10, (1.2, 0.8, 0.8, 0.8, 0.6)),
    _p("Elf", "Elves",      (130, 225, 120), 0.016, 0.30, 0.30, 0.75, 0.70, 0.65, 0.80, 0.35, 0.50, 0.30, (0.6, 1.4, 1.0, 0.4, 0.6)),
    _p("Gob", "Goblins",    (245, 135, 35),  0.018, 0.65, 0.70, 0.55, 0.40, 0.30, 0.45, 0.20, 0.35, 0.45, (0.9, 1.0, 1.1, 0.7, 0.5)),
    _p("Gnt", "Giants",     (190, 190, 225), 0.017, 0.70, 0.65, 0.85, 0.65, 0.55, 0.45, 0.20, 0.30, 0.20, (1.0, 1.0, 0.7, 0.6, 1.2)),
    _p("Snk", "Snake folk", (150, 65, 195),  0.018, 0.65, 0.55, 0.90, 0.75, 0.90, 0.80, 0.30, 0.40, 0.15, (0.7, 0.6, 1.2, 1.3, 0.2)),
    _p("Dwf", "Dwarves",    (55, 110, 215),  0.019, 0.40, 0.35, 0.65, 0.85, 0.80, 0.85, 0.35, 0.65, 0.40, (0.9, 1.0, 0.6, 0.8, 1.0)),
    _p("Frg", "Frogloks",   (235, 110, 185), 0.020, 0.35, 0.35, 0.35, 0.65, 0.60, 0.50, 0.55, 0.55, 0.75, (0.5, 0.9, 1.5, 0.2, 0.2)),
]
