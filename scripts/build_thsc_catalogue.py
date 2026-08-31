#!/usr/bin/env python3
"""Build public metadata for THSC's current Mathematics Standard 2 trial list.

No PDFs, question text, screenshots, or viewer worker keys are written to the
repository. This data intentionally describes papers only; it is not a
topic-level question bank.
"""

from __future__ import annotations

import argparse
import html as html_module
import json
import re
from pathlib import Path


START = "<!-- BEGIN CONTENT 5318 --->"
END = "<!-- END CONTENT 5318 --->"


def slug(value: str) -> str:
    value = value.lower().replace("w. sol", "with-solutions")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def trial_records(source_html: str) -> list[dict[str, object]]:
    try:
        standard_section = source_html.split(START, 1)[1].split(END, 1)[0]
    except IndexError as error:
        raise ValueError("Could not find the current Standard Maths trial-paper section") from error

    records: list[dict[str, object]] = []
    for raw_title in re.findall(r">([^<>]+)</a>", standard_section):
        title = html_module.unescape(raw_title).strip()
        year_match = re.search(r"\b(20\d{2})\b", title)
        if not year_match:
            continue
        year = int(year_match.group(1))
        school = title[: year_match.start()].strip()
        records.append(
            {
                "id": f"thsc-{slug(title)}",
                "title": title,
                "school": school,
                "year": year,
                "includes_solutions": "w. sol" in title.lower(),
                "viewer_id": 5318,
                "catalogue_url": "https://thsconline.github.io/s/yr12/Maths/trialpapers_general.html",
                "source_kind": "THSC Online Standard Maths trial paper",
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_html", type=Path, help="saved THSC trial-paper catalogue HTML")
    parser.add_argument("output", type=Path, help="path for public metadata JSON")
    args = parser.parse_args()

    records = trial_records(args.source_html.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} current Standard trial-paper records to {args.output}")


if __name__ == "__main__":
    main()
