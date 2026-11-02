"""Generate assets/banner.svg, the README banner.

The title and 初号機 are drawn as glyph outlines from Noto Serif JP Black
(SIL Open Font License 1.1), so the banner looks the same for every viewer,
with no font installed and no font file in the repository.

Requirements: fontTools (`pip install fonttools`) and the variable font
https://github.com/google/fonts/raw/main/ofl/notoserifjp/NotoSerifJP%5Bwght%5D.ttf

Usage: python make_banner.py <NotoSerifJP[wght].ttf> [out.svg]
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from palette import BG, GREEN, ORANGE, PURPLE_METER, PURPLE_TEXT, RED_TEXT, WHITE

W, H = 1200, 530
LEFT, RIGHT = 60, 1140
CONTENT_Y = 50  # everything below the monitor header strip is shifted down by this
TITLE_RIGHT, TITLE_GAP = 1040, 30  # title box ends before the kanji column
MAX_TITLE_COMPRESSION = 0.85

# meter colour, text colour, label, readout key, readout value, meter kind, lamp lit
CHANNELS = [
    (PURPLE_METER, PURPLE_TEXT, "CH-01 // NERV-INIT", "READ HARMONICS", "OK", "full", True),
    (GREEN, GREEN, "CH-02 // SYNC-RATIO", "SYNC RATE", "99.8%", "full", True),
    (ORANGE, ORANGE, "CH-03 // MAGI-REVIEW", "MAGI VOTE", "3/3 APPROVE", "votes", True),
    (RED_TEXT, RED_TEXT, "CH-04 // YASHIMA", "FATAL RISK", "0", "empty", False),
]
COL_W, COL_GAP, SEGMENTS = 262, 10, 20
METER_TOP, METER_H = 294, 24
SWEEP_STEP, CHANNEL_STAGGER = 0.035, 0.15  # seconds, for the one-time boot sweep
MOTTO = "GOD'S IN HIS HEAVEN. ALL'S RIGHT WITH THE WORLD."
MOTTO_W = 700


def outline(font, text, tracking_em=0.0):
    """Path data in font units (y up) for text, plus its advance width."""
    gs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm
    pen, x = SVGPathPen(gs), 0.0
    for ch in text:
        name = cmap[ord(ch)]
        gs[name].draw(TransformPen(pen, (1, 0, 0, 1, x, 0)))
        x += gs[name].width + tracking_em * upm
    return pen.getCommands(), x - tracking_em * upm


def placed(font, text, x, baseline, cap_px, sx, tracking_em=0.0):
    """<path> with its cap height scaled to cap_px and width compressed by sx."""
    d, adv = outline(font, text, tracking_em)
    s = cap_px / font["OS/2"].sCapHeight
    tf = f"translate({x:.2f} {baseline:.2f}) scale({s * sx:.5f} {-s:.5f})"
    return f'<path transform="{tf}" d="{d}"/>', adv * s * sx


def kanji_column(font, chars, cx, first_baseline, size, step, sx):
    s, out = size / font["head"].unitsPerEm, []
    for i, ch in enumerate(chars):
        d, adv = outline(font, ch)
        tf = f"translate({cx - adv * s * sx / 2:.2f} {first_baseline + i * step:.2f}) scale({s * sx:.5f} {-s:.5f})"
        out.append(f'<path transform="{tf}" d="{d}"/>')
    return "\n    ".join(out)


def title_block(font):
    """NERV and SEQ-UNIT-01 compressed to fit the title box, EPISODE:1, and 初号機."""
    _, nerv0 = placed(font, "NERV", 0, 0, 118, 1.0, -0.01)
    _, seq0 = placed(font, "SEQ-UNIT-01", 0, 0, 96, 1.0, -0.01)
    sx = min(MAX_TITLE_COMPRESSION, (TITLE_RIGHT - LEFT - TITLE_GAP) / (nerv0 + seq0))
    nerv, nerv_w = placed(font, "NERV", LEFT, 160, 118, sx, -0.01)
    seq, _ = placed(font, "SEQ-UNIT-01", LEFT + nerv_w + TITLE_GAP, 160, 96, sx, -0.01)
    episode, ep_w = placed(font, "EPISODE:1", LEFT + 2, 222, 24, sx, 0.02)
    # Ink runs flush with the NERV cap top and the EPISODE:1 baseline.
    kanji = kanji_column(font, "初号機", 1114, 90.5, 61, 63, 0.75)
    return "\n    ".join([nerv, seq, episode, kanji]), ep_w


def hexagon(cx, cy, r):
    """Flat-top hexagon points."""
    h = r * 0.866
    pts = [(cx - r, cy), (cx - r / 2, cy - h), (cx + r / 2, cy - h), (cx + r, cy), (cx + r / 2, cy + h), (cx - r / 2, cy + h)]
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def delay(channel, k):
    return f'style="animation-delay:{channel * CHANNEL_STAGGER + k * SWEEP_STEP:.3f}s"'


def segment_meter(i, col, x0, kind):
    inner0, inner_w, gap = x0 + 11, COL_W - 22, 3
    seg_w = (inner_w - gap * (SEGMENTS - 1)) / SEGMENTS
    out = []
    for k in range(SEGMENTS):
        sx = inner0 + k * (seg_w + gap)
        if kind == "full":
            out.append(f'<rect class="seg" {delay(i, k)} x="{sx:.2f}" y="{METER_TOP}" width="{seg_w:.2f}" height="{METER_H}" fill="{col}"/>')
        else:  # empty segment: a visible outline, not a faint block
            out.append(f'<rect class="seg" {delay(i, k)} x="{sx + 0.75:.2f}" y="{METER_TOP + 0.75}" width="{seg_w - 1.5:.2f}" '
                       f'height="{METER_H - 1.5}" fill="none" stroke="{col}" stroke-width="1.5" stroke-opacity="0.7"/>')
    return out


def vote_meter(i, col, x0):
    """Three elongated hex cells, one per MAGI seat."""
    inner0, inner_w, gap, point = x0 + 11, COL_W - 22, 8, 8
    cw = (inner_w - 2 * gap) / 3
    top, mid, bot = METER_TOP, METER_TOP + METER_H / 2, METER_TOP + METER_H
    out = []
    for k in range(3):
        a = inner0 + k * (cw + gap)
        b = a + cw
        pts = f"{a:.2f},{mid} {a + point:.2f},{top} {b - point:.2f},{top} {b:.2f},{mid} {b - point:.2f},{bot} {a + point:.2f},{bot}"
        out.append(f'<polygon class="seg" {delay(i, k * 6)} points="{pts}" fill="{col}"/>')
    return out


def telemetry():
    """Per skill: hex status lamp, label, bracketed meter, gauge ticks, readout."""
    parts = []
    for i, (col, text_col, label, key, value, kind, lit) in enumerate(CHANNELS):
        x0 = LEFT + i * (COL_W + COL_GAP)
        x1 = x0 + COL_W
        lamp = f'fill="{col}"' if lit else f'fill="none" stroke="{col}" stroke-width="1.5"'
        parts.append(f'<polygon points="{hexagon(x0 + 8, 272, 8)}" {lamp}/>')
        parts.append(f'<text class="label" x="{x0 + 24}" y="278" fill="{text_col}">{label}</text>')
        parts.append(
            f'<path d="M{x0 + 8} 290 H{x0} V322 H{x0 + 8} M{x1 - 8} 290 H{x1} V322 H{x1 - 8}" '
            f'fill="none" stroke="{col}" stroke-width="2"/>'
        )
        parts += vote_meter(i, col, x0) if kind == "votes" else segment_meter(i, col, x0, kind)
        seg_w = (COL_W - 22 - 3 * (SEGMENTS - 1)) / SEGMENTS
        for k in range(SEGMENTS):
            tx, tick = x0 + 11 + k * (seg_w + 3) + seg_w / 2, 9 if k % 5 == 0 else 5
            parts.append(f'<line class="tick" x1="{tx:.2f}" y1="327" x2="{tx:.2f}" y2="{327 + tick}"/>')
        parts.append(f'<text class="key" x="{x0}" y="362">{key}</text>')
        parts.append(f'<text class="value" x="{x0}" y="400" fill="{text_col}">{value}</text>')
    return "\n    ".join(parts)


def header():
    """Monitor header strip above the title card."""
    return f"""<polygon points="{hexagon(LEFT + 7, 36, 7)}" fill="{ORANGE}"/>
  <text class="head" x="{LEFT + 22}" y="42" fill="{ORANGE}">NERV // SEQ-UNIT-01 ACTIVATION SEQUENCE</text>
  <text class="head" x="{RIGHT}" y="42" text-anchor="end" fill="{WHITE}" opacity="0.8">PILOT: AI AGENT · ENTRY PLUG: INSERTED</text>
  <line class="hair" x1="{LEFT}" y1="58.5" x2="{RIGHT}" y2="58.5"/>"""


def corners():
    """Monitor corner brackets, which also give the banner an edge on GitHub dark mode."""
    a, i = 24, 16
    d = (f"M{i} {i + a} V{i} H{i + a} M{W - i - a} {i} H{W - i} V{i + a} "
         f"M{W - i} {H - i - a} V{H - i} H{W - i - a} M{i + a} {H - i} H{i} V{H - i - a}")
    return f'<path d="{d}" fill="none" stroke="{ORANGE}" stroke-width="1.5" opacity="0.6"/>'


def banner(font):
    title, ep_w = title_block(font)
    m0, m1 = (W - MOTTO_W) / 2, (W + MOTTO_W) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">NERV · Seq-Unit-01</title>
  <desc id="desc">Episode title card style banner: NERV SEQ-UNIT-01, agent skills for sequencing projects, with a telemetry display for the four skills. Unofficial fan homage.</desc>
  <!-- Generated by assets/make_banner.py; edit that, not this file. Title and 初号機 are glyph
       outlines from Noto Serif JP Black (SIL Open Font License 1.1). -->
  <style>
    .head {{ font-family: Consolas, Menlo, 'DejaVu Sans Mono', monospace; font-size: 16px; font-weight: 700; letter-spacing: 2px; }}
    .sub {{ font-family: Helvetica, Arial, 'Liberation Sans', sans-serif; font-weight: 700; font-size: 33px; fill: {ORANGE}; letter-spacing: 1px; }}
    .label {{ font-family: Consolas, Menlo, 'DejaVu Sans Mono', monospace; font-size: 18px; font-weight: 700; letter-spacing: 1.5px; }}
    .key {{ font-family: Consolas, Menlo, 'DejaVu Sans Mono', monospace; font-size: 16px; fill: {WHITE}; opacity: 0.8; letter-spacing: 2px; }}
    .value {{ font-family: Consolas, Menlo, 'DejaVu Sans Mono', monospace; font-size: 36px; font-weight: 700; letter-spacing: 1px; }}
    .tick {{ stroke: {WHITE}; stroke-width: 1.5; opacity: 0.5; }}
    .motto {{ font-family: Helvetica, Arial, 'Liberation Sans', sans-serif; font-size: 17px; fill: {WHITE}; opacity: 0.8; letter-spacing: 3px; }}
    .hair {{ stroke: {WHITE}; stroke-width: 0.5; opacity: 0.4; }}
    /* One-time boot sweep. The static, fully lit state is the default. */
    @media (prefers-reduced-motion: no-preference) {{
      .seg {{ animation: boot 0.25s ease-out both; }}
    }}
    @keyframes boot {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  </style>

  <rect width="{W}" height="{H}" fill="{BG}"/>
  {corners()}
  {header()}

  <g transform="translate(0 {CONTENT_Y})">
  <!-- Title block -->
  <g fill="{WHITE}">
    {title}
  </g>
  <text class="sub" x="{LEFT + ep_w + 22:.0f}" y="222" textLength="700" lengthAdjust="spacingAndGlyphs">AGENT SKILLS FOR SEQUENCING PROJECTS</text>

  <!-- Hairline rule between title and telemetry -->
  <line x1="{LEFT}" y1="244.5" x2="{RIGHT}" y2="244.5" stroke="{ORANGE}" stroke-width="1" opacity="0.7"/>

  <!-- Telemetry: one channel per skill -->
    {telemetry()}

  <!-- NERV motto (Robert Browning, Pippa Passes) -->
  <line class="hair" x1="{LEFT}" y1="443.5" x2="{m0 - 18:.0f}" y2="443.5"/>
  <line class="hair" x1="{m1 + 18:.0f}" y1="443.5" x2="{RIGHT}" y2="443.5"/>
  <text class="motto" x="{W / 2:.0f}" y="449" text-anchor="middle" textLength="{MOTTO_W}" lengthAdjust="spacing">{MOTTO}</text>
  </g>
</svg>
"""


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    font = instantiateVariableFont(TTFont(sys.argv[1]), {"wght": 900})
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else Path(__file__).with_name("banner.svg")
    out.write_text(banner(font), encoding="utf-8", newline="\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
