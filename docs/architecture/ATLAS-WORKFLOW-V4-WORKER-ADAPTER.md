# ATLAS Workflow V4 worker-adapter boundary

This Wave 1B contract describes the identity and evidence boundary between the
V4 runtime core and a future Codex worker executor.

## What it does

- Captures non-secret worker, run, process, task, requested-model, and
  effective-model identity.
- Constructs identity-bound heartbeats without sending them.
- Builds and fail-closed validates structured worker receipts.
- Renders a future Codex CLI command as a dry-run plan only.

## What it deliberately does not do

- Start Codex, spawn a process, invoke a subprocess, or mutate a Codex task.
- Claim or complete an `AtlasRuntime` task.
- Write runtime state, call GitHub/Supabase/Vercel, access credentials, or
  contact any external provider.

The future executor must persist heartbeats and pass its receipt through this
contract before the runtime core accepts a terminal state. The requested and
effective model profile are both mandatory so a fallback cannot be mistaken for
the requested policy.

## Verification

Run:

```powershell
python -m unittest tests.test_atlas_worker_adapter -v
```

The tests construct only in-memory Python values and spawn no worker.
