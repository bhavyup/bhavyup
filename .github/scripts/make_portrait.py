#!/usr/bin/env python3
"""Turn a photo into ascii.svg — a self-typing, monochrome ASCII portrait.

This is the generator that produced the portrait at the top of the README.
Run it once; it is not on a schedule, unlike scripts/generate_stats.py.

    pip install pillow numpy opencv-python-headless rembg onnxruntime
    python3 scripts/make_portrait.py photo.png --crop 400,110,910,790
    python3 scripts/embed_portrait_font.py      # inline the font, see below

Two output modes:

  * Standalone (default): each row types once on load, via a single
    begin="Xs" ... fill="freeze" animation, and stays frozen forever.
    Fine for viewing ascii.svg on its own.

  * Looping (--loop N): use this when the portrait is going to be embedded
    inside a larger animation that repeats every N seconds (e.g. the profile
    banner's logo-morph loop). Each row instead gets ONE continuous
    keyTimes/values animation with repeatCount="indefinite" spanning the
    whole N-second cycle, so it re-types correctly on every pass.

    Do NOT try to make a single-shot animation "loop" by giving it a list of
    multiple begin times (begin="0s;20s;40s;..."). That pattern is a known
    Chromium SMIL bug: only the first occurrence in the list actually
    interpolates from `from`; every later occurrence in the list just snaps
    straight to the frozen end value with no visible animation, because the
    engine doesn't correctly re-arm a frozen animation for later scheduled
    begins. If you see the portrait type correctly the first time a page
    loads and then just "pop in" fully-built on every loop after that, this
    is the bug you're hitting, and --loop is the fix.

The first run downloads a ~176 MB background-removal model, once.

Two things decide whether the output is any good, and neither is a parameter:

  * The photo. ASCII draws with shadow, not detail — about 13 brightness levels
    in total. You need side light (a window at ~45°, everything else off), a
    tight crop from chin to just above the hair, and real resolution. A 320px
    headshot fails: thin features like glasses frames are averaged away on
    downscale. Flat frontal light renders the face as a hole.
  * The darkening curve below. Without it the face comes out washed out and
    featureless — brows, glasses and lips all dissolve.

The grid bakes in an advance width of exactly 0.600 em (CHAR_W / FONT_SIZE), so
after generating, run scripts/embed_portrait_font.py to inline JetBrains Mono.
Otherwise a viewer whose default monospace is narrower — Consolas is ≈0.55 —
sees the portrait about 7% too narrow.

Motion is SMIL, because GitHub strips <script> from READMEs: each row is
revealed by a clipPath wipe with a cursor block riding its edge, staggered top
to bottom.
"""
import argparse
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

RAMP = " .`:-=+*cs#%@"     # bright/sparse -> dark/dense; leading space = blank
COLS = 90                  # below ~88 the face muddies; far above it dominates
CLAHE_CLIP = 3.0           # higher amplifies skin texture into noise
GAMMA = 1.0                # ramp mapping exponent
CURVE = 1.7                # the darkening curve — the difference-maker
CROP_BOTTOM = 0.0          # fraction to trim off the bottom (torso, chair)
ROW_RATIO = 0.48           # monospace cells are about twice as tall as wide

FG_LIGHT = "#7C3AED"       # readable on GitHub light — the portrait's grey
FG_DARK = "#A78BFA"        # and its dark-mode step
CHAR_W = 7.74              # 0.600 em at FONT_SIZE — keep these in step
FONT_SIZE = 12.9
LINE_H = 15
ROW_DELAY = 0.04           # per-row stagger, seconds
FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def prep(path, crop=None):
    """Cut out the background, even the local contrast, then darken."""
    src = Image.open(path).convert("RGBA")
    if crop:
        src = src.crop(crop)

    cut = remove(src)
    alpha = np.array(cut.split()[-1])

    # Composite onto white so everything outside the subject maps to the blank
    # end of the ramp. Skip this and the background fills with @ and %.
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    gray = np.array(Image.alpha_composite(white, cut).convert("L"))

    gray = cv2.bilateralFilter(gray, 11, 50, 50)      # smooth skin, keep edges
    gray = cv2.createCLAHE(clipLimit=CLAHE_CLIP,
                           tileGridSize=(8, 8)).apply(gray)
    gray = (255.0 * (gray / 255.0) ** CURVE).astype("uint8")
    gray[alpha < 20] = 255                            # force the matte to white
    return Image.fromarray(gray)


def to_lines(img, cols=COLS, gamma=GAMMA):
    w, h = img.size
    if CROP_BOTTOM:
        img = img.crop((0, 0, w, int(h * (1 - CROP_BOTTOM))))
        w, h = img.size

    rows = int(cols * (h / w) * ROW_RATIO)
    img = img.resize((cols, rows), Image.LANCZOS)
    px = list(img.getdata())
    n = len(RAMP)

    out = []
    for r in range(rows):
        out.append("".join(
            RAMP[min(n - 1, int((1 - px[r * cols + c] / 255.0) ** gamma * n))]
            for c in range(cols)
        ).rstrip())

    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def _row_anim_once(attr, begin, dur, frm, to):
    """Standalone mode: play once on load, freeze. (Original behavior.)"""
    return (f'<animate attributeName="{attr}" from="{frm}" to="{to}" '
            f'begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>')


