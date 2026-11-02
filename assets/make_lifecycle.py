"""Generate assets/lifecycle.svg, the README lifecycle picture.

Standard library only. Edit the tables and layout constants below, then rerun.
tests/test_readme_art.py checks that the committed SVG matches this script's output.

Usage: python make_lifecycle.py [out.svg]
"""
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from palette import BG, CYAN, GREEN, HAZARD, ORANGE, PURPLE_METER, PURPLE_TEXT, RED_TEXT, WHITE

MONO = "Consolas, Menlo, 'DejaVu Sans Mono', monospace"

# Casing: labels in CAPS, skill names and fragments in lowercase, sentences in sentence case.
# Phases, left to right: title, the skill that runs it (None: you + your agent), description,
# frame colour, text colour. NERV's phases come first.
PHASES = [
    ("SET UP", "nerv-init", ["set up the project,", "take in raw data"], PURPLE_METER, PURPLE_TEXT),
    ("PLAN", "yashima-blueprint", ["plan the analysis", "before any results"], RED_TEXT, RED_TEXT),
    ("ANALYZE", None, ["build, run, explore", "your tools + skills"], CYAN, CYAN),
    ("PUBLISH", None, ["figures, paper,", "data deposit"], CYAN, CYAN),
]
PILOT = "you + your agent"
LOOP = 2  # the phase the gates loop on; a deviation returns to the phase before it
GATES = [("magi-review", ORANGE), ("sync-ratio", GREEN)]  # in loop order, top to bottom

HEADER_LEFT, HEADER_RIGHT = "NERV // SEQ-UNIT-01 OPERATIONS", "LIFECYCLE OF A PROJECT"
NERV_HEAD, PILOT_HEAD = "NERV BUILDS THE BASE", "THE PILOT FLIES"
GATES_LABEL, DEVIATION = "GATES ON THE LOOP", "DEVIATION"
BAND_TAG = "ALWAYS ON"
BAND_LINES = ["A few hard rules protect raw data, secrets, and reproducibility.",
              "Folder READMEs keep your agent oriented."]
# The caption, one sentence under each half.
CAPTION = ("NERV sets up the base and checks the gates.", "How you build is up to you and your agent.")
TITLE = "Lifecycle of a sequencing project with NERV skills"
DESC = ("NERV skills cover two phases: nerv-init sets up the project and takes in the raw data, "
        "and yashima-blueprint plans the analysis before any results exist. Analysis (building, running, "
        "exploring) and publishing are yours and your agent's, with your own tools and skills. On the "
        "analysis loop, magi-review and sync-ratio are the gates, and a deviation goes back to the plan. "
        "In every phase, a few hard rules protect raw data, secrets, and reproducibility, and folder "
        "READMEs keep your agent oriented.")

# Layout, in viewBox pixels. All text is one monospace size, so widths are predictable.
W = 1200
LEFT, RIGHT = 60, 1140
SIZE, EM = 18, 0.6  # about 13px when GitHub scales the picture to 880px; advance per character
PAD, LAMP_SPACE = 16, 22  # box padding; room for a hex lamp before its text
GAP = 40  # between phase boxes, which share one width
BOX_W = (RIGHT - LEFT - (len(PHASES) - 1) * GAP) // len(PHASES)
RHYTHM = 24  # vertical space between rows
REGION_Y = 100
BOX_TOP, STRIP_H, BOX_H = 124, 36, 144
CHIP_H, CHIP_GAP, CHIP_PAD = 36, 12, 12
CHIP_TOP = BOX_TOP + BOX_H + RHYTHM
LOOP_Y = CHIP_TOP + len(GATES) * (CHIP_H + CHIP_GAP) - CHIP_GAP + RHYTHM
LABEL_Y = LOOP_Y + 32
BAND_TOP, BAND_H, HAZARD_W = LABEL_Y + RHYTHM, 84, 24
H = BAND_TOP + BAND_H + RHYTHM + 60  # the footer mirrors the header
N_NERV = sum(1 for p in PHASES if p[1])


