# ProjectHub

ProjectHub is a desktop app for managing local Django projects from a dark dashboard-style launcher.

It opens on a home page with project cards, then lets you switch to a manager page for the detailed table and server controls.

## Features

- Home page with project cards
- Start/stop project actions from the card
- Manager page for project status, ports, logs, and controls
- Add, edit, and remove project entries
- Django process monitoring and status updates
- Dark theme with consistent UI styling
- Windows installer output via PyInstaller + Inno Setup

## Project structure

```text
main.py                              # application entry point
ProjectHub.spec                      # PyInstaller packaging config
ProjectHubInstaller.iss               # Inno Setup installer config
computer.ico                         # app icon
Output/                              # generated installer output
projecthub/
├── __init__.py
├── app.py                            # QApplication bootstrap
├── config.py                         # app constants
├── dialogs.py                        # add/edit project dialog
├── main_window.py                    # main window + page switching
├── models.py                         # Project dataclass
├── network_utils.py                  # network checks
├── process_utils.py                  # process management helpers
├── project_manager_mixin.py          # add/edit/remove project logic
├── server_manager_mixin.py           # start/stop/restart Django server logic
├── storage.py                        # save/load project data
├── ui_builder.py                     # page layout and styling
└── __init__.py
```

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

## Build a fresh executable

```bash
pyinstaller --clean --noconfirm ProjectHub.spec
```

## Build a fresh installer

```bash
pyinstaller --clean --noconfirm ProjectHub.spec
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "ProjectHubInstaller.iss"
```

If Inno Setup is installed in the default location, the installer will be generated in the Output folder.

## Quick sanity check without a display

```bash
QT_QPA_PLATFORM=offscreen python -c "
from PySide6.QtWidgets import QApplication
from projecthub.main_window import ProjectHub
app = QApplication([])
w = ProjectHub()
print(w.windowTitle(), len(w.projects), w.stack.currentWidget().objectName())
"
```

## Notes

- The app starts on the home page by default.
- Project cards show a compact launcher-style summary and status.
- The manager page keeps the detailed project table and server log overview.
- Project data is stored under the user's home directory in a .projecthub folder.

