# Verta-Core Scrub Report

## Scope

This report covers the scrubbed Verta launcher/config/docs surfaces used to produce the sanitized knowledge candidate. The raw imported zip evidence at `data/imports/knowledge/personal/verta-core/raw/Verta-Core.zip` was not mutated.

## Actions

| File | Finding | Action |
| --- | --- | --- |
| `repos/Verta-Core/Verta-Core/.claude/launcher/launch_verta_core_with_auth.ps1` | Hardcoded auth flow and working-root details | Replaced with a placeholder template and local-only variables |
| `repos/Verta-Core/Verta-Core/.claude/launcher/launch_verta_with_auth.ps1` | Hardcoded auth flow and working-root details | Replaced with a placeholder template and local-only variables |
| `repos/Verta-Core/Verta-Core/.claude/launcher/README.md` | Launcher docs described live endpoints and user-local paths | Replaced with a sanitized template note |
| `repos/Verta-Core/Verta-Core/CLAUDE_RUNS_FROM_HERE.md` | User-home launch guidance and workspace path leakage | Replaced with a placeholder note |
| `repos/Verta-Core/Verta-Core/data/archive/config/teams_auth.example.json` | Sample auth config and secret-style field names | Replaced with placeholders and removed secret-style wording |
| `repos/Verta-Core/Verta-Core/CLEANUP_EXECUTION.sh` | Cleanup steps referenced sensitive values directly | Replaced with a template-only shell stub |
| `repos/Verta-Core/Verta-Core/FINAL_CLEANUP.bat` | Cleanup steps referenced sensitive values directly | Replaced with a template-only batch stub |
| `repos/Verta-Core/Verta-Core/EVOLVING.md` | Runtime-root and auth wording was concrete | Replaced with a sanitized placeholder |
| `repos/Verta-Core/Verta-Core/HOMEOSTASIS_ACHIEVED.md` | Concrete launch-root and auth wording | Replaced with a sanitized placeholder |
| `repos/Verta-Core/Verta-Core/LAUNCH_CLAUDE_CODE.bat` | Hardcoded local workspace path | Replaced with a template-only batch stub |
| `repos/Verta-Core/Verta-Core/LAUNCH_VERTA_CLAUDE.bat` | Hardcoded auth value references | Replaced with a template-only batch stub using generic local-value placeholders |
| `repos/Verta-Core/Verta-Core/LAUNCHER_FIX_REQUIRED.md` | Shortcut target and user-home path leakage | Replaced with a sanitized placeholder |
| `repos/Verta-Core/Verta-Core/LAUNCHER_SETUP_COMPLETE.md` | Concrete launcher and auth details | Replaced with a sanitized placeholder |
| `repos/Verta-Core/Verta-Core/SNAPSHOT_PRE_FORK.txt` | Concrete host path and sensitive-value wording | Replaced with a sanitized placeholder |
| `repos/Verta-Core/Verta-Core/START_HERE.md` | Concrete working-root guidance | Replaced with a sanitized placeholder |
| `repos/Verta-Core/Verta-Core/UPDATE_SHORTCUT.bat` | Shortcut target leaked local workspace details | Replaced with a template-only batch stub |
| `repos/Verta-Core/Verta-Core/VERTA_QUICK_START.bat` | Hardcoded local workspace path | Replaced with a template-only batch stub |
| `repos/Verta-Core/Verta-Core/verta_launcher.bat` | Hardcoded local workspace path | Replaced with a template-only batch stub |

## Candidate Exports

- exploratory full-repo import: `personal--verta-core-clean`
- sanitized candidate import: `personal--verta-core-sanitized`

## Verification

- clean candidate secret scan: no blocking secret-pattern hits in the curated export
- import: completed for `personal--verta-core-sanitized`
- evaluation: `safe_for_indexing = restricted`, `indexing_profile = metadata_only`, `promotion_status = not_promoted`
- normalization: completed for `personal--verta-core-sanitized`
- promotion: not attempted

## Residuals

- The original `personal--verta-core` archive remains quarantined and not promoted.
- The exploratory whole-repo candidate `personal--verta-core-clean` still carries broader private/courseware/executable signals and stays quarantined.
