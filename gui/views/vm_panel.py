from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableView, QHeaderView, QPushButton, QGroupBox,
    QLabel, QMessageBox, QAbstractItemView,
)

from gui.models.vm_model import VMTableModel
from gui.services.libvirt_service import LibvirtService
from gui.constants import REFRESH_INTERVAL_MS


class VMPanel(QWidget):
    def __init__(self, libvirt_service, parent=None):
        super().__init__(parent)
        self._libvirt = libvirt_service
        self._setup_ui()
        self._start_refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)

        # Top: VM table with buttons
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self._vm_model = VMTableModel()
        self._vm_table = QTableView()
        self._vm_table.setModel(self._vm_model)
        self._vm_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._vm_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._vm_table.setAlternatingRowColors(True)
        self._vm_table.verticalHeader().setVisible(False)
        self._vm_table.horizontalHeader().setStretchLastSection(True)
        self._vm_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._vm_table.selectionModel().currentRowChanged.connect(
            self._on_vm_selected
        )
        top_layout.addWidget(self._vm_table)

        # Buttons
        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton("Start")
        self._stop_btn = QPushButton("Stop")
        self._ssh_btn = QPushButton("SSH")
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._ssh_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn.clicked.connect(self._on_stop)
        self._ssh_btn.clicked.connect(self._on_ssh)
        btn_layout.addWidget(self._start_btn)
        btn_layout.addWidget(self._stop_btn)
        btn_layout.addWidget(self._ssh_btn)
        btn_layout.addStretch()
        top_layout.addLayout(btn_layout)

        splitter.addWidget(top_widget)

        # Bottom: Detail pane (USB + Shares for selected VM)
        self._detail_widget = QWidget()
        detail_layout = QHBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        # USB devices group
        usb_group = QGroupBox("Assigned USB Devices")
        usb_layout = QVBoxLayout(usb_group)
        self._usb_table = QTableView()
        self._usb_table.setAlternatingRowColors(True)
        self._usb_table.verticalHeader().setVisible(False)
        self._usb_table.horizontalHeader().setStretchLastSection(True)
        self._usb_detail_model = None
        usb_layout.addWidget(self._usb_table)

        self._usb_detach_btn = QPushButton("Detach Selected")
        self._usb_detach_btn.setEnabled(False)
        self._usb_detach_btn.clicked.connect(self._on_detach_usb)
        usb_layout.addWidget(self._usb_detach_btn)

        detail_layout.addWidget(usb_group)

        # Shares group
        shares_group = QGroupBox("Assigned Shares")
        shares_layout = QVBoxLayout(shares_group)
        self._shares_table = QTableView()
        self._shares_table.setAlternatingRowColors(True)
        self._shares_table.verticalHeader().setVisible(False)
        self._shares_table.horizontalHeader().setStretchLastSection(True)
        self._shares_detail_model = None
        shares_layout.addWidget(self._shares_table)
        detail_layout.addWidget(shares_group)

        self._detail_widget.setVisible(False)
        splitter.addWidget(self._detail_widget)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _start_refresh(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(REFRESH_INTERVAL_MS)
        self.refresh()

    @Slot()
    def refresh(self):
        try:
            vms = self._libvirt.list_vms()
        except Exception as e:
            self.window().statusBar().showMessage(f"libvirt error: {e}", 5000)
            return

        # Preserve selection
        selected_row = self._vm_table.currentIndex().row()
        selected_name = self._vm_model.get_vm_name(selected_row)

        self._vm_model.set_vms(vms)

        # Restore selection
        if selected_name:
            for i, vm in enumerate(vms):
                if vm['name'] == selected_name:
                    self._vm_table.selectRow(i)
                    break

    def _selected_vm(self):
        row = self._vm_table.currentIndex().row()
        return self._vm_model.get_vm(row)

    @Slot()
    def _on_vm_selected(self):
        vm = self._selected_vm()
        if vm is None:
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._ssh_btn.setEnabled(False)
            self._detail_widget.setVisible(False)
            return

        is_running = vm['state'] == 'running'
        self._start_btn.setEnabled(not is_running)
        self._stop_btn.setEnabled(is_running)
        self._ssh_btn.setEnabled(is_running and bool(vm.get('ip')))
        self._detail_widget.setVisible(True)
        self._refresh_detail(vm['name'])

    def _refresh_detail(self, vm_name):
        # Refresh USB devices
        try:
            usb_devices = self._libvirt.get_vm_usb_devices(vm_name)
            self._show_usb_detail(usb_devices, vm_name)
        except Exception:
            pass

        # Refresh shares
        try:
            shares = self._libvirt.get_vm_shares(vm_name)
            self._show_shares_detail(shares)
        except Exception:
            pass

    def _show_usb_detail(self, devices, vm_name):
        from gui.models.vm_detail_models import USBDetailModel
        self._usb_detail_model = USBDetailModel(devices, vm_name)
        self._usb_table.setModel(self._usb_detail_model)
        self._usb_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._usb_detach_btn.setEnabled(len(devices) > 0)

    def _show_shares_detail(self, shares):
        from gui.models.vm_detail_models import ShareDetailModel
        self._shares_detail_model = ShareDetailModel(shares)
        self._shares_table.setModel(self._shares_detail_model)
        self._shares_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

    @Slot()
    def _on_start(self):
        vm = self._selected_vm()
        if vm is None:
            return
        try:
            self._libvirt.start_vm(vm['name'])
            self.window().statusBar().showMessage(
                f"Starting {vm['name']}...", 3000
            )
        except Exception as e:
            QMessageBox.warning(self, "Start Failed", str(e))
        self.refresh()

    @Slot()
    def _on_stop(self):
        vm = self._selected_vm()
        if vm is None:
            return
        reply = QMessageBox.question(
            self, "Stop VM",
            f"Shut down {vm['name']}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self._libvirt.stop_vm(vm['name'])
                self.window().statusBar().showMessage(
                    f"Shutting down {vm['name']}...", 3000
                )
            except Exception as e:
                QMessageBox.warning(self, "Stop Failed", str(e))
            self.refresh()

    @Slot()
    def _on_ssh(self):
        vm = self._selected_vm()
        if vm is None or not vm.get('ip'):
            return
        import subprocess
        subprocess.Popen([
            'x-terminal-emulator', '-e',
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f"peter@{vm['ip']}",
        ])

    @Slot()
    def _on_detach_usb(self):
        vm = self._selected_vm()
        if vm is None:
            return
        idx = self._usb_table.currentIndex()
        if not idx.isValid() or self._usb_detail_model is None:
            QMessageBox.information(self, "Detach USB", "Select a USB device first.")
            return
        device = self._usb_detail_model.get_device(idx.row())
        if device is None:
            return

        # Build XML for detach
        if device.get('addressing') == 'vendor':
            xml = (
                "<hostdev mode='subsystem' type='usb' managed='yes'>\n"
                "  <source>\n"
                f"    <vendor id='0x{device['vendor_id']}'/>\n"
                f"    <product id='0x{device['product_id']}'/>\n"
                "  </source>\n"
                "</hostdev>"
            )
        else:
            xml = (
                "<hostdev mode='subsystem' type='usb' managed='yes'>\n"
                "  <source>\n"
                f"    <address bus='{device['bus']}' device='{device['device']}'/>\n"
                "  </source>\n"
                "</hostdev>"
            )

        try:
            self._libvirt.detach_usb_device(vm['name'], xml)
            self.window().statusBar().showMessage(
                f"Detached USB device from {vm['name']}", 3000
            )
        except Exception as e:
            QMessageBox.warning(self, "Detach Failed", str(e))
        self._refresh_detail(vm['name'])