def text_w(s, track=0):
    return math.ceil(len(s) * (EM * SIZE + track))


def col_x(i):
    return LEFT + i * (BOX_W + GAP)


DIVIDER = col_x(N_NERV) - GAP // 2


def hexagon(cx, cy, r):
    """Flat-top hexagon points."""
    h = r * 0.866
    pts = [(cx - r, cy), (cx - r / 2, cy - h), (cx + r / 2, cy - h), (cx + r, cy), (cx + r / 2, cy + h), (cx - r / 2, cy + h)]
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def lamp(cx, cy, col, lit):
    paint = f'fill="{col}"' if lit else f'fill="none" stroke="{col}" stroke-width="1.5"'
    return f'<polygon points="{hexagon(cx, cy, 7)}" {paint}/>'


def text(x, y, cls, content, extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}"{extra}>{escape(content)}</text>'


def rect(x, y, w, h, extra):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {extra}/>'


def arrow(points, dashed=False, cls="flow"):
    """Polyline through points, with an arrowhead at the last one."""
    (x0, y0), (x1, y1) = points[-2], points[-1]
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    px, py = -dy, dx  # perpendicular
    head = [(x1, y1), (x1 - 12 * dx + 6 * px, y1 - 12 * dy + 6 * py), (x1 - 12 * dx - 6 * px, y1 - 12 * dy - 6 * py)]
    # Stop the line at the arrowhead's base so its end doesn't poke through the tip.
    pts = points[:-1] + [(x1 - 10 * dx, y1 - 10 * dy)]
    d = " ".join(f"{x},{y}" for x, y in pts)
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    tip = " ".join(f"{x},{y}" for x, y in head)
    return f'<polyline class="{cls}" points="{d}"{dash}/>\n  <polygon class="{cls}-head" points="{tip}"/>'


def box(i):
    """A phase: a title strip, who runs it, and what it covers. NERV's are solid, yours are dashed."""
    title, skill, lines, col, text_col = PHASES[i]
    x, nerv, number = col_x(i), skill is not None, f"{i + 1:02d}"
    need = max([text_w(f"{number} {title}", 2), LAMP_SPACE + text_w(skill or PILOT)] + [text_w(s) for s in lines])
    assert need <= BOX_W - 2 * PAD, f"phase {title} is too wide: {need} > {BOX_W - 2 * PAD}"
    if nerv:
        out = [rect(x, BOX_TOP, BOX_W, BOX_H, f'fill="{col}" fill-opacity="0.16"'),
               rect(x, BOX_TOP, BOX_W, STRIP_H, f'fill="{col}"'),
               rect(x, BOX_TOP, BOX_W, BOX_H, f'fill="none" stroke="{col}" stroke-width="2"')]
    else:
        out = [rect(x, BOX_TOP, BOX_W, STRIP_H, f'fill="{col}" fill-opacity="0.16"'),
               rect(x, BOX_TOP, BOX_W, BOX_H, f'class="yours" stroke="{col}"')]
    out.append(f'<text class="head" x="{x + PAD}" y="{BOX_TOP + 24}" fill="{BG if nerv else col}">'
               f'<tspan opacity="0.6">{number}</tspan> {escape(title)}</text>')
    op_y = BOX_TOP + STRIP_H + 32
    out += [lamp(x + PAD + 7, op_y - 6, col, nerv), text(x + PAD + LAMP_SPACE, op_y, "op", skill or PILOT, f' fill="{text_col}"')]
    out += [text(x + PAD, op_y + 30 + k * 26, "body", line) for k, line in enumerate(lines)]
    return "\n  ".join(out)


