# Discord Feedback Rollout Issues Note — 2026-05-25

## Purpose
- Record the concrete issues encountered while stabilizing the Fitness-owned Discord feedback workflow.
- Preserve the difference between resolved issues, residual debt, and blockers for later rollout lanes.
- Keep this operational context in ATLAS instead of chat memory.

## Scope
- Fitness-owned Discord feedback workflow
- Completed-board recovery and duplicate cleanup
- DiscordOS separation-adjacent feedback shaping
- Deploy-backed rollout readiness

## Issues Encountered

### 1. Production deployment lag blocked truthful rollout closeout
- Intended rollout steps were:
  - refresh the launcher with `/setup-feedback` or `computa setup feedback`
  - update feedback card `16d98fc2`
  - make the governed `Update:` post in `#updates`
- These steps were intentionally held because Vercel production had not actually advanced to the feedback-submission implementation commit line.
- Verified state:
  - current local Fitness history includes `a71269b0` (`feat: move discord feedback intake to dedicated channel`)
  - later local work advanced well beyond that
  - latest visible production deployment remained on older commit `072fb3c04db1d84717ca1635895fed27ea7373da`
- Rule reinforced:
  - do not claim a Discord workflow change is live until production is verifiably on the required commit.

### 2. Vercel deployment provenance is still noisy
- Recent production deployments show mixed provenance:
  - direct-style `gitCommitRef: HEAD`
  - recurring `gitDirty: 1`
  - not every deployment clearly maps to the expected governed rollout artifact
- Impact:
  - weakens confidence when deciding whether a Discord-facing workflow is truly live
  - slows rollout closeout because deployment truth requires extra manual inspection
- Follow-up:
  - keep this under Lifeline / Vercel-health / deployment-governance hardening

### 3. Feedback card formatting is not fully canonical yet
- Observed symptom:
  - some cards show type emoji placement at the front of the visible title/body treatment
  - other bug/feature cards do not match that same presentation after being touched by different flows
- Root cause:
  - title formatting and body-header formatting are split across different logic paths
  - `buildDiscordBugForumThreadTitle(...)` does not prepend type emoji
  - body-header emoji rendering depends on `buildDiscordFeedbackEmojiPrefix(...)`
  - maintenance flows do not all establish the same emoji-validation state before syncing
- Impact:
  - cards can look inconsistent even after being created or repaired by official tools
- Required future lane:
  - one canonical formatter
  - one board-wide normalization pass

### 4. Repo-local Supabase env drift blocked normal script verification
- Fitness repo-local env resolved to a non-canonical Supabase host during board repair work:
  - local env path pointed at `hcjbdxrekkbfbngrfvcv.supabase.co`
  - canonical Fitness project is `lpswxoyfniocuhljgzbc`
- Result:
  - normal repo scripts that depend on local Supabase env could not be trusted for that lane
  - MCP-backed canonical Fitness row reads were used instead
- Impact:
  - slowed feedback-board repair and forced a workaround
  - confirms that local env state is not currently reliable as rollout truth for every Discord maintenance package
- Rule reinforced:
  - when repo-local env drifts from canonical project truth, use canonical source verification before mutating anything

### 5. Discord active-thread index lag can mask successful archive operations
- During duplicate completed-card cleanup:
  - archive calls succeeded immediately
  - direct thread fetches confirmed `archived=true` and `locked=true`
  - immediate follow-up active-thread scans still temporarily showed the same threads
- After short settling time, a fresh scan drained to zero duplicates
- Impact:
  - a naive immediate re-scan can look like the archive failed even when Discord has already applied the state
- Rule reinforced:
  - verify archive state directly on the thread when Discord thread-list lag is suspected

### 6. One historical board target remains structurally incomplete
- Residual note from board-state repair:
  - thread `1505779648250908734` still reports `starter_message_unavailable`
- Impact:
  - this is not an active duplicate-completed blocker
  - it remains historical board residue that may need a later targeted cleanup lane

### 7. Existing repo residue still complicates scoped Fitness work
- The Fitness repo still contains unrelated preexisting tracked changes outside the Discord feedback lane.
- Impact:
  - every scoped package still requires careful staging discipline
  - commit hygiene remains manual instead of effortless

## What Is Resolved
- Completed board exists and is populated for the intended recovered/mirrored finished cards
- Duplicate completed source-board copies were archived and locked
- Feedback board state was repaired so completed cards show success and non-completed cards show failure
- Fitness-side feedback runtime boundary is isolated
- DiscordOS feedback contract docs, interfaces, and adapter stubs exist

## What Is Still Open
- deploy-backed proof that the feedback-submission UX is live in production
- card-format normalization so all touched cards share one canonical presentation
- repo-local Supabase env truth repair or explicit documented split
- broader Vercel deployment provenance cleanup

## Recommended Next Lanes
1. Deploy-backed Fitness production verification for the feedback-submission rollout
2. Discord feedback card format canonicalization and board-wide normalization
3. Fitness env/source-truth repair for Discord maintenance scripts
4. Lifeline/Vercel deployment provenance hardening

## Validation Expectation
- This note is documentation only.
- Root stack validation should still run after adding it.
