import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYBOOKS_DIR = os.path.join(PROJECT_DIR, 'playbooks')
VM_SCRIPT = os.path.join(PROJECT_DIR, 'vm')

LIBVIRT_URI = 'qemu:///system'
VM_USER = os.environ.get('SUDO_USER') or os.environ.get('USER', 'peter')

REFRESH_INTERVAL_MS = 3000

STATE_COLORS = {
    'running': '#4CAF50',
    'shut off': '#9E9E9E',
    'paused': '#FF9800',
    'crashed': '#F44336',
    'blocked': '#FF9800',
    'shutdown': '#FFC107',
    'pmsuspended': '#9C27B0',
}

STATE_NAMES = {
    0: 'no state',
    1: 'running',
    2: 'blocked',
    3: 'paused',
    4: 'shutdown',
    5: 'shut off',
    6: 'crashed',
    7: 'pmsuspended',
}

SHARE_DISCOVERY_PATHS = ['/opt', '/srv/git']

UDEV_RULES_DIR = '/etc/udev/rules.d'
UDEV_RULE_PREFIX = '90-vm-usb-'

SOFTWARE_REGISTRY = [
    {'key': 'gh', 'label': 'GitHub CLI', 'playbook': 'install-gh', 'detect_cmd': 'which gh'},
    {'key': 'code', 'label': 'VS Code', 'playbook': 'install-vscode', 'detect_cmd': 'which code'},
    {'key': 'codium', 'label': 'VSCodium', 'playbook': 'install-codium', 'detect_cmd': 'which codium'},
    {'key': 'claude', 'label': 'Claude Code', 'playbook': 'install-claude', 'detect_cmd': 'which claude'},
    {'key': 'opencode', 'label': 'OpenCode', 'playbook': 'install-opencode', 'detect_cmd': 'which opencode'},
    {'key': 'spinalhdl', 'label': 'SpinalHDL', 'playbook': 'install-spinalhdl', 'detect_cmd': 'which sbt'},
    {'key': 'blaster', 'label': 'USB Blaster', 'playbook': 'install-blaster', 'detect_cmd': 'test -f /etc/udev/rules.d/51-usb-blaster.rules'},
    {'key': 'alchitry', 'label': 'Alchitry AU', 'playbook': 'install-alchitry', 'detect_cmd': 'test -f /etc/udev/rules.d/99-alchitry.rules'},
]
