from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QStatusBar, QButtonGroup,
)

from gui.services.libvirt_service import LibvirtService
from gui.views.vm_panel import VMPanel


class MainWindow(QMainWindow):
    def __init__(self, libvirt_service):
        super().__init__()
        self._libvirt = libvirt_service
        self.setWindowTitle("VM Manager")
        self.resize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(90)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        self._stack = QStackedWidget()

        # VM panel
        self._vm_panel = VMPanel(self._libvirt)
        vm_btn = self._make_nav_button("VMs", 0)
        self._stack.addWidget(self._vm_panel)

        # Shares panel (placeholder, will be replaced in Phase 3)
        self._shares_panel = None
        shares_btn = self._make_nav_button("Shares", 1)

        # USB panel (placeholder, will be replaced in Phase 4)
        self._usb_panel = None
        usb_btn = self._make_nav_button("USB", 2)

        sidebar_layout.addWidget(vm_btn)
        sidebar_layout.addWidget(shares_btn)
        sidebar_layout.addWidget(usb_btn)
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self._stack, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        # Select VMs panel by default
        vm_btn.setChecked(True)

    def _make_nav_button(self, text, index):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setMinimumHeight(40)
        self._nav_group.addButton(btn, index)
        btn.clicked.connect(lambda: self._switch_panel(index))
        return btn

    def _switch_panel(self, index):
        # Lazy-load panels
        if index == 1 and self._shares_panel is None:
            from gui.views.shares_panel import SharesPanel
            self._shares_panel = SharesPanel(self._libvirt)
            self._stack.addWidget(self._shares_panel)
        if index == 2 and self._usb_panel is None:
            from gui.views.usb_panel import USBPanel
            self._usb_panel = USBPanel(self._libvirt)
            self._stack.addWidget(self._usb_panel)

        if index == 0:
            self._stack.setCurrentWidget(self._vm_panel)
        elif index == 1 and self._shares_panel:
            self._stack.setCurrentWidget(self._shares_panel)
            self._shares_panel.refresh()
        elif index == 2 and self._usb_panel:
            self._stack.setCurrentWidget(self._usb_panel)
            self._usb_panel.refresh()

    def closeEvent(self, event):
        self._libvirt.close()
        super().closeEvent(event)
