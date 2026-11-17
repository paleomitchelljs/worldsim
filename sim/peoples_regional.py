"""
peoples_balanced with regional homelands (U, 2026-10-30, from the user's
sketch): each people's founding groups start and wander only in its
homeland; Goblins start anywhere, small islands included (dragons are
everywhere already). Other
peoples meet only by sea, or on the shared southern continent.

  Humans, Lizardfolk,    the western island and the island east of it
  Frogloks               (U, 2026-10-30: all three on both)
  Elves                  the northern island
  Snake folk             the eastern island
  Dwarves                two mountain regions of the southern continent
  Trolls, Giants, Ogres  regions of the southern continent

A part is the landmass at a point (lon, lat), optionally only within
radius_km of the point (C: points read off the sketch, radii C).

Run with:  worldsim.py --peoples peoples_regional --starts 20 ...
"""
import copy

from peoples_balanced import PEOPLES as _BAL

REGIONS = {
    "Hum": [dict(at=(-87.0, -7.0)), dict(at=(-50.0, -19.0))],
    "Liz": [dict(at=(-87.0, -7.0)), dict(at=(-50.0, -19.0))],
    "Frg": [dict(at=(-87.0, -7.0)), dict(at=(-50.0, -19.0))],
    "Elf": [dict(at=(-20.0, 22.0))],
    "Snk": [dict(at=(53.0, 4.0))],
    "Dwf": [dict(at=(97.0, 12.0), radius_km=1200),
            dict(at=(70.0, -59.5), radius_km=1200)],
    "Trl": [dict(at=(114.0, -2.5), radius_km=1200)],
    "Gnt": [dict(at=(109.0, -41.0), radius_km=1500)],
    "Ogr": [dict(at=(38.7, -53.0), radius_km=1200)],
}

PEOPLES = []
for _p in _BAL:
    q = copy.deepcopy(_p)
    if q["key"] in REGIONS:
        q["region"] = REGIONS[q["key"]]
    if q["key"] == "Gob":
        q["anywhere"] = True     # small islands too
    PEOPLES.append(q)
