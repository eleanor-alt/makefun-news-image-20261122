"""Render the world news of Sunday 22 November 2026 as one 1024x1024 PNG.

Pure standard library, no network, no clock, no randomness: the same input
always produces the same bytes. The picture is a newspaper front page: a
masthead naming the day, one lead story, and a grid of eight more stories,
each with a coloured section tag, a headline and a one-fact deck.

The letterforms are stored as rows of '#' and '.' strings (6 columns by
8 rows) and painted onto a flat RGB buffer, which is then packed into a
PNG by hand.
"""

import zlib

SIZE = 1024

# ------------------------------------------------------------------ font --
# Each glyph is 8 rows of 6 characters: '#' paints, '.' stays blank.
GLYPHS = {
    "A": (".####.", "#....#", "#....#", "#....#", "######", "#....#", "#....#", "#....#"),
    "B": ("#####.", "#....#", "#....#", "#####.", "#....#", "#....#", "#....#", "#####."),
    "C": (".####.", "#....#", "#.....", "#.....", "#.....", "#....#", "#....#", ".####."),
    "D": ("####..", "#...#.", "#....#", "#....#", "#....#", "#....#", "#...#.", "####.."),
    "E": ("######", "#.....", "#.....", "#####.", "#.....", "#.....", "#.....", "######"),
    "F": ("######", "#.....", "#.....", "#####.", "#.....", "#.....", "#.....", "#....."),
    "G": (".####.", "#....#", "#.....", "#.####", "#....#", "#....#", "#....#", ".####."),
    "H": ("#....#", "#....#", "#....#", "######", "#....#", "#....#", "#....#", "#....#"),
    "I": (".####.", "...#..", "...#..", "...#..", "...#..", "...#..", "...#..", ".####."),
    "J": ("..####", ".....#", ".....#", ".....#", ".....#", "#....#", "#....#", ".####."),
    "K": ("#....#", "#...#.", "#..#..", "###...", "#..#..", "#...#.", "#....#", "#....#"),
    "L": ("#.....", "#.....", "#.....", "#.....", "#.....", "#.....", "#.....", "######"),
    "M": ("#....#", "##..##", "#.#.##", "#.##.#", "#....#", "#....#", "#....#", "#....#"),
    "N": ("#....#", "##...#", "#.#..#", "#..#.#", "#...##", "#....#", "#....#", "#....#"),
    "O": (".####.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####."),
    "P": ("#####.", "#....#", "#....#", "#####.", "#.....", "#.....", "#.....", "#....."),
    "Q": (".####.", "#....#", "#....#", "#....#", "#....#", "#.#..#", "#..#..", ".##.#."),
    "R": ("#####.", "#....#", "#....#", "#####.", "#..#..", "#...#.", "#....#", "#....#"),
    "S": (".####.", "#....#", "#.....", ".####.", ".....#", ".....#", "#....#", ".####."),
    "T": ("######", "...#..", "...#..", "...#..", "...#..", "...#..", "...#..", "...#.."),
    "U": ("#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####."),
    "V": ("#....#", "#....#", "#....#", "#....#", "#....#", ".#..#.", ".#..#.", "..##.."),
    "W": ("#....#", "#....#", "#....#", "#....#", "#.##.#", "#.#.#.", "#.#.#.", ".#.#.."),
    "X": ("#....#", ".#..#.", "..##..", "...#..", "..##..", ".#..#.", "#....#", "#....#"),
    "Y": ("#....#", "#....#", ".#..#.", "..##..", "...#..", "...#..", "...#..", "...#.."),
    "Z": ("######", ".....#", "....#.", "...#..", "..#...", ".#....", "#.....", "######"),
    "0": (".####.", "#....#", "#...##", "#..#.#", "#.#..#", "##...#", "#....#", ".####."),
    "1": ("...#..", "..##..", "...#..", "...#..", "...#..", "...#..", "...#..", ".#####."),
    "2": (".####.", "#....#", ".....#", "....#.", "...#..", "..#...", ".#....", "######"),
    "3": ("#####.", "....#.", "...#..", "....#.", ".....#", "#....#", "#....#", ".####."),
    "4": ("....#.", "...##.", "..#.#.", ".#..#.", "######", "....#.", "....#.", "....#."),
    "5": ("######", "#.....", "#####.", ".....#", ".....#", "#....#", "#....#", ".####."),
    "6": ("..###.", ".#....", "#.....", "#####.", "#....#", "#....#", "#....#", ".####."),
    "7": ("######", ".....#", "....#.", "...#..", "..#...", "..#...", ".#....", ".#...."),
    "8": (".####.", "#....#", "#....#", ".####.", "#....#", "#....#", "#....#", ".####."),
    "9": (".####.", "#....#", "#....#", "#....#", ".#####", ".....#", "....#.", ".###.."),
    " ": ("......", "......", "......", "......", "......", "......", "......", "......"),
    ".": ("......", "......", "......", "......", "......", "......", ".##...", ".##..."),
    ",": ("......", "......", "......", "......", "......", ".##...", ".##...", ".#...."),
    "'": ("..#...", "..#...", ".#....", "......", "......", "......", "......", "......"),
    "-": ("......", "......", "......", "######", "......", "......", "......", "......"),
    ":": ("......", ".##...", ".##...", "......", ".##...", ".##...", "......", "......"),
    ";": ("......", ".##...", ".##...", "......", ".##...", ".##...", ".#....", "......"),
    "&": (".##...", "#..#..", "#.#...", "..#...", ".#.#..", "#..#..", "#..#..", ".###.#"),
    "(": ("...##.", "..#...", ".#....", ".#....", ".#....", ".#....", "..#...", "...##."),
    ")": (".##...", "...#..", "....#.", "....#.", "....#.", "....#.", "...#..", ".##..."),
    "/": (".....#", "....#.", "...#..", "...#..", "..#...", ".#....", "#.....", "#....."),
    "+": ("......", "...#..", "...#..", "######", "...#..", "...#..", "......", "......"),
    "!": ("...#..", "...#..", "...#..", "...#..", "...#..", "...#..", "......", "...#.."),
    "?": (".####.", "#....#", ".....#", "....#.", "...#..", "...#..", "......", "...#.."),
    "%": ("##...#", "##..#.", "....#.", "...#..", "..#...", ".#..##", "#...##", "......"),
    "$": ("...#..", ".####.", "#.#...", "#.#...", ".###..", "..#.#.", "...#.#", ".####."),
    "=": ("......", "......", "######", "......", "######", "......", "......", "......"),
}

