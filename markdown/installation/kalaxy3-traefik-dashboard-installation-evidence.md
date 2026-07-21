# Kalaxy3 Protected Traefik Dashboard Installation and Rebuild Guide

**Project:** Kalaxy3  
**Implementation date:** July 20, 2026, America/Chicago  
**Target path:** `markdown/installation/kalaxy3-traefik-dashboard-installation-evidence.md`  
**Traefik LoadBalancer address:** `192.168.2.20`  
**Dashboard hostname:** `traefik.kalaxy3.home.arpa`

## Purpose

This page records why the Traefik dashboard was exposed, how it is routed, how
it is protected, and how to reproduce the configuration during a future
Kalaxy3 rebuild.

The Traefik dashboard provides a read-only operational view of Traefik's active
routers, services, middleware, and entry points. It is useful for diagnosing
routing failures such as unmatched hostnames, missing middleware, incorrect
backend services, and unavailable entry points.

The dashboard must not be exposed without protection because it reveals
internal routing and cluster topology information.

No plaintext password, password hash, rendered Kubernetes Secret, or other
credential material belongs in this document or in Git.

## Final design

```text
Traefik LoadBalancer IP:        192.168.2.20
Dashboard hostname:             traefik.kalaxy3.home.arpa
Dashboard URL:                  http://traefik.kalaxy3.home.arpa/dashboard/
Traefik internal backend:       api@internal
Allowed client network:         192.168.2.0/24
Authentication:                 Traefik Basic Authentication
External traffic policy:        Local
Kubernetes namespace:           kube-system
```

The dashboard route covers both paths required by the Traefik web interface:

```text
/dashboard
/api
```

The browser URL must include the trailing slash:

```text
http://traefik.kalaxy3.home.arpa/dashboard/
```

## Why the dashboard was added

Longhorn and Prometheus had already been exposed through protected,
host-based Traefik routes. The Traefik dashboard was added to provide a direct
way to inspect the routing layer responsible for those services.

The dashboard helps answer operational questions such as:

- Did Traefik load the expected `IngressRoute`?
- Is a router attached to the expected entry point?
- Did Traefik accept the middleware configuration?
- Is the target Kubernetes service visible and healthy?
- Is a hostname request failing because no router matched it?

This is especially useful in Kalaxy3 because several internal services share
the single Traefik MetalLB address `192.168.2.20`.

## Security model

### Host-based routing

Traefik distinguishes the dashboard from Longhorn and Prometheus using the HTTP
`Host` header:

```text
traefik.kalaxy3.home.arpa    -> Traefik dashboard
longhorn.kalaxy3.home.arpa   -> Longhorn
prometheus.kalaxy3.home.arpa -> Prometheus
```

All three names resolve to:

```text
192.168.2.20
```

The hostname is therefore part of the route. Browsing directly to
`http://192.168.2.20` does not select the dashboard router.

### LAN allow-list

A Traefik `ipAllowList` middleware permits only clients whose preserved source
address is within:

```text
192.168.2.0/24
```

This prevents non-LAN clients from reaching the authentication challenge or
dashboard.

### Basic Authentication

The dashboard is protected by the same Basic Authentication model used for
Longhorn and Prometheus.

The middleware is in `kube-system`, so its referenced `ui-basic-auth` Secret
must also exist in `kube-system`. Kubernetes Secrets are namespace-scoped.

The Secret is created at runtime and is never committed to Git.

### Preserving the client IP

The Traefik service uses:

```yaml
externalTrafficPolicy: Local
```

This preserves the original administrative-client IP so the LAN allow-list can
evaluate the actual `192.168.2.x` source address.

Without this setting, source network address translation may cause Traefik to
see a node or cluster address instead. The request can then be rejected with
`403 Forbidden` even though the workstation is on the LAN.

## Persistent Traefik configuration

The bundled K3s Traefik installation is configured through a
`HelmChartConfig`, rather than by editing generated resources directly.

**File:**

```text
infrastructure/k3s-homelab/manifests/traefik-config.yml.j2
```

Required template:

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
    api:
      dashboard: true
      insecure: false

    ingressRoute:
      dashboard:
        enabled: false

    service:
      spec:
        loadBalancerIP: {{ traefik_load_balancer_ip }}
        externalTrafficPolicy: Local
      annotations:
        metallb.io/address-pool: {{ metallb_pool_name }}
```

The important choices are:

```text
api.dashboard: true
```

Enables the dashboard and internal API.

```text
api.insecure: false
```

Prevents Traefik from exposing an unprotected dashboard endpoint.

```text
ingressRoute.dashboard.enabled: false
```

Disables the chart's default dashboard route so Kalaxy3 can provide its own
LAN-restricted, authenticated route.

The existing inventory values remain:

```yaml
metallb_pool_name: lan-pool
traefik_load_balancer_ip: 192.168.2.20
```

## Applying the persistent Traefik configuration

The template is rendered and applied by the tagged tasks in:

```text
infrastructure/k3s-homelab/playbooks/tasks/network-storage.yml
```

From the `infrastructure/k3s-homelab` directory:

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/platform.yml   --limit arm64-01   --tags traefik-config
```

