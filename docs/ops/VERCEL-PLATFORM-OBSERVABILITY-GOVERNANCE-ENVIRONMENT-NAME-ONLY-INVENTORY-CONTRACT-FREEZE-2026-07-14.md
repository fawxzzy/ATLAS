# Vercel Platform Observability Governance environment-name-only inventory contract freeze

- Date: `2026-07-14`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root read-only metadata contract`
- Marker movement: none in the contract step

## Scope

This contract admits Vercel environment metadata only when the input contains:

- a governed project id and matching project name
- a capture timestamp
- environment variable names
- target scopes: `production`, `preview`, or `development`
- presence: `configured` or `missing`
- type posture: `encrypted`, `sensitive`, `plain`, `system`, or `unknown`

## Frozen schemas

Input wrapper:

```text
atlas.vercel.observability.environment_name_wrapper.v1
```

Normalized report:

```text
atlas.vercel_environment_name_inventory.v1
```

## Prohibited data

The contract forbids:

- environment values or paraphrases of values
- token or secret values
- authorization, cookie, body, payload, or header material
- raw API responses containing secret-bearing fields
- files outside root-relative `tmp/**.json`
- environment creation, edit, deletion, pull, or push
- deployment or project-setting mutation

Environment names may contain words such as `TOKEN`, `SECRET`, or `KEY`; those identifiers are metadata. A field named `value`, `token_value`, `secret`, or an equivalent secret-bearing key is a blocker.

## Authority

This contract grants validation and normalization authority only. It grants no live query, Vercel mutation, owner-repository mutation, deployment, Discord, analytics, trace, drain, alert, or billing authority.

## Acceptance

An implementation must prove:

1. valid names, target scopes, presence, and posture normalize deterministically
2. value-bearing keys are rejected recursively
3. assignment strings in the name field are rejected
4. unknown wrapper and variable fields are rejected
5. unknown or mismatched projects are rejected
6. duplicate project captures are rejected
7. input and output stay under `tmp/**.json`
8. every report states `environment_value_accessed=false`

## Exact implementation surface

- `ops/atlas/vercel_environment_name_inventory.py`
- `tests/test_atlas_vercel_environment_name_inventory.py`

## Reusable knowledge

**RULE - Names are metadata; values are secrets**

An environment inventory may persist identifiers and target scope but must reject any field or assignment that can carry a value.

**FAILURE MODE - Name-only scope creep**

A supposedly metadata-only packet retains an unrecognized description, payload, or raw API field that can leak secret material.
