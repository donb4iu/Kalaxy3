#!/usr/bin/env python3
"""Verify inventory SSH host keys and write repository-owned known_hosts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "inventory/ssh_known_hosts"
FINGERPRINT_RE = re.compile(r"SHA256:[A-Za-z0-9+/]+")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verified-json",
        help="JSON mapping inventory host names to independently verified fingerprints.",
    )
    return parser.parse_args()


def inventory_hosts() -> dict[str, str]:
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/ansible-inventory"),
            "-i",
            str(ROOT / "inventory/hosts.yml"),
            "--list",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    hostvars = json.loads(result.stdout).get(
        "_meta", {}
    ).get("hostvars", {})
    hosts: dict[str, str] = {}
    for name, variables in hostvars.items():
        address = str(variables.get("ansible_host", "")).strip()
        if not address:
            raise RuntimeError(f"{name} lacks ansible_host")
        hosts[str(name)] = address
    if not hosts:
        raise RuntimeError("Effective inventory contains no hosts")
    return hosts


def fingerprint_from_key(key_type: str, key_data: str) -> str:
    if key_type != "ssh-ed25519":
        raise RuntimeError(f"Unexpected host key type: {key_type}")
    raw = base64.b64decode(key_data.encode("ascii"), validate=True)
    digest = base64.b64encode(
        hashlib.sha256(raw).digest()
    ).decode("ascii").rstrip("=")
    return f"SHA256:{digest}"


def scan_key(address: str) -> tuple[str, str, str]:
    result = subprocess.run(
        ["ssh-keyscan", "-T", "10", "-t", "ed25519", address],
        check=False,
        capture_output=True,
        text=True,
    )
    candidates = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one ED25519 key from {address}, found {len(candidates)}"
        )
    fields = candidates[0].split()
    if len(fields) != 3:
        raise RuntimeError(f"Invalid ssh-keyscan record for {address}")
    _, key_type, key_data = fields
    return key_type, key_data, fingerprint_from_key(key_type, key_data)


def supplied_fingerprint(raw: str) -> str:
    match = FINGERPRINT_RE.search(raw)
    if match is None:
        raise RuntimeError("Input does not contain a SHA256 fingerprint")
    return match.group(0)


def main() -> int:
    options = arguments()
    verified: dict[str, str] = {}
    if options.verified_json:
        payload = json.loads(
            Path(options.verified_json).read_text(encoding="utf-8")
        )
        verified = {
            str(name): supplied_fingerprint(str(value))
            for name, value in payload.items()
        }

    hosts = inventory_hosts()
    records: list[str] = []

    print("Kalaxy3 SSH host-key verification")
    print(f"Repository: {ROOT}")
    print(f"Output:     {OUTPUT}")
    print()
    print(
        "No key is accepted from ssh-keyscan alone. Every key must match "
        "an independently obtained fingerprint."
    )

    for name, address in hosts.items():
        key_type, key_data, network_fingerprint = scan_key(address)
        print()
        print(f"Node:         {name}")
        print(f"Address:      {address}")
        print(f"Network scan: {network_fingerprint}")

        expected = verified.get(name)
        if expected:
            print(f"Verified:     {expected}")
        else:
            print()
            print(
                "On the node console or another already trusted channel, run:"
            )
            print(
                "  sudo ssh-keygen -lf "
                "/etc/ssh/ssh_host_ed25519_key.pub"
            )
            raw = input(
                "Paste that output or SHA256 fingerprint "
                "(or type SKIP): "
            ).strip()
            if raw.upper() == "SKIP":
                print("Stopped without writing a known_hosts file.")
                return 1
            expected = supplied_fingerprint(raw)

        if expected != network_fingerprint:
            raise RuntimeError(
                f"{name}: verified fingerprint {expected} does not match "
                f"network fingerprint {network_fingerprint}"
            )

        records.append(
            f"{name},{address} {key_type} {key_data}"
        )
        print(f"PASS {name}: fingerprint matched")

    content = "\n".join(records) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=OUTPUT.parent,
        prefix=".ssh_known_hosts.",
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(content)

    temporary.chmod(0o644)
    temporary.replace(OUTPUT)

    print()
    print("Kalaxy3 SSH host-key verification: PASS")
    print(f"Wrote {len(records)} verified keys to {OUTPUT}")
    print("This script did not modify ~/.ssh/known_hosts.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SSH host-key verification failed: {error}")
        raise SystemExit(1)
