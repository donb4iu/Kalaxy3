---
title: Ubuntu Node Provisioning
description: Mixed arm64 Raspberry Pi and amd64 Ubuntu provisioning guide
---

# Ubuntu Installation and Node Provisioning

This guide describes how to provision Ubuntu nodes for a mixed-architecture
homelab or Kubernetes cluster. It supports both Raspberry Pi `arm64` machines
and Intel/AMD `amd64` bare-metal machines.

The goal is to produce repeatable Ubuntu installs while avoiding the two most
common provisioning mistakes:

1. Flashing or installing to the wrong disk.
2. Assuming Linux disk ordering is stable.

For new installs, prefer Ubuntu 24.04 LTS unless a specific project requires a
different release. Raspberry Pi nodes use Ubuntu's preinstalled Raspberry Pi
server image. Bare-metal `amd64` nodes use the standard Ubuntu Server installer
ISO.

This document assumes the flashing workstation is macOS.

All commands are shown in fenced code blocks so they can be selected and copied
directly from a browser.

---

## Table of Contents

- [1. Supported Node Types](#1-supported-node-types)
- [2. General Safety Rules](#2-general-safety-rules)
- [3. Recommended Repository Layout](#3-recommended-repository-layout)
- [4. Raspberry Pi arm64 Provisioning](#4-raspberry-pi-arm64-provisioning)
- [5. amd64 Bare-Metal Provisioning](#5-amd64-bare-metal-provisioning)
- [6. Optional amd64 Cloud-Init and Autoinstall](#6-optional-amd64-cloud-init-and-autoinstall)
- [7. First-Boot Validation for All Nodes](#7-first-boot-validation-for-all-nodes)
- [8. Storage Validation for MinIO Nodes](#8-storage-validation-for-minio-nodes)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Recommended Current Workflows](#10-recommended-current-workflows)
- [11. Archived Historical Notes](#11-archived-historical-notes)
- [Appendix A: Useful Validation Commands](#appendix-a-useful-validation-commands)
- [Appendix B: Publishing Notes](#appendix-b-publishing-notes)

---

# 1. Supported Node Types

This provisioning guide supports two node families.

| Node Type | Architecture | Install Method | Boot Media |
|---|---:|---|---|
| Raspberry Pi 4 / Pi 5 | `arm64` | Ubuntu Raspberry Pi preinstalled image plus cloud-init | USB SSD or SD card |
| Intel / AMD bare metal | `amd64` | Ubuntu Server ISO or autoinstall | SSD or NVMe |

Example cluster layout:

```text
arm64-01  Raspberry Pi
arm64-02  Raspberry Pi
arm64-03  Raspberry Pi
arm64-04  Raspberry Pi
arm64-05  Raspberry Pi

amd64-01  Intel / AMD bare metal
amd64-02  Intel / AMD bare metal
amd64-03  Intel / AMD bare metal
```

Recommended operating system:

```text
Ubuntu 24.04 LTS Server
```

---

# 2. General Safety Rules

Provisioning writes directly to disks. Treat every flashing, imaging, and
installer step as destructive until proven otherwise.

Never assume any of the following device names are stable:

```text
/dev/disk3
/dev/sda
/dev/sdb
/dev/nvme0n1
```

These names can change depending on boot order, attached USB devices, drive
controllers, BIOS behavior, and kernel discovery order.

Before writing an image, always identify the target disk by:

```text
size
model
vendor
serial number
connection type
whether it appeared after insertion
whether it is removable
```

For MinIO or other data disks, never rely only on `/dev/sda` or `/dev/sdb`.
Identify the intended disk using durable characteristics such as:

```text
rotational status
size
model
serial number
existing filesystems
mount status
whether it contains the root filesystem
operator confirmation
```

---

# 3. Recommended Repository Layout

A recommended repository layout is shown below.

```text
setup/
  cloud-config-arm64-01.yml
  cloud-config-arm64-02.yml
  cloud-config-arm64-03.yml
  cloud-config-arm64-04.yml
  cloud-config-arm64-05.yml

  autoinstall-amd64-01/
    user-data
    meta-data

  autoinstall-amd64-02/
    user-data
    meta-data

  autoinstall-amd64-03/
    user-data
    meta-data

docs/
  ubuntu-node-provisioning.md
```

The `arm64` files are intended for Raspberry Pi nodes. The `amd64` autoinstall
directories are optional and should only be used once disk selection has been
tested carefully.

---

# 4. Raspberry Pi arm64 Provisioning

Use this section for Raspberry Pi nodes.

Raspberry Pi provisioning uses the Ubuntu preinstalled server image for
Raspberry Pi. The cloud-init configuration is injected into the image during
flashing.

## 4.1 Install the Flash Tool on macOS

The Hypriot `flash` utility can write Ubuntu images and inject a cloud-init
`user-data` file during the flashing process.

Download the `flash` utility.

```bash
curl -LO "https://github.com/hypriot/flash/releases/download/2.5.1/flash"
```

Make the downloaded file executable.

```bash
chmod +x flash
```

Move the executable into `/usr/local/bin`.

```bash
sudo mv flash /usr/local/bin/flash
```

Verify that the tool is available.

```bash
flash --version
```

If the command is not found, confirm that `/usr/local/bin` is in your shell
`PATH`.

```bash
echo "$PATH"
```

---

## 4.2 Download the Ubuntu Raspberry Pi Image

Create a local download directory for Raspberry Pi images.

```bash
mkdir -p ~/Downloads/ubuntu-rpi
```

Move into the download directory.

```bash
cd ~/Downloads/ubuntu-rpi
```

Download the Ubuntu Raspberry Pi `arm64` server image.

```bash
curl -LO "https://cdimage.ubuntu.com/releases/noble/release/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz"
```

Download the checksum file from the same release directory.

```bash
curl -LO "https://cdimage.ubuntu.com/releases/noble/release/SHA256SUMS"
```

The image file should remain compressed as `.img.xz`. The `flash` tool can use
the compressed image directly.

---

## 4.3 Verify the Raspberry Pi Image

Generate the local SHA-256 checksum.

```bash
shasum -a 256 ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

Show the expected checksum from Ubuntu's `SHA256SUMS` file.

```bash
grep "ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz" SHA256SUMS
```

The value from `shasum` should match the value shown by `grep`.

Do not flash the image if the checksum does not match.

---

## 4.4 Identify the Target Disk on macOS

Before inserting the SD card or USB boot drive, list the disks currently attached
to the Mac.

```bash
diskutil list
```

Insert the SD card or USB boot drive.

Then list the disks again.

```bash
diskutil list
```

Identify the newly added disk by comparing the two command outputs.

Example target disk:

```text
/dev/disk3
```

Do not assume your target disk is `/dev/disk3`. The correct disk may be
`/dev/disk2`, `/dev/disk4`, or another value.

The disk shown by `flash` must match the disk you identified with
`diskutil list`.

---

## 4.5 Select the Correct arm64 Cloud-Init File

Use the cloud-init file that matches the Raspberry Pi node being provisioned.

```text
setup/cloud-config-arm64-01.yml  -> arm64-01
setup/cloud-config-arm64-02.yml  -> arm64-02
setup/cloud-config-arm64-03.yml  -> arm64-03
setup/cloud-config-arm64-04.yml  -> arm64-04
setup/cloud-config-arm64-05.yml  -> arm64-05
```

Before flashing, inspect the selected file and confirm that the hostname,
network settings, users, and SSH keys are correct.

```bash
grep -E "hostname|fqdn|192\.168\.2|users|ssh_authorized_keys" \
  setup/cloud-config-arm64-01.yml
```

If this command does not show the expected node identity, stop and check the
cloud-init file before flashing.

---

## 4.6 Flash the Raspberry Pi Boot Device

The following example flashes `arm64-01`.

```bash
flash \
  --userdata setup/cloud-config-arm64-01.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

During flashing, the tool may prompt for confirmation.

Example prompt:

```text
Is /dev/disk3 correct?
```

Only answer `y` if the displayed disk is definitely the intended SD card or USB
boot drive.

```text
y
```

If the disk is not correct, answer `n` or terminate the command.

---

## 4.7 Boot the Raspberry Pi

After flashing completes:

1. Eject the boot device from macOS.
2. Insert the SD card or USB drive into the Raspberry Pi.
3. Connect Ethernet.
4. Connect power.
5. Wait for first boot and cloud-init to complete.

The first boot may take several minutes because Ubuntu expands the filesystem,
applies cloud-init, configures networking, creates users, installs packages, and
starts services.

---

# 5. amd64 Bare-Metal Provisioning

Use this section for Intel or AMD bare-metal machines.

The `amd64` workflow is different from the Raspberry Pi workflow. Instead of
flashing a preinstalled image directly to the boot disk, create a bootable Ubuntu
Server installer USB and install Ubuntu onto the machine.

## 5.1 Download the Ubuntu Server amd64 ISO

Create a local download directory for the Ubuntu Server ISO.

```bash
mkdir -p ~/Downloads/ubuntu-amd64
```

Move into the download directory.

```bash
cd ~/Downloads/ubuntu-amd64
```

Download the Ubuntu Server `amd64` ISO.

```bash
curl -LO "https://releases.ubuntu.com/noble/ubuntu-24.04.4-live-server-amd64.iso"
```

Download the checksum file.

```bash
curl -LO "https://releases.ubuntu.com/noble/SHA256SUMS"
```

Download the signed checksum file.

```bash
curl -LO "https://releases.ubuntu.com/noble/SHA256SUMS.gpg"
```

---

## 5.2 Verify the amd64 ISO

Generate the local SHA-256 checksum.

```bash
shasum -a 256 ubuntu-24.04.4-live-server-amd64.iso
```

Show the expected checksum from Ubuntu's `SHA256SUMS` file.

```bash
grep "ubuntu-24.04.4-live-server-amd64.iso" SHA256SUMS
```

The value from `shasum` should match the value shown by `grep`.

Do not write the ISO to a USB installer if the checksum does not match.

---

## 5.3 Identify the USB Installer Disk on macOS

Insert the USB drive that will become the Ubuntu installer.

Before inserting the USB drive, list attached disks.

```bash
diskutil list
```

After inserting the USB drive, list attached disks again.

```bash
diskutil list
```

Identify the newly added USB drive by size, model, and device name.

Example USB installer disk:

```text
/dev/disk3
```

Do not assume this value is always correct.

---

## 5.4 Create a Bootable USB Installer on macOS

Unmount the USB installer disk.

Replace `/dev/disk3` with the disk you identified.

```bash
diskutil unmountDisk /dev/disk3
```

Write the Ubuntu Server ISO to the USB drive.

Replace `/dev/rdisk3` with the raw disk path that corresponds to your target
disk. On macOS, `/dev/rdisk3` is the raw version of `/dev/disk3`.

```bash
sudo dd \
  if=ubuntu-24.04.4-live-server-amd64.iso \
  of=/dev/rdisk3 \
  bs=4m \
  status=progress
```

Flush pending writes.

```bash
sync
```

Eject the USB installer.

```bash
diskutil eject /dev/disk3
```

The `dd` command overwrites the target disk. If the wrong disk is selected, data
loss can occur.

---

## 5.5 Install Ubuntu on the amd64 Machine

Insert the USB installer into the target `amd64` machine.

Boot the machine and select the USB drive from the boot menu.

During installation:

1. Choose Ubuntu Server.
2. Select the intended OS disk.
3. Do not select the MinIO or data disk as the OS target.
4. Enable OpenSSH server.
5. Create the expected administrative user.
6. Complete the installation.
7. Reboot after installation finishes.

For machines with both an OS drive and a MinIO drive, the OS should normally be
installed on the SSD or NVMe device, not the HDD intended for MinIO.

Example disk layout:

```text
4 TB NVMe       OS / Kubernetes boot disk
1 TB HDD        MinIO data disk
```

---

## 5.6 amd64 Disk Selection Guidance

After the first boot, inspect the disks from Ubuntu.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

Useful signals:

| Signal | Meaning |
|---|---|
| `ROTA=0` | SSD or NVMe |
| `ROTA=1` | Rotational HDD |
| Large NVMe device | Likely OS or fast storage |
| 1 TB rotational disk | Likely MinIO disk |
| Mounted `/` | Current boot/root disk |
| Unmounted blank disk | Candidate data disk |

Do not hard-code Linux disk names.

Avoid assuming these are stable:

```text
/dev/sda
/dev/sdb
/dev/nvme0n1
```

For MinIO provisioning, identify the intended data disk by combining several
signals:

```text
size
rotational status
filesystem state
mount state
model
serial
operator confirmation
```

---

# 6. Optional amd64 Cloud-Init and Autoinstall

Ubuntu autoinstall can make `amd64` provisioning repeatable, but it should be
used carefully. A bad autoinstall storage configuration can wipe the wrong disk.

For first-pass installs, manual installation is safer. After Ubuntu is installed,
use Ansible or a post-install script to apply node-specific configuration.

---

## 6.1 Recommended Autoinstall File Layout

Use one autoinstall directory per `amd64` node.

```text
setup/
  autoinstall-amd64-01/
    user-data
    meta-data

  autoinstall-amd64-02/
    user-data
    meta-data

  autoinstall-amd64-03/
    user-data
    meta-data
```

---

## 6.2 amd64 Autoinstall Node Mapping

Map each autoinstall configuration to a specific node.

```text
setup/autoinstall-amd64-01/user-data  -> amd64-01
setup/autoinstall-amd64-02/user-data  -> amd64-02
setup/autoinstall-amd64-03/user-data  -> amd64-03
```

---

## 6.3 Autoinstall Safety Warning

Use autoinstall only after disk selection rules have been validated on the
actual machine model.

Do not use an autoinstall storage block until you are certain it targets the
correct OS disk.

For machines with mixed storage, such as NVMe plus HDD, avoid generic storage
rules that blindly select the first available disk.

Bad pattern:

```text
Install to first available disk.
```

Safer pattern:

```text
Install to the expected SSD or NVMe boot disk after confirming size, model,
serial number, and whether it is already the root target.
```

---

# 7. First-Boot Validation for All Nodes

Run these checks after the first boot on both `arm64` and `amd64` machines.

These steps confirm that the node is reachable, correctly named, running the
expected OS, and using the expected disks.

---

## 7.1 Check Network Reachability

Ping the node by IP address.

```bash
ping <node-ip>
```

Example:

```bash
ping 192.168.2.51
```

If the node does not respond, confirm Ethernet, DHCP or static IP configuration,
switch connectivity, and whether the machine completed first boot.

---

## 7.2 SSH into the Node

Connect with SSH.

```bash
ssh dbuddenbaum@<node-ip>
```

Example:

```bash
ssh dbuddenbaum@192.168.2.51
```

If SSH fails, confirm that OpenSSH was installed and that cloud-init completed.

---

## 7.3 Check Cloud-Init Status

Wait for cloud-init to finish.

```bash
cloud-init status --wait
```

Show detailed cloud-init status.

```bash
cloud-init status --long
```

Cloud-init should report that it is done. If it reports an error, review the
cloud-init logs before continuing.

---

## 7.4 Check Hostname

Show the active hostname and operating system identity.

```bash
hostnamectl
```

Confirm that the hostname matches the expected node name.

Examples:

```text
arm64-01
arm64-02
amd64-01
amd64-02
```

---

## 7.5 Check IP Addresses and Routes

Show assigned IP addresses.

```bash
ip addr
```

Show the routing table.

```bash
ip route
```

Confirm that the node has the expected static IP or DHCP-assigned IP and that a
default route exists.

---

## 7.6 Check OS Version

Show the Ubuntu release.

```bash
lsb_release -a
```

The release should match the expected Ubuntu version for the cluster.

---

## 7.7 Check Block Devices

List block devices with size, rotational status, filesystem, mountpoint, model,
and serial number.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

This is one of the most important validation commands. Use it to confirm which
disk is the boot disk and which disk is the candidate MinIO or data disk.

---

## 7.8 Check Mounted Filesystems

Show mounted filesystems and available space.

```bash
df -h
```

Confirm that the root filesystem is mounted on the expected boot device.

---

## 7.9 Check SSH Service

Show the SSH service status.

```bash
systemctl status ssh --no-pager
```

The service should be active and running.

---

# 8. Storage Validation for MinIO Nodes

Before formatting or mounting a MinIO disk, confirm that the selected disk is
not the boot disk.

This matters for both Raspberry Pi and `amd64` nodes.

Expected storage pattern:

```text
Raspberry Pi nodes:
  boot device: USB SSD or SD card
  MinIO disk: 1 TB HDD

amd64 nodes:
  boot device: SSD or NVMe
  MinIO disk: 1 TB HDD
```

---

## 8.1 Identify the Root Filesystem

Show the mounted root filesystem.

```bash
findmnt /
```

Example output:

```text
TARGET SOURCE         FSTYPE OPTIONS
/      /dev/nvme0n1p2 ext4   rw,relatime
```

The parent disk of the root filesystem must not be used for MinIO.

In this example, `/dev/nvme0n1` is the parent disk of `/dev/nvme0n1p2`, so
`/dev/nvme0n1` is the boot disk.

---

## 8.2 List Candidate Data Disks

List whole disks without partitions.

```bash
lsblk -dn -o NAME,SIZE,ROTA,TYPE,MODEL,SERIAL
```

Look for the expected MinIO disk by size, rotational status, model, and serial
number.

---

## 8.3 Show Filesystems

Show existing filesystems.

```bash
lsblk -f
```

A candidate MinIO disk should not contain the active root filesystem.

If a disk already contains data, stop and confirm whether it should be reused,
wiped, or excluded.

---

## 8.4 Safe MinIO Disk Rule

A disk is a candidate MinIO disk only if all of the following are true:

```text
it is not the root disk
it is the expected size
it is not already mounted
it does not contain the OS filesystem
it matches expected rotational or model characteristics
the operator confirms it
```

Do not format any disk unless these checks pass.

---

## 8.5 Example Manual Confirmation

Use `lsblk` to inspect the machine.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

Use `findmnt` to identify the root filesystem.

```bash
findmnt /
```

Use `df` to confirm mounted filesystems.

```bash
df -h
```

Only after the boot disk and MinIO disk are clearly identified should a
formatting or mounting step be allowed.

---

# 9. Troubleshooting

This section covers common provisioning failures.

---

## 9.1 Cannot SSH into the Node

Check whether the node responds to ping.

```bash
ping <node-ip>
```

Check whether port 22 is reachable.

```bash
nc -vz <node-ip> 22
```

If ping works but SSH fails, check the SSH service from the node console.

```bash
sudo systemctl status ssh --no-pager
```

Check SSH logs.

```bash
sudo journalctl -u ssh --no-pager
```

Check cloud-init status.

```bash
cloud-init status --long
```

Common causes:

```text
cloud-init did not finish
OpenSSH server was not installed
wrong username
wrong SSH key
wrong static IP configuration
node is on the wrong network
```

---

## 9.2 Cloud-Init Did Not Finish

Check cloud-init status.

```bash
cloud-init status --long
```

Check cloud-init service logs.

```bash
sudo journalctl -u cloud-init --no-pager
```

Check final-stage cloud-init logs.

```bash
sudo journalctl -u cloud-final --no-pager
```

Cloud-init issues usually come from YAML formatting errors, package install
failures, network configuration errors, or commands in `runcmd` that failed.

---

## 9.3 Wrong Hostname or IP Address

Check the active hostname.

```bash
hostnamectl
```

Check IP addresses.

```bash
ip addr
```

Check routes.

```bash
ip route
```

Check netplan.

```bash
cat /etc/netplan/*.yaml
```

On the provisioning workstation, check the cloud-init file that was used.

```bash
grep -E "hostname|fqdn|addresses|gateway4|nameservers" \
  setup/cloud-config-arm64-01.yml
```

If the wrong cloud-init file was flashed, reflash the node with the correct file.

---

## 9.4 Wrong Disk Was Selected

If the wrong disk may have been selected, stop immediately before formatting,
mounting, or installing anything else.

Inspect all block devices.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

Identify the mounted root filesystem.

```bash
findmnt /
```

Check mounted filesystems.

```bash
df -h
```

Do not continue until the root disk and intended data disk are clearly
identified.

---

## 9.5 Raspberry Pi Does Not Boot from USB

Check the following:

1. The Raspberry Pi model supports USB boot.
2. The EEPROM or bootloader is current.
3. The USB drive is powered correctly.
4. The image was flashed to the correct device.
5. Ethernet is connected.
6. Power is stable.
7. A monitor shows boot activity.

For Raspberry Pi 4 and newer, USB boot should be handled through the Raspberry
Pi bootloader settings. Do not rely on disk-number tricks from the flashing host.

---

# 10. Recommended Current Workflows

This section summarizes the preferred provisioning path for each node type.

---

## 10.1 Raspberry Pi arm64 Node Workflow

Use this workflow for each Raspberry Pi node.

1. Select the correct `setup/cloud-config-arm64-NN.yml` file.
2. Download the Ubuntu Raspberry Pi `arm64` image.
3. Verify the image checksum.
4. Identify the target boot device with `diskutil list`.
5. Flash with `flash --userdata`.
6. Boot the Raspberry Pi.
7. Wait for cloud-init to finish.
8. SSH into the node.
9. Validate hostname, IP address, users, SSH, packages, and disks.
10. Confirm MinIO disk identity before formatting or mounting.
11. Add the node to the cluster only after validation succeeds.

---

## 10.2 amd64 Node Workflow

Use this workflow for each Intel or AMD bare-metal node.

1. Download the Ubuntu Server `amd64` ISO.
2. Verify the ISO checksum.
3. Create a bootable USB installer.
4. Boot the `amd64` machine from USB.
5. Install Ubuntu to the intended boot SSD or NVMe.
6. Do not install Ubuntu to the MinIO or data HDD.
7. Reboot.
8. SSH into the node.
9. Validate hostname, IP address, users, SSH, packages, and disks.
10. Confirm MinIO disk identity before formatting or mounting.
11. Add the node to the cluster only after validation succeeds.

---

## 10.3 When to Use Manual Install vs Autoinstall

Use manual installation when:

```text
the machine is new
the disk layout has not been validated
there are multiple disks
you are not sure which disk is the OS disk
you are not sure which disk is the MinIO disk
```

Use autoinstall only when:

```text
the machine model is known
the disk layout is known
the autoinstall storage configuration has been tested
the risk of wiping the wrong disk has been removed
```

---

# 11. Archived Historical Notes

This section preserves older notes for historical reference only.

The following old command pattern was previously used.

```bash
flash \
  --userdata setup/cloud-config-5.yml \
  ~/Downloads/ubuntu-20.04.2-preinstalled-server-arm64+raspi.img
```

Old Ubuntu 20.04 images and old `setup/cloud-config-N.yml` files should not be
used for new provisioning unless there is a specific compatibility reason.

Avoid old notes such as:

```text
switch to USB drive to trick flash
remove the card, reboot, and then add the card
```

Those notes may describe a one-time workaround, but they are not reliable
provisioning instructions.

---

# Appendix A: Useful Validation Commands

This appendix collects frequently used validation commands.

Show attached disks on macOS.

```bash
diskutil list
```

Show Ubuntu block devices.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

Show whole disks only.

```bash
lsblk -dn -o NAME,SIZE,ROTA,TYPE,MODEL,SERIAL
```

Show filesystems.

```bash
lsblk -f
```

Show the root filesystem.

```bash
findmnt /
```

Show mounted filesystems.

```bash
df -h
```

Show IP addresses.

```bash
ip addr
```

Show routes.

```bash
ip route
```

Show hostname and OS identity.

```bash
hostnamectl
```

Show Ubuntu version.

```bash
lsb_release -a
```

Show cloud-init status.

```bash
cloud-init status --long
```

Wait for cloud-init to finish.

```bash
cloud-init status --wait
```

Check SSH service.

```bash
systemctl status ssh --no-pager
```

Check SSH port reachability.

```bash
nc -vz <node-ip> 22
```

---

# Appendix B: Publishing Notes

This document is suitable for a GitHub Pages, MkDocs, or static site publishing
pipeline.

Recommended filename:

```text
docs/ubuntu-node-provisioning.md
```

For Jekyll-style GitHub Pages, this document already includes front matter.

For MkDocs, a matching navigation entry could look like this:

```yaml
nav:
  - Ubuntu Node Provisioning: ubuntu-node-provisioning.md
```

For plain GitHub rendering, no additional metadata is required.

---

# Appendix C: Source URLs

Ubuntu Raspberry Pi Noble release images:

```text
https://cdimage.ubuntu.com/releases/noble/release/
```

Ubuntu Server Noble amd64 ISO:

```text
https://releases.ubuntu.com/noble/
```

Hypriot flash releases:

```text
https://github.com/hypriot/flash/releases
```
