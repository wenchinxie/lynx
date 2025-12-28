# lynx Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-14

## Active Technologies
- SQLite (existing `lynx.db`) - schema migration required (002-run-timestamp-disambiguation)
- Python 3.13 (with uv package manager) + pandas 2.0+, FastAPI 0.109+, SQLite3 (stdlib), Plotly 5.18+, Jinja2 3.1+ (002-run-timestamp-disambiguation)
- SQLite (`lynx.db`) with Parquet artifacts (002-run-timestamp-disambiguation)
- Python 3.13 (with uv package manager) + pandas 2.0+, FastAPI 0.109+, SQLite3 (stdlib), Plotly 5.18+, Jinja2 3.1+, uvicorn 0.27+, click 8.1+ (002-run-timestamp-disambiguation)
- SQLite (`lynx.db`) for metadata + Parquet for artifacts (existing architecture) (002-run-timestamp-disambiguation)

- Python 3.13 (with uv package manager) (001-backtest-monitor-dashboard)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.13 (with uv package manager): Follow standard conventions

## Recent Changes
- 002-run-timestamp-disambiguation: Added Python 3.13 (with uv package manager) + pandas 2.0+, FastAPI 0.109+, SQLite3 (stdlib), Plotly 5.18+, Jinja2 3.1+, uvicorn 0.27+, click 8.1+
- 002-run-timestamp-disambiguation: Added Python 3.13 (with uv package manager) + pandas 2.0+, FastAPI 0.109+, SQLite3 (stdlib), Plotly 5.18+, Jinja2 3.1+
- 002-run-timestamp-disambiguation: Added Python 3.13 (with uv package manager)


<!-- MANUAL ADDITIONS START -->

## Dashboard

Start the dashboard server:

```bash
source .venv/bin/activate
uvicorn lynx.dashboard.server:app --host 0.0.0.0 --port 5301
```

Then open http://localhost:5301 in your browser.

## Test Data

Fake test data is stored in `~/.lynx/`:
- `lynx.db` - SQLite metadata database
- `artifacts/` - Parquet files for each run

<!-- MANUAL ADDITIONS END -->
