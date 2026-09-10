import os

from PySide6.QtWidgets import QApplication

from projecthub.main_window import ProjectHub
from projecthub.models import Project


def test_projecthub_starts_on_home_page():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    window = ProjectHub()

    assert hasattr(window, "home_page")
    assert hasattr(window, "stack")
    assert window.stack.currentWidget() is window.home_page
    assert hasattr(window, "project_grid")
    assert len(window.project_cards) == len(window.projects)

    window.close()


def test_project_status_mapping_matches_runtime_state():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    window = ProjectHub()

    assert window._project_status_text(Project("Demo", "C:/demo", status="Running")) == "● Running"
    assert window._project_status_text(Project("Demo", "C:/demo", status="Starting")) == "● Starting"
    assert window._project_status_text(Project("Demo", "C:/demo", status="Stopped")) == "● Idle"
    assert window._project_status_text(Project("Demo", "C:/demo", status="Error")) == "● Error"

    window.close()


def test_show_manager_page_ignores_clicked_bool_signal():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    window = ProjectHub()

    window.show_manager_page(True)

    assert window.stack.currentWidget() is window.manager_page

    window.close()
