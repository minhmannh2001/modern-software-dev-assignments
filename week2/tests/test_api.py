from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import week2.app.db as db_module
from week2.app.main import app

_LLM_PATCH = "week2.app.services.extract.chat"


def _mock_llm(items: list) -> MagicMock:
    mock = MagicMock()
    mock.message.content = json.dumps({"items": items})
    return mock


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    with TestClient(app) as client:
        yield client


# --- /notes ---

def test_create_note_returns_note(client):
    res = client.post("/notes", json={"content": "hello world"})
    assert res.status_code == 200
    body = res.json()
    assert body["content"] == "hello world"
    assert "id" in body
    assert "created_at" in body


def test_create_note_empty_content_returns_400(client):
    res = client.post("/notes", json={"content": ""})
    assert res.status_code == 400


def test_get_note_returns_note(client):
    created = client.post("/notes", json={"content": "my note"}).json()
    res = client.get(f"/notes/{created['id']}")
    assert res.status_code == 200
    assert res.json()["content"] == "my note"


def test_get_note_not_found_returns_404(client):
    res = client.get("/notes/99999")
    assert res.status_code == 404


# --- /action-items ---

def test_extract_returns_items(client):
    res = client.post("/action-items/extract", json={"text": "- fix the bug\n- write tests"})
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) == 2


def test_extract_empty_text_returns_400(client):
    res = client.post("/action-items/extract", json={"text": ""})
    assert res.status_code == 400


def test_list_action_items_returns_list(client):
    client.post("/action-items/extract", json={"text": "- task one"})
    res = client.get("/action-items")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert any(item["text"] == "task one" for item in res.json())


# --- /action-items/extract-llm ---

def test_extract_llm_returns_items(client):
    with patch(_LLM_PATCH, return_value=_mock_llm(["fix the bug", "write tests"])):
        res = client.post("/action-items/extract-llm", json={"text": "we need to fix the bug and write tests"})
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["text"] == "fix the bug"


def test_extract_llm_empty_text_returns_400(client):
    res = client.post("/action-items/extract-llm", json={"text": ""})
    assert res.status_code == 400


# --- GET /notes ---

def test_list_notes_returns_list(client):
    client.post("/notes", json={"content": "first note"})
    client.post("/notes", json={"content": "second note"})
    res = client.get("/notes")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert any(n["content"] == "first note" for n in data)


def test_mark_done_returns_updated_status(client):
    extract_body = client.post(
        "/action-items/extract", json={"text": "- task one"}
    ).json()
    item_id = extract_body["items"][0]["id"]

    res = client.post(f"/action-items/{item_id}/done", json={"done": True})
    assert res.status_code == 200
    assert res.json()["done"] is True
