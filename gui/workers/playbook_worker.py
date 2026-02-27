import subprocess

from gui.workers.base_worker import BaseWorker
from gui.constants import PROJECT_DIR


class PlaybookWorker(BaseWorker):
    def __init__(self, playbook, extra_vars=None, parent=None):
        super().__init__(parent)
        self._playbook = playbook
        self._extra_vars = extra_vars or {}

    def run(self):
        cmd = ['sudo', 'ansible-playbook', f'playbooks/{self._playbook}.yml']
        for key, value in self._extra_vars.items():
            cmd.extend(['-e', f"{key}={value}"])

        self.output_line.emit(f"$ {' '.join(cmd)}\n")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=PROJECT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            while True:
                if self._cancelled:
                    proc.terminate()
                    self.output_line.emit("\n--- Cancelled ---\n")
                    self.finished_signal.emit(-1, "Cancelled")
                    return
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    self.output_line.emit(line)

            rc = proc.returncode
            if rc == 0:
                self.finished_signal.emit(0, "Success")
            else:
                self.finished_signal.emit(rc, f"Failed (exit code {rc})")
        except Exception as e:
            self.finished_signal.emit(-1, str(e))
