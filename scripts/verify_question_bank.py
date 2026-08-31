#!/usr/bin/env python3
"""Fast structural checks for the published metadata-only bank."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
bank = json.loads((ROOT / "data" / "questions.json").read_text())
curriculum = json.loads((ROOT / "data" / "curriculum.json").read_text())

assert len(bank) >= 250, f"Expected a substantial 2019-2025 bank; got {len(bank)} items"
assert {item["year"] for item in bank} == set(range(2019, 2026))
assert all(item["official_paper_url"].startswith("https://www.nsw.gov.au/") for item in bank)
assert all(item["official_marking_guideline_url"].startswith("https://www.nsw.gov.au/") for item in bank)
assert all(item["paper_page"] for item in bank), "Every item should navigate to a source PDF page"

marks = defaultdict(int)
for item in bank:
    marks[item["year"]] += item["marks"]
assert marks == {year: 100 for year in range(2019, 2026)}, marks

curriculum_codes = {topic["code"] for stream in curriculum["streams"] for topic in stream["topics"]}
bank_codes = {topic_code for item in bank for topic_code in item["topic_codes"]}
assert bank_codes == curriculum_codes, sorted(curriculum_codes ^ bank_codes)

print(f"Verified {len(bank)} metadata items, 7 papers x 100 marks, and {len(bank_codes)} topics.")
