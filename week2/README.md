# Action Item Extractor

A FastAPI + SQLite app that converts free-form notes into enumerated action items. Supports both heuristic-based and LLM-powered extraction via Ollama.

## Overview

- **Heuristic extraction** — fast, offline; detects bullet points, checkboxes, and keyword-prefixed lines (`todo:`, `action:`, `next:`)
- **LLM extraction** — uses a local Ollama model to extract action items from any free-form text
- **Persistence** — notes and action items are stored in a local SQLite database
- **Frontend** — minimal HTML interface served at `http://localhost:8000`

## Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- [Ollama](https://ollama.com/) (for LLM extraction)

### Install dependencies

```bash
poetry install
```

### Pull an Ollama model

```bash
ollama pull llama3.1:8b
```

To use a different model, set the `OLLAMA_MODEL` environment variable:

```bash
export OLLAMA_MODEL=mistral-nemo:12b
```

## Running the app

From the project root:

```bash
poetry run uvicorn week2.app.main:app --reload
```

Open `http://localhost:8000` in a browser.

## API Endpoints

### Notes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/notes` | List all saved notes |
| `POST` | `/notes` | Create a note |
| `GET` | `/notes/{id}` | Get a note by ID |

**POST /notes** request body:
```json
{ "content": "your note text" }
```

### Action Items

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/action-items/extract` | Extract using heuristics |
| `POST` | `/action-items/extract-llm` | Extract using Ollama LLM |
| `GET` | `/action-items` | List all action items (optionally filter by `?note_id=`) |
| `POST` | `/action-items/{id}/done` | Mark an item done/undone |

**POST /action-items/extract** and **POST /action-items/extract-llm** request body:
```json
{ "text": "your notes here", "save_note": true }
```

**POST /action-items/{id}/done** request body:
```json
{ "done": true }
```

Interactive API docs are available at `http://localhost:8000/docs`.

## Running the tests

```bash
poetry run pytest week2/tests/
```

Tests use an in-memory SQLite database and mock all Ollama calls — no running server required.

To run a specific test file:

```bash
poetry run pytest week2/tests/test_extract.py   # unit tests for extraction logic
poetry run pytest week2/tests/test_api.py       # API integration tests
```
