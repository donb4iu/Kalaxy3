# Kalaxy3 Protected Longhorn and Prometheus UI Installation Evidence and Rebuild Guide

**Project:** Kalaxy3  
**Completed:** July 20, 2026, America/Chicago  
**Kubernetes timestamps:** July 21, 2026 UTC  
**Target path:** `markdown/installation/kalaxy3-protected-ui-installation-evidence.md`  
**Traefik LoadBalancer address:** `192.168.2.20`

## Purpose

This page records how the Longhorn and Prometheus administrative interfaces
were exposed through the bundled K3s Traefik ingress controller, why host-based
routing was selected, how access was restricted to the Kalaxy3 LAN, and how
Basic Authentication was added for services that do not provide sufficient
built-in authentication.

The document is intended to make the configuration reproducible during a future
Kalaxy3 rebuild without relying on memory or repeating the troubleshooting that
was required to preserve the original client IP address.

No password, password hash, rendered Kubernetes Secret, or other credential
material belongs in this document or in Git.

## Final validated result

```text
Traefik service IP:              192.168.2.20
Traefik external traffic policy: Local
Allowed client network:          192.168.2.0/24

Longhorn hostname:               longhorn.kalaxy3.home.arpa
Longhorn backend:                longhorn-system/longhorn-frontend:80

Prometheus hostname:             prometheus.kalaxy3.home.arpa
Prometheus backend:              observability/
                                 kube-prometheus-stack-prometheus:9090

Anonymous Longhorn request:      401 Unauthorized
Anonymous Prometheus request:    401 Unauthorized
Authenticated Longhorn request:  200 OK
Authenticated Prometheus root:   302 Found -> /query
Authenticated Prometheus final:  200 OK
```

The `prometheus-operated` headless service is not used as the Traefik backend.
The route targets the normal `kube-prometheus-stack-prometheus` ClusterIP
service.

## Why this access model was selected

### A shared Traefik LoadBalancer address

The bundled K3s Traefik service already uses the MetalLB address
`192.168.2.20`. Both administrative interfaces can therefore share one LAN IP.
Traefik distinguishes them using the HTTP `Host` header:

```text
longhorn.kalaxy3.home.arpa   -> Longhorn
prometheus.kalaxy3.home.arpa -> Prometheus
```

This avoids assigning another MetalLB address to every internal administrative
service.

### Host-based routing instead of URL prefixes

Longhorn is most reliable when served from the root of a hostname rather than
from a rewritten path such as `/longhorn`. Prometheus can be configured for a
path prefix, but doing so requires additional external URL and route-prefix
configuration.

Separate hostnames keep both applications at `/` and avoid application-specific
path rewriting.

### Basic Authentication

Longhorn does not provide its own user login. Prometheus also exposes sensitive
cluster and workload information without an application login in this
installation. Traefik Basic Authentication provides an authentication boundary
before either backend is reached.

The same administrator username may be used for both services, but each
namespace requires its own Kubernetes Secret because Traefik middleware
references namespace-local Secrets.

### LAN restriction

An `ipAllowList` middleware permits only clients in:

```text
192.168.2.0/24
```

This prevents the routes from accepting requests whose client address is not on
the Kalaxy3 LAN, even if the request reaches Traefik.

### `externalTrafficPolicy: Local`

The Traefik service must preserve the original client address so the LAN
allow-list can evaluate the actual workstation IP.

With the default policy of `Cluster`, Kubernetes source NAT caused Traefik to
see a translated cluster or node address rather than the Mac's `192.168.2.x`
address. Both routes therefore returned:

```text
HTTP/1.1 403 Forbidden
```

Changing the Traefik service to:

```yaml
externalTrafficPolicy: Local
```

preserved the client address. The same anonymous requests then reached Basic
Authentication and correctly returned `401 Unauthorized`.

## Backend service evidence

The validated Kubernetes services were:

