# Ubuntu Installation and Node Provisioning

This document describes how to provision the Ubuntu nodes for the Kalaxy3 / homelab Kubernetes cluster.

It supports both:

- **ARM64 Raspberry Pi nodes**, using Ubuntu preinstalled Raspberry Pi server images and `flash --userdata`
- **AMD64 bare-metal nodes**, using Ubuntu Server autoinstall with NoCloud `user-data` and `meta-data`

The important distinction is that the Raspberry Pi image is a preinstalled disk image, while the normal AMD64 Ubuntu Server download is an installer ISO. That means the ARM and AMD workflows both use cloud-init-style YAML, but they are consumed differently.

---

## 1. Repository layout

This document assumes the repository contains a `setup/` directory with one cloud-init file per node.

```text
setup/
├── cloud-config-arm64-01.yml
├── cloud-config-arm64-02.yml
├── cloud-config-arm64-03.yml
├── cloud-config-arm64-04.yml
├── cloud-config-arm64-05.yml
├── cloud-config-amd64-01.yml
├── cloud-config-amd64-02.yml
└── cloud-config-amd64-03.yml
```

The ARM64 files are used directly by the Raspberry Pi flashing process.

The AMD64 files are used as Ubuntu autoinstall NoCloud `user-data` files.

---

## 2. Node inventory

Adjust names and IP addresses if the actual hardware differs.

| Node | Architecture | Intended role | Example IP |
|---|---:|---|---:|
| arm64-01 | ARM64 Raspberry Pi | Kubernetes worker/control candidate | 192.168.2.51 |
| arm64-02 | ARM64 Raspberry Pi | Kubernetes worker | 192.168.2.52 |
| arm64-03 | ARM64 Raspberry Pi | Kubernetes worker | 192.168.2.53 |
| arm64-04 | ARM64 Raspberry Pi | Kubernetes worker | 192.168.2.54 |
| arm64-05 | ARM64 Raspberry Pi | Kubernetes worker | 192.168.2.55 |
| amd64-01 | AMD64 bare metal | Kubernetes node / GPU-capable | 192.168.2.61 |
| amd64-02 | AMD64 bare metal | Kubernetes node / GPU-capable | 192.168.2.62 |
| amd64-03 | AMD64 bare metal | Kubernetes node / GPU-capable | 192.168.2.63 |

---

## 3. Install required tools on macOS

The examples below assume the commands are being run from macOS.

Install Homebrew if it is not already installed.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Install helper tools.

```bash
brew install coreutils xz wget
```

Install the Raspberry Pi flashing tool.

```bash
curl -L https://raw.githubusercontent.com/hypriot/flash/master/$(uname -s)/flash   -o /usr/local/bin/flash
```

Make it executable.

```bash
chmod +x /usr/local/bin/flash
```

Confirm that `flash` is available.

```bash
flash --help
```

---

## 4. Download Ubuntu images

Create a local download directory.

```bash
mkdir -p ~/Downloads/ubuntu-rpi
mkdir -p ~/Downloads/ubuntu-amd64
```

Download the Ubuntu Raspberry Pi ARM64 preinstalled image.

```bash
cd ~/Downloads/ubuntu-rpi
```

```bash
wget https://cdimage.ubuntu.com/releases/24.04.4/release/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

Download the Ubuntu Server AMD64 installer ISO.

```bash
cd ~/Downloads/ubuntu-amd64
```

```bash
wget https://releases.ubuntu.com/24.04.4/ubuntu-24.04.4-live-server-amd64.iso
```

The ARM64 file is a preinstalled disk image.

The AMD64 file is an installer ISO.

That difference is why the provisioning commands are different.

---

## 5. ARM64 Raspberry Pi provisioning model

For Raspberry Pi nodes, use the Ubuntu preinstalled server image and inject each node's cloud-init file with `flash --userdata`.

This works because the Raspberry Pi image is already a bootable installed operating system image. The `flash` tool writes the image to the target disk and injects the selected cloud-init config.

### 5.1 List disks before inserting the target SSD or SD card

```bash
diskutil list
```

Insert the target SSD or SD card, then list disks again.

```bash
diskutil list
```

Identify the new external disk.

Example:

```text
/dev/disk3 (external, physical)
```

Do not use `/dev/disk0`. That is normally the Mac internal disk.

### 5.2 Flash arm64-01

```bash
flash   --userdata setup/cloud-config-arm64-01.yml   ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

### 5.3 Flash arm64-02

```bash
flash   --userdata setup/cloud-config-arm64-02.yml   ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

### 5.4 Flash arm64-03

```bash
flash   --userdata setup/cloud-config-arm64-03.yml   ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