def _row_anim_loop(attr, row_start, row_end, loop_dur, v0, v1):
    """
    Looping mode: ONE continuous animation spanning the whole loop_dur cycle,
    repeatCount=indefinite. Holds at v0 until row_start, ramps to v1 by
    row_end, holds at v1 until the cycle wraps back to 0 and repeats.
    This avoids the begin-list/freeze replay bug entirely — there is only
    ever one <animate>, never restarted, just cyclically re-evaluated.
    """
    k0 = row_start / loop_dur
    k1 = min(row_end / loop_dur, 0.999999)
    return (f'<animate attributeName="{attr}" '
            f'values="{v0};{v0};{v1};{v1}" '
            f'keyTimes="0;{k0:.6f};{k1:.6f};1" '
            f'dur="{loop_dur}s" repeatCount="indefinite"/>')


def build_svg(lines, cols=COLS, loop_dur=None):
    pad = 14
    width = int(cols * CHAR_W + pad * 2)
    height = len(lines) * LINE_H + pad * 2

    total_typing = len(lines) * ROW_DELAY
    if loop_dur is not None and total_typing > loop_dur:
        print(f"warning: typing takes {total_typing:.2f}s but --loop is "
              f"{loop_dur}s — later rows will be cut off mid-type. "
              f"Raise --loop to at least {total_typing:.2f}.", file=sys.stderr)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
         f'height="{height}" viewBox="0 0 {width} {height}" '
         f'font-family="{FAMILY}">',
         f'<style>.a{{fill:{FG_LIGHT}}}'
         f'@media(prefers-color-scheme:dark){{.a{{fill:{FG_DARK}}}}}</style>']

    for i, line in enumerate(lines):
        y = pad + i * LINE_H
        row_start = i * ROW_DELAY
        row_end = (i + 1) * ROW_DELAY
        w = max(len(line), 1) * CHAR_W
        safe = (line.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;"))

        if loop_dur is None:
            width_anim = _row_anim_once("width", row_start, ROW_DELAY, "0", f"{w:.1f}")
        else:
            width_anim = _row_anim_loop("width", row_start, row_end, loop_dur, "0", f"{w:.1f}")

        p.append(f'<clipPath id="c{i}"><rect x="{pad}" y="{y}" '
                 f'height="{LINE_H}" width="0">{width_anim}</rect></clipPath>')
        p.append(f'<g clip-path="url(#c{i})"><text xml:space="preserve" '
                 f'x="{pad}" y="{y + 11.2:.1f}" class="a" '
                 f'font-size="{FONT_SIZE}">{safe}</text></g>')

        # cursor block riding the wipe edge
        if loop_dur is None:
            x_anim = _row_anim_once("x", row_start, ROW_DELAY, f"{pad}", f"{pad + w:.1f}")
            cursor = (f'<rect y="{y + 1}" width="6" height="12" class="a" opacity="0">'
                      f'{x_anim}'
                      f'<set attributeName="opacity" to="0.8" begin="{row_start:.2f}s"/>'
                      f'<set attributeName="opacity" to="0" begin="{row_end:.2f}s"/></rect>')
        else:
            x_anim = _row_anim_loop("x", row_start, row_end, loop_dur, f"{pad}", f"{pad + w:.1f}")
            op_anim = _row_anim_loop("opacity", row_start, row_end, loop_dur, "0", "0.8")
            # opacity needs to drop back to 0 right after the row lands, not
            # stay at 0.8 for the rest of the cycle — build that 4-point curve
            # directly rather than reusing the generic helper.
            k0 = row_start / loop_dur
            k1 = min(row_end / loop_dur, 0.999999)
            op_anim = (f'<animate attributeName="opacity" '
                       f'values="0;0;0.8;0" '
                       f'keyTimes="0;{k0:.6f};{k0:.6f};{k1:.6f}" '
                       f'dur="{loop_dur}s" repeatCount="indefinite" '
                       f'fill="freeze"/>' if k1 > k0 else
                       f'<animate attributeName="opacity" values="0;0" '
                       f'keyTimes="0;1" dur="{loop_dur}s" repeatCount="indefinite"/>')
            cursor = (f'<rect y="{y + 1}" width="6" height="12" class="a" opacity="0">'
                      f'{x_anim}{op_anim}</rect>')

        p.append(cursor)

    p.append("</svg>")
    return "".join(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("photo")
    ap.add_argument("out", nargs="?", default="ascii.svg")
    ap.add_argument("--crop", help="left,top,right,bottom, applied first — crop "
                                   "tight to the head so the whole grid goes to "
                                   "the face")
    ap.add_argument("--cols", type=int, default=COLS)
    ap.add_argument("--loop", type=float, default=None,
                     help="seconds — emit a repeatCount=indefinite animation "
                          "cycling over this duration, for embedding inside a "
                          "larger animated banner. Omit for standalone "
                          "type-once-and-freeze behavior.")
    ap.add_argument("--preview", action="store_true",
                    help="print the ASCII to the terminal as well")
    args = ap.parse_args()

    crop = None
    if args.crop:
        parts = [int(v) for v in args.crop.split(",")]
        if len(parts) != 4:
            sys.exit("--crop needs four numbers: left,top,right,bottom")
        crop = tuple(parts)

    lines = to_lines(prep(args.photo, crop), cols=args.cols)
    if args.preview:
        print("\n".join(lines))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_svg(lines, cols=args.cols, loop_dur=args.loop))
    print(f"wrote {args.out} — {len(lines)} rows, {args.cols} columns"
          + (f", looping every {args.loop}s" if args.loop else ", plays once"))
    print("next: python3 scripts/embed_portrait_font.py")


if __name__ == "__main__":
    main()