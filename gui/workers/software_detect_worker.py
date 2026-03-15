import subprocess

from PySide6.QtCore import Signal

from gui.workers.base_worker import BaseWorker
from gui.constants import SOFTWARE_REGISTRY, VM_USER


class SoftwareDetectWorker(BaseWorker):
    detection_complete = Signal(str, dict)  # vm_name, {key: status}

    def __init__(self, vm_name, vm_ip, parent=None):
        super().__init__(parent)
        self._vm_name = vm_name
        self._vm_ip = vm_ip

    def run(self):
        # Build a compound command: each detect_cmd prints key=yes or key=no
        parts = []
        for entry in SOFTWARE_REGISTRY:
            if entry.get('detect_cmd') is None:
                continue
            key = entry['key']
            cmd = entry['detect_cmd']
            parts.append(f'({cmd}) >/dev/null 2>&1 && echo {key}=yes || echo {key}=no')
        compound = '; '.join(parts)

        ssh_cmd = [
            'ssh',
            '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=5',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'{VM_USER}@{self._vm_ip}',
            compound,
        ]

        results = {}
        try:
            proc = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if self._cancelled:
                return
            if proc.returncode == 0:
                for line in proc.stdout.strip().splitlines():
                    if '=' in line:
                        key, val = line.split('=', 1)
                        results[key] = 'installed' if val == 'yes' else 'not installed'
            else:
                # SSH failed — mark all as unknown
                for entry in SOFTWARE_REGISTRY:
                    results[entry['key']] = '-'
        except (subprocess.TimeoutExpired, Exception):
            for entry in SOFTWARE_REGISTRY:
                results[entry['key']] = '-'

        if not self._cancelled:
            self.detection_complete.emit(self._vm_name, results)
