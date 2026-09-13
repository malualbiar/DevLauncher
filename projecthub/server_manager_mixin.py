"""Starting, stopping, restarting and monitoring each project's dev
server (one QProcess per running project).

Supports Django, Laravel (artisan serve), and plain PHP (built-in server).
"""

import os
import webbrowser
from pathlib import Path

from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import QMessageBox

from .config import (
    LARAVEL_READY_MESSAGES,
    PHP_READY_MESSAGES,
    PROCESS_START_TIMEOUT_MS,
    SERVER_READY_MESSAGES,
)
from .network_utils import is_port_available
from .process_utils import (
    build_activation_script,
    build_php_activation_script,
    build_process_environment,
    find_php_executable,
    find_python_executable,
    kill_process_tree,
)


class ServerManagerMixin:
    # ================================================================
    # START
    # ================================================================

    def start_selected(self):
        project = self.get_selected_project()
        if project:
            self.start_project(project)

    def start_project(self, project):
        if project.name in self.processes:
            self.log(f"[{project.name}] Server is already running.")
            return

        project_path = Path(project.path)

        if not project_path.exists():
            QMessageBox.warning(
                self,
                "Project Not Found",
                f"The project folder no longer exists:\n\n{project.path}",
            )
            project.status = "Error"
            self.refresh_table()
            return

        project_type = getattr(project, "project_type", "django")

        if project_type in ("laravel", "php"):
            self._start_php_project(project, project_path, project_type)
        else:
            self._start_django_project(project, project_path)

    # ----------------------------------------------------------------
    # Django
    # ----------------------------------------------------------------

    def _start_django_project(self, project, project_path: Path):
        manage_py = project_path / "manage.py"

        if not manage_py.exists():
            QMessageBox.warning(
                self,
                "Django Project Error",
                f"manage.py was not found in:\n\n{project.path}",
            )
            project.status = "Error"
            self.refresh_table()
            return

        if not is_port_available(project.host, project.port):
            QMessageBox.warning(
                self,
                "Port Already In Use",
                f"Port {project.port} is already in use.\n\n"
                f"Project: {project.name}\n"
                f"Host: {project.host}\n"
                f"Port: {project.port}",
            )
            return

        python_executable = find_python_executable(project_path)

        self.log(f"[{project.name}] Python: {python_executable}")
        self.log(f"[{project.name}] Working directory: {project_path}")
        self.log(
            f"[{project.name}] Starting Django on "
            f"{project.host}:{project.port}"
        )

        process = self._build_process(project, project_path)

        self.processes[project.name] = process
        self.project_logs[project.name] = ""
        self.browser_opened.discard(project.name)

        project.status = "Starting"
        self.refresh_table()

        arguments = [
            str(manage_py),
            "runserver",
            f"{project.host}:{project.port}",
        ]

        if os.name == "nt":
            bat_script = build_activation_script(
                project_path,
                python_executable,
                str(manage_py),
                f"{project.host}:{project.port}",
            )
            self.log(f"[{project.name}] Launch script: {bat_script}")
            if bat_script:
                process.start("cmd.exe", ["/d", "/s", "/c", bat_script])
                return

        process.start(python_executable, arguments)

        if not process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            self.log(f"[{project.name}] Failed to start Django.")

            error = process.errorString()
            if error:
                self.log(f"[{project.name}] {error}")

            project.status = "Error"
            self.processes.pop(project.name, None)
            self.refresh_table()

    # ----------------------------------------------------------------
    # PHP / Laravel
    # ----------------------------------------------------------------

    def _start_php_project(self, project, project_path: Path, project_type: str):
        php_executable = find_php_executable()

        if not php_executable:
            QMessageBox.warning(
                self,
                "PHP Not Found",
                "PHP was not found on your system PATH.\n\n"
                "Install PHP and make sure it is accessible from the command line.",
            )
            project.status = "Error"
            self.refresh_table()
            return

        if project_type == "laravel":
            artisan = project_path / "artisan"
            if not artisan.exists():
                QMessageBox.warning(
                    self,
                    "Laravel Project Error",
                    f"artisan was not found in:\n\n{project.path}",
                )
                project.status = "Error"
                self.refresh_table()
                return

        if not is_port_available(project.host, project.port):
            QMessageBox.warning(
                self,
                "Port Already In Use",
                f"Port {project.port} is already in use.\n\n"
                f"Project: {project.name}\n"
                f"Host: {project.host}\n"
                f"Port: {project.port}",
            )
            return

        label = "Laravel" if project_type == "laravel" else "PHP"
        self.log(f"[{project.name}] PHP: {php_executable}")
        self.log(f"[{project.name}] Working directory: {project_path}")
        self.log(
            f"[{project.name}] Starting {label} server on "
            f"{project.host}:{project.port}"
        )

        process = self._build_process(project, project_path)

        self.processes[project.name] = process
        self.project_logs[project.name] = ""
        self.browser_opened.discard(project.name)

        project.status = "Starting"
        self.refresh_table()

        if os.name == "nt":
            bat_script = build_php_activation_script(
                project_path,
                php_executable,
                project.host,
                project.port,
                project_type,
            )
            self.log(f"[{project.name}] Launch script: {bat_script}")
            if bat_script:
                process.start("cmd.exe", ["/d", "/s", "/c", bat_script])
                return

        # POSIX
        if project_type == "laravel":
            artisan = project_path / "artisan"
            process.start(
                php_executable,
                [str(artisan), "serve", f"--host={project.host}", f"--port={project.port}"],
            )
        else:
            process.start(
                php_executable,
                ["-S", f"{project.host}:{project.port}", "-t", str(project_path)],
            )

        if not process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            self.log(f"[{project.name}] Failed to start {label} server.")

            error = process.errorString()
            if error:
                self.log(f"[{project.name}] {error}")

            project.status = "Error"
            self.processes.pop(project.name, None)
            self.refresh_table()

    # ----------------------------------------------------------------
    # Shared QProcess factory
    # ----------------------------------------------------------------

    def _build_process(self, project, project_path):
        """Create and wire up a QProcess for the given project."""
        process = QProcess(self)
        process.setWorkingDirectory(str(project_path))

        environment = process.processEnvironment()
        clean_env = build_process_environment(project_path, os.environ)

        for key, value in clean_env.items():
            environment.insert(key, str(value))

        process.setProcessEnvironment(environment)

        process.started.connect(lambda p=project: self.process_started(p))

        process.readyReadStandardOutput.connect(
            lambda p=project: self.read_stdout(p)
        )
        process.readyReadStandardError.connect(
            lambda p=project: self.read_stderr(p)
        )

        process.errorOccurred.connect(
            lambda error, p=project: self.process_error(p, error)
        )

        process.finished.connect(
            lambda exit_code, exit_status, p=project, proc=process: (
                self.process_finished(p, proc, exit_code, exit_status)
            )
        )

        return process

    # ================================================================
    # PROCESS LIFECYCLE CALLBACKS
    # ================================================================

    def process_started(self, project):
        project.status = "Starting"
        self.refresh_table()

        process = self.processes.get(project.name)
        if process:
            self.log(f"[{project.name}] Process started. PID: {process.processId()}")

    def read_stdout(self, project):
        process = self.processes.get(project.name)
        if not process:
            return

        data = process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")

        if text:
            self.handle_process_output(project, text)

    def read_stderr(self, project):
        process = self.processes.get(project.name)
        if not process:
            return

        data = process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")

        if text:
            self.handle_process_output(project, text)

    def _ready_messages_for(self, project) -> list:
        """Return the list of ready-indicator strings for this project type."""
        project_type = getattr(project, "project_type", "django")
        if project_type == "laravel":
            return LARAVEL_READY_MESSAGES
        if project_type == "php":
            return PHP_READY_MESSAGES
        return SERVER_READY_MESSAGES

    def handle_process_output(self, project, text):
        self.project_logs[project.name] = (
            self.project_logs.get(project.name, "") + text
        )
        project.last_log = text

        for line in text.splitlines():
            if line.strip():
                self.log(f"[{project.name}] {line}")

        ready_messages = self._ready_messages_for(project)
        if any(message in text for message in ready_messages):
            self.mark_project_running(project)

    def mark_project_running(self, project):
        if project.status == "Running":
            return

        project.status = "Running"
        self.refresh_table()
        self.log(f"[{project.name}] Server is running.")

        if project.auto_open_browser and project.name not in self.browser_opened:
            self.browser_opened.add(project.name)
            QTimer.singleShot(300, lambda p=project: self.open_project(p))

    def process_error(self, project, error):
        # Ignore errors caused by intentional termination (restart in
        # progress); process_finished will handle the state transition.
        if project.name in self.pending_restarts:
            return

        process = self.processes.get(project.name)
        error_message = process.errorString() if process else ""

        self.log(f"[{project.name}] Process error: {error_message or error}")

        project.status = "Error"
        self.refresh_table()

    def process_finished(self, project, process, exit_code, exit_status):
        current_process = self.processes.get(project.name)

        if current_process is process:
            self.processes.pop(project.name, None)

        if project.name in self.pending_restarts:
            self.pending_restarts.discard(project.name)

            project.status = "Starting"
            self.refresh_table()

            self.log(
                f"[{project.name}] Old server stopped. Starting new server..."
            )

            QTimer.singleShot(500, lambda p=project: self.start_project(p))
            return

        project.status = "Stopped"
        self.refresh_table()
        self.log(f"[{project.name}] Server stopped. Exit code: {exit_code}")

    # ================================================================
    # PORT MONITOR (called on a timer by the main window)
    # ================================================================

    def check_running_projects(self):
        for project in self.projects:
            process = self.processes.get(project.name)

            if not process:
                continue

            if process.state() == QProcess.NotRunning:
                continue

            if project.status == "Starting":
                if not is_port_available(project.host, project.port):
                    self.mark_project_running(project)

    # ================================================================
    # STOP
    # ================================================================

    def stop_selected(self):
        project = self.get_selected_project()
        if project:
            self.stop_project(project)

    def stop_project(self, project):
        process = self.processes.get(project.name)

        if not process:
            project.status = "Stopped"
            self.refresh_table()
            return

        pid = process.processId()
        self.log(f"[{project.name}] Stopping process tree (PID {pid})...")

        if pid:
            kill_process_tree(pid, log=self.log)

        process.waitForFinished(3000)

        if self.processes.get(project.name) is process:
            self.processes.pop(project.name, None)

        project.status = "Stopped"
        self.browser_opened.discard(project.name)

        self.refresh_table()
        self.log(f"[{project.name}] Server stopped.")

    # ================================================================
    # RESTART
    # ================================================================

    def restart_selected(self):
        project = self.get_selected_project()
        if project:
            self.restart_project(project)

    def restart_project(self, project):
        process = self.processes.get(project.name)

        if not process:
            self.start_project(project)
            return

        self.log(f"[{project.name}] Restart requested.")
        self.pending_restarts.add(project.name)

        pid = process.processId()

        if pid:
            kill_process_tree(pid, log=self.log)
        else:
            process.kill()

    # ================================================================
    # OPEN BROWSER
    # ================================================================

    def open_selected(self):
        project = self.get_selected_project()
        if project:
            self.open_project(project)

    def open_project(self, project):
        url = f"http://{project.host}:{project.port}"
        webbrowser.open(url)
        self.log(f"[{project.name}] Opened {url}")
