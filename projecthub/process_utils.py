"""Helpers for locating a project's Python interpreter and for
forcefully killing a Django dev server's process tree (the dev server
spawns a reloader child process, so killing just the parent PID is not
enough)."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Callable, Optional


def find_python_executable(project_path) -> str:
    """Look for a project-local virtualenv interpreter; fall back to
    the interpreter currently running ProjectHub."""
    project_path = Path(project_path)

    if os.name == "nt":
        candidates = [
            project_path / ".venv" / "Scripts" / "python.exe",
            project_path / "venv" / "Scripts" / "python.exe",
        ]
    else:
        candidates = [
            project_path / ".venv" / "bin" / "python",
            project_path / "venv" / "bin" / "python",
        ]

    for executable in candidates:
        if executable.exists():
            return str(executable)

    return sys.executable


def kill_process_tree(
    pid: int,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """Kill a process and all of its children."""
    if not pid:
        return

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )

        except subprocess.TimeoutExpired:
            if log:
                log("[ProjectHub] taskkill timed out.")

        except Exception as exc:
            if log:
                log(f"[ProjectHub] Could not kill process tree: {exc}")

    else:
        try:
            os.kill(pid, 9)

        except ProcessLookupError:
            pass

        except Exception as exc:
            if log:
                log(f"[ProjectHub] Could not kill process: {exc}")
