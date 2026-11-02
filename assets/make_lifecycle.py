"""Generate assets/lifecycle.svg, the README lifecycle picture.

Standard library only. Edit the tables and layout constants below, then rerun.
tests/test_readme_art.py checks that the committed SVG matches this script's output.

Usage: python make_lifecycle.py [out.svg]
"""
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from palette import BG, GREEN, ORANGE, PURPLE_METER, PURPLE_TEXT, RED_TEXT, WHITE

MONO = "Consolas, Menlo, 'DejaVu Sans Mono', monospace"
SANS = "Helvetica, Arial, 'Liberation Sans', sans-serif"

# NERV phases: skill name, description lines, stroke and lamp colour, text colour.
NERV_PHASES = [
    ("nerv-init", ["Set up +", "take in data"], PURPLE_METER, PURPLE_TEXT),
    ("yashima-blueprint", ["Plan the", "analysis"], RED_TEXT, RED_TEXT),
]
# The user's phases: title, description lines, example line (or None).
USER_PHASES = [
    ("BUILD / RUN / EXPLORE", ["your code, methods, compute,", "and other agent skills"],
     "e.g. DESeq2 / Scanpy, SLURM, TDD"),
    ("PUBLISH", ["figures, paper,", "data deposit"], None),
]
# Gates on the loop's return arrow, top to bottom (the return arrow runs upward).
GATES = [("magi-review", ORANGE), ("sync-ratio", GREEN)]

HEADER_LEFT = "NERV // SEQ-UNIT-01 OPERATIONS"
HEADER_RIGHT = "LIFECYCLE OF A PROJECT"
NERV_HEAD = "NERV BUILDS THE BASE"
PILOT_HEAD, PILOT_WHO = "THE PILOT FLIES", "you + your agent"
PILOT_SUB = "Bring your own methods, tools, and skills."
GATES_LABEL = "GATES ON THE LOOP"
DEVIATION = "deviation"
BAND_TAG = "ALWAYS ON"
BAND_LINES = ["A few hard rules protect raw data, secrets, and reproducibility.",
              "Folder READMEs keep your agent oriented."]
CAPTION = "NERV sets up the base and checks the gates. How you build is up to you and your agent."
TITLE = "Lifecycle of a sequencing project with NERV skills"
DESC = ("NERV skills cover two phases: nerv-init sets up the project and takes in the raw data, "
        "and yashima-blueprint plans the analysis. Building, running, exploring, and publishing are "
        "yours and your agent's, with your own methods, tools, and skills. On the build loop, "
        "magi-review and sync-ratio are the gates, and a deviation goes back to the plan. In every "
        "phase, a few hard rules protect raw data, secrets, and reproducibility, and folder READMEs "
        "keep your agent oriented.")

# Layout, in viewBox pixels. Text is sized from estimated advance widths.
W, H = 1200, 640
LEFT, RIGHT = 60, 1140
SIZE = 18  # smallest text; about 13px when GitHub scales the picture to 880px
MONO_EM, SANS_EM = 0.6, 0.55  # advance width per character, in em (sans is a generous average)
TRACK = 1  # letter-spacing of box titles and chips
PAD, LAMP_SPACE = 16, 26  # box padding; room for the hex lamp before a box title
ARROW_GAP, REGION_GAP = 36, 50
REGION_HEAD_Y, PILOT_SUB_Y = 104, 132
BOX_TOP, BOX_H, LINE_STEP = 152, 140, 26
ARROW_Y = BOX_TOP + BOX_H // 2
LOOP_INSET = 40  # where the loop leaves the build box, from its right edge
CHIP_H, CHIP_STEP, LOOP_BOTTOM = 36, 52, 440
BAND_TOP, BAND_H = 470, 84
CAPTION_Y = 600


def mono_w(text, track=TRACK):
    return math.ceil(len(text) * (MONO_EM * SIZE + track))


def sans_w(text):
    return math.ceil(len(text) * SANS_EM * SIZE)


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


