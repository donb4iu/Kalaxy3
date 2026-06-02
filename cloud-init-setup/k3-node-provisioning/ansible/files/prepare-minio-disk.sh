#!/usr/bin/env bash
set -euo pipefail

MOUNT_POINT="/mnt/minio"
MIN_DATA_BYTES=800000000000

log() {
  echo "[prepare-minio-disk] $1" >&2
}

fail() {
  echo "[prepare-minio-disk] ERROR: $1" >&2
  exit 1
}

get_root_disk_name() {
  local root_source
  local parent_name

  root_source="$(findmnt -n -o SOURCE /)"

  if [[ -z "${root_source}" ]]; then
    fail "Unable to determine root filesystem source."
  fi

  parent_name="$(lsblk -no PKNAME "${root_source}" 2>/dev/null | head -n 1 || true)"

  if [[ -n "${parent_name}" ]]; then
    echo "${parent_name}"
    return
  fi

  if [[ -b "${root_source}" ]]; then
    basename "${root_source}"
    return
  fi

  fail "Unable to resolve root disk from ${root_source}."
}

list_minio_candidates() {
  local root_name

  root_name="$(get_root_disk_name)"

  lsblk -b -dn -o NAME,SIZE,TYPE,RM,ROTA |
    awk -v root="${root_name}" -v min_bytes="${MIN_DATA_BYTES}" '
      $1 != root &&
      $2 >= min_bytes &&
      $3 == "disk" &&
      $4 == 0 &&
      $5 == 1 {
        print "/dev/" $1
      }
    '
}

print_disk_inventory() {
  log "Detected disk inventory:"
  lsblk -o NAME,SIZE,TYPE,RM,ROTA,TRAN,MOUNTPOINT,MODEL,SERIAL >&2 || true
}

select_minio_disk() {
  local candidates
  local count
  local root_name

  root_name="$(get_root_disk_name)"
  candidates="$(list_minio_candidates | sed '/^$/d')"
  count="$(printf '%s\n' "${candidates}" | sed '/^$/d' | wc -l)"

  log "Detected root disk: /dev/${root_name}"

  if [[ "${count}" -ne 1 ]]; then
    log "Expected exactly one non-root, non-removable, rotational HDD >= ${MIN_DATA_BYTES} bytes."
    log "Matched MinIO candidates:"
    printf '%s\n' "${candidates:-none}" >&2
    print_disk_inventory
    fail "Refusing to partition a disk because MinIO disk selection was ambiguous."
  fi

  printf '%s\n' "${candidates}"
}

partition_suffix() {
  local disk="$1"

  if [[ "${disk}" =~ nvme|mmcblk ]]; then
    echo "p1"
    return
  fi

  echo "1"
}

ensure_partition_table() {
  local disk="$1"

  if ! parted -s "${disk}" print >/dev/null 2>&1; then
    log "No readable partition table on ${disk}; creating GPT label."
    parted -s "${disk}" mklabel gpt
  fi
}

create_partition_if_missing() {
  local disk="$1"
  local part="$2"
  local partition_count

  if [[ -b "${part}" ]]; then
    log "Partition already exists: ${part}"
    return
  fi

  partition_count="$(lsblk -nr -o TYPE "${disk}" | awk '$1 == "part" {count++} END {print count + 0}')"

  if [[ "${partition_count}" -ne 0 ]]; then
    print_disk_inventory
    fail "${disk} already has partitions, but ${part} does not exist. Refusing to guess."
  fi

  log "Creating XFS partition on ${disk}."
  parted -s "${disk}" mkpart primary xfs 1MiB 100%
  partprobe "${disk}"
  udevadm settle || true
  sleep 2

  [[ -b "${part}" ]] || fail "Expected partition ${part} was not created."
}

format_partition_if_missing() {
  local part="$1"
  local fstype

  fstype="$(blkid -s TYPE -o value "${part}" 2>/dev/null || true)"

  if [[ "${fstype}" == "xfs" ]]; then
    log "Partition ${part} already contains XFS."
    return
  fi

  if [[ -n "${fstype}" ]]; then
    fail "Partition ${part} already has filesystem ${fstype}; refusing to overwrite."
  fi

  log "Formatting ${part} as XFS."
  mkfs.xfs -f "${part}"
}

mount_partition() {
  local part="$1"
  local uuid

  mkdir -p "${MOUNT_POINT}"
  uuid="$(blkid -s UUID -o value "${part}")"

  if [[ -z "${uuid}" ]]; then
    fail "Unable to determine UUID for ${part}."
  fi

  if ! grep -q "UUID=${uuid}" /etc/fstab; then
    echo "UUID=${uuid} ${MOUNT_POINT} xfs defaults,nofail 0 2" >> /etc/fstab
  fi

  mount -a
}

main() {
  local disk
  local part

  disk="$(select_minio_disk)"
  part="${disk}$(partition_suffix "${disk}")"

  log "Selected MinIO disk: ${disk}"
  ensure_partition_table "${disk}"
  create_partition_if_missing "${disk}" "${part}"
  format_partition_if_missing "${part}"
  mount_partition "${part}"
  log "MinIO disk prepared and mounted at ${MOUNT_POINT}."
}

main "$@"
