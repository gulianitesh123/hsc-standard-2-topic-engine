# HSC Standard 2 Question Engine

A static, personal-use practice engine for the 2019-2025 HSC Mathematics Standard 2 papers.

Choose one of the 16 syllabus topics, optionally narrow by year or exam section, then select a matching card. The question bank remains on the left while the official source PDF is displayed on the right at the relevant page. Completion ticks are saved only in the browser that you use.

## What is in the repository

- 378 topic-indexed question items from the seven official HSC papers.
- The 2017-syllabus Year 12 topic map plus Year 11 assumed knowledge.
- Official paper, marking-guideline and exam-pack links, source-PDF page references, marks and syllabus outcomes.
- A source manifest with URL, page count and SHA-256 evidence for each downloaded analysis source.
- A separately-filterable catalogue of 93 current (2019 onward) THSC Mathematics Standard trial papers. These are paper-level library records, not topic-labelled question records.

It does not contain exam PDFs, question text, diagrams, answers or screenshots. Those remain on the source sites or in a local personal cache. This makes the public project an index and study workspace rather than a republished past-paper library.

## Use it locally

Serve the folder from a local web server, then open the address it prints:

```sh
python3 -m http.server 4173
```

Visit `http://localhost:4173`.

## Personal THSC cache and page captures

The THSC trial library in the site opens THSC's own embedded viewer. To retain personal offline copies and first-page PNG captures, run the cache command with a directory **outside this repository**:

```sh
python3 scripts/download_thsc_personal_cache.py \
  --output-dir /path/outside-this-repository/thsc-standard-2 \
  --render-first-page
```

The downloader is resumable and creates `manifest.json` with the catalogue source, source viewer URL, download timestamp, byte count and SHA-256 for every file. It only fetches the current Standard Maths section of the public THSC trial catalogue (93 records when this library was last indexed). Do not add the resulting PDFs or captures to the public repository unless you have the rightsholders' permission.

To use those local PDFs inside the same left-bank/right-viewer workspace, start the companion server instead of `http.server`:

```sh
python3 scripts/serve_personal_workspace.py \
  --cache-dir /path/outside-this-repository/thsc-standard-2
```

On `http://127.0.0.1:4173`, THSC trial cards use cached PDFs when present. The public GitHub Pages version never receives those files and continues to use THSC's online viewer.

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

The topic mapping follows the NESA marking-guideline grids for the 2019-2025 Mathematics Standard 2 HSC papers. The linked [THSC Online catalogue](https://thsconline.github.io/s/yr12/Maths/) is deliberately a separate library: it contains both older General Maths material and trial/internal papers. The 93 current Standard trial papers are useful for practice, but are not mixed into the verified official topic bank until each question is individually mapped and checked.

The 2019-2025 papers use the [Mathematics Standard Stage 6 (2017) syllabus](https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-standard-stage-6-2017). NESA's HSC specifications state that Year 11 knowledge may be examined in Mathematics Standard 2.
