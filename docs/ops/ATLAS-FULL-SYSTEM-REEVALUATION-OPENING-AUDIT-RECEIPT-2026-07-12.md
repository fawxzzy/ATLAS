# Atlas Full-System Re-evaluation Opening Audit Receipt — 2026-07-12

This receipt accepts the exhaustive opening gate and only the `Atlas Full-System Re-evaluation` transition from 0 to 50. It does not claim current stack health, execute a child lane, resume an owner lane, mutate an external plane, publish, commit, or push.

## `atlas_full_system_opening_audit_receipt` object

```json
{
  "receipt_type": "atlas_full_system_opening_audit_receipt",
  "status": "governed_success_pending_parent_publication",
    "marker_transition": {"marker": "Atlas Full-System Re-evaluation", "from": 0, "to": 50, "gate": "opening"},
    "marker": {"name": "Atlas Full-System Re-evaluation", "completed_units": 1, "denominator": 2, "unit": "accepted exhaustive audit gate", "discovered_work_points": 0, "closing_gate": "blocked until a separate later accepted exhaustive closing audit"},
    "paths": {
      "audit": "docs/audits/ATLAS-FULL-SYSTEM-OPENING-AUDIT-2026-07-12.md",
      "marker": "docs/atlas-book/02-lanes-and-markers.md",
      "lane_registry": "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json",
      "continuity_manifest": "docs/memory/initiatives/continuity-manifest-atlas-full-system-re-evaluation.json",
      "restart_guide": "docs/atlas-book/12-restart-and-handoff-guide.md",
      "receipt": "docs/ops/ATLAS-FULL-SYSTEM-REEVALUATION-OPENING-AUDIT-RECEIPT-2026-07-12.md"
    },
    "artifact_hashes": {
      "docs/audits/ATLAS-FULL-SYSTEM-OPENING-AUDIT-2026-07-12.md": "F39FC7D5E91A7FDD58713479795702A42FA745C6980D006BA1A301733B7CF919",
      "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json": "48091B1ED43A81FE8967B16D2ECF27D15606B78F788E7D1FA673835070246582",
      "docs/memory/initiatives/continuity-manifest-atlas-full-system-re-evaluation.json": "A11EB8810DB80B958DA422A70FD8F3B0B902958ABAD574BE9F19B14493ED6E74"
    },
    "primary_lane_ids": [
      "lane-root-truth-convergence", "lane-github-control-plane-integration", "lane-playbook-universal-adoption", "lane-atlas-contracts-mesh", "lane-cortex-context-synthesis", "lane-codex-execution-contracts", "lane-project-command-surfaces", "lane-atlas-control-ledger", "lane-delivery-event-plane", "lane-discordos-single-writer", "lane-persistent-workspaces", "lane-cross-project-knowledge-promotion", "lane-ci-delivery-health", "lane-marker-integrity", "lane-workspace-branch-worktree-hygiene", "lane-security-containment", "lane-historical-task-intelligence", "lane-vercel-supabase-monitoring-correlation"
    ],
    "backlog_lane_ids": [
      "lane-stack-adapter-coverage", "lane-local-branch-retention-classification", "lane-stack-inventory-lock-head-reconciliation", "lane-playbook-demo-contract-synchronization", "lane-fitness-atlas-contracts-loader", "lane-fitness-playbook-runtime-artifacts", "lane-fitness-dependency-security", "lane-fitness-critical-secret-containment", "lane-default-branch-governance", "lane-dependabot-visibility", "lane-release-policy-and-evidence", "lane-remote-branch-cleanup-review", "lane-local-worktree-retention-classification", "lane-cortex-boundary-decision", "lane-stream-remote-decision", "lane-stack-github-event-contracts", "lane-discordos-github-projections", "lane-source-hierarchy-doc-normalization", "lane-component-generated-state-hygiene", "lane-archive-package-retention", "lane-owner-metric-scope-alignment", "lane-root-path-hygiene", "lane-discordos-command-surface-convergence", "lane-supabase-security-advisor-remediation", "lane-mazer-legacy-nested-repo-admission", "lane-foundation-control-plane-truth-reconciliation", "lane-sensitive-runtime-residue-containment", "lane-nat1-remote-recovery", "lane-trove-command-path-repair", "lane-mazer-board-truth-reconciliation", "lane-validation-ratchet-remediation"
    ],
    "opening_validation_snapshot": {
      "source": "runtime/receipts/validation/stack-validation.latest.json",
      "generated_at": "2026-07-12T11:26:09.595602Z",
      "critical": 0,
      "error": 4,
      "warning": 25,
      "info": 0,
      "errors": [
        {"category": "stack-lock-drift", "path": "stack.lock.yaml", "message": "Stack lockfile does not match the current pinned working set."},
        {"category": "stack-lock-render-drift", "path": "stack.lock.yaml", "message": "Stack lockfile bytes do not match the canonical generated lockfile payload."},
        {"category": "stack-lock-pin-drift", "path": "stack.lock.yaml#_stack", "message": "pinned component fields differ from the current generated working set: commit."},
        {"category": "stack-lock-missing-ref", "path": "stack.lock.yaml#_stack", "message": "pinned `2127af207370cacf8752fd4f13c6545ea49bb503` does not match current `_stack` HEAD `5ea6b712b91a691689b619addb8f8ba649126661`."}
      ],
      "warning_work_items": [
        {"id": "root-preserved-untracked-path-hygiene", "count": 16, "path": "docs/ops/ATLAS-CURRENT-STATE-INTELLIGENCE-PACKET-2026-07-10.md", "lines": [16,25,41,134,340,355,356,357,358,359,360,361,362,363,364,365], "lane_id": "lane-root-path-hygiene"},
        {"id": "owner-stack-path-hygiene", "count": 9, "paths": ["repos/_stack/AGENTS.md:18", "repos/_stack/README.md:23", "repos/_stack/README.md:207", "repos/_stack/docs/canonical-atlas-workspace-writer.md:3", "repos/_stack/docs/canonical-atlas-workspace-writer.md:13", "repos/_stack/docs/canonical-atlas-workspace-writer.md:113", "repos/_stack/docs/codex-orchestration.md:164", "repos/_stack/docs/codex-orchestration.md:469", "repos/_stack/docs/dispatcher-protocol.md:38"], "lane_id": "lane-root-path-hygiene"}
      ],
      "warning_work_item_total": 25,
      "label": "pre-package opening observation",
      "interpretation": "The frozen 0/4/25/0 observation does not claim current health; its discoveries are externalized and do not block the opening discovery gate."
    },
    "final_validation": {
      "source": "runtime/receipts/validation/stack-validation.latest.json",
      "label": "post-package final validation",
      "critical": 0,
      "error": 5,
      "warning": 25,
      "info": 0,
      "errors": [
        {"category": "working-memory-catalog-drift", "path": "runtime/cortex/catalog/memory/working-memory.latest.json", "message": "Working-memory catalog does not match the current structured memory documents."},
        {"category": "stack-lock-drift", "path": "stack.lock.yaml", "message": "Stack lockfile does not match the current pinned working set."},
        {"category": "stack-lock-render-drift", "path": "stack.lock.yaml", "message": "Stack lockfile bytes do not match the canonical generated lockfile payload."},
        {"category": "stack-lock-pin-drift", "path": "stack.lock.yaml#_stack", "message": "Pinned component fields differ from the current generated working set: commit."},
        {"category": "stack-lock-missing-ref", "path": "stack.lock.yaml#_stack", "message": "Pinned commit '2127af207370cacf8752fd4f13c6545ea49bb503' does not match current HEAD '5ea6b712b91a691689b619addb8f8ba649126661'."}
      ],
      "warning_work_item_total": 25,
      "interpretation": "The authoritative non-ratchet final result includes the same 16 preserved-root and 9 owner-_stack path warnings plus the five exact errors. The new working-memory catalog drift follows the required continuity manifest; the other four are existing lock/head debt. No clean-health claim is made."
    },
    "ratchet_remediation": {"lane_id":"lane-validation-ratchet-remediation","statement":"Ratchet remediation is a separate lane, not an opening-audit success criterion.","opening_audit_gate":"not evaluated by --ratchet","later_success_required":true},
    "continuity_validation": {"manifest_count": 23, "ok": 23, "warning": 0, "error": 0, "eligible_execution_open_marker_backed": "8/8", "eligible_execution_open_marker_restart_ready": "8/8", "audit_gate_marker_backed": true, "audit_gate_restart_ready": true, "total_open_markers_including_audit_gate": 9, "maintained_manifest_restart_ready": "23/23", "pending_review": 0},
    "owner_resume": {
      "mazer": {"resume_allowed_after_publication": true, "resume_effective": false, "standing_task_id":"019f52e6-3b96-78b0-adb4-946b475f4ba6", "gate_reconciliation":"The 0-to-50 opening gate is governed-success pending parent publication; guarded publication and ATLAS MAIN review still precede the explicit RESUME MAZER message.", "reason": "No Fitness-like Critical secret blocker was found; preserve the canonical dirty file, dirty turnlive worktree, eight Mazer candidate worktrees, all registered worktrees, and the preserved checkpoint."},
      "fitness": {"resume_allowed": false, "reason": "Published open Critical secret-scanning alert #1 for a Supabase service key requires explicit operator-authorized containment, rotation, and verification; the value is never included, and history remediation and alert closure are separate decisions."}
    },
    "mazer": {"resume_allowed_after_publication": true, "resume_effective": false, "standing_task_id":"019f52e6-3b96-78b0-adb4-946b475f4ba6", "gate_reconciliation":"The 0-to-50 opening gate is governed-success pending parent publication; corrective runner success, guarded publication, and ATLAS MAIN review still precede the explicit RESUME MAZER message.", "reason": "No Fitness-like Critical secret blocker was found; preserve the canonical dirty file, dirty turnlive worktree, eight Mazer candidate worktrees, all registered worktrees, and the preserved checkpoint."},
    "fitness": {"resume_allowed": false, "reason": "Published open Critical secret-scanning alert #1 for a Supabase service key requires explicit operator-authorized containment, rotation, and verification; the value is never included, and history remediation and alert closure are separate decisions."},
    "baseline": {"branch": "main", "commit": "845d1802095cd8458806285bf2b053778b120f90", "origin_ahead": 0, "origin_behind": 0, "published_subject": "docs(github): establish control-plane opening audit"},
    "publication": {"state":"pending_parent_publication", "commit_subject": "docs(atlas): record opening full-system audit", "commit_sha": "pending_parent_publication", "push_parity": "pending_parent_publication", "push_performed": false},
    "recovery_control": {"stashes":[{"name":"atlas-full-system-opening-audit-13-path-recovery-2026-07-12","oid":"5595299105c20b361f13653708de3030cc3fbd11","payload_count":13,"payload_verified_exact":true,"pop_or_drop_performed":false},{"name":"atlas-full-system-opening-audit-terra-validation-recovery-2026-07-12","oid":"5e93dad8dccab196370737413d0e7e60bc0f8cca","payload_count":13,"payload_verified_exact":true,"pop_or_drop_performed":false},{"name":"atlas-full-system-opening-audit-terra-semantic-recovery-2026-07-12","oid":"e9fe1190afc7468c6b52b3c642db47b3099dd070","payload_count":13,"payload_verified_exact":true,"pop_or_drop_performed":false}],"pop_or_drop_performed":false,"preserve_or_cleanup":"deferred until reviewed"},
    "two_commit_recovery": {"worker_created_commit":"34fa6c713d79dc4717c52b7dd7f5046cb785b389","runner_status_at_first_commit":"verification_failed","publication_authorized_only_after_corrective_runner_success":true,"required_pre_push_parity":"0 2","required_post_push_parity":"0 0","history_rewrite_prohibited":["amend","reset","rebase","squash","revert","rewrite"]},
    "runtime": {
      "codex_version": "codex-cli 0.144.1",
      "requested": {"model": "gpt-5.6-sol", "reasoning": "xhigh", "reasoning_display": "Ultra/extra-high mapping", "speed": "standard", "permissions": {"mode": "full-access", "permission_profile": ":danger-full-access", "sandbox_mode": null}},
      "effective": {"model": "gpt-5.6-sol", "model_probe": "accepted", "reasoning": "xhigh", "speed": "standard", "permissions": {"mode": "full-access", "permission_profile": ":danger-full-access", "sandbox_mode": null}, "approval": "never", "web_search": "live"},
      "fast_forbidden": true
    },
    "preserved_inventory": [
      {"path":"d/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-ai-corpus-board","head":"b1f852f33aea69a97734c9c16f06cca713279d8c","status":"clean","parity":"0/0"},
      {"path":"d2/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-ai-metric-board","head":"ce8998f60be471b593a93db97645ad80934b552c","status":"clean","parity":"0/0"},
      {"path":"d3/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-board-epic-reconciliation","head":"41455a3013315638030d59cea66bc061552815dd","status":"clean","parity":"no upstream"},
      {"path":"d4/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-ui-evidence-board-update","head":"41fffe73b9ea07fa62ec67e10b14dc854028708a","status":"clean","parity":"no upstream"},
      {"path":"d5/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-player-input-evidence","head":"6f9cd30e049c04f9bbb3dd43aa4cc8e8ee79aaa7","status":"clean","parity":"0/0"},
      {"path":"d6/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-play-loop-evidence","head":"69b8d95e52f9d0b17f39d744f56e7bcd89c4c2ad","status":"clean","parity":"0/0"},
      {"path":"d7/","owner":"DiscordOS","class":"registered_worktree","branch":"codex/mazer-world-turn-evidence","head":"015b92afe5ce2f73b25d2c5cae80fe3e5ca1d234","status":"clean","parity":"0/0"},
      {"path":"input4/","owner":"Mazer","class":"registered_worktree","branch":"codex/player-input-movement-correctness","head":"9759ce22f68746ca73a294695fb28449cfc6a76e","status":"clean","parity":"no upstream"},
      {"path":"m2/","owner":"Mazer","class":"registered_worktree","branch":"codex/ai-metric-contract-parity","head":"e11ab6e5c677f1f8d2859be310122f3c73b7a605","status":"clean","parity":"0/0"},
      {"path":"playloop/","owner":"Mazer","class":"registered_worktree","branch":"codex/play-mode-perpetual-loop","head":"e9647e77b48e71b4df7b8dd7c14d3cc2652b3f61","status":"clean","parity":"0/0"},
      {"path":"turnlive/","owner":"Mazer","class":"registered_worktree","branch":"codex/world-turn-live-integration","head":"8ced175c65cfb36bb057cf25e93f59819c57803b","status":"dirty","modified_files":["scripts/analysis/live-play-qa.mjs","src/scenes/MenuScene.ts","src/scenes/menuRuntimeDiagnostics.ts","tests/reset/live-play-qa-script.test.mjs","tests/scenes/menu-render-frame.test.ts"]},
      {"path":"turnsim/","owner":"Mazer","class":"registered_worktree","branch":"codex/turn-synchronous-world-simulation","head":"cf94ede0127a802108c7261556a61af4c9f5df8a","status":"clean","parity":"0/0"},
      {"path":"ui3/","owner":"Mazer","class":"registered_worktree","branch":"codex/cross-platform-ui-followup","head":"a27324a422809c577b29e66a53b84ed94c6cb163","status":"clean","parity":"no upstream"},
      {"path":"docs/codex/MAZER-WAVE-2-RESUME-HANDOFF-2026-07-11.md","owner":"stack-root","class":"preserved_untracked_file","sha256":"39FD57F7700F5E824F53E58E442DC55A593C89CDC518BE013E8D02028BDADDC5"},
      {"path":"docs/memory/initiatives/initiative-mazer-wave2-metric-contract-parity.json","owner":"stack-root","class":"preserved_untracked_file","sha256":"CC1B9CC7B14A52F0BCE6D86E853CE2916DEDC775F7671FA6A326DB97D2569478"},
      {"path":"docs/memory/plans/plan-mazer-wave2-to-wave5-resume.json","owner":"stack-root","class":"preserved_untracked_file","sha256":"B27D95DEB018F43BAB7FD84C306279E417AC329C5BA5EDEDBF9DCE16821D5EC6"},
      {"path":"docs/ops/ATLAS-CURRENT-STATE-INTELLIGENCE-PACKET-2026-07-10.md","owner":"stack-root","class":"preserved_untracked_file","sha256":"B8D1A1618F0FD3C050C6A550E5795AF98256D8B04D06133EF76285871CEF6993"}
    ],
    "prohibited_action_confirmations": {"owner_repo_mutation":false,"external_mutation":false,"secret_value_access":false,"discord_write":false,"supabase_write":false,"vercel_deploy_or_promotion":false,"github_cleanup":false,"branch_or_worktree_cleanup":false,"retention_action":false,"stack_lock_unchanged":true,"continuity_manifest_intentionally_created_in_first_admitted_package":true,"pre_existing_17_root_entries_untouched":true,"runtime_source_test_or_executable_mutation":false,"root_untracked_entry_mutation":false,"first_commit_provenance":"worker-created after runner verification_failed; the canonical runner did not record the first commit","push":false},
    "exact_next_action": "After the corrective canonical runner succeeds, confirm pre-push 0 2, push without force, fetch, confirm post-push 0 0, and obtain ATLAS MAIN review; only then may ATLAS MAIN send the explicit RESUME MAZER message to standing task 019f52e6-3b96-78b0-adb4-946b475f4ba6 from its preserved checkpoint. Fitness remains security-blocked."
}
```

## Interpretation

The receipt object is the durable opening decision. Publication fields remain `pending_parent_publication` because the canonical writer neither knows the future commit SHA nor pushes. Mazer resume is conditional on guarded publication and remains ineffective in this committed receipt. The parent runner must report terminal Git truth. The audit, registry, and continuity manifest are frozen at the SHA-256 values above and must not be modified after this point.
