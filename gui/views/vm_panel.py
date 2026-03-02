from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableView, QHeaderView, QPushButton, QGroupBox,
    QLabel, QMessageBox, QAbstractItemView,
)

from gui.models.vm_model import VMTableModel
from gui.services.libvirt_service import LibvirtService
from gui.constants import REFRESH_INTERVAL_MS, SOFTWARE_REGISTRY, VM_USER


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
        self._vm_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._vm_table.setAlternatingRowColors(True)
        self._vm_table.verticalHeader().setVisible(False)
        self._vm_table.horizontalHeader().setStretchLastSection(True)
        self._vm_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._vm_table.selectionModel().currentRowChanged.connect(
            self._on_vm_selected
        )
        self._vm_table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
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

        # Bottom: Detail pane (Shares + Software for selected VM)
        self._detail_widget = QWidget()
        detail_layout = QHBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)

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

        # Software group
        software_group = QGroupBox("Software")
        software_layout = QVBoxLayout(software_group)
        self._software_table = QTableView()
        self._software_table.setAlternatingRowColors(True)
        self._software_table.verticalHeader().setVisible(False)
        self._software_table.horizontalHeader().setStretchLastSection(True)
        self._software_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._software_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._software_detail_model = None
        software_layout.addWidget(self._software_table)

        self._install_btn = QPushButton("Install Selected")
        self._install_btn.setEnabled(False)
        self._install_btn.clicked.connect(self._on_install_software)
        software_layout.addWidget(self._install_btn)

        detail_layout.addWidget(software_group)

        # Software state tracking
        self._software_cache = {}  # {vm_name: {key: status}}
        self._detect_worker = None
        self._last_vm_states = {}  # {vm_name: state} for transition detection

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

        # Invalidate software cache on state transitions to running
        new_states = {vm['name']: vm['state'] for vm in vms}
        for name, state in new_states.items():
            old_state = self._last_vm_states.get(name)
            if state == 'running' and old_state and old_state != 'running':
                self._software_cache.pop(name, None)
        self._last_vm_states = new_states

        # Preserve selection (current + all selected)
        current_name = self._vm_model.get_vm_name(
            self._vm_table.currentIndex().row()
        )
        selected_names = set()
        for idx in self._vm_table.selectionModel().selectedRows():
            name = self._vm_model.get_vm_name(idx.row())
            if name:
                selected_names.add(name)

        self._vm_model.set_vms(vms)

        # Restore selection
        name_to_row = {vm['name']: i for i, vm in enumerate(vms)}
        sel_model = self._vm_table.selectionModel()
        for name in selected_names:
            if name in name_to_row:
                row_idx = self._vm_model.index(name_to_row[name], 0)
                sel_model.select(
                    row_idx,
                    sel_model.SelectionFlag.Select | sel_model.SelectionFlag.Rows,
                )
        if current_name and current_name in name_to_row:
            row_idx = self._vm_model.index(name_to_row[current_name], 0)
            sel_model.setCurrentIndex(row_idx, sel_model.SelectionFlag.NoUpdate)

    def _selected_vm(self):
        """Return the current (last-clicked) VM for the detail pane."""
        row = self._vm_table.currentIndex().row()
        return self._vm_model.get_vm(row)

    def _selected_vms(self):
        """Return list of all selected VM dicts."""
        vms = []
        for idx in self._vm_table.selectionModel().selectedRows():
            vm = self._vm_model.get_vm(idx.row())
            if vm:
                vms.append(vm)
        return vms

    @Slot()
    def _on_selection_changed(self):
        """Update button states based on all selected VMs."""
        vms = self._selected_vms()
        if not vms:
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._ssh_btn.setEnabled(False)
            return
        self._start_btn.setEnabled(any(v['state'] != 'running' for v in vms))
        self._stop_btn.setEnabled(any(v['state'] == 'running' for v in vms))
        # SSH is single-VM only — based on current row
        vm = self._selected_vm()
        if vm:
            self._ssh_btn.setEnabled(
                vm['state'] == 'running' and bool(vm.get('ip'))
            )

    @Slot()
    def _on_vm_selected(self):
        """Current row changed — update detail pane for last-clicked VM."""
        vm = self._selected_vm()
        if vm is None:
            self._detail_widget.setVisible(False)
            return

        self._detail_widget.setVisible(True)
        self._refresh_detail(vm['name'])

    def _refresh_detail(self, vm_name):
        # Refresh shares
        try:
            shares = self._libvirt.get_vm_shares(vm_name)
            self._show_shares_detail(shares)
        except Exception:
            pass

        # Refresh software
        self._refresh_software_detail(vm_name)

    def _show_shares_detail(self, shares):
        from gui.models.vm_detail_models import ShareDetailModel
        self._shares_detail_model = ShareDetailModel(shares)
        self._shares_table.setModel(self._shares_detail_model)
        self._shares_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

    def _refresh_software_detail(self, vm_name):
        vm = self._selected_vm()
        if vm is None:
            return

        if vm_name in self._software_cache:
            self._show_software_detail(self._software_cache[vm_name])
            return

        if vm['state'] != 'running' or not vm.get('ip'):
            # Not running or no IP — show dashes
            results = {e['key']: '-' for e in SOFTWARE_REGISTRY}
            self._show_software_detail(results)
            return

        # Start background detection if not already running for this VM
        if self._detect_worker is not None and self._detect_worker.isRunning():
            return

        self._start_software_detection(vm_name, vm['ip'])

    def _start_software_detection(self, vm_name, vm_ip):
        if self._detect_worker is not None and self._detect_worker.isRunning():
            self._detect_worker.cancel()
            self._detect_worker.wait(2000)

        # Show "checking..." placeholder
        results = {e['key']: 'checking...' for e in SOFTWARE_REGISTRY}
        self._show_software_detail(results)

        from gui.workers.software_detect_worker import SoftwareDetectWorker
        self._detect_worker = SoftwareDetectWorker(vm_name, vm_ip, parent=self)
        self._detect_worker.detection_complete.connect(self._on_detection_complete)
        self._detect_worker.start()

    @Slot(str, dict)
    def _on_detection_complete(self, vm_name, results):
        self._software_cache[vm_name] = results
        # Update UI if this VM is still selected
        vm = self._selected_vm()
        if vm and vm['name'] == vm_name:
            self._show_software_detail(results)

    def _show_software_detail(self, results):
        # Skip rebuild if the model already shows the same data
        if self._software_detail_model is not None:
            same = all(
                self._software_detail_model.get_item(i)
                and self._software_detail_model.get_item(i)['status']
                == results.get(SOFTWARE_REGISTRY[i]['key'], '-')
                for i in range(len(SOFTWARE_REGISTRY))
            )
            if same:
                return

        from gui.models.vm_detail_models import SoftwareDetailModel
        selected_row = self._software_table.currentIndex().row()
        items = []
        for entry in SOFTWARE_REGISTRY:
            items.append({
                'key': entry['key'],
                'label': entry['label'],
                'playbook': entry['playbook'],
                'status': results.get(entry['key'], '-'),
            })
        self._software_detail_model = SoftwareDetailModel(items)
        self._software_table.setModel(self._software_detail_model)
        self._software_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        # Restore software row selection
        if 0 <= selected_row < len(items):
            self._software_table.selectRow(selected_row)
        has_installable = any(
            i['status'] == 'not installed' for i in items
        )
        self._install_btn.setEnabled(has_installable)

    @Slot()
    def _on_start(self):
        vms = [v for v in self._selected_vms() if v['state'] != 'running']
        if not vms:
            return
        started = []
        for vm in vms:
            try:
                self._libvirt.start_vm(vm['name'])
                started.append(vm['name'])
            except Exception as e:
                QMessageBox.warning(
                    self, "Start Failed", f"{vm['name']}: {e}"
                )
        if started:
            names = ', '.join(started)
            self.window().statusBar().showMessage(
                f"Starting {names}...", 3000
            )
        self.refresh()

    @Slot()
    def _on_stop(self):
        vms = [v for v in self._selected_vms() if v['state'] == 'running']
        if not vms:
            return
        names = ', '.join(v['name'] for v in vms)
        count = len(vms)
        msg = f"Shut down {names}?" if count <= 3 else f"Shut down {count} VMs?"
        reply = QMessageBox.question(
            self, "Stop VM", msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            stopped = []
            for vm in vms:
                try:
                    self._libvirt.stop_vm(vm['name'])
                    stopped.append(vm['name'])
                except Exception as e:
                    QMessageBox.warning(
                        self, "Stop Failed", f"{vm['name']}: {e}"
                    )
            if stopped:
                self.window().statusBar().showMessage(
                    f"Shutting down {', '.join(stopped)}...", 3000
                )
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
            f"{VM_USER}@{vm['ip']}",
        ])

    @Slot()
    def _on_install_software(self):
        idx = self._software_table.currentIndex()
        if not idx.isValid() or self._software_detail_model is None:
            QMessageBox.information(
                self, "Install Software", "Select a software item first."
            )
            return
        item = self._software_detail_model.get_item(idx.row())
        if item is None or item['status'] != 'not installed':
            QMessageBox.information(
                self, "Install Software",
                "Select a software item that is not installed."
            )
            return

        # Collect all selected VMs that are running and have an IP
        target_vms = [
            v for v in self._selected_vms()
            if v['state'] == 'running' and v.get('ip')
        ]
        if not target_vms:
            QMessageBox.information(
                self, "Install Software",
                "No selected VMs are running with an IP address."
            )
            return

        from gui.services.playbook_service import PlaybookService
        from gui.views.dialogs.operation_dialog import OperationDialog

        vm_names = [v['name'] for v in target_vms]
        if len(vm_names) == 1:
            worker = PlaybookService.run_install(item['playbook'], vm_names[0])
        else:
            worker = PlaybookService.run_install_batch(
                item['playbook'], vm_names
            )

        label = item['label']
        title = (
            f"Installing {label} on {vm_names[0]}"
            if len(vm_names) == 1
            else f"Installing {label} on {len(vm_names)} VMs"
        )
        dlg = OperationDialog(title, worker, parent=self)
        dlg.exec()

        if dlg.success:
            # Invalidate cache and re-probe for all target VMs
            for name in vm_names:
                self._software_cache.pop(name, None)
            current = self._selected_vm()
            if current:
                self._refresh_software_detail(current['name'])