```text
NAMESPACE          NAME                                  TYPE        CLUSTER-IP      PORTS
longhorn-system    longhorn-frontend                     ClusterIP   10.43.248.144   80/TCP
observability      kube-prometheus-stack-prometheus      ClusterIP   10.43.129.4     9090/TCP,8080/TCP
observability      prometheus-operated                   ClusterIP   None            9090/TCP
```

Traefik routes to:

```text
longhorn-system/longhorn-frontend:80
observability/kube-prometheus-stack-prometheus:9090
```

## Required administrative-client name resolution

The Xfinity gateway does not support configuring an internal DNS server or
local DNS overrides. Until Kalaxy3 has a LAN DNS service, each administrative
client must map the two hostnames to the Traefik MetalLB address.

Add these entries to `/etc/hosts` on each Mac or Linux administrative client:

```text
192.168.2.20 longhorn.kalaxy3.home.arpa
192.168.2.20 prometheus.kalaxy3.home.arpa
```

On macOS, flush cached DNS after changing `/etc/hosts`:

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Confirm resolution:

```bash
ping -c 1 longhorn.kalaxy3.home.arpa
ping -c 1 prometheus.kalaxy3.home.arpa
```

Both names must resolve to `192.168.2.20`.

## Persistent Traefik configuration

**File:**

```text
infrastructure/k3s-homelab/manifests/traefik-config.yml.j2
```

Validated template:

```yaml
---
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: traefik
  namespace: kube-system
spec:
  failurePolicy: reinstall
  valuesContent: |-
    service:
      spec:
        loadBalancerIP: {{ traefik_load_balancer_ip }}
        externalTrafficPolicy: Local
      annotations:
        metallb.io/address-pool: {{ metallb_pool_name }}
```

Relevant variables are stored in:

```text
infrastructure/k3s-homelab/inventory/group_vars/all.yml
```

```yaml
metallb_pool_name: lan-pool
traefik_load_balancer_ip: 192.168.2.20
```

The `HelmChartConfig` is required because a direct patch to the generated
Traefik Service may be lost during K3s or Helm reconciliation. The template is
the source of truth for future rebuilds.

## Targeted Ansible deployment

The Traefik template is rendered and applied by:

```text
infrastructure/k3s-homelab/playbooks/tasks/network-storage.yml
```

Relevant tasks:

```yaml
- name: Render Traefik HelmChartConfig
  ansible.builtin.template:
    src: "{{ playbook_dir }}/../manifests/traefik-config.yml.j2"
    dest: /tmp/traefik-config.yml
    mode: '0600'
  tags:
    - traefik-config

- name: Configure bundled Traefik
  ansible.builtin.command:
    cmd: k3s kubectl apply -f /tmp/traefik-config.yml
  changed_when: true
  tags:
    - traefik-config
```

The include in `playbooks/platform.yml` carries the same tag so Ansible opens
the included task file during a targeted run:

```yaml
- name: Run networking and storage phase
  ansible.builtin.include_tasks: tasks/network-storage.yml
  when: selected_platform_phase in ['all', 'network_storage']
  tags:
    - network-storage
    - traefik-config
```

Validated targeted command:

```bash
cd infrastructure/k3s-homelab

ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --limit arm64-01 \
  --tags traefik-config
```

Observed recap:

```text
TASK [Run networking and storage phase]
included: playbooks/tasks/network-storage.yml for arm64-01

TASK [Render Traefik HelmChartConfig]
changed: [arm64-01]

TASK [Configure bundled Traefik]
changed: [arm64-01]

PLAY RECAP
arm64-01 : ok=4 changed=2 unreachable=0 failed=0 skipped=0
```

Service verification:

```bash
kubectl -n kube-system get svc traefik \
  -o jsonpath='IP={.spec.loadBalancerIP} policy={.spec.externalTrafficPolicy}{"\n"}'
```

Observed:

```text
IP=192.168.2.20 policy=Local
```

