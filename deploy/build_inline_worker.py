#!/usr/bin/env python3
"""Rebuild deploy/_worker_inline.js from the files in deploy/.

Keeps the waitlist handler already in _worker_inline.js. Does not deploy.
"""
from __future__ import annotations

import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "_worker_inline.js"
FILES = [
    ("/index.html", "text/html; charset=utf-8", ROOT / "index.html"),
    ("/assets/style.css", "text/css; charset=utf-8", ROOT / "assets" / "style.css"),
    ("/assets/decoder-data.js", "text/javascript; charset=utf-8", ROOT / "assets" / "decoder-data.js"),
    ("/assets/decoder.js", "text/javascript; charset=utf-8", ROOT / "assets" / "decoder.js"),
    ("/assets/decode-ui.js", "text/javascript; charset=utf-8", ROOT / "assets" / "decode-ui.js"),
    ("/assets/sample-report-1.png", "image/png", ROOT / "assets" / "sample-report-1.png"),
    ("/assets/sample-report.pdf", "application/pdf", ROOT / "assets" / "sample-report.pdf"),
]


def handler_source():
    text = OUT.read_text(encoding="utf-8")
    marker = "\nconst EMAIL_RE"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("could not find the waitlist handler in _worker_inline.js")
    return text[idx + 1:]


def render():
    assets = {}
    for url, ctype, path in FILES:
        assets[url] = [ctype, base64.b64encode(path.read_bytes()).decode("ascii")]
    line = "const ASSETS_INLINE = " + json.dumps(assets, separators=(", ", ": ")) + ";\n"
    return line + handler_source()


def main():
    text = render()
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != text:
            print(" _worker_inline.js is stale. Run: python3 deploy/build_inline_worker.py", file=sys.stderr)
            return 1
        print("_worker_inline.js matches deploy/")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
