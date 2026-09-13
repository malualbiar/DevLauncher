"""Builds the static widgets of the main window.

Kept separate from behaviour (project_manager_mixin / server_manager_mixin)
so the visual layout can be changed without touching business logic.
"""

import hashlib

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
    QStackedWidget,
    QScrollArea,
    QGridLayout,
    QSizePolicy,
)


class UIBuilderMixin:
    """Expects the host class to provide the callback methods referenced
    below (add_project, start_selected, stop_selected, etc.) and to set
    self.table / self.log_output / the control buttons as attributes."""

    def build_ui(self):
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #1E1E1E; }")
        self.setCentralWidget(self.stack)

        self.home_page = QWidget()
        self.home_page.setStyleSheet("QWidget { background: #1E1E1E; color: #edf3ff; }")
        self.manager_page = QWidget()
        self.manager_page.setStyleSheet("QWidget { background: #1E1E1E; color: #edf3ff; }")

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.manager_page)

        self._build_home_page()
        self._build_manager_page()

        self.update_button_states()

    def _build_home_page(self):
        home_layout = QVBoxLayout(self.home_page)
        home_layout.setContentsMargins(22, 20, 22, 20)
        home_layout.setSpacing(18)

        home_header = QHBoxLayout()
        title_layout = QVBoxLayout()

        title = QLabel(self.windowTitle() or "ProjectHub")
        title.setStyleSheet("QLabel { font-size: 30px; font-weight: bold; }")

        subtitle = QLabel("Choose a project to run, manage, or open")
        subtitle.setStyleSheet("QLabel { color: #7a7a7a; font-size: 13px; }")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        home_header.addLayout(title_layout)
        home_header.addStretch()

        add_button = QPushButton("+ Add Project")
        add_button.setMinimumHeight(42)
        add_button.setMinimumWidth(150)
        add_button.setStyleSheet(
            "QPushButton { background: #2d3748; color: #e5e7eb; border: 1px solid #44506a; border-radius: 10px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background: #37445c; }"
        )
        add_button.clicked.connect(self.add_project)
        home_header.addWidget(add_button)

        self.home_manage_button = QPushButton("Open Manager")
        self.home_manage_button.setMinimumHeight(42)
        self.home_manage_button.setMinimumWidth(150)
        self.home_manage_button.setStyleSheet(
            "QPushButton { background: #1d2737; color: #e5e7eb; border: 1px solid #3a4b63; border-radius: 10px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background: #243149; }"
        )
        self.home_manage_button.clicked.connect(self.show_manager_page)
        home_header.addWidget(self.home_manage_button)

        home_layout.addLayout(home_header)

        self.project_scroll = QScrollArea()
        self.project_scroll.setWidgetResizable(True)
        self.project_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        project_grid_container = QWidget()
        self.project_grid = QGridLayout(project_grid_container)
        self.project_grid.setSpacing(16)
        self.project_grid.setContentsMargins(0, 0, 0, 0)
        self.project_grid.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.project_scroll.setWidget(project_grid_container)
        home_layout.addWidget(self.project_scroll)

        self.project_cards = []

    def _build_manager_page(self):
        self.manager_page.setStyleSheet(
            "QWidget { background: #1E1E1E; color: #edf3ff; }"
        )

        manager_layout = QVBoxLayout(self.manager_page)
        manager_layout.setContentsMargins(18, 18, 18, 18)
        manager_layout.setSpacing(14)

        manager_layout.addLayout(self._build_header())
        manager_layout.addWidget(self._build_table())
        manager_layout.addWidget(self._build_log_group())
        manager_layout.addLayout(self._build_controls())

    # ------------------------------------------------------------
    # Header
    # ------------------------------------------------------------

    def _build_header(self):
        header = QHBoxLayout()
        title_layout = QVBoxLayout()

        title = QLabel(self.windowTitle() or "ProjectHub")
        title.setStyleSheet(
            "QLabel { font-size: 28px; font-weight: 700; color: #edf3ff; }"
        )

        subtitle = QLabel("Development Server Manager  ·  Django · Laravel · PHP")
        subtitle.setStyleSheet("QLabel { color: #8ea2c7; font-size: 13px; }")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header.addLayout(title_layout)
        header.addStretch()

        home_button = QPushButton("Home")
        home_button.setMinimumHeight(42)
        home_button.setMinimumWidth(150)
        home_button.setStyleSheet(
            "QPushButton { background: #1d2737; color: #e5e7eb; border: 1px solid #3a4b63; border-radius: 10px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background: #243149; }"
        )
        home_button.clicked.connect(self.show_home_page)
        header.addWidget(home_button)

        add_button = QPushButton("+ Add Project")
        add_button.setMinimumHeight(42)
        add_button.setMinimumWidth(150)
        add_button.setStyleSheet(
            "QPushButton { background: #2d3748; color: #e5e7eb; border: 1px solid #44506a; border-radius: 10px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background: #37445c; }"
        )
        add_button.clicked.connect(self.add_project)
        header.addWidget(add_button)

        remove_button = QPushButton("Remove")
        remove_button.setMinimumHeight(42)
        remove_button.setMinimumWidth(150)
        remove_button.setStyleSheet(
            "QPushButton { background: #3b1f1f; color: #f5d0d0; border: 1px solid #7a2d2d; border-radius: 10px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background: #512525; }"
            "QPushButton:disabled { background: #1f232a; color: #60708e; border: 1px solid #2d3744; }"
        )
        remove_button.clicked.connect(self.remove_selected)
        header.addWidget(remove_button)

        return header

    # ------------------------------------------------------------
    # Project table
    # ------------------------------------------------------------

    def _build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Project", "Path", "Type", "Port", "Status", "URL", "Actions"]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background: #111d2d;
                color: #edf3ff;
                border: 1px solid #2b3e58;
                border-radius: 10px;
                gridline-color: #24344d;
            }
            QHeaderView::section {
                background: #1a2940;
                color: #dfe7ff;
                border: none;
                padding: 8px;
                font-weight: 600;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background: #223b5c;
                color: white;
            }
            """
        )

        header_view = self.table.horizontalHeader()
        header_view.setMinimumSectionSize(10)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.Fixed)
        header_view.resizeSection(6, 160)

        self.table.verticalHeader().setDefaultSectionSize(42)
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
        log_group.setStyleSheet(
            "QGroupBox { color: #edf3ff; font-weight: 600; border: 1px solid #2b3e58; border-radius: 10px; margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }"
        )
        log_layout = QVBoxLayout(log_group)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(5000)
        self.log_output.setStyleSheet(
            "QPlainTextEdit { background: #0e1b2d; color: #dfe7ff; border: 1px solid #253952; border-radius: 8px; }"
        )

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

        for button in (
            self.start_button,
            self.stop_button,
            self.restart_button,
            self.open_button,
            self.edit_button,
            self.remove_button,
        ):
            button.setMinimumHeight(38)
            button.setStyleSheet(
                "QPushButton { background: #1d2737; color: #e5e7eb; border: 1px solid #3a4b63; border-radius: 10px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background: #243149; }"
                "QPushButton:disabled { background: #1b2433; color: #60708e; border: 1px solid #2b3b53; }"
            )

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

    def refresh_home_page(self):
        for card in self.project_cards:
            card.deleteLater()
        self.project_cards.clear()

        if not self.projects:
            empty_label = QLabel("No projects yet. Add your first project to begin.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(
                "QLabel { color: #7a7a7a; font-size: 16px; padding: 40px; }"
            )
            self.project_grid.addWidget(empty_label, 0, 0)
            return

        for index, project in enumerate(self.projects):
            card = self._build_project_card(project)
            self.project_cards.append(card)
            row, col = divmod(index, 4)
            self.project_grid.addWidget(card, row, col)

        self.project_grid.setColumnStretch(0, 1)
        self.project_grid.setColumnStretch(1, 1)
        self.project_grid.setColumnStretch(2, 1)
        self.project_grid.setColumnStretch(3, 1)

    def _project_type_badge(self, project):
        """Return a dict with 'text' and 'color' for the project type badge."""
        project_type = getattr(project, "project_type", "django")
        return {
            "django":  {"text": "Django",  "color": "#60a5fa"},
            "laravel": {"text": "Laravel", "color": "#f472b6"},
            "php":     {"text": "PHP",     "color": "#a78bfa"},
        }.get(project_type, {"text": project_type.capitalize(), "color": "#94a3b8"})

    def _project_status_color(self, project):
        return {
            "Running": "#34d399",
            "Starting": "#fbbf24",
            "Stopped": "#a8b3c7",
            "Error": "#f87171",
        }.get(project.status, "#a8b3c7")

    def _project_status_text(self, project):
        if project.status == "Running":
            return "● Running"
        if project.status == "Starting":
            return "● Starting"
        if project.status == "Error":
            return "● Error"
        return "● Idle"

    def _build_project_card(self, project):
        card = QPushButton()
        card.setObjectName("ProjectCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedSize(220, 142)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(
            """
            QPushButton#ProjectCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #121d2e);
                border: 1px solid #2b3e58;
                border-radius: 14px;
                text-align: left;
                padding: 10px;
            }
            QPushButton#ProjectCard:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #122033, stop:1 #172742);
                border: 1px solid #5476b9;
            }
            """
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(6)

        status_color = self._project_status_color(project)
        type_badge = self._project_type_badge(project)

        hash_value = hashlib.sha1(project.name.encode("utf-8")).hexdigest()

        accent_palette = [
            ("#4f46e5", "#7c3aed"),
            ("#0ea5e9", "#2563eb"),
            ("#10b981", "#059669"),
            ("#f59e0b", "#f97316"),
            ("#ef4444", "#dc2626"),
            ("#8b5cf6", "#6366f1"),
            ("#14b8a6", "#0ea5e9"),
            ("#f43f5e", "#ec4899"),
        ]
        gradient_start, gradient_end = accent_palette[int(hash_value[-1], 16) % len(accent_palette)]

        top_row = QHBoxLayout()
        name_label = QLabel(project.name)
        name_label.setStyleSheet(
            "QLabel { color: #edf3ff; font-size: 14px; font-weight: 700; }"
        )

        status_label = QLabel(self._project_status_text(project))
        status_label.setStyleSheet(
            f"QLabel {{ color: {status_color}; font-size: 10px; font-weight: 700; }}"
        )

        top_row.addWidget(name_label)
        top_row.addStretch()
        top_row.addWidget(status_label)

        text_col = QVBoxLayout()
        text_col.addWidget(name_label)
        badge_label = QLabel(type_badge["text"])
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_label.setStyleSheet(
            f"QLabel {{ color: {type_badge['color']}; font-size: 10px; font-weight: 600; background: transparent; }}"
        )
        text_col.addWidget(badge_label)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        toggle_button = QPushButton("Start" if project.name not in self.processes else "Stop")
        toggle_button.setFixedHeight(34)
        toggle_button.setMinimumWidth(92)
        toggle_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #22c55e, stop:1 #16a34a); color: white; border: none; border-radius: 10px; font-weight: 700; font-size: 12px; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34d399, stop:1 #22c55e); }"
            "QPushButton:disabled { background: #334155; color: #94a3b8; }"
        )

        def toggle_project_action(checked=False, current_project=project):
            if current_project.name in self.processes:
                self.stop_project(current_project)
            else:
                self.start_project(current_project)

        toggle_button.clicked.connect(toggle_project_action)

        open_button = QPushButton("Open")
        open_button.setFixedHeight(34)
        open_button.setMinimumWidth(92)
        open_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f5ef6, stop:1 #3b4fe0); color: white; border: none; border-radius: 10px; font-weight: 700; font-size: 12px; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5c6dff, stop:1 #4d5df0); }"
        )
        open_button.clicked.connect(lambda checked=False, p=project: self.open_project(p))

        actions.addWidget(toggle_button)
        actions.addStretch()
        actions.addWidget(open_button)

        card.clicked.connect(lambda checked=False, p=project: self.show_manager_page(p))
        card_layout.addLayout(top_row)
        card_layout.addLayout(text_col)
        card_layout.addStretch()
        card_layout.addLayout(actions)

        return card
