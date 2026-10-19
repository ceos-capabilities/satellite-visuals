# satellite-visuals

Visual assets for Earth-observation missions — stylised satellite vectors (SVG), rasters rendered from them, and (progressively) properly-licensed satellite photographs, mapped to CEOS MIM mission IDs via `index.json`.

## Naming convention

One folder per entity under `satellites/` (or `other-spacecraft/` for non-EO), all lowercase. Files inside use the folder name as their stem:

```
satellites/<name>/
  <name>.svg                    colour vector (original work)
  <name>-icon.svg              monochrome icon vector (original work)
  <name>-1024px.png            render of <name>.svg (regenerate with tools/render_pngs.mjs)
  <name>-512px.png             render of <name>.svg
  grey/<name>-grey.svg         greyscale twin of <name>.svg (derived: tools/desaturate_svg.py)
  grey/<name>-grey-1024px.png  render of the grey twin (tools/render_pngs.mjs)
  grey/<name>-grey-512px.png   render of the grey twin
  grey/<name>-grey.render.json provenance: hashes of the grey SVG rendered and the PNGs produced
  <name>-photo.<ext>          raw sourced photo, bit-identical to source (evidence-grade)
  <name>-photo-cut-1024px.png  transparent cutout, natural aspect, max-dim 1024 (derived)
  <name>-photo-cut-512px.png   smaller cutout for cards (derived)
  <name>-photo-clean.<ext>     rights holder's own clean render, as published
  <name>-photo-clean-1024px.png  display copy: crop + resize only, no background edits
  <name>-photo-clean-512px.png   display copy: crop + resize only
```

Lowercase matters: these paths are served from a case-sensitive Linux bind-mount.

**House drawings have a greyscale twin.** The colour SVG is the master and
stays in the repository; the `grey/` twin is a luminance-only copy derived from
it (CSS `grayscale(1)` weights), intended as the form the Explorer and the API
show for a house drawing once the API is switched to it (a separate eogos-api
change; until then the colour render is still what is served). Photographs are
never desaturated, so a grey image will read as "our drawing" and a colour one
as "the rights holder's picture". Regenerate the twins after editing any colour
SVG:

```
python3 tools/desaturate_svg.py && (cd tools && node render_pngs.mjs)
python3 tools/check_index.py        # fails on a missing, stale or chromatic twin, or PNGs not rendered from it
```

**Not every folder has every file.** A folder with a licensed photo and no house
artwork is valid — the mission page shows the photo, and lists show an icon only
if one exists. Each entry in `index.json` carries an explicit `folder` field as its
identity; the path fields are optional content and may be `""`. See the photo-only
lane in `TASKING.md`.

## Generic placeholders

