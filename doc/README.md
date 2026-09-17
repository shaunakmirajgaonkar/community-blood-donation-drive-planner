# Community Blood Donation Drive Planner

100% local Streamlit planning dashboard for community blood-drive location and timing analysis.

## Core features
- blood-group demand-gap analysis
- donation-history reliability signals
- travel access and population reach analysis
- local event-calendar opportunity analysis
- candidate site/date scoring
- estimated drive-capacity planning signal
- High/Critical review queue
- what-if planning scenario lab
- CSV reports and data-quality checks
- local SVG visuals
- no external APIs or cloud inference

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q
streamlit run app.py
```

This is planning support only and does not determine donor eligibility, medical suitability, blood safety, or clinical inventory decisions.
