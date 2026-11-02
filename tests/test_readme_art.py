import re
import sys
import xml.etree.ElementTree as ET

from conftest import REPO

ASSETS = REPO / "assets"
SVG = ASSETS / "lifecycle.svg"
NS = "{http://www.w3.org/2000/svg}"


def generate():
    sys.path.insert(0, str(ASSETS))
    try:
        import make_lifecycle
    finally:
        sys.path.remove(str(ASSETS))
    return make_lifecycle.lifecycle()


def test_committed_lifecycle_matches_generator():
    committed = SVG.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert generate() == committed, "assets/lifecycle.svg is stale: run python assets/make_lifecycle.py"


def test_every_skill_is_drawn_in_lifecycle():
    root = ET.fromstring(SVG.read_text(encoding="utf-8"))
    drawn = ["".join(t.itertext()) for t in root.iter(f"{NS}text")]
    skills = sorted(p.name for p in (REPO / "skills").iterdir() if p.is_dir())
    assert skills
    missing = [s for s in skills if not any(s in text for text in drawn)]
    assert not missing, f"skills not drawn in assets/lifecycle.svg: {missing}"


def test_readme_shows_lifecycle_under_briefing():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    briefing = readme.index("> **NERV briefing.**")
    quick_start = readme.index("\n## Quick start")
    between = readme[briefing:quick_start]
    img = re.search(r'<img\s[^>]*src="assets/lifecycle\.svg"[^>]*>', between)
    assert img, "lifecycle image missing between the NERV briefing and Quick start"
    alt = re.search(r'alt="([^"]*)"', img.group(0))
    assert alt and alt.group(1).strip(), "lifecycle image needs alt text"
