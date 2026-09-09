"""Load and save the project list to disk as JSON."""

import json
from dataclasses import asdict
from typing import Callable, List, Optional

from .config import DEFAULT_HOST, DEFAULT_PORT, DATA_DIR, PROJECTS_FILE
from .models import Project


def save_projects(
    projects: List[Project],
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """Persist the given projects to PROJECTS_FILE.

    Runtime-only fields (status) are reset to "Stopped" before saving,
    since a project should never be reloaded as "Running".
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        data = []
        for project in projects:
            item = asdict(project)
            item["status"] = "Stopped"
            data.append(item)

        with open(PROJECTS_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except Exception as exc:
        if log:
            log(f"[ProjectHub] Could not save projects: {exc}")


def load_projects(
    log: Optional[Callable[[str], None]] = None,
) -> List[Project]:
    """Load the project list from PROJECTS_FILE, if it exists."""
    projects: List[Project] = []

    if not PROJECTS_FILE.exists():
        return projects

    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            return projects

        for item in data:
            if not isinstance(item, dict):
                continue

            try:
                project = Project(
                    name=str(item.get("name", "Unnamed")),
                    path=str(item.get("path", "")),
                    host=str(item.get("host", DEFAULT_HOST)),
                    port=int(item.get("port", DEFAULT_PORT)),
                    auto_open_browser=bool(
                        item.get("auto_open_browser", True)
                    ),
                    status="Stopped",
                    last_log=str(item.get("last_log", "")),
                )
                projects.append(project)

            except (TypeError, ValueError):
                continue

    except Exception as exc:
        message = f"Could not load projects: {exc}"
        if log:
            log(message)
        else:
            print(message)

    return projects
