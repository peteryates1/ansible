from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    output_line = Signal(str)
    finished_signal = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
