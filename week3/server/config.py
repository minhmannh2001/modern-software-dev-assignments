import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_REQUIRED = ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "REDIRECT_URI")


@dataclass
class Config:
    github_client_id: str
    github_client_secret: str
    redirect_uri: str
    port: int

    def __init__(self) -> None:
        missing = [k for k in _REQUIRED if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        self.github_client_id = os.environ["GITHUB_CLIENT_ID"]
        self.github_client_secret = os.environ["GITHUB_CLIENT_SECRET"]
        self.redirect_uri = os.environ["REDIRECT_URI"]
        self.port = int(os.getenv("PORT", "8000"))