def layout():
    """Box positions: NERV boxes chain from LEFT, PUBLISH ends at RIGHT, BUILD fills the rest."""
    boxes, x = [], LEFT
    for name, lines, col, text_col in NERV_PHASES:
        w = 2 * PAD + max([LAMP_SPACE + mono_w(name)] + [sans_w(s) for s in lines])
        boxes.append(dict(x=x, w=w, title=name, lines=lines, example=None, col=col, text_col=text_col, nerv=True))
        x += w + ARROW_GAP
    divider = x - ARROW_GAP + REGION_GAP // 2
    (b_title, b_lines, b_ex), (p_title, p_lines, p_ex) = USER_PHASES
    p_w = 2 * PAD + max([LAMP_SPACE + mono_w(p_title)] + [sans_w(s) for s in p_lines])
    build_x = divider + REGION_GAP // 2
    build_w = RIGHT - p_w - ARROW_GAP - build_x
    need = 2 * PAD + max([LAMP_SPACE + mono_w(b_title), sans_w(b_ex)] + [sans_w(s) for s in b_lines])
    assert build_w >= need, f"build box too narrow: {build_w} < {need}"
    boxes.append(dict(x=build_x, w=build_w, title=b_title, lines=b_lines, example=b_ex, col=WHITE, text_col=WHITE, nerv=False))
    boxes.append(dict(x=RIGHT - p_w, w=p_w, title=p_title, lines=p_lines, example=p_ex, col=WHITE, text_col=WHITE, nerv=False))
    return boxes, divider


def box(b):
    x, w = b["x"], b["w"]
    if b["nerv"]:
        frame = (f'<rect x="{x}" y="{BOX_TOP}" width="{w}" height="{BOX_H}" fill="{b["col"]}" fill-opacity="0.16" '
                 f'stroke="{b["col"]}" stroke-width="2"/>')
    else:
        frame = f'<rect class="yours" x="{x}" y="{BOX_TOP}" width="{w}" height="{BOX_H}"/>'
    out = [frame, lamp(x + PAD + 7, BOX_TOP + 30, b["col"], b["nerv"]),
           text(x + PAD + LAMP_SPACE, BOX_TOP + 36, "title", b["title"], f' fill="{b["text_col"]}"')]
    y = BOX_TOP + 36 + 32
    for line in b["lines"]:
        out.append(text(x + PAD, y, "body", line))
        y += LINE_STEP
    if b["example"]:
        out.append(text(x + PAD, y, "dim", b["example"]))
    return "\n  ".join(out)


def chip_w(name):
    return PAD + 24 + mono_w(name) + PAD


def gate(cx, cy, w, name, col):
    """A gate chip centred on the loop line; the BG fill hides the line behind it."""
    x, y = cx - w // 2, cy - CHIP_H // 2
    return "\n  ".join([
        f'<rect x="{x}" y="{y}" width="{w}" height="{CHIP_H}" fill="{BG}"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{CHIP_H}" fill="{col}" fill-opacity="0.16" stroke="{col}" stroke-width="2"/>',
        lamp(x + PAD + 7, cy, col, True),
        text(x + PAD + 24, cy + 6, "title", name, f' fill="{col}"'),
    ])


def flows(boxes):
    """Phase arrows, the build loop with its gates, and the deviation arrow back to the plan."""
    out = []
    for a, b in zip(boxes, boxes[1:]):
        out.append(arrow([(a["x"] + a["w"], ARROW_Y), (b["x"], ARROW_Y)]))
    plan, build = boxes[1], boxes[2]
    bottom = BOX_TOP + BOX_H
    widest = max(chip_w(n) for n, _ in GATES)
    gate_x = build["x"] + 20 + widest // 2
    out_x = build["x"] + build["w"] - LOOP_INSET
    out.append(f'<polyline class="flow" points="{out_x},{bottom} {out_x},{LOOP_BOTTOM} {gate_x},{LOOP_BOTTOM}"/>')
    out.append(arrow([(gate_x, LOOP_BOTTOM), (gate_x, bottom)]))
    first_gate_y = LOOP_BOTTOM - 20 - CHIP_H // 2 - (len(GATES) - 1) * CHIP_STEP
    for i, (name, col) in enumerate(GATES):
        out.append(gate(gate_x, first_gate_y + i * CHIP_STEP, widest, name, col))
    out.append(text(out_x + 16, first_gate_y + 6, "key", GATES_LABEL))
    plan_x = plan["x"] + plan["w"] // 2
    out.append(arrow([(gate_x, LOOP_BOTTOM), (plan_x, LOOP_BOTTOM), (plan_x, bottom)], dashed=True, cls="dev"))
    out.append(text(plan_x + 14, bottom + 44, "devlabel", DEVIATION))
    return "\n  ".join(out)


def band():
    tag_x, text_x = LEFT + 20, LEFT + 20 + 26 + mono_w(BAND_TAG, 2) + 30
    first = BAND_TOP + 34
    out = [
        f'<rect x="{LEFT}" y="{BAND_TOP}" width="{RIGHT - LEFT}" height="{BAND_H}" fill="{ORANGE}" fill-opacity="0.08" '
        f'stroke="{ORANGE}" stroke-width="1.5" stroke-opacity="0.7"/>',
        lamp(tag_x + 7, first - 6, ORANGE, True),
        text(tag_x + 26, first, "tag", BAND_TAG),
    ]
    for i, line in enumerate(BAND_LINES):
        out.append(text(text_x, first + i * 28, "body", line))
    return "\n  ".join(out)


