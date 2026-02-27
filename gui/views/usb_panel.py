from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QHeaderView, QPushButton,
    QLabel, QMessageBox, QAbstractItemView,
)

from gui.models.usb_model import USBTableModel
from gui.services.usb_service import USBService
from gui.services.playbook_service import PlaybookService
from gui.views.dialogs.usb_assign_dialog import USBAssignDialog
from gui.views.dialogs.operation_dialog import OperationDialog


class USBPanel(QWidget):
    def __init__(self, libvirt_service, parent=None):
        super().__init__(parent)
        self._libvirt = libvirt_service
        self._usb_service = USBService(libvirt_service)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Host USB Devices — assigned devices shown greyed out")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        layout.addWidget(header)

        self._model = USBTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
        layout.addWidget(self._table)

        # Action buttons
        btn_layout = QHBoxLayout()

        self._assign_btn = QPushButton("Assign")
        self._assign_btn.setEnabled(False)
        self._assign_btn.clicked.connect(self._on_assign)
        btn_layout.addWidget(self._assign_btn)

        self._reassign_btn = QPushButton("Reassign")
        self._reassign_btn.setEnabled(False)
        self._reassign_btn.clicked.connect(self._on_reassign)
        btn_layout.addWidget(self._reassign_btn)

        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._on_remove)
        btn_layout.addWidget(self._remove_btn)

        btn_layout.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(self._refresh_btn)

        layout.addLayout(btn_layout)

    @Slot()
    def refresh(self):
        try:
            devices = self._usb_service.list_host_devices()
            self._model.set_devices(devices)
        except Exception as e:
            self.window().statusBar().showMessage(f"USB error: {e}", 5000)

    def _selected_devices(self):
        rows = sorted({idx.row() for idx in self._table.selectionModel().selectedRows()})
        return [self._model.get_device(r) for r in rows if self._model.get_device(r)]

    @Slot()
    def _on_selection_changed(self):
        devices = self._selected_devices()
        if not devices:
            self._assign_btn.setEnabled(False)
            self._reassign_btn.setEnabled(False)
            self._remove_btn.setEnabled(False)
            return
        any_unassigned = any(not d.assigned_vm for d in devices)
        any_assigned = any(d.assigned_vm for d in devices)
        self._assign_btn.setEnabled(any_unassigned)
        self._reassign_btn.setEnabled(any_assigned)
        self._remove_btn.setEnabled(any_assigned)

    def _usb_name_for(self, dev):
        if dev.has_duplicate_id and dev.display_name != 'USB Device':
            return dev.display_name
        return None

    def _run_op(self, title, worker):
        dialog = OperationDialog(title, worker, self)
        dialog.exec()
        return dialog.success

    @Slot()
    def _on_assign(self):
        devices = [d for d in self._selected_devices() if not d.assigned_vm]
        if not devices:
            return
        self._do_assign(devices)

    @Slot()
    def _on_reassign(self):
        devices = [d for d in self._selected_devices() if d.assigned_vm]
        if not devices:
            return

        # Ask where to reassign first
        try:
            vm_names = [v['name'] for v in self._libvirt.list_vms()]
        except Exception:
            vm_names = []

        dialog = USBAssignDialog(devices, vm_names, self)
        if dialog.exec() != USBAssignDialog.Accepted:
            return

        new_vm = dialog.selected_vm
        is_auto = dialog.is_auto

        # For each device: detach from old VM, remove auto rule, assign to new VM
        for dev in devices:
            # 1. Detach from current VM via libvirt directly
            self._detach_device(dev)

            # 2. Remove auto rule if it was auto
            if dev.assignment_mode == 'auto':
                self._run_op(
                    f"Removing auto rule for {dev.usb_id}",
                    PlaybookService.run_usb_auto_remove(dev.assigned_vm, dev.usb_id)
                )

            # 3. Assign to new VM
            name = self._usb_name_for(dev)
            if is_auto:
                self._run_op(
                    f"Auto-passthrough {dev.usb_id} to {new_vm}",
                    PlaybookService.run_usb_auto(new_vm, dev.usb_id, name)
                )
            else:
                self._run_op(
                    f"Attaching {dev.usb_id} to {new_vm}",
                    PlaybookService.run_usb_attach(new_vm, dev.usb_id, name)
                )

        self.refresh()

    @Slot()
    def _on_remove(self):
        devices = [d for d in self._selected_devices() if d.assigned_vm]
        if not devices:
            return
        names = "\n".join(f"  {d.usb_id} ({d.display_name}) from {d.assigned_vm}" for d in devices)
        reply = QMessageBox.question(
            self, "Remove Assignment",
            f"Remove {len(devices)} assignment(s)?\n\n{names}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        for dev in devices:
            # Detach live device via libvirt directly
            self._detach_device(dev)
            # Then remove auto rule if applicable
            if dev.assignment_mode == 'auto':
                self._run_op(
                    f"Removing auto rule for {dev.usb_id}",
                    PlaybookService.run_usb_auto_remove(dev.assigned_vm, dev.usb_id)
                )

        self.refresh()

    def _detach_device(self, dev):
        """Detach USB device from its assigned VM using libvirt directly."""
        if not dev.assigned_vm:
            return
        try:
            ok = self._libvirt.find_and_detach_usb(
                dev.assigned_vm, dev.vendor_id, dev.product_id
            )
            if ok:
                self.window().statusBar().showMessage(
                    f"Detached {dev.usb_id} from {dev.assigned_vm}", 3000
                )
            else:
                QMessageBox.warning(
                    self, "Detach",
                    f"Device {dev.usb_id} not found in {dev.assigned_vm} XML"
                )
        except Exception as e:
            QMessageBox.warning(self, "Detach Failed", str(e))

    def _do_assign(self, devices):
        try:
            vm_names = [v['name'] for v in self._libvirt.list_vms()]
        except Exception:
            vm_names = []

        dialog = USBAssignDialog(devices, vm_names, self)
        if dialog.exec() != USBAssignDialog.Accepted:
            return

        vm_name = dialog.selected_vm
        for dev in devices:
            name = self._usb_name_for(dev)
            if dialog.is_auto:
                self._run_op(
                    f"Auto-passthrough {dev.usb_id} to {vm_name}",
                    PlaybookService.run_usb_auto(vm_name, dev.usb_id, name)
                )
            else:
                self._run_op(
                    f"Attaching {dev.usb_id} to {vm_name}",
                    PlaybookService.run_usb_attach(vm_name, dev.usb_id, name)
                )
        self.refresh()
