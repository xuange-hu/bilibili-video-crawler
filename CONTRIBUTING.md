# Contributing

bilibili-video-crawler is a Python tool for fetching Bilibili videos and metadata, with WBI
signing, rate-limit-aware retry, and SQLite persistence.

## Setup

```bash
git clone https://github.com/xuange-hu/bilibili-video-crawler && cd bilibili-video-crawler
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q            # full suite (network layer is mocked)
python -m mypy                # incremental type gate (see mypy.ini)
```

## Rules

- **Pure logic lives in `config.py` / `logger.py` / `database.py` / `wbi_sign.py`.** Add tests
  under `tests/`.
- **No live network in the test suite.** Mock the fetch layer; tests that call the real API are
  rejected.
- **Keep `crawler.py` thin.** Business logic that can't be unit-tested should be extracted into a
  pure, importable function (see `_evaluate_response`) so it can be tested offline.
- New modules are added to the `mypy.ini` `files =` list once they carry type annotations.

## Pull requests

Small and focused. Any behaviour change — especially retry/error-classification changes — must
include a test in `tests/`.
