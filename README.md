# Human Judge Coordinate Emulator

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_pilot_fixture.py --images 20 --annotators 3
python scripts/human_agreement.py data/pilot_fixture/annotations.json
python scripts/evaluate_baseline.py data/pilot_fixture/annotations.json
streamlit run src/annotation_app.py
uvicorn src.api:app --reload
```

API test:

```bash
curl -X POST http://localhost:8000/predict -F image=@path/to/image.jpg
```

## Important dataset limitation

`generate_pilot_fixture.py` creates synthetic fixtures only. It does **not** collect BOTB images or human labels. A real 1,000-image × 3-annotator pilot requires permitted image access, consented annotators, independent labeling, and review of source terms. The annotation UI stores labels locally in SQLite and exports them for validation.

## Components

- `src/annotation_app.py`: Streamlit coordinate capture UI
- `src/validate_images.py`: decode checks, SHA-256 manifest, duplicate detection
- `scripts/generate_pilot_fixture.py`: synthetic pipeline fixture
- `scripts/human_agreement.py`: pairwise human disagreement report
- `scripts/evaluate_baseline.py`: center baseline metrics
- `src/api.py`: FastAPI prediction endpoint using the transparent center baseline

The API intentionally does not automate competition entry, clicking, payment, account activity, or external submission.