### 5.5 Flash arm64-04

```bash
flash   --userdata setup/cloud-config-arm64-04.yml   ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

### 5.6 Flash arm64-05

```bash
flash   --userdata setup/cloud-config-arm64-05.yml   ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

### 5.7 Boot each Raspberry Pi

After flashing:

1. Eject the disk from macOS.
2. Insert it into the Raspberry Pi.
3. Connect Ethernet.
4. Power on the Pi.
5. Wait for first boot and cloud-init to complete.

Cloud-init may take several minutes during first boot.

---

## 6. AMD64 bare-metal provisioning model

For AMD64 nodes, do **not** use the Raspberry Pi `flash --userdata` command against the AMD64 installer ISO.

This is the wrong model:

```bash
flash   --userdata setup/cloud-config-amd64-01.yml   ~/Downloads/ubuntu-amd64/ubuntu-24.04.4-live-server-amd64.iso
```

The normal AMD64 Ubuntu Server image is an installer ISO, not a preinstalled disk image. The installer needs to consume cloud-init through Ubuntu autoinstall using the NoCloud datasource.

The AMD64 files are still used, but they are used as NoCloud `user-data`.

---

## 7. AMD64 option A: installer ISO plus seed USB

This is the simplest and clearest AMD64 method.

You boot the machine from the normal Ubuntu Server ISO, and you attach a second USB drive containing the autoinstall seed data.

The seed USB contains:

```text
user-data
meta-data
```

For each AMD64 node, the `user-data` file is copied from the matching generated cloud config.

### 7.1 Create a seed directory for amd64-01

Run this from the repository root.

```bash
mkdir -p build/nocloud/amd64-01
```

Copy the node-specific config into the NoCloud seed directory.

```bash
cp setup/cloud-config-amd64-01.yml build/nocloud/amd64-01/user-data
```

Create the metadata file.

```bash
cat > build/nocloud/amd64-01/meta-data <<'EOF'
instance-id: amd64-01
local-hostname: amd64-01
EOF
```

### 7.2 Create a seed directory for amd64-02

```bash
mkdir -p build/nocloud/amd64-02
```

```bash
cp setup/cloud-config-amd64-02.yml build/nocloud/amd64-02/user-data
```

```bash
cat > build/nocloud/amd64-02/meta-data <<'EOF'
instance-id: amd64-02
local-hostname: amd64-02
EOF
```

### 7.3 Create a seed directory for amd64-03

```bash
mkdir -p build/nocloud/amd64-03
```

```bash
cp setup/cloud-config-amd64-03.yml build/nocloud/amd64-03/user-data
```

```bash
cat > build/nocloud/amd64-03/meta-data <<'EOF'
instance-id: amd64-03
local-hostname: amd64-03
EOF
```

---

## 8. Write a NoCloud seed USB on macOS

Use a small USB drive for the seed media.

The seed drive can be very small. It only needs to hold `user-data` and `meta-data`.

### 8.1 Identify the seed USB

Before inserting the seed USB:

```bash
diskutil list
```

Insert the seed USB and run:

```bash
diskutil list
```

Identify the new external disk.

Example:

```text
/dev/disk4 (external, physical)
```

### 8.2 Erase the seed USB

Replace `/dev/disk4` with the actual seed USB device.

```bash
diskutil eraseDisk FAT32 CIDATA MBR /dev/disk4
```

The volume name `CIDATA` is important. NoCloud commonly expects the seed volume label to be `CIDATA`.

### 8.3 Mount location

After formatting, macOS should mount it here:

```text
/Volumes/CIDATA
```

Confirm it mounted.

```bash
ls /Volumes/CIDATA
```

### 8.4 Copy amd64-01 seed files

To prepare the seed USB for `amd64-01`:

```bash
cp build/nocloud/amd64-01/user-data /Volumes/CIDATA/user-data
cp build/nocloud/amd64-01/meta-data /Volumes/CIDATA/meta-data
sync
diskutil eject /Volumes/CIDATA
```

### 8.5 Copy amd64-02 seed files

To reuse the same seed USB for `amd64-02`, reinsert it and replace the files.

```bash
cp build/nocloud/amd64-02/user-data /Volumes/CIDATA/user-data
cp build/nocloud/amd64-02/meta-data /Volumes/CIDATA/meta-data
sync
diskutil eject /Volumes/CIDATA
```

### 8.6 Copy amd64-03 seed files

To reuse the same seed USB for `amd64-03`, reinsert it and replace the files.

```bash
cp build/nocloud/amd64-03/user-data /Volumes/CIDATA/user-data
cp build/nocloud/amd64-03/meta-data /Volumes/CIDATA/meta-data
sync
diskutil eject /Volumes/CIDATA
```

