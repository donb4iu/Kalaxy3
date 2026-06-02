---
title: Ubuntu Node Provisioning
summary: Mixed Raspberry Pi arm64 cloud-init and Intel amd64 Ansible provisioning for a k3s cluster
---

# Ubuntu Node Provisioning for the New k3s Cluster

This guide provisions five Raspberry Pi `arm64` nodes and three Intel `amd64`
nodes for a new k3s Kubernetes cluster.

The important split is:

```text
arm64 Raspberry Pi nodes -> Ubuntu Raspberry Pi image + cloud-init
amd64 Intel nodes        -> Ubuntu Server ISO + Ansible after first boot
```

The Intel machines are intentionally **not** using Ubuntu ISO autoinstall seed
media here. Install Ubuntu Server normally from the ISO, get SSH working, then
run Ansible from your Mac or admin workstation.

All commands are in fenced blocks so browser-rendered Markdown keeps them easy
to swipe-copy.

---

## 1. Final Node Map

```text
arm64-01  192.168.2.51  Raspberry Pi
arm64-02  192.168.2.52  Raspberry Pi
arm64-03  192.168.2.53  Raspberry Pi
arm64-04  192.168.2.54  Raspberry Pi
arm64-05  192.168.2.55  Raspberry Pi

amd64-01  192.168.2.61  Intel / AMD bare metal
amd64-02  192.168.2.62  Intel / AMD bare metal
amd64-03  192.168.2.63  Intel / AMD bare metal

nfs-server 192.168.2.7
```

Expected OS:

```text
Ubuntu 24.04 LTS Server
```

Cluster prep common to both architectures:

```text
SSH key login only
root SSH login disabled
password SSH login disabled
users pi and dbuddenbaum created with passwordless sudo
open-iscsi installed and enabled
nfs-common installed
parted and xfsprogs installed
/etc/hosts populated with every cluster node
/mnt/minio prepared only when exactly one safe non-root rotational data disk is detected
```

---

## 2. Repository Layout

Use this layout:

```text
setup/
  cloud-config-arm64-01.yml
  cloud-config-arm64-02.yml
  cloud-config-arm64-03.yml
  cloud-config-arm64-04.yml
  cloud-config-arm64-05.yml

ansible/
  inventory.yml
  configure-amd64-nodes.yml
  files/
    prepare-minio-disk.sh
  templates/
    50-k3s-uplink.yaml.j2
    hosts.j2
```

---

## 3. Raspberry Pi arm64 Provisioning

Use cloud-init for the Raspberry Pi nodes because the Ubuntu Raspberry Pi image
is a preinstalled image and the `flash --userdata` flow works cleanly.

### 3.1 Install the flash Tool on macOS

```bash
curl -LO "https://github.com/hypriot/flash/releases/download/2.5.1/flash"
```

```bash
chmod +x flash
```

```bash
sudo mv flash /usr/local/bin/flash
```

```bash
flash --version
```

---

### 3.2 Download the Ubuntu Raspberry Pi Image

```bash
mkdir -p ~/Downloads/ubuntu-rpi
```

```bash
cd ~/Downloads/ubuntu-rpi
```

```bash
curl -LO "https://cdimage.ubuntu.com/releases/noble/release/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz"
```

```bash
curl -LO "https://cdimage.ubuntu.com/releases/noble/release/SHA256SUMS"
```

---

### 3.3 Verify the Raspberry Pi Image

```bash
shasum -a 256 ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

```bash
grep "ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz" SHA256SUMS
```

The two checksums must match before flashing.

---

### 3.4 Identify the Target Boot Device on macOS

List disks before inserting the SD card or USB SSD.

```bash
diskutil list
```

Insert the target boot device and list disks again.

```bash
diskutil list
```

The new disk is the target. Do not assume it is `/dev/disk3`.

---

### 3.5 Use the Correct arm64 Cloud-Init File

```text
setup/cloud-config-arm64-01.yml -> arm64-01 -> 192.168.2.51
setup/cloud-config-arm64-02.yml -> arm64-02 -> 192.168.2.52
setup/cloud-config-arm64-03.yml -> arm64-03 -> 192.168.2.53
setup/cloud-config-arm64-04.yml -> arm64-04 -> 192.168.2.54
setup/cloud-config-arm64-05.yml -> arm64-05 -> 192.168.2.55
```

Before flashing, check the file identity.

```bash
grep -E "hostname|192\.168\.2|ssh_authorized_keys" setup/cloud-config-arm64-01.yml
```

---

### 3.6 Flash arm64-01

```bash
flash \
  --userdata setup/cloud-config-arm64-01.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

Only answer `y` when the displayed target disk is definitely the Pi boot device.

---

### 3.7 Flash arm64-02

