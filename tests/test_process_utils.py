import os
from pathlib import Path

from projecthub.process_utils import (
    build_activation_script,
    build_process_environment,
    get_venv_dir,
)


def test_get_venv_dir_finds_local_virtualenv(tmp_path):
    venv_dir = tmp_path / ".venv"
    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    bin_dir.mkdir(parents=True)

    assert get_venv_dir(tmp_path) == venv_dir


def test_build_process_environment_isolates_project_runtime(tmp_path):
    venv_dir = tmp_path / ".venv"
    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    bin_dir.mkdir(parents=True)

    env = {
        "PATH": "C:/parent/bin",
        "PYTHONPATH": "C:/parent/site-packages",
        "PYTHONHOME": "C:/parent/python",
    }

    result = build_process_environment(tmp_path, env)

    assert result["PYTHONUNBUFFERED"] == "1"
    assert result["VIRTUAL_ENV"] == str(venv_dir)
    assert result["PATH"].startswith(str(bin_dir))
    assert result["PYTHONPATH"] == str(tmp_path)
    assert "PYTHONHOME" not in result
    assert "HF_HOME" in result
    assert result["PYTHONNOUSERSITE"] == "1"
    assert str(Path.home()) == result["HOME"]


def test_build_activation_script_uses_venv_activation(tmp_path):
    venv_dir = tmp_path / ".venv"
    activate = venv_dir / "Scripts" / "activate.bat"
    activate.parent.mkdir(parents=True)
    activate.write_text("@echo off\n")

    script = build_activation_script(
        tmp_path,
        "C:/venv/Scripts/python.exe",
        "C:/project/manage.py",
        "127.0.0.1:8000",
    )

    assert script is not None
    with open(script, "r", encoding="utf-8") as handle:
        content = handle.read()

    assert 'activate.bat' in content
    assert 'manage.py' in content
    assert '127.0.0.1:8000' in content
    assert os.path.exists(script)