## Protected route manifest

**File:**

```text
infrastructure/k3s-homelab/manifests/protected-ui-routes.yml
```

Validated manifest:

```yaml
---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: lan-only
  namespace: longhorn-system
spec:
  ipAllowList:
    sourceRange:
      - 192.168.2.0/24

---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: basic-auth
  namespace: longhorn-system
spec:
  basicAuth:
    secret: ui-basic-auth
    removeHeader: true

---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: longhorn-ui
  namespace: longhorn-system
spec:
  entryPoints:
    - web
  routes:
    - kind: Rule
      match: Host(`longhorn.kalaxy3.home.arpa`)
      middlewares:
        - name: lan-only
        - name: basic-auth
      services:
        - name: longhorn-frontend
          port: 80

---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: lan-only
  namespace: observability
spec:
  ipAllowList:
    sourceRange:
      - 192.168.2.0/24

---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: basic-auth
  namespace: observability
spec:
  basicAuth:
    secret: ui-basic-auth
    removeHeader: true

---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: prometheus-ui
  namespace: observability
spec:
  entryPoints:
    - web
  routes:
    - kind: Rule
      match: Host(`prometheus.kalaxy3.home.arpa`)
      middlewares:
        - name: lan-only
        - name: basic-auth
      services:
        - name: kube-prometheus-stack-prometheus
          port: 9090
```

The manifest references a Secret by name but contains no credential data.

## Credential creation during a rebuild

The authentication Secret must be created separately in both namespaces. It
must never be committed to Git or copied into installation evidence.

On macOS with zsh, use a hidden prompt rather than Bash's incompatible
`read -p` option:

```bash
read -rs "UI_PASSWORD?Longhorn/Prometheus password: "
printf '\n'

if [[ -z "${UI_PASSWORD}" ]]; then
  echo "Password cannot be empty." >&2
  unset UI_PASSWORD
else
  UI_USERS="$(htpasswd -nbB admin "${UI_PASSWORD}")"

  for namespace in longhorn-system observability; do
    kubectl -n "${namespace}" create secret generic ui-basic-auth \
      --from-literal="users=${UI_USERS}" \
      --dry-run=client \
      -o yaml | \
      kubectl apply -f -
  done

  unset UI_PASSWORD UI_USERS
fi
```

This process creates the required runtime Secrets without writing a plaintext
password or rendered Secret manifest to the repository.

Confirm only that each Secret contains the expected username:

```bash
for namespace in longhorn-system observability; do
  printf '%s: ' "${namespace}"

  kubectl -n "${namespace}" get secret ui-basic-auth \
    -o jsonpath='{.data.users}' | \
    base64 --decode | \
    cut -d: -f1

  printf '\n'
done
```

Expected:

```text
longhorn-system: admin
observability: admin
```

Do not print, log, document, or commit the remainder of the decoded value.

## Applying the protected routes

After both Secrets exist:

```bash
kubectl apply \
  -f infrastructure/k3s-homelab/manifests/protected-ui-routes.yml
```

Resource verification:

```bash
kubectl -n longhorn-system get middleware,ingressroute
kubectl -n observability get middleware,ingressroute
```

Expected logical resources:

```text
longhorn-system:
  middleware/lan-only
  middleware/basic-auth
  ingressroute/longhorn-ui

observability:
  middleware/lan-only
  middleware/basic-auth
  ingressroute/prometheus-ui
```

## Validation evidence

### Anonymous requests

Commands:

```bash
curl -I http://longhorn.kalaxy3.home.arpa
curl -I http://prometheus.kalaxy3.home.arpa
```

Observed for both services:

```text
HTTP/1.1 401 Unauthorized
Content-Type: text/plain
Www-Authenticate: Basic realm="traefik"
Content-Length: 17
```

Interpretation:

1. Client-side hostname resolution worked.
2. The request reached Traefik at `192.168.2.20`.
3. The hostname matched the intended `IngressRoute`.
4. The source address passed the LAN allow-list.
5. Basic Authentication rejected the anonymous request before the backend was
   reached.

### Authenticated Longhorn request

Command:

```bash
curl -u admin \
  -o /dev/null \
  -s \
  -w 'Longhorn: %{http_code}\n' \
  http://longhorn.kalaxy3.home.arpa
```

Observed:

```text
Longhorn: 200
```

This proved that the credentials were accepted and Traefik successfully proxied
the request to `longhorn-system/longhorn-frontend:80`.

### Authenticated Prometheus redirect

Command:

```bash
curl -u admin \
  -s \
  -D - \
  -o /dev/null \
  http://prometheus.kalaxy3.home.arpa | \
grep -iE 'HTTP/|location:'
```

Observed:

```text
HTTP/1.1 302 Found
Location: /query
```

Prometheus correctly redirected its root path to `/query`.

Final request following the redirect:

```bash
curl -u admin \
  -L \
  -o /dev/null \
  -s \
  -w 'Prometheus final: %{http_code}\n' \
  http://prometheus.kalaxy3.home.arpa
```

Observed:

```text
Prometheus final: 200
```

This proved that authentication, routing, redirect handling, and the Prometheus
backend were all functioning.

## Browser endpoints

Administrative clients with the required `/etc/hosts` entries can use:

```text
http://longhorn.kalaxy3.home.arpa
http://prometheus.kalaxy3.home.arpa
```

The browser should display a Basic Authentication prompt. The username is
`admin`; the password is the runtime credential created by the administrator
and is intentionally not recorded here.

## Rebuild procedure

### 1. Install Traefik and MetalLB

Complete the normal Kalaxy3 networking phase and confirm Traefik owns:

```text
192.168.2.20
```

```bash
kubectl -n kube-system get svc traefik -o wide
```

### 2. Confirm backend services

```bash
kubectl -n longhorn-system get svc longhorn-frontend

kubectl -n observability get svc \
  kube-prometheus-stack-prometheus
```

Required ports:

```text
longhorn-frontend:                    80
kube-prometheus-stack-prometheus:    9090
```

### 3. Apply the persistent Traefik policy

Run the targeted Ansible tasks:

```bash
cd infrastructure/k3s-homelab

ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --limit arm64-01 \
  --tags traefik-config
```

Verify:

```bash
kubectl -n kube-system get svc traefik \
  -o jsonpath='IP={.spec.loadBalancerIP} policy={.spec.externalTrafficPolicy}{"\n"}'
```

Required result:

```text
IP=192.168.2.20 policy=Local
```

### 4. Configure administrative-client hostnames

Add:

```text
192.168.2.20 longhorn.kalaxy3.home.arpa
192.168.2.20 prometheus.kalaxy3.home.arpa
```

to `/etc/hosts` on each administrative workstation.

### 5. Create runtime authentication Secrets

Create `ui-basic-auth` separately in:

```text
longhorn-system
observability
```

Use the hidden-password procedure documented above. Do not save the plaintext
password, generated hash, or rendered Secret in Git.

### 6. Apply the protected routes

```bash
kubectl apply \
  -f infrastructure/k3s-homelab/manifests/protected-ui-routes.yml
```

### 7. Verify anonymous denial

```bash
curl -I http://longhorn.kalaxy3.home.arpa
curl -I http://prometheus.kalaxy3.home.arpa
```

Both must return:

```text
401 Unauthorized
```

A `404` means the host rule or route did not match. A `403` means the LAN
allow-list rejected the source address; recheck `externalTrafficPolicy: Local`
and confirm the client uses `192.168.2.0/24`.

### 8. Verify authenticated access

```bash
curl -u admin \
  -o /dev/null \
  -s \
  -w 'Longhorn: %{http_code}\n' \
  http://longhorn.kalaxy3.home.arpa

curl -u admin \
  -L \
  -o /dev/null \
  -s \
  -w 'Prometheus: %{http_code}\n' \
  http://prometheus.kalaxy3.home.arpa
```

