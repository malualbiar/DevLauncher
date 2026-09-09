"""Builds the static widgets of the main window.

Kept separate from behaviour (project_manager_mixin / server_manager_mixin)
so the visual layout can be changed without touching business logic.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QHeaderView,
    QPlainTextEdit,
    QGroupBox,
)


class UIBuilderMixin:
    """Expects the host class to provide the callback methods referenced
    below (add_project, start_selected, stop_selected, etc.) and to set
    self.table / self.log_output / the control buttons as attributes."""

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        main_layout.addLayout(self._build_header())
        main_layout.addWidget(self._build_table())
        main_layout.addWidget(self._build_log_group())
        main_layout.addLayout(self._build_controls())

        self.update_button_states()

    # ------------------------------------------------------------
    # Header
    # ------------------------------------------------------------

    def _build_header(self):
        header = QHBoxLayout()
        title_layout = QVBoxLayout()

        title = QLabel(self.windowTitle() or "ProjectHub")
        title.setStyleSheet(
            "QLabel { font-size: 28px; font-weight: bold; }"
        )

        subtitle = QLabel("Django Development Server Manager")
        subtitle.setStyleSheet("QLabel { color: #777; font-size: 13px; }")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header.addLayout(title_layout)
        header.addStretch()

        add_button = QPushButton("+ Add Project")
        add_button.setMinimumHeight(38)
        add_button.clicked.connect(self.add_project)
        header.addWidget(add_button)

        return header

    # ------------------------------------------------------------
    # Project table
    # ------------------------------------------------------------

    def _build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Project", "Path", "Port", "Status", "URL", "Actions"]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.itemSelectionChanged.connect(self.update_button_states)
        self.table.doubleClicked.connect(self.table_double_click)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        return self.table

    # ------------------------------------------------------------
    # Log panel
    # ------------------------------------------------------------

    def _build_log_group(self):
        log_group = QGroupBox("Server Log")
        log_layout = QVBoxLayout(log_group)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(5000)

        log_layout.addWidget(self.log_output)
        return log_group

    # ------------------------------------------------------------
    # Bottom controls
    # ------------------------------------------------------------

    def _build_controls(self):
        controls = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")
        self.open_button = QPushButton("Open Browser")
        self.edit_button = QPushButton("Edit")
        self.remove_button = QPushButton("Remove")

        self.start_button.clicked.connect(self.start_selected)
        self.stop_button.clicked.connect(self.stop_selected)
        self.restart_button.clicked.connect(self.restart_selected)
        self.open_button.clicked.connect(self.open_selected)
        self.edit_button.clicked.connect(self.edit_selected)
        self.remove_button.clicked.connect(self.remove_selected)

        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.restart_button)
        controls.addWidget(self.open_button)
        controls.addStretch()
        controls.addWidget(self.edit_button)
        controls.addWidget(self.remove_button)

        return controls