Verify the resulting Traefik service:

```bash
kubectl -n kube-system get svc traefik   -o jsonpath='IP={.spec.loadBalancerIP} policy={.spec.externalTrafficPolicy}{"\n"}'
```

Expected:

```text
IP=192.168.2.20 policy=Local
```

Verify that the HelmChartConfig contains the dashboard configuration:

```bash
kubectl -n kube-system get helmchartconfig traefik   -o jsonpath='{.spec.valuesContent}'
```

## Runtime authentication Secret

The protected route references:

```text
kube-system/ui-basic-auth
```

Do not add this Secret to a manifest stored in Git.

If the same administrator credential already exists for Longhorn, copy only
the existing runtime `htpasswd` value into a new namespace-local Secret:

```bash
AUTH_USERS="$(
  kubectl -n longhorn-system get secret ui-basic-auth     -o jsonpath='{.data.users}' |     base64 --decode
)"

kubectl -n kube-system create secret generic ui-basic-auth   --from-literal="users=${AUTH_USERS}"   --dry-run=client   -o yaml | kubectl apply -f -

unset AUTH_USERS
```

This command transfers the runtime password verifier without writing it to a
repository file.

Verify only that the expected username is present:

```bash
kubectl -n kube-system get secret ui-basic-auth   -o jsonpath='{.data.users}' | base64 --decode | cut -d: -f1

printf '\n'
```

Expected:

```text
admin
```

Do not print, document, or commit the remainder of the decoded value.

## Protected dashboard route

The dashboard resources belong in:

```text
infrastructure/k3s-homelab/manifests/protected-ui-routes.yml
```

Append or preserve these resources:

```yaml
---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: lan-only
  namespace: kube-system
spec:
  ipAllowList:
    sourceRange:
      - 192.168.2.0/24

---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: basic-auth
  namespace: kube-system
spec:
  basicAuth:
    secret: ui-basic-auth
    removeHeader: true

---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: traefik-dashboard
  namespace: kube-system
spec:
  entryPoints:
    - web
  routes:
    - kind: Rule
      match: >-
        Host(`traefik.kalaxy3.home.arpa`) &&
        (PathPrefix(`/api`) || PathPrefix(`/dashboard`))
      middlewares:
        - name: lan-only
        - name: basic-auth
      services:
        - name: api@internal
          kind: TraefikService
```

The service target is not a normal Kubernetes Service. It is Traefik's internal
dashboard/API service:

```text
api@internal
```

Therefore the service entry must include:

```yaml
kind: TraefikService
```

## Applying the dashboard route

Apply the complete protected-routes manifest:

```bash
kubectl apply -f manifests/protected-ui-routes.yml
```

The apply output should include the `kube-system` resources:

```text
middleware.traefik.io/lan-only created
middleware.traefik.io/basic-auth created
ingressroute.traefik.io/traefik-dashboard created
```

Existing Longhorn and Prometheus resources may report `unchanged`.

Verify all dashboard dependencies:

```bash
kubectl -n kube-system get   ingressroute/traefik-dashboard   middleware/lan-only   middleware/basic-auth   secret/ui-basic-auth
```

Expected logical resources:

```text
ingressroute/traefik-dashboard
middleware/lan-only
middleware/basic-auth
secret/ui-basic-auth
```

Inspect the final route when troubleshooting:

```bash
kubectl -n kube-system get   ingressroute traefik-dashboard   -o yaml
```

## Administrative-client name resolution

Until Kalaxy3 provides internal DNS, add this entry to `/etc/hosts` on each
administrative Mac or Linux client:

```text
192.168.2.20 traefik.kalaxy3.home.arpa
```

The complete protected-UI set is:

```text
192.168.2.20 longhorn.kalaxy3.home.arpa
192.168.2.20 prometheus.kalaxy3.home.arpa
192.168.2.20 traefik.kalaxy3.home.arpa
```

On macOS, flush the DNS cache after changing `/etc/hosts`:

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Confirm name resolution:

```bash
ping -c 1 traefik.kalaxy3.home.arpa
```

The hostname must resolve to:

```text
192.168.2.20
```

## Validation procedure

### Before the dashboard route existed

The following request reached Traefik but returned `404 Not Found`:

```bash
curl -I http://traefik.kalaxy3.home.arpa/dashboard/
```

Observed response:

```text
HTTP/1.1 404 Not Found
```

The cause was confirmed with:

```bash
kubectl -n kube-system get ingressroute traefik-dashboard
```

Observed:

```text
Error from server (NotFound):
ingressroutes.traefik.io "traefik-dashboard" not found
```

Applying the earlier version of `protected-ui-routes.yml` created or retained
only the Longhorn and Prometheus resources. It did not contain the dashboard
middleware or `IngressRoute`.

