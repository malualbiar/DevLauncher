"""Dialog for adding or editing a project entry (Django, Laravel, PHP)."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QMessageBox,
)

from .config import DEFAULT_HOST, DEFAULT_PORT
from .models import Project, PROJECT_TYPES
from .process_utils import detect_project_type


# Human-readable labels shown in the combo box.
_TYPE_LABELS = {
    "django":  "Django (Python)",
    "laravel": "Laravel (PHP)",
    "php":     "PHP (built-in server)",
}

# Default ports per project type.
_TYPE_DEFAULT_PORTS = {
    "django":  8000,
    "laravel": 8000,
    "php":     8000,
}


class ProjectDialog(QDialog):
    """Collects/edits the fields needed to describe a project."""

    def __init__(self, parent=None, project: Project = None):
        super().__init__(parent)

        self.project = project

        self.setWindowTitle("Edit Project" if project else "Add Project")
        self.setMinimumWidth(600)

        self._build_ui()

        if project:
            self._load_project(project)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Project name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My Project")
        form.addRow("Project Name:", self.name_input)

        # Project folder
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(r"C:\Users\You\Projects\MyProject")

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_project)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        form.addRow("Project Folder:", path_layout)

        # Project type
        self.type_combo = QComboBox()
        for key in PROJECT_TYPES:
            self.type_combo.addItem(_TYPE_LABELS.get(key, key), userData=key)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Project Type:", self.type_combo)

        # Host
        self.host_input = QLineEdit(DEFAULT_HOST)
        form.addRow("Host:", self.host_input)

        # Port
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(DEFAULT_PORT)
        form.addRow("Port:", self.port_input)

        # Browser
        self.browser_checkbox = QCheckBox(
            "Open browser automatically when server starts"
        )
        self.browser_checkbox.setChecked(True)
        form.addRow("", self.browser_checkbox)

        layout.addLayout(form)

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save Project")
        save_button.clicked.connect(self._validate_and_accept)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    def _on_type_changed(self, _index: int):
        """Update the default port when the project type changes."""
        project_type = self.type_combo.currentData()
        current_port = self.port_input.value()
        # Only reset the port if it still looks like a default value
        if current_port in _TYPE_DEFAULT_PORTS.values():
            self.port_input.setValue(
                _TYPE_DEFAULT_PORTS.get(project_type, DEFAULT_PORT)
            )

    def _browse_project(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Project Folder"
        )

        if not folder:
            return

        self.path_input.setText(folder)

        if not self.name_input.text().strip():
            self.name_input.setText(Path(folder).name)

        # Auto-detect the project type and update the combo box.
        detected = detect_project_type(folder)
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == detected:
                self.type_combo.setCurrentIndex(i)
                break

    def _load_project(self, project: Project):
        self.name_input.setText(project.name)
        self.path_input.setText(project.path)
        self.host_input.setText(project.host)
        self.port_input.setValue(project.port)
        self.browser_checkbox.setChecked(project.auto_open_browser)

        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == project.project_type:
                self.type_combo.setCurrentIndex(i)
                break

    def _validate_and_accept(self):
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        host = self.host_input.text().strip()
        project_type = self.type_combo.currentData()

        if not name:
            QMessageBox.warning(
                self, "Invalid Project", "Please enter a project name."
            )
            return

        if not path:
            QMessageBox.warning(
                self, "Invalid Project", "Please select a project folder."
            )
            return

        project_path = Path(path)

        if not project_path.exists():
            QMessageBox.warning(
                self, "Invalid Project", "The selected folder does not exist."
            )
            return

        # Type-specific validation
        if project_type == "django":
            if not (project_path / "manage.py").exists():
                QMessageBox.warning(
                    self,
                    "Not a Django Project",
                    "The selected folder does not contain manage.py.",
                )
                return

        elif project_type == "laravel":
            if not (project_path / "artisan").exists():
                QMessageBox.warning(
                    self,
                    "Not a Laravel Project",
                    "The selected folder does not contain an artisan file.\n\n"
                    "Make sure you selected the Laravel project root.",
                )
                return

        # For plain PHP we just require at least one .php file.
        elif project_type == "php":
            if not any(project_path.rglob("*.php")):
                QMessageBox.warning(
                    self,
                    "No PHP Files Found",
                    "The selected folder does not contain any PHP files.",
                )
                return

        if not host:
            QMessageBox.warning(self, "Invalid Host", "Please enter a host.")
            return

        self.accept()

    def get_project(self) -> Project:
        return Project(
            name=self.name_input.text().strip(),
            path=self.path_input.text().strip(),
            host=self.host_input.text().strip(),
            port=self.port_input.value(),
            auto_open_browser=self.browser_checkbox.isChecked(),
            project_type=self.type_combo.currentData(),
        )
