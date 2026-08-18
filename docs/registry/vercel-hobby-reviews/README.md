# Vercel Hobby-plan review-override records

This directory is the tracked, source-owned home for `keep_hobby` review-override
records consumed by `ops/atlas/vercel_hobby_decision_checkpoint.py`. It replaces
`data/atlas/qa/vercel-hobby-cost-governance/`, which `.gitignore` excludes
wholesale and therefore never survived a fresh clone or hosted CI checkout.

**No active review record is created by this change.** This directory is
currently empty of instance files. That is correct: a review record must
correspond to a real, current generated guardrail signature and an explicit
human review -- neither of which this change performs. Fabricating a
`keep_hobby` approval merely to populate the path would defeat the point of
the control.

## Filename convention

`{repo_id}.latest.json`, e.g. `fitness.latest.json`.

## Record contract

Each record must conform to `schemas/atlas.vercel-hobby-review.v1.json`
(closed schema, enforced at runtime by `_load_matching_review()`, not only in
tests). Required fields: `contract_version`, `repo_id`, `checkpoint_status`,
`decision`, `accepted_signature_digest`, `accepted_drift_fields`.

Optional fields `decision_reason` and `next_action` are operator-authored
presentation text, propagated through unchanged into the resulting
checkpoint's `decision_reason` / `next_action` output fields. Neither
participates in digest authorization, drift-field coverage, or any other
matching/authority logic -- only `accepted_signature_digest` and
`accepted_drift_fields` do that.

## What this record is -- and is not

- `target_sha`, if present, is **audit-only**. It is surfaced as
  `review_target_sha` / `review_target_sha_authority: "audit_only"` and is
  never validated against anything -- there is no independently trustworthy
  source for "the guardrail's current source commit" to check it against.
- This is **ordinary Git-reviewed governance evidence, not independent
  cryptographic attestation**. Nothing in this codebase requires the review
  commit to come from a different author than the drift-state commit; the
  control's strength is ordinary git-history auditability (an override is
  always a traceable, reviewable commit).
- A review only unblocks a `keep_hobby` decision when its
  `accepted_signature_digest` exactly matches the *current* guardrail
  comparison signature and its `accepted_drift_fields` is a superset of every
  *currently*-drifted field. A stale review (wrong digest, or one that
  doesn't cover newly-drifted fields) fails closed to
  `upgrade_review_required`, the same as having no review at all.

## Adding a real review

1. Generate the current guardrail report and decision checkpoint for the
   `repo_id` in question.
2. Have a human review the actual drift and explicitly decide `keep_hobby`.
3. Commit `{repo_id}.latest.json` here, matching the schema, with
   `accepted_signature_digest` bound to the signature the reviewer actually
   looked at.
4. `tests/test_atlas_vercel_hobby_registry_contracts.py` enumerates and
   schema-validates every record found here -- zero records is valid, and a
   correctly-shaped new record requires no test-code changes to be accepted.
