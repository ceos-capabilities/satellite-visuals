"""Build the generic placeholder drawings into the lane's gitignored working directory:

    python3 tools/house_art/candidates/generic/build.py optical generic-optical
    python3 tools/house_art/candidates/generic/build.py sar generic-sar
    python3 tools/house_art/candidates/generic/build.py smallsat generic-smallsat

compose -> checks -> SVG + icon -> description.json, into tools/out/house_art/<folder>/,
then the usual lane steps (make_art_checker.py, apply_art.py, render_pngs.mjs).
These are the sources of the three reserved satellites/generic-* folders (README,
"Generic placeholders"). The description records build timing, so a rebuild gets
a new candidate fingerprint and needs a fresh review before apply.
"""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))  # tools/
sys.path.insert(0, str(HERE))
from house_art import checks, kit, schema  # noqa: E402
from house_art.refs import OUT, text_reference  # noqa: E402
import desc, draw  # noqa: E402

ROUTE = ("(b) code-generating model writes the SVG directly from this structured "
         "description; no reference raster is read, sampled, traced or vectorised")


def build(design, folder):
    base = OUT / folder
    base.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    scene = draw.DESIGNS[design]()
    d = dict(desc.D[design])
    chk = checks.run_all(d, scene, draw.ASSERTS[design])
    info = kit.render(scene, base / f"{folder}.svg", base / f"{folder}-icon.svg")
    info["build_seconds"] = round(time.time() - t0, 3)
    info["checks"] = chk
    (base / "checks.json").write_text(json.dumps(chk, indent=1) + "\n")
    refs = []
    for i, url in enumerate(desc.TEXT_REFS[design], 1):
        r = text_reference(url, "text reference: general EO spacecraft configuration")
        r["n"] = i
        r["title"] = url.rsplit("/", 1)[-1].replace("_", " ")
        refs.append(r)
    (base / "references.json").write_text(json.dumps(refs, indent=2) + "\n")
    d.update(folder=folder, owner="none: generic placeholder", generation_route=ROUTE,
             icon_derivation=(f"union silhouette of our own structural polygons from "
                              f"{folder}.svg, re-emitted with fill:currentColor"),
             references=refs,
             svg={"file": f"{folder}.svg", "icon": f"{folder}-icon.svg", **info})
    problems = schema.validate(d, folder)
    if problems:
        raise SystemExit(f"{folder}: description invalid -> {problems}")
    (base / "description.json").write_text(json.dumps(d, indent=2) + "\n")
    print(("ok  " if chk["ok"] else "FAIL"), folder, info["faces"], "faces",
          len(info["colours"]), "colours")
    for c in chk["checks"]:
        for line in c.get("problems", []) + c.get("report", []):
            print("     ", line)
    return chk["ok"]


if __name__ == "__main__":
    ok = build(sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
