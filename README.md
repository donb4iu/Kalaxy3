# Kalaxy3
mixed amd and arm homelab based on k3s
   
    daux_build_publish.yml - git action to generate daux webpages from markdown directory to docs directory and then push to git pages repo

## SAGE change discovery

Every repository change begins with automatic SAGE context discovery:

```bash
python3 scripts/sage/sage-change-preflight.py \
  --request "<the request exactly as received>"
```

See [SAGE.md](SAGE.md) for the repository-owned change process.