Three folders are **reserved**: `satellites/generic-optical/`,
`satellites/generic-sar/` and `satellites/generic-smallsat/`. Each holds one
house drawing of a generic Earth-observation spacecraft that depicts no real
vehicle, and each `index.json` entry carries `generic: true`, a `genericClass`
(`optical`, `sar`, `smallsat`) and no `missionID`. They exist so that every
mission in the Explorer has a baseline image (George, 19 Oct 2026: "I'd like to
have at least a baseline for all missions for launch").

The rule, which `tools/check_index.py` and the eogos-api enforce between them:

- a generic is **served only with `kind: "generic"` and a caption** ("Generic
  illustration. We do not yet hold an image of this spacecraft."), and the
  portal always shows that caption under it;
- it is **never a mission's own image**: no mission maps to it, a mission with
  its own folder never sees it, and a mission whose index rows conflict does
  not fall back to it;
- folders named `generic-*` are reserved by name, not by a prefix character
  (the API's folder guard refuses a leading underscore): `check_index.py`
  fails if a `generic-*` folder lacks the flag, if a generic row has a
  missionID or sits in any folder other than `generic-<class>`, or if two rows
  share a class.

### Which generic a mission gets: `generic-classes.json`

The API reads `generic-classes.json` (repo root) beside `index.json`, so a
curator can change the choice with an image sync and API restart, no API
release. The rules are evaluated in order; the first that matches picks the
class, and no match falls to `default`:

```json
{
  "schema": 1,
  "rules": [
    {"class": "sar", "when": {"instrument_type_contains": ["imaging radar", "sar", "synthetic aperture"]}},
    {"class": "smallsat", "when": {"any_of": ["constellation_unit", "horizon_entry"]}}
  ],
  "default": "optical"
}
```

| Predicate | Value | Matches when |
|---|---|---|
| `instrument_type_contains` | non-empty list of strings | any of the mission's instrument type strings contains any listed string (case-insensitive substring) |
| `any_of` | non-empty list of flags | any listed flag is true for the mission: `constellation_unit` (the mission appears in a constellation roster), `horizon_entry` (the mission is a Horizon entry) |

Each rule holds exactly one predicate. Every class named (in a rule or as
`default`) must have its generic row. `note` is an optional free-text key.
`python3 tools/check_index.py` validates the file; the API applies the same
validation and, if the file is missing or malformed, serves no generic at all
(a mission with no folder 404s, as before) and logs why.

The drawings were made like any house drawing (`tools/house_art`), but from a
written brief rather than reference imagery: "it should look like an EO
satellite not a comms satellite" — a box bus, a nadir-pointing payload, solar
wings, small star trackers, no parabolic dish. Their build script is
`tools/house_art/candidates/generic/build.py`.

## Deriving photo cutouts

Transparent cutouts (`-photo-cut-*.png`) are derived from raw `-photo.*` files by
`tools/process_photos.py`. When the raw carries its own alpha channel (many agency
renders ship pre-cut — 13 of the 22 batch-1 raws did), that alpha is used directly:
it is ground truth, and matting over it only loses structure (#115). Otherwise the
background is removed with rembg (default model `isnet-general-use`, which beat
u2net on thin structure in the batch-1 bake-off; `--model` overrides,
`--force-matting` disables the source-alpha preference) → alpha-bbox crop → size
set. The raw photo is never modified; the cutout is a mechanical derivative and the
source licence flows through unchanged (see `ASSET-LICENSING.md` and issue #109).

```bash
# one-off setup (venv — never install these globally)
python3 -m venv .venv && . .venv/bin/activate     # needs Python >= 3.10
pip install -r tools/requirements.txt              # rembg downloads a ~176 MB model on first run

# 1. PROCESS — derive cutouts + write cut_report.json (source sha, rembg version, bbox)
python3 tools/process_photos.py --all              # every index.json entry with a PhotoPath
python3 tools/process_photos.py ace cloudsat       # or named folders
#   --out-dir DIR   write cutouts + report elsewhere (dry runs — nothing lands in the tree)
#   --gallery       also emit cut_gallery.html
#   --margin 0.04   crop margin as a fraction of the cutout's larger side
#   --force         rebuild existing cutouts (otherwise idempotent — existing outputs skip)

# 2. GALLERY REVIEW — open cut_gallery.html, eyeball each before/after (cutout sits on a
#    checkerboard so transparency shows), approve/reject, then "Copy picks JSON".
#    Expected failure mode: thin booms/antennas and low-contrast bodies get eaten —
#    reject those for manual mask touch-up.

# 3. APPLY — copy approved cutouts into the tree and write the paperwork (inherited
#    ATTRIBUTIONS.csv rows inserted after each raw photo's row + PhotoCut1024Path /
#    PhotoCut512Path index fields). Idempotent; rejected folders are ignored.
python3 tools/apply_cuts.py --report cuts/cut_report.json \
    --picks picks.json --cuts-dir cuts --repo-root .
#    then: git diff, branch, commit, PR (the products PR is separate from tool changes)
```

Licences that do not permit derivatives (media-terms, ND) are skipped by default;
`--allow-nonderiv` overrides once permission is confirmed. `tools/licenses.py` maps
each licence name to its deed URL (the hyperlink target the portal credit line needs).

## License

• Original materials — the SVGs, the rasters rendered from them, documentation, and curation/metadata authored by the maintainers — are licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

• Sourced photographs are added only under their owners' open licences, recorded per image in `index.json` and `ATTRIBUTIONS.csv`. See `ASSET-LICENSING.md` for the policy, including the attribution-is-not-a-licence rule.

## Agent comments

Comments on issues and PRs that start with `CC:`, `CX:` or `CR:` are written by AI agents working for @gamedaygeorge under `.diamondsky/PROTOCOL.md`.