```bash
flash \
  --userdata setup/cloud-config-arm64-02.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

---

### 3.8 Flash arm64-03

```bash
flash \
  --userdata setup/cloud-config-arm64-03.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

---

### 3.9 Flash arm64-04

```bash
flash \
  --userdata setup/cloud-config-arm64-04.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

---

### 3.10 Flash arm64-05

```bash
flash \
  --userdata setup/cloud-config-arm64-05.yml \
  ~/Downloads/ubuntu-rpi/ubuntu-24.04.4-preinstalled-server-arm64+raspi.img.xz
```

---

## 4. Intel amd64 Provisioning with Ansible

Use this flow for the three Intel machines:

```text
Install Ubuntu Server from ISO manually
Create temporary dbuddenbaum sudo user if the installer did not create it
Enable SSH
Confirm the machine is reachable
Run Ansible from your Mac or admin workstation
```

Ansible applies the same effective configuration as the uploaded `amd64-01`,
`amd64-02`, and `amd64-03` cloud-init examples, but without requiring NoCloud
seed media.

---

### 4.1 Install Ubuntu Server on Each Intel Node

Install Ubuntu Server 24.04 LTS from the normal ISO.

During install, create this user when possible:

```text
dbuddenbaum
```

Enable OpenSSH Server during the install.

Use DHCP during the ISO install if that is easier. Ansible will later set the
final static IPs.

---

### 4.2 If Needed, Create the Admin User from the Console

Run this only if the ISO install did not create `dbuddenbaum`.

```bash
sudo adduser dbuddenbaum
```

```bash
sudo usermod -aG sudo dbuddenbaum
```

```bash
sudo systemctl enable --now ssh
```

---

### 4.3 Install Ansible on macOS

```bash
python3 -m pip install --user ansible-core
```

```bash
python3 -m pip install --user ansible-posix
```

If `ansible-playbook` is not found, add the Python user binary directory to your
shell path.

```bash
echo 'export PATH="$HOME/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
```

```bash
source ~/.zshrc
```

Check Ansible.

```bash
ansible --version
```

---

### 4.4 Put Your SSH Key on Each Fresh Intel Node

Replace the IPs below with the temporary DHCP IPs if the nodes are not already
using `192.168.2.61`, `192.168.2.62`, and `192.168.2.63`.

```bash
ssh-copy-id dbuddenbaum@192.168.2.61
```

```bash
ssh-copy-id dbuddenbaum@192.168.2.62
```

```bash
ssh-copy-id dbuddenbaum@192.168.2.63
```

Test SSH.

```bash
ssh dbuddenbaum@192.168.2.61 hostnamectl
```

```bash
ssh dbuddenbaum@192.168.2.62 hostnamectl
```

```bash
ssh dbuddenbaum@192.168.2.63 hostnamectl
```

---

### 4.5 If DHCP IPs Are Different, Edit the Inventory First

Edit this file:

```text
ansible/inventory.yml
```

For each host, `ansible_host` is the address Ansible connects to now.
`node_ip` is the final static address Ansible writes into netplan.

Example when `amd64-01` is temporarily at `192.168.2.145`:

```yaml
amd64-01:
  ansible_host: 192.168.2.145
  node_ip: 192.168.2.61
  node_hostname: amd64-01
