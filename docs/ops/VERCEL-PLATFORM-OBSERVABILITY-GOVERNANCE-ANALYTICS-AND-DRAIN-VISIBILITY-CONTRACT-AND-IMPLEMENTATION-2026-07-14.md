# Vercel Platform Observability Governance analytics and drain visibility contract and implementation

- Date: `2026-07-14`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root read-only visibility classification`
- Marker movement: `30% -> 40%`
- Denominator: `4 / 10`

## Scope

This unit implements a deterministic read model for:

- Web Analytics
- Speed Insights
- traces
- alerts
- drains
- Observability Plus posture

Each surface is classified as `visible`, `unproven`, `unavailable`, `forbidden`, or `unknown` with an evidence class and a boolean mutation-capability risk flag.

## Safety boundary

The wrapper and report cannot:

- enable or configure a product
- create, update, or delete a drain
- store a drain destination
- change retention
- claim entitlement
- store values, tokens, or secrets
- perform Vercel or owner-repository mutation

`visible` requires direct connector, CLI, or dashboard readback. Documentation or an unqueried surface cannot be upgraded to visible.

## Implementation

- `ops/atlas/vercel_observability_surface_visibility.py`
- `tests/test_atlas_vercel_observability_surface_visibility.py`

Frozen schemas:

- `atlas.vercel.observability.surface_visibility_wrapper.v1`
- `atlas.vercel_observability_surface_visibility.v1`

Every report states:

- `mutation_performed=false`
- `entitlement_claimed=false`

## Verification

Focused proof covers safe unproven classification, direct-readback requirements, mutation-field rejection, complete surface-set enforcement, state enums, project identity, path boundaries, and safe output.

Current result:

- `8` focused tests passed
- `62` combined Vercel inventory and selector tests passed
- root validation: `critical=0 error=0 warning=19 info=0`
- all 19 warnings are inherited absolute-path findings outside this change set

## Marker decision

This visibility classifier is the fourth distinct implementation-backed unit:

```text
4 / 10 = 40%
```

It proves a safe evidence model, not live visibility. Live capability truth remains a separate read-only audit.

## Exact next packet

```text
Vercel Platform Observability Governance analytics and drain live read-only capability audit
```

The audit may query only read surfaces available through the connected Vercel app or documented CLI. Unsupported surfaces remain `unproven`; no fallback mutation, dashboard automation, entitlement inference, product enablement, drain creation, or retention change is allowed.
