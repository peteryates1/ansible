# Ansible Libvirt VM Automation

This repository automates local KVM/libvirt VM workflows with Ansible and a `./vm` wrapper script.

It supports:
- Creating reusable Debian-based templates with security hardening.
- Creating VMs from templates for role types: `common`, `claude`, `git`, `opencode`, `mate`, `jop-dev`.
- VM lifecycle operations (`start`, `stop`, `status`, `destroy`, `list`, `ip`, `ssh`).
- Sharing host directories into VMs via virtiofs/9p.
- USB device attach/detach flows for FPGA and serial workflows.
- Git mirror management for shared reference repos.
- Toolchain installers for SpinalHDL, Alchitry, and Arrow USB Blaster.
- Automated post-creation setup for complex VM types (`jop-dev`).

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
./vm template create common      # Base hardened template (required first)
./vm template create claude      # Claude Code VM
./vm template create git         # Git server VM
./vm template create opencode    # OpenCode VM
./vm template create mate        # MATE desktop + xrdp
./vm template create jop-dev     # MATE + FPGA dev tools (Quartus/Vivado/Eclipse launchers, sbt, udev rules)
```

2. Create VMs from templates:

```bash
./vm create claude01 claude
./vm create git01 git
./vm create jop01 jop-dev        # Auto-runs setup (shares host dirs, installs blaster .so)
```

3. Check and connect:

```bash
./vm list
./vm status claude01
./vm ip claude01
./vm ssh claude01
./vm ssh claude01 claude -- whoami
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
./vm template create <type>      # Types: common, claude, git, opencode, mate, jop-dev
./vm template list
./vm template destroy <type>
```

Sharing and setup:

```bash
./vm share-dir <vm> <host_dir> [mount_point]   # Share host dir into VM (read-only, virtiofs/9p)
./vm setup <vm> <type>                          # Post-creation setup (types: jop-dev)
```

USB management:

```bash
./vm usb-list
./vm usb-serials
./vm usb-attach <vm> <usb_id> [usb_addr] [usb_name]
./vm usb-detach <vm|all> <usb_id> [usb_addr] [usb_name]
```

Git mirrors (shared reference repos for fast clones in VMs):

```bash
./vm mirror add <git-url>        # Clone bare mirror to /srv/git
./vm mirror list
./vm mirror sync [repo]          # Fetch updates
./vm mirror remove <repo>
```

Toolchain installers:

```bash
./vm install-spinalhdl <vm> [user]    # Java/Scala/sbt (skips Java if already available)
./vm install-alchitry <vm> [user]     # Alchitry AU udev rules
./vm install-blaster <vm> [user]      # Arrow USB Blaster support (host .so + VM udev/config)
./vm resize-disk <vm> <size>          # Resize VM disk and grow guest filesystem
./vm set-passwd <vm> <user>           # Set login password (for xrdp)
```

## jop-dev template

The `jop-dev` template builds a MATE desktop VM for FPGA development. It bakes in:
- MATE desktop with custom panel layout (Quartus 18.1/25.1, Vivado 2025.2, Eclipse, Chrome, Terminal, Caja)
- openjdk-21-jdk-headless, scala, sbt
- Alchitry AU and USB-Blaster udev rules
- Arrow USB Blaster config, libpng12 (Quartus 18.1), legacy ncurses/tinfo symlinks (Vivado)
- Google Chrome, xrdp, locale support

After `./vm create jop01 jop-dev`, setup auto-runs to share host directories and install the host-side Arrow Blaster `.so`.

Prerequisites on host:
- `/opt/altera` (Quartus 18.1 and/or 25.1)
- `/opt/xilinx` (Vivado 2025.2)
- `/opt/eclipse` and `/opt/.p2` (Eclipse IDE)
- `/opt/jdk1.6.0_45`, `/opt/jdk1.8.0_202` (legacy JDKs for older tools)
- `/srv/git` (or use `./vm mirror add <url>` to create it)
- `/var/lib/libvirt/shared/libpng12-0_1.2.54-1ubuntu1.1_amd64.deb`
- `/var/lib/libvirt/shared/Arrow_USB_Programmer_2.5.1_linux64/`

## Configuration notes

- Global defaults live in `inventory/hosts.yml`.
- Template types are auto-discovered from subdirectories under `roles/`.
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
ansible-playbook playbooks/share-dir.yml -e vm_name=jop01 -e host_dir=/opt/xilinx
```

