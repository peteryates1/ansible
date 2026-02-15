# Ansible Libvirt VM Automation

This repository automates local KVM/libvirt VM workflows with Ansible and a `./vm` wrapper script.

It supports:
- Creating reusable Debian-based templates.
- Creating VMs from templates for role types: `common`, `claude`, `git`, `opencode`.
- VM lifecycle operations (`start`, `stop`, `status`, `destroy`, `list`, `ip`, `ssh`).
- USB device attach/detach flows for FPGA and serial workflows.
- Optional in-VM installers for Quartus and SpinalHDL toolchains.

## Repository layout

- `vm`: main CLI wrapper around Ansible playbooks.
- `inventory/hosts.yml`: shared defaults (VM storage paths, default `vm_user`, etc.).
- `playbooks/`: task entry points (create, template-create, usb-attach, install-quartus, ...).
- `roles/`: role-specific cloud-init customizations and defaults.

## Prerequisites

Host requirements:
- Linux host with KVM/libvirt working (`virsh` against `qemu:///system`).
- Default libvirt network available (`default`).
- `sudo` access.

Tools expected by playbooks/scripts:
- `ansible-playbook`
- `virsh`, `virt-install`, `qemu-img`
- `genisoimage`
- `virt-sysprep`, `virt-customize`
- `ssh`
- `lsusb`, `udevadm` (for USB-related commands)

SSH prerequisites:
- A host authorized keys file is used when building templates.
- By default this is derived from your host user (`/home/<host_user>/.ssh/authorized_keys`), or you can override `ssh_authorized_keys_file`.

## One-time setup

From repo root:

```bash
ansible-playbook playbooks/setup-sudo.yml
```

Then refresh group membership (or log out/in):

```bash
newgrp libvirt
```

## Quick start

1. Create templates (recommended order):

```bash
./vm template create common
./vm template create claude
./vm template create git
./vm template create opencode
```

2. Create VMs from templates:

```bash
./vm create claude01 claude
./vm create git01 git
```

3. Check and connect:

```bash
./vm list
./vm status claude01
./vm ip claude01
./vm ssh claude01
```

## Common commands

```bash
./vm help
./vm create <name> <type>
./vm destroy <name>
./vm start <name>
./vm stop <name>
./vm status <name>
./vm ip <name>
./vm list
./vm ssh <name> [user]
./vm copy-key <src_vm> <dest_vm> [src_user] [dest_user]
```

Template management:

```bash
./vm template create <common|claude|git|opencode>
./vm template list
./vm template destroy <common|claude|git|opencode>
```

USB management:

```bash
./vm usb-list
./vm usb-serials
./vm usb-attach <vm_name> <usb_id> [usb_addr] [usb_name]
./vm usb-detach <vm_name|all> <usb_id> [usb_addr] [usb_name]
```

## Toolchain installers

Quartus installer flow (requires host shared directories):

```bash
./vm install-quartus <vm_name> [vm_user]
```

Expected default share paths:
- `/var/lib/libvirt/shared/quartus`
- `/var/lib/libvirt/shared/Arrow_USB_Programmer_2.5.1_linux64`

SpinalHDL toolchain installer:

```bash
./vm install-spinalhdl <vm_name> [vm_user]
```

## Configuration notes

- Global defaults live in `inventory/hosts.yml`.
- `vm_user` controls several host-side ownership and SSH invocation defaults.
- Cloud-init guest user naming is defined in:
  - `roles/common/templates/user-data.yml.j2`
  - `roles/common/templates/instance-user-data.yml.j2`

If you want a different default guest login user, update those templates and rebuild templates.

## Running playbooks directly

You can call playbooks without `./vm` when needed:

```bash
ansible-playbook playbooks/create.yml -e vm_name=claude01 -e vm_role=claude
ansible-playbook playbooks/template-create.yml -e template_type=common
ansible-playbook playbooks/usb-attach.yml -e vm_name=claude01 -e usb_id=09fb:6001
```

