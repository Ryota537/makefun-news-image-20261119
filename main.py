#!/usr/bin/env python3
"""news-image-20261119 — "The World in One Page".

Draws a 1024x1024 newspaper front page summarising world news of
Thursday, 19 November 2026, and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png.

Pure Python standard library: hand-rolled PNG encoder (zlib + CRC32)
and a hand-drawn 5x7 bitmap font. No network, no randomness, no
timestamps — output is fully deterministic (byte-identical every run).

Facts verified against /tmp/news-20261119-research.md (19 Nov 2026,
~14:20-14:45 WIB) plus a live web check at ~14:22 WIB confirming the
ICJ Rohingya verdict had NOT yet been delivered (due 16:00 WIB), so
the ICJ panel says "rules today" with no outcome claimed.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- canvas
W, H = 1024, 1024

PAPER = (248, 244, 232)   # newsprint off-white
INK = (26, 26, 26)        # near-black ink
RED = (163, 22, 33)       # masthead / accent red
NAVY = (31, 78, 121)      # ICJ blue
TEAL = (15, 118, 110)     # Anthropic teal
ORANGE = (194, 92, 16)    # cyclone orange
PURPLE = (88, 60, 148)    # GTA purple
GOLD = (176, 132, 24)     # skyline gold
SKY = (214, 228, 238)     # hero sky
WHITE = (255, 255, 255)
GREY = (110, 105, 92)

px = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def fill_rect(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i], px[i + 1], px[i + 2] = c


def rect_outline(x, y, w, h, c, t=1):
    fill_rect(x, y, w, t, c)
    fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c)
    fill_rect(x + w - t, y, t, h, c)


def hline(x, y, w, c, t=1):
    fill_rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill_rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    """Bresenham line with square thickness t."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, filled=True, t=1):
    if filled:
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            for xx in range(cx - half, cx + half + 1):
                set_px(xx, yy, c)
    else:
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                fill_rect(cx + sx - t // 2, cy + sy - t // 2, t, t, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, written as strings. Hand-drawn.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ',': ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "00100", "00100", "01000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '•': ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}


def text_width(s, scale):
    """Advance width of s at scale (6 px per char cell, incl. spacing)."""
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '1':
                    fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cx, y, s, scale, color):
    draw_text(cx - text_width(s, scale) // 2, y, s, scale, color)


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines fitting max_w."""
    words = s.upper().split(' ')
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if text_width(cand, scale) <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- icons
def icon_scales(x, y, s, color):
    """Scales of justice inside box (x, y, s x s)."""
    cx, cy = x + s // 2, y + s // 2
    vline(cx, y + 4, s - 14, color, 3)
    hline(x + 6, y + 8, s - 12, color, 3)
    circle(cx, y + 6, 3, color)
    # left pan
    line(x + 6, y + 9, cx - 12, y + s - 16, color, 2)
    line(x + 12, y + 9, cx - 12, y + s - 16, color, 2)
    line(cx - 20, y + s - 16, cx - 4, y + s - 16, color, 3)
    # right pan
    line(x + s - 6, y + 9, cx + 12, y + s - 16, color, 2)
    line(x + s - 12, y + 9, cx + 12, y + s - 16, color, 2)
    line(cx + 4, y + s - 16, cx + 20, y + s - 16, color, 3)
    hline(x + 8, y + s - 8, s - 16, color, 3)


def icon_bridge(x, y, s, color):
    """Suspension bridge over water."""
    deck_y = y + s // 2 + 6
    hline(x + 2, deck_y, s - 4, color, 4)
    # two towers
    vline(x + s // 4, y + 6, deck_y - y - 6, color, 4)
    vline(x + 3 * s // 4, y + 6, deck_y - y - 6, color, 4)
    # main cable arc (approximated with segments)
    line(x + s // 4, y + 8, x + s // 2, y + 16, color, 2)
    line(x + s // 2, y + 16, x + 3 * s // 4, y + 8, color, 2)
    line(x + 2, y + 14, x + s // 4, y + 8, color, 2)
    line(x + 3 * s // 4, y + 8, x + s - 2, y + 14, color, 2)
    # suspenders
    for sx in (x + s // 3, x + s // 2, x + 2 * s // 3):
        vline(sx, y + 13, deck_y - y - 13, color, 2)
    # water
    hline(x + 4, deck_y + 12, s - 8, color, 2)
    hline(x + 12, deck_y + 20, s - 24, color, 2)


def icon_chart(x, y, s, color):
    """Rising bar chart with arrow."""
    base_y = y + s - 10
    hline(x + 4, base_y, s - 8, color, 3)
    bw, gap = 10, 8
    heights = (16, 26, 38)
    bx = x + 8
    for h in heights:
        fill_rect(bx, base_y - h, bw, h, color)
        bx += bw + gap
    line(x + 8, base_y - 44, x + s - 10, base_y - 52, color, 3)
    line(x + s - 10, base_y - 52, x + s - 18, base_y - 50, color, 3)
    line(x + s - 10, base_y - 52, x + s - 12, base_y - 44, color, 3)


def icon_cyclone(x, y, s, color):
    """Cyclone spiral: concentric arcs + rain ticks."""
    cx, cy = x + s // 2, y + s // 2 - 4
    for r in (6, 12, 18):
        circle(cx, cy, r, color, filled=False, t=3)
    circle(cx, cy, 3, color)
    # rain ticks below
    for i, rx in enumerate((x + 8, x + s // 2 - 2, x + s - 12)):
        line(rx, y + s - 16, rx - 3, y + s - 6, color, 2)


def icon_controller(x, y, s, color):
    """Game controller."""
    rect_outline(x + 4, y + 14, s - 8, s - 28, color, 3)
    fill_rect(x + 4, y + 14, s - 8, s - 28, WHITE)
    rect_outline(x + 4, y + 14, s - 8, s - 28, color, 3)
    # d-pad
    fill_rect(x + 12, y + s // 2 - 2, 16, 5, color)
    fill_rect(x + 18, y + s // 2 - 8, 5, 16, color)
    # buttons
    circle(x + s - 18, y + s // 2 - 6, 3, color)
    circle(x + s - 26, y + s // 2 + 2, 3, color)
    circle(x + s - 18, y + s // 2 + 10, 3, color)
    circle(x + s - 10, y + s // 2 + 2, 3, color)


ICONS = {
    'scales': icon_scales,
    'bridge': icon_bridge,
    'chart': icon_chart,
    'cyclone': icon_cyclone,
    'controller': icon_controller,
}


# ---------------------------------------------------------------- layout
def draw_flag_us(x, y, w, h):
    """Simplified US flag: stripes + blue canton with star dots."""
    stripe = h // 13
    for i in range(13):
        fill_rect(x, y + i * stripe, w, stripe + 1,
                  RED if i % 2 == 0 else WHITE)
    cw, ch = int(w * 0.4), stripe * 7
    fill_rect(x, y, cw, ch, NAVY)
    for r in range(4):
        for c in range(5):
            circle(x + 6 + c * 9, y + 5 + r * 7, 1, WHITE)


def draw_flag_cn(x, y, w, h):
    """Simplified China flag: red field, one big + four small stars."""
    fill_rect(x, y, w, h, RED)
    # big star (5-point approx: plus + diagonals)
    sx, sy = x + w // 5, y + h // 4
    fill_rect(sx - 2, sy - 8, 4, 16, GOLD)
    fill_rect(sx - 8, sy - 2, 16, 4, GOLD)
    line(sx - 6, sy - 6, sx + 6, sy + 6, GOLD, 2)
    line(sx + 6, sy - 6, sx - 6, sy + 6, GOLD, 2)
    for dx, dy in ((22, -2), (28, 6), (22, 14), (14, 10)):
        fill_rect(x + dx - 1, y + dy - 1, 3, 3, GOLD)


def draw_flag_ru(x, y, w, h):
    """Russia flag: white / blue / red horizontal bands."""
    fill_rect(x, y, w, h // 3 + 1, WHITE)
    fill_rect(x, y + h // 3, w, h // 3 + 1, NAVY)
    fill_rect(x, y + 2 * h // 3, w, h - 2 * h // 3, RED)


def draw_hero(x, y, w, h):
    """Skyline of Shenzhen + three flags above it."""
    fill_rect(x, y, w, h, SKY)
    # sun
    circle(x + w - 90, y + 42, 26, GOLD)
    # skyline silhouettes (deterministic heights, capped so the top
    # ~60 px of sky stays clear for the caption text)
    heights = [52, 96, 70, 100, 84, 98, 62, 90, 76, 100, 58, 92, 66]
    bw = w // len(heights)
    base = y + h - 8
    for i, bh in enumerate(heights):
        fill_rect(x + i * bw + 3, base - bh, bw - 6, bh, INK)
        # lit windows
        for wy in range(base - bh + 8, base - 8, 14):
            for wx in (x + i * bw + 8, x + i * bw + bw - 12):
                fill_rect(wx, wy, 3, 4, GOLD)
    # flags on poles above the skyline
    fw, fh = 92, 56
    fy = y + 10
    poles = [(x + 60, draw_flag_us), (x + 210, draw_flag_cn), (x + 360, draw_flag_ru)]
    for fx, fn in poles:
        vline(fx - 4, fy - 2, fh + 8, INK, 3)
        fn(fx, fy, fw, fh)
    # caption
    draw_text(x + 480, fy + 8, "SHENZHEN, CHINA", 2, INK)
    draw_text(x + 480, fy + 26, "APEC SUMMIT", 2, INK)
    draw_text(x + 480, fy + 44, "19 NOV 2026", 2, RED)


def draw_panel(x, y, w, h, color, title, fact, icon, fact_scale=2, icon_size=64):
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, INK, 2)
    fill_rect(x, y, w, 40, color)
    draw_text(x + 12, y + 13, title, 2, WHITE)
    # icon box
    ix, iy, isz = x + 12, y + 52, icon_size
    ICONS[icon](ix, iy, isz, color)
    # fact text to the right of icon, wrapped
    tx = x + 24 + icon_size
    tw = w - 36 - icon_size
    lines = wrap_text(fact, fact_scale, tw)
    ly = y + 56
    for ln in lines:
        draw_text(tx, ly, ln, fact_scale, INK)
        ly += 9 * fact_scale


def main():
    fill_rect(0, 0, W, H, PAPER)
    # double outer border
    rect_outline(14, 14, W - 28, H - 28, INK, 3)
    rect_outline(22, 22, W - 44, H - 44, INK, 1)

    # ---- masthead
    draw_text_centered(W // 2, 40, "THE WORLD", 11, INK)
    hline(40, 128, W - 80, INK, 2)

    # ---- date band (prominent, criterion #1)
    fill_rect(40, 140, W - 80, 46, INK)
    draw_text_centered(W // 2, 153, "THURSDAY, 19 NOVEMBER 2026", 4, WHITE)

    # ---- kicker
    draw_text_centered(W // 2, 200,
                       "THE WORLD IN ONE PAGE - SIX STORIES THAT MATTER TODAY",
                       2, GREY)

    # ---- main headline
    draw_text_centered(W // 2, 226, "TRUMP, XI & PUTIN", 7, INK)
    draw_text_centered(W // 2, 284, "MEET IN SHENZHEN", 7, RED)
    draw_text_centered(
        W // 2, 346,
        "FIRST US-CHINA-RUSSIA TRILATERAL, ON APEC SIDELINES", 3, INK)

    # ---- hero art
    draw_hero(40, 384, W - 80, 168)
    draw_text_centered(W // 2, 560, "LEADERS MEET AS APEC OPENS IN SHENZHEN", 2, GREY)

    # ---- section divider
    hline(40, 588, W - 80, INK, 2)
    draw_text_centered(W // 2, 598, "ALSO TODAY", 3, INK)
    hline(40, 626, W - 80, INK, 2)

    # ---- five supporting panels
    pw1, ph = 304, 176
    gap = 16
    x0 = 40
    draw_panel(x0, 640, pw1, ph, NAVY,
               "WORLD COURT RULES TODAY",
               "THE HAGUE DECIDES GAMBIA V. MYANMAR, ROHINGYA GENOCIDE CASE",
               'scales')
    draw_panel(x0 + pw1 + gap, 640, pw1, ph, RED,
               "CRIMEA BRIDGE HIT AGAIN",
               "3RD STRIKE IN A WEEK. TRAFFIC HALTED, DAMAGE ASSESSED",
               'bridge')
    draw_panel(x0 + 2 * (pw1 + gap), 640, pw1, ph, TEAL,
               "ANTHROPIC IPO DEBUTS",
               "PRICED $83 A SHARE. RECORD $81.3BN LISTING, NASDAQ: ANT",
               'chart')
    pw2 = (W - 80 - gap) // 2
    draw_panel(x0, 832, pw2, ph, ORANGE,
               "CYCLONE AKVAN NEARS INDIA",
               "TENS OF THOUSANDS EVACUATED IN ODISHA. LANDFALL DUE FRIDAY",
               'cyclone', fact_scale=3, icon_size=80)
    draw_panel(x0 + pw2 + gap, 832, pw2, ph, PURPLE,
               "GTA VI LAUNCHES TODAY",
               "ROCKSTAR'S EPIC OUT NOW ON PS5 AND XBOX. METACRITIC 99",
               'controller', fact_scale=3, icon_size=80)

    write_png()


# ---------------------------------------------------------------- PNG encoder
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


def write_png():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = bytearray()
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += px[yy * W * 3:(yy + 1) * W * 3]
    data = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
