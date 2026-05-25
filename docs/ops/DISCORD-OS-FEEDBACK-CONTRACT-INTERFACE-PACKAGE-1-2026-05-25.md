# DiscordOS Feedback Contract Interface Package 1 - 2026-05-25

## Scope

- Repo: `repos/DiscordOS`
- Mode: code-facing contract scaffold only
- No Fitness code copy
- No runtime behavior
- No Supabase client
- No Vercel config
- No env files

## Goal

Add typed feedback-domain interfaces that mirror the governed contract documented in `repos/DiscordOS/docs/contracts/feedback-runtime.md` so later Fitness-to-DiscordOS extraction has a stable code seam.

## Inputs

- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `docs/ops/DISCORD-OS-FEEDBACK-CONTRACT-SCAFFOLD-PACKAGE-1-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`

## Files Changed

- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/contracts/index.ts`
- `repos/DiscordOS/README.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`

## Interfaces Added

The new code-facing seam defines only types and port names for:

- `FeedbackCardIdentity`
- `FeedbackStatus`
- `FeedbackCompletionReviewStatus`
- `FeedbackAuditEvent`
- `FeedbackCompletionReviewEvent`
- `FitnessReportReference`
- `DiscordOSFeedbackRuntimeState`
- `DiscordOSFeedbackResult`
- `FeedbackReportStorePort`
- `FeedbackLookupPort`
- `FeedbackThreadSyncPort`
- `FeedbackAuditPort`
- `FeedbackPermissionPort`

## What Did Not Happen

This package intentionally did **not**:

- copy Fitness `helpers.ts`
- copy Fitness `forum.ts`
- copy Fitness `bug-reports.ts`
- add a Supabase client
- add bot runtime code
- add Vercel config
- add `.env` files
- add external dependencies
- add DiscordOS runtime implementation

## Tooling Decision

DiscordOS still has no package manager or TypeScript runtime/tooling surface.

Decision:

- keep the interface package compile-ready but untooled
- do not introduce `package.json`, `tsconfig.json`, or a typecheck pipeline just to hold the seam

## Verification

From `repos/DiscordOS` before changes:

- `git status --short`: clean

From `repos/DiscordOS` after changes, before commit:

- only expected files changed:
  - `README.md`
  - `docs/contracts/feedback-runtime.md`
  - `src/contracts/feedback.ts`
  - `src/contracts/index.ts`

Additional checks:

- `.env*` files present in `repos/DiscordOS`: `0`
- no Fitness application files were copied into the repo
- no runtime dependencies or service clients were introduced

Typecheck:

- not run

Reason:

- DiscordOS does not yet have local TypeScript tooling
- this package intentionally avoided introducing package/runtime scaffolding

From ATLAS root:

```text
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

Result:

- root validation passed: `critical=0 error=0 warning=289`

## Stack Metadata Decision

- no `stack.yaml` update was required
- no `stack.lock.yaml` update was required

Reason:

- `repos/DiscordOS` was already registered during bootstrap
- `discordos` is not being reclassified or newly lock-tracked by this package

## Result

DiscordOS now has a tiny code-facing feedback contract seam that matches the governed docs contract while still avoiding premature runtime, database, or deployment coupling.

## Next Safe Move

The next clean package remains narrow:

- implement adapter-facing stubs or interface consumers only after a specific extraction package names them, or
- continue with contract-first planning for the next DiscordOS-owned domain without copying live Fitness runtime code
