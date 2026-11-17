"""
The five peoples. Edit freely: every number here is a dial.

All traits are 0..1 unless noted. Names are placeholders pending the
naming-conventions pass; the letters are what the sim logs.

  r            intrinsic growth rate per year at full agriculture
  violence     propensity to start wars and raid; severity of sacks
  expansion    drive to emigrate before land is full; pioneer leaps
  separation   avoidance of other peoples: steers settlers away from
               foreign borders, and decides whether conquered foreigners
               are kept as subjects (low) or cleared off the land (high)
  cohesion     how fast group solidarity regrows (Turchin's asabiya);
               holds large states together
  statecraft   how far a capital can project rule (admin reach growth)
               and how readily towns join an existing state rather than
               standing alone as city-states
  innovation   speed of agricultural / metallurgical invention
  seafaring    how fast sailing range grows; sea colonization rate
  trade        willingness to trade; dampens war with partners
  tolerance    acceptance of the unlike: gates and speeds trade, alliance
               and fusion of states (kin need little, other peoples need
               high tolerance on both sides); softens clearances and
               the unrest of foreign subjects
  affinity     carrying-capacity multiplier by biome (homeland bias)
  start        None = auto-pick a site that suits the affinity;
               or (lon, lat) to pin the founding group
"""

PEOPLES = [
    dict(key="A", label="valley farmers",
         color=(214, 170, 52),
         r=0.022, violence=0.25, expansion=0.35, separation=0.40,
         cohesion=0.55, statecraft=0.70, innovation=0.85, seafaring=0.25,
         trade=0.70, tolerance=0.60,
         affinity={"Grassland": 1.2, "Temperate forest": 1.0, "Jungle": 0.7,
                   "Desert": 0.9, "Tundra": 0.4},
         start=None),
    dict(key="B", label="horse raiders",
         color=(196, 60, 52),
         r=0.016, violence=0.90, expansion=0.85, separation=0.55,
         cohesion=0.85, statecraft=0.45, innovation=0.35, seafaring=0.05,
         trade=0.25, tolerance=0.25,
         affinity={"Grassland": 1.4, "Temperate forest": 0.7, "Jungle": 0.4,
                   "Desert": 1.0, "Tundra": 0.7},
         start=None),
    dict(key="C", label="sea traders",
         color=(54, 128, 204),
         r=0.018, violence=0.40, expansion=0.60, separation=0.30,
         cohesion=0.45, statecraft=0.40, innovation=0.65, seafaring=0.95,
         trade=0.95, tolerance=0.80,
         affinity={"Grassland": 1.0, "Temperate forest": 1.0, "Jungle": 0.9,
                   "Desert": 0.6, "Tundra": 0.5},
         start=None),
    dict(key="D", label="forest clans",
         color=(62, 150, 74),
         r=0.014, violence=0.55, expansion=0.25, separation=0.90,
         cohesion=0.75, statecraft=0.30, innovation=0.45, seafaring=0.20,
         trade=0.20, tolerance=0.15,
         affinity={"Grassland": 0.8, "Temperate forest": 1.4, "Jungle": 1.1,
                   "Desert": 0.3, "Tundra": 0.8},
         start=None),
    dict(key="E", label="temple builders",
         color=(150, 82, 186),
         r=0.020, violence=0.60, expansion=0.50, separation=0.65,
         cohesion=0.65, statecraft=0.95, innovation=0.70, seafaring=0.30,
         trade=0.50, tolerance=0.35,
         affinity={"Grassland": 1.0, "Temperate forest": 0.9, "Jungle": 1.3,
                   "Desert": 1.0, "Tundra": 0.3},
         start=None),
]
