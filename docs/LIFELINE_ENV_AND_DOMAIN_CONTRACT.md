# Lifeline Environment And Domain Contract

This document captures the operator-facing environment and hostname contract that the machine-readable topology manifest projects.

## Rule

- Topology manifests must resolve to one canonical owner path.

## Named environments

- `dev`
  - kind: `local`
  - public hostname mode: `none`
- `preview`
  - kind: `shared-preview`
  - public hostname mode: `default`
- `prod`
  - kind: `production`
  - public hostname mode: `default`

## Ephemeral environments

- `pr`
  - environment template: `pr-{number}`
  - match: `^pr-[1-9][0-9]*$`
  - public hostname mode: `default`

## Public identity contract

- Stable service key template: `{app}/{environment}`
- Stable public unit: `app/environment`
- Routing default: `subdomain-first`
- Public hostnames must hide:
  - machine identity
  - provider instance identity
  - placement identity

## Path routing allowlist

Path routing is disallowed for distinct apps by default. The only approved shared allowlist categories are:

- `docs`
- `admin`
- `internal-tools`
- `tightly-coupled-surfaces`

## Failure Mode

- Fixing topology verification by copying topology truth into the wrong repo creates long-term drift and turns hostname policy into duplicated folklore.
