# HSC Standard 2 Question Engine

A static, personal-use practice engine for the 2019-2025 HSC Mathematics Standard 2 papers.

Choose one of the 16 syllabus topics, optionally narrow by year or exam section, then open the matching question at the relevant page of the official NSW Government PDF. Completion ticks are saved only in the browser that you use.

## What is in the repository

- 378 topic-indexed question items from the seven official HSC papers.
- The 2017-syllabus Year 12 topic map plus Year 11 assumed knowledge.
- Official paper, marking-guideline and exam-pack links, source-PDF page references, marks and syllabus outcomes.
- A source manifest with URL, page count and SHA-256 evidence for each downloaded analysis source.

It does not contain exam PDFs, question text, diagrams, answers or screenshots. Those remain on the official sources. This makes the project an index and practice launcher rather than a republished past-paper library.

## Use it locally

Serve the folder from a local web server, then open the address it prints:

```sh
python3 -m http.server 4173
```

Visit `http://localhost:4173`.

## Rebuild the question metadata

The checked-in bank was produced from the official paper and marking-guideline PDFs using their Mapping Grids. Keep the PDFs outside this repository, with this layout:

```text
sources/
  papers/2019.pdf ... papers/2025.pdf
  marking-guidelines/2019.pdf ... marking-guidelines/2025.pdf
```

Then run:

```sh
python3 -m pip install pypdf
python3 scripts/build_question_bank.py --source-dir /path/to/sources
python3 scripts/verify_question_bank.py
```

The verification requires every paper to reconcile to 100 marks, each topic to be represented, every item to link to an official source, and every item to have an official PDF page.

## Source treatment

The topic mapping follows the NESA marking-guideline grids for the 2019-2025 Mathematics Standard 2 HSC papers. The linked [THSC Online catalogue](https://thsconline.github.io/s/yr12/Maths/) is included as a separate resource directory only: it contains both older General Maths material and trial/internal papers, so it should not be mixed into the verified 2019-2025 Standard 2 bank without its own topic mapping and source-permission check.

The 2019-2025 papers use the [Mathematics Standard Stage 6 (2017) syllabus](https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-standard-stage-6-2017). NESA's HSC specifications state that Year 11 knowledge may be examined in Mathematics Standard 2.