def gate(cx, top, w, name, col):
    """A gate chip centred on the loop line; the BG fill hides the line behind it."""
    x = cx - w // 2
    return "\n  ".join([
        rect(x, top, w, CHIP_H, f'fill="{BG}"'),
        rect(x, top, w, CHIP_H, f'fill="{col}" fill-opacity="0.16" stroke="{col}" stroke-width="2"'),
        lamp(x + CHIP_PAD + 7, top + CHIP_H // 2, col, True),
        text(x + CHIP_PAD + LAMP_SPACE, top + CHIP_H // 2 + 6, "op", name, f' fill="{col}"'),
    ])


def flows():
    """Phase arrows; the loop down through the gates and back up; the deviation back to the plan."""
    mid = BOX_TOP + (STRIP_H + BOX_H) // 2
    out = [arrow([(col_x(i) + BOX_W, mid), (col_x(i + 1), mid)]) for i in range(len(PHASES) - 1)]
    bottom = BOX_TOP + BOX_H
    cx, back_x = col_x(LOOP) + BOX_W // 2, col_x(LOOP) + BOX_W - PAD
    plan_x = col_x(LOOP - 1) + BOX_W // 2
    chip_w = 2 * CHIP_PAD + LAMP_SPACE + max(text_w(n) for n, _ in GATES)
    assert cx + chip_w // 2 + PAD <= back_x, "gate chips crowd the loop's return line"
    out.append(f'<line class="flow" x1="{cx}" y1="{bottom}" x2="{cx}" y2="{LOOP_Y}"/>')
    out.append(arrow([(cx, LOOP_Y), (back_x, LOOP_Y), (back_x, bottom)]))
    out.append(arrow([(cx, LOOP_Y), (plan_x, LOOP_Y), (plan_x, bottom)], dashed=True, cls="dev"))
    out += [gate(cx, CHIP_TOP + k * (CHIP_H + CHIP_GAP), chip_w, n, c) for k, (n, c) in enumerate(GATES)]
    out.append(text(cx, LABEL_Y, "key", GATES_LABEL, f' text-anchor="middle" fill="{WHITE}" opacity="0.7"'))
    out.append(text(plan_x, LABEL_Y, "key", DEVIATION, f' text-anchor="middle" fill="{RED_TEXT}"'))
    return "\n  ".join(out)


def regions():
    """The two halves: a head and a rule each, split by a dashed divider."""
    out = []
    for x, end, label, col in [(LEFT, DIVIDER - GAP // 2, NERV_HEAD, ORANGE), (col_x(N_NERV), RIGHT, PILOT_HEAD, CYAN)]:
        rule_x = x + text_w(label, 2) + PAD
        out += [text(x, REGION_Y, "head", label, f' fill="{col}"'),
                f'<line class="hair" x1="{rule_x}" y1="{REGION_Y - 6}.5" x2="{end}" y2="{REGION_Y - 6}.5"/>']
    out.append(f'<line class="hair" x1="{DIVIDER}.5" y1="80" x2="{DIVIDER}.5" y2="{LABEL_Y + 8}" stroke-dasharray="4 6"/>')
    return "\n  ".join(out)


def band():
    """Always on: hazard stripes at both ends, a caution tag, and the rules on the second column's edge."""
    mid = BAND_TOP + BAND_H // 2
    text_x = col_x(1)
    tag_x = text_x - 2 * PAD - LAMP_SPACE - text_w(BAND_TAG, 2)
    assert tag_x >= LEFT + HAZARD_W + PAD, "band tag runs into the stripes"
    assert text_x + max(text_w(s) for s in BAND_LINES) + PAD <= RIGHT - HAZARD_W, "band text runs into the stripes"
    out = [rect(LEFT, BAND_TOP, HAZARD_W, BAND_H, 'fill="url(#hazard)"'),
           rect(RIGHT - HAZARD_W, BAND_TOP, HAZARD_W, BAND_H, 'fill="url(#hazard)"'),
           rect(LEFT, BAND_TOP, RIGHT - LEFT, BAND_H, f'fill="none" stroke="{HAZARD}" stroke-width="1.5" stroke-opacity="0.7"'),
           lamp(tag_x + 7, mid - 8 - 6, HAZARD, True),
           text(tag_x + LAMP_SPACE, mid - 8, "head", BAND_TAG, f' fill="{HAZARD}"')]
    out += [text(text_x, mid - 8 + k * 28, "body", line) for k, line in enumerate(BAND_LINES)]
    return "\n  ".join(out)


def header():
    return "\n  ".join([
        lamp(LEFT + 7, 36, ORANGE, True),
        text(LEFT + 22, 42, "head", HEADER_LEFT, f' fill="{ORANGE}"'),
        text(RIGHT, 42, "head", HEADER_RIGHT, f' text-anchor="end" fill="{WHITE}" opacity="0.8"'),
        f'<line class="hair" x1="{LEFT}" y1="58.5" x2="{RIGHT}" y2="58.5"/>',
    ])


def footer():
    """The caption, mirroring the header: a rule, then one sentence flush with each margin."""
    return "\n  ".join([
        f'<line class="hair" x1="{LEFT}" y1="{H - 59}.5" x2="{RIGHT}" y2="{H - 59}.5"/>',
        text(LEFT, H - 29, "body", CAPTION[0]),
        text(RIGHT, H - 29, "body", CAPTION[1], ' text-anchor="end"'),
    ])


def corners():
    a, i = 24, 16
    d = (f"M{i} {i + a} V{i} H{i + a} M{W - i - a} {i} H{W - i} V{i + a} "
         f"M{W - i} {H - i - a} V{H - i} H{W - i - a} M{i + a} {H - i} H{i} V{H - i - a}")
    return f'<path d="{d}" fill="none" stroke="{ORANGE}" stroke-width="1.5" opacity="0.6"/>'


def lifecycle():
    assert all(p[1] for p in PHASES[:N_NERV]), "NERV's phases must come first"
    phase_boxes = "\n  ".join(box(i) for i in range(len(PHASES)))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(TITLE)}</title>
  <desc id="desc">{escape(DESC)}</desc>
  <!-- Generated by assets/make_lifecycle.py; edit that, not this file. -->
  <style>
    text {{ font-family: {MONO}; font-size: {SIZE}px; }}
    .head {{ font-weight: 700; letter-spacing: 2px; }}
    .op {{ font-weight: 700; }}
    .body {{ fill: {WHITE}; opacity: 0.85; }}
    .key {{ letter-spacing: 2px; }}
    .yours {{ fill: none; stroke-width: 2; stroke-dasharray: 8 6; opacity: 0.8; }}
    .flow {{ fill: none; stroke: {WHITE}; stroke-width: 2; opacity: 0.8; }}
    .flow-head {{ fill: {WHITE}; opacity: 0.8; }}
    .dev {{ fill: none; stroke: {RED_TEXT}; stroke-width: 1.5; }}
    .dev-head {{ fill: {RED_TEXT}; }}
    .hair {{ stroke: {WHITE}; stroke-width: 0.5; opacity: 0.4; }}
  </style>
  <defs>
    <pattern id="hazard" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="8" height="16" fill="{HAZARD}"/>
    </pattern>
  </defs>

  <rect width="{W}" height="{H}" fill="{BG}"/>
  {corners()}
  {header()}

  <!-- Regions: what NERV provides, and what is yours -->
  {regions()}

  <!-- Phases -->
  {phase_boxes}

  <!-- Arrows, the analysis loop and its gates, deviation back to the plan -->
  {flows()}

  <!-- Always on: hard rules and folder READMEs -->
  {band()}

  {footer()}
</svg>
"""


def main():
    if len(sys.argv) > 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).with_name("lifecycle.svg")
    out.write_text(lifecycle(), encoding="utf-8", newline="\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
