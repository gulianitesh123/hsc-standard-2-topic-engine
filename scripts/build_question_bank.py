#!/usr/bin/env python3
"""Build the metadata-only HSC Standard 2 question bank from official NESA PDFs.

The script deliberately outputs question identifiers, topic mappings, marks and
official source links only. It does not copy the wording, diagrams, screenshots
or PDFs into this repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]

SOURCES = {
    2019: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2019-hsc-mathematics-standard-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2019-hsc-mathematics-std-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2019",
    },
    2020: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2020-hsc-mathematics-standard-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2020-hsc-mathematics-standard-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2020",
    },
    2021: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2021-hsc-mathematics-standard-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2021-hsc-mathematics-standard-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2021",
    },
    2022: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2022-hsc-mathematics-standard-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2022-hsc-mathematics-standard-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2022",
    },
    2023: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2023-hsc-maths-std-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2023-hsc-maths-std-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2023",
    },
    2024: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2024-hsc-maths-std-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2024-hsc-maths-std-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2024",
    },
    2025: {
        "paper": "https://www.nsw.gov.au/sites/default/files/noindex/2025-10/2025-hsc-maths-standard-2.pdf",
        "guide": "https://www.nsw.gov.au/sites/default/files/noindex/2025-11/2025-hsc-maths-standard-2-mg.pdf",
        "exam_pack": "https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-standard/2025",
    },
}

TOPICS = {
    "MS-A1": {"name": "Formulae and Equations", "stream": "year-11", "strand": "Algebra"},
    "MS-A2": {"name": "Linear Relationships", "stream": "year-11", "strand": "Algebra"},
    "MS-A4": {"name": "Types of Relationships", "stream": "year-12", "strand": "Algebra"},
    "MS-M1": {"name": "Applications of Measurement", "stream": "year-11", "strand": "Measurement"},
    "MS-M2": {"name": "Working with Time", "stream": "year-11", "strand": "Measurement"},
    "MS-M6": {"name": "Non-right-angled Trigonometry", "stream": "year-12", "strand": "Measurement"},
    "MS-M7": {"name": "Rates and Ratios", "stream": "year-12", "strand": "Measurement"},
    "MS-F1": {"name": "Money Matters", "stream": "year-11", "strand": "Financial Mathematics"},
    "MS-F4": {"name": "Investments and Loans", "stream": "year-12", "strand": "Financial Mathematics"},
    "MS-F5": {"name": "Annuities", "stream": "year-12", "strand": "Financial Mathematics"},
    "MS-S1": {"name": "Data Analysis", "stream": "year-11", "strand": "Statistical Analysis"},
    "MS-S2": {"name": "Relative Frequency and Probability", "stream": "year-11", "strand": "Statistical Analysis"},
    "MS-S4": {"name": "Bivariate Data Analysis", "stream": "year-12", "strand": "Statistical Analysis"},
    "MS-S5": {"name": "The Normal Distribution", "stream": "year-12", "strand": "Statistical Analysis"},
    "MS-N2": {"name": "Network Concepts", "stream": "year-12", "strand": "Networks"},
    "MS-N3": {"name": "Critical Path Analysis", "stream": "year-12", "strand": "Networks"},
}

# Two Section I number labels are disrupted by the text layer in the official PDFs.
# These overrides retain the printed PDF page so source navigation stays complete.
PAGE_OVERRIDES = {2021: {6: 4}, 2022: {14: 7}}

# Year 11 outcomes use the form MS11-3, while Year 12 outcomes use MS2-12-3.
OUTCOME = r"MS(?:\d+)?-\d+(?:-\d+)?"
ROW = re.compile(
    rf"(?P<question>\d{{1,2}}(?:\s+\([a-z]\))?(?:\s+\([ivx]+\))?)\s+"
    rf"(?P<marks>[1-5])\s+(?P<topic>MS(?:2)?-[A-Z]\d)\s+.*?\s+"
    rf"(?P<outcomes>{OUTCOME}(?:\s*,\s*{OUTCOME})*)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tidy_grid_text(guide_path: Path) -> str:
    reader = PdfReader(guide_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages[-3:])
    mapping_grid = re.search(r"Mapping\s+Grid", text)
    if not mapping_grid:
        raise ValueError(f"No mapping grid found in {guide_path}")
    text = text[mapping_grid.end():].replace("–", "-")
    text = re.sub(r"(MS\d?-\d{2}-)\s+(\d+)", r"\1\2", text)
    return re.sub(r"\s+", " ", text)


def question_pages(paper_path: Path, year: int) -> dict[int, int]:
    """Find the first printed PDF page for each whole question number."""
    reader = PdfReader(paper_path)
    locations: dict[int, int] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for number in re.findall(r"\bQuestion\s+(\d{1,2})\b", text):
            locations.setdefault(int(number), page_number)
        # Section I has no printed "Question" prefix. A question number is either
        # on its own line or followed by an uppercase opening word; this avoids
        # mistaking values such as "2 cm" for a new question.
        if page_number <= 12:
            for match in re.finditer(r"(?m)^(1[0-5]|[1-9])(?=\s*(?:$|[A-Z]))", text):
                locations.setdefault(int(match.group(1)), page_number)
    locations.update(PAGE_OVERRIDES.get(year, {}))
    return locations


def question_sort_key(item: dict) -> tuple[int, str]:
    return item["question_number"], item["question"].lower()


def parse_year(year: int, source_dir: Path) -> tuple[list[dict], dict]:
    paper = source_dir / "papers" / f"{year}.pdf"
    guide = source_dir / "marking-guidelines" / f"{year}.pdf"
    if not paper.exists() or not guide.exists():
        raise FileNotFoundError(f"Expected {paper} and {guide}")

    pages = question_pages(paper, year)
    rows = []
    seen = set()
    for match in ROW.finditer(tidy_grid_text(guide)):
        question = re.sub(r"\s+", " ", match.group("question")).strip()
        topic_codes = list(dict.fromkeys(code.replace("MS2-", "MS-") for code in re.findall(r"MS(?:2)?-[A-Z]\d", match.group(0))))
        if any(topic_code not in TOPICS for topic_code in topic_codes):
            raise ValueError(f"Unrecognised topic in {year} {question}: {topic_codes}")
        if question in seen:
            continue
        seen.add(question)
        number = int(re.match(r"\d+", question).group())
        outcomes = re.findall(OUTCOME, match.group("outcomes"))
        rows.append({
            "id": f"hsc-{year}-q-{question.lower().replace(' ', '-').replace('(', '').replace(')', '')}",
            "year": year,
            "question": question,
            "question_number": number,
            "section": "I" if number <= 15 else "II",
            "marks": int(match.group("marks")),
            "topic_code": topic_codes[0],
            "topic_codes": topic_codes,
            "topic": TOPICS[topic_codes[0]]["name"],
            "topics": [TOPICS[topic_code]["name"] for topic_code in topic_codes],
            "stream": TOPICS[topic_codes[0]]["stream"],
            "strand": TOPICS[topic_codes[0]]["strand"],
            "outcomes": outcomes,
            "paper_page": pages.get(number),
            "official_paper_url": SOURCES[year]["paper"],
            "official_marking_guideline_url": SOURCES[year]["guide"],
            "official_exam_pack_url": SOURCES[year]["exam_pack"],
        })
    rows.sort(key=question_sort_key)
    marks = sum(item["marks"] for item in rows)
    if marks != 100:
        raise ValueError(f"{year} parsed {marks} marks rather than 100 ({len(rows)} items)")
    manifest = {
        "year": year,
        "paper": {"url": SOURCES[year]["paper"], "sha256": sha256(paper), "pages": len(PdfReader(paper).pages)},
        "marking_guideline": {"url": SOURCES[year]["guide"], "sha256": sha256(guide), "pages": len(PdfReader(guide).pages)},
        "exam_pack": SOURCES[year]["exam_pack"],
        "items": len(rows),
        "marks": marks,
    }
    return rows, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory with papers/<year>.pdf and marking-guidelines/<year>.pdf")
    args = parser.parse_args()

    bank: list[dict] = []
    manifest = {"generated_on": str(date.today()), "source_policy": "Metadata and official source links only; source PDFs are not included.", "years": []}
    for year in SOURCES:
        rows, source_record = parse_year(year, args.source_dir)
        bank.extend(rows)
        manifest["years"].append(source_record)

    covered = Counter(topic_code for item in bank for topic_code in item["topic_codes"])
    missing = sorted(set(TOPICS) - set(covered))
    if missing:
        raise ValueError(f"Topics with no indexed items: {', '.join(missing)}")

    data_dir = ROOT / "data"
    (data_dir / "questions.json").write_text(json.dumps(bank, indent=2) + "\n", encoding="utf-8")
    (data_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(bank)} question items across {len(SOURCES)} papers and {len(covered)} syllabus topics.")


if __name__ == "__main__":
    main()