def header():
    return "\n  ".join([
        lamp(LEFT + 7, 36, ORANGE, True),
        text(LEFT + 22, 42, "head", HEADER_LEFT, f' fill="{ORANGE}"'),
        text(RIGHT, 42, "head", HEADER_RIGHT, f' text-anchor="end" fill="{WHITE}" opacity="0.8"'),
        f'<line class="hair" x1="{LEFT}" y1="58.5" x2="{RIGHT}" y2="58.5"/>',
    ])


def regions(divider):
    pilot_x = divider + REGION_GAP // 2
    return "\n  ".join([
        text(LEFT, REGION_HEAD_Y, "head", NERV_HEAD, f' fill="{ORANGE}"'),
        f'<text class="head" x="{pilot_x}" y="{REGION_HEAD_Y}" fill="{WHITE}">{escape(PILOT_HEAD)}'
        f'<tspan class="who" dx="14">· {escape(PILOT_WHO)}</tspan></text>',
        text(pilot_x, PILOT_SUB_Y, "body", PILOT_SUB),
        f'<line class="hair" x1="{divider}.5" y1="80" x2="{divider}.5" y2="{LOOP_BOTTOM + 10}" stroke-dasharray="4 6"/>',
    ])


def corners():
    a, i = 24, 16
    d = (f"M{i} {i + a} V{i} H{i + a} M{W - i - a} {i} H{W - i} V{i + a} "
         f"M{W - i} {H - i - a} V{H - i} H{W - i - a} M{i + a} {H - i} H{i} V{H - i - a}")
    return f'<path d="{d}" fill="none" stroke="{ORANGE}" stroke-width="1.5" opacity="0.6"/>'


def lifecycle():
    boxes, divider = layout()
    phase_boxes = "\n  ".join(box(b) for b in boxes)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(TITLE)}</title>
  <desc id="desc">{escape(DESC)}</desc>
  <!-- Generated by assets/make_lifecycle.py; edit that, not this file. -->
  <style>
    .head {{ font-family: {MONO}; font-size: {SIZE}px; font-weight: 700; letter-spacing: 2px; }}
    .who {{ font-family: {SANS}; font-weight: 400; letter-spacing: 0; opacity: 0.8; }}
    .title {{ font-family: {MONO}; font-size: {SIZE}px; font-weight: 700; letter-spacing: {TRACK}px; }}
    .tag {{ font-family: {MONO}; font-size: {SIZE}px; font-weight: 700; letter-spacing: 2px; fill: {ORANGE}; }}
    .key {{ font-family: {MONO}; font-size: {SIZE}px; fill: {WHITE}; opacity: 0.75; letter-spacing: 1px; }}
    .body {{ font-family: {SANS}; font-size: {SIZE}px; fill: {WHITE}; opacity: 0.9; }}
    .dim {{ font-family: {SANS}; font-size: {SIZE}px; font-style: italic; fill: {WHITE}; opacity: 0.65; }}
    .caption {{ font-family: {SANS}; font-size: 20px; fill: {WHITE}; }}
    .devlabel {{ font-family: {MONO}; font-size: {SIZE}px; fill: {RED_TEXT}; letter-spacing: 1px; }}
    .yours {{ fill: none; stroke: {WHITE}; stroke-width: 2; stroke-dasharray: 8 6; opacity: 0.75; }}
    .flow {{ fill: none; stroke: {WHITE}; stroke-width: 2; opacity: 0.8; }}
    .flow-head {{ fill: {WHITE}; opacity: 0.8; }}
    .dev {{ fill: none; stroke: {RED_TEXT}; stroke-width: 1.5; }}
    .dev-head {{ fill: {RED_TEXT}; }}
    .hair {{ stroke: {WHITE}; stroke-width: 0.5; opacity: 0.4; }}
  </style>

  <rect width="{W}" height="{H}" fill="{BG}"/>
  {corners()}
  {header()}

  <!-- Regions: what NERV provides, and what is yours -->
  {regions(divider)}

  <!-- Phases -->
  {phase_boxes}

  <!-- Arrows, build loop and gates, deviation back to the plan -->
  {flows(boxes)}

  <!-- Always on: hard rules and folder READMEs -->
  {band()}

  <text class="caption" x="{W // 2}" y="{CAPTION_Y}" text-anchor="middle">{escape(CAPTION)}</text>
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
