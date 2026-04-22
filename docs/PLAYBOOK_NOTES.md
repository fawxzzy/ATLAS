# Playbook Notes

## Deploy identity guards

- Production deploy guards should validate the configured live hosting identity for the current lane, not a guessed future owner or namespace.
- For Vercel-backed repos, keep the expected scope and project in checked-in operator config and allow explicit environment overrides for one-off validation.
- Treat visible team-label cleanup and namespace changes as separate lanes. Namespace changes can alter future generated hosting URLs and should not be bundled into an unrelated production deploy.
- Hosting identity checks must validate immutable team/project IDs, not only mutable slugs or display names.
- Use connector-confirmed project identity as source of truth, then mirror that identity into operator deploy guards and repo-local `.vercel/project.json` metadata.
- Failure Mode: A team rename makes slug-only checks lie, which looks like a wrong-owner failure even when the linked Vercel project is correct.
- If Vercel sees the correct team and project but a fresh pushed SHA creates no deployment object, classify it as a Git integration ingestion failure before diagnosing app code or retrying production deploys from the CLI.
- After connector repair, prefer one fresh Git-triggered branch deployment as the proof path; only resume production shipping after Vercel creates and runs that branch deployment from Git.
- Failure Mode: Repeated CLI production retries can mask the real issue when Git-connected preview creation is disabled or dead, which makes an ingestion outage look like an app or build failure.
- Failure Mode: A mounted app folder under `C:\ATLAS` inherits the parent repo boundary and poisons Git recovery until the app is recloned as a real standalone repo.
- Failure Mode: Windows prebuilt deploy fallback can fail on symlink packaging; do not diagnose app code from that signal alone.
