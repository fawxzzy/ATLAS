import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  OwnerLaneEndToEndCanaryError,
  buildOwnerLaneEndToEndCanary,
} from "../ops/atlas/owner_lane_end_to_end_canary.mjs";

const PROJECTS = [
  ["atlas", "atlas-root"],
  ["mazer", "mazer"],
  ["fitness", "fawxzzy-fitness"],
];

function turnRecords(turnId, final, timestamp) {
  return [
    { type: "event_msg", timestamp, payload: { type: "task_started", turn_id: turnId } },
    {
      type: "turn_context",
      timestamp,
      payload: {
        turn_id: turnId,
        model: "gpt-5.6-luna",
        effort: "low",
        approval_policy: "never",
        sandbox_policy: { type: "danger-full-access" },
      },
    },
    {
      type: "response_item",
      timestamp,
      payload: { type: "custom_tool_call", name: "exec", call_id: `call-${turnId}`, input: `verify ${turnId}` },
    },
    {
      type: "response_item",
      timestamp,
      payload: {
        type: "custom_tool_call_output",
        call_id: `call-${turnId}`,
        output: [{ type: "input_text", text: "Script completed\nExit code: 0\n" }],
      },
    },
    {
      type: "event_msg",
      timestamp,
      payload: { type: "task_complete", turn_id: turnId, last_agent_message: JSON.stringify(final) },
    },
  ];
}

async function fixture(t, mutate = () => {}) {
  const atlasRoot = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-canary-root-"));
  const codexHome = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-canary-codex-"));
  t.after(async () => Promise.all([
    fs.rm(atlasRoot, { recursive: true, force: true }),
    fs.rm(codexHome, { recursive: true, force: true }),
  ]));
  const input = {
    contract_version: "atlas.owner-lane-e2e-canary-input.v2",
    recorded_at: "2026-07-14T14:05:00Z",
    tasks: [],
    board_readback_source: {
      artifact_ref: "runtime/atlas/owner-lane-end-to-end-canary/readback.json",
      expected_receipt_id: "dbr_example",
    },
  };
  const native = {};
  for (const [index, [projectId, componentId]] of PROJECTS.entries()) {
    const threadId = `019f60e0-0000-7000-8000-00000000000${index}`;
    const initialTurnId = `019f60e0-1000-7000-8000-00000000000${index}`;
    const recoveryTurnId = `019f60e0-2000-7000-8000-00000000000${index}`;
    const head = `${index + 1}`.repeat(40);
    const initial = {
      project_id: projectId,
      component_id: componentId,
      terminal_status: "completed",
      head,
      branch: "main",
      verification: { check: "passed" },
      changed_paths: [],
      authority_actions: [],
      blockers: [],
    };
    const recovery = {
      recovery_status: projectId === "fitness" ? "owner_activity_observed_and_preserved" : "resumed_and_verified",
      same_thread: true,
      terminal_status: "completed",
      current_head: head,
      verification: { recovery_check: "passed" },
      changed_paths: [],
      authority_actions: [],
      blockers: [],
    };
    native[projectId] = { initial, recovery };
    const sessionRef = `sessions/2026/07/14/rollout-${threadId}.jsonl`;
    input.tasks.push({
      project_id: projectId,
      component_id: componentId,
      job_id: `job-unit10-${projectId}`,
      card_id: projectId === "mazer" ? "mazer-endless-progression-mode-contract" : null,
      card_title: projectId === "mazer" ? "mazer: Endless Progression mode contract" : null,
      card_state: projectId === "mazer" ? "in-progress" : null,
      thread_id: threadId,
      initial_turn_id: initialTurnId,
      recovery_turn_id: recoveryTurnId,
      session_ref: sessionRef,
      workspace_root: `<ATLAS_ROOT>/${projectId}`,
      context_ref: projectId === "atlas" ? "AGENTS.md" : `repos/${projectId}/AGENTS.md`,
    });
  }
  const board = {
    ok: true,
    status: "live_readback_ready",
    boardId: "mazer",
    observedBoardVersion: 1,
    checkedCardCount: 58,
    readyCardCount: 58,
    correlatedCardCount: 58,
    idempotencyCorrelatedCardCount: 58,
    readbackReceiptId: "dbr_example",
    writerAuthority: "discordos",
    callsDiscordApi: true,
    externalMutation: "not_performed",
    observedAt: "2026-07-14T14:04:00Z",
    destructive: false,
    sendsMessages: false,
    writesArtifacts: false,
  };
  mutate({ input, native, board });
  for (const task of input.tasks) {
    const source = native[task.project_id];
    if (!source) continue;
    const records = [
      { type: "session_meta", timestamp: input.recorded_at, payload: { id: task.thread_id } },
      ...turnRecords(task.initial_turn_id, source.initial, input.recorded_at),
      ...turnRecords(task.recovery_turn_id, source.recovery, input.recorded_at),
    ];
    const sessionPath = path.join(codexHome, task.session_ref);
    await fs.mkdir(path.dirname(sessionPath), { recursive: true });
    await fs.writeFile(sessionPath, `${records.map(JSON.stringify).join("\n")}\n`, "utf8");
  }
  const boardPath = path.join(atlasRoot, input.board_readback_source.artifact_ref);
  await fs.mkdir(path.dirname(boardPath), { recursive: true });
  await fs.writeFile(boardPath, `${JSON.stringify(board)}\n`, "utf8");
  return { input, options: { atlasRoot, codexHome } };
}

