---
title: AMD64 NoCloud Seed USB Helper
description: Create a CIDATA NoCloud seed USB for Ubuntu Server amd64 autoinstall
---

# AMD64 NoCloud Seed USB Helper

This guide creates one script that prepares the `amd64` NoCloud seed USB for Ubuntu Server autoinstall.

The script takes a node name such as `amd64-01` and copies the matching file:

```text
setup/cloud-config-amd64-01.yml
```

to the seed USB as:

```text
user-data
```

It also creates the required:

```text
meta-data
```

file and formats the seed USB with the required NoCloud label:

```text
CIDATA
```

The goal is to make the `amd64` workflow feel closer to the Raspberry Pi workflow.

For Raspberry Pi:

```bash
flash \
  --userdata setup/cloud-config-arm64-01.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

For `amd64`, the equivalent flow is:

```text
setup/cloud-config-amd64-01.yml
  -> CIDATA/user-data
  -> Ubuntu Server installer booted with autoinstall ds=nocloud
  -> provisioned amd64-01
```

---

## 1. Expected repository layout

Run these commands from the root of your repository.

Expected files:

```text
setup/
  cloud-config-amd64-01.yml
  cloud-config-amd64-02.yml
  cloud-config-amd64-03.yml

scripts/
  make-amd64-nocloud-seed.sh
```

---

## 2. Create the scripts directory

```bash
mkdir -p scripts
```

---

## 3. Create the NoCloud seed helper script

Create the script file.

```bash
cat > scripts/make-amd64-nocloud-seed.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'HELP'
Usage:
  make-amd64-nocloud-seed.sh <node-name> <seed-disk>

Examples:
  ./scripts/make-amd64-nocloud-seed.sh amd64-01 /dev/disk4
  ./scripts/make-amd64-nocloud-seed.sh amd64-02 /dev/disk4
  ./scripts/make-amd64-nocloud-seed.sh amd64-03 /dev/disk4

This script:
  1. Uses setup/cloud-config-<node-name>.yml as NoCloud user-data
  2. Creates matching meta-data
  3. Formats the seed USB as FAT32 with label CIDATA
  4. Copies user-data and meta-data to the seed USB

The seed USB is used with the Ubuntu Server amd64 installer.
At the Ubuntu installer GRUB boot line, add:

  autoinstall ds=nocloud
HELP
}

require_command() {
  local command_name="$1"

  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: ${command_name}" >&2
    exit 1
  fi
}

get_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || pwd
}

validate_node_name() {
  local node_name="$1"

  if [[ ! "${node_name}" =~ ^amd64-[0-9][0-9]$ ]]; then
    echo "ERROR: Node name must look like amd64-01, amd64-02, amd64-03." >&2
    exit 1
  fi
}

validate_source_file() {
  local source_user_data="$1"

  if [[ ! -f "${source_user_data}" ]]; then
    echo "ERROR: Missing cloud-init file: ${source_user_data}" >&2
    exit 1
  fi
}

show_seed_disk() {
  local seed_disk="$1"

  echo
  echo "Selected seed USB disk:"
  echo
  diskutil info "${seed_disk}" || {
    echo "ERROR: Could not inspect ${seed_disk}" >&2
    exit 1
  }
}

confirm_seed_disk() {
  local seed_disk="$1"

  show_seed_disk "${seed_disk}"

  echo
  echo "This will erase ${seed_disk} and recreate it as a CIDATA seed USB."
  read -r -p "Type CIDATA to continue: " answer

  if [[ "${answer}" != "CIDATA" ]]; then
    echo "Aborted."
    exit 1
  fi
}

create_seed_files() {
  local node_name="$1"
  local source_user_data="$2"
  local build_dir="$3"

  mkdir -p "${build_dir}"

  cp "${source_user_data}" "${build_dir}/user-data"

  cat > "${build_dir}/meta-data" <<META
instance-id: ${node_name}
local-hostname: ${node_name}
META
}

format_seed_usb() {
  local seed_disk="$1"

  echo
  echo "Formatting seed USB as FAT32 CIDATA..."
  diskutil eraseDisk FAT32 CIDATA MBR "${seed_disk}"
}

