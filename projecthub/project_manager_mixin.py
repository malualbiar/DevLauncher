"""Adding, editing, removing projects, and keeping the table in sync.

This mixin owns everything about *which* projects exist and how they
are displayed; starting/stopping their servers lives in
server_manager_mixin.ServerManagerMixin.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QMenu,
)
from PySide6.QtGui import QAction

from . import storage
from .dialogs import ProjectDialog


class ProjectManagerMixin:
    # ================================================================
    # ADD PROJECT
    # ================================================================

    def add_project(self):
        dialog = ProjectDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        project = dialog.get_project()
        new_path = Path(project.path).resolve()

        for existing in self.projects:
            try:
                existing_path = Path(existing.path).resolve()
            except Exception:
                continue

            if existing_path == new_path:
                QMessageBox.warning(
                    self,
                    "Duplicate Project",
                    "This project has already been added.",
                )
                return

        for existing in self.projects:
            if existing.name.lower() == project.name.lower():
                QMessageBox.warning(
                    self,
                    "Duplicate Project Name",
                    "A project with this name already exists.",
                )
                return

        self.projects.append(project)
        self.save_projects()
        self.refresh_table()
        self.log(f"[ProjectHub] Added project: {project.name}")

    # ================================================================
    # EDIT PROJECT
    # ================================================================

    def edit_selected(self):
        project = self.get_selected_project()
        if project:
            self.edit_project(project)

    def edit_project(self, project):
        if project.name in self.processes:
            QMessageBox.warning(
                self,
                "Project Running",
                "Stop the project before editing it.",
            )
            return

        dialog = ProjectDialog(self, project)

        if dialog.exec() != QDialog.Accepted:
            return

        new_project = dialog.get_project()

        for existing in self.projects:
            if existing is project:
                continue
            if existing.name.lower() == new_project.name.lower():
                QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    "Another project already uses this name.",
                )
                return

        new_path = Path(new_project.path).resolve()

        for existing in self.projects:
            if existing is project:
                continue
            try:
                existing_path = Path(existing.path).resolve()
            except Exception:
                continue
            if existing_path == new_path:
                QMessageBox.warning(
                    self,
                    "Duplicate Project",
                    "Another project already uses this folder.",
                )
                return

        new_project.status = "Stopped"
        new_project.last_log = project.last_log

        index = self.projects.index(project)
        self.projects[index] = new_project

        self.project_logs[new_project.name] = self.project_logs.pop(
            project.name, ""
        )

        self.save_projects()
        self.refresh_table()
        self.log(f"[ProjectHub] Updated project: {new_project.name}")

    # ================================================================
    # REMOVE PROJECT
    # ================================================================

    def remove_selected(self):
        project = self.get_selected_project()
        if project:
            self.remove_project(project)

    def remove_project(self, project):
        if project.name in self.processes:
            QMessageBox.warning(
                self,
                "Project Running",
                "Stop the project before removing it.",
            )
            return

        answer = QMessageBox.question(
            self, "Remove Project", f"Remove '{project.name}' from ProjectHub?"
        )

        if answer != QMessageBox.Yes:
            return

        self.projects.remove(project)
        self.project_logs.pop(project.name, None)
        self.browser_opened.discard(project.name)

        self.save_projects()
        self.refresh_table()
        self.log(f"[ProjectHub] Removed project: {project.name}")

    # ================================================================
    # STORAGE (thin wrappers around the storage module)
    # ================================================================

    def save_projects(self):
        storage.save_projects(self.projects, log=self.log)

    def load_projects(self):
        self.projects = storage.load_projects(log=print)

    # ================================================================
    # TABLE
    # ================================================================

    def refresh_table(self):
        self.table.setRowCount(0)

        for row, project in enumerate(self.projects):
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(project.name))

            path_item = QTableWidgetItem(project.path)
            path_item.setToolTip(project.path)
            self.table.setItem(row, 1, path_item)

            project_type = getattr(project, "project_type", "django")
            type_labels = {"django": "Django", "laravel": "Laravel", "php": "PHP"}
            self.table.setItem(row, 2, QTableWidgetItem(type_labels.get(project_type, project_type.capitalize())))

            self.table.setItem(row, 3, QTableWidgetItem(str(project.port)))
            self.table.setItem(row, 4, QTableWidgetItem(project.status))

            url = f"http://{project.host}:{project.port}"
            self.table.setItem(row, 5, QTableWidgetItem(url))

            self.table.setCellWidget(row, 6, self._build_row_actions(project))

        if hasattr(self, "refresh_home_page"):
            self.refresh_home_page()

        self.update_button_states()

    def _build_row_actions(self, project):
        actions_widget = QWidget()
        actions_widget.setFixedWidth(160)
        actions_widget.setStyleSheet("QWidget { background: transparent; }")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(6, 4, 6, 4)
        actions_layout.setSpacing(6)

        run_button = QPushButton("Run")
        stop_button = QPushButton("Stop")

        for button in (run_button, stop_button):
            button.setFixedSize(64, 28)
            button.setStyleSheet(
                "QPushButton { background: #1d2737; color: #e5e7eb; border: 1px solid #3a4b63; border-radius: 6px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background: #243149; }"
                "QPushButton:disabled { background: #1b2433; color: #60708e; border: 1px solid #2b3b53; }"
            )

        run_button.clicked.connect(
            lambda checked=False, p=project: self.start_project(p)
        )
        stop_button.clicked.connect(
            lambda checked=False, p=project: self.stop_project(p)
        )

        run_button.setEnabled(project.name not in self.processes)
        stop_button.setEnabled(project.name in self.processes)

        actions_layout.addWidget(run_button)
        actions_layout.addWidget(stop_button)

        return actions_widget

    # ================================================================
    # SELECTED PROJECT
    # ================================================================

    def get_selected_project(self):
        row = self.table.currentRow()

        if row < 0 or row >= len(self.projects):
            return None

        return self.projects[row]

    # ================================================================
    # CONTEXT MENU
    # ================================================================

    def show_context_menu(self, position):
        project = self.get_selected_project()
        if not project:
            return

        menu = QMenu(self)

        run_action = QAction("Run", self)
        stop_action = QAction("Stop", self)
        restart_action = QAction("Restart", self)
        browser_action = QAction("Open Browser", self)
        edit_action = QAction("Edit", self)
        remove_action = QAction("Remove", self)

        run_action.triggered.connect(lambda: self.start_project(project))
        stop_action.triggered.connect(lambda: self.stop_project(project))
        restart_action.triggered.connect(lambda: self.restart_project(project))
        browser_action.triggered.connect(lambda: self.open_project(project))
        edit_action.triggered.connect(lambda: self.edit_project(project))
        remove_action.triggered.connect(lambda: self.remove_project(project))

        is_running = project.name in self.processes

        run_action.setEnabled(not is_running)
        stop_action.setEnabled(is_running)
        edit_action.setEnabled(not is_running)
        remove_action.setEnabled(not is_running)

        menu.addAction(run_action)
        menu.addAction(stop_action)
        menu.addAction(restart_action)
        menu.addSeparator()
        menu.addAction(browser_action)
        menu.addSeparator()
        menu.addAction(edit_action)
        menu.addAction(remove_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    # ================================================================
    # DOUBLE CLICK / LOG VIEW
    # ================================================================

    def table_double_click(self, index):
        project = self.get_selected_project()
        if project:
            self.show_project_log(project)

    def show_project_log(self, project):
        self.log_output.clear()

        log = self.project_logs.get(project.name, "")

        if log:
            self.log_output.setPlainText(log)
        else:
            self.log_output.setPlainText(f"No logs available for {project.name}.")

    # ================================================================
    # BUTTON STATES
    # ================================================================

    def update_button_states(self):
        project = self.get_selected_project()
        has_project = project is not None
        is_running = has_project and project.name in self.processes

        self.start_button.setEnabled(has_project and not is_running)
        self.stop_button.setEnabled(is_running)
        self.restart_button.setEnabled(has_project)
        self.open_button.setEnabled(has_project)
        self.edit_button.setEnabled(has_project and not is_running)
        self.remove_button.setEnabled(has_project and not is_running)
