# ATLAS Cockpit Runbook

## Purpose

`ops/atlas/cockpit.py` serves a thin read-only operator cockpit for the ATLAS root.

It exists to present the current awareness slice cleanly, not to add a new state system.

Boundary:

- the cockpit is a client
- the Awareness API and root read model remain the source of truth
- no write, execute, resume, proposal, or approval controls are exposed
- no local cache or private state is persisted by the cockpit

## Sources Of Truth

The cockpit reads from the existing stack surfaces only:

- `ops/atlas/awareness.py`
- `ops/atlas/serve_awareness.py`
- `ops/cortex/render_status.py`
- `runtime/state/atlas/world-model.*.latest.json`
- `runtime/cortex/artifacts/**`
- `stack.lock.yaml`

Operational rule:

- root selects context
- child repos own truth
- the cockpit only renders the current read model

## What It Shows

- active conversation and active session state
- active initiatives
- attention queue
- repo work waiting on blessing review
- latest governed proposal and proposal-only conversation state
- repo inventory state
- lock and worktree hygiene state
- trust posture, including Verta as visible, untrusted, and metadata-only
- focused operator paths from active initiatives and proposal state when present

## Running

Directly from the root read model:

```powershell
python ops/atlas/cockpit.py
```

Through the Awareness API:

```powershell
python ops/atlas/serve_awareness.py
python ops/atlas/cockpit.py --awareness-base-url http://127.0.0.1:8765
```

With bearer auth for the upstream Awareness API:

```powershell
python ops/atlas/cockpit.py --awareness-base-url http://127.0.0.1:8765 --auth-token-file secrets/local/atlas-awareness.token
```

Remote bind with cockpit auth enforced:

```powershell
python ops/atlas/cockpit.py --host 0.0.0.0 --port 8786 --server-auth-token-file secrets/local/atlas-cockpit.token
```

JSON-only verification:

```powershell
python ops/atlas/cockpit.py --dump-json
```

## Read-Only Boundary

The cockpit deliberately omits:

- execute buttons
- resume buttons
- proposal buttons
- approval controls
- local mutation or cache files

If a future lane adds controls, they must call existing governed entrypoints exactly. This cockpit lane does not do that.

Remote-bind rule:

- loopback binds may run without cockpit auth for local operator use
- non-loopback binds fail closed unless `--server-auth-token` or `--server-auth-token-file` is configured
- when cockpit auth is configured, both `/` and `/api/cockpit` require a bearer token

## Example Views

Playbook convergence projection:

- root summary shows `verified_count=2`
- `fitness` and `mazer` project as bounded `verified` at `verification_scope=targeted`
- root consumes owner-repo verification artifacts read-only instead of restating repo truth as a second source

Verta trust posture:

- visible in trust posture
- `trust_class: untrusted`
- `read_mode: metadata_only`
- not promoted

## Verification

Confirm all of the following:

1. The cockpit answers what is active, what needs attention, and what repo work is waiting on blessing review.
2. The latest governed proposal is visible and proposal-only conversation state is visible separately.
3. The Playbook convergence card shows `verified_count=2` and projects `fitness` and `mazer` as targeted `verified` without implying broader certification.
4. Lock and worktree hygiene answer whether the lock is frozen and which repos are dirty or drifted.
5. Verta appears as visible, untrusted, and metadata-only.
6. `python ops/validation/validate_stack.py --ratchet` stays green.
