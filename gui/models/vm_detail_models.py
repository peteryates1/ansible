from PySide6.QtCore import Qt, QAbstractTableModel


class USBDetailModel(QAbstractTableModel):
    COLUMNS = ['ID', 'Addressing', 'Bus', 'Device']

    def __init__(self, devices, vm_name, parent=None):
        super().__init__(parent)
        self._devices = devices
        self._vm_name = vm_name

    def rowCount(self, parent=None):
        return len(self._devices)

    def columnCount(self, parent=None):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        dev = self._devices[index.row()]
        col = index.column()
        if col == 0:
            if dev.get('addressing') == 'vendor':
                return f"{dev['vendor_id']}:{dev['product_id']}"
            return ''
        if col == 1:
            return dev.get('addressing', '')
        if col == 2:
            return dev.get('bus', '')
        if col == 3:
            return dev.get('device', '')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def get_device(self, row):
        if 0 <= row < len(self._devices):
            return self._devices[row]
        return None


class ShareDetailModel(QAbstractTableModel):
    COLUMNS = ['Host Directory', 'Mount Tag', 'Type']

    def __init__(self, shares, parent=None):
        super().__init__(parent)
        self._shares = shares

    def rowCount(self, parent=None):
        return len(self._shares)

    def columnCount(self, parent=None):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        share = self._shares[index.row()]
        col = index.column()
        if col == 0:
            return share.get('host_dir', '')
        if col == 1:
            return share.get('mount_tag', '')
        if col == 2:
            return share.get('fs_type', '')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None
