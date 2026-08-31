#!/usr/bin/env python3
"""Serve the study workspace with an optional private THSC PDF cache.

Usage:
  python3 scripts/serve_personal_workspace.py --cache-dir /path/to/thsc-standard-2

The public GitHub Pages site has no `private-thsc` route and falls back to
THSC's embedded source viewer. This local server exposes the cache only on
localhost so the same split-view app can use personal downloaded PDFs.
"""

from __future__ import annotations

import argparse
import http.server
import posixpath
from pathlib import Path
from urllib.parse import unquote, urlparse


class PersonalWorkspaceHandler(http.server.SimpleHTTPRequestHandler):
    cache_dir: Path

    def translate_path(self, path: str) -> str:
        requested = urlparse(path).path
        normalized = posixpath.normpath(unquote(requested)).lstrip("/")
        if normalized == "private-thsc" or normalized.startswith("private-thsc/"):
            relative = normalized.removeprefix("private-thsc").lstrip("/")
            target = (self.cache_dir / relative).resolve()
            if target == self.cache_dir or self.cache_dir in target.parents:
                return str(target)
            return str(self.cache_dir / "missing")
        return super().translate_path(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, required=True, help="private cache created by download_thsc_personal_cache.py")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()

    cache_dir = args.cache_dir.expanduser().resolve()
    if not (cache_dir / "manifest.json").is_file():
        parser.error(f"{cache_dir} does not contain manifest.json")
    site_dir = Path(__file__).resolve().parents[1]
    handler = lambda *handler_args, **handler_kwargs: PersonalWorkspaceHandler(*handler_args, directory=str(site_dir), **handler_kwargs)
    PersonalWorkspaceHandler.cache_dir = cache_dir
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Study workspace: http://127.0.0.1:{args.port}")
        print(f"Private THSC cache: {cache_dir}")
        server.serve_forever()


if __name__ == "__main__":
    main()