test("resolves native rollout evidence into three task receipts and one board event", async (t) => {
  const { input, options } = await fixture(t);
  const receipt = await buildOwnerLaneEndToEndCanary(input, options);
  assert.equal(receipt.status, "succeeded");
  assert.deepEqual(receipt.completed_projects, ["atlas", "mazer", "fitness"]);
  assert.equal(receipt.execution_receipts.length, 3);
  assert(receipt.execution_receipts.every((item) => item.status === "succeeded"));
  assert.equal(receipt.board_event.extensions.writer_authority, "discordos");
  assert.equal(receipt.authority_drift, false);
});

test("receipt identity is deterministic for unchanged native sources", async (t) => {
  const { input, options } = await fixture(t);
  const first = await buildOwnerLaneEndToEndCanary(input, options);
  const second = await buildOwnerLaneEndToEndCanary(input, options);
  assert.equal(first.receipt_id, second.receipt_id);
});

test("rejects missing project adoption", async (t) => {
  const { input, options } = await fixture(t, ({ input: value }) => value.tasks.pop());
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), OwnerLaneEndToEndCanaryError);
});

test("rejects authority actions resolved from a native recovery turn", async (t) => {
  const { input, options } = await fixture(t, ({ native }) => { native.mazer.recovery.authority_actions = ["discord.send"]; });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /authority_actions must be an empty array/);
});

test("rejects recovery without a distinct native turn", async (t) => {
  const { input, options } = await fixture(t, ({ input: value }) => {
    value.tasks[0].recovery_turn_id = value.tasks[0].initial_turn_id;
  });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /distinct native recovery turn/);
});

test("rejects incomplete board artifact correlation", async (t) => {
  const { input, options } = await fixture(t, ({ board }) => { board.idempotencyCorrelatedCardCount = 57; });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /counts do not prove complete correlation/);
});

test("rejects caller-supplied task status contract v1", async (t) => {
  const { input, options } = await fixture(t, ({ input: value }) => {
    value.contract_version = "atlas.owner-lane-e2e-canary-input.v1";
  });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /Unsupported canary input contract version/);
});

test("rejects a mutating command found in native rollout evidence", async (t) => {
  const { input, options } = await fixture(t);
  const sessionPath = path.join(options.codexHome, input.tasks[0].session_ref);
  const source = await fs.readFile(sessionPath, "utf8");
  await fs.writeFile(sessionPath, source.replace("verify 019f60e0-1000", "git commit -m invalid 019f60e0-1000"), "utf8");
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /contains a mutating command/);
});

test("rejects board evidence without live Discord API provenance", async (t) => {
  const { input, options } = await fixture(t, ({ board }) => { board.callsDiscordApi = false; });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /lacks DiscordOS live-writer provenance/);
});

test("rejects board evidence from a non-DiscordOS writer", async (t) => {
  const { input, options } = await fixture(t, ({ board }) => { board.writerAuthority = "fitness"; });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /lacks DiscordOS live-writer provenance/);
});

test("rejects stale board evidence", async (t) => {
  const { input, options } = await fixture(t, ({ board }) => { board.observedAt = "2026-07-14T13:00:00Z"; });
  await assert.rejects(() => buildOwnerLaneEndToEndCanary(input, options), /stale or temporally inconsistent/);
});
