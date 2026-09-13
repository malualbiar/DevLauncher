"""Data model for a managed project (Django, PHP, or Laravel)."""

from dataclasses import dataclass, field

from .config import DEFAULT_HOST, DEFAULT_PORT

# Supported project types.  New entries here are automatically propagated
# to the dialog, storage, and server-start logic.
PROJECT_TYPES = ["django", "laravel", "php"]


@dataclass
class Project:
    name: str
    path: str
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    auto_open_browser: bool = True
    project_type: str = "django"   # "django" | "laravel" | "php"
    status: str = "Stopped"
    last_log: str = ""
