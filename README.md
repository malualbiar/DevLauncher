# ProjectHub

Django development server manager (PySide6).

## Layout

```
main.py                              # entry point: `python main.py`
computer.png                         # application icon used by the window
projecthub/
├── __init__.py
├── config.py                        # constants (paths, defaults, timing)
├── models.py                        # Project dataclass
├── storage.py                       # load_projects() / save_projects()
├── network_utils.py                 # is_port_available()
├── process_utils.py                 # find_python_executable(), kill_process_tree()
├── dialogs.py                       # ProjectDialog (add/edit form)
├── ui_builder.py                    # UIBuilderMixin — builds all static widgets
├── project_manager_mixin.py         # ProjectManagerMixin — CRUD, table, context menu
├── server_manager_mixin.py          # ServerManagerMixin — QProcess start/stop/restart
├── main_window.py                   # ProjectHub(QMainWindow) — combines the mixins
└── app.py                           # QApplication bootstrap / main()
```

## Why this split

- **`config.py` / `models.py`** — pure data, no Qt or I/O, safe to import
  from anywhere (and to unit test without a display).
- **`storage.py` / `network_utils.py` / `process_utils.py`** — plain
  functions with no dependency on the main window, easy to test in
  isolation (e.g. mock `socket` for `is_port_available`, or feed
  `storage.load_projects()` a temp file).
- **`dialogs.py`** — the one self-contained popup, kept separate from
  the main window entirely.
- **`ui_builder.py` / `project_manager_mixin.py` / `server_manager_mixin.py`**
  — the original `ProjectHub` class did three different jobs (layout,
  project bookkeeping, process management). Splitting those into
  mixins keeps each file under ~250 lines and focused on one
  responsibility, while `main_window.py` stays a thin composition root
  that wires the mixins together and owns only truly cross-cutting
  state (`self.projects`, `self.processes`, `closeEvent`, `log()`).
- **`app.py` / `main.py`** — separates "build a QApplication and run
  it" from "define the window", which makes the window class importable
  and testable (see the smoke test below) without spinning up a full
  event loop.

## Running

```bash
pip install PySide6
python main.py
```

## Quick sanity check without a display

```bash
QT_QPA_PLATFORM=offscreen python -c "
from PySide6.QtWidgets import QApplication
from projecthub.main_window import ProjectHub
app = QApplication([])
w = ProjectHub()
print(w.windowTitle(), len(w.projects))
"
```
