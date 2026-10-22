#!/usr/bin/env python3
"""Validate index.json structural + licence-condition invariants (run at PR review).

Two families of check.

**Identity.** Every entry carries an explicit `folder` — the directory under
`satellites/` that holds its files. Before the photo-only lane the folder was
implied by `SVGColourPath`, which stops working the moment a folder has a
licensed photo and no SVG: the path fields are then empty and there is nothing
to derive from. `folder` is now the identity, and the path fields are optional
content.

**Licence conditions.** The ESA Standard Licence grant
(docs/permissions/esa-20260819-0333.md) is conditional: every ESA image must be
marked as available only under that licence, linking ESA's copyright-notice
page. The field carrying that mark is `licenceNoticeUrl` — this check makes the
condition structural instead of a convention a future batch could silently drop.

    python3 tools/check_index.py          # exit 0 clean, 1 with findings

Checks:
  - every entry has a non-empty `folder`, lowercase, and unique across the file;
  - `folder` matches the directory component of every non-empty path field, so
    an entry can never point at another folder's files;
  - `missionID` is a run of digits or "" (blank = not yet mapped, issue #99);
  - `artStatus`, when present, is one of the known values, and a
    `house-generated` entry carries both a colour SVG and a non-empty
    `references` list of URLs — a generated drawing without the record of what
    was looked at cannot be reviewed against golden rule 6;
  - `references` are URLs and never repo paths: reference imagery is consulted,
    never stored (see "House artwork lane" in TASKING.md);
  - every entry with imageLicense "ESA Standard Licence" carries
    licenceNoticeUrl with exactly the required URL;
  - licenceNoticeUrl never appears on a non-ESA entry (it is the marker of a
    rights-holder-imposed display condition, not a general link slot — a new
    licence with its own notice condition must be added here deliberately);
  - any licenceNoticeUrl value is https;
  - the generic placeholders (README "Generic placeholders"): `generic`, when
    present, is a boolean; a `generic: true` entry names its `genericClass`,
    lives in the reserved folder `generic-<class>`, maps to no mission
    (missionID ""), and is a house drawing with its icon; at most one entry per
    class; any folder named `generic-*` must be such an entry; and
    `generic-classes.json` is well formed and names only classes that have an
    entry — the API serves these to missions with no image of their own, only
    ever labelled as generic;
  - every entry with a colour SVG has its greyscale twin (grey/<folder>-grey.svg
    plus the two PNG renders), the twin is stamped from the current colour SVG
    (not stale) and carries no chroma — the served form is the grey twin, so a
    colour edit without a regenerated twin would ship the old drawing
    (tools/desaturate_svg.py --check is the same gate, standalone).
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from index_utils import REPO_URL, SAFE_FOLDER  # noqa: E402  (local sibling module)
from licenses import _norm  # noqa: E402  (local sibling module)
from desaturate_svg import check_entry as check_grey_twin  # noqa: E402  (local sibling module)

REPO = Path(__file__).resolve().parent.parent

# How a folder's artwork came to exist. Absent means the question has not been
# asked of that entry — the 72 pre-existing hand-drawn SVGs are not retro-labelled.
#   hand-drawn       drawn by a person, the original 72
#   house-generated  written from a structured description by tools/house_art
ART_STATUS = ("hand-drawn", "house-generated")

# Generic placeholders: folders the API may serve, labelled `kind: "generic"`
# with a caption, to a mission that has no folder of its own. Reserved by
# name (`generic-<class>`; not an underscore prefix, which the API's folder
# guard refuses) and by the `generic` flag on the index entry; the two must
# agree. generic-classes.json picks the class per mission.
GENERIC_PREFIX = "generic-"
GENERIC_RULES_FILE = "generic-classes.json"
# Same raw pattern as the API, and always used with fullmatch (re.match with
# ^...$ would accept a trailing newline).
GENERIC_CLASS_RE = re.compile(r"[a-z0-9]+")
# The mission facts a rule may test (computed by the API from its corpus).
GENERIC_FLAGS = ("constellation_unit", "horizon_entry")
GENERIC_PREDICATES = ("instrument_type_contains", "any_of")
# Every file the API needs before it will serve a generic class.
GENERIC_SERVED_FIELDS = ("SVGColourPath", "SVGBlackPath", "PNG512Path", "PNG1024Path")

# licence (normalised) -> the exact notice URL the rights holder requires
NOTICE_REQUIRED = {
    "esa standard licence": "https://www.esa.int/ESA_Multimedia/Copyright_Notice_Images",
}

# Every field whose value is a repo-relative path to one of the entry's files.
PATH_FIELDS = (
    "SVGColourPath", "SVGBlackPath", "PNG1024Path", "PNG512Path",
    "PhotoPath", "PhotoCut512Path", "PhotoCut1024Path",
    "PhotoCleanPath", "PhotoClean512Path", "PhotoClean1024Path",
    "SVGGreyPath", "PNGGrey1024Path", "PNGGrey512Path",
)


def check_entries(entries, repo=REPO):
    """All findings for an index; [] when clean. `repo` is the tree the path
    fields are resolved against (tests point it at a temporary layout)."""
    problems = []
    seen_folders = {}
    generic_by_class = {}

    for i, e in enumerate(entries):
        folder = e.get("folder")
        name = folder or e.get("SVGColourPath") or e.get("PhotoPath") or f"<entry {i}>"

        # --- identity -------------------------------------------------------
        if not isinstance(folder, str) or not folder:
            problems.append(f"{name}: missing `folder` — every entry needs one, it is "
                            f"the entry's identity now that path fields may be empty")
        else:
            if not SAFE_FOLDER.match(folder):
                problems.append(f"{folder}: `folder` must be lowercase "
                                f"[a-z0-9][a-z0-9.-]* (naming policy, PR #103)")
            if folder in seen_folders:
                problems.append(f"{folder}: duplicate `folder` (also at entry "
                                f"{seen_folders[folder]}) — folders are unique")
            else:
                seen_folders[folder] = i
            for field in PATH_FIELDS:
                value = e.get(field)
                if not value:
                    continue  # empty is legitimate: photo-only folders have no SVG
                if not isinstance(value, str):
                    problems.append(f"{folder}: {field} is not a string: {value!r}")
                    continue
                parts = value.split("/")
                if len(parts) < 3 or parts[1] != folder:
                    problems.append(f"{folder}: {field} points into another folder: "
                                    f"{value!r}")

        # --- house artwork lane --------------------------------------------
        art_status = e.get("artStatus")
        refs = e.get("references")
        if art_status is not None and art_status not in ART_STATUS:
            problems.append(f"{name}: artStatus must be one of {ART_STATUS}, "
                            f"found {art_status!r}")
        if refs is not None:
            if not isinstance(refs, list) or not refs:
                problems.append(f"{name}: references must be a non-empty list of URLs")
            else:
                for r in refs:
                    if not isinstance(r, str) or not r.startswith(("https://", "http://")):
                        problems.append(f"{name}: references entries must be URLs, "
                                        f"found {r!r} — reference imagery is consulted, "
                                        f"never stored in this repository")
        if art_status == "house-generated":
            if not e.get("SVGColourPath"):
                problems.append(f"{name}: artStatus house-generated needs a "
                                f"SVGColourPath — the drawing is the point of the entry")
            if not refs:
                problems.append(f"{name}: artStatus house-generated needs a non-empty "
                                f"`references` list — an original depiction must record "
                                f"which pages it was drawn from (golden rule 6)")
        if refs and art_status is None:
            problems.append(f"{name}: `references` present without artStatus — set "
                            f"artStatus so the lane is explicit")

        crop = e.get("photoCrop")
        if crop is not None:
            # bool is an int subclass; a JSON true would otherwise read as 1
            ok = (isinstance(crop, list) and len(crop) == 4
                  and all(isinstance(v, int) and not isinstance(v, bool)
                          for v in crop)
                  and crop[2] > 0 and crop[3] > 0
                  and crop[0] >= 0 and crop[1] >= 0)
            if not ok:
                problems.append(f"{name}: photoCrop must be [x, y, w, h] with four "
                                f"non-negative integers and positive w/h, found {crop!r}")

        mission_id = e.get("missionID", "")
        if not (isinstance(mission_id, str) and (mission_id == "" or mission_id.isdigit())):
            problems.append(f"{name}: missionID must be digits or \"\" (blank = "
                            f"unmapped, issue #99), found {mission_id!r}")

        # --- generic placeholders -------------------------------------------
        generic = e.get("generic")
        gclass = e.get("genericClass")
        if generic is not None and not isinstance(generic, bool):
            problems.append(f"{name}: `generic` must be true or false, found {generic!r}")
        if generic is True:
            if not (isinstance(gclass, str) and GENERIC_CLASS_RE.fullmatch(gclass)):
                problems.append(f"{name}: a generic placeholder needs a `genericClass` "
                                f"(lowercase letters/digits), found {gclass!r}")
            else:
                generic_by_class.setdefault(gclass, []).append(name)
                if folder != GENERIC_PREFIX + gclass:
                    problems.append(f"{name}: the {gclass!r} generic placeholder must "
                                    f"live in folder {GENERIC_PREFIX + gclass!r}")
            mid = e.get("missionID", "")
            if mid != "":
                problems.append(f"{name}: a generic placeholder maps to no mission — "
                                f"missionID must be \"\", found {mid!r}")
            if art_status != "house-generated":
                problems.append(f"{name}: a generic placeholder must be a house "
                                f"drawing (artStatus house-generated)")
            # The API treats a generic folder missing any served file as absent
            # and 404s the whole class, so all four must exist, not just be named
            # (the grey twin and its renders are gated by check_grey_twin below).
            for field in GENERIC_SERVED_FIELDS:
                value = e.get(field)
                if not (isinstance(value, str) and value):
                    problems.append(f"{name}: a generic placeholder needs {field} "
                                    f"— the API refuses the class without it")
                elif not (repo / value).is_file():
                    problems.append(f"{name}: {field} {value!r} does not exist "
                                    f"— the API refuses the class without it")
        else:
            if gclass is not None:
                problems.append(f"{name}: `genericClass` without `generic: true`")
            if isinstance(folder, str) and folder.startswith(GENERIC_PREFIX):
                problems.append(f"{name}: folders named {GENERIC_PREFIX}* are reserved "
                                f"for generic placeholders and must carry `generic: true`")

        # --- licence conditions ---------------------------------------------
        lic = _norm(e.get("imageLicense", ""))
        notice = e.get("licenceNoticeUrl")
        required = NOTICE_REQUIRED.get(lic)
        if required and notice != required:
            problems.append(f"{name}: imageLicense '{e['imageLicense']}' requires "
                            f"licenceNoticeUrl {required!r}, found {notice!r}")
        if notice and not required:
            problems.append(f"{name}: licenceNoticeUrl present but licence "
                            f"'{e.get('imageLicense', '')}' has no registered notice "
                            f"condition — add it to NOTICE_REQUIRED if intentional")
        if notice and not str(notice).startswith("https://"):
            problems.append(f"{name}: licenceNoticeUrl is not https: {notice!r}")

        # --- greyscale twin (the served form of a house drawing) -----------
        problems.extend(check_grey_twin(e, repo))

    for gclass, names in sorted(generic_by_class.items()):
        if len(names) > 1:
            problems.append(f"generic class {gclass!r} on {len(names)} entries "
                            f"({', '.join(names)}) — exactly one entry per class")
    return problems


def check_generic_rules(rules, entries):
    """Findings for generic-classes.json against the index; [] when clean.

    Shape: {"schema": 1, "rules": [{"class": C, "when": {PRED: VALUE}}, ...],
    "default": C}. PRED is `instrument_type_contains` (non-empty list of
    strings, each matched case-insensitively as a whole term — not bordered by
    a letter or digit — within the mission's instrument types AND instrument
    technologies) or `any_of` (non-empty list drawn from GENERIC_FLAGS).
    Every class named must have a generic entry. The API applies the same
    validation and disables generics entirely (404, as before) on a failure."""
    problems = []
    classes = {e.get("genericClass") for e in entries
               if isinstance(e, dict) and e.get("generic") is True
               and isinstance(e.get("genericClass"), str)}
    if not isinstance(rules, dict):
        return [f"{GENERIC_RULES_FILE}: must be a JSON object"]
    if rules.get("schema") != 1:
        problems.append(f"{GENERIC_RULES_FILE}: schema must be 1, found {rules.get('schema')!r}")
    unknown = set(rules) - {"schema", "note", "rules", "default"}
    if unknown:
        problems.append(f"{GENERIC_RULES_FILE}: unknown keys {sorted(unknown)}")
    default = rules.get("default")
    if not isinstance(default, str) or default not in classes:
        problems.append(f"{GENERIC_RULES_FILE}: default {default!r} has no generic "
                        f"entry (classes: {sorted(c for c in classes if c)})")
    rows = rules.get("rules")
    if not isinstance(rows, list):
        return problems + [f"{GENERIC_RULES_FILE}: rules must be a list"]
    for i, r in enumerate(rows):
        where = f"{GENERIC_RULES_FILE}: rules[{i}]"
        if not isinstance(r, dict) or set(r) != {"class", "when"}:
            problems.append(f"{where} must be an object with exactly `class` and `when`")
            continue
        if not isinstance(r["class"], str) or r["class"] not in classes:
            problems.append(f"{where}: class {r['class']!r} has no generic entry")
        when = r["when"]
        if not isinstance(when, dict) or len(when) != 1:
            problems.append(f"{where}: `when` must hold exactly one predicate")
            continue
        (pred, value), = when.items()
        if pred not in GENERIC_PREDICATES:
            problems.append(f"{where}: unknown predicate {pred!r} "
                            f"(known: {', '.join(GENERIC_PREDICATES)})")
        elif not (isinstance(value, list) and value
                  and all(isinstance(v, str) and v.strip() for v in value)):
            problems.append(f"{where}: {pred} needs a non-empty list of strings")
        elif pred == "any_of" and not set(value) <= set(GENERIC_FLAGS):
            problems.append(f"{where}: any_of accepts only {', '.join(GENERIC_FLAGS)}, "
                            f"found {sorted(set(value) - set(GENERIC_FLAGS))}")
    return problems


def check_ledger(rows, repo_url=REPO_URL):
    """ATTRIBUTIONS.csv invariant: a row whose rights holder is the repo itself
    ("repo maintainers": house SVGs, their PNG renders, grey twins, icons) must
    cite this repository as its source, under its current owner. Hand-added rows
    copied from a pre-transfer checkout would otherwise reintroduce the old
    URL. [] when clean."""
    problems = []
    for i, row in enumerate(rows, start=2):   # 1-based, after the header line
        if row.get("creator_or_rights_holder") == "repo maintainers" \
                and row.get("source_url") != repo_url:
            problems.append(f"ATTRIBUTIONS.csv:{i}: {row.get('path')}: repo-maintainers row "
                            f"must cite {repo_url}, found {row.get('source_url')!r}")
    return problems


def main():
    entries = json.load(open(REPO / "index.json"))
    problems = check_entries(entries)
    with open(REPO / "ATTRIBUTIONS.csv", newline="", encoding="utf-8") as fh:
        problems.extend(check_ledger(list(csv.DictReader(fh))))
    rules_path = REPO / GENERIC_RULES_FILE
    if any(isinstance(e, dict) and e.get("generic") is True for e in entries) \
            or rules_path.exists():
        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"{GENERIC_RULES_FILE}: unreadable ({exc})")
        else:
            problems.extend(check_generic_rules(rules, entries))
    for p in problems:
        print(f"FAIL {p}")
    if not problems:
        house = sum(1 for e in entries if e.get("artStatus") == "house-generated")
        print(f"OK   {len(entries)} entries; folders unique and consistent, "
              f"notice conditions consistent, grey twins present and fresh, ledger sources current, "
              f"{house} house-generated")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
