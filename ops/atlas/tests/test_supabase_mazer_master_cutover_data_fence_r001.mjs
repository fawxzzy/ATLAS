import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import {
  CONTRACT,
  CutoverHold,
  classifyAclObservation,
  classifyAclRecoveryObservation,
  classifyCutover,
  classifyRecoveryState,
  classifyWriterCapture,
  renderAclObservationSql,
  renderFenceSql,
  renderLockBarrierSql,
  renderRestoreSql,
  renderWriterCaptureSql,
  renderWriterDrainSql,
  sha256,
  snapshotDigest
} from '../classify_supabase_mazer_master_cutover_data_fence_r001.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const classifierPath = path.join(root, 'ops/atlas/classify_supabase_mazer_master_cutover_data_fence_r001.mjs');
const uid = (value) => `00000000-0000-4000-8000-${String(value).padStart(12, '0')}`;
const digest = (value) => sha256(`fixture:${value}`);
const iso = (minute) => `2026-08-24T19:${String(minute).padStart(2, '0')}:00.000Z`;

const ids = Object.freeze({
  legacyA: uid(1),
  legacyB: uid(2),
  legacyC: uid(3),
  masterA: uid(101),
  masterB: uid(102),
  masterC: uid(103),
  receipt1: uid(201),
  receipt2: uid(202),
  receipt3: uid(203),
  receipt4: uid(204),
  run1: uid(301),
  run2: uid(302),
  run3: uid(303),
  run4: uid(304)
});

function profile(userId, revision, username = null) {
  const row = {
    user_id: userId,
    display_name: null,
    selected_control_mode: 'stick',
    settings: { trailFade: true },
    created_at: iso(1),
    updated_at: iso(2),
    revision,
    username
  };
  return {
    user_id: userId,
    revision,
    username_present: username !== null,
    username_digest: username === null ? null : sha256(username.toLowerCase()),
    payload_digest: sha256(row),
    row
  };
}

function player(userId, level, completedCycles, revision = 0, targetComplexity = 8, rank = 'E') {
  const levelDecimal = typeof level === 'bigint' ? level.toString() : String(level);
  const cyclesDecimal = typeof completedCycles === 'bigint' ? completedCycles.toString() : String(completedCycles);
  const row = {
    user_id: userId,
    schema_version: 1,
    state: { tracks: { player: { level: levelDecimal, completedCycles: cyclesDecimal, targetComplexity } } },
    last_completed_cycle_at: BigInt(cyclesDecimal) > 0n ? iso(3) : null,
    created_at: iso(1),
    updated_at: iso(3),
    player_level: levelDecimal,
    player_rank: rank,
    player_target_complexity: targetComplexity,
    player_completed_cycles: cyclesDecimal,
    revision,
    level_reached_at: BigInt(cyclesDecimal) > 0n ? iso(3) : null
  };
  return {
    user_id: userId,
    level: levelDecimal,
    completed_cycles: cyclesDecimal,
    revision,
    target_complexity: targetComplexity,
    rank,
    state_projection_matches: true,
    payload_digest: sha256(row),
    row
  };
}

function ai(userId, level, completedCycles, targetComplexity = 8, rank = 'E') {
  const levelDecimal = typeof level === 'bigint' ? level.toString() : String(level);
  const cyclesDecimal = typeof completedCycles === 'bigint' ? completedCycles.toString() : String(completedCycles);
  const row = {
    user_id: userId,
    runner_key: 'menu-runner',
    schema_version: 1,
    state: { level: levelDecimal, completedCycles: cyclesDecimal, targetComplexity },
    summary: { level: levelDecimal, completedCycles: cyclesDecimal, targetComplexity },
    level: levelDecimal,
    rank,
    target_complexity: targetComplexity,
    completed_cycles: cyclesDecimal,
    last_completed_cycle_at: BigInt(cyclesDecimal) > 0n ? iso(3) : null,
    created_at: iso(1),
    updated_at: iso(3)
  };
  return {
    user_id: userId,
    runner_key: 'menu-runner',
    level: levelDecimal,
    completed_cycles: cyclesDecimal,
    target_complexity: targetComplexity,
    rank,
    state_projection_matches: true,
    payload_digest: sha256(row),
    row
  };
}

function receipt(userId, id, clientRunId, payload = 'same') {
  const row = {
    id,
    user_id: userId,
    surface: 'play',
    maze_seed: 7,
    maze_size: 37,
    route_quality: 'multi-route',
    start_cell: {},
    goal_cell: {},
    path_length: 20,
    wrong_turns: 1,
    backtracks: 0,
    completion_time_ms: 2000,
    reset_used: false,
    control_mode: 'stick',
    average_frame_ms: 16.667,
    receipt: { fixturePayload: payload },
    completed_at: iso(3),
    created_at: iso(3),
    ruleset_id: 'legacy-v1',
    recipe_version: null,
    recipe_hash: null,
    client_run_id: clientRunId
  };
  return {
    id,
    user_id: userId,
    client_run_id: clientRunId,
    // User ownership is conserved separately; the common payload digest is
    // intentionally stable across the source-to-canonical UUID rewrite.
    payload_digest: sha256({ ...row, user_id: '__mapped-owner__' }),
    row
  };
}

function auth(userId, label) {
  return { user_id: userId, email_digest: digest(label), identity_count: 1, email_identity_count: 1, ambiguous: false };
}

function snapshot({ observedAt, users, profiles, playerRows, aiRows, receipts }) {
  return {
    observed_at: observedAt,
    auth: users,
    profiles,
    player: playerRows,
    ai: aiRows,
    receipts
  };
}

function aclPreimage(schema) {
  const tableAcl = [...CONTRACT.tables].sort().map((name) => ({
    name,
    grants: name === 'mazer_profiles'
      ? [
          { grantee: 'authenticated', privilege: 'INSERT', is_grantable: false },
          { grantee: 'authenticated', privilege: 'UPDATE', is_grantable: false }
        ]
      : []
  }));
  const rpcAcl = [...CONTRACT.mutatingRpcs].sort().map((signature) => ({
    signature,
    grants: [{ grantee: 'authenticated', is_grantable: false }]
  }));
  return {
    schema,
    table_acl: tableAcl,
    rpc_acl: rpcAcl,
    catalog: {
      tables: [...CONTRACT.tables].sort().map((name) => ({ name, relkind: 'r', rls_enabled: true, force_rls: false })),
      rpcs: [...CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, kind: 'f', security_definer: true, volatility: 'v' }))
    }
  };
}

function fenceSide({ schema, signupDisabled = undefined, hookEnabled = undefined, fencedAt = iso(10) } = {}) {
  const preimage = aclPreimage(schema);
  const value = {
    table_writers: Object.fromEntries(CONTRACT.tables.map((table) => [table, 'FENCED'])),
    rpc_writers: Object.fromEntries(CONTRACT.mutatingRpcs.map((rpc) => [rpc, 'FENCED'])),
    acl_preimage: preimage,
    acl_preimage_digest: sha256({ schema, table_acl: preimage.table_acl, rpc_acl: preimage.rpc_acl }),
    catalog_digest: sha256({ schema, catalog: preimage.catalog }),
    fenced_at: fencedAt
  };
  if (signupDisabled !== undefined) value.signup_disabled = signupDisabled;
  if (hookEnabled !== undefined) value.before_user_created_hook_enabled = hookEnabled;
  return value;
}

