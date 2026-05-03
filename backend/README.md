# Backend

## Setup
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in real keys
```

## Run tests
```bash
pytest -v
```

## Run M0 acceptance eval
```bash
python -m eval.run_eval --output eval/reports/m0_$(date +%Y%m%d).json
```
