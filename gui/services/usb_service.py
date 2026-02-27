import os
import re
import subprocess

from gui.constants import UDEV_RULES_DIR, UDEV_RULE_PREFIX


class USBDevice:
    def __init__(self, bus, device, vendor_id, product_id,
                 manufacturer='', product='', serial=''):
        self.bus = bus
        self.device = device
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.manufacturer = manufacturer
        self.product = product
        self.serial = serial
        self.assigned_vm = ''
        self.assignment_mode = ''  # 'auto', 'live', or ''

    @property
    def usb_id(self):
        return f"{self.vendor_id}:{self.product_id}"

    @property
    def display_name(self):
        parts = []
        if self.manufacturer and self.manufacturer != '-':
            parts.append(self.manufacturer)
        if self.product and self.product != '-':
            parts.append(self.product)
        return ' '.join(parts) or 'USB Device'

    # Set by USBService after listing all devices
    has_duplicate_id = False


class USBService:
    def __init__(self, libvirt_service):
        self._libvirt = libvirt_service

    def list_host_devices(self):
        devices = []
        try:
            result = subprocess.run(
                ['lsusb'], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return devices
        except Exception:
            return devices

        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            # Bus 001 Device 003: ID 2e8a:000a ...
            m = re.match(
                r'Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+'
                r'([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)',
                line
            )
            if not m:
                continue
            bus, device_num, vendor, product, desc = m.groups()
            dev = USBDevice(bus, device_num, vendor.lower(), product.lower())

            # Get detailed info
            dev_path = f"/dev/bus/usb/{bus}/{device_num}"
            self._enrich_device(dev, dev_path)
            devices.append(dev)

        # Mark devices with duplicate vendor:product IDs
        id_counts = {}
        for dev in devices:
            id_counts[dev.usb_id] = id_counts.get(dev.usb_id, 0) + 1
        for dev in devices:
            dev.has_duplicate_id = id_counts[dev.usb_id] > 1

        # Get assignments
        auto_rules = self._parse_auto_rules()
        live_assignments = self._get_live_assignments()

        for dev in devices:
            # Check auto rules first
            rule_key = (dev.vendor_id, dev.product_id, dev.serial)
            rule_key_no_serial = (dev.vendor_id, dev.product_id, '')
            if rule_key in auto_rules:
                dev.assigned_vm = auto_rules[rule_key]
                dev.assignment_mode = 'auto'
            elif rule_key_no_serial in auto_rules:
                dev.assigned_vm = auto_rules[rule_key_no_serial]
                dev.assignment_mode = 'auto'
            # Check live assignments
            elif (dev.vendor_id, dev.product_id) in live_assignments:
                dev.assigned_vm = live_assignments[
                    (dev.vendor_id, dev.product_id)
                ]
                dev.assignment_mode = 'live'

        return devices

    def _enrich_device(self, dev, dev_path):
        # Get manufacturer/product from lsusb -D
        try:
            result = subprocess.run(
                ['lsusb', '-D', dev_path],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    stripped = line.strip()
                    if stripped.startswith('iManufacturer'):
                        parts = stripped.split(None, 2)
                        if len(parts) >= 3:
                            dev.manufacturer = parts[2]
                    elif stripped.startswith('iProduct'):
                        parts = stripped.split(None, 2)
                        if len(parts) >= 3:
                            dev.product = parts[2]
        except Exception:
            pass

        # Get serial from udevadm
        try:
            result = subprocess.run(
                ['udevadm', 'info', '--query=property', '--name', dev_path],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith('ID_SERIAL_SHORT='):
                        dev.serial = line.split('=', 1)[1].strip()
                        break
        except Exception:
            pass

    def _parse_auto_rules(self):
        rules = {}
        if not os.path.isdir(UDEV_RULES_DIR):
            return rules
        for fname in os.listdir(UDEV_RULES_DIR):
            if not fname.startswith(UDEV_RULE_PREFIX) or not fname.endswith('.rules'):
                continue
            # 90-vm-usb-<vm>-<vvvvpppp>[-<serial>].rules
            base = fname[:-len('.rules')]
            suffix = base[len(UDEV_RULE_PREFIX):]

            # Try with serial: <vm>-<8hex>-<serial>
            m = re.match(r'^(.*)-([0-9a-f]{8})-(.+)$', suffix)
            if m:
                vm_name = m.group(1)
                devid = m.group(2)
                serial = m.group(3)
                vendor = devid[:4]
                product = devid[4:]
                rules[(vendor, product, serial)] = vm_name
                continue

            # Without serial: <vm>-<8hex>
            m = re.match(r'^(.*)-([0-9a-f]{8})$', suffix)
            if m:
                vm_name = m.group(1)
                devid = m.group(2)
                vendor = devid[:4]
                product = devid[4:]
                rules[(vendor, product, '')] = vm_name
        return rules

    def _get_live_assignments(self):
        assignments = {}
        try:
            vms = self._libvirt.list_vms()
            for vm in vms:
                if vm['state'] != 'running':
                    continue
                try:
                    usb_devs = self._libvirt.get_vm_usb_devices(vm['name'])
                    for dev in usb_devs:
                        if dev.get('addressing') == 'vendor':
                            key = (dev['vendor_id'], dev['product_id'])
                            assignments[key] = vm['name']
                except Exception:
                    pass
        except Exception:
            pass
        return assignments
