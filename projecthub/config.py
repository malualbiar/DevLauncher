"""Application-wide configuration constants."""

from pathlib import Path

APP_NAME = "ProjectHub"

DATA_DIR = Path.home() / ".projecthub"

PROJECTS_FILE = DATA_DIR / "projects.json"

# Use the Windows-compatible ICO file so the app icon also appears in the taskbar.
ICON_FILE = Path(__file__).resolve().parent.parent / "computer.ico"

DEFAULT_HOST = "127.0.0.1"

DEFAULT_PORT = 8000

# Substrings that indicate the Django dev server has finished starting.
SERVER_READY_MESSAGES = [
    "Starting development server at",
    "Quit the server with",
    "Watching for file changes",
    "System check identified no issues",
]

# Substrings that indicate a Laravel artisan serve has finished starting.
LARAVEL_READY_MESSAGES = [
    "Development Server",         # "Laravel development server started"
    "started on http",
    "Press Ctrl+C to stop",
]

# Substrings that indicate the PHP built-in server is ready.
PHP_READY_MESSAGES = [
    "PHP",                        # "PHP X.Y.Z Development Server"
    "started",
    "Listening on",
]

# How often (ms) to poll running projects to detect readiness.
PORT_POLL_INTERVAL_MS = 500

# How long to wait for a freshly started process before giving up.
PROCESS_START_TIMEOUT_MS = 1500

# How long to wait for a process to actually terminate.
PROCESS_STOP_TIMEOUT_MS = 3000