```

After Ansible applies netplan, future SSH should use `192.168.2.61`.

---

### 4.6 Check Ansible Connectivity

```bash
cd ansible
```

```bash
ansible -i inventory.yml amd64_nodes -m ping
```

---

### 4.7 Run the amd64 Node Provisioning Playbook

```bash
ansible-playbook -i inventory.yml configure-amd64-nodes.yml
```

The playbook runs one Intel node at a time because it changes networking.

---

### 4.8 Run One Node Only

Use this when testing the first Intel node.

```bash
ansible-playbook -i inventory.yml configure-amd64-nodes.yml --limit amd64-01
```

Then run the next node.

```bash
ansible-playbook -i inventory.yml configure-amd64-nodes.yml --limit amd64-02
```

Then run the third node.

```bash
ansible-playbook -i inventory.yml configure-amd64-nodes.yml --limit amd64-03
```

---

## 5. Intel amd64 Ansible Inventory

Save this as:

```text
ansible/inventory.yml
```

```yaml
all:
  children:
    amd64_nodes:
      hosts:
        amd64-01:
          ansible_host: 192.168.2.61
          node_ip: 192.168.2.61
          node_hostname: amd64-01
        amd64-02:
          ansible_host: 192.168.2.62
          node_ip: 192.168.2.62
          node_hostname: amd64-02
        amd64-03:
          ansible_host: 192.168.2.63
          node_ip: 192.168.2.63
          node_hostname: amd64-03
      vars:
        ansible_user: dbuddenbaum
        ansible_become: true
        ansible_python_interpreter: /usr/bin/python3
        node_gateway: 192.168.2.1
        node_dns:
        - 192.168.2.1
        - 1.1.1.1
        - 8.8.8.8
        ethernet_match_name: e*
        prepare_minio_disk: true
        k3s_users:
        - pi
        - dbuddenbaum
        k3s_ssh_authorized_keys:
        - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCft3wmZVTlcGwUvg5SYRYUcpifwpV+lBX6gOV3qmn5Bj2tAHT03QtZe4qsxwMShiNkUihsULzMwtHZ1U07MPHOG+QOi17QsHM2V1il47AGTaI59GQhf07q0wi2dOONt+hyzbTSlej3S0W78tvIhLgXLcGXRJc76RUzL96Y2t3/0wcCo7XnZUNp3q2+Vwlgg3TtfF3y5/IZ7+1Uu8rqQgrmKyTRV58LKh8ChhClRBAY9wlxcoJByg0s1teOWMOoO0JDHeSXkLCV+YO1OUYs1z/L/w7nghf3Ap8Ghz0jrl2q1WkMfR625ptXnoowvtdDp3fziv9ry3TEJ+Yf2Yd5Q4YEj8KviF3zK1YWhIZLylIJRmhv33VYMKFAkCIz2AiBcpSGCzJZoMdWFxEG3n6tru451AoXtAyeVFSvXzBKOKdXZMtRGz6JaCX8XEy4soIHWlf/7xVqmsbrFTcAmy/UoQcqW/rlAv8NhXd6pHMZ+DMTLVIzUJ2BXUs+H5+2BAkWUCmhDfvOiQjWPxic5DgHGjHg66uJ4fknRGf228/3sIRUZNaehxXRoSYwhaXu0Gw57vMh7NsEyCNmBbAC/ZSLCU4j0TiCVa1VSf3YTtJlw+YTZroXe73r9qLKyVplBRhK1hMxgV5EsXXmMPxHtJqLWd1J66NyeYhn445h+/yVGvPeLw== donbuddenbaum@donbs-iMac
```

---

## 6. Intel amd64 Ansible Playbook

Save this as:

```text
ansible/configure-amd64-nodes.yml
```

```yaml
---
- name: Configure Intel amd64 nodes for the k3s cluster
  hosts: amd64_nodes
  become: true
  gather_facts: true
  serial: 1

  tasks:
    - name: Confirm this playbook is only running on amd64 hosts
      ansible.builtin.assert:
        that:
          - ansible_architecture in ['x86_64', 'amd64']
        fail_msg: "This host is not amd64/x86_64. Stop before applying Intel node settings."

    - name: Set hostname
      ansible.builtin.hostname:
        name: "{{ node_hostname }}"

    - name: Set timezone
      ansible.builtin.command: timedatectl set-timezone America/Chicago
      changed_when: false

    - name: Ensure locale exists
      ansible.builtin.command: locale-gen en_US.UTF-8
      changed_when: false

    - name: Update apt cache and upgrade packages
      ansible.builtin.apt:
        update_cache: true
        upgrade: dist
        cache_valid_time: 3600

    - name: Install base cluster packages
      ansible.builtin.apt:
        name:
          - open-iscsi
          - nfs-common
          - parted
          - xfsprogs
          - python3
          - sudo
          - openssh-server
        state: present

    - name: Ensure local users exist
      ansible.builtin.user:
        name: "{{ item }}"
        groups:
          - users
          - sudo
        append: true
        shell: /bin/bash
        password_lock: true
        create_home: true
      loop: "{{ k3s_users }}"

    - name: Install authorized SSH keys
      ansible.posix.authorized_key:
        user: "{{ item.0 }}"
        key: "{{ item.1 }}"
        state: present
      loop: "{{ k3s_users | product(k3s_ssh_authorized_keys) | list }}"

    - name: Allow passwordless sudo for cluster users
      ansible.builtin.copy:
        dest: "/etc/sudoers.d/90-k3s-users"
        owner: root
        group: root
        mode: '0440'
        validate: 'visudo -cf %s'
        content: |
          pi ALL=(ALL) NOPASSWD:ALL
          dbuddenbaum ALL=(ALL) NOPASSWD:ALL

    - name: Disable SSH password login and root login
      ansible.builtin.copy:
        dest: /etc/ssh/sshd_config.d/99-k3s-hardening.conf
        owner: root
        group: root
        mode: '0644'
        content: |
          PasswordAuthentication no
          PermitRootLogin no
      notify: Restart ssh

    - name: Write cluster hosts file
      ansible.builtin.template:
        src: hosts.j2
        dest: /etc/hosts
        owner: root
        group: root
        mode: '0644'

    - name: Write static netplan configuration
      ansible.builtin.template:
        src: 50-k3s-uplink.yaml.j2
        dest: /etc/netplan/50-k3s-uplink.yaml
        owner: root
        group: root
        mode: '0600'
      notify: Apply netplan

    - name: Enable and start iSCSI service
      ansible.builtin.service:
        name: iscsid
        enabled: true
        state: started

    - name: Install safe MinIO disk preparation script
      ansible.builtin.copy:
        src: prepare-minio-disk.sh
        dest: /usr/local/sbin/prepare-minio-disk.sh
        owner: root
        group: root
        mode: '0755'

    - name: Prepare MinIO disk when enabled
      ansible.builtin.command: /usr/local/sbin/prepare-minio-disk.sh
      register: minio_prepare
      changed_when: "'Formatting' in minio_prepare.stderr or 'Creating XFS partition' in minio_prepare.stderr"
      when: prepare_minio_disk | bool

    - name: Show final validation summary
      ansible.builtin.debug:
        msg:
          - "Configured {{ node_hostname }} at {{ node_ip }}"
          - "Run: ssh dbuddenbaum@{{ node_ip }} 'hostnamectl && lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL'"

  handlers:
    - name: Restart ssh
      ansible.builtin.service:
        name: ssh
        state: restarted

    - name: Apply netplan
      ansible.builtin.command: netplan apply
      async: 45
      poll: 0
      changed_when: true
