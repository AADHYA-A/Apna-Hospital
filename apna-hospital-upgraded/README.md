# Apna Hospital: AI symptom triage

Describe how you feel in plain language. Get ranked possible conditions, an urgency level,
smart follow-up questions, a care plan and a PDF report.

## Run locally
```bash
pip install -r requirements.txt
python train.py          # builds models/model.joblib (already included)
python main.py           # http://localhost:5000
```

## Deploy (pick one, all free)

**Render** (easiest): push this folder to GitHub, then Render -> New -> Blueprint -> select the repo.
`render.yaml` is already configured (build runs `train.py`, health check on `/health`).

**Hugging Face Spaces**: New Space -> SDK "Docker" -> upload these files. The `Dockerfile` listens on port 7860.

**Railway / Heroku-style**: the `Procfile` runs `gunicorn main:app`.

## What's new vs. the original
| Area | Upgrade |
|---|---|
| Input | Free-text understanding (synonyms, typos, negation), searchable symptom chips, voice input |
| Model | Probabilistic top-3 ranking (random forest) instead of a single label |
| Reasoning | Adaptive follow-up questions that best separate the leading candidates, live re-ranking |
| Safety | Red-flag emergency override, severity score, 4-level triage, 112/108 guidance |
| Explainability | "Why this match": matched vs. missing typical symptoms |
| Output | Care plan, treatments, specialist + Google Maps link, PDF report, print, copy summary |
| UX | Dark mode, mobile layout, local history, accessible, reduced-motion aware |
| Platform | JSON API, `/health`, Docker, Procfile, render.yaml, no `debug=True` in production |
| Data quality | Fixed a row-shift bug in `medications.csv` (see `fix_data.py`), fixed 2 wrong precaution rows, fixed name mismatches that made two diseases silently return "NA" |
| Robustness | Pickle version mismatches can't crash the app: the model auto-retrains if it fails to load |

## API
```
POST /api/predict   {"symptoms":["headache","vomiting"]}
POST /api/parse     {"text":"bad headache, threw up, no fever"}
GET  /api/symptoms
GET  /health
```

## Disclaimer
Educational project. Not a medical device and not a diagnosis.
