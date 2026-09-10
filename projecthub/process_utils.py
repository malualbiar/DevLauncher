"""Helpers for locating a project's Python interpreter and for
forcefully killing a Django dev server's process tree (the dev server
spawns a reloader child process, so killing just the parent PID is not
enough)."""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Mapping, Optional


def get_venv_dir(project_path) -> Optional[Path]:
    """Return the project-local virtualenv directory if present."""
    project_path = Path(project_path)

    candidates = [
        project_path / ".venv",
        project_path / "venv",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return None


def find_python_executable(project_path) -> str:
    """Look for a project-local virtualenv interpreter; fall back to
    the interpreter currently running ProjectHub."""
    project_path = Path(project_path)

    venv_dir = get_venv_dir(project_path)
    if not venv_dir:
        return sys.executable

    if os.name == "nt":
        executable = venv_dir / "Scripts" / "python.exe"
    else:
        executable = venv_dir / "bin" / "python"

    if executable.exists():
        return str(executable)

    return sys.executable


def build_process_environment(project_path, inherited_env: Optional[Mapping[str, str]] = None) -> dict:
    """Build a clean environment for a project process.

    The project's local venv should be authoritative, and inherited Python
    path contamination from the ProjectHub runtime should never leak into a
    child project process.
    """
    env = dict(os.environ if inherited_env is None else inherited_env)

    project_path = Path(project_path)
    venv_dir = get_venv_dir(project_path)

    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
        "PYTHONNOUSERSITE",
        "HF_HOME",
        "HUGGINGFACE_HUB_CACHE",
        "TRANSFORMERS_CACHE",
        "HF_DATASETS_CACHE",
        "XDG_CACHE_HOME",
    ):
        env.pop(key, None)

    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONSAFEPATH"] = "1"

    home_dir = str(Path.home())
    env["HOME"] = home_dir
    env["USERPROFILE"] = home_dir
    env["HOMEDRIVE"] = os.environ.get("HOMEDRIVE", "C:")
    env["HOMEPATH"] = os.environ.get("HOMEPATH", "\\Users\\" + Path.home().name)
    env["HF_HOME"] = str(Path.home() / ".cache" / "huggingface")
    env["TRANSFORMERS_CACHE"] = str(Path.home() / ".cache" / "huggingface" / "transformers")

    if venv_dir:
        if os.name == "nt":
            venv_bin = venv_dir / "Scripts"
        else:
            venv_bin = venv_dir / "bin"

        existing_path = env.get("PATH", "")
        env["PATH"] = str(venv_bin) + (os.pathsep + existing_path if existing_path else "")
        env["VIRTUAL_ENV"] = str(venv_dir)
        env["CONDA_PREFIX"] = str(venv_dir)

    env["PYTHONPATH"] = str(project_path)

    return env


def build_activation_script(project_path, python_executable, manage_py, host_port):
    """Write a small .bat launcher that activates the project venv and runs
    the project command. This is more reliable than passing a shell command
    string directly to cmd.exe via QProcess on Windows.
    """
    if os.name != "nt":
        return None

    venv_dir = get_venv_dir(project_path)
    script_handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".bat",
        prefix="projecthub_",
        delete=False,
        newline="\r\n",
    )

    script_handle.write("@echo off\r\n")

    if venv_dir:
        activate_script = venv_dir / "Scripts" / "activate.bat"
        if activate_script.exists():
            script_handle.write(f'call "{activate_script}"\r\n')

    script_handle.write(f'"{python_executable}" "{manage_py}" runserver "{host_port}"\r\n')
    script_handle.close()

    return script_handle.name


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
