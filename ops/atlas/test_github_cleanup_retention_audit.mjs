import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyRetention,
  parseWorktreeList,
  renderMarkdown,
} from "./github_cleanup_retention_audit.mjs";

test("parses branch, detached, and prunable worktree records", () => {
  const parsed = parseWorktreeList([
    "worktree fixture/atlas",
    "HEAD abc123",
    "branch refs/heads/main",
    "",
    "worktree fixture/atlas-worktrees/repro",
    "HEAD def456",
    "detached",
    "prunable gitdir file points to non-existent location",
    "",
  ].join("\n"));

  assert.deepEqual(parsed, [
    {
      path: "fixture/atlas",
      head: "abc123",
      branch: "main",
      detached: false,
      prunable: false,
    },
    {
      path: "fixture/atlas-worktrees/repro",
      head: "def456",
      branch: null,
      detached: true,
      prunable: true,
    },
  ]);
});

test("classifies every preservation state fail-closed", () => {
  const base = {
    present: true,
    repositoryAvailable: true,
    dirtyCount: 0,
    openPullRequest: null,
    detached: false,
    mergedIntoDefault: false,
  };

  assert.equal(classifyRetention({ ...base, repositoryAvailable: false }), "repository_unavailable_hold");
  assert.equal(classifyRetention({ ...base, present: false }), "missing_registration_hold");
  assert.equal(classifyRetention({ ...base, dirtyCount: 2 }), "dirty_uncommitted_work_hold");
  assert.equal(classifyRetention({ ...base, openPullRequest: { number: 1 } }), "open_pull_request_hold");
  assert.equal(classifyRetention({ ...base, detached: true }), "detached_reproduction_hold");
  assert.equal(classifyRetention({ ...base, mergedIntoDefault: true }), "merged_clean_candidate_hold");
  assert.equal(classifyRetention(base), "unmerged_branch_hold");
});

test("renders a no-mutation governance report", () => {
  const markdown = renderMarkdown({
    captured_at: "2026-07-13T00:00:00Z",
    summary: {
      cleanup_governance_classification_complete: true,
      local_worktree_candidate_count: 1,
      explicit_local_retention_count: 1,
      unknown_local_retention_count: 0,
      remote_branch_candidate_count: 2,
    },
    local_worktree_candidates: [
      {
        repository: "ATLAS",
        registered_path: "tmp/example",
        external_locator: null,
        registered_branch: "codex/example",
        observed: {
          branch: "codex/example",
          dirty_count: 0,
          merged_into_default: true,
        },
        retention_class: "merged_clean_candidate_hold",
      },
    ],
  });

  assert.match(markdown, /No cleanup mutation is authorized/);
  assert.match(markdown, /Removal-safe candidates: `0`/);
  assert.match(markdown, /merged_clean_candidate_hold/);
  assert.doesNotMatch(markdown, /\n\n$/);
});
