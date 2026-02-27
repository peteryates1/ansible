import xml.etree.ElementTree as ET

import libvirt

from gui.constants import LIBVIRT_URI, STATE_NAMES


class LibvirtService:
    def __init__(self):
        self._conn = None

    def connect(self):
        if self._conn is None:
            self._conn = libvirt.open(LIBVIRT_URI)
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def list_vms(self):
        conn = self.connect()
        vms = []
        for dom in conn.listAllDomains():
            info = dom.info()
            state_num = info[0]
            vms.append({
                'name': dom.name(),
                'state': STATE_NAMES.get(state_num, 'unknown'),
                'memory': info[2] // 1024,  # KiB -> MiB
                'vcpus': info[3],
                'ip': self._get_ip(dom) if state_num == 1 else '',
            })
        vms.sort(key=lambda v: v['name'])
        return vms

    def start_vm(self, name):
        conn = self.connect()
        dom = conn.lookupByName(name)
        dom.create()

    def stop_vm(self, name):
        conn = self.connect()
        dom = conn.lookupByName(name)
        dom.shutdown()

    def get_vm_shares(self, name):
        conn = self.connect()
        dom = conn.lookupByName(name)
        xml_str = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
        return self._parse_shares(xml_str)

    def get_vm_usb_devices(self, name):
        conn = self.connect()
        dom = conn.lookupByName(name)
        xml_str = dom.XMLDesc(0)
        return self._parse_usb_devices(xml_str)

    def detach_share(self, vm_name, share_xml):
        conn = self.connect()
        dom = conn.lookupByName(vm_name)
        dom.detachDeviceFlags(share_xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)

    def detach_usb_device(self, vm_name, device_xml):
        conn = self.connect()
        dom = conn.lookupByName(vm_name)
        dom.detachDeviceFlags(device_xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)

    def attach_usb_device(self, vm_name, device_xml):
        conn = self.connect()
        dom = conn.lookupByName(vm_name)
        dom.attachDeviceFlags(device_xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)

    def get_vm_state(self, name):
        conn = self.connect()
        dom = conn.lookupByName(name)
        info = dom.info()
        return STATE_NAMES.get(info[0], 'unknown')

    def _get_ip(self, dom):
        try:
            # Get MAC address from domain XML
            xml_str = dom.XMLDesc(0)
            root = ET.fromstring(xml_str)
            mac_elem = root.find(".//interface/mac")
            if mac_elem is None:
                return ''
            mac = mac_elem.get('address', '').lower()
            if not mac:
                return ''

            # Try DHCP leases from default network
            conn = self.connect()
            try:
                net = conn.networkLookupByName('default')
                for lease in net.DHCPLeases():
                    if lease.get('mac', '').lower() == mac:
                        return lease.get('ipaddr', '')

                # Try static reservations in network XML
                net_xml = ET.fromstring(net.XMLDesc())
                for host in net_xml.findall(".//dhcp/host"):
                    if host.get('mac', '').lower() == mac:
                        return host.get('ip', '')
            except libvirt.libvirtError:
                pass

            # Fallback: domain interface addresses
            try:
                ifaces = dom.interfaceAddresses(
                    libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE
                )
                for iface_info in ifaces.values():
                    for addr in iface_info.get('addrs', []):
                        if addr.get('type') == 0:  # IPv4
                            return addr.get('addr', '')
            except libvirt.libvirtError:
                pass
        except Exception:
            pass
        return ''

    def _parse_shares(self, xml_str):
        shares = []
        root = ET.fromstring(xml_str)
        for fs in root.findall(".//filesystem"):
            source = fs.find("source")
            target = fs.find("target")
            driver = fs.find("driver")
            if source is not None and target is not None:
                host_dir = source.get('dir', '')
                mount_tag = target.get('dir', '')
                fs_type = 'virtiofs' if (
                    driver is not None and driver.get('type') == 'virtiofs'
                ) else '9p'
                shares.append({
                    'host_dir': host_dir,
                    'mount_tag': mount_tag,
                    'fs_type': fs_type,
                })
        return shares

    def _parse_usb_devices(self, xml_str):
        devices = []
        root = ET.fromstring(xml_str)
        for hostdev in root.findall(".//hostdev[@type='usb']"):
            source = hostdev.find("source")
            if source is None:
                continue
            vendor_elem = source.find("vendor")
            product_elem = source.find("product")
            address_elem = source.find("address")

            device = {}
            if vendor_elem is not None and product_elem is not None:
                device['vendor_id'] = vendor_elem.get('id', '').replace('0x', '')
                device['product_id'] = product_elem.get('id', '').replace('0x', '')
                device['addressing'] = 'vendor'
            elif address_elem is not None:
                device['bus'] = address_elem.get('bus', '')
                device['device'] = address_elem.get('device', '')
                device['addressing'] = 'address'
            else:
                continue
            devices.append(device)
        return devices

    def find_and_detach_usb(self, vm_name, vendor_id, product_id):
        """Find a USB device in a VM by vendor:product and detach it.

        Matches against both vendor:product and bus:device addressed hostdevs
        in both running and persistent configs. Returns True if detached.
        """
        conn = self.connect()
        dom = conn.lookupByName(vm_name)
        info = dom.info()
        is_running = info[0] == 1
        detached = False

        # Try running config first
        if is_running:
            xml_str = dom.XMLDesc(0)
            hostdev_xml = self._find_usb_hostdev_xml(
                xml_str, vendor_id, product_id
            )
            if hostdev_xml:
                try:
                    dom.detachDeviceFlags(
                        hostdev_xml, libvirt.VIR_DOMAIN_AFFECT_LIVE
                    )
                    detached = True
                except libvirt.libvirtError:
                    pass

        # Also try persistent config (may differ from running)
        inactive_xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
        hostdev_xml = self._find_usb_hostdev_xml(
            inactive_xml, vendor_id, product_id
        )
        if hostdev_xml:
            try:
                dom.detachDeviceFlags(
                    hostdev_xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG
                )
                detached = True
            except libvirt.libvirtError:
                pass

        return detached

    def _find_usb_hostdev_xml(self, domain_xml, vendor_id, product_id):
        """Find a hostdev element matching vendor:product in domain XML.

        Matches vendor:product addressed devices directly.
        For bus:device addressed devices, resolves the host USB address
        via sysfs to match against vendor:product.
        """
        import subprocess

        root = ET.fromstring(domain_xml)
        vid = vendor_id.lower().replace('0x', '')
        pid = product_id.lower().replace('0x', '')

        for hostdev in root.findall(".//hostdev[@type='usb']"):
            source = hostdev.find("source")
            if source is None:
                continue

            vendor_elem = source.find("vendor")
            product_elem = source.find("product")
            address_elem = source.find("address")

            # Direct vendor:product match
            if vendor_elem is not None and product_elem is not None:
                dev_vid = vendor_elem.get('id', '').replace('0x', '').lower()
                dev_pid = product_elem.get('id', '').replace('0x', '').lower()
                if dev_vid == vid and dev_pid == pid:
                    return ET.tostring(hostdev, encoding='unicode')

            # Bus:device match - check if the host device at that address
            # has our vendor:product
            if address_elem is not None:
                bus = address_elem.get('bus', '')
                device = address_elem.get('device', '')
                if bus and device:
                    try:
                        bus_pad = f"{int(bus):03d}"
                        dev_pad = f"{int(device):03d}"
                        result = subprocess.run(
                            ['lsusb', '-s', f'{bus_pad}:{dev_pad}'],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            for line in result.stdout.strip().splitlines():
                                if f'{vid}:{pid}' in line.lower():
                                    return ET.tostring(
                                        hostdev, encoding='unicode'
                                    )
                    except Exception:
                        pass

        return None

    def get_share_xml_block(self, vm_name, host_dir):
        conn = self.connect()
        dom = conn.lookupByName(vm_name)
        xml_str = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
        root = ET.fromstring(xml_str)
        for fs in root.findall(".//filesystem"):
            source = fs.find("source")
            if source is not None and source.get('dir') == host_dir:
                return ET.tostring(fs, encoding='unicode')
        return None
