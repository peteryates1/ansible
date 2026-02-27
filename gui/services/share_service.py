import os

from gui.constants import SHARE_DISCOVERY_PATHS


class ShareService:
    def __init__(self, libvirt_service):
        self._libvirt = libvirt_service
        self._custom_dirs = set()

    def add_custom_dir(self, path):
        self._custom_dirs.add(path)

    def discover_host_dirs(self, vm_names=None):
        dirs = set()

        # Scan filesystem paths
        for path in SHARE_DISCOVERY_PATHS:
            if not os.path.isdir(path):
                continue
            if path == '/srv/git':
                dirs.add(path)
            else:
                try:
                    for entry in sorted(os.listdir(path)):
                        full = os.path.join(path, entry)
                        if os.path.isdir(full):
                            dirs.add(full)
                except PermissionError:
                    pass

        # Include dirs already attached to VMs
        if vm_names:
            for vm_name in vm_names:
                try:
                    shares = self._libvirt.get_vm_shares(vm_name)
                    for s in shares:
                        dirs.add(s['host_dir'])
                except Exception:
                    pass

        # Include user-added custom dirs
        dirs.update(self._custom_dirs)

        return sorted(dirs)

    def get_share_matrix(self, vm_names, host_dirs):
        # Cache per-VM shares to avoid re-querying
        vm_shares = {}
        for vm_name in vm_names:
            try:
                shares = self._libvirt.get_vm_shares(vm_name)
                vm_shares[vm_name] = {s['host_dir'] for s in shares}
            except Exception:
                vm_shares[vm_name] = set()

        matrix = {}
        for d in host_dirs:
            for vm_name in vm_names:
                matrix[(d, vm_name)] = d in vm_shares[vm_name]
        return matrix

    def detach_share(self, vm_name, host_dir):
        share_xml = self._libvirt.get_share_xml_block(vm_name, host_dir)
        if share_xml is None:
            raise RuntimeError(
                f"Share {host_dir} not found in {vm_name} config"
            )
        self._libvirt.detach_share(vm_name, share_xml)
