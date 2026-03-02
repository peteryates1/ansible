import subprocess

from gui.workers.base_worker import BaseWorker
from gui.constants import PROJECT_DIR


class ChainedPlaybookWorker(BaseWorker):
    """Runs multiple playbook tasks sequentially in a single QThread."""

    def __init__(self, tasks, parent=None):
        """
        tasks: list of (playbook_name, extra_vars_dict) tuples
        """
        super().__init__(parent)
        self._tasks = tasks

    def run(self):
        for i, (playbook, extra_vars) in enumerate(self._tasks, 1):
            if self._cancelled:
                self.finished_signal.emit(-1, "Cancelled")
                return

            vm_name = extra_vars.get('vm_name', '')
            self.output_line.emit(
                f"\n--- [{i}/{len(self._tasks)}] {vm_name} ---\n"
            )

            cmd = ['sudo', 'ansible-playbook', f'playbooks/{playbook}.yml']
            for key, value in extra_vars.items():
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
                if rc != 0:
                    self.finished_signal.emit(
                        rc, f"Failed on {vm_name} (exit code {rc})"
                    )
                    return
            except Exception as e:
                self.finished_signal.emit(-1, str(e))
                return

        self.finished_signal.emit(0, "Success")
