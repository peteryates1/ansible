import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYBOOKS_DIR = os.path.join(PROJECT_DIR, 'playbooks')
VM_SCRIPT = os.path.join(PROJECT_DIR, 'vm')

LIBVIRT_URI = 'qemu:///system'

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
