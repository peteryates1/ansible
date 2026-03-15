from gui.workers.playbook_worker import PlaybookWorker
from gui.workers.chained_playbook_worker import ChainedPlaybookWorker
from gui.constants import VM_USER


class PlaybookService:
    @staticmethod
    def run_share_dir(vm_name, host_dir, mount_point=None, config_only=False):
        extra_vars = {
            'vm_name': vm_name,
            'vm_user': VM_USER,
            'host_dir': host_dir,
            'mount_point': mount_point or host_dir,
        }
        if config_only:
            extra_vars['config_only'] = 'true'
        return PlaybookWorker('share-dir', extra_vars)

    @staticmethod
    def run_usb_auto(vm_name, usb_id, usb_name=None, usb_serial=None):
        extra_vars = {
            'vm_name': vm_name,
            'usb_id': usb_id,
        }
        if usb_serial:
            extra_vars['usb_serial'] = usb_serial
        elif usb_name:
            extra_vars['usb_name'] = usb_name
        return PlaybookWorker('usb-auto', extra_vars)

    @staticmethod
    def run_usb_auto_remove(vm_name, usb_id, usb_serial=None):
        extra_vars = {
            'vm_name': vm_name,
            'usb_id': usb_id,
        }
        if usb_serial:
            extra_vars['usb_serial'] = usb_serial
        return PlaybookWorker('usb-auto-remove', extra_vars)

    @staticmethod
    def run_usb_attach(vm_name, usb_id, usb_name=None, usb_serial=None):
        extra_vars = {
            'vm_name': vm_name,
            'usb_id': usb_id,
        }
        if usb_serial:
            extra_vars['usb_serial'] = usb_serial
        elif usb_name:
            extra_vars['usb_name'] = usb_name
        return PlaybookWorker('usb-attach', extra_vars)

    @staticmethod
    def run_usb_detach_all(vm_name=None):
        extra_vars = {}
        if vm_name:
            extra_vars['vm_name'] = vm_name
        return PlaybookWorker('usb-detach-all', extra_vars)

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
        return PlaybookWorker('mount-shares', {
            'vm_name': vm_name,
            'vm_user': VM_USER,
        })

    @staticmethod
    def run_install(playbook_name, vm_name, target_user=None):
        extra_vars = {
            'vm_name': vm_name,
            'vm_user': VM_USER,
        }
        if target_user:
            if playbook_name == 'create-vm-user':
                extra_vars['target_user'] = target_user
            else:
                extra_vars['install_user'] = target_user
        return PlaybookWorker(playbook_name, extra_vars)

    @staticmethod
    def run_install_batch(playbook_name, vm_names, target_user=None):
        tasks = []
        for name in vm_names:
            extra_vars = {'vm_name': name, 'vm_user': VM_USER}
            if target_user:
                if playbook_name == 'create-vm-user':
                    extra_vars['target_user'] = target_user
                else:
                    extra_vars['install_user'] = target_user
            tasks.append((playbook_name, extra_vars))
        return ChainedPlaybookWorker(tasks)