function baseForward() {
  const identityMap = [
    { legacy_user_id: ids.legacyA, master_user_id: ids.masterA, disposition: 'BOUND' },
    { legacy_user_id: ids.legacyB, master_user_id: ids.masterB, disposition: 'BOUND' }
  ];
  const source = snapshot({
    observedAt: iso(11),
    users: [auth(ids.legacyA, 'a'), auth(ids.legacyB, 'b')],
    profiles: [profile(ids.legacyA, 2, 'fixture-a'), profile(ids.legacyB, 1, null)],
    playerRows: [player(ids.legacyA, 4, 3, 2, 20), player(ids.legacyB, 2, 1, 1, 12)],
    aiRows: [ai(ids.legacyA, 3, 2, 16), ai(ids.legacyB, 2, 1, 12)],
    receipts: [
      receipt(ids.legacyA, ids.receipt1, ids.run1, 'overlap'),
      receipt(ids.legacyB, ids.receipt2, ids.run2, 'legacy-new')
    ]
  });
  const target = snapshot({
    observedAt: iso(9),
    users: [auth(ids.masterA, 'a'), auth(ids.masterB, 'b')],
    profiles: [profile(ids.masterA, 1, 'fixture-a')],
    playerRows: [player(ids.masterA, 3, 2, 1, 16)],
    aiRows: [ai(ids.masterA, 2, 1, 12)],
    receipts: [
      receipt(ids.masterA, ids.receipt1, ids.run1, 'overlap'),
      receipt(ids.masterA, ids.receipt3, ids.run3, 'master-only')
    ]
  });
  const appContract = {
    migration_blobs: {
      M1: '2b8495a95fca9a860571343174bfb93bcad8c5e9',
      M2: '1bbf69cf8f38aa1e2b053d0b70d82a315317b58a',
      M3: '481ab55323afff53f5e841012684b7e26f689349'
    },
    difficulty_bounds: [8, 400],
    receipt_identity: ['id', 'mapped_user_id+client_run_id']
  };
  const input = {
    schema: CONTRACT.inputSchema,
    direction: 'forward',
    packet_id: 'MAZER-MASTER-CUTOVER-FENCE-R001-FIXTURE',
    bindings: {
      legacy: { project_ref: CONTRACT.legacy.projectRef, schema: CONTRACT.legacy.schema },
      master: { project_ref: CONTRACT.master.projectRef, schema: CONTRACT.master.schema }
    },
    identity_map: identityMap,
    expected_identity_map_digest: sha256(identityMap),
    app_contract: appContract,
    expected_app_contract_digest: sha256(appContract),
    fence: {
      legacy: fenceSide({ schema: CONTRACT.legacy.schema, signupDisabled: true }),
      master: fenceSide({ schema: CONTRACT.master.schema, hookEnabled: false })
    },
    source_snapshot: source,
    target_snapshot: target,
    expected_source_high_water_digest: snapshotDigest(source),
    zero_delta_reads: [
      { ...structuredClone(source), observed_at: iso(12) },
      { ...structuredClone(source), observed_at: iso(13) }
    ]
  };
  return input;
}

function expectHold(input, category) {
  assert.throws(() => classifyCutover(input), (error) => error instanceof CutoverHold && error.code === category);
}

