"""Validate environment arguments and render the existing SAGE manifests."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent
FILES = ("requirements.txt", "service/__init__.py", "service/context.py",
         "service/main.py", "service/handoff.py", "service/architect.py", "service/probe.py", "service/evidence.py", "service/roles.py", "service/selfcheck.py",
         "service/workflow.py")


def source_digest() -> str:
    """Hash the complete deployable SAGE source with stable relative names."""
    digest = hashlib.sha256()
    for name in FILES:
        data = (ROOT / name).read_bytes()
        digest.update(name.encode() + b"\0" + data + b"\0")
    return digest.hexdigest()


def safe_configuration() -> Dict[str, str]:
    """Validate configuration before interpolation into Kubernetes YAML."""
    config = {
        "SAGE_OLLAMA_URL": os.environ.get(
            "SAGE_OLLAMA_URL", "http://192.168.2.27:11434"),
        "SAGE_OLLAMA_MODEL": os.environ.get("SAGE_OLLAMA_MODEL", "qwen3:8b"),
        "SAGE_OLLAMA_EMBED_MODEL": os.environ.get("SAGE_OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        "PYTHON_IMAGE": os.environ.get(
            "SAGE_PYTHON_IMAGE", "python:3.12-bookworm"),
    }
    if not re.fullmatch(r"https?://[a-zA-Z0-9._:-]+/?", config["SAGE_OLLAMA_URL"]):
        raise ValueError("SAGE_OLLAMA_URL must be a plain HTTP(S) origin")
    for key in ("SAGE_OLLAMA_MODEL", "SAGE_OLLAMA_EMBED_MODEL"):
        if not re.fullmatch(r"[A-Za-z0-9._:/-]+", config[key]):
            raise ValueError(f"{key} must name an installed Ollama model")
    if not re.fullmatch(r"[A-Za-z0-9._/:@-]+", config["PYTHON_IMAGE"]):
        raise ValueError("invalid base image reference")
    digest = source_digest()
    config["SOURCE_DIGEST"] = digest
    config["SOURCE_CONFIGMAP"] = f"sage-runtime-source-{digest[:20]}"
    return config


def main() -> None:
    """Render Kubernetes manifest and publish source configuration metadata."""
    config = safe_configuration()
    template = (ROOT / "k8s/runtime-nodocker.yaml.tmpl").read_text()
    for key, value in config.items():
        template = template.replace(f"__{key}__", value)
    if re.search(r"__[A-Z_]+__", template):
        raise ValueError("unrendered deployment placeholder")
    target = Path(os.environ["SAGE_MANIFEST_OUT"])
    target.write_text(template)
    metadata = Path(os.environ["SAGE_METADATA_OUT"])
    metadata.write_text(json.dumps(config, indent=2, sort_keys=True))
    print(f"SOURCE SHA256: {config['SOURCE_DIGEST']}")
    print(f"IMMUTABLE SOURCE CONFIGMAP: {config['SOURCE_CONFIGMAP']}")


if __name__ == "__main__":
    main()
