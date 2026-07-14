# Atlas Socials OS Registration and Inventory Reconciliation

## Decision

Register `socials-os` as a standing, unmanaged, non-root-blocking owner lane.
Atlas owns its lifecycle, repository visibility, receipts, remote parity, and
cross-stack relationships. Socials OS implementation remains owned by its
dedicated task and `repos/socials-os` repository.

This owner-lane posture matches the coordination boundary used for Fitness and
Mazer. It does not make Socials OS a fallback implementation lane for Atlas
root sessions.

## Verified owner state

- Local repository: `repos/socials-os`
- Local branch: `main`
- Local commit: `0c5309f5a448e286ced93e6e65184384f0a96ef4`
- Working tree: clean
- Remote: absent
- Current lifecycle: deterministic scaffold complete; Instagram baseline
  incomplete
- Current blocker: the desktop in-app browser webview did not attach after two
  supported retries
- External account mutation: none
- Production deployment: none

The repository currently provides the append-only schemas, ingestion,
validation, reporting, and security boundary needed for a future read-only
social analytics baseline. A private GitHub remote remains deferred until the
first trustworthy Instagram baseline is complete.

## Atlas truth updates

- `stack.yaml` now records `socials-os` with role `analytics-data-system`,
  status `unmanaged`, and `root_blocking: false`.
- `stack.lock.yaml` was regenerated from the current governed managed-repo
  working set. Unmanaged owner lanes remain visible through the manifest and
  published repo inventory rather than becoming managed lock components.
- `docs/registry/STACK-REPO-INVENTORY.json` and
  `docs/audits/STACK-REPO-INVENTORY.md` now include the Socials OS owner lane.
- The working-memory catalog was deterministically rebuilt to `42` items with
  content digest
  `sha256:19cd8ba0dccfe7e4c302335ec1c5aeb243f65895a050dcdc6e6533cbcf917570`.

## Verification

- Repo inventory: `13` repositories, `1` dirty repository at generation time
- Repo inventory digest:
  `sha256:c8bd1a15b2ebbd61230732f8c1cfbc2d0a96ae1a6aa7e20ca79298ac2ddff02e`
- Stack validation: `critical=0 error=0 warning=3 info=0`
- Remaining warnings: three inherited absolute-path findings, unchanged by
  this admission
- Git diff check: passed for the manifest, lock, and generated inventory

## Boundaries

This reconciliation does not:

- create or push a Socials OS remote;
- collect Instagram data;
- access credentials or account state;
- mutate Mazer, Fitness, DiscordOS, or another owner repository;
- authorize Socials OS as an Atlas-root fallback lane;
- normalize active `_stack`, Playbook, or DiscordOS owner branches; or
- claim that the browser collection blocker is resolved.

Active owner-branch normalization, remote creation, and GitHub monitoring stay
in their separately governed lanes.
