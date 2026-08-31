#!/usr/bin/env python3
"""Download THSC's current Standard 2 trials to a local, non-repository cache.

The script uses THSC's published catalogue and viewer endpoint as a personal
study downloader. It writes a provenance/checksum manifest and can capture the
first page of each PDF. Do not point --output-dir inside the public repository
or publish the resulting PDFs/screenshots without permission from rightsholders.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html as html_module
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from build_thsc_catalogue import trial_records


CATALOGUE_URL = "https://thsconline.github.io/s/yr12/Maths/trialpapers_general.html"
VIEWER_SCRIPT_URL = "https://thsconline.github.io/s/viewer.js"
USER_AGENT = "HSC-Standard-2-Personal-Study-Cache/1.0"


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return response.read()


def viewer_workers(script: str) -> list[str]:
    workers = list(dict.fromkeys(re.findall(r"\b(AKfy[a-zA-Z0-9_-]{25,})\b", script)))
    if not workers:
        raise RuntimeError("No THSC viewer workers were found in the published viewer script")
    return workers


def safe_filename(title: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{stem}.pdf"


def fetch_pdf(record: dict[str, object], workers: list[str]) -> tuple[bytes, str]:
    viewer_id = str(record["viewer_id"])
    title = str(record["title"])
    digest = hashlib.sha256(viewer_id.encode("utf-8")).hexdigest()
    encoded = urlencode({"export": "view", "base": viewer_id, "field": title, "hash": digest})
    errors: list[str] = []
    for worker in workers:
        endpoint = f"https://script.google.com/macros/s/{worker}/exec?{encoded}"
        try:
            response = json.loads(fetch_bytes(endpoint).decode("utf-8"))
            if response.get("error"):
                raise RuntimeError(str(response["error"]))
            payload = response.get("data")
            if not isinstance(payload, str):
                raise RuntimeError("viewer response did not contain encoded PDF data")
            pdf = base64.b64decode(payload, validate=True)
            if not pdf.startswith(b"%PDF"):
                raise RuntimeError("viewer response was not a PDF")
            return pdf, endpoint
        except (HTTPError, URLError, ValueError, RuntimeError, UnicodeDecodeError) as error:
            errors.append(f"{worker[-8:]}: {error}")
    raise RuntimeError(f"Could not retrieve {title}: {'; '.join(errors)}")


def render_first_page(pdf_path: Path, screenshots_dir: Path) -> Path | None:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return None
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    target_prefix = screenshots_dir / pdf_path.stem
    command = [pdftoppm, "-f", "1", "-l", "1", "-png", "-r", "144", str(pdf_path), str(target_prefix)]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rendered = sorted(screenshots_dir.glob(f"{pdf_path.stem}-*.png"))
    return rendered[0] if rendered else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="local-only directory for PDFs and manifest")
    parser.add_argument("--limit", type=int, default=0, help="download only the first N catalogue papers (0 means all)")
    parser.add_argument("--render-first-page", action="store_true", help="capture a PNG of each downloaded paper's first page")
    parser.add_argument("--pause", type=float, default=0.35, help="seconds between new downloads")
    args = parser.parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    pdf_dir = output_dir / "pdfs"
    shots_dir = output_dir / "first-pages"
    manifest_path = output_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(exist_ok=True)

    records = trial_records(fetch_bytes(CATALOGUE_URL).decode("utf-8"))
    if args.limit:
        records = records[: args.limit]
    workers = viewer_workers(fetch_bytes(VIEWER_SCRIPT_URL).decode("utf-8"))
    existing = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"items": []}
    items_by_id = {item["id"]: item for item in existing.get("items", [])}
    completed = 0

    for index, record in enumerate(records, start=1):
        file_path = pdf_dir / safe_filename(str(record["title"]))
        item = items_by_id.get(record["id"])
        if file_path.exists() and item and item.get("sha256"):
            if args.render_first_page and not item.get("first_page_screenshot"):
                screenshot = render_first_page(file_path, shots_dir)
                if screenshot:
                    item["first_page_screenshot"] = str(screenshot.relative_to(output_dir))
            print(f"[{index}/{len(records)}] reused {record['title']}")
            continue
        print(f"[{index}/{len(records)}] downloading {record['title']}", flush=True)
        pdf, endpoint = fetch_pdf(record, workers)
        file_path.write_bytes(pdf)
        item = {
            **record,
            "source_viewer_url": f"https://thsconline.github.io/s/v/{record['viewer_id']}/{quote(str(record['title']))}",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "retrieval_endpoint": endpoint,
            "local_file": str(file_path.relative_to(output_dir)),
            "bytes": len(pdf),
            "sha256": hashlib.sha256(pdf).hexdigest(),
        }
        if args.render_first_page:
            screenshot = render_first_page(file_path, shots_dir)
            if screenshot:
                item["first_page_screenshot"] = str(screenshot.relative_to(output_dir))
        items_by_id[str(record["id"])] = item
        completed += 1
        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "catalogue_url": CATALOGUE_URL,
            "scope": "Current THSC Mathematics Standard trial papers (2019 onwards), personal local cache only",
            "items": list(items_by_id.values()),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        time.sleep(args.pause)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalogue_url": CATALOGUE_URL,
        "scope": "Current THSC Mathematics Standard trial papers (2019 onwards), personal local cache only",
        "items": list(items_by_id.values()),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Finished: {completed} new downloads, {len(records)} requested records. Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Stopped safely; rerun to resume from the manifest.")
