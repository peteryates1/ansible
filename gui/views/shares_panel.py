from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QHeaderView, QPushButton,
    QLabel, QMessageBox, QFileDialog,
)

from gui.models.share_model import ShareMatrixModel
from gui.services.share_service import ShareService
from gui.services.playbook_service import PlaybookService
from gui.views.dialogs.operation_dialog import OperationDialog


class SharesPanel(QWidget):
    def __init__(self, libvirt_service, parent=None):
        super().__init__(parent)
        self._libvirt = libvirt_service
        self._share_service = ShareService(libvirt_service)
        self._refreshing = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Shares Matrix — check to attach, uncheck to detach (config only)")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        layout.addWidget(header)

        self._model = ShareMatrixModel()
        self._model.check_toggled.connect(self._on_check_toggled)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._add_dir_btn = QPushButton("Add Directory...")
        self._add_dir_btn.clicked.connect(self._on_add_directory)
        btn_layout.addWidget(self._add_dir_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(self._refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    @Slot()
    def refresh(self):
        try:
            vms = self._libvirt.list_vms()
            vm_names = [v['name'] for v in vms]
            host_dirs = self._share_service.discover_host_dirs(vm_names)
            matrix = self._share_service.get_share_matrix(vm_names, host_dirs)
            # Suppress toggle handler during data reset
            self._refreshing = True
            self._model.set_data(host_dirs, vm_names, matrix)
            self._refreshing = False
        except Exception as e:
            self._refreshing = False
            QMessageBox.warning(self, "Refresh Error", str(e))

    @Slot(str, str, bool)
    def _on_check_toggled(self, host_dir, vm_name, checked):
        if self._refreshing:
            return
        if checked:
            self._attach_share(host_dir, vm_name)
        else:
            self._detach_share(host_dir, vm_name)

    def _attach_share(self, host_dir, vm_name):
        worker = PlaybookService.run_share_dir(vm_name, host_dir)
        dialog = OperationDialog(
            f"Attaching {host_dir} to {vm_name}", worker, self
        )
        dialog.exec()
        self.refresh()

    def _detach_share(self, host_dir, vm_name):
        try:
            self._share_service.detach_share(vm_name, host_dir)
            QMessageBox.information(
                self, "Share Detached",
                f"Detached {host_dir} from {vm_name} config.\n"
                "VM restart required for changes to take effect."
            )
        except Exception as e:
            QMessageBox.warning(self, "Detach Failed", str(e))
        self.refresh()

    @Slot()
    def _on_add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Host Directory to Share", "/opt"
        )
        if dir_path:
            self._share_service.add_custom_dir(dir_path)
            self.refresh()
