import json
import os
from unittest.mock import MagicMock, patch

import pytest

from ..app.services.extract import extract_action_items, extract_action_items_llm

_PATCH_TARGET = "week2.app.services.extract.chat"


def _mock_chat_response(items: list) -> MagicMock:
    mock = MagicMock()
    mock.message.content = json.dumps({"items": items})
    return mock


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# --- extract_action_items_llm ---

def test_llm_empty_input_returns_empty_list():
    with patch(_PATCH_TARGET) as mock_chat:
        result = extract_action_items_llm("")
        mock_chat.assert_not_called()
    assert result == []


def test_llm_whitespace_only_returns_empty_list():
    with patch(_PATCH_TARGET) as mock_chat:
        result = extract_action_items_llm("   \n\t  ")
        mock_chat.assert_not_called()
    assert result == []


def test_llm_free_form_text_extracts_action_items():
    expected = ["fix the login bug", "update the README"]
    with patch(_PATCH_TARGET, return_value=_mock_chat_response(expected)):
        result = extract_action_items_llm(
            "We need to fix the login bug and update the README."
        )
    assert result == expected


def test_llm_bullet_list_extracts_items():
    expected = ["Set up database", "Implement API endpoint", "Write tests"]
    with patch(_PATCH_TARGET, return_value=_mock_chat_response(expected)):
        result = extract_action_items_llm(
            "- Set up database\n- Implement API endpoint\n1. Write tests"
        )
    assert result == expected


def test_llm_keyword_prefixed_lines_extracts_items():
    expected = ["Send report to team", "Schedule review meeting"]
    with patch(_PATCH_TARGET, return_value=_mock_chat_response(expected)):
        result = extract_action_items_llm(
            "todo: Send report to team\naction: Schedule review meeting"
        )
    assert result == expected


def test_llm_no_action_items_returns_empty_list():
    with patch(_PATCH_TARGET, return_value=_mock_chat_response([])):
        result = extract_action_items_llm("The weather is nice today.")
    assert result == []
