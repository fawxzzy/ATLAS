# Vercel Platform Observability Governance analytics and drain live read-only capability audit

- Date: `2026-07-14`
- Lane: `Vercel Platform Observability Governance`
- Mode: `read-only connected-Vercel capability audit`
- Marker movement: none; remains `40%`
- Blocker class: `read_transport_unavailable`

## Decision

The current Vercel product surface is broader than the read transport exposed to this Atlas session.

Official Vercel documentation confirms:

- `GET /v1/drains` exists for listing drains
- `GET /v1/drains/{id}` exists for reading one drain
- `GET /v1/observability/manage/configuration/projects` exists for listing projects disabled for Observability Plus
- separate POST, PUT, PATCH, and DELETE endpoints are mutation-capable and remain forbidden
- Web Analytics and Speed Insights have documented product and data surfaces

Current connected-app inspection found no callable project-level tools for:

- Web Analytics
- Speed Insights
- traces
- alerts
- drains
- Observability Plus configuration

Current local CLI proof:

```text
Vercel CLI 50.41.0
Error: "metrics" is not a valid target directory or subcommand.
```

No raw bearer token, undocumented API call, dashboard automation, or mutation-capable fallback was used.

## Current classification

| Surface | State | Evidence class | Reason |
| --- | --- | --- | --- |
| Web Analytics | `unproven` | `not_queried` | product is documented; current connector exposes no project read tool |
| Speed Insights | `unproven` | `not_queried` | product is documented; connector has no project read tool and CLI lacks `metrics` |
| traces | `unproven` | `not_queried` | no safe project read tool is exposed in the current connector |
| alerts | `unproven` | `not_queried` | no safe project read tool is exposed in the current connector |
| drains | `unproven` | `documented_unproven` | official GET API exists, but current connector exposes no drain-list tool |
| Observability Plus | `unproven` | `documented_unproven` | official GET API exists, but current connector exposes no configuration-read tool |

`unproven` does not mean disabled, unavailable, or absent. It means this session lacks a safely exposed authenticated read transport that can prove project truth without broadening authority.

## Authority preservation

This audit performed no:

- product enablement
- drain create, update, test, delete, or destination read
- retention change
- entitlement claim
- environment or token read
- Vercel project or deployment mutation
- owner-repository or Discord mutation

## Marker decision

The marker remains `40%` because the visibility classifier is implemented, but no additional live read capability was proven.

Documentation that an API exists is not implementation or current project-state proof.

## Blocker conversion

Future reopening requires one of:

1. connected Vercel tools that expose the relevant GET surfaces without mutation
2. a separately governed read-only API adapter that uses existing auth without exposing credentials or response fields outside the frozen visibility contract
3. a documented CLI release that exposes the required read surfaces safely

Until one materially changes, the Vercel lane is held and Atlas should continue another execution-ready lane.

## Reusable knowledge

**RULE - API existence is not active read authority**

An official GET endpoint proves product capability, not that the current worker has a safely exposed authenticated transport.

**FAILURE MODE - Capability-to-state inference**

Treating a documented product or endpoint as proof that a project has the feature enabled, visible, or entitled creates false operational truth.
