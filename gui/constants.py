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
    {'key': 'create_user', 'label': 'Create VM User', 'playbook': 'create-vm-user', 'detect_cmd': None, 'needs_user': True},
    {'key': 'gh', 'label': 'GitHub CLI', 'playbook': 'install-gh', 'detect_cmd': 'which gh', 'needs_user': False},
    {'key': 'code', 'label': 'VS Code', 'playbook': 'install-vscode', 'detect_cmd': 'which code', 'needs_user': False},
    {'key': 'codium', 'label': 'VSCodium', 'playbook': 'install-codium', 'detect_cmd': 'which codium', 'needs_user': False},
    {'key': 'claude', 'label': 'Claude Code', 'playbook': 'install-claude', 'detect_cmd': 'which claude', 'needs_user': True},
    {'key': 'opencode', 'label': 'OpenCode', 'playbook': 'install-opencode', 'detect_cmd': 'which opencode', 'needs_user': True},
    {'key': 'spinalhdl', 'label': 'SpinalHDL', 'playbook': 'install-spinalhdl', 'detect_cmd': 'which sbt', 'needs_user': False},
    {'key': 'blaster', 'label': 'USB Blaster', 'playbook': 'install-blaster', 'detect_cmd': 'test -f /etc/udev/rules.d/51-usb-blaster.rules', 'needs_user': False},
    {'key': 'alchitry', 'label': 'Alchitry AU', 'playbook': 'install-alchitry', 'detect_cmd': 'test -f /etc/udev/rules.d/99-alchitry.rules', 'needs_user': False},
]

TARGET_USER_CHOICES = list(dict.fromkeys([VM_USER, 'claude', 'opencode']))
