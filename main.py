"""Entry point: render the 22 November 2026 news image to /output/entry.png.

Renders the front page twice and refuses to write anything unless both
renders are byte-identical, so the program is deterministic by construction.
The output is checked against the competition's shape (PNG magic, at most
1 MiB, at most 1024x1024) before it is written atomically.
"""

import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import build  # noqa: E402

MAX_BYTES = 1_048_576
MAGIC = b"\x89PNG\r\n\x1a\n"


def render_checked():
    first = build()
    second = build()
    if hashlib.sha256(first).digest() != hashlib.sha256(second).digest():
        raise SystemExit("render is not deterministic")
    if not first.startswith(MAGIC):
        raise SystemExit("render did not produce a PNG")
    if len(first) > MAX_BYTES:
        raise SystemExit("image too large: %d bytes" % len(first))
    width, height = struct.unpack(">II", first[16:24])
    if width > 1024 or height > 1024:
        raise SystemExit("image too big: %dx%d" % (width, height))
    return first, width, height


def main():
    data, width, height = render_checked()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    staging = target + ".staging"
    with open(staging, "wb") as handle:
        handle.write(data)
    os.replace(staging, target)
    print("wrote %s: %d bytes, %dx%d" % (target, len(data), width, height))


if __name__ == "__main__":
    main()
