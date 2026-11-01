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

BG, WHITE = "#0B0A14", "#F2F2F2"
PURPLE, GREEN, ORANGE, RED = "#734F9A", "#8BD450", "#FF9900", "#E52F20"
W, H = 1200, 400
LEFT, RIGHT = 60, 1140
TITLE_RIGHT, TITLE_GAP = 1040, 30  # title box ends before the kanji column
MAX_TITLE_COMPRESSION = 0.85

CHANNELS = [  # colour, label, readout key, readout value, filled segments
    (PURPLE, "CH-01 // NERV-INIT", "READ HARMONICS", "OK", 20),
    (GREEN, "CH-02 // SYNC-RATIO", "SYNC RATE", "99.8%", 20),
    (ORANGE, "CH-03 // MAGI-REVIEW", "MAGI VOTE", "3/3 APPROVE", 20),
    (RED, "CH-04 // YASHIMA", "FATAL RISK", "0", 0),
]
COL_W, COL_GAP, SEGMENTS = 262, 10, 20
MOTTO = "GOD'S IN HIS HEAVEN. ALL'S RIGHT WITH THE WORLD."
MOTTO_W = 560


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
    """NERV and SEQ-UNIT-01 compressed to fit the title box, plus EPISODE:1."""
    _, nerv0 = placed(font, "NERV", 0, 0, 118, 1.0, -0.01)
    _, seq0 = placed(font, "SEQ-UNIT-01", 0, 0, 96, 1.0, -0.01)
    sx = min(MAX_TITLE_COMPRESSION, (TITLE_RIGHT - LEFT - TITLE_GAP) / (nerv0 + seq0))
    nerv, nerv_w = placed(font, "NERV", LEFT, 160, 118, sx, -0.01)
    seq, _ = placed(font, "SEQ-UNIT-01", LEFT + nerv_w + TITLE_GAP, 160, 96, sx, -0.01)
    episode, ep_w = placed(font, "EPISODE:1", LEFT + 2, 222, 24, sx, 0.02)
    kanji = kanji_column(font, "初号機", 1108, 88, 66, 68, 0.75)
    return "\n    ".join([nerv, seq, episode, kanji]), ep_w


def telemetry():
    """One bracketed, segmented meter per skill, with ticks and a readout."""
    parts = []
    for i, (col, label, key, value, filled) in enumerate(CHANNELS):
        x0 = LEFT + i * (COL_W + COL_GAP)
        x1 = x0 + COL_W
        parts.append(f'<text class="label" x="{x0}" y="266" fill="{col}">{label}</text>')
        parts.append(
            f'<path d="M{x0 + 7} 274 H{x0} V296 H{x0 + 7} M{x1 - 7} 274 H{x1} V296 H{x1 - 7}" '
            f'fill="none" stroke="{col}" stroke-width="1.5"/>'
        )
        inner0, inner_w, gap = x0 + 11, COL_W - 22, 3
        seg_w = (inner_w - gap * (SEGMENTS - 1)) / SEGMENTS
        for k in range(SEGMENTS):
            sx = inner0 + k * (seg_w + gap)
            opacity = "1" if k < filled else "0.18"
            parts.append(f'<rect x="{sx:.2f}" y="278" width="{seg_w:.2f}" height="14" fill="{col}" opacity="{opacity}"/>')
            tx, tick = sx + seg_w / 2, 8 if k % 5 == 0 else 4
            parts.append(f'<line class="tick" x1="{tx:.2f}" y1="300" x2="{tx:.2f}" y2="{300 + tick}"/>')
        parts.append(f'<text class="read" x="{x0}" y="327">{key}: <tspan fill="{col}">{value}</tspan></text>')
    return "\n  ".join(parts)


def banner(font):
    title, ep_w = title_block(font)
    m0, m1 = (W - MOTTO_W) / 2, (W + MOTTO_W) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">NERV · Seq-Unit-01</title>
  <desc id="desc">Episode title card style banner: NERV SEQ-UNIT-01, agent skills for sequencing projects, with a telemetry display for the four skills in Eva Purple, Eva Green, NERV Orange and Alert Red. Unofficial fan homage.</desc>
  <!-- Generated by assets/make_banner.py; edit that, not this file. Title and 初号機 are glyph
       outlines from Noto Serif JP Black (SIL Open Font License 1.1). -->
  <style>
    .sub {{ font-family: Helvetica, Arial, 'Liberation Sans', sans-serif; font-weight: 700; font-size: 26px; fill: {ORANGE}; letter-spacing: 1.5px; }}
    .label {{ font-family: Consolas, Menlo, 'DejaVu Sans Mono', monospace; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; }}
    .read {{ font-family: Consolas, Menlo, 'DejaVu Sans Mono', monospace; font-size: 15px; fill: {WHITE}; letter-spacing: 1px; }}
    .tick {{ stroke: {WHITE}; stroke-width: 1; opacity: 0.35; }}
    .motto {{ font-family: Helvetica, Arial, 'Liberation Sans', sans-serif; font-size: 14px; fill: {WHITE}; opacity: 0.75; letter-spacing: 3px; }}
    .hair {{ stroke: {WHITE}; stroke-width: 0.5; opacity: 0.4; }}
  </style>

  <rect width="{W}" height="{H}" fill="{BG}"/>

  <!-- Title block -->
  <g fill="{WHITE}">
    {title}
  </g>
  <text class="sub" x="{LEFT + ep_w + 22:.0f}" y="222">AGENT SKILLS FOR SEQUENCING PROJECTS</text>

  <!-- Hairline rule between title and telemetry -->
  <line x1="{LEFT}" y1="244.5" x2="{RIGHT}" y2="244.5" stroke="{ORANGE}" stroke-width="1" opacity="0.7"/>

  <!-- Telemetry: one channel per skill -->
  {telemetry()}

  <line class="hair" x1="{LEFT}" y1="345.5" x2="{RIGHT}" y2="345.5"/>

  <!-- NERV motto (Robert Browning, Pippa Passes) -->
  <line class="hair" x1="{LEFT}" y1="368.5" x2="{m0 - 18:.0f}" y2="368.5"/>
  <line class="hair" x1="{m1 + 18:.0f}" y1="368.5" x2="{RIGHT}" y2="368.5"/>
  <text class="motto" x="{W / 2:.0f}" y="373" text-anchor="middle" textLength="{MOTTO_W}" lengthAdjust="spacing">{MOTTO}</text>
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
