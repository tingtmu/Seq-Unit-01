# Tasks

## 1. Shared palette

- [x] 1.1 Create `assets/palette.py` with the banner's colour constants (`BG`, `WHITE`, `GREEN`, `ORANGE`, `PURPLE_METER`, `PURPLE_TEXT`, `RED_TEXT`) and its contrast comment, and make `assets/make_banner.py` import them instead of defining them. Verify:
  - the diff of `make_banner.py` only swaps the definitions for the import;
  - `.venv/Scripts/python -m py_compile assets/make_banner.py` succeeds;
  - a short script confirms that every name in `make_banner.py`'s `from palette import` line exists in `palette`, and that each value equals the literal in `git show 07c9bf5:assets/make_banner.py`.

## 2. Tests first

- [x] 2.1 Write `tests/test_readme_art.py` with the three tests from design.md: the generator output matches the committed `assets/lifecycle.svg` (line endings normalised), every `skills/*/` folder name appears whole inside a single `<text>` element (not counting `<title>`/`<desc>`), and the README has an image of `assets/lifecycle.svg` with non-empty alt text between the "NERV briefing" blockquote and `## Quick start`. Verify that `.venv/Scripts/python -m pytest tests/test_readme_art.py` fails (red) because the generator and SVG don't exist yet.

## 3. Generator and picture

- [x] 3.1 Write `assets/make_lifecycle.py` (standard library only): a phase, gate, and text table, layout constants, and deterministic SVG output (`role="img"`, `<title>`, `<desc>`, palette from `palette.py`, system font stacks, `\n` endings), with usage `python assets/make_lifecycle.py [out.svg]`. Verify that running it twice gives identical files.
- [x] 3.2 Generate `assets/lifecycle.svg` and render it to PNG with headless Chrome or Edge at about 880px and about 400px wide. Check that no text overflows or overlaps, the smallest text is legible at 880px, NERV boxes and "yours" boxes are distinguishable, and all four skills are visible. Iterate on the layout constants until it does. Verify by looking at the final PNGs.
- [x] 3.3 Check the picture's wording against the honesty requirement: hard rules and folder READMEs are shown as always on, the band names what the hard rules protect accurately (raw data, secrets, reproducibility), the caption reads "NERV sets up the base and checks the gates…", no arrow routes a later delivery back through `nerv-init`, and no deferred layout (nf-core) is given as an example. Verify by reading the `<text>` elements in the SVG against `skills/nerv-init/templates/base/AGENTS.md.tmpl` and `docs/principles.md`.

## 4. README

- [x] 4.1 Add the image under the "NERV briefing" blockquote in `README.md` (`<img src="assets/lifecycle.svg" alt="…" width="100%">`, alt text a one-line version of the message), and update the Repository layout entry for `assets/` to name `lifecycle.svg`, `make_lifecycle.py`, and `palette.py`. Verify that `.venv/Scripts/python -m pytest tests/test_readme_art.py` passes (green).

## 5. Integration

- [x] 5.1 Run the full suite with `.venv/Scripts/python -m pytest` and verify it passes.

## Workflow follow-up

- Review gate after apply: commit (repo identity, Co-Authored-By line, no push), then a fresh-context reviewer checks the commit range against AGENTS.md and this change's spec, especially the honesty requirement and the `make_banner.py` diff.
- Mark this item done in `ROADMAP.md` (Docs and housekeeping) when it ships.
- Archive with `/opsx:archive`, then run the review gate again.
