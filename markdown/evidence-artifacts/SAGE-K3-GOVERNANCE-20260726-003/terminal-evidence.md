# Kalaxy3 Daux landing-page working-session evidence

Evidence ID: SAGE-K3-GOVERNANCE-20260726-003
Work date: 2026-07-26
Local timezone: America/Chicago
Execution host: donbs-imac
Repository: donb4iu/Kalaxy3
Branch: feature/kalaxy3-daux-landing-page
Implementation commit reference: 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc

## EV-001 — Kalaxy2 and Kalaxy3 source-root audit

The operator compared the documentation source roots.

Observed Kalaxy2 source-root files:

```text
Kalaxy2/markdown/_index.md
Kalaxy2/markdown/config.json
Kalaxy2/markdown/image.png
Kalaxy2/markdown/microk8s.md
Kalaxy2/markdown/rpi4.png
```

Observed Kalaxy2 Daux configuration:

```json
{
  "title": "Kalaxy2 MicroK8s Cluster",
  "tagline": "Arm64/Amd64 cluster research",
  "image": "rpi4.png",
  "html": {
    "auto_toc": true,
    "date_modified": true,
    "search": true
  },
  "author": "Don Buddenbaum"
}
```

Observed configured image:

```text
Kalaxy2/markdown/rpi4.png
PNG image data, 654 x 366, 8-bit/color RGBA, non-interlaced
SHA-256 b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130
```

Observed Kalaxy3 source-root state:

```text
Kalaxy3/markdown/index.md
```

Conclusion: Kalaxy3 had landing-page content but lacked Daux's `_index.md`
landing-page convention, a root `config.json`, and the configured image asset.

## EV-002 — Scope decision

The operator explicitly chose local validation only and rejected expanding the
feature branch to add branch-publishing automation.

Accepted scope:

```text
rename markdown/index.md to markdown/_index.md
add markdown/config.json
add markdown/rpi4.png
run Daux locally
write preview outside the repository
make no workflow changes
commit no generated docs
```

The existing main workflow was reviewed and left unchanged. It checks out the
repository, runs `daux/daux.io:latest`, removes `docs`, generates from
`markdown` to `docs`, commits generated documentation, and pushes to `main`.
Because that workflow pushes `HEAD:main`, enabling it broadly on feature
branches was considered outside this correction and potentially unsafe.

## EV-003 — Source implementation

A dedicated branch was created:

```text
feature/kalaxy3-daux-landing-page
```

The source change was:

```text
R  markdown/index.md -> markdown/_index.md
?? markdown/config.json
?? markdown/rpi4.png
```

The new configuration identifies Kalaxy3 rather than copying the stale Kalaxy2
identity:

```json
{
  "title": "Kalaxy3 K3s Cluster",
  "tagline": "ARM64 and AMD64 homelab architecture, operations, and evidence",
  "image": "rpi4.png",
  "html": {
    "auto_toc": true,
    "date_modified": true,
    "search": true
  },
  "author": "Don Buddenbaum"
}
```

The copied image retained the observed Kalaxy2 checksum:

```text
b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130
```

## EV-004 — Local Daux bootstrap and full generation

The local validator used the same container family and generation command as
the GitHub workflow while mounting the repository read-only and writing the
preview under `~/Downloads`.

The image was not already present locally. Docker pulled:

```text
daux/daux.io:latest
Digest: sha256:b29a089551c11303474d972679d3bdeb12a49ba65e552d954f3e0110dc57dd88
```

This demonstrated bootstrap from the container image without a host Daux
installation.

Daux reported successful static-asset copy and successful generation of the
landing page, evidence indexes, evidence artifacts, infrastructure pages,
installation pages, operations pages, security pages, standards, and templates.

Final validator output:

```text
Local Daux validation: PASS
branch=feature/kalaxy3-daux-landing-page
preview=/Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU
index=/Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU/index.html
image=/Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU/rpi4.png
image_sha256=b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130
```

Repository status after validation remained limited to the intended source
changes. The validator did not write `docs/` or modify workflow files.

## EV-005 — Visual validation

The operator opened the generated local `index.html`. The captured page visibly
contains:

```text
Kalaxy3 K3s Cluster
ARM64 and AMD64 homelab architecture, operations, and evidence
Raspberry Pi landing image
VIEW DOCUMENTATION control
Kalaxy3 source landing content
page-level Table of Contents
search field
```

The screenshot packaged as `rendered-landing-page.png` is cropped to remove
browser tabs and unrelated browser chrome.

## EV-006 — Git commit and remote preservation

The source change passed staged whitespace validation and was committed:

```text
[feature/kalaxy3-daux-landing-page 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc] Add Kalaxy3 Daux landing page
3 files changed, 11 insertions(+)
rename markdown/{index.md => _index.md} (100%)
create mode 100644 markdown/config.json
create mode 100644 markdown/rpi4.png
```

The branch was pushed to:

```text
origin/feature/kalaxy3-daux-landing-page
```

Final repository state:

```text
branch up to date with origin/feature/kalaxy3-daux-landing-page
nothing to commit, working tree clean
```

## EV-007 — Explicitly unvalidated publication state

The feature was not merged into `main` during this evidence collection. The
main-only GitHub workflow had therefore not yet regenerated and published the
new landing page. This record validates the source change and local render, not
the final live GitHub Pages deployment.
