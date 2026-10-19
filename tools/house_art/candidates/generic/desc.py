"""Descriptions for the generic EO spacecraft candidates.

These depict NO real spacecraft. The references are text pages describing the
general configuration of an Earth-observation satellite; no image of any
specific vehicle informed the geometry.
"""
GEN = ("deliberately generic composition depicting no real spacecraft; drawn from "
       "the general configuration of Earth-observation satellites described in text "
       "references, not from any image of a specific vehicle")

TEXT_REFS = {
    "optical": ["https://en.wikipedia.org/wiki/Earth_observation_satellite",
                "https://en.wikipedia.org/wiki/Reconnaissance_satellite"],
    "sar": ["https://en.wikipedia.org/wiki/Earth_observation_satellite",
            "https://en.wikipedia.org/wiki/Synthetic-aperture_radar"],
    "smallsat": ["https://en.wikipedia.org/wiki/Earth_observation_satellite",
                 "https://en.wikipedia.org/wiki/Small_satellite"],
}

NO_DISH = {"element": "parabolic dish antenna",
           "reason": "Owner brief (George, 19 Oct 2026): the generic must read as an EO "
                     "satellite, not a comms satellite; a large dish is the comms cue"}

D = {
    "optical": {
        "mission": "Generic EO spacecraft, optical class",
        "evidence": "C",
        "evidence_note": GEN,
        "bus": {"form": "boxy chamfered bus, gold MLI, white zenith deck",
                "dims_m": [1.4, 1.2, 1.3], "finish": "olive-gold MLI with panel seams"},
        "solar": {"wings": 2, "panels_per_wing": 3, "layout": "3 columns x 1 row",
                  "mount": "short yokes either side of the bus, straight out cross-track"},
        "instruments": [
            {"name": "telescope",
             "form": "white cylindrical telescope barrel on a mounting plate under the "
                     "bus, pointing straight down (nadir), with a dark flared sunshade "
                     "lip at its aperture"},
            {"name": "star trackers",
             "form": "two small baffled cones on the zenith deck, tilted off-axis"}],
        "antennas": [{"name": "downlink antenna",
                      "form": "small flared X-band horn on the nadir face beside the telescope"}],
        "deliberately_omitted": [NO_DISH],
        "distinctive": "A telescope barrel hanging under a gold box: the payload points "
                       "at the Earth, the wings are the only thing that reaches out.",
    },
    "sar": {
        "mission": "Generic EO spacecraft, SAR class",
        "evidence": "C",
        "evidence_note": GEN,
        "bus": {"form": "boxy chamfered bus, gold MLI, white zenith deck",
                "dims_m": [1.3, 1.6, 1.1], "finish": "olive-gold MLI with panel seams"},
        "solar": {"wings": 1, "panels_per_wing": 4, "layout": "4 columns x 1 row",
                  "mount": "single wing on a short yoke, on the side away from the radar look direction"},
        "instruments": [
            {"name": "radar antenna panel",
             "form": "long flat white phased-array panel under the bus, running "
                     "along-track, panel tiles marked by dark seams, on two short stand-offs"},
            {"name": "star trackers",
             "form": "two small baffled cones on the zenith deck, tilted off-axis"}],
        "deliberately_omitted": [NO_DISH],
        "distinctive": "A long flat radar plank under a short box, with a single wing "
                       "on the other side: the panel faces the Earth.",
    },
    "smallsat": {
        "mission": "Generic EO spacecraft, smallsat class",
        "evidence": "C",
        "evidence_note": GEN,
        "bus": {"form": "near-cube chamfered bus, white structure, body-mounted cells on two faces",
                "dims_m": [0.9, 0.9, 0.9], "finish": "white anodised frame with cell panels"},
        "solar": {"wings": 2, "panels_per_wing": 2, "layout": "2 columns x 1 row",
                  "mount": "deployable panel pair hinged at the top edges of the side faces"},
        "instruments": [
            {"name": "imager",
             "form": "small dark lens barrel on the nadir face, pointing straight down"},
            {"name": "star trackers",
             "form": "one small baffled cone on the zenith face, tilted off-axis"}],
        "antennas": [{"name": "downlink antenna",
                      "form": "small flat patch on the zenith face"}],
        "deliberately_omitted": [NO_DISH],
        "distinctive": "A cube with two flat panels out either side and a small lens "
                       "looking down: the modern Earth-imaging smallsat shape.",
    },
}
