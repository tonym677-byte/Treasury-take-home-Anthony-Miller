# Alcohol Label Review Assistant — Treasury Take-Home Prototype

Prepared for Anthony Miller's Treasury take-home submission.

## Live prototype

https://treasury-label-review-anthony-miller.streamlit.app/

Hosted on Streamlit Community Cloud from this repository's `main` branch, using `app.py`. Live smoke testing confirmed image upload, OCR, four sample field matches, and a review flag for a missing warning. The sample OCR runtime was 0.39 seconds; this is not a representative performance benchmark.

A standalone, human-in-the-loop prototype for comparing OCR-extracted alcohol label text against values entered from a label application. **This is not an official TTB tool, does not connect to COLA, and never approves or rejects a label.**

## Features

- Clear browser-based UI with single-image and batch (up to 25 images) review
- Offline Tesseract OCR; no external AI API or API key needed
- Comparison of brand, class/type, ABV/proof, net contents, producer, address, and country of origin
- Exact-text check for the standard government health warning, with mandatory visual typography review
- Field-level MATCH / REVIEW / NOT_CHECKED indicators; export CSV or JSON
- Defensive file-size/pixel limits, OCR timeout, and per-file error handling
- Automated unit tests

## Setup and run

**Requirements:** Python 3.10+, Tesseract OCR executable, and pip.

Install Tesseract: Ubuntu/Debian: `sudo apt-get install tesseract-ocr`; macOS (Homebrew): `brew install tesseract`; Windows: install Tesseract and ensure `tesseract.exe` is on PATH.

```bash
git clone https://github.com/tonym677-byte/Treasury-take-home-Anthony-Miller.git
cd Treasury-take-home-Anthony-Miller
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit (typically `http://localhost:8501`). Enter application values in the sidebar, upload an image, and click **Analyze labels**. The same values apply to all files in a batch. Export results using the download buttons.

## Tests

```bash
python -m pytest -q
```

## Deploy (Streamlit Community Cloud)

1. Push this folder to a GitHub repository.
2. At https://share.streamlit.io/ select **Create app**, choose the repository, branch, and `app.py` entrypoint.
3. `requirements.txt` installs Python dependencies and `packages.txt` installs Tesseract on supported Debian-based builds.
4. Deploy and test with a sample label. Copy the resulting public URL for the assignment submission.

The live prototype is deployed at the URL above. Use nonsensitive demonstration labels when testing.

## Architecture and tools

- `app.py`: Streamlit upload, forms, batch processing, visual results, exports.
- `src/ocr.py`: PIL preprocessing and local Tesseract OCR.
- `src/verifier.py`: deterministic field comparisons and warning-text checks.
- `tests/`: pytest regression tests.
- Libraries: Streamlit, Pillow, pytesseract, pytest. No network calls are made by application code.

## Approach and assumptions

1. **Human review first:** OCR is fallible. Missing text triggers REVIEW, not a definitive regulatory violation. All submissions require agent judgment.
2. **Scope:** This is a proof-of-concept, not a full beverage-specific regulatory rules engine. Optional fields are NOT_CHECKED if left blank. The same application fields are used for each image in a batch.
3. **Comparisons:** Brand/type/producer/address/country comparisons ignore case and punctuation, accommodating harmless formatting differences. ABV compares percentages and US proof (2× ABV). Net contents supports mL and L equivalence.
4. **Warning:** The standard government warning must be present. The text check preserves capitalization and punctuation (normalizing whitespace only). OCR cannot verify bold weight, size, placement, or full regulatory compliance; these require visual review. OCR line wrapping or errors may create false REVIEW flags.
5. **Privacy:** Files are processed in server memory for the current session; no database, account system, or external OCR API. Hosting providers may independently log or retain data.
6. **Performance:** Stakeholders requested approximately 5 seconds per label. OCR uses an 8-second per-image timeout and a small thread pool for batches; speed depends on image size and host resources and is not guaranteed. No benchmark is claimed.
7. **Image limitations:** PNG/JPEG/WEBP, 12 MB and 20 MP maximum. Skewed, blurry, low-contrast, or highly stylized labels may fail OCR.

## Known limitations / next steps

- No COLA integration, authentication, audit logs, persistent case history, or FedRAMP authorization.
- No image-coordinate highlighting or reliable validation of warning typography.
- No automatic deskewing, perspective correction, or multimodal vision model.
- No per-file application metadata in batch mode; add CSV manifest support for production.
- Regulatory checks beyond the common fields are not implemented; consult current TTB requirements before real use.
- For production: role-based access, retention policies, threat modeling, rate limits, accessibility testing, image redaction, human audit trails, and performance benchmarking.

## Assignment source

https://github.com/treasurytakehome-rgb/instructions