const forward = baseForward();
const classified = classifyCutover(forward);
assert.equal(classified.receipt.result, 'PASS_FORWARD_DELTA');
assert.deepEqual(classified.receipt.changed_rows, { profiles: 2, player: 2, ai: 2, receipts: 1 });
assert.deepEqual(classified.receipt.desired_counts, { profiles: 2, player: 2, ai: 2, receipts: 3 });
assert.equal(classified.receipt.receipt_conservation.final, 3);
assert.equal(classified.receipt.zero_delta_reads, 2);
assert.equal(classified.receipt.auth_high_water_scope, 'LEGACY_DEDICATED_EXACT');
assert.equal(classified.receipt.fence_plan_validated, true);
assert.equal(classified.receipt.fence_complete, false);
assert.equal(classified.receipt.raw_identifiers_emitted, false);
assert.equal(classified.receipt.pii_emitted, false);
assert.match(classified.privatePlan.transactional_sql, /pg_advisory_xact_lock/);
assert.match(classified.privatePlan.transactional_sql, /TARGET_PREIMAGE_DRIFT/);
assert.match(classified.privatePlan.transactional_sql, /on conflict/);
assert.match(classified.privatePlan.transactional_sql, /is distinct from/);
assert.match(classified.privatePlan.transactional_sql, /left join atlas_expected_receipts/);
assert.match(classified.privatePlan.transactional_sql, /do update set[\s\S]+where exists \(select 1 from atlas_expected_receipts guard/);
assert.match(classified.privatePlan.fence_sql, /PARTIAL_WRITER_REVOKE/);
assert.match(classified.privatePlan.fence_sql, /PASS_WRITER_REVOKE_COMMITTED/);
assert.match(classified.privatePlan.fence_sql, /from authenticated, anon, public/);
assert.match(classified.privatePlan.fence_sql, /a\.grantee = 0/);
assert.ok(classified.privatePlan.fence_sql.indexOf('FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT') < classified.privatePlan.fence_sql.indexOf('revoke insert, update, delete'));
assert.ok(classified.privatePlan.fence_sql.indexOf('revoke insert, update, delete') < classified.privatePlan.fence_sql.indexOf('commit;'));
assert.ok(classified.privatePlan.fence_sql.indexOf('commit;') < classified.privatePlan.fence_sql.indexOf('PASS_WRITER_REVOKE_COMMITTED'));
assert.doesNotMatch(classified.privatePlan.fence_sql, /lock table/);
assert.match(classified.privatePlan.writer_capture_sql, /pg_catalog\.pg_stat_activity/);
assert.match(classified.privatePlan.writer_capture_sql, /a\.pid, a\.backend_start, a\.xact_start, a\.query_start/);
assert.match(classified.privatePlan.writer_capture_sql, /PASS_WRITER_SET_CAPTURE/);
assert.match(classified.privatePlan.writer_capture_sql, /WRITER_CAPTURE_ACL_OR_CATALOG_DRIFT/);
assert.match(renderAclObservationSql(CONTRACT.legacy.schema), /pg_catalog\.aclexplode/);
assert.match(classified.privatePlan.source_observation_sql, /LEGACY_DEDICATED_AUTH_SET_EXACT/);
assert.match(classified.privatePlan.source_observation_sql, /atlas_observed_auth except select \* from atlas_expected_auth/);
assert.match(classified.privatePlan.source_observation_sql, /atlas_expected_auth except select \* from atlas_observed_auth/);
assert.doesNotMatch(classified.privatePlan.source_observation_sql, /MASTER_MAZER_NAMESPACE_OR_PROFILE_OWNERSHIP/);

const staleProfilePayload = baseForward();
staleProfilePayload.source_snapshot.profiles[0].row.settings.trailFade = false;
expectHold(staleProfilePayload, 'PROFILE_PAYLOAD_DIGEST_MISMATCH');

const stalePlayerPayload = baseForward();
stalePlayerPayload.source_snapshot.player[0].row.state.tracks.player.targetComplexity = 21;
expectHold(stalePlayerPayload, 'PLAYER_PAYLOAD_DIGEST_MISMATCH');

const staleAiPayload = baseForward();
staleAiPayload.source_snapshot.ai[0].row.summary.targetComplexity = 17;
expectHold(staleAiPayload, 'AI_PAYLOAD_DIGEST_MISMATCH');

const staleReceiptPayload = baseForward();
staleReceiptPayload.source_snapshot.receipts[0].row.receipt.fixturePayload = 'tampered';
expectHold(staleReceiptPayload, 'RECEIPT_PAYLOAD_DIGEST_MISMATCH');

const ownerSpecificReceiptDigest = baseForward();
ownerSpecificReceiptDigest.source_snapshot.receipts[0].payload_digest = sha256(ownerSpecificReceiptDigest.source_snapshot.receipts[0].row);
expectHold(ownerSpecificReceiptDigest, 'RECEIPT_PAYLOAD_DIGEST_MISMATCH');

const staleAclDigest = baseForward();
staleAclDigest.fence.legacy.acl_preimage_digest = digest('stale-acl-preimage');
expectHold(staleAclDigest, 'ACL_PREIMAGE_DIGEST_DRIFT');

const staleCatalogDigest = baseForward();
staleCatalogDigest.fence.legacy.catalog_digest = digest('stale-catalog-preimage');
expectHold(staleCatalogDigest, 'FENCE_CATALOG_DIGEST_DRIFT');

const observedPacket = baseForward();
const observedPacketAcl = { ...structuredClone(observedPacket.fence.legacy.acl_preimage), observed_at: iso(14) };
const matchingAcl = classifyAclObservation(observedPacket, observedPacketAcl, 'primary');
assert.equal(matchingAcl.matched, true);
assert.equal(matchingAcl.receipt.result, 'PASS_ACL_PREIMAGE_MATCH');
assert.equal(matchingAcl.receipt.actual_acl_preimage_digest, observedPacket.fence.legacy.acl_preimage_digest);
assert.equal(matchingAcl.receipt.actual_catalog_digest, observedPacket.fence.legacy.catalog_digest);
assert.match(matchingAcl.fenceSql, /FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT/);
assert.ok(matchingAcl.fenceSql.indexOf('FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT') < matchingAcl.fenceSql.indexOf('revoke insert, update, delete'));
assert.match(matchingAcl.receipt.acl_observation_binding_digest, /^[a-f0-9]{64}$/);
assert.equal(matchingAcl.receipt.acl_observation_binding_digest, classifyAclObservation(observedPacket, observedPacketAcl, 'primary').receipt.acl_observation_binding_digest);

const customAcl = structuredClone(observedPacketAcl);
customAcl.table_acl.find(({ name }) => name === 'mazer_profiles').grants.push({
  grantee: 'anon',
  privilege: 'DELETE',
  is_grantable: true
});
const customAclAgainstPacket = classifyAclObservation(observedPacket, customAcl, 'primary');
assert.equal(customAclAgainstPacket.matched, false);
assert.equal(customAclAgainstPacket.receipt.result, 'HOLD_ACL_PREIMAGE_DRIFT');
assert.match(customAclAgainstPacket.fenceSql, /FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT/);
assert.match(customAclAgainstPacket.restoreSql, /grant DELETE on table "public"\."mazer_profiles" to "anon" with grant option;/);
assert.doesNotMatch(customAclAgainstPacket.restoreSql, /grant INSERT, UPDATE on table "public"\."mazer_profiles" to "anon"/);
const restoredCustomAcl = classifyAclObservation(observedPacket, customAcl, 'primary', customAcl);
assert.equal(restoredCustomAcl.matched, true);
assert.equal(restoredCustomAcl.receipt.actual_acl_preimage_digest, restoredCustomAcl.receipt.expected_acl_preimage_digest);
assert.equal(restoredCustomAcl.receipt.actual_catalog_digest, restoredCustomAcl.receipt.expected_catalog_digest);
const customAclPreimage = structuredClone(customAcl);
delete customAclPreimage.observed_at;
assert.equal(renderRestoreSql(CONTRACT.legacy.schema, customAclPreimage).includes('with grant option'), true);

const customCatalog = structuredClone(observedPacketAcl);
customCatalog.catalog.tables.find(({ name }) => name === 'mazer_profiles').rls_enabled = false;
const customCatalogAgainstPacket = classifyAclObservation(observedPacket, customCatalog, 'primary');
assert.equal(customCatalogAgainstPacket.matched, false);
assert.notEqual(customCatalogAgainstPacket.receipt.actual_catalog_digest, customCatalogAgainstPacket.receipt.expected_catalog_digest);

const alreadyRestoredAcl = classifyAclRecoveryObservation(observedPacket, observedPacketAcl, observedPacketAcl, 'primary');
assert.equal(alreadyRestoredAcl.recoverable, true);
assert.equal(alreadyRestoredAcl.restoreRequired, false);
assert.equal(alreadyRestoredAcl.receipt.result, 'PASS_ACL_PREIMAGE_ALREADY_PRESENT');
const fencedAclObservation = structuredClone(observedPacketAcl);
fencedAclObservation.observed_at = iso(15);
for (const table of fencedAclObservation.table_acl) table.grants = [];
for (const rpc of fencedAclObservation.rpc_acl) rpc.grants = [];
const committedFenceRecovery = classifyAclRecoveryObservation(observedPacket, observedPacketAcl, fencedAclObservation, 'primary');
assert.equal(committedFenceRecovery.recoverable, true);
assert.equal(committedFenceRecovery.restoreRequired, true);
assert.equal(committedFenceRecovery.receipt.result, 'PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED');
assert.equal(committedFenceRecovery.restoreSql, matchingAcl.restoreSql);
const ambiguousAclRecovery = classifyAclRecoveryObservation(observedPacket, observedPacketAcl, customAcl, 'primary');
assert.equal(ambiguousAclRecovery.recoverable, false);
assert.equal(ambiguousAclRecovery.receipt.result, 'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS');
assert.throws(
  () => classifyAclRecoveryObservation(observedPacket, customAcl, fencedAclObservation, 'primary'),
  (error) => error instanceof CutoverHold && error.code === 'JOURNALED_ACL_PACKET_DRIFT'
);

const fencedAcl = structuredClone(fencedAclObservation);
delete fencedAcl.observed_at;
const writerCapture = {
  result: 'PASS_WRITER_SET_CAPTURE',
  schema: CONTRACT.legacy.schema,
  captured_at: iso(16),
  fenced_acl: fencedAcl,
  writers: [
    { pid: 4102, backend_start: iso(1), xact_start: iso(2), query_start: iso(3) },
    { pid: 4101, backend_start: iso(1), xact_start: iso(2), query_start: iso(4) }
  ]
};
const boundWriterCapture = classifyWriterCapture(observedPacket, writerCapture, 'primary');
assert.equal(boundWriterCapture.receipt.result, 'PASS_WRITER_SET_CAPTURE_BOUND');
assert.equal(boundWriterCapture.receipt.writer_count, 2);
assert.match(boundWriterCapture.receipt.writer_set_digest, /^[a-f0-9]{64}$/);
assert.match(boundWriterCapture.receipt.writer_capture_binding_digest, /^[a-f0-9]{64}$/);
assert.match(boundWriterCapture.drainSql, /CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED/);
assert.match(boundWriterCapture.drainSql, /WAIT_CAPTURED_WRITERS/);
assert.match(boundWriterCapture.drainSql, /a\.pid = w\.pid[\s\S]+a\.backend_start = w\.backend_start/);
assert.match(boundWriterCapture.lockBarrierSql, /PASS_WRITER_LOCK_BARRIER/);
assert.match(boundWriterCapture.lockBarrierSql, /CAPTURED_WRITER_REAPPEARED/);
assert.match(boundWriterCapture.lockBarrierSql, /LOCK_BARRIER_POST_ACL_OR_CATALOG_DRIFT/);
for (const table of [...CONTRACT.tables].sort()) assert.match(boundWriterCapture.lockBarrierSql, new RegExp(`lock table "public"\\."${table}" in share row exclusive mode`));
assert.ok(boundWriterCapture.lockBarrierSql.indexOf('CAPTURED_WRITER_REAPPEARED') < boundWriterCapture.lockBarrierSql.indexOf('lock table'));
assert.ok(boundWriterCapture.lockBarrierSql.indexOf('lock table') < boundWriterCapture.lockBarrierSql.indexOf('LOCK_BARRIER_POST_ACL_OR_CATALOG_DRIFT'));

const emptyWriterCapture = classifyWriterCapture(observedPacket, { ...writerCapture, writers: [], captured_at: iso(17) }, 'primary');
assert.equal(emptyWriterCapture.receipt.writer_count, 0);
assert.match(emptyWriterCapture.drainSql, /case when 0 > 0/);
assert.doesNotMatch(emptyWriterCapture.drainSql, /pg_stat_activity a on/);

assert.throws(
  () => classifyWriterCapture(observedPacket, { ...writerCapture, writers: [{ ...writerCapture.writers[0], query: 'select secret' }] }, 'primary'),
  (error) => error instanceof CutoverHold && error.code === 'WRITER_IDENTITY_DISCLOSURE'
);
assert.throws(
  () => classifyWriterCapture(observedPacket, { ...writerCapture, writers: [writerCapture.writers[0], writerCapture.writers[0]] }, 'primary'),
  (error) => error instanceof CutoverHold && error.code === 'WRITER_CAPTURE_DUPLICATE'
);
assert.throws(
  () => classifyWriterCapture(observedPacket, { ...writerCapture, fenced_acl: { ...fencedAcl, catalog: customCatalog.catalog } }, 'primary'),
  (error) => error instanceof CutoverHold && error.code === 'WRITER_CAPTURE_ACL_OR_CATALOG_DRIFT'
);
assert.throws(
  () => renderWriterDrainSql(CONTRACT.legacy.schema, [{ ...writerCapture.writers[0], pid: 0 }], boundWriterCapture.receipt.writer_set_digest),
  (error) => error instanceof CutoverHold && error.code === 'WRITER_IDENTITY_PID'
);
assert.match(renderWriterCaptureSql(CONTRACT.master.schema, aclPreimage(CONTRACT.master.schema)), /mazer_complete_level\(/);
assert.match(renderWriterCaptureSql(CONTRACT.master.schema, aclPreimage(CONTRACT.master.schema)), /insertinto"mazer"\."mazer_profiles"/);

// REVOKE must commit before the post-commit identity capture. The exact captured
// transactions drain before an ordered table barrier, and only then may the two
// high-water reads accept the source.
const concurrentWriterSchedule = [
  'old-acl-rpc-admitted',
  'revoke-commits',
  'active-writer-identities-captured',
  'captured-writers-drained',
  'ordered-table-lock-barrier',
  'fenced-acl-catalog-reproved',
  'source-read-1',
  'source-read-2'
];
assert.ok(concurrentWriterSchedule.indexOf('revoke-commits') < concurrentWriterSchedule.indexOf('active-writer-identities-captured'));
assert.ok(concurrentWriterSchedule.indexOf('captured-writers-drained') < concurrentWriterSchedule.indexOf('ordered-table-lock-barrier'));
assert.doesNotMatch(renderFenceSql(CONTRACT.master.schema, aclPreimage(CONTRACT.master.schema)), /lock table/);
assert.match(renderLockBarrierSql(CONTRACT.master.schema, aclPreimage(CONTRACT.master.schema), writerCapture.writers, boundWriterCapture.receipt.writer_set_digest), /lock table[\s\S]+share row exclusive mode/);

const staleMap = baseForward();
staleMap.expected_identity_map_digest = digest('stale-map');
expectHold(staleMap, 'IDENTITY_MAP_DIGEST_DRIFT');

const staleApp = baseForward();
staleApp.expected_app_contract_digest = digest('stale-app');
expectHold(staleApp, 'APP_CONTRACT_DIGEST_DRIFT');

const ambiguous = baseForward();
ambiguous.identity_map[0].ambiguous = true;
ambiguous.expected_identity_map_digest = sha256(ambiguous.identity_map);
expectHold(ambiguous, 'AMBIGUOUS_IDENTITY');

const missingEdge = baseForward();
missingEdge.identity_map.pop();
missingEdge.expected_identity_map_digest = sha256(missingEdge.identity_map);
expectHold(missingEdge, 'AMBIGUOUS_IDENTITY');

const receiptConflict = baseForward();
receiptConflict.target_snapshot.receipts[0] = receipt(ids.masterA, ids.receipt1, ids.run1, 'divergent');
expectHold(receiptConflict, 'RECEIPT_ID_CONFLICT');

const clientRunConflict = baseForward();
clientRunConflict.target_snapshot.receipts[0] = receipt(ids.masterA, ids.receipt4, ids.run1, 'divergent-run');
expectHold(clientRunConflict, 'RECEIPT_CLIENT_RUN_CONFLICT');

const playerComponentRegression = baseForward();
playerComponentRegression.target_snapshot.player[0] = player(ids.masterA, 5, 4, 3, 16, 'D');
expectHold(playerComponentRegression, 'PLAYER_INCOMPATIBLE_HISTORY');

const aiComponentRegression = baseForward();
aiComponentRegression.target_snapshot.ai[0] = ai(ids.masterA, 4, 3, 12, 'D');
expectHold(aiComponentRegression, 'AI_INCOMPATIBLE_HISTORY');

const sqlDelimiterPayload = baseForward();
const delimiterMarker = '$atlas_desired_profiles$; rollback;';
sqlDelimiterPayload.source_snapshot.profiles[0].row.settings.marker = delimiterMarker;
sqlDelimiterPayload.source_snapshot.profiles[0].payload_digest = sha256(sqlDelimiterPayload.source_snapshot.profiles[0].row);
sqlDelimiterPayload.expected_source_high_water_digest = snapshotDigest(sqlDelimiterPayload.source_snapshot);
sqlDelimiterPayload.zero_delta_reads = [
  { ...structuredClone(sqlDelimiterPayload.source_snapshot), observed_at: iso(12) },
  { ...structuredClone(sqlDelimiterPayload.source_snapshot), observed_at: iso(13) }
];
const encodedPayloadPlan = classifyCutover(sqlDelimiterPayload);
assert.doesNotMatch(encodedPayloadPlan.privatePlan.transactional_sql, /\$atlas_desired_profiles\$/);
assert.match(encodedPayloadPlan.privatePlan.transactional_sql, /pg_catalog\.decode\('[A-Za-z0-9+/=]+'/);

const partialFence = baseForward();
partialFence.fence.legacy.table_writers.mazer_profiles = 'WRITABLE';
expectHold(partialFence, 'PARTIAL_WRITER_FENCE');

const lateWrite = baseForward();
lateWrite.zero_delta_reads[1].receipts.push(receipt(ids.legacyA, ids.receipt4, ids.run4, 'late'));
expectHold(lateWrite, 'POST_FENCE_LATE_WRITE');

const maxSafePlusOne = baseForward();
maxSafePlusOne.source_snapshot.player[0] = player(ids.legacyA, '9007199254740992', '9007199254740991', 2, 20);
maxSafePlusOne.target_snapshot.player[0] = player(ids.masterA, '9007199254740991', '9007199254740990', 1, 20);
maxSafePlusOne.source_snapshot.ai[0] = ai(ids.legacyA, '9223372036854775807', '9007199254740992', 20);
maxSafePlusOne.target_snapshot.ai[0] = ai(ids.masterA, '9007199254740992', '9007199254740991', 20);
maxSafePlusOne.expected_source_high_water_digest = snapshotDigest(maxSafePlusOne.source_snapshot);
maxSafePlusOne.zero_delta_reads = [
  { ...structuredClone(maxSafePlusOne.source_snapshot), observed_at: iso(12) },
  { ...structuredClone(maxSafePlusOne.source_snapshot), observed_at: iso(13) }
];
const bigintClassified = classifyCutover(maxSafePlusOne);
assert.equal(bigintClassified.privatePlan.desired.player[0].player_level, '9007199254740992');
assert.equal(bigintClassified.privatePlan.desired.player[0].player_completed_cycles, '9007199254740991');
assert.equal(bigintClassified.privatePlan.desired.ai[0].level, '9223372036854775807');
assert.equal(bigintClassified.privatePlan.desired.ai[0].completed_cycles, '9007199254740992');

const numericBigint = baseForward();
numericBigint.source_snapshot.player[0].level = 9007199254740992;
expectHold(numericBigint, 'PLAYER_LEVEL_SHAPE');

const numericNestedBigint = baseForward();
numericNestedBigint.source_snapshot.player[0].row.state.tracks.player.level = 9007199254740992;
numericNestedBigint.source_snapshot.player[0].payload_digest = sha256(numericNestedBigint.source_snapshot.player[0].row);
expectHold(numericNestedBigint, 'PLAYER_STATE_LEVEL_SHAPE');

const mismatchedNestedAiBigint = baseForward();
mismatchedNestedAiBigint.source_snapshot.ai[0].row.summary.completedCycles = '9007199254740992';
mismatchedNestedAiBigint.source_snapshot.ai[0].payload_digest = sha256(mismatchedNestedAiBigint.source_snapshot.ai[0].row);
expectHold(mismatchedNestedAiBigint, 'AI_RAW_STATE_PROJECTION_CONFLICT');

const overflowingBigint = baseForward();
overflowingBigint.source_snapshot.player[0] = player(ids.legacyA, '9223372036854775808', '3', 2, 20);
expectHold(overflowingBigint, 'PLAYER_RAW_LEVEL_SHAPE');

const leadingZeroBigint = baseForward();
leadingZeroBigint.source_snapshot.ai[0] = ai(ids.legacyA, '03', '2', 16);
expectHold(leadingZeroBigint, 'AI_RAW_LEVEL_SHAPE');

const scientificBigint = baseForward();
scientificBigint.source_snapshot.ai[0].completed_cycles = '1e3';
scientificBigint.source_snapshot.ai[0].row.completed_cycles = '1e3';
scientificBigint.source_snapshot.ai[0].row.state.completedCycles = '1e3';
scientificBigint.source_snapshot.ai[0].row.summary.completedCycles = '1e3';
scientificBigint.source_snapshot.ai[0].payload_digest = sha256(scientificBigint.source_snapshot.ai[0].row);
expectHold(scientificBigint, 'AI_RAW_CYCLES_SHAPE');

const negativeBigint = baseForward();
negativeBigint.source_snapshot.player[0] = player(ids.legacyA, '4', '-1', 2, 20);
expectHold(negativeBigint, 'PLAYER_RAW_CYCLES_SHAPE');

const interruptedForward = baseForward();
interruptedForward.journal = { direction: 'forward', phase: 'LEGACY_WRITERS_FENCED', interrupted: true };
expectHold(interruptedForward, 'INTERRUPTED_FORWARD_PREIMAGE_RESTORE_REQUIRED');

const interruptedReverse = baseForward();
interruptedReverse.direction = 'reverse';
interruptedReverse.baseline_source_snapshot = structuredClone(interruptedReverse.source_snapshot);
interruptedReverse.journal = { direction: 'reverse', phase: 'REVERSE_DELTA_APPLIED', interrupted: true };
expectHold(interruptedReverse, 'INTERRUPTED_REVERSE_VERIFY_OR_ROLLBACK_REQUIRED');

assert.deepEqual(classifyRecoveryState(null), { result: 'START', effect: 'NONE' });
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITERS_FENCED' }),
  { result: 'RESTORE_JOURNALED_ACL_AND_AUTH_PREIMAGE', effect: 'DRAIN_AND_LOCK_BARRIER_PROVEN' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITERS_PREOBSERVING' }),
  { result: 'RESTORE_LEGACY_SIGNUP_PREIMAGE', effect: 'AUTH_CONFIG_ONLY' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITERS_PREOBSERVED' }),
  { result: 'RESTORE_LEGACY_SIGNUP_PREIMAGE', effect: 'AUTH_CONFIG_ONLY' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITERS_FENCING' }),
  { result: 'OBSERVE_REVOKE_THEN_DRAIN_OR_RESTORE', effect: 'REVOKE_COMMIT_UNKNOWN' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITER_REVOKE_COMMITTED' }),
  { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITER_SET_CAPTURED' }),
  { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_WRITERS_DRAINING' }),
  { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'LEGACY_LOCK_BARRIER_ACQUIRING' }),
  { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }
);
for (const [phase, expected] of [
  ['LEGACY_WRITERS_FENCING', { result: 'OBSERVE_REVOKE_THEN_DRAIN_OR_RESTORE', effect: 'REVOKE_COMMIT_UNKNOWN' }],
  ['LEGACY_WRITER_SET_CAPTURING', { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }],
  ['LEGACY_WRITERS_DRAINING', { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }],
  ['LEGACY_LOCK_BARRIER_ACQUIRING', { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }]
]) {
  assert.deepEqual(classifyRecoveryState({ direction: 'forward', phase, fault: 'CHILD_COMMIT_OR_OUTPUT_PERSISTENCE_LOST' }), expected);
}
assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'MASTER_HOOK_DISABLED' }),
  { result: 'RESTORE_MASTER_PREIMAGE', effect: 'FENCE_ONLY' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'REVERSE_DELTA_APPLIED' }),
  { result: 'RESUME_REVERSE_VERIFICATION', effect: 'DELTA_MAY_BE_COMMITTED' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'FORWARD_DELTA_APPLYING' }),
  { result: 'RESUME_FORWARD_VERIFICATION', effect: 'DELTA_MAY_BE_COMMITTED' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'ZERO_DELTA_READ_2' }),
  { result: 'RESUME_REVERSE_VERIFICATION', effect: 'DELTA_MAY_BE_COMMITTED' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'LEGACY_SIGNUP_RESTORING' }),
  { result: 'REFENCE_LEGACY_WRITERS', effect: 'DUAL_WRITER_RISK' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'forward', phase: 'COMPLETE' }),
  { result: 'EXACT_REPLAY_NOOP', effect: 'TERMINAL' }
);

