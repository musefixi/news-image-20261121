#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE - a one-image summary of Saturday 21 November 2026.

A pure Python 3 standard-library program: no network, no PIL, no assets.
It keeps a 1024x1024 RGB framebuffer, draws a newspaper front page on it
with a hand-made vector stroke font, tiny spot illustrations and rules,
then encodes the result as a PNG with zlib and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

The output is deterministic: the same bytes on every run.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- PNG -----


def png_bytes(width, height, rgb):
    """Encode an RGB bytearray as a PNG (filter 0 rows, zlib level 9)."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ------------------------------------------------------------- Canvas -----


class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.px = bytearray(width * height * 3)
        self.fill_all(bg)

    def fill_all(self, color):
        row = bytes(color) * self.w
        for y in range(self.h):
            self.px[y * self.w * 3:(y + 1) * self.w * 3] = row

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def stamp(self, cx, cy, r, color):
        """Filled disc of radius r centred at (cx, cy)."""
        cx = int(round(cx)); cy = int(round(cy)); r = int(round(r))
        if r <= 0:
            self.set_px(cx, cy, color)
            return
        for dy in range(-r, r + 1):
            span = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - span, cy + dy, cx + span + 1, cy + dy + 1, color)

    def line(self, x0, y0, x1, y1, color, r=1):
        """Thick line: discs stamped along the segment."""
        dx = x1 - x0; dy = y1 - y0
        steps = max(1, int(max(abs(dx), abs(dy)) * 2))
        for i in range(steps + 1):
            t = i / steps
            self.stamp(x0 + dx * t, y0 + dy * t, r, color)

    def polyline(self, points, color, r=1, close=False):
        pts = list(points)
        if close and pts:
            pts.append(pts[0])
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], color, r)

    def fill_polygon(self, points, color):
        """Scanline even-odd fill of a polygon."""
        ys = [p[1] for p in points]
        y_lo = max(0, int(min(ys))); y_hi = min(self.h - 1, int(max(ys)))
        n = len(points)
        for y in range(y_lo, y_hi + 1):
            xs = []
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, color)

    def circle(self, cx, cy, rad, color, r=1):
        pts = []
        steps = max(12, int(rad * 2))
        for i in range(steps):
            a = 2 * 3.141592653589793 * i / steps
            pts.append((cx + rad * _cos(a), cy + rad * _sin(a)))
        self.polyline(pts, color, r, close=True)


def _sin(a):
    # tiny deterministic trig (math module would do; kept local for clarity)
    import math
    return math.sin(a)


def _cos(a):
    import math
    return math.cos(a)


# --------------------------------------------------------------- Font -----
# A hand-drawn vector stroke font. Each glyph is a list of strokes; each
# stroke is a string of "x,y" points on a 10-wide, 0..13-tall cell where
# y=1 is the cap top and y=11 is the baseline. A single-point stroke is a
# dot. Lowercase letters are drawn as small caps by the text engine.

FONT = {
    'A': ["0,11 5,1 10,11", "2.4,7.5 7.6,7.5"],
    'B': ["0,1 0,11", "0,1 5,1 7.5,3 7.5,4.8 5,6 0,6",
          "0,6 6.5,6 9,8.5 9,10 6.5,11 0,11"],
    'C': ["9,3.5 7,1.5 4.5,1 2,1.8 0.5,4 0.5,8 2,10.3 4.5,11 7,10.8 9,8.5"],
    'D': ["0,1 0,11", "0,1 4.5,1 8,3.5 8,8.5 4.5,11 0,11"],
    'E': ["9,1 0,1 0,11 9,11", "0,6 6.5,6"],
    'F': ["9,1 0,1 0,11", "0,6 6,6"],
    'G': ["9,3.5 7,1.5 4.5,1 2,1.8 0.5,4 0.5,8 2,10.3 4.5,11 7.5,11 9,9 9,6.8 6,6.8"],
    'H': ["0,1 0,11", "9,1 9,11", "0,6 9,6"],
    'I': ["4.5,1 4.5,11", "1.5,1 7.5,1", "1.5,11 7.5,11"],
    'J': ["9,1 9,8.5 7.5,10.8 4.5,11.5 1.5,10.5 0.5,8.5"],
    'K': ["0,1 0,11", "9,1 0.8,6.8", "2.2,5.6 9,11"],
    'L': ["0,1 0,11 9,11"],
    'M': ["0,11 0,1 5,7 10,1 10,11"],
    'N': ["0,11 0,1 10,11 10,1"],
    'O': ["4.5,1 7.5,1 9.5,3.5 9.5,8.5 7.5,11 4.5,11 2,11 0,8.5 0,3.5 2,1 4.5,1"],
    'P': ["0,11 0,1", "0,1 6,1 8.5,3 8.5,5.5 6,7.5 0,7.5"],
    'Q': ["4.5,1 7.5,1 9.5,3.5 9.5,8.5 7.5,11 4.5,11 2,11 0,8.5 0,3.5 2,1 4.5,1",
          "5.5,8.5 9.5,12.5"],
    'R': ["0,11 0,1", "0,1 6,1 8.5,3 8.5,5.5 6,7.5 0,7.5", "5,7.5 9.5,11"],
    'S': ["9,3 7,1.2 4,1 1.5,2.5 1,4.5 2.5,6 7,7.3 8.8,8.8 8.2,10.6 5.5,11.5 2.5,11.3 0.5,9.8"],
    'T': ["0,1 10,1", "5,1 5,11"],
    'U': ["0,1 0,8.5 1.5,10.5 4,11 6.5,11 9,10.5 10,8.5 10,1"],
    'V': ["0,1 5,11 10,1"],
    'W': ["0,1 2.2,11 5,4.5 7.8,11 10,1"],
    'X': ["0,1 10,11", "10,1 0,11"],
    'Y': ["0,1 5,6", "10,1 5,6", "5,6 5,11"],
    'Z': ["0,1 10,1 0,11 10,11"],
    '0': ["4.5,1 7,1 8.8,3 8.8,9 7,11 4.5,11 2.2,11 1,9 1,3 2.2,1 4.5,1"],
    '1': ["2.5,3.5 6,1 6,11", "2.5,11 9.5,11"],
    '2': ["1,3.5 2.5,1.5 5.5,1 8,2.5 8.5,4.5 7,6.5 0.5,11 9.5,11"],
    '3': ["1,2.5 3.5,1 6.5,1 8.5,3 6.5,5.5 3.5,5.8",
          "6.5,5.5 8.8,7.5 8.5,9.8 6,11.3 3,11.2 0.8,9.5"],
    '4': ["6.5,11 6.5,1 0.5,8.5 10,8.5"],
    '5': ["9,1 2,1 1.2,5.5 3.5,4.8 6.5,5 8.8,7 8.5,9.8 6,11.3 2.5,11.2 0.5,9.8"],
    '6': ["8.8,3.5 6,1.2 3,2 1,5 0.8,8 2,10.5 4.5,11.3 7.5,11 9,9 8.8,6.8 7,5.3 4.2,5.2 1,6.5"],
    '7': ["0.5,1 9.5,1 4,11"],
    '8': ["4.8,5.8 2.5,4.8 1.8,2.8 3,1.2 6.5,1.2 8,2.8 7.2,4.8 4.8,5.8",
          "4.8,5.8 2,7.2 1.5,9.5 3.2,11.2 6.8,11.2 8.5,9.5 8,7.2 4.8,5.8"],
    '9': ["1.2,8.5 3.5,10.8 6.5,10.5 8.8,8 9.3,5 8.2,2.2 5.8,1 3,1.2 1.2,3.2 1.5,5.5 3.2,6.8 5.8,6.8 9,5.5"],
    '.': ["5,10.8"],
    ',': ["5,10.8", "5.4,11 4.4,12.8"],
    ':': ["5,3", "5,10.8"],
    ';': ["5,3", "5,10.8", "5.4,11 4.4,12.8"],
    "'": ["5,0.8 4.6,3"],
    '"': ["3.2,0.8 2.8,3", "7,0.8 6.6,3"],
    '-': ["1.5,6 8.5,6"],
    '\u2013': ["1,6 10,6"],
    '\u2014': ["0.5,6 11,6"],
    '%': ["0.5,11 9.5,1",
          "2.5,1 4,1 4.8,2 4,3.2 2.5,3.2 1.8,2 2.5,1",
          "6,8.8 7.5,8.8 8.3,9.8 7.5,11 6,11 5.3,9.8 6,8.8"],
    '\u00b7': ["5,6"],
    '/': ["1.5,11 8.5,1"],
    '(': ["7.5,1 5,3 4,6 5,9.5 7.5,11.5"],
    ')': ["2.5,1 5,3 6,6 5,9.5 2.5,11.5"],
    '!': ["5,1 5,7.5", "5,10.8"],
    '?': ["1.5,3 3,1.2 6,1 8.3,2.5 8,4.8 5.2,6.5 5,8.5", "5,10.8"],
    '&': ["8.5,10.5 4,5.5 2,3.5 2.5,1.5 5,1.2 6.5,2.8 5.5,4.8 1,8 1.8,10.5 4.5,11.2 7,10 8.5,7.5"],
    '+': ["5,2.5 5,9.5", "1.5,6 8.5,6"],
    '$': ["9,3 7,1.2 4,1 1.5,2.5 1,4.5 2.5,6 7,7.3 8.8,8.8 8.2,10.6 5.5,11.5 2.5,11.3 0.5,9.8",
          "5,0 5,12.5"],
    '=': ["1.5,4.2 8.5,4.2", "1.5,7.8 8.5,7.8"],
    ' ': [],
}

# Per-glyph advance widths, in font units (default 11.3).
ADV = {'I': 6.5, '1': 8.0, ' ': 6.0, '.': 5.0, ',': 5.0, ':': 5.0,
       ';': 5.0, "'": 4.0, '\u00b7': 5.0, '!': 5.0, '(': 7.0, ')': 7.0,
       '/': 7.0, 'J': 8.5, 'M': 12.5, 'W': 12.5}

_parsed = {}


def glyph(ch):
    """Return the parsed stroke list for a character (cached)."""
    if ch not in _parsed:
        strokes = []
        for raw in FONT.get(ch, []):
            pts = []
            for pair in raw.split():
                xs, ys = pair.split(',')
                pts.append((float(xs), float(ys)))
            strokes.append(pts)
        _parsed[ch] = strokes
    return _parsed[ch]


# -------------------------------------------------------- Text engine -----

CAP_UNITS = 10.0  # glyph cap height spans y=1..11


def _adv(ch, unit):
    return ADV.get(ch, 11.3) * unit


def text_width(text, size, sx=1.0):
    """Width in pixels of a string at the given cap-height size."""
    unit = size / CAP_UNITS
    total = 0.0
    for ch in text:
        total += _adv(ch.upper(), unit)
    return total * sx


def draw_text(cv, x, top, text, size, color, bold=False, sx=1.0,
              align='left'):
    """Draw one line of text. (x, top) is the cap-height top-left.

    Lowercase letters render as small caps. Returns the drawn width.
    """
    unit = size / CAP_UNITS
    pen = max(0.6, size * (0.075 if bold else 0.052))
    width = text_width(text, size, sx)
    if align == 'center':
        x = x - width / 2
    elif align == 'right':
        x = x - width
    cx = x
    for ch in text:
        up = ch.upper()
        strokes = glyph(up)
        if ch.islower():
            gx_s, gy_s = 0.82, 0.74
        else:
            gx_s, gy_s = 1.0, 1.0
        adv = _adv(up, unit) * sx
        if strokes:
            for pts in strokes:
                mapped = []
                for gx, gy in pts:
                    px = cx + gx * unit * gx_s * sx
                    py = top + (gy - 1) * unit * gy_s
                    if gy_s < 1:  # small caps sit on the same baseline
                        py += size * (1 - gy_s)
                    mapped.append((px, py))
                if len(mapped) == 1:
                    cv.stamp(mapped[0][0], mapped[0][1], pen * 1.05, color)
                else:
                    cv.polyline(mapped, color, pen)
        cx += adv
    return width


def wrap_text(text, size, max_width, sx=1.0):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split()
    lines = []
    cur = ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, size, sx) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(cv, x, top, text, size, color, max_width, step,
                 bold=False, sx=1.0, max_lines=None):
    """Draw wrapped text; returns the y just past the last line."""
    lines = wrap_text(text, size, max_width, sx)
    if max_lines is not None:
        lines = lines[:max_lines]
    y = top
    for line in lines:
        draw_text(cv, x, y, line, size, color, bold=bold, sx=sx)
        y += step
    return y


# ------------------------------------------------------- Illustrations ----


def burst(cv, cx, cy, r_out, r_in, color):
    """A twelve-point explosion star."""
    import math
    pts = []
    for i in range(24):
        ang = math.pi * i / 12
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    cv.fill_polygon(pts, color)


def lead_panel(cv, x0, y0, x1, y1, ink, paper, red, orange, grey):
    """Spot illustration for the lead story: a missile arcs over a dashed
    border into Polish airspace and bursts."""
    navy = (21, 42, 69)
    cv.fill_rect(x0, y0, x1, y1, navy)
    # dashed border line, roughly two fifths across
    bx = x0 + (x1 - x0) * 0.58
    y = y0 + 14
    while y < y1 - 46:
        cv.fill_rect(bx, y, bx + 3, y + 12, (148, 178, 205))
        y += 22
    draw_text(cv, x0 + 14, y0 + 12, 'UKRAINE', 11, (148, 178, 205), bold=True)
    draw_text(cv, bx + 12, y0 + 12, 'POLAND', 11, (240, 244, 248), bold=True)
    # dotted trajectory from upper left to the burst point
    import math
    ex, ey = bx + 62, y0 + 128
    sx_, sy_ = x0 + 26, y0 + 30
    for i in range(26):
        t = i / 25
        px = sx_ + (ex - sx_) * t
        py = sy_ + (ey - sy_) * t + 46 * (t * (1 - t)) * 2
        cv.stamp(px, py, 1.6, (240, 244, 248))
    # missile body along the last stretch of the arc
    ang = math.atan2(ey - (sy_ + 40), ex - sx_)
    mx, my = ex - 46 * math.cos(ang), ey - 46 * math.sin(ang)
    tipx, tipy = ex - 8 * math.cos(ang), ey - 8 * math.sin(ang)
    cv.line(mx - 9 * math.sin(ang), my + 9 * math.cos(ang),
            tipx, tipy, (232, 236, 240), 4)
    cv.line(mx + 9 * math.sin(ang), my - 9 * math.cos(ang),
            tipx, tipy, (232, 236, 240), 4)
    cv.line(mx, my, tipx, tipy, red, 2)
    # the burst
    burst(cv, ex, ey, 30, 12, orange)
    burst(cv, ex, ey, 16, 7, (255, 214, 120))
    cv.stamp(ex, ey, 4, red)
    # ground line
    cv.fill_rect(x0 + 10, y1 - 44, x1 - 10, y1 - 42, (90, 120, 155))
    draw_text(cv, x0 + 14, y1 - 27, 'INTO NATO AIRSPACE', 11.5,
              (240, 244, 248), bold=True)


def market_chart(cv, x0, y0, x1, y1, red, grey, ink):
    """A small jagged line chart sliding downhill, with a big -3.7%."""
    cv.line(x0, y0, x0, y1, grey, 1)
    cv.line(x0, y1, x1, y1, grey, 1)
    pts = [(0.02, 0.10), (0.16, 0.24), (0.30, 0.17), (0.44, 0.38),
           (0.58, 0.33), (0.72, 0.56), (0.86, 0.52), (0.98, 0.78)]
    mapped = [(x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)) for fx, fy in pts]
    cv.polyline(mapped, red, 2)
    for px, py in mapped:
        cv.stamp(px, py, 2.4, red)
    # arrowhead at the end of the slide
    ex, ey = mapped[-1]
    cv.line(ex, ey, ex - 11, ey - 3, red, 2)
    cv.line(ex, ey, ex - 3, ey - 11, red, 2)


# ------------------------------------------------------------ The page ----

PAPER = (248, 244, 236)
INK = (25, 25, 25)
RED = (167, 30, 30)
GREY = (107, 107, 107)
LIGHT = (201, 194, 180)
ORANGE = (240, 140, 40)
BLACK = (20, 20, 20)
WHITE = (248, 244, 236)

MX = 36          # left/right margin
RX = W - MX      # right edge of the content column


def story_box(cv, x, top, width, kicker, headline, deck, chart=False):
    """One grid story: rule, kicker, two-line headline, short deck."""
    cv.fill_rect(x, top, x + width, top + 2, INK)
    draw_text(cv, x, top + 10, kicker, 12.5, RED, bold=True)
    draw_wrapped(cv, x, top + 31, headline, 22, INK, width, 27,
                  bold=True, sx=0.92, max_lines=2)
    deck_w = width - 124 if chart else width
    draw_wrapped(cv, x, top + 94, deck, 13, INK, deck_w, 19,
                 max_lines=3)
    if chart:
        market_chart(cv, x + width - 112, top + 92,
                     x + width, top + 150, RED, GREY, INK)


def brief(cv, x, top, width, kicker, headline):
    """A one-column brief: kicker plus a two-line headline."""
    draw_text(cv, x, top, kicker, 11.5, RED, bold=True)
    draw_wrapped(cv, x, top + 19, headline, 15, INK, width, 19,
                  bold=True, sx=0.92, max_lines=2)


def build():
    cv = Canvas(W, H, PAPER)
    cv.polyline([(18, 18), (W - 18, 18), (W - 18, H - 18), (18, H - 18)],
                LIGHT, 1, close=True)

    # folio line
    draw_text(cv, MX, 26, 'SATURDAY, 21 NOVEMBER 2026', 12.5, INK, bold=True)
    draw_text(cv, RX, 26, 'ONE DAY · ONE PAGE', 12.5, INK, bold=True,
              align='right')
    cv.fill_rect(MX, 48, RX, 50, INK)
    cv.fill_rect(MX, 54, RX, 55, INK)

    # masthead
    draw_text(cv, W // 2, 68, 'THE WORLD IN ONE PAGE', 40, INK, bold=True,
              align='center')
    draw_text(cv, W // 2, 120, "THE DAY'S NEWS, DRAWN ENTIRELY BY A PROGRAM",
              12.5, GREY, align='center')
    cv.fill_rect(MX, 146, RX, 149, INK)
    cv.fill_rect(MX, 153, RX, 154, INK)

    # lead story
    draw_text(cv, MX, 168, 'CONFLICT · EASTERN EUROPE', 14.5, RED, bold=True)
    for i, line in enumerate(['RUSSIAN', 'MISSILES', 'FALL IN POLAND']):
        draw_text(cv, MX, 196 + i * 64, line, 53, INK, bold=True, sx=0.80)
    draw_wrapped(cv, MX, 404,
                 'Two missiles and a suspected drone came down on Polish '
                 'soil. Warsaw called it a deliberate provocation; NATO '
                 'condemned a grave violation of its airspace.',
                 14.5, INK, 600, 22, max_lines=4)
    lead_panel(cv, 664, 196, RX, 500, INK, PAPER, RED, ORANGE, GREY)

    # markets ticker
    cv.fill_rect(MX, 516, RX, 552, BLACK)
    draw_text(cv, W // 2, 527,
              'S&P 500 -3.7% · NASDAQ -5% · NIKKEI -5.06% · GOLD -4% · '
              'BRENT $90', 14, WHITE, bold=True, sx=0.9, align='center')

    # grid of four
    story_box(cv, MX, 570, 466, 'JUSTICE · THE HAGUE',
              'WORLD COURT: MYANMAR COMMITTED GENOCIDE',
              'The court ruled Myanmar committed genocide against '
              'the Rohingya and ordered refugees home.')
    story_box(cv, 522, 570, 466, 'POLITICS · SHENZHEN',
              'FIRST TRUMP-XI-PUTIN SUMMIT HELD',
              'Joint declaration on nuclear war, oil and UN reform, '
              'but few concrete results.')
    story_box(cv, MX, 738, 466, 'MARKETS · NEW YORK',
              'AI ROUT TIPS WALL ST INTO CORRECTION',
              'Investors fled AI and chip shares; Nasdaq erased its '
              '2026 gains.', chart=True)
    story_box(cv, 522, 738, 466, 'POLITICS · BRUSSELS',
              'UK AND EU SIGN FOOD AND YOUTH DEALS',
              'PM Andy Burnham signed three pacts on food exports, '
              'linked carbon markets and youth travel.')

    # briefs
    cv.fill_rect(MX, 908, RX, 910, INK)
    brief(cv, MX, 918, 304, 'CONFLICT · RIYADH',
          'SAUDIS DOWN THREE MISSILES OVER RIYADH')
    brief(cv, 360, 918, 304, 'CLIMATE · ANTALYA',
          'COP31 TALKS ENTER DECISIVE FINAL STAGE')
    brief(cv, 684, 918, 304, 'HEALTH · UNITED STATES',
          'CANCER PILL HAILED AS BREAKTHROUGH')

    # footer
    cv.fill_rect(MX, 982, RX, 983, LIGHT)
    draw_text(cv, W // 2, 988,
              'ALSO: CYCLONE AKVAN HITS ODISHA · PALISADES FIRE VERDICT · '
              'YOUTH PROTESTS SWEEP EUROPE', 10.5, INK, sx=0.9,
              align='center')
    draw_text(cv, W // 2, 1007,
              'SOURCES: AFP · BBC · NPR · PBS NEWSHOUR · THE GUARDIAN · '
              'UPI · MIDDLE EAST EYE · ONE TURN', 9, GREY, sx=0.9,
              align='center')
    return cv


def main():
    cv = build()
    data = png_bytes(W, H, cv.px)
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'entry.png'), 'wb') as fh:
        fh.write(data)


if __name__ == '__main__':
    main()