```

---

## 7. Important MinIO Disk Safety Rule

The MinIO prep script refuses to format when disk selection is ambiguous.

It only proceeds when it finds exactly one disk that is:

```text
not the root disk
not removable
rotational
at least 800 GB
not already mounted as the OS filesystem
```

Before running provisioning, check each node from the console or SSH.

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

```bash
findmnt /
```

```bash
df -h
```

If a node has more than one possible MinIO disk, set this in the inventory before
running Ansible:

```yaml
prepare_minio_disk: false
```

Then prepare the data disk manually after confirming the disk identity.

---

## 8. First-Boot Validation for Every Node

Run these after each Pi first boot and after each Intel Ansible run.

```bash
ssh dbuddenbaum@192.168.2.51 hostnamectl
```

```bash
ssh dbuddenbaum@192.168.2.61 hostnamectl
```

```bash
ssh dbuddenbaum@192.168.2.61 cloud-init status --long || true
```

```bash
ssh dbuddenbaum@192.168.2.61 ip addr
```

```bash
ssh dbuddenbaum@192.168.2.61 ip route
```

```bash
ssh dbuddenbaum@192.168.2.61 lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

```bash
ssh dbuddenbaum@192.168.2.61 systemctl status ssh --no-pager
```

```bash
ssh dbuddenbaum@192.168.2.61 systemctl status iscsid --no-pager
```

---

## 9. k3s Readiness Checks Before Joining Nodes

Run these checks on all eight nodes before installing k3s.

```bash
ansible -i ansible/inventory.yml amd64_nodes -m command -a "hostnamectl"
```

```bash
ansible -i ansible/inventory.yml amd64_nodes -m command -a "lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL"
```

```bash
ansible -i ansible/inventory.yml amd64_nodes -m command -a "systemctl is-active ssh"
```

```bash
ansible -i ansible/inventory.yml amd64_nodes -m command -a "systemctl is-active iscsid"
```

---

## 10. Troubleshooting

### 10.1 Ansible Cannot Connect

```bash
ssh -v dbuddenbaum@192.168.2.61
```

```bash
nc -vz 192.168.2.61 22
```

If the node is still on DHCP, update `ansible_host` in `ansible/inventory.yml`.

---

### 10.2 Static IP Did Not Apply

```bash
sudo netplan generate
```

```bash
sudo netplan apply
```

```bash
ip addr
```

```bash
ip route
```

---

### 10.3 MinIO Disk Prep Refused to Run

This is usually good. It means disk selection was not safe enough.

```bash
sudo /usr/local/sbin/prepare-minio-disk.sh
```

```bash
lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
```

```bash
findmnt /
```

Set `prepare_minio_disk: false` until the disk is confirmed.

---

## Appendix A. arm64 Cloud-Init Files Generated With This Package

```text
setup/cloud-config-arm64-01.yml
setup/cloud-config-arm64-02.yml
setup/cloud-config-arm64-03.yml
setup/cloud-config-arm64-04.yml
setup/cloud-config-arm64-05.yml
```

Each file sets the node hostname, static IP, SSH users, authorized keys, cluster
hosts file, base packages, iSCSI service, and safe MinIO disk prep script.

---

## Appendix B. Generated amd64 Files

```text
ansible/inventory.yml
ansible/configure-amd64-nodes.yml
ansible/templates/hosts.j2
ansible/templates/50-k3s-uplink.yaml.j2
ansible/files/prepare-minio-disk.sh
```
