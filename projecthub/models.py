"""Data model for a managed Django project."""

from dataclasses import dataclass

from .config import DEFAULT_HOST, DEFAULT_PORT


@dataclass
class Project:
    name: str
    path: str
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    auto_open_browser: bool = True
    status: str = "Stopped"
    last_log: str = ""
