from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QRadioButton, QButtonGroup,
    QPushButton, QLabel, QGroupBox,
)


class USBAssignDialog(QDialog):
    def __init__(self, devices, vm_names, parent=None):
        super().__init__(parent)
        self._devices = devices if isinstance(devices, list) else [devices]

        if len(self._devices) == 1:
            dev = self._devices[0]
            self.setWindowTitle(f"Assign {dev.usb_id} - {dev.display_name}")
        else:
            self.setWindowTitle(f"Assign {len(self._devices)} USB devices")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Device info
        if len(self._devices) == 1:
            dev = self._devices[0]
            info_text = (
                f"<b>Device:</b> {dev.usb_id} - {dev.display_name}"
                f"{'<br><b>Serial:</b> ' + dev.serial if dev.serial else ''}"
            )
        else:
            lines = []
            for dev in self._devices:
                lines.append(f"{dev.usb_id} - {dev.display_name}")
            info_text = f"<b>Devices ({len(self._devices)}):</b><br>" + "<br>".join(lines)
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # VM selection
        form = QFormLayout()
        self._vm_combo = QComboBox()
        for name in vm_names:
            self._vm_combo.addItem(name)
        form.addRow("Target VM:", self._vm_combo)
        layout.addLayout(form)

        # Mode selection
        mode_group = QGroupBox("Assignment Mode")
        mode_layout = QVBoxLayout(mode_group)
        self._mode_group = QButtonGroup(self)

        self._auto_radio = QRadioButton(
            "Auto-passthrough (persistent udev rule)"
        )
        self._onetime_radio = QRadioButton(
            "One-time (live attach only, lost on unplug/reboot)"
        )
        self._auto_radio.setChecked(True)
        self._mode_group.addButton(self._auto_radio, 0)
        self._mode_group.addButton(self._onetime_radio, 1)
        mode_layout.addWidget(self._auto_radio)
        mode_layout.addWidget(self._onetime_radio)
        layout.addWidget(mode_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Assign")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    @property
    def selected_vm(self):
        return self._vm_combo.currentText()

    @property
    def is_auto(self):
        return self._auto_radio.isChecked()
