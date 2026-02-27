from PySide6.QtCore import Qt, QAbstractTableModel, Signal


class ShareMatrixModel(QAbstractTableModel):
    check_toggled = Signal(str, str, bool)  # host_dir, vm_name, checked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._host_dirs = []
        self._vm_names = []
        self._matrix = {}  # (host_dir, vm_name) -> bool

    def set_data(self, host_dirs, vm_names, matrix):
        self.beginResetModel()
        self._host_dirs = host_dirs
        self._vm_names = vm_names
        self._matrix = matrix
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._host_dirs)

    def columnCount(self, parent=None):
        return len(self._vm_names)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.CheckStateRole:
            host_dir = self._host_dirs[index.row()]
            vm_name = self._vm_names[index.column()]
            return Qt.Checked if self._matrix.get(
                (host_dir, vm_name), False
            ) else Qt.Unchecked
        return None

    def setData(self, index, value, role=Qt.CheckStateRole):
        if not index.isValid() or role != Qt.CheckStateRole:
            return False
        host_dir = self._host_dirs[index.row()]
        vm_name = self._vm_names[index.column()]
        checked = value == Qt.Checked.value
        self._matrix[(host_dir, vm_name)] = checked
        self.dataChanged.emit(index, index, [role])
        self.check_toggled.emit(host_dir, vm_name, checked)
        return True

    def flags(self, index):
        return (
            Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        )

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section < len(self._vm_names):
                return self._vm_names[section]
        elif orientation == Qt.Vertical:
            if section < len(self._host_dirs):
                return self._host_dirs[section]
        return None

    def get_host_dir(self, row):
        if 0 <= row < len(self._host_dirs):
            return self._host_dirs[row]
        return None

    def get_vm_name(self, col):
        if 0 <= col < len(self._vm_names):
            return self._vm_names[col]
        return None