# Colours as (red, green, blue).
PAPER = (246, 241, 231)
INK = (20, 33, 61)
WHITE = (255, 255, 255)
RED = (180, 35, 24)
RULE = (180, 172, 156)

TAG_COLOURS = {
    "CLIMATE": (30, 107, 58),
    "WAR AT SEA": (180, 35, 24),
    "UKRAINE": (31, 90, 160),
    "GULF": (176, 92, 8),
    "SPACE": (94, 53, 140),
    "DISASTER": (150, 84, 4),
    "WEST BANK": (13, 110, 110),
    "AVIATION": (40, 110, 160),
    "WASHINGTON": (80, 84, 96),
}

# The day's stories. Lead first, then the eight grid stories.
LEAD = {
    "tag": "LEAD STORY - CLIMATE",
    "head": "COP31 COLLAPSES WITH NO DEAL",
    "deck": "ANTALYA TALKS END ON SUNDAY AS THE EU REJECTS A PACT WITH NO "
            "MENTION OF FOSSIL FUELS",
}

STORIES = [
    {"tag": "WAR AT SEA", "head": "RUSSIAN WARSHIP SINKS IN LIBYA",
     "deck": "CORVETTE MERKURY SUNK BY SUSPECTED UKRAINIAN SEA DRONES"},
    {"tag": "UKRAINE", "head": "DRONE HITS FLATS NEAR KYIV",
     "deck": "BOY, 7, PULLED ALIVE AFTER 14 HOURS; FOUR DEAD IN DYMER"},
    {"tag": "GULF", "head": "BAHRAIN COUNTS COST OF IRAN STRIKE",
     "deck": "TEHRAN HITS CIVILIAN SITE; TWO WOUNDED, SAUDI ARABIA CONDEMNS"},
    {"tag": "SPACE", "head": "BEPICOLOMBO REACHES MERCURY",
     "deck": "PROBE ENTERS ORBIT AFTER 8 YEARS; THRUSTER GLITCH REPORTED"},
    {"tag": "DISASTER", "head": "FACTORY FIRE KILLS 3 IN INDONESIA",
     "deck": "36 MISSING AFTER BLAZE AT CANDY PLANT WEST OF JAKARTA"},
    {"tag": "WEST BANK", "head": "SETTLERS TORCH CARS; ISRAEL PROBES",
     "deck": "12 VEHICLES TORCHED IN 4 VILLAGES NEAR RAMALLAH"},
    {"tag": "AVIATION", "head": "DELTA OUTAGE DELAYS 1,600 FLIGHTS",
     "deck": "WEIGHT-SYSTEM FAILURE HITS US FLYERS BEFORE THANKSGIVING"},
    {"tag": "WASHINGTON", "head": "TRUMP WARNS OF NEW IRAN STRIKES",
     "deck": "US PRESIDENT SAYS STRIKES COULD FOLLOW IN NEW YEAR, NO DEAL"},
]


