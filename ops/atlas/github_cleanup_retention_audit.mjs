import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const modulePath = fileURLToPath(import.meta.url);
const moduleDir = path.dirname(modulePath);
const defaultAtlasRoot = path.resolve(moduleDir, "..", "..");

const HOLD_CLASSES = Object.freeze([
  "dirty_uncommitted_work_hold",
  "open_pull_request_hold",
  "detached_reproduction_hold",
  "merged_clean_candidate_hold",
  "unmerged_branch_hold",
  "missing_registration_hold",
  "repository_unavailable_hold",
]);

function stableValue(value) {
  if (Array.isArray(value)) {
    return value.map((entry) => stableValue(entry));
  }

  if (value === null || typeof value !== "object") {
    return value;
  }

  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, stableValue(value[key])]),
  );
}

function stableStringify(value, { pretty = false } = {}) {
  return JSON.stringify(stableValue(value), null, pretty ? 2 : 0);
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function normalizePath(value) {
  return path.resolve(value).replaceAll("\\", "/").toLowerCase();
}

function parseArgs(argv) {
  const args = {
    atlasRoot: defaultAtlasRoot,
    registryPath: null,
    jsonPath: null,
    markdownPath: null,
    capturedAt: null,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (argument === "--atlas-root") {
      args.atlasRoot = path.resolve(value);
      index += 1;
    } else if (argument === "--registry") {
      args.registryPath = path.resolve(value);
      index += 1;
    } else if (argument === "--json") {
      args.jsonPath = path.resolve(value);
      index += 1;
    } else if (argument === "--markdown") {
      args.markdownPath = path.resolve(value);
      index += 1;
    } else if (argument === "--captured-at") {
      args.capturedAt = value;
      index += 1;
    } else if (argument === "--help") {
      args.help = true;
    } else {
      throw new Error(`Unknown or incomplete argument: ${argument}`);
    }
  }

  args.registryPath ??= path.join(
    args.atlasRoot,
    "docs",
    "registry",
    "GITHUB-CONTROL-PLANE-REGISTRY.json",
  );
  args.capturedAt ??= new Date().toISOString();
  return args;
}

function runGit(cwd, args, { allowFailure = false } = {}) {
  const result = spawnSync("git", ["-C", cwd, ...args], {
    encoding: "utf8",
    windowsHide: true,
  });

  if (result.error) {
    if (allowFailure) {
      return { ok: false, status: null, stdout: "", stderr: result.error.message };
    }
    throw result.error;
  }

  const ok = result.status === 0;
  if (!ok && !allowFailure) {
    throw new Error(
      `git -C ${cwd} ${args.join(" ")} failed: ${result.stderr.trim() || result.stdout.trim()}`,
    );
  }

  return {
    ok,
    status: result.status,
    stdout: result.stdout,
    stderr: result.stderr,
  };
}

export function parseWorktreeList(raw) {
  const entries = [];
  let current = null;

  for (const line of raw.split(/\r?\n/)) {
    if (line.startsWith("worktree ")) {
      if (current) {
        entries.push(current);
      }
      current = {
        path: line.slice("worktree ".length),
        head: null,
        branch: null,
        detached: false,
        prunable: false,
      };
    } else if (!current) {
      continue;
    } else if (line.startsWith("HEAD ")) {
      current.head = line.slice("HEAD ".length);
    } else if (line.startsWith("branch refs/heads/")) {
      current.branch = line.slice("branch refs/heads/".length);
    } else if (line === "detached") {
      current.detached = true;
    } else if (line.startsWith("prunable")) {
      current.prunable = true;
    }
  }

  if (current) {
    entries.push(current);
  }
  return entries;
}

export function classifyRetention({
  present,
  repositoryAvailable,
  dirtyCount,
  openPullRequest,
  detached,
  mergedIntoDefault,
}) {
  if (!repositoryAvailable) {
    return "repository_unavailable_hold";
  }
  if (!present) {
    return "missing_registration_hold";
  }
  if (dirtyCount > 0) {
    return "dirty_uncommitted_work_hold";
  }
  if (openPullRequest) {
    return "open_pull_request_hold";
  }
  if (detached) {
    return "detached_reproduction_hold";
  }
  if (mergedIntoDefault) {
    return "merged_clean_candidate_hold";
  }
  return "unmerged_branch_hold";
}

function resolveDefaultRef(repoPath, defaultBranch) {
  const candidates = [
    `refs/remotes/origin/${defaultBranch}`,
    `refs/heads/${defaultBranch}`,
  ];

  for (const candidate of candidates) {
    const result = runGit(repoPath, ["rev-parse", "--verify", candidate], {
      allowFailure: true,
    });
    if (result.ok) {
      return { ref: candidate, head: result.stdout.trim() };
    }
  }
  return { ref: null, head: null };
}

function candidatePath(atlasRoot, candidate) {
  return candidate.path ? path.resolve(atlasRoot, candidate.path) : null;
}

function matchWorktree(candidate, liveWorktrees, expectedPath) {
  if (expectedPath) {
    const expected = normalizePath(expectedPath);
    const byPath = liveWorktrees.find((entry) => normalizePath(entry.path) === expected);
    if (byPath) {
      return byPath;
    }
  }

  if (candidate.branch) {
    const byBranch = liveWorktrees.find((entry) => entry.branch === candidate.branch);
    if (byBranch) {
      return byBranch;
    }
  }

  if (candidate.head) {
    return liveWorktrees.find((entry) => entry.head === candidate.head) ?? null;
  }
  return null;
}

function inspectRepository(atlasRoot, repository) {
  if (!repository.local?.path) {
    return {
      available: false,
      repoPath: null,
      worktrees: [],
      defaultRef: { ref: null, head: null },
    };
  }

  const repoPath = path.resolve(atlasRoot, repository.local.path);
  const probe = runGit(repoPath, ["rev-parse", "--git-dir"], { allowFailure: true });
  if (!probe.ok) {
    return {
      available: false,
      repoPath,
      worktrees: [],
      defaultRef: { ref: null, head: null },
    };
  }

  const list = runGit(repoPath, ["worktree", "list", "--porcelain"]);
  const defaultBranch = repository.cloud?.default_branch ?? "main";
  return {
    available: true,
    repoPath,
    worktrees: parseWorktreeList(list.stdout),
    defaultRef: resolveDefaultRef(repoPath, defaultBranch),
  };
}

function dirtyPaths(worktreePath) {
  const result = runGit(
    worktreePath,
    ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    { allowFailure: true },
  );
  if (!result.ok) {
    return { count: null, paths: [], error: result.stderr.trim() || "git_status_failed" };
  }

  const entries = result.stdout.split("\0").filter(Boolean);
  return {
    count: entries.length,
    paths: entries.map((entry) => entry.slice(3)).sort(),
    error: null,
  };
}

function isMerged(repoPath, head, defaultRef) {
  if (!head || !defaultRef) {
    return null;
  }
  const result = runGit(
    repoPath,
    ["merge-base", "--is-ancestor", head, defaultRef],
    { allowFailure: true },
  );
  if (result.status === 0) {
    return true;
  }
  if (result.status === 1) {
    return false;
  }
  return null;
}

function classifyLocalCandidates(atlasRoot, repository) {
  const inspection = inspectRepository(atlasRoot, repository);
  const openPullRequests = new Map(
    (repository.open_work?.pull_requests ?? [])
      .filter((entry) => entry.head)
      .map((entry) => [entry.head, entry]),
  );

  return (repository.cleanup?.local_worktree_candidates ?? []).map((candidate) => {
    const expectedPath = candidatePath(atlasRoot, candidate);
    const live = inspection.available
      ? matchWorktree(candidate, inspection.worktrees, expectedPath)
      : null;
    const status = live ? dirtyPaths(live.path) : { count: null, paths: [], error: null };
    const openPullRequest = live?.branch
      ? openPullRequests.get(live.branch) ?? null
      : candidate.branch
        ? openPullRequests.get(candidate.branch) ?? null
        : null;
    const mergedIntoDefault = live && inspection.available
      ? isMerged(inspection.repoPath, live.head, inspection.defaultRef.ref)
      : null;
    const retentionClass = classifyRetention({
      present: Boolean(live),
      repositoryAvailable: inspection.available,
      dirtyCount: status.count ?? 0,
      openPullRequest,
      detached: live?.detached ?? candidate.detached ?? false,
      mergedIntoDefault,
    });

    return {
      repository: repository.name,
      logical_id: repository.logical_id,
      registered_path: candidate.path ?? null,
      external_locator: candidate.external_locator ?? null,
      registered_branch: candidate.branch ?? null,
      registered_head: candidate.head ?? null,
      observed: {
        present: Boolean(live),
        branch: live?.branch ?? null,
        head: live?.head ?? null,
        detached: live?.detached ?? candidate.detached ?? false,
        prunable: live?.prunable ?? candidate.prunable ?? false,
        dirty_count: status.count,
        dirty_paths: status.paths,
        status_error: status.error,
        default_ref: inspection.defaultRef.ref,
        default_head: inspection.defaultRef.head,
        merged_into_default: mergedIntoDefault,
        open_pull_request: openPullRequest
          ? {
              number: openPullRequest.number,
              url: openPullRequest.url,
              draft: openPullRequest.draft,
            }
          : null,
      },
      retention_class: retentionClass,
      retention_basis: retentionBasis(retentionClass),
      removal_safe: false,
      automatic_cleanup_authorized: false,
      required_removal_receipt: "required_before_removal",
    };
  });
}

function retentionBasis(retentionClass) {
  const bases = {
    dirty_uncommitted_work_hold: "The worktree has uncommitted files and must remain preserved.",
    open_pull_request_hold: "The worktree branch is tied to an open pull request in the accepted GitHub registry.",
    detached_reproduction_hold: "The detached worktree is retained as reproduction or forensic evidence.",
    merged_clean_candidate_hold: "The clean worktree head is reachable from the observed default ref; removal still requires explicit authority and a receipt.",
    unmerged_branch_hold: "The clean worktree head is not proven merged into the observed default ref.",
    missing_registration_hold: "The registered worktree could not be matched to current Git worktree state and requires owner review.",
    repository_unavailable_hold: "The registered repository checkout was unavailable, so the candidate remains preserved for owner review.",
  };
  return bases[retentionClass];
}

function classifyRemoteCandidates(repository) {
  return (repository.cleanup?.merged_remote_branch_candidates ?? []).map((candidate) => ({
    repository: repository.name,
    logical_id: repository.logical_id,
    branch: candidate.branch,
    head: candidate.head,
    comparison_status: candidate.comparison_status,
    ahead_by: candidate.ahead_by,
    behind_by: candidate.behind_by,
    retention_class: "merged_remote_branch_candidate_hold",
    retention_basis: "The accepted registry classifies this branch as fully merged; deletion remains unauthorized until a separate mutation receipt exists.",
    removal_safe: false,
    automatic_cleanup_authorized: false,
    required_removal_receipt: "required_before_removal",
  }));
}

function countBy(items, key) {
  const counts = {};
  for (const item of items) {
    counts[item[key]] = (counts[item[key]] ?? 0) + 1;
  }
  return Object.fromEntries(Object.entries(counts).sort(([a], [b]) => a.localeCompare(b)));
}

export function auditRegistry(registry, { atlasRoot, capturedAt, sourceDigest }) {
  const localCandidates = registry.repositories.flatMap((repository) =>
    classifyLocalCandidates(atlasRoot, repository),
  );
  const remoteCandidates = registry.repositories.flatMap((repository) =>
    classifyRemoteCandidates(repository),
  );
  const invalidClasses = localCandidates
    .filter((candidate) => !HOLD_CLASSES.includes(candidate.retention_class));
  const unknownCount = localCandidates
    .filter((candidate) => candidate.retention_class === "UNKNOWN").length;

  return {
    schema_version: "atlas.github.cleanup-retention-audit.v1",
    captured_at: capturedAt,
    source_registry: {
      schema_version: registry.schema_version,
      generated_at: registry.generated_at,
      sha256: sourceDigest,
    },
    authority: {
      mode: "classification_only",
      deletion_authorized: false,
      branch_deletion_authorized: false,
      worktree_removal_authorized: false,
      archive_authorized: false,
      remote_mutation_performed: false,
      local_removal_performed: false,
    },
    summary: {
      repository_count: registry.repositories.length,
      local_worktree_candidate_count: localCandidates.length,
      remote_branch_candidate_count: remoteCandidates.length,
      explicit_local_retention_count: localCandidates.length - unknownCount,
      unknown_local_retention_count: unknownCount,
      invalid_local_retention_count: invalidClasses.length,
      local_retention_classes: countBy(localCandidates, "retention_class"),
      remote_retention_classes: countBy(remoteCandidates, "retention_class"),
      cleanup_governance_classification_complete:
        localCandidates.length === registry.cleanup_summaries.local_worktree_candidate_count
        && remoteCandidates.length === registry.cleanup_summaries.merged_remote_branch_candidate_count
        && unknownCount === 0
        && invalidClasses.length === 0,
    },
    local_worktree_candidates: localCandidates,
    remote_branch_candidates: remoteCandidates,
  };
}

export function renderMarkdown(audit) {
  const lines = [
    "# GitHub Cleanup Retention Classification",
    "",
    `Captured: \`${audit.captured_at}\``,
    "",
    "## Decision",
    "",
    audit.summary.cleanup_governance_classification_complete
      ? "All accepted remote-branch and local-worktree candidates have explicit retention classes. No cleanup mutation is authorized."
      : "Classification is incomplete. No cleanup mutation is authorized.",
    "",
    "## Summary",
    "",
    `- Local worktree candidates: \`${audit.summary.local_worktree_candidate_count}\``,
    `- Explicit local retention classes: \`${audit.summary.explicit_local_retention_count}\``,
    `- Unknown local retention classes: \`${audit.summary.unknown_local_retention_count}\``,
    `- Remote branch candidates: \`${audit.summary.remote_branch_candidate_count}\``,
    "- Removal-safe candidates: `0`",
    "- Deletion, pruning, archive, and worktree removal authority: `false`",
    "",
    "## Local Worktrees",
    "",
    "| Repository | Registered path or locator | Branch | Dirty | Merged | Retention class |",
    "|---|---|---|---:|---|---|",
  ];

  for (const candidate of audit.local_worktree_candidates) {
    const location = candidate.registered_path ?? candidate.external_locator ?? "unresolved";
    lines.push(
      `| ${candidate.repository} | \`${location}\` | \`${candidate.observed.branch ?? candidate.registered_branch ?? "detached"}\` | ${candidate.observed.dirty_count ?? "unknown"} | ${candidate.observed.merged_into_default ?? "unknown"} | \`${candidate.retention_class}\` |`,
    );
  }

  lines.push(
    "",
    "## Remote Branches",
    "",
    `All \`${audit.summary.remote_branch_candidate_count}\` accepted merged-remote candidates are classified as \`merged_remote_branch_candidate_hold\`. They remain removal-unsafe until a separate, explicitly authorized deletion receipt is produced.`,
    "",
    "## Governance",
    "",
    "- Classification is not cleanup authority.",
    "- Clean is not removal-safe.",
    "- Dirty, unmerged, detached, open-PR, missing, and unavailable candidates remain preserved.",
    "- Every eventual removal requires a correlated pre/post receipt and explicit authority.",
    "",
  );
  return `${lines.join("\n").trimEnd()}\n`;
}

function writeArtifact(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
}

function printHelp() {
  process.stdout.write([
    "Usage: node ops/atlas/github_cleanup_retention_audit.mjs [options]",
    "",
    "Options:",
    "  --atlas-root <path>",
    "  --registry <path>",
    "  --json <path>",
    "  --markdown <path>",
    "  --captured-at <ISO-8601>",
    "  --help",
    "",
  ].join("\n"));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  const rawRegistry = fs.readFileSync(args.registryPath, "utf8");
  const registry = JSON.parse(rawRegistry);
  const audit = auditRegistry(registry, {
    atlasRoot: args.atlasRoot,
    capturedAt: args.capturedAt,
    sourceDigest: sha256(rawRegistry),
  });
  const json = `${stableStringify(audit, { pretty: true })}\n`;
  const markdown = renderMarkdown(audit);

  if (args.jsonPath) {
    writeArtifact(args.jsonPath, json);
  }
  if (args.markdownPath) {
    writeArtifact(args.markdownPath, markdown);
  }
  if (!args.jsonPath && !args.markdownPath) {
    process.stdout.write(json);
  }

  if (!audit.summary.cleanup_governance_classification_complete) {
    process.exitCode = 2;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === modulePath) {
  main().catch((error) => {
    process.stderr.write(`${error.stack ?? error.message}\n`);
    process.exitCode = 1;
  });
}
