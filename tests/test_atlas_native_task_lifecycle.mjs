import assert from "node:assert/strict";
import test from "node:test";

import { NativeTaskLifecycleError, buildLifecycleEvent } from "../ops/atlas/native_task_lifecycle.mjs";

const base = {
  jobId: "job-lifecycle-001",
  componentId: "atlas-root",
  threadId: "thread-001",
  turnId: "turn-001",
};

async function event(action, occurredAt, previousEvent = null, extra = {}) {
  return buildLifecycleEvent({ ...base, action, occurredAt, previousEvent, ...extra });
}

test("builds deterministic admitted and running events", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  const duplicate = await event("admit", "2026-07-14T05:00:00Z");
  assert.equal(admitted.event_id, duplicate.event_id);
  assert.equal(admitted.payload.attempt, 1);
  const running = await event("start", "2026-07-14T05:01:00Z", admitted);
  assert.equal(running.payload.from_state, "admitted");
  assert.equal(running.payload.to_state, "running");
  assert.equal(running.payload.sequence, 2);
});

test("supports awaiting review and success", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  const running = await event("start", "2026-07-14T05:01:00Z", admitted);
  const review = await event("await-review", "2026-07-14T05:02:00Z", running);
  const succeeded = await event("succeed", "2026-07-14T05:03:00Z", review);
  assert.equal(succeeded.payload.to_state, "succeeded");
  assert.equal(succeeded.payload.terminal, true);
});

test("retry increments attempt after failure", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  const running = await event("start", "2026-07-14T05:01:00Z", admitted);
  const failed = await event("fail", "2026-07-14T05:02:00Z", running, { reason: "fixture failure" });
  const retry = await event("retry", "2026-07-14T05:03:00Z", failed);
  assert.equal(retry.payload.attempt, 2);
  assert.equal(retry.payload.to_state, "admitted");
});

test("replay records the prior terminal event", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  const running = await event("start", "2026-07-14T05:01:00Z", admitted);
  const succeeded = await event("succeed", "2026-07-14T05:02:00Z", running);
  const replay = await event("replay", "2026-07-14T05:03:00Z", succeeded);
  assert.equal(replay.payload.replay_of, succeeded.event_id);
  assert.equal(replay.payload.attempt, 2);
});

test("archive requires a receipt and terminal predecessor", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  const running = await event("start", "2026-07-14T05:01:00Z", admitted);
  const succeeded = await event("succeed", "2026-07-14T05:02:00Z", running);
  await assert.rejects(
    event("archive", "2026-07-14T05:03:00Z", succeeded),
    (error) => error instanceof NativeTaskLifecycleError && error.message.includes("receipt_id"),
  );
  const archived = await event("archive", "2026-07-14T05:03:00Z", succeeded, { receiptId: "atr_001" });
  assert.equal(archived.payload.to_state, "archived");
  assert.equal(archived.links[0].href, "atr_001");
});

test("rejects invalid transitions", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  await assert.rejects(
    event("succeed", "2026-07-14T05:01:00Z", admitted),
    (error) => error instanceof NativeTaskLifecycleError && error.message.includes("Invalid lifecycle transition"),
  );
});

test("rejects identity drift", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  await assert.rejects(
    buildLifecycleEvent({ ...base, threadId: "thread-other", action: "start", occurredAt: "2026-07-14T05:01:00Z", previousEvent: admitted }),
    (error) => error instanceof NativeTaskLifecycleError && error.message.includes("identity"),
  );
  await assert.rejects(
    buildLifecycleEvent({ ...base, componentId: "component-other", action: "start", occurredAt: "2026-07-14T05:01:00Z", previousEvent: admitted }),
    (error) => error instanceof NativeTaskLifecycleError && error.message.includes("identity"),
  );
});

test("rejects backward time", async () => {
  const admitted = await event("admit", "2026-07-14T05:00:00Z");
  await assert.rejects(
    event("start", "2026-07-14T04:59:00Z", admitted),
    (error) => error instanceof NativeTaskLifecycleError && error.message.includes("cannot move backward"),
  );
});
