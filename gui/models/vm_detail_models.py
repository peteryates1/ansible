from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor


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


STATUS_COLORS = {
    'installed': QColor('#4CAF50'),
    'not installed': QColor('#9E9E9E'),
    'checking...': QColor('#FF9800'),
    '-': QColor('#9E9E9E'),
}


class SoftwareDetailModel(QAbstractTableModel):
    COLUMNS = ['Software', 'Status']

    def __init__(self, items, parent=None):
        super().__init__(parent)
        self._items = items  # list of dicts: key, label, playbook, status

    def rowCount(self, parent=None):
        return len(self._items)

    def columnCount(self, parent=None):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return item.get('label', '')
            if col == 1:
                return item.get('status', '-')
        if role == Qt.ForegroundRole and col == 1:
            return STATUS_COLORS.get(item.get('status', '-'), QColor('#9E9E9E'))
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def get_item(self, row):
        if 0 <= row < len(self._items):
            return self._items[row]
        return None