function baseReverse() {
  const identityMap = [
    { legacy_user_id: ids.legacyA, master_user_id: ids.masterA, disposition: 'BOUND' }
  ];
  const baseline = snapshot({
    observedAt: iso(20),
    users: [auth(ids.masterA, 'a')],
    profiles: [profile(ids.masterA, 2, 'fixture-a')],
    playerRows: [player(ids.masterA, 2, 1, 2, 12)],
    aiRows: [ai(ids.masterA, 2, 1, 12)],
    receipts: [receipt(ids.masterA, ids.receipt1, ids.run1, 'historical')]
  });
  const source = snapshot({
    observedAt: iso(22),
    users: [auth(ids.masterA, 'a')],
    profiles: [profile(ids.masterA, 2, 'fixture-a')],
    playerRows: [player(ids.masterA, 3, 2, 3, 16)],
    aiRows: [ai(ids.masterA, 3, 2, 16)],
    receipts: [
      receipt(ids.masterA, ids.receipt1, ids.run1, 'historical'),
      receipt(ids.masterA, ids.receipt4, ids.run4, 'target-era')
    ]
  });
  const target = snapshot({
    observedAt: iso(19),
    users: [auth(ids.legacyA, 'a')],
    profiles: [profile(ids.legacyA, 2, 'fixture-a')],
    playerRows: [player(ids.legacyA, 2, 1, 2, 12)],
    aiRows: [ai(ids.legacyA, 2, 1, 12)],
    receipts: [receipt(ids.legacyA, ids.receipt1, ids.run1, 'historical')]
  });
  const appContract = { inverse_map_required: true, target_era_receipts_only: true, difficulty_bounds: [8, 400] };
  return {
    schema: CONTRACT.inputSchema,
    direction: 'reverse',
    packet_id: 'MAZER-MASTER-CUTOVER-REVERSE-R001-FIXTURE',
    bindings: {
      legacy: { project_ref: CONTRACT.legacy.projectRef, schema: CONTRACT.legacy.schema },
      master: { project_ref: CONTRACT.master.projectRef, schema: CONTRACT.master.schema }
    },
    identity_map: identityMap,
    expected_identity_map_digest: sha256(identityMap),
    app_contract: appContract,
    expected_app_contract_digest: sha256(appContract),
    fence: {
      legacy: fenceSide({ schema: CONTRACT.legacy.schema, signupDisabled: false, fencedAt: iso(21) }),
      master: fenceSide({ schema: CONTRACT.master.schema, hookEnabled: false, fencedAt: iso(21) })
    },
    baseline_source_snapshot: baseline,
    source_snapshot: source,
    target_snapshot: target,
    expected_source_high_water_digest: snapshotDigest(source),
    zero_delta_reads: [
      { ...structuredClone(source), observed_at: iso(23) },
      { ...structuredClone(source), observed_at: iso(24) }
    ]
  };
}

