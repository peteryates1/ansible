from gui.workers.playbook_worker import PlaybookWorker


class PlaybookService:
    @staticmethod
    def run_share_dir(vm_name, host_dir, mount_point=None, config_only=False):
        extra_vars = {
            'vm_name': vm_name,
            'host_dir': host_dir,
            'mount_point': mount_point or host_dir,
        }
        if config_only:
            extra_vars['config_only'] = 'true'
        return PlaybookWorker('share-dir', extra_vars)

    @staticmethod
    def run_usb_auto(vm_name, usb_id, usb_name=None):
        extra_vars = {
            'vm_name': vm_name,
            'usb_id': usb_id,
        }
        if usb_name:
            extra_vars['usb_name'] = usb_name
        return PlaybookWorker('usb-auto', extra_vars)

    @staticmethod
    def run_usb_auto_remove(vm_name, usb_id):
        return PlaybookWorker('usb-auto-remove', {
            'vm_name': vm_name,
            'usb_id': usb_id,
        })

    @staticmethod
    def run_usb_attach(vm_name, usb_id, usb_name=None):
        extra_vars = {
            'vm_name': vm_name,
            'usb_id': usb_id,
        }
        if usb_name:
            extra_vars['usb_name'] = usb_name
        return PlaybookWorker('usb-attach', extra_vars)

    @staticmethod
    def run_usb_detach(usb_id, vm_name=None, usb_name=None):
        extra_vars = {'usb_id': usb_id}
        if vm_name:
            extra_vars['vm_name'] = vm_name
        if usb_name:
            extra_vars['usb_name'] = usb_name
        return PlaybookWorker('usb-detach', extra_vars)

    @staticmethod
    def run_mount_shares(vm_name):
        return PlaybookWorker('mount-shares', {'vm_name': vm_name})