class Page:
    """A flat RGB canvas with a tiny bitmap-text painter."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(background) * (width * height)

    def _set(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            at = (y * self.width + x) * 3
            self.pixels[at:at + 3] = bytes(colour)

    def fill(self, x0, y0, x1, y1, colour):
        for y in range(max(0, y0), min(self.height, y1)):
            for x in range(max(0, x0), min(self.width, x1)):
                self._set(x, y, colour)

    def disc(self, cx, cy, radius, colour):
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                    self._set(x, y, colour)

    def ring(self, cx, cy, radius, colour):
        for angle in range(360):
            import math
            x = cx + int(radius * math.cos(math.radians(angle)))
            y = cy + int(radius * math.sin(math.radians(angle)))
            self._set(x, y, colour)
            self._set(x + 1, y, colour)

    def glyph(self, char, x, y, scale, colour):
        rows = GLYPHS.get(char)
        if rows is None:
            rows = GLYPHS["?"]
        for row_i, row in enumerate(rows):
            for col_i, mark in enumerate(row):
                if mark != "#":
                    continue
                self.fill(x + col_i * scale, y + row_i * scale,
                          x + (col_i + 1) * scale, y + (row_i + 1) * scale,
                          colour)

    def text(self, string, x, y, scale, colour):
        """Paint one line; returns the x position just past the last glyph."""
        cursor = x
        for char in string:
            self.glyph(char, cursor, y, scale, colour)
            cursor += 7 * scale
        return cursor

    def text_width(self, string, scale):
        return len(string) * 7 * scale

    def centred(self, string, y, scale, colour):
        x = (self.width - self.text_width(string, scale)) // 2
        self.text(string, x, y, scale, colour)

    def wrapped(self, string, width_chars):
        """Greedy word wrap; returns a list of lines of at most width_chars."""
        lines, current = [], ""
        for word in string.split(" "):
            trial = word if not current else current + " " + word
            if len(trial) <= width_chars:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


def chip(page, tag, x, y, colour):
    """A solid coloured tag with white small text, with a little padding."""
    pad_x, pad_y = 8, 3
    wide = len(tag) * 7 + 2 * pad_x
    tall = 8 + 2 * pad_y
    page.fill(x, y, x + wide, y + tall, colour)
    page.text(tag, x + pad_x, y + pad_y, 1, WHITE)
    return wide


def draw_masthead(page):
    page.fill(0, 0, SIZE, 104, INK)
    page.centred("THE WORLD IN ONE DAY", 20, 3, WHITE)
    page.centred("SUNDAY 22 NOVEMBER 2026", 64, 2, (214, 196, 150))
    # A small globe at the right edge of the band.
    page.ring(948, 52, 30, WHITE)
    page.fill(918, 50, 978, 54, WHITE)
    page.fill(946, 22, 950, 82, WHITE)


def draw_lead(page):
    top, bottom = 120, 296
    page.fill(36, top, 46, bottom, RED)
    chip(page, LEAD["tag"], 62, top + 12, RED)
    page.text(LEAD["head"], 62, top + 44, 3, INK)
    for i, line in enumerate(page.wrapped(LEAD["deck"], 64)):
        page.text(line, 62, top + 100 + i * 26, 2, (52, 58, 74))


def draw_grid(page):
    top = 312
    row_h, col_w = 162, 476
    for row in range(4):
        y = top + row * row_h
        if row:
            page.fill(36, y, 988, y + 2, RULE)
        for col in range(2):
            x = 36 + col * 512
            if col:
                page.fill(512, y + 10, 514, y + row_h - 10, RULE)
            story = STORIES[row * 2 + col]
            chip(page, story["tag"], x + 14, y + 12,
                 TAG_COLOURS[story["tag"]])
            head_lines = page.wrapped(story["head"], 31)
            for i, line in enumerate(head_lines[:2]):
                page.text(line, x + 14, y + 42 + i * 24, 2, INK)
            deck_lines = page.wrapped(story["deck"], 31)
            for i, line in enumerate(deck_lines[:2]):
                page.text(line, x + 14, y + 98 + i * 22, 2, (52, 58, 74))


def draw_footer(page):
    page.fill(0, 964, SIZE, SIZE, INK)
    page.centred("22 NOVEMBER 2026 - THE WORLD IN ONE DAY", 984, 2, WHITE)


def _chunk(kind, payload):
    import struct
    import binascii
    body = kind + payload
    return (struct.pack(">I", len(payload)) + body
            + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF))


def encode_png(page):
    """Pack the canvas as a deterministic RGB PNG (no filtering)."""
    import struct
    raw = bytearray()
    stride = page.width * 3
    for y in range(page.height):
        raw.append(0)
        start = y * stride
        raw += page.pixels[start:start + stride]
    header = struct.pack(">IIBBBBB", page.width, page.height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", header)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def build():
    """Compose the whole front page and return the PNG bytes."""
    page = Page(SIZE, SIZE, PAPER)
    draw_masthead(page)
    draw_lead(page)
    draw_grid(page)
    draw_footer(page)
    return encode_png(page)
