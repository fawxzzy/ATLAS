import assert from "node:assert/strict";
import fs from "node:fs/promises";
import test from "node:test";

import {
  buildGateReceipt,
  validateEngineeringMemoryGate,
} from "../ops/atlas/engineering_memory_gate.mjs";

const profileFixture = JSON.parse(
  await fs.readFile(new URL("../packages/atlas-contracts/fixtures/valid/engineering-memory-profile.v1.json", import.meta.url), "utf8"),
);

function makeJob(profile = structuredClone(profileFixture)) {
  return {
    contract_version: "atlas.job-envelope.v2",
    job_id: profile.task_id,
    component_id: "fitness",
    project_id: profile.project,
    created_at: "2026-08-20T12:01:00Z",
    objective: profile.normalized_title,
    scope: {
      owner_repository: profile.repo,
      allowed_paths: ["src/components/ui/app/**", "src/app/globals.css"],
      forbidden_paths: ["supabase/**"],
    },
    runtime: { model: "gpt-5.6-terra", reasoning: "medium", speed: "standard", permissions: "full-access", approval_policy: "never" },
    authority: {
      external_mutations: [],
      production_deploy: false,
      destructive_actions: false,
    },
    verification: { commands: ["npm run verify"], evidence_required: ["visual-proof"] },
    correlations: { card_id: "FITNESS-PWA-001", parent_job_id: null },
    expected_receipt_version: "atlas.execution-receipt.v2",
    extensions: { engineering_memory: profile },
  };
}

function makeCard(lifecycle = "ready") {
  return {
    contract_version: "atlas.card-record.v2",
    card_id: "FITNESS-PWA-001",
    project_id: "fitness",
    board_id: "atlas:fitness",
    title: "Remove phantom standalone bottom spacing",
    description: "Dry-run card for engineering-memory enforcement.",
    card_type: "bug",
    lifecycle,
    priority: "high",
    owner: "fitness",
    dependencies: [],
    board_version: 1,
    updated_at: "2026-08-20T12:01:00Z",
    source_ref: "operator-request",
  };
}

function verifiedProfile() {
  const profile = structuredClone(profileFixture);
  profile.phase = "verified";
  profile.verification.unverified = [];
  profile.verification.evidence = [
    { kind: "test", ref: "runtime/fitness/verify.json", result: "passed", surfaces: [] },
    {
      kind: "screenshot",
      ref: "tmp/captures/fitness-pwa-parity.png",
      result: "passed",
      surfaces: [
        profile.verification.visual.source_surface,
        ...profile.verification.visual.target_surfaces,
      ],
    },
  ];
  return profile;
}

test("passes the mutation gate only after task, card, and precedent evidence are bound", async () => {
  const result = await validateEngineeringMemoryGate({ job: makeJob(), card: makeCard(), gate: "mutation" });
  assert.deepEqual(result, { ok: true, errors: [] });
});

test("blocks mutation when the canonical current-repo precedent search is missing", async () => {
  const profile = structuredClone(profileFixture);
  profile.precedent_check.searched_sources = profile.precedent_check.searched_sources.filter((source) => source.kind !== "current_repo");
  const result = await validateEngineeringMemoryGate({ job: makeJob(profile), card: makeCard(), gate: "mutation" });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((error) => error.includes("current_repo")));
});

test("blocks parity wording that was normalized as a generic visual change", async () => {
  const profile = structuredClone(profileFixture);
  profile.source_text = "Make the gameplay settings control match the main menu control.";
  profile.task_type = "visual_change";
  const result = await validateEngineeringMemoryGate({ job: makeJob(profile), card: makeCard(), gate: "mutation" });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((error) => error.includes("task_type ui_parity")));
});

test("blocks verified visual work without evidence for every source and target surface", async () => {
  const profile = verifiedProfile();
  profile.verification.evidence[1].surfaces = [profile.verification.visual.source_surface];
  const result = await validateEngineeringMemoryGate({ job: makeJob(profile), card: makeCard("review"), gate: "verify" });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((error) => error.includes("missing required surface")));
});

test("passes verification with technical and route-aware visual evidence", async () => {
  const profile = verifiedProfile();
  const result = await validateEngineeringMemoryGate({ job: makeJob(profile), card: makeCard("review"), gate: "verify" });
  assert.deepEqual(result, { ok: true, errors: [] });
});

test("requires a repository-visible archive before complete closeout", async () => {
  const profile = verifiedProfile();
  profile.phase = "archived";
  profile.archive = {
    status: "created",
    ref: "docs/architecture/VISUAL-CHANGE-WORKFLOW.md",
    final_status: "complete",
  };
  const receipt = await buildGateReceipt({ job: makeJob(profile), card: makeCard("archived"), gate: "archive" });
  assert.equal(receipt.status, "passed");
  assert.match(receipt.receipt_id, /^aemg_[a-f0-9]{24}$/);
});

test("blocks fast-lane classification when protected boundary language is present", async () => {
  const profile = structuredClone(profileFixture);
  profile.fast_lane = {
    lane: "fast",
    eligible: true,
    verification_route_known: true,
    disqualifiers: [],
    rationale: "Small source edit.",
  };
  profile.source_text = "Make the production auth screen match the other screen.";
  profile.task_type = "ui_parity";
  const result = await validateEngineeringMemoryGate({ job: makeJob(profile), card: makeCard(), gate: "mutation" });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((error) => error.includes("Fast-lane work cannot cross")));
});