copy_seed_files() {
  local build_dir="$1"
  local cidata_volume="/Volumes/CIDATA"

  if [[ ! -d "${cidata_volume}" ]]; then
    echo "ERROR: Expected ${cidata_volume} to be mounted." >&2
    exit 1
  fi

  echo
  echo "Copying NoCloud seed files..."
  cp "${build_dir}/user-data" "${cidata_volume}/user-data"
  cp "${build_dir}/meta-data" "${cidata_volume}/meta-data"

  sync

  echo
  echo "Seed USB contents:"
  ls -la "${cidata_volume}"

  echo
  echo "Ejecting seed USB..."
  diskutil eject "${cidata_volume}"
}

main() {
  if [[ "$#" -ne 2 ]]; then
    usage
    exit 1
  fi

  local node_name="$1"
  local seed_disk="$2"
  local repo_root
  local source_user_data
  local build_dir

  require_command diskutil
  require_command cp
  require_command sync

  validate_node_name "${node_name}"

  repo_root="$(get_repo_root)"
  source_user_data="${repo_root}/setup/cloud-config-${node_name}.yml"
  build_dir="${repo_root}/build/nocloud/${node_name}"

  validate_source_file "${source_user_data}"

  echo "Repository root: ${repo_root}"
  echo "Node name:       ${node_name}"
  echo "Source config:   ${source_user_data}"
  echo "Seed disk:       ${seed_disk}"

  confirm_seed_disk "${seed_disk}"
  create_seed_files "${node_name}" "${source_user_data}" "${build_dir}"
  format_seed_usb "${seed_disk}"
  copy_seed_files "${build_dir}"

  echo
  echo "Done."
  echo
  echo "Use this seed USB with the Ubuntu Server amd64 installer."
  echo "At the installer GRUB boot line, add:"
  echo
  echo "  autoinstall ds=nocloud"
  echo
}

main "$@"
EOF
```

---

## 4. Make the script executable

```bash
chmod +x scripts/make-amd64-nocloud-seed.sh
```

---

## 5. Confirm your AMD64 cloud-init files exist

```bash
ls -la setup/cloud-config-amd64-*.yml
```

Expected files:

```text
setup/cloud-config-amd64-01.yml
setup/cloud-config-amd64-02.yml
setup/cloud-config-amd64-03.yml
```

---

## 6. Insert the seed USB and identify it

Insert the small USB drive that will become the NoCloud seed USB.

Then run:

```bash
diskutil list
```

Find the USB disk.

Example:

```text
/dev/disk4
```

Use the disk for the small seed USB, not the Ubuntu installer USB and not any external data disk.

---

## 7. Create the seed USB for amd64-01

Replace `/dev/disk4` with the seed USB disk from `diskutil list`.

```bash
./scripts/make-amd64-nocloud-seed.sh amd64-01 /dev/disk4
```

This creates a seed USB where:

```text
CIDATA/user-data  = setup/cloud-config-amd64-01.yml
CIDATA/meta-data  = instance-id and hostname for amd64-01
```

---

## 8. Boot amd64-01 with autoinstall

Insert both USB devices into the `amd64-01` machine:

```text
Ubuntu Server amd64 installer USB
CIDATA NoCloud seed USB
```

Boot from the Ubuntu Server installer USB.

At the Ubuntu installer GRUB menu, edit the boot command and add:

```text
autoinstall ds=nocloud
```

Then continue booting.

The installer should discover the `CIDATA` seed USB and run:

```text
setup/cloud-config-amd64-01.yml
```

as its NoCloud `user-data`.

---

## 9. Create the seed USB for amd64-02

Reinsert the same seed USB into the Mac.

Then run:

```bash
diskutil list
```

Replace `/dev/disk4` with the current seed USB disk.

```bash
./scripts/make-amd64-nocloud-seed.sh amd64-02 /dev/disk4
```

This creates a seed USB where:

```text
CIDATA/user-data  = setup/cloud-config-amd64-02.yml
CIDATA/meta-data  = instance-id and hostname for amd64-02
```

---

## 10. Boot amd64-02 with autoinstall

Insert both USB devices into the `amd64-02` machine:

```text
Ubuntu Server amd64 installer USB
CIDATA NoCloud seed USB
```

Boot from the Ubuntu Server installer USB.

At the Ubuntu installer GRUB menu, edit the boot command and add:

```text
autoinstall ds=nocloud
```

Then continue booting.

The installer should discover the `CIDATA` seed USB and run:

```text
setup/cloud-config-amd64-02.yml
```

as its NoCloud `user-data`.

---

## 11. Create the seed USB for amd64-03

Reinsert the same seed USB into the Mac.

Then run:

```bash
diskutil list
```

Replace `/dev/disk4` with the current seed USB disk.

```bash
./scripts/make-amd64-nocloud-seed.sh amd64-03 /dev/disk4
```

This creates a seed USB where:

```text
CIDATA/user-data  = setup/cloud-config-amd64-03.yml
CIDATA/meta-data  = instance-id and hostname for amd64-03
```

---

## 12. Boot amd64-03 with autoinstall

Insert both USB devices into the `amd64-03` machine:

```text
Ubuntu Server amd64 installer USB
CIDATA NoCloud seed USB
```

Boot from the Ubuntu Server installer USB.

At the Ubuntu installer GRUB menu, edit the boot command and add:

```text
autoinstall ds=nocloud
```

Then continue booting.

The installer should discover the `CIDATA` seed USB and run:

```text
setup/cloud-config-amd64-03.yml
```

as its NoCloud `user-data`.

---

## 13. Validate first boot

After the machine reboots, SSH into the node.

For `amd64-01`:

```bash
ssh dbuddenbaum@192.168.2.61
```

For `amd64-02`:

```bash
ssh dbuddenbaum@192.168.2.62
```

For `amd64-03`:

```bash
ssh dbuddenbaum@192.168.2.63
```

Check cloud-init status.

```bash
cloud-init status --wait
```

```bash
cloud-init status --long
```

Check hostname.

```bash
hostnamectl
```

Check disks.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL
```