Required final results:

```text
Longhorn: 200
Prometheus: 200
```

## Troubleshooting

### `404 Not Found`

The request reached Traefik but no route matched. Check:

```bash
kubectl -n longhorn-system describe ingressroute longhorn-ui
kubectl -n observability describe ingressroute prometheus-ui
```

Confirm the browser or `curl` request uses the exact configured hostname rather
than only `http://192.168.2.20`.

### `403 Forbidden`

The `lan-only` middleware rejected the address visible to Traefik.

Check:

```bash
kubectl -n kube-system get svc traefik \
  -o jsonpath='{.spec.externalTrafficPolicy}{"\n"}'
```

It must return:

```text
Local
```

Also confirm the administrative client has a `192.168.2.x` address.

### `401 Unauthorized`

For an anonymous request, `401` is the expected result and proves that the route
is protected.

For a request that supplied credentials, recreate the namespace-local Secret
and confirm the username is `admin` without exposing the password hash.

### Longhorn succeeds but Prometheus returns `302`

This is normal for the Prometheus root URL. It redirects to:

```text
/query
```

Use `curl -L` to follow the redirect and verify the final `200` response.

### Traefik route or middleware errors

```bash
kubectl -n kube-system logs deployment/traefik --tail=100

kubectl -n longhorn-system get middleware,ingressroute -o yaml
kubectl -n observability get middleware,ingressroute -o yaml
```

Do not include Secret values when collecting or committing diagnostic output.

## Security limitations and future hardening

This configuration provides LAN source filtering and Basic Authentication, but
the current endpoints use plain HTTP. Basic Authentication credentials are
encoded in the HTTP request and are not encrypted in transit.

The current design is acceptable only on the trusted Kalaxy3 LAN. The next
hardening step should be HTTPS using a locally trusted certificate or an
internal certificate authority. The LAN allow-list and Basic Authentication
should remain in place as additional controls after TLS is enabled.

The routes must not be forwarded through the Internet gateway, exposed by a
public DNS record, or made reachable from an untrusted network while they use
plain HTTP.

## Files that belong in Git

```text
infrastructure/k3s-homelab/manifests/traefik-config.yml.j2
infrastructure/k3s-homelab/manifests/protected-ui-routes.yml
infrastructure/k3s-homelab/playbooks/platform.yml
infrastructure/k3s-homelab/playbooks/tasks/network-storage.yml
markdown/installation/kalaxy3-protected-ui-installation-evidence.md
```

## Material that must not be committed

Never commit any of the following:

- The Basic Authentication password.
- The generated bcrypt or other password hash.
- Output from `kubectl get secret ... -o yaml`.
- A rendered `ui-basic-auth` Secret manifest.
- Shell history or terminal captures containing a credential.
- An unencrypted Ansible variable containing the password.

The repository should contain only the Secret name expected by the Traefik
middleware and the procedure for recreating the runtime Secret.

## Final validation checklist

- [x] Traefik MetalLB IP is `192.168.2.20`.
- [x] Traefik uses `externalTrafficPolicy: Local`.
- [x] Longhorn hostname is `longhorn.kalaxy3.home.arpa`.
- [x] Prometheus hostname is `prometheus.kalaxy3.home.arpa`.
- [x] Administrative clients map both names to `192.168.2.20`.
- [x] Requests are restricted to `192.168.2.0/24`.
- [x] Both routes require Basic Authentication.
- [x] Anonymous Longhorn returns `401`.
- [x] Anonymous Prometheus returns `401`.
- [x] Authenticated Longhorn returns `200`.
- [x] Authenticated Prometheus redirects to `/query`.
- [x] Authenticated Prometheus returns final `200`.
- [x] No password or Kubernetes Secret is stored in Git.
