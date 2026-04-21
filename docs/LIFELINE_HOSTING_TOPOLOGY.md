# Lifeline Hosting Topology

This document defines the ATLAS-owned public topology contract for Lifeline-managed surfaces.

## Rule

- Public identity is stable at the `app/environment` layer. Host placement, machine identity, and provider instance details must stay hidden behind the gateway.

## Topology

- Default topology: shared gateway plus isolated services.
- Public product apps currently covered by the topology manifest:
  - `fitness`
  - `mazer`
  - `trove`
- Operator service covered by the topology manifest:
  - `lifeline`

## Environment model

- `dev` is local-only and has no public hostname.
- `preview` is the shared named preview environment for product apps.
- `prod` is the named production environment.
- `pr-{number}` is the only approved ephemeral public environment pattern.

## Hostname model

- Production hostname pattern: `{app}.{zone}`
- Preview hostname pattern: `preview-{app}.{zone}`
- PR preview hostname pattern: `pr-{number}.{app}.{zone}`
- Lifeline is intentionally different:
  - production hostname: `lifeline.{zone}`
  - no named preview hostname
  - no PR preview hostname

## Placement doctrine

- Stable contract unit: `app/environment`
- Public hostname must not change with placement.
- Gateway resolves service before placement.
- TLS terminates at the shared gateway.
- Cookie boundary stays at the application hostname.

## Stage progression

1. `single-host-many-services`
2. `shared-gateway-plus-worker-hosts`
3. `lifeline-controlled-multi-host`

## Lifeline v1 exclusions

- hosted-control-plane
- reverse-proxy-ownership
- domain-automation
- tls-automation
- multi-node-orchestration
