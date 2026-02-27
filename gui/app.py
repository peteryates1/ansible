import sys

from PySide6.QtWidgets import QApplication

from gui.services.libvirt_service import LibvirtService
from gui.views.main_window import MainWindow

STYLESHEET = """
* {
    font-size: 15px;
}
QPushButton[checkable="true"] {
    text-align: center;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #f0f0f0;
}
QPushButton[checkable="true"]:checked {
    background: #4a90d9;
    color: white;
    border-color: #3a7bc8;
}
QTableView {
    font-size: 14px;
}
QTableView::item {
    padding: 3px;
}
QTableView::item:selected {
    background: #4a90d9;
    color: white;
}
QHeaderView::section {
    font-size: 14px;
}
QGroupBox {
    font-weight: bold;
    font-size: 15px;
    padding-top: 18px;
}
"""


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("VM Manager")
    app.setStyleSheet(STYLESHEET)

    libvirt_service = LibvirtService()
    try:
        libvirt_service.connect()
    except Exception as e:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None, "Connection Error",
            f"Cannot connect to libvirt:\n{e}\n\n"
            "Make sure libvirtd is running and you have permission."
        )
        sys.exit(1)

    window = MainWindow(libvirt_service)
    window.show()
    sys.exit(app.exec())