This evidence is useful because a Traefik `404` at this hostname usually means
the request reached Traefik but no active router matched the hostname and path.

### Anonymous request acceptance test

After creating the dashboard route:

```bash
curl -I http://traefik.kalaxy3.home.arpa/dashboard/
```

Expected:

```text
HTTP/1.1 401 Unauthorized
Content-Type: text/plain
Www-Authenticate: Basic realm="traefik"
```

A `401` proves that:

1. The hostname resolves to `192.168.2.20`.
2. Traefik matched the dashboard router.
3. The client passed the LAN allow-list.
4. Basic Authentication rejected the anonymous request.

### Authenticated request acceptance test

```bash
curl -u admin   -L   -o /dev/null   -s   -w 'Traefik dashboard: %{http_code}\n'   http://traefik.kalaxy3.home.arpa/dashboard/
```

Expected:

```text
Traefik dashboard: 200
```

Then open:

```text
http://traefik.kalaxy3.home.arpa/dashboard/
```

Use the runtime Basic Authentication username and password.

## Troubleshooting

### `404 Not Found`

Likely causes:

- `ingressroute/traefik-dashboard` does not exist.
- The protected route manifest was not updated or applied.
- The request hostname does not match `traefik.kalaxy3.home.arpa`.
- The request path does not begin with `/dashboard` or `/api`.
- Dashboard/API support was not enabled in the Traefik HelmChartConfig.

Check:

```bash
kubectl -n kube-system get ingressroute traefik-dashboard
kubectl -n kube-system get ingressroute traefik-dashboard -o yaml
kubectl -n kube-system get helmchartconfig traefik -o yaml
```

### `403 Forbidden`

The route matched, but the LAN allow-list rejected the source address.

Check:

```bash
kubectl -n kube-system get svc traefik   -o jsonpath='{.spec.externalTrafficPolicy}{"\n"}'
```

Expected:

```text
Local
```

Also confirm the client uses a `192.168.2.x` address.

### `401 Unauthorized`

This is the expected anonymous result.

If credentials are rejected, confirm that `ui-basic-auth` exists in
`kube-system` and contains the expected username. Do not expose the password
hash while troubleshooting.

### `500 Internal Server Error`

Possible causes include:

- The `basic-auth` middleware references a missing Secret.
- The Secret does not contain the expected `users` key.
- The dashboard route targets `api@internal` without
  `kind: TraefikService`.

Inspect:

```bash
kubectl -n kube-system describe ingressroute traefik-dashboard
kubectl -n kube-system describe middleware basic-auth
kubectl -n kube-system logs deployment/traefik --tail=100
```

## Rebuild sequence

During a future Kalaxy3 rebuild, perform these steps in order:

1. Install K3s, MetalLB, and bundled Traefik.
2. Confirm the Traefik MetalLB address is `192.168.2.20`.
3. Apply the Traefik `HelmChartConfig` through the tagged Ansible task.
4. Verify `externalTrafficPolicy=Local`.
5. Create the runtime `ui-basic-auth` Secret in `kube-system`.
6. Apply `manifests/protected-ui-routes.yml`.
7. Add the dashboard hostname to each administrative client's `/etc/hosts`.
8. Confirm anonymous access returns `401 Unauthorized`.
9. Confirm authenticated access returns `200`.
10. Open `/dashboard/` with the required trailing slash.

## Files that are safe to commit

```text
infrastructure/k3s-homelab/manifests/traefik-config.yml.j2
infrastructure/k3s-homelab/manifests/protected-ui-routes.yml
infrastructure/k3s-homelab/playbooks/platform.yml
infrastructure/k3s-homelab/playbooks/tasks/network-storage.yml
markdown/installation/kalaxy3-traefik-dashboard-installation-evidence.md
```

## Material that must not be committed

Never commit any of the following:

```text
The plaintext Basic Authentication password
The generated htpasswd line or password hash
A rendered ui-basic-auth Secret manifest
kubectl output containing Secret data
Shell history containing a plaintext credential
Temporary files containing credential material
```

The protected route manifest may reference the Secret by name:

```yaml
secret: ui-basic-auth
```

That reference is safe because it contains no credential data.

## Completion checklist

```text
[ ] Traefik HelmChartConfig enables the dashboard
[ ] Insecure dashboard exposure remains disabled
[ ] Built-in dashboard IngressRoute remains disabled
[ ] Traefik service uses 192.168.2.20
[ ] Traefik service uses externalTrafficPolicy=Local
[ ] kube-system/ui-basic-auth exists at runtime
[ ] kube-system/lan-only middleware exists
[ ] kube-system/basic-auth middleware exists
[ ] kube-system/traefik-dashboard IngressRoute exists
[ ] /etc/hosts maps traefik.kalaxy3.home.arpa to 192.168.2.20
[ ] Anonymous dashboard request returns 401
[ ] Authenticated dashboard request returns 200
[ ] No credential material is present in Git
```
