"""Generic EO spacecraft candidates (Tier 0 placeholder).

Frame: +X cross-track (wing side), +Y along-track, +Z zenith (nadir = -Z).
Every solid sits inside `with s.part(name)`, name exactly as in desc.py.

Brief (George, 19 Oct 2026): "it should look like an EO satellite not a comms
satellite (many satellite icons overemphasise the antenna)". So: boxy bus,
nadir-facing payload pointing DOWN, one or two wings, small star trackers,
and no parabolic dish anywhere.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/
from house_art.kit import Camera, Face, Scene, _add  # noqa: E402

DESIGNS, ASSERTS = {}, {}
_W = {"assert": "visible", "element": "solar array", "min_frac": 0.10}


def star_trackers(s, pts, axis_tilt):
    with s.part("star trackers"):
        for (x, y, z) in pts:
            tip = (x + axis_tilt[0], y + axis_tilt[1], z + axis_tilt[2])
            s.box((x, y, z - 0.02), (0.20, 0.20, 0.16), "white")
            s.frustum((x, y, z + 0.06), tip, 0.07, 0.12, "white", n=8)
            s.disc(tip, axis_tilt, 0.12, "dark", shade=3)


# ------------------------------------------------- A: optical imager ----
def optical():
    s = Scene(Camera(az=36, el=16))
    with s.part("bus"):
        s.prism((0, 0, 0.55), (1.40, 1.20, 1.30), "gold", bevel=0.10)
        s.greeble((0.71, -0.55, 0.0), (0, 1.10, 0), (0, 0, 1.10),
                  [(.10, .10, .34, .22), (.52, .10, .36, .16), (.10, .44, .80, .10),
                   (.10, .62, .30, .26), (.50, .62, .38, .20)], "gold", 2)
        s.plate((-0.70, -0.60, 1.20), (1.40, 0, 0), (0, 1.20, 0), 0.04, "white")
    with s.part("telescope"):
        s.box((0, 0, -0.18), (0.95, 0.95, 0.16), "white")
        s.tube((0, 0, -0.26), (0, 0, -1.25), 0.40, "white", n=14)
        s.frustum((0, 0, -1.25), (0, 0, -1.55), 0.40, 0.46, "dark", n=14)
        for z in (-0.55, -0.95):
            s.tube((0, 0, z), (0, 0, z - 0.05), 0.415, "white", n=14, caps=False)
    with s.part("solar array"):
        for sgn in (1, -1):
            root = (sgn * 0.70, 0.0, 0.85)
            s.strut(root, _add(root, (sgn * 0.40, 0, 0)), 0.06, "white")
            s.wing(_add(root, (sgn * 0.40, -0.55, 0)), (sgn * 2.70, 0, 0),
                   (0, 1.10, 0), "panel", cols=3)
    star_trackers(s, [(-0.40, 0.35, 1.30), (-0.05, 0.40, 1.30)], (-0.12, 0.10, 0.30))
    with s.part("downlink antenna"):
        s.box((0.50, -0.45, -0.16), (0.16, 0.16, 0.14), "white")
        s.frustum((0.50, -0.45, -0.23), (0.50, -0.45, -0.45), 0.05, 0.10, "white", n=8)
    return s


DESIGNS["optical"] = optical
ASSERTS["optical"] = [_W,
    {"assert": "visible", "element": "telescope", "min_frac": 0.08},
    {"assert": "touches", "elements": ["telescope", "bus"]},
    {"assert": "touches", "elements": ["solar array", "bus"]}]


# ---------------------------------------------------------- B: SAR ----
def sar():
    s = Scene(Camera(az=30, el=15))
    with s.part("bus"):
        s.prism((0, 0, 0.30), (1.30, 1.60, 1.10), "gold", bevel=0.10)
        s.greeble((0.66, -0.75, -0.20), (0, 1.50, 0), (0, 0, 0.95),
                  [(.08, .10, .30, .24), (.44, .10, .40, .16), (.08, .46, .84, .10),
                   (.08, .64, .30, .24), (.46, .64, .36, .20)], "gold", 2)
        s.plate((-0.65, -0.80, 0.85), (1.30, 0, 0), (0, 1.60, 0), 0.04, "white")
    with s.part("radar antenna panel"):
        for sy in (-0.55, 0.55):
            s.box((0, sy, -0.34), (0.20, 0.20, 0.20), "white")
        s.plate((-0.55, -2.60, -0.62), (1.10, 0, 0), (0, 5.20, 0), 0.16, "white")
        for i in range(1, 8):
            t = -2.60 + 5.20 * i / 8
            s.add(Face([(-0.55, t - 0.025, -0.535), (0.55, t - 0.025, -0.535),
                        (0.55, t + 0.025, -0.535), (-0.55, t + 0.025, -0.535)],
                       "white", struct=False, shade=3))
        for i in range(8):
            y0 = -2.60 + 5.20 * i / 8
            s.greeble((0.56, y0 + 0.06, -0.62), (0, 5.20 / 8 - 0.12, 0), (0, 0, 0.14),
                      [(0.0, 0.2, 1.0, 0.6)], "dark", 2, lift=0.01)
    with s.part("solar array"):
        root = (-0.65, 0.0, 0.55)
        s.strut(root, _add(root, (-0.45, 0, 0)), 0.06, "white")
        s.wing(_add(root, (-0.45, -0.60, 0)), (-3.40, 0, 0), (0, 1.20, 0),
               "panel", cols=4)
    star_trackers(s, [(0.30, 0.45, 0.89), (0.30, 0.05, 0.89)], (0.12, 0.08, 0.30))
    return s


DESIGNS["sar"] = sar
ASSERTS["sar"] = [_W,
    {"assert": "visible", "element": "radar antenna panel", "min_frac": 0.12},
    {"assert": "touches", "elements": ["radar antenna panel", "bus"]},
    {"assert": "touches", "elements": ["solar array", "bus"]}]


# ---------------------------------------------- C: compact smallsat ----
def smallsat():
    s = Scene(Camera(az=22, el=20))
    with s.part("bus"):
        s.prism((0, 0, 0), (0.90, 0.90, 0.90), "white", bevel=0.08)
        s.greeble((0.46, -0.40, -0.40), (0, 0.80, 0), (0, 0, 0.80),
                  [(.10, .10, .80, .36), (.10, .56, .36, .34), (.54, .56, .36, .34)],
                  "panel", None)
        s.greeble((-0.40, -0.46, -0.40), (0.80, 0, 0), (0, 0, 0.80),
                  [(.10, .10, .80, .36), (.10, .56, .80, .34)], "panel", None, lift=-0.02)
    with s.part("imager"):
        s.box((0, 0, -0.50), (0.50, 0.50, 0.10), "white")
        s.tube((0, 0, -0.55), (0, 0, -0.85), 0.18, "dark", n=12)
        s.disc((0, 0, -0.86), (0, 0, -1), 0.13, "dark", shade=3)
    with s.part("solar array"):
        for sgn in (1, -1):
            hinge = (sgn * 0.45, -0.36, 0.40)
            s.strut(hinge, _add(hinge, (sgn * 0.12, 0, 0)), 0.03, "white")
            s.wing(_add(hinge, (sgn * 0.12, 0.0, 0)), (sgn * 1.70, 0, 0),
                   (0, 0.72, 0), "panel", cols=2, rows=1, thick=0.04)
    star_trackers(s, [(-0.20, 0.25, 0.47)], (-0.08, 0.08, 0.22))
    with s.part("downlink antenna"):
        s.plate((0.10, -0.32, 0.45), (0.26, 0, 0), (0, 0.26, 0), 0.03, "gold")
    return s


DESIGNS["smallsat"] = smallsat
ASSERTS["smallsat"] = [_W,
    {"assert": "visible", "element": "imager", "min_frac": 0.03},
    {"assert": "touches", "elements": ["imager", "bus"]},
    {"assert": "touches", "elements": ["solar array", "bus"]}]
