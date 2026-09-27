# ANC8+ Programme Review — Ethiopia

Four-page dashboard presenting approved aggregate study evidence for programme review.
Descriptive patterns and predictive model findings do not establish causal effects.
Decision cues are questions for local investigation, not operational priorities.

## Run

Use Python 3.13. Install `requirements.txt`, then from this repository root run:

```
python -m streamlit run dashboard/streamlit_app/app.py
```

## Streamlit Community Cloud

- Repository: `binibhi2013-cpu/anc8-programme-review`
- Branch: `main`
- Main file: `dashboard/streamlit_app/app.py`
- Advanced settings: Python 3.13
- Intended visibility: public

The repository contains only runtime code, display specifications, approved aggregate
tables, their original checksum manifest, and the derived geography/crosswalk.
The original manifest is retained intact; source files not required by the dashboard
are intentionally omitted. Runtime loaders verify every requested table against it.
Raw survey data, individual records, development notebooks, source shapefiles, backups
and local provenance logs are not included.

The dashboard is a research/capstone product. Its presentation is MoH-inspired;
no official endorsement is implied. Keep source, denominator and uncertainty context
with any exported evidence. Consult original guidance for local applicability.
