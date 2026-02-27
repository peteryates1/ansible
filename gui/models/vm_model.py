from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor

from gui.constants import STATE_COLORS

COLUMNS = ['Name', 'State', 'IP', 'Memory (MiB)', 'vCPUs']
COLUMN_KEYS = ['name', 'state', 'ip', 'memory', 'vcpus']


class VMTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._vms = []

    def set_vms(self, vms):
        self.beginResetModel()
        self._vms = vms
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._vms)

    def columnCount(self, parent=None):
        return len(COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        vm = self._vms[index.row()]
        col = index.column()
        key = COLUMN_KEYS[col]

        if role == Qt.DisplayRole:
            return str(vm.get(key, ''))
        if role == Qt.ForegroundRole and key == 'state':
            color = STATE_COLORS.get(vm.get('state', ''))
            if color:
                return QColor(color)
        if role == Qt.FontRole and key == 'state':
            from PySide6.QtGui import QFont
            font = QFont()
            font.setBold(True)
            return font
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return COLUMNS[section]
        return None

    def get_vm_name(self, row):
        if 0 <= row < len(self._vms):
            return self._vms[row]['name']
        return None

    def get_vm(self, row):
        if 0 <= row < len(self._vms):
            return self._vms[row]
        return None