---

## 9. Boot AMD64 installer with NoCloud autoinstall

For each AMD64 machine:

1. Insert the Ubuntu Server AMD64 installer USB.
2. Insert the NoCloud seed USB labeled `CIDATA`.
3. Boot the machine from the Ubuntu Server installer USB.
4. At the GRUB menu, edit the boot entry.
5. Add the autoinstall datasource argument to the Linux command line.

The kernel command line should include:

```text
autoinstall ds=nocloud
```

Depending on the installer behavior, this variant may be needed:

```text
autoinstall ds=nocloud;s=/cdrom/
```

Or this variant if the seed is mounted separately:

```text
autoinstall ds=nocloud;s=file:///cdrom/
```

The exact mount path can vary depending on the machine and installer environment. The key idea is that the installer must see a NoCloud datasource containing:

```text
user-data
meta-data
```

on the `CIDATA` volume.

---

## 10. AMD64 option B: serve NoCloud data over HTTP

Instead of using a second USB seed drive, you can serve each node's `user-data` and `meta-data` over HTTP from another machine on the LAN.

From the repository root, serve the NoCloud directory.

```bash
cd build/nocloud/amd64-01
```

```bash
python3 -m http.server 8080
```

Then boot the AMD64 installer with:

```text
autoinstall ds=nocloud-net;s=http://192.168.2.100:8080/
```

Replace `192.168.2.100` with the IP address of the machine running the HTTP server.

For `amd64-02`:

```bash
cd build/nocloud/amd64-02
```

```bash
python3 -m http.server 8080
```

Use:

```text
autoinstall ds=nocloud-net;s=http://192.168.2.100:8080/
```

For `amd64-03`:

```bash
cd build/nocloud/amd64-03
```

```bash
python3 -m http.server 8080
```

Use:

```text
autoinstall ds=nocloud-net;s=http://192.168.2.100:8080/
```

Only run one of these simple HTTP servers at a time on the same port.

---

## 11. AMD64 option C: build a custom autoinstall ISO

This option embeds the NoCloud data directly into a custom Ubuntu Server ISO.

Use this if you want one bootable ISO per AMD64 node and do not want a second seed USB.

High-level flow:

1. Extract the Ubuntu Server ISO.
2. Add `user-data` and `meta-data`.
3. Modify the boot menu to include `autoinstall ds=nocloud`.
4. Rebuild the ISO.
5. Write the rebuilt ISO to USB.

This is cleaner for repeat installs, but more work than the seed USB approach.

For this cluster, the recommended path is:

```text
ARM64 Raspberry Pi nodes: flash --userdata
AMD64 bare-metal nodes: Ubuntu autoinstall with NoCloud seed USB
```

---

## 12. Verify first boot

After a node boots, wait a few minutes for cloud-init to finish.

Then SSH into the node.

Example for `arm64-01`:

```bash
ssh dbuddenbaum@192.168.2.51
```

Example for `amd64-01`:

```bash
ssh dbuddenbaum@192.168.2.61
```

Check hostname.

```bash
hostnamectl
```

Check cloud-init status.

```bash
cloud-init status --long
```

Check storage devices.

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
```

Check network address.

```bash
ip addr
```

Check default route.

```bash
ip route
```

---

## 13. Validate MinIO data disk selection

The node configs should avoid assuming that Linux drive order is stable.

Do not assume:

```text
/dev/sda
/dev/sdb
/dev/nvme0n1
```

will always appear in the same order.

The safer pattern is to detect the intended MinIO disk by durable characteristics such as:

- rotational HDD status
- size
- exclusion of the boot disk
- explicit operator confirmation where needed

After first boot, confirm the intended MinIO disk.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL
```

Look for the 1 TB HDD intended for MinIO.

Check mounted filesystems.

```bash
df -h
```

Check block IDs.

```bash
sudo blkid
```

---

## 14. Confirm package installation

Check that common packages were installed.

```bash
which curl
which wget
which git
which jq
which yq
```

Check NFS and iSCSI support.

```bash
systemctl status open-iscsi --no-pager
```

```bash
dpkg -l | grep -E 'nfs-common|open-iscsi'
```

---

## 15. Confirm SSH access

From the Mac or admin workstation, test each node.

```bash
ssh dbuddenbaum@192.168.2.51 hostname
ssh dbuddenbaum@192.168.2.52 hostname
ssh dbuddenbaum@192.168.2.53 hostname
ssh dbuddenbaum@192.168.2.54 hostname
ssh dbuddenbaum@192.168.2.55 hostname
ssh dbuddenbaum@192.168.2.61 hostname
ssh dbuddenbaum@192.168.2.62 hostname
ssh dbuddenbaum@192.168.2.63 hostname
```

