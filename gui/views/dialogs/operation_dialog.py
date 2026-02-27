from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel,
)
from PySide6.QtGui import QFont, QTextCursor


class OperationDialog(QDialog):
    def __init__(self, title, worker, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 450)
        self.setModal(True)

        self._worker = worker
        self._success = False

        layout = QVBoxLayout(self)

        self._status_label = QLabel("Running...")
        self._status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._status_label)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("monospace", 12))
        layout.addWidget(self._log)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._cancel_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

        # Connect worker signals
        self._worker.output_line.connect(self._on_output)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    @property
    def success(self):
        return self._success

    @Slot(str)
    def _on_output(self, line):
        self._log.moveCursor(QTextCursor.End)
        self._log.insertPlainText(line)
        self._log.moveCursor(QTextCursor.End)

    @Slot(int, str)
    def _on_finished(self, return_code, message):
        self._success = return_code == 0
        if return_code == 0:
            self._status_label.setText(f"Completed: {message}")
            self._status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #4CAF50;"
            )
        else:
            self._status_label.setText(f"Failed: {message}")
            self._status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #F44336;"
            )
        self._cancel_btn.setEnabled(False)
        self._close_btn.setEnabled(True)
        self._close_btn.setFocus()

    @Slot()
    def _on_cancel(self):
        self._worker.cancel()

    def closeEvent(self, event):
        if self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        super().closeEvent(event)
