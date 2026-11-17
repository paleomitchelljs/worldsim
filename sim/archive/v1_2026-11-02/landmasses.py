"""
Short codes for landmasses, and the key map that shows them.

Codes (C, 2026-11-01): S the southern continent; W the western islands,
numbered by area; N the islands north of the open sea; E the eastern
island; X the small outliers. Landmass ids are those of World().landmass
(stable for a given world.gpkg). Landmasses under 0.05M km2 have no code.

Run:
  ~/.venvs/worldsim/bin/python landmasses.py     # writes docs/landmass_key.png
"""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

CODES = {
    24: "S",
    33: "W1", 36: "W2", 20: "W3", 32: "W4", 34: "W5",
    22: "N1", 35: "N2", 26: "N3", 21: "N4",
    29: "E1",
    40: "X1", 42: "X2", 23: "X3", 41: "X4",
}
GROUPS = {
    "S": ["S"],
    "W": ["W1", "W2", "W3", "W4", "W5"],
    "N": ["N1", "N2", "N3", "N4"],
    "E": ["E1"],
    "X": ["X1", "X2", "X3", "X4"],
}
NUDGE = {"N4": (-70, 4)}          # key-map label offsets, pixels
IDS = {v: k for k, v in CODES.items()}


def code(lm):
    return CODES.get(int(lm), "-")


def ids(spec):
    """'W' or 'W1,N1' or '33' -> set of landmass ids."""
    out = set()
    for t in str(spec).split(","):
        t = t.strip()
        if not t:
            continue
        if t in GROUPS:
            out |= {IDS[c] for c in GROUPS[t]}
        elif t in IDS:
            out.add(IDS[t])
        else:
            out.add(int(t))
    return out


def key_map(path=os.path.join(HERE, "docs", "landmass_key.png"), scale=2):
    import sys
    sys.path.insert(0, HERE)
    import worldsim
    from PIL import Image, ImageDraw
    W = worldsim.World()
    img = W.base.astype(float) * 0.35 + 150
    col = {"S": (205, 92, 92), "W": (70, 130, 180), "N": (120, 170, 90),
           "E": (230, 150, 50), "X": (150, 120, 180)}
    for lm, c in CODES.items():
        m = W.landmass == lm
        img[W.row[m], W.col[m]] = col[c[0]]
    im = img[W.r0:W.r1].clip(0, 255).astype(np.uint8)
    im = Image.fromarray(np.repeat(np.repeat(im, scale, 0), scale, 1))
    d = ImageDraw.Draw(im)
    f, fs = worldsim.font(18), worldsim.font(12)
    for lm, c in CODES.items():
        m = W.landmass == lm
        # label at the cell nearest the centroid that lies on the landmass
        cx, cy = W.col[m].mean(), W.row[m].mean()
        k = np.argmin((W.col[m] - cx) ** 2 + (W.row[m] - cy) ** 2)
        x = (W.col[m][k] + 0.5) * scale
        y = max((W.row[m][k] - W.r0 + 0.5) * scale, 10)
        dx, dy = NUDGE.get(c, (0, 0))
        x = min(max(x + dx, 40), im.width - 40)
        y += dy
        a = W.landmass_area[lm] / 1e6
        d.text((x, y), c, fill=(255, 255, 255), font=f, anchor="mm",
               stroke_width=3, stroke_fill=(0, 0, 0))
        d.text((x, y + 15), f"{a:.2f}M km2" if a < 1 else f"{a:.1f}M km2",
               fill=(255, 255, 255), font=fs, anchor="mm",
               stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(path)
    return path


if __name__ == "__main__":
    print(key_map())
