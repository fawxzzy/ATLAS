# Stack Lock Fitness Manifest Surface Repair Decision

Date: 2026-05-24
Status: accepted

## Decision

Accept the canonical Fitness repo manifest-surface repair commit into ATLAS stack truth and repin the Fitness entry in `stack.lock.yaml`.

## Why

- the change is a narrow canonical-repo fix
- it repairs a real preview-surface blocker discovered during local live verification
- repo-local verification passed:
  - `npm run sanity:quick`
  - `npm run typecheck`
  - `npm run build`
- the fix does not reopen `tmp` as source truth
- the fix does not require deploy, Vercel mutation, or Supabase mutation

## Accepted Repo State

- repo: `repos/fawxzzy-fitness`
- branch: `main`
- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- accepted commit: `fe6cf9e7`
- accepted purpose: exclude `manifest.webmanifest` from auth middleware interception and restore local manifest JSON behavior

## Scope

This stack-lock repair accepts only the canonical Fitness HEAD movement caused by the manifest-surface fix.

It does not:

- alter any other component pin
- regenerate stack state broadly
- change deploy policy
- change `tmp` governance