---

## 16. Confirm GPU visibility on AMD64 nodes

On AMD64 nodes with NVIDIA GPUs, confirm PCI visibility first.

```bash
lspci | grep -i nvidia
```

Check recommended Ubuntu drivers.

```bash
ubuntu-drivers devices
```

Install the recommended driver if the cloud-init file did not already do it.

Example:

```bash
sudo apt update
sudo apt install -y nvidia-driver-580
sudo reboot
```

After reboot:

```bash
nvidia-smi
```

---

## 17. Troubleshooting

### 17.1 Disk Utility shows only ESP or tiny partitions

In macOS Disk Utility:

1. Click **View**.
2. Select **Show All Devices**.
3. Select the top-level physical disk.
4. Erase the whole device, not just the tiny `ESP` partition.

Terminal is often clearer.

```bash
diskutil list
```

Erase the correct external device only.

Example:

```bash
diskutil eraseDisk ExFAT USBSTICK GPT /dev/disk3
```

Do not erase `/dev/disk0`.

### 17.2 Cloud-init still running

Check status.

```bash
cloud-init status --long
```

Watch logs.

```bash
sudo tail -f /var/log/cloud-init.log
```

```bash
sudo tail -f /var/log/cloud-init-output.log
```

### 17.3 SSH does not work

Check whether the node responds.

```bash
ping 192.168.2.51
```

Check SSH port.

```bash
nc -vz 192.168.2.51 22
```

Try verbose SSH.

```bash
ssh -vvv dbuddenbaum@192.168.2.51
```

### 17.4 AMD64 installer does not pick up autoinstall

Confirm the seed USB has exactly these files at the root:

```text
user-data
meta-data
```

Confirm the volume label is:

```text
CIDATA
```

On macOS, confirm with:

```bash
diskutil list
```

Recreate the seed USB if needed.

```bash
diskutil eraseDisk FAT32 CIDATA MBR /dev/disk4
```

Then copy files again.

```bash
cp build/nocloud/amd64-01/user-data /Volumes/CIDATA/user-data
cp build/nocloud/amd64-01/meta-data /Volumes/CIDATA/meta-data
sync
diskutil eject /Volumes/CIDATA
```

### 17.5 AMD64 installer asks questions instead of running unattended

That usually means one of these is wrong:

- `autoinstall` was not added to the boot command line
- the NoCloud datasource was not found
- `user-data` is invalid
- `meta-data` is missing
- the seed volume is not labeled `CIDATA`
- the YAML file is cloud-init only but not valid Ubuntu autoinstall format

Validate YAML before trying again.

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

for path in Path("setup").glob("cloud-config-*.yml"):
    with path.open("r", encoding="utf-8") as file:
        yaml.safe_load(file)
    print(f"OK: {path}")
PY
```

If `PyYAML` is missing:

```bash
python3 -m pip install pyyaml
```

---

## 18. Summary

Use this workflow:

```text
ARM64 Raspberry Pi:
  Ubuntu preinstalled Raspberry Pi image
  flash --userdata setup/cloud-config-arm64-XX.yml image.img.xz

AMD64 bare metal:
  Ubuntu Server AMD64 installer ISO
  Ubuntu autoinstall
  NoCloud seed USB or NoCloud HTTP datasource
  setup/cloud-config-amd64-XX.yml copied as user-data
```

The AMD64 cloud-init files are not unused. They are used differently because AMD64 installation normally starts from an installer ISO, while the Raspberry Pi installation starts from a preinstalled disk image.

---

## 19. Quick command reference

### ARM64

```bash
flash   --userdata setup/cloud-config-arm64-01.yml   ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

### AMD64 seed USB preparation

```bash
mkdir -p build/nocloud/amd64-01
cp setup/cloud-config-amd64-01.yml build/nocloud/amd64-01/user-data
cat > build/nocloud/amd64-01/meta-data <<'EOF'
instance-id: amd64-01
local-hostname: amd64-01
EOF
```

```bash
diskutil eraseDisk FAT32 CIDATA MBR /dev/disk4
```

```bash
cp build/nocloud/amd64-01/user-data /Volumes/CIDATA/user-data
cp build/nocloud/amd64-01/meta-data /Volumes/CIDATA/meta-data
sync
diskutil eject /Volumes/CIDATA
```

### AMD64 installer boot argument

```text
autoinstall ds=nocloud
```

or:

```text
autoinstall ds=nocloud-net;s=http://192.168.2.100:8080/
```
