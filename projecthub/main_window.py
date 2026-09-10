"""The ProjectHub main window.

Behaviour is composed from three mixins so each concern stays in its
own file:

  - UIBuilderMixin        builds the static widgets (table, log, buttons)
  - ProjectManagerMixin   add/edit/remove projects, table refresh
  - ServerManagerMixin    start/stop/restart Django dev servers
"""

from PySide6.QtCore import QProcess, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from .config import APP_NAME, ICON_FILE, PORT_POLL_INTERVAL_MS
from .process_utils import kill_process_tree
from .project_manager_mixin import ProjectManagerMixin
from .server_manager_mixin import ServerManagerMixin
from .ui_builder import UIBuilderMixin


class ProjectHub(QMainWindow, UIBuilderMixin, ProjectManagerMixin, ServerManagerMixin):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1150, 750)

        if ICON_FILE.exists():
            self.setWindowIcon(QIcon(str(ICON_FILE)))

        # ------------------------------------------------------------
        # Data
        # ------------------------------------------------------------

        self.projects = []          # list[Project]
        self.processes = {}         # project name -> QProcess
        self.project_logs = {}      # project name -> accumulated log text
        self.browser_opened = set()  # project names that already auto-opened
        self.pending_restarts = set()  # project names mid-restart
        self.project_cards = []     # project home-page cards

        self.load_projects()
        self.build_ui()
        self.refresh_table()
        self.refresh_home_page()
        self.stack.setCurrentWidget(self.home_page)

        # ------------------------------------------------------------
        # Server polling timer
        # ------------------------------------------------------------

        self.port_timer = QTimer(self)
        self.port_timer.setInterval(PORT_POLL_INTERVAL_MS)
        self.port_timer.timeout.connect(self.check_running_projects)
        self.port_timer.start()

    def show_home_page(self):
        self.stack.setCurrentWidget(self.home_page)

    def show_manager_page(self, project=None):
        self.stack.setCurrentWidget(self.manager_page)

        if project is None or not hasattr(project, "name"):
            return

        for row, item in enumerate(self.projects):
            if item.name == project.name:
                self.table.setCurrentCell(row, 0)
                break

    # ====================================================================
    # LOG
    # ====================================================================

    def log(self, message: str):
        self.log_output.appendPlainText(message)

        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ====================================================================
    # CLOSE APPLICATION
    # ====================================================================

    def closeEvent(self, event):
        if self.port_timer:
            self.port_timer.stop()

        running_processes = list(self.processes.items())

        if running_processes:
            self.log("[ProjectHub] Stopping all Django servers...")

        for project_name, process in running_processes:
            if process.state() == QProcess.NotRunning:
                continue

            pid = process.processId()
            self.log(f"[{project_name}] Killing process tree (PID {pid})...")

            if pid:
                kill_process_tree(pid, log=self.log)

        for project_name, process in running_processes:
            if process.state() != QProcess.NotRunning:
                process.waitForFinished(2000)

        self.processes.clear()
        self.pending_restarts.clear()

        for project in self.projects:
            project.status = "Stopped"

        self.save_projects()

        self.log("[ProjectHub] All servers stopped.")
        event.accept()
