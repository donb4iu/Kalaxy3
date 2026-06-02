# Ubuntu Installation and Node Provisioning

This document describes how to install Ubuntu on both Raspberry Pi arm64 nodes
and amd64 bare-metal machines, apply cloud-init configuration, validate first
boot, and prepare each node for cluster use.

For new installs, prefer Ubuntu 24.04 LTS unless a specific compatibility reason
requires another release. Ubuntu provides Raspberry Pi preinstalled server images
for modern Pi boards, and standard Ubuntu Server ISO images for amd64 machines.
The Raspberry Pi preinstalled images include a cloud-init seed on the boot
partition. For amd64 installs, cloud-init can be provided through autoinstall,
NoCloud seed media, or post-install provisioning.

## References:

- Ubuntu Raspberry Pi images
- Ubuntu Server amd64 ISO images
- cloud-init documentation
- Ubuntu autoinstall documentation
- Hypriot flash utility

## Target Environment

Supported node types:

| Node Type | Architecture | Install Method | Boot Media |
|---|---:|---|---|
| Raspberry Pi 4 / Pi 5 | arm64 | Preinstalled Raspberry Pi image + cloud-init | USB SSD or SD card |
| Intel / AMD bare metal | amd64 | Ubuntu Server ISO or autoinstall | SSD / NVMe |

Recommended OS:

```text
Ubuntu 24.04 LTS Server

arm64-01  Raspberry Pi
arm64-02  Raspberry Pi
arm64-03  Raspberry Pi
arm64-04  Raspberry Pi
arm64-05  Raspberry Pi

amd64-01  Intel / AMD bare metal
amd64-02  Intel / AMD bare metal
amd64-03  Intel / AMD bare metal