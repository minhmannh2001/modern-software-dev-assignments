import os
import sys
from unittest.mock import patch

import pytest


def load_config(env: dict):
    """Helper: load config with a controlled environment, bypassing .env file."""
    original = os.environ.copy()
    os.environ.clear()
    os.environ.update(env)
    try:
        if "server.config" in sys.modules:
            del sys.modules["server.config"]
        with patch("dotenv.load_dotenv"):  # prevent .env file from overriding test env
            from server.config import Config
            return Config()
    finally:
        os.environ.clear()
        os.environ.update(original)


_FULL_ENV = {
    "GITHUB_CLIENT_ID": "id123",
    "GITHUB_CLIENT_SECRET": "secret123",
    "REDIRECT_URI": "http://localhost:8000/oauth/callback",
}


def test_missing_github_client_id_raises():
    with pytest.raises(Exception, match="GITHUB_CLIENT_ID"):
        load_config({"GITHUB_CLIENT_SECRET": "secret", "REDIRECT_URI": "http://localhost/cb"})


def test_missing_github_client_secret_raises():
    with pytest.raises(Exception, match="GITHUB_CLIENT_SECRET"):
        load_config({"GITHUB_CLIENT_ID": "id", "REDIRECT_URI": "http://localhost/cb"})


def test_all_required_vars_loads_correctly():
    config = load_config(_FULL_ENV)
    assert config.github_client_id == "id123"
    assert config.github_client_secret == "secret123"
    assert config.redirect_uri == "http://localhost:8000/oauth/callback"


def test_port_defaults_to_8000():
    config = load_config(_FULL_ENV)
    assert config.port == 8000