Check network.

```bash
ip addr
```

```bash
ip route
```

---

## 14. Quick reference

Create seed for `amd64-01`:

```bash
./scripts/make-amd64-nocloud-seed.sh amd64-01 /dev/disk4
```

Create seed for `amd64-02`:

```bash
./scripts/make-amd64-nocloud-seed.sh amd64-02 /dev/disk4
```

Create seed for `amd64-03`:

```bash
./scripts/make-amd64-nocloud-seed.sh amd64-03 /dev/disk4
```

Boot argument:

```text
autoinstall ds=nocloud
```

Effective mapping:

```text
setup/cloud-config-amd64-01.yml -> CIDATA/user-data -> amd64-01
setup/cloud-config-amd64-02.yml -> CIDATA/user-data -> amd64-02
setup/cloud-config-amd64-03.yml -> CIDATA/user-data -> amd64-03
```

---

## 15. Troubleshooting

If the installer does not autoinstall, confirm that the seed USB volume is named:

```text
CIDATA
```

Confirm that the seed USB has these two files at the root:

```text
user-data
meta-data
```

On macOS, after reinserting the seed USB, check:

```bash
ls -la /Volumes/CIDATA
```

Expected output includes:

```text
user-data
meta-data
```

If the installer still does not find the seed, try this boot argument instead:

```text
autoinstall ds=nocloud;s=/cdrom/
```

If that still does not work, use the HTTP NoCloud method instead of the seed USB method.

---

## 16. HTTP NoCloud fallback

From the repository root, create the `amd64-01` seed files.

```bash
mkdir -p build/nocloud/amd64-01
cp setup/cloud-config-amd64-01.yml build/nocloud/amd64-01/user-data
cat > build/nocloud/amd64-01/meta-data <<'EOF'
instance-id: amd64-01
local-hostname: amd64-01
EOF
```

Serve the seed directory over HTTP.

```bash
cd build/nocloud/amd64-01
python3 -m http.server 8080
```

Boot the AMD64 installer and add this boot argument.

Replace `192.168.2.100` with the IP address of the machine serving the files.

```text
autoinstall ds=nocloud-net;s=http://192.168.2.100:8080/
```