const reverse = classifyCutover(baseReverse());
assert.equal(reverse.receipt.result, 'PASS_REVERSE_DELTA');
assert.equal(reverse.receipt.hook_disabled_first, true);
assert.equal(reverse.receipt.auth_high_water_scope, 'MASTER_MAZER_NAMESPACE_OR_PROFILE');
assert.deepEqual(reverse.receipt.changed_rows, { profiles: 0, player: 1, ai: 1, receipts: 1 });
assert.equal(reverse.receipt.desired_counts.receipts, 2);
assert.match(reverse.privatePlan.source_observation_sql, /MASTER_MAZER_NAMESPACE_OR_PROFILE_OWNERSHIP/);
assert.match(reverse.privatePlan.source_observation_sql, /raw_user_meta_data ->> 'app_namespace'/);
assert.match(reverse.privatePlan.source_observation_sql, /ownership_profile\.user_id = u\.id/);
assert.match(reverse.privatePlan.source_observation_sql, /atlas_observed_auth except select \* from atlas_expected_auth/);

// The generated shared-project scope includes an auth-only explicit Mazer
// marker and a profile owner, but excludes an unrelated application identity.
const scopedMasterAuth = [
  { id: ids.masterA, namespace: 'website', profileOwner: false },
  { id: ids.masterB, namespace: 'mazer', profileOwner: false },
  { id: ids.masterC, namespace: 'fitness', profileOwner: true }
].filter((entry) => entry.namespace === 'mazer' || entry.profileOwner).map((entry) => entry.id);
assert.deepEqual(scopedMasterAuth, [ids.masterB, ids.masterC]);
assert.equal(scopedMasterAuth.includes(ids.masterA), false);

assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'MASTER_WRITERS_PREOBSERVED' }),
  { result: 'RESTORE_MASTER_HOOK_PREIMAGE', effect: 'AUTH_CONFIG_ONLY' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'MASTER_WRITERS_FENCING' }),
  { result: 'OBSERVE_REVOKE_THEN_DRAIN_OR_RESTORE', effect: 'REVOKE_COMMIT_UNKNOWN' }
);
assert.deepEqual(
  classifyRecoveryState({ direction: 'reverse', phase: 'MASTER_WRITERS_DRAINED' }),
  { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' }
);

const targetEraUnknown = baseReverse();
targetEraUnknown.source_snapshot.auth.push(auth(ids.masterC, 'c'));
targetEraUnknown.source_snapshot.profiles.push(profile(ids.masterC, 0, null));
targetEraUnknown.zero_delta_reads = [
  { ...structuredClone(targetEraUnknown.source_snapshot), observed_at: iso(23) },
  { ...structuredClone(targetEraUnknown.source_snapshot), observed_at: iso(24) }
];
targetEraUnknown.expected_source_high_water_digest = snapshotDigest(targetEraUnknown.source_snapshot);
expectHold(targetEraUnknown, 'AMBIGUOUS_IDENTITY');

const historicalReceiptMutation = baseReverse();
historicalReceiptMutation.source_snapshot.receipts[0] = receipt(ids.masterA, ids.receipt1, ids.run1, 'mutated-history');
historicalReceiptMutation.zero_delta_reads = [
  { ...structuredClone(historicalReceiptMutation.source_snapshot), observed_at: iso(23) },
  { ...structuredClone(historicalReceiptMutation.source_snapshot), observed_at: iso(24) }
];
historicalReceiptMutation.expected_source_high_water_digest = snapshotDigest(historicalReceiptMutation.source_snapshot);
expectHold(historicalReceiptMutation, 'RECEIPT_HISTORY_CONFLICT');

const noOp = baseForward();
const noOpFirst = classifyCutover(noOp);
const desired = noOpFirst.privatePlan.desired;
const targetUser = ids.masterA;
const exactSource = snapshot({
  observedAt: iso(11),
  users: [auth(ids.legacyA, 'a')],
  profiles: [profile(ids.legacyA, 1, 'fixture-a')],
  playerRows: [player(ids.legacyA, 2, 1, 1, 12)],
  aiRows: [ai(ids.legacyA, 2, 1, 12)],
  receipts: [receipt(ids.legacyA, ids.receipt1, ids.run1, 'same')]
});
const exactTarget = snapshot({
  observedAt: iso(9),
  users: [auth(targetUser, 'a')],
  profiles: [profile(targetUser, 1, 'fixture-a')],
  playerRows: [player(targetUser, 2, 1, 1, 12)],
  aiRows: [ai(targetUser, 2, 1, 12)],
  receipts: [receipt(targetUser, ids.receipt1, ids.run1, 'same')]
});
const noOpMap = [{ legacy_user_id: ids.legacyA, master_user_id: targetUser, disposition: 'BOUND' }];
const noOpContract = { exact_replay: true };
const noOpInput = {
  ...baseForward(),
  identity_map: noOpMap,
  expected_identity_map_digest: sha256(noOpMap),
  app_contract: noOpContract,
  expected_app_contract_digest: sha256(noOpContract),
  source_snapshot: exactSource,
  target_snapshot: exactTarget,
  expected_source_high_water_digest: snapshotDigest(exactSource),
  zero_delta_reads: [
    { ...structuredClone(exactSource), observed_at: iso(12) },
    { ...structuredClone(exactSource), observed_at: iso(13) }
  ]
};
assert.equal(classifyCutover(noOpInput).receipt.result, 'PASS_EXACT_REPLAY_NOOP');
assert.ok(desired.receipts.length > 0);

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-mazer-fence-test-'));
try {
  const inputPath = path.join(tmp, 'input.json');
  const planPath = path.join(tmp, 'private-plan.json');
  const sqlPath = path.join(tmp, 'private-plan.sql');
  const sourceObservationSqlPath = path.join(tmp, 'private-source-observation.sql');
  const fenceSqlPath = path.join(tmp, 'private-fence.sql');
  const writerCaptureSqlPath = path.join(tmp, 'private-writer-capture.sql');
  const aclObservationSqlPath = path.join(tmp, 'private-acl-observation.sql');
  const restoreSqlPath = path.join(tmp, 'private-restore.sql');
  const legacyFenceSqlPath = path.join(tmp, 'private-legacy-fence.sql');
  const legacyWriterCaptureSqlPath = path.join(tmp, 'private-legacy-writer-capture.sql');
  const legacyAclObservationSqlPath = path.join(tmp, 'private-legacy-acl-observation.sql');
  const legacyRestoreSqlPath = path.join(tmp, 'private-legacy-restore.sql');
  fs.writeFileSync(inputPath, JSON.stringify(baseForward()), { encoding: 'utf8', mode: 0o600 });
  const cli = spawnSync(process.execPath, [
    classifierPath,
    '--input', inputPath,
    '--private-plan', planPath,
    '--private-sql', sqlPath,
    '--private-source-observation-sql', sourceObservationSqlPath,
    '--private-fence-sql', fenceSqlPath,
    '--private-writer-capture-sql', writerCaptureSqlPath,
    '--private-acl-observation-sql', aclObservationSqlPath,
    '--private-restore-sql', restoreSqlPath,
    '--private-legacy-fence-sql', legacyFenceSqlPath,
    '--private-legacy-writer-capture-sql', legacyWriterCaptureSqlPath,
    '--private-legacy-acl-observation-sql', legacyAclObservationSqlPath,
    '--private-legacy-restore-sql', legacyRestoreSqlPath
  ], {
    encoding: 'utf8',
    timeout: 30000,
    windowsHide: true
  });
  assert.equal(cli.status, 0, cli.stderr);
  const output = JSON.parse(cli.stdout.trim());
  assert.equal(output.result, 'PASS_FORWARD_DELTA');
  assert.equal(output.raw_identifiers_emitted, false);
  assert.equal(output.secrets_emitted, false);
  assert.ok(fs.statSync(planPath).size > 0);
  assert.ok(fs.statSync(sqlPath).size > 0);
  assert.ok(fs.statSync(sourceObservationSqlPath).size > 0);
  assert.ok(fs.statSync(fenceSqlPath).size > 0);
  assert.ok(fs.statSync(writerCaptureSqlPath).size > 0);
  assert.ok(fs.statSync(aclObservationSqlPath).size > 0);
  assert.ok(fs.statSync(restoreSqlPath).size > 0);
  assert.ok(fs.statSync(legacyFenceSqlPath).size > 0);
  assert.ok(fs.statSync(legacyWriterCaptureSqlPath).size > 0);
  assert.ok(fs.statSync(legacyAclObservationSqlPath).size > 0);
  assert.ok(fs.statSync(legacyRestoreSqlPath).size > 0);
  const sourceObservationSql = fs.readFileSync(sourceObservationSqlPath, 'utf8');
  assert.match(sourceObservationSql, /begin transaction isolation level repeatable read;/);
  assert.match(sourceObservationSql, /create temporary table atlas_expected_auth/);
  assert.match(sourceObservationSql, /SOURCE_AUTH_HIGH_WATER_DRIFT/);
  assert.match(sourceObservationSql, /SOURCE_HIGH_WATER_DRIFT:mazer_cycle_receipts/);
  assert.match(sourceObservationSql, /PASS_SOURCE_HIGH_WATER/);
  assert.doesNotMatch(sourceObservationSql, /fixture-a|\$atlas_desired_profiles\$/);
  assert.doesNotMatch(cli.stdout, /fixture-a|@|password|service_role|authorization/i);
  for (const value of Object.values(ids)) assert.equal(cli.stdout.includes(value), false);

  const observedAclPath = path.join(tmp, 'observed-acl.json');
  const matchingExpectedAclPath = path.join(tmp, 'expected-observed-acl.json');
  const journaledPacketAclPath = path.join(tmp, 'journaled-packet-acl.json');
  const fencedAclPath = path.join(tmp, 'fenced-acl.json');
  const mismatchedRestorePath = path.join(tmp, 'mismatched-observed-restore.sql');
  const mismatchedFencePath = path.join(tmp, 'mismatched-observed-fence.sql');
  const matchingRestorePath = path.join(tmp, 'matching-observed-restore.sql');
  const matchingFencePath = path.join(tmp, 'matching-observed-fence.sql');
  fs.writeFileSync(observedAclPath, JSON.stringify(customAcl), { encoding: 'utf8', mode: 0o600 });
  fs.writeFileSync(matchingExpectedAclPath, JSON.stringify(customAcl), { encoding: 'utf8', mode: 0o600 });
  fs.writeFileSync(journaledPacketAclPath, JSON.stringify(observedPacketAcl), { encoding: 'utf8', mode: 0o600 });
  fs.writeFileSync(fencedAclPath, JSON.stringify(fencedAclObservation), { encoding: 'utf8', mode: 0o600 });
  const mismatchedAclCli = spawnSync(process.execPath, [
    classifierPath,
    '--input', inputPath,
    '--verify-acl-observation', observedAclPath,
    '--acl-side', 'primary',
    '--private-observed-fence-sql', mismatchedFencePath,
    '--private-observed-restore-sql', mismatchedRestorePath
  ], { encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(mismatchedAclCli.status, 2, mismatchedAclCli.stderr);
  assert.equal(JSON.parse(mismatchedAclCli.stdout.trim()).result, 'HOLD_ACL_PREIMAGE_DRIFT');
  assert.match(fs.readFileSync(mismatchedRestorePath, 'utf8'), /grant DELETE[\s\S]+to "anon" with grant option/);
  assert.match(fs.readFileSync(mismatchedFencePath, 'utf8'), /FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT/);
  assert.doesNotMatch(mismatchedAclCli.stdout, /fixture-a|@|password|service_role|authorization/i);

  const matchingAclCli = spawnSync(process.execPath, [
    classifierPath,
    '--input', inputPath,
    '--verify-acl-observation', observedAclPath,
    '--acl-side', 'primary',
    '--expected-acl-observation', matchingExpectedAclPath,
    '--private-observed-fence-sql', matchingFencePath,
    '--private-observed-restore-sql', matchingRestorePath
  ], { encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(matchingAclCli.status, 0, matchingAclCli.stderr);
  const matchingAclOutput = JSON.parse(matchingAclCli.stdout.trim());
  assert.equal(matchingAclOutput.result, 'PASS_ACL_PREIMAGE_MATCH');
  assert.equal(matchingAclOutput.actual_acl_preimage_digest, matchingAclOutput.expected_acl_preimage_digest);
  assert.equal(matchingAclOutput.actual_catalog_digest, matchingAclOutput.expected_catalog_digest);
  assert.match(matchingAclOutput.acl_observation_binding_digest, /^[a-f0-9]{64}$/);
  assert.equal(fs.readFileSync(matchingRestorePath, 'utf8'), fs.readFileSync(mismatchedRestorePath, 'utf8'));
  assert.equal(fs.readFileSync(matchingFencePath, 'utf8'), fs.readFileSync(mismatchedFencePath, 'utf8'));

  const writerCapturePath = path.join(tmp, 'writer-capture.json');
  const writerDrainSqlPath = path.join(tmp, 'writer-drain.sql');
  const lockBarrierSqlPath = path.join(tmp, 'lock-barrier.sql');
  fs.writeFileSync(writerCapturePath, JSON.stringify(writerCapture), { encoding: 'utf8', mode: 0o600 });
  const writerCaptureCli = spawnSync(process.execPath, [
    classifierPath,
    '--input', inputPath,
    '--verify-writer-capture', writerCapturePath,
    '--writer-side', 'primary',
    '--private-writer-drain-sql', writerDrainSqlPath,
    '--private-lock-barrier-sql', lockBarrierSqlPath
  ], { encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(writerCaptureCli.status, 0, writerCaptureCli.stderr);
  const writerCaptureOutput = JSON.parse(writerCaptureCli.stdout.trim());
  assert.equal(writerCaptureOutput.result, 'PASS_WRITER_SET_CAPTURE_BOUND');
  assert.equal(writerCaptureOutput.writer_count, 2);
  assert.match(writerCaptureOutput.writer_set_digest, /^[a-f0-9]{64}$/);
  assert.ok(fs.statSync(writerDrainSqlPath).size > 0);
  assert.ok(fs.statSync(lockBarrierSqlPath).size > 0);
  assert.match(fs.readFileSync(writerDrainSqlPath, 'utf8'), /CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED/);
  assert.match(fs.readFileSync(lockBarrierSqlPath, 'utf8'), /PASS_WRITER_LOCK_BARRIER/);
  assert.doesNotMatch(writerCaptureCli.stdout, /4101|4102|query_start|backend_start/);

  const recoveryCli = spawnSync(process.execPath, [
    classifierPath,
    '--input', inputPath,
    '--classify-acl-recovery', fencedAclPath,
    '--journaled-acl-observation', journaledPacketAclPath,
    '--acl-side', 'primary'
  ], { encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(recoveryCli.status, 0, recoveryCli.stderr);
  assert.equal(JSON.parse(recoveryCli.stdout.trim()).result, 'PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED');
  const ambiguousRecoveryCli = spawnSync(process.execPath, [
    classifierPath,
    '--input', inputPath,
    '--classify-acl-recovery', observedAclPath,
    '--journaled-acl-observation', journaledPacketAclPath,
    '--acl-side', 'primary'
  ], { encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(ambiguousRecoveryCli.status, 2, ambiguousRecoveryCli.stderr);
  assert.equal(JSON.parse(ambiguousRecoveryCli.stdout.trim()).result, 'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}

function toWslPath(value) {
  const absolute = path.resolve(value);
  const match = /^([A-Za-z]):\\(.*)$/.exec(absolute);
  if (!match) throw new Error('PG17_WINDOWS_PATH_REQUIRED');
  return `/mnt/${match[1].toLowerCase()}/${match[2].replaceAll('\\', '/')}`;
}

function waitForMarker(child, marker, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    let output = '';
    let error = '';
    const timer = setTimeout(() => reject(new Error(`PG17_MARKER_TIMEOUT:${marker}:${error}`)), timeoutMs);
    child.stdout.on('data', (chunk) => {
      output += chunk.toString('utf8');
      if (output.includes(marker)) {
        clearTimeout(timer);
        resolve(output);
      }
    });
    child.stderr.on('data', (chunk) => { error += chunk.toString('utf8'); });
    child.once('exit', (code) => {
      if (!output.includes(marker)) {
        clearTimeout(timer);
        reject(new Error(`PG17_PROCESS_EXITED:${marker}:${code}:${error}`));
      }
    });
  });
}

function waitForExit(child, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString('utf8'); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString('utf8'); });
    const timer = setTimeout(() => {
      try { child.kill(); } catch {}
      reject(new Error(`PG17_PROCESS_TIMEOUT:${stderr}`));
    }, timeoutMs);
    child.once('exit', (code) => {
      clearTimeout(timer);
      if (code !== 0) reject(new Error(`PG17_PROCESS_FAILED:${code}:${stderr}`));
      else resolve(stdout);
    });
  });
}

async function runDisposablePostgres17Concurrency() {
  if (process.env.ATLAS_RUN_PG17_CONCURRENCY !== '1') return 'SKIPPED_EXPLICIT_OPT_IN_REQUIRED';
  if (process.platform !== 'win32') throw new Error('PG17_WSL_WINDOWS_REQUIRED');
  const distro = process.env.ATLAS_PG17_WSL_DISTRO || 'Ubuntu';
  const pgRoot = process.env.ATLAS_PG17_ROOT || '/home/zjhre/.cache/atlas-pg17-root';
  if (!/^\/(?:tmp|home\/[a-z0-9_-]+\/\.cache)\/atlas-pg17-root(?:-[a-z0-9]+)?$/.test(pgRoot)) throw new Error('PG17_ROOT_SCOPE');
  const libPath = `${pgRoot}/usr/lib/x86_64-linux-gnu:${pgRoot}/usr/lib/postgresql/17/lib`;
  const binary = (name) => `${pgRoot}/usr/lib/postgresql/17/bin/${name}`;
  const wslArgs = (name, args) => ['-d', distro, '--', 'env', `LD_LIBRARY_PATH=${libPath}`, binary(name), ...args];
  const run = (name, args, options = {}) => spawnSync('wsl.exe', wslArgs(name, args), {
    encoding: 'utf8',
    timeout: options.timeout || 30000,
    windowsHide: true
  });
  const required = (name, args, options = {}) => {
    const result = run(name, args, options);
    assert.equal(result.status, 0, `${name}: ${result.stderr}`);
    return result.stdout;
  };
  const token = `${process.pid}-${crypto.randomBytes(4).toString('hex')}`;
  const clusterRoot = `/tmp/atlas-mazer-fence-pg17-${token}`;
  if (!/^\/tmp\/atlas-mazer-fence-pg17-[0-9]+-[a-f0-9]{8}$/.test(clusterRoot)) throw new Error('PG17_CLUSTER_SCOPE');
  const data = `${clusterRoot}/data`;
  const socket = `${clusterRoot}/socket`;
  const port = 60000 + (process.pid % 4000);
  const pgCommon = ['-X', '-qAt', '-h', socket, '-p', String(port), '-d', 'postgres', '-v', 'ON_ERROR_STOP=1'];
  const pgSql = (sql, options = {}) => run('psql', [...pgCommon, '-c', sql], options);
  const pgSqlRequired = (sql, options = {}) => {
    const result = pgSql(sql, options);
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim();
  };
  const pgFile = (file, options = {}) => run('psql', [...pgCommon, '--file', toWslPath(file)], options);
  const pgFileRequired = (file, options = {}) => {
    const result = pgFile(file, options);
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim();
  };
  const pgSpawn = () => spawn('wsl.exe', wslArgs('psql', pgCommon), { windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
  const shell = (args) => spawnSync('wsl.exe', ['-d', distro, '--', ...args], { encoding: 'utf8', timeout: 30000, windowsHide: true });
  let started = false;
  const pgTmp = fs.mkdtempSync(path.join(root, 'tmp', 'atlas-mazer-pg17-concurrency-'));
  let gate = null;
  let direct = null;
  let rpc = null;
  let drain = null;
  try {
    const version = required('postgres', ['--version']).trim();
    assert.match(version, /PostgreSQL\) 17\./);
    assert.equal(shell(['mkdir', '-p', clusterRoot, socket]).status, 0);
    required('initdb', ['-D', data, '--auth=trust', '--no-locale'], { timeout: 60000 });
    required('pg_ctl', ['-D', data, '-l', `${clusterRoot}/postgres.log`, '-o', `-F -k ${socket} -p ${port} -c listen_addresses=''`, '-w', 'start'], { timeout: 60000 });
    started = true;

    const setupSql = `
      create role authenticated nologin;
      create role anon nologin;
      create table public.rpc_gate (id integer primary key);
      insert into public.rpc_gate values (1);
      create table public.mazer_profiles (user_id uuid primary key);
      create table public.mazer_progression_states (id bigint primary key);
      create table public.mazer_ai_progression_states (id bigint primary key);
      create table public.mazer_cycle_receipts (id bigint primary key);
      create function public.mazer_initialize_progression(p1 uuid) returns void language plpgsql volatile security definer set search_path = pg_catalog, public as 'begin null; end';
      create function public.mazer_complete_level(p_level bigint,p2 uuid,p3 text,p4 integer,p5 integer,p6 uuid,p7 text,p8 integer,p9 text,p10 timestamp with time zone,p11 jsonb) returns void language plpgsql volatile security definer set search_path = pg_catalog, public as 'begin perform 1 from public.rpc_gate; insert into public.mazer_cycle_receipts(id) values (p_level); end';
      create function public.mazer_complete_ai_level(p1 uuid,p2 text,p3 integer,p4 integer,p5 uuid,p6 text,p7 integer,p8 text,p9 timestamp with time zone,p10 jsonb) returns void language plpgsql volatile security definer set search_path = pg_catalog, public as 'begin null; end';
      create function public.mazer_reset_progression(p1 bigint,p2 uuid) returns void language plpgsql volatile security definer set search_path = pg_catalog, public as 'begin null; end';
      revoke all on function public.mazer_initialize_progression(uuid) from public;
      revoke all on function public.mazer_complete_level(bigint,uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb) from public;
      revoke all on function public.mazer_complete_ai_level(uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb) from public;
      revoke all on function public.mazer_reset_progression(bigint,uuid) from public;
      grant insert, update on table public.mazer_profiles to authenticated;
      grant execute on function public.mazer_initialize_progression(uuid) to authenticated;
      grant execute on function public.mazer_complete_level(bigint,uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb) to authenticated;
      grant execute on function public.mazer_complete_ai_level(uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb) to authenticated;
      grant execute on function public.mazer_reset_progression(bigint,uuid) to authenticated;
    `;
    pgSqlRequired(setupSql);

    const observationPath = path.join(pgTmp, 'acl-observation.sql');
    fs.writeFileSync(observationPath, renderAclObservationSql(CONTRACT.legacy.schema), 'utf8');
    const liveAclObservation = JSON.parse(pgFileRequired(observationPath));
    const livePreimage = structuredClone(liveAclObservation);
    delete livePreimage.observed_at;
    const liveInput = baseForward();
    liveInput.fence.legacy.acl_preimage = livePreimage;
    liveInput.fence.legacy.acl_preimage_digest = sha256({ schema: livePreimage.schema, table_acl: livePreimage.table_acl, rpc_acl: livePreimage.rpc_acl });
    liveInput.fence.legacy.catalog_digest = sha256({ schema: livePreimage.schema, catalog: livePreimage.catalog });
    const livePlan = classifyCutover(liveInput).privatePlan;

    gate = pgSpawn();
    gate.stdin.write('begin; lock table public.rpc_gate in access exclusive mode; \\echo GATE_READY\n');
    await waitForMarker(gate, 'GATE_READY');

    rpc = pgSpawn();
    rpc.stdin.end(`set role authenticated; select public.mazer_complete_level(1,'${ids.legacyA}','x',1,1,'${ids.run1}','x',1,'x',now(),'{}'::jsonb);\n\\q\n`);
    const rpcSeen = () => Number(pgSqlRequired("select count(*) from pg_catalog.pg_stat_activity where pid <> pg_backend_pid() and state = 'active' and query like '%mazer_complete_level(1,%';")) === 1;
    for (let attempt = 0; attempt < 100 && !rpcSeen(); attempt += 1) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 25);
    assert.equal(rpcSeen(), true, 'old-ACL SECURITY DEFINER RPC was not active behind the relation lock');

    direct = pgSpawn();
    direct.stdin.write(`set role authenticated; begin; insert into public.mazer_profiles(user_id) values ('${ids.legacyB}'); \\echo DIRECT_READY\n`);
    await waitForMarker(direct, 'DIRECT_READY');

    const revokePath = path.join(pgTmp, 'writer-revoke.sql');
    const capturePath = path.join(pgTmp, 'writer-capture.sql');
    fs.writeFileSync(revokePath, livePlan.fence_sql, 'utf8');
    fs.writeFileSync(capturePath, livePlan.writer_capture_sql, 'utf8');
    const revokeReceipt = JSON.parse(pgFileRequired(revokePath));
    assert.equal(revokeReceipt.result, 'PASS_WRITER_REVOKE_COMMITTED');
    const liveWriterCapture = JSON.parse(pgFileRequired(capturePath));
    assert.equal(liveWriterCapture.result, 'PASS_WRITER_SET_CAPTURE');
    assert.equal(liveWriterCapture.writers.length, 2);
    const liveWriterPlan = classifyWriterCapture(liveInput, liveWriterCapture, 'primary');
    const drainPath = path.join(pgTmp, 'writer-drain.sql');
    const barrierPath = path.join(pgTmp, 'lock-barrier.sql');
    fs.writeFileSync(drainPath, liveWriterPlan.drainSql, 'utf8');
    fs.writeFileSync(barrierPath, liveWriterPlan.lockBarrierSql, 'utf8');

    const waitingDrainReceipt = JSON.parse(pgFileRequired(drainPath));
    assert.equal(waitingDrainReceipt.result, 'WAIT_CAPTURED_WRITERS');
    assert.equal(waitingDrainReceipt.remaining_writer_count, 2);
    direct.stdin.end('commit;\n\\q\n');
    gate.stdin.end('commit;\n\\q\n');
    await Promise.all([waitForExit(direct), waitForExit(gate), waitForExit(rpc)]);
    direct = null;
    gate = null;
    rpc = null;
    const drainedReceipt = JSON.parse(pgFileRequired(drainPath));
    assert.equal(drainedReceipt.result, 'PASS_CAPTURED_WRITERS_DRAINED');
    assert.equal(drainedReceipt.remaining_writer_count, 0);

    const barrierReceipt = JSON.parse(pgFileRequired(barrierPath, { timeout: 160000 }));
    assert.equal(barrierReceipt.result, 'PASS_WRITER_LOCK_BARRIER');
    const beforeRejectedWrites = Number(pgSqlRequired('select (select count(*) from public.mazer_profiles) + (select count(*) from public.mazer_cycle_receipts);'));
    assert.equal(beforeRejectedWrites, 2);
    const rejectedDirect = pgSql(`set role authenticated; insert into public.mazer_profiles(user_id) values ('${ids.legacyC}');`);
    const rejectedRpc = pgSql(`set role authenticated; select public.mazer_complete_level(2,'${ids.legacyA}','x',1,1,'${ids.run2}','x',1,'x',now(),'{}'::jsonb);`);
    assert.notEqual(rejectedDirect.status, 0);
    assert.notEqual(rejectedRpc.status, 0);
    const afterRejectedWrites = Number(pgSqlRequired('select (select count(*) from public.mazer_profiles) + (select count(*) from public.mazer_cycle_receipts);'));
    assert.equal(afterRejectedWrites, beforeRejectedWrites);

    const restorePath = path.join(pgTmp, 'restore.sql');
    fs.writeFileSync(restorePath, livePlan.restore_sql, 'utf8');
    pgFileRequired(restorePath);
    const restoredObservation = JSON.parse(pgFileRequired(observationPath));
    assert.equal(classifyAclObservation(liveInput, restoredObservation, 'primary', liveAclObservation).matched, true);
    pgSqlRequired(`set role authenticated; insert into public.mazer_profiles(user_id) values ('${ids.legacyC}');`);
    pgSqlRequired(`set role authenticated; select public.mazer_complete_level(2,'${ids.legacyA}','x',1,1,'${ids.run2}','x',1,'x',now(),'{}'::jsonb);`);
    assert.equal(Number(pgSqlRequired('select (select count(*) from public.mazer_profiles) + (select count(*) from public.mazer_cycle_receipts);')), 4);
    return 'PASS_POSTGRESQL_17_REAL_CONCURRENCY';
  } finally {
    for (const child of [direct, gate, rpc, drain]) {
      if (child) { try { child.kill(); } catch {} }
    }
    if (started) run('pg_ctl', ['-D', data, '-m', 'immediate', '-w', 'stop'], { timeout: 60000 });
    const removed = shell(['rm', '-rf', clusterRoot]);
    assert.equal(removed.status, 0, removed.stderr);
    fs.rmSync(pgTmp, { recursive: true, force: true });
  }
}

const pg17Concurrency = await runDisposablePostgres17Concurrency();

console.log(JSON.stringify({
  result: 'PASS_MAZER_MASTER_CUTOVER_DATA_FENCE_R001',
  scenarios: 76,
  postgresql17_concurrency: pg17Concurrency,
  provider_calls: 0,
  provider_writes: 0,
  auth_writes: 0,
  live_data_writes: 0,
  secret_or_pii_output: 0
}));
