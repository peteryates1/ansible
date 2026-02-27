from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor

COLUMNS = ['ID', 'Name', 'Serial', 'Assigned To', 'Mode']
COL_ID, COL_NAME, COL_SERIAL, COL_ASSIGNED, COL_MODE = range(5)


class USBTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices = []

    def set_devices(self, devices):
        self.beginResetModel()
        self._devices = devices
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._devices)

    def columnCount(self, parent=None):
        return len(COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        dev = self._devices[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == COL_ID:
                return dev.usb_id
            if col == COL_NAME:
                return dev.display_name
            if col == COL_SERIAL:
                return dev.serial or '-'
            if col == COL_ASSIGNED:
                return dev.assigned_vm or '-'
            if col == COL_MODE:
                return dev.assignment_mode or '-'
        if role == Qt.ForegroundRole:
            if dev.assigned_vm:
                return QColor('#888888')
        if role == Qt.BackgroundRole:
            if dev.assigned_vm:
                return QColor('#f5f5f5')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return COLUMNS[section]
        return None

    def get_device(self, row):
        if 0 <= row < len(self._devices):
            return self._devices[row]
        return None
