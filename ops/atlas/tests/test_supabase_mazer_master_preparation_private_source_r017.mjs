import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { CONTRACT as FENCE_CONTRACT, classifyCutover, sha256 } from '../classify_supabase_mazer_master_cutover_data_fence_r001.mjs';
import { validatePrivateSource, wrapMigrationTransaction } from '../materialize_supabase_mazer_master_preparation_r017.mjs';
import {
  PRODUCER_CONTRACT,
  SNAPSHOT_SQL,
  buildIdentityPlan,
  producePrivateSource,
  renderOperationalSql,
  verifyEvidence,
  writePrivateSource
} from '../produce_supabase_mazer_master_preparation_private_source_r017.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
function findEvidenceRoot(start) {
  let cursor = start;
  while (true) {
    if (fs.existsSync(path.join(cursor, PRODUCER_CONTRACT.evidence.topology.relativePath))) return cursor;
    const parent = path.dirname(cursor); if (parent === cursor) throw new Error('ATLAS_EVIDENCE_ROOT_NOT_FOUND'); cursor = parent;
  }
}
assert.doesNotThrow(() => verifyEvidence(findEvidenceRoot(root)));
function findMazerRepository(start) {
  let cursor = start;
  while (true) {
    const candidate = path.join(cursor, 'repos', 'mazer');
    if (fs.existsSync(path.join(candidate, '.git'))) return candidate;
    const parent = path.dirname(cursor); if (parent === cursor) throw new Error('MAZER_REPOSITORY_NOT_FOUND'); cursor = parent;
  }
}
const mazerRepository = findMazerRepository(root);
const uid = (value) => `00000000-0000-4000-8000-${String(value).padStart(12, '0')}`;
const now = Date.now();
const iso = (offset) => new Date(now + offset).toISOString();
const verifier = `$2b$12$${'A'.repeat(53)}`;
const sharedLegacy = Array.from({ length: 16 }, (_, index) => uid(index + 1));
const sharedMaster = sharedLegacy.map((id, index) => index < 2 ? id : uid(100 + index));
const legacyOnly = [uid(17), uid(18), uid(19)];
const unrelatedMaster = Array.from({ length: 98 }, (_, index) => uid(1000 + index));

function user(id, email, instance = uid(9000)) {
  return {
    id, instance_id: instance, aud: 'authenticated', role: 'authenticated', email, encrypted_password: verifier,
    email_confirmed_at: iso(-10000), invited_at: null, confirmation_token: '', confirmation_sent_at: null,
    recovery_token: '', recovery_sent_at: null, email_change_token_new: '', email_change: '', email_change_sent_at: null,
    last_sign_in_at: null, raw_app_meta_data: { provider: 'email', providers: ['email'] }, raw_user_meta_data: {},
    is_super_admin: false, created_at: iso(-20000), updated_at: iso(-10000), phone: null, phone_confirmed_at: null,
    phone_change: '', phone_change_token: '', phone_change_sent_at: null, confirmed_at: iso(-10000),
    email_change_token_current: '', email_change_confirm_status: 0, banned_until: null, reauthentication_token: '',
    reauthentication_sent_at: null, is_sso_user: false, deleted_at: null, is_anonymous: false
  };
}
function identity(id, email, index) { return { id: uid(20000 + index), user_id: id, provider_id: id, identity_data: { sub: id, email }, provider: 'email', created_at: iso(-20000), updated_at: iso(-10000), last_sign_in_at: iso(-10000), email: email.toLowerCase() }; }
function profile(id, index) { return { user_id: id, display_name: null, selected_control_mode: 'stick', settings: { trailFade: true }, created_at: iso(-9000), updated_at: iso(-8000), revision: index, username: index % 2 ? null : `u${index + 10}` }; }
function player(id, reset = false, target = false) {
  const level = reset ? (target ? 6 : 5) : 2; const cycles = reset ? (target ? 5 : 4) : 1; const complexity = reset ? (target ? 25 : 24) : 12;
  return { user_id: id, schema_version: 1, state: { tracks: { player: { level, completedCycles: cycles, targetComplexity: complexity } } }, last_completed_cycle_at: iso(-7000), created_at: iso(-9000), updated_at: iso(-7000), player_level: level, player_rank: 'E', player_target_complexity: complexity, player_completed_cycles: cycles, revision: 0, level_reached_at: iso(-7000) };
}
function ai(id, reset, target = false) {
  const level = reset ? (target ? 39 : 9) : 2; const cycles = reset ? (target ? 108 : 8) : 1; const complexity = reset ? (target ? 161 : 40) : 12; const rank = reset ? (target ? 'S' : 'D') : 'E';
  return { user_id: id, runner_key: 'menu-runner', schema_version: 1, state: { level, completedCycles: cycles, targetComplexity: complexity }, summary: { level, completedCycles: cycles, targetComplexity: complexity }, level, rank, target_complexity: complexity, completed_cycles: cycles, last_completed_cycle_at: iso(target ? -9000 : -1000), created_at: iso(-20000), updated_at: iso(target ? -9000 : -1000) };
}
function receipt(id, owner, run, payload) { return { id, user_id: owner, surface: 'play', maze_seed: 7, maze_size: 37, route_quality: 'multi-route', start_cell: {}, goal_cell: {}, path_length: 20, wrong_turns: 1, backtracks: 0, completion_time_ms: 2000, reset_used: false, control_mode: 'stick', average_frame_ms: 16.667, receipt: { fixture: payload }, completed_at: iso(-5000), created_at: iso(-5000), ruleset_id: 'legacy-v1', recipe_version: null, recipe_hash: null, client_run_id: run };
}
function catalog() {
  return {
    columns: [
      { table: 'mazer_profiles', column: 'user_id', ordinal: 1, data_type: 'uuid', udt_name: 'uuid', nullable: 'NO', default: null },
      { table: 'mazer_progression_states', column: 'user_id', ordinal: 1, data_type: 'uuid', udt_name: 'uuid', nullable: 'NO', default: null },
      { table: 'mazer_ai_progression_states', column: 'user_id', ordinal: 1, data_type: 'uuid', udt_name: 'uuid', nullable: 'NO', default: null },
      { table: 'mazer_cycle_receipts', column: 'id', ordinal: 1, data_type: 'uuid', udt_name: 'uuid', nullable: 'NO', default: null }
    ],
    constraints: [
      { table: 'mazer_progression_states', name: 'mazer_progression_states_player_level_check', type: 'c', definition: 'CHECK (player_level >= 1 AND player_level <= 99)' },
      { table: 'mazer_progression_states', name: 'mazer_progression_states_player_target_complexity_check', type: 'c', definition: 'CHECK (player_target_complexity >= 8 AND player_target_complexity <= 240)' },
      { table: 'mazer_ai_progression_states', name: 'mazer_ai_progression_states_level_check', type: 'c', definition: 'CHECK (level >= 1 AND level <= 99)' },
      { table: 'mazer_ai_progression_states', name: 'mazer_ai_progression_states_target_complexity_check', type: 'c', definition: 'CHECK (target_complexity >= 8 AND target_complexity <= 240)' }
    ], indexes: [], functions: [], policies: [], triggers: [], username_secret_named_count: 0,
    schema_acl: [{ grantee: 'authenticated', privilege: 'USAGE', grantable: false }, { grantee: 'service_role', privilege: 'USAGE', grantable: false }],
    rls: ['mazer_ai_progression_states','mazer_cycle_receipts','mazer_profiles','mazer_progression_states'].map((table) => ({ table, enabled: true, forced: true }))
  };
}
function rawFixture() {
  const legacyEmails = [...sharedLegacy, ...legacyOnly].map((id, index) => [`person-${index}@example.test`, id]);
  const masterEmails = [...sharedMaster.map((id, index) => [`person-${index}@example.test`, id]), ...unrelatedMaster.map((id, index) => [`other-${index}@example.test`, id])];
  const resetLegacy = sharedLegacy[13]; const resetMaster = sharedMaster[13];
  const overlappingLegacyReceipts = Array.from({ length: 1281 }, (_, index) => receipt(uid(30000 + index), index < 1239 ? resetLegacy : sharedLegacy[0], uid(50000 + index), index));
  const overlappingMasterReceipts = overlappingLegacyReceipts.map((row, index) => ({ ...structuredClone(row), user_id: index < 1239 ? resetMaster : sharedMaster[0] }));
  const legacyOnlyReceipts = Array.from({ length: 597 }, (_, index) => receipt(uid(40000 + index), index < 477 ? resetLegacy : sharedLegacy[1], uid(60000 + index), 1281 + index));
  const masterOnlyReceipts = Array.from({ length: 9 }, (_, index) => receipt(uid(45000 + index), sharedMaster[2], uid(65000 + index), 2000 + index));
  const targetUsers = [0, 1, 2, 3, 4, 5, 13];
  return {
    legacy: {
      observed_at: iso(0), auth_users: legacyEmails.map(([email, id]) => user(id, email)), auth_identities: legacyEmails.map(([email, id], index) => identity(id, email, index)),
      profiles: sharedLegacy.slice(0, 13).map(profile), player: sharedLegacy.map((id, index) => player(id, index === 13)), ai: sharedLegacy.map((id, index) => ai(id, index === 13, false)), receipts: [...overlappingLegacyReceipts, ...legacyOnlyReceipts], catalog: catalog()
    },
    master: {
      observed_at: iso(-1000), auth_users: masterEmails.map(([email, id]) => user(id, email)), auth_identities: masterEmails.map(([email, id], index) => identity(id, email, 100 + index)),
      profiles: sharedMaster.slice(0, 5).map(profile), player: targetUsers.map((index) => player(sharedMaster[index], index === 13, index === 13)), ai: targetUsers.map((index) => ai(sharedMaster[index], index === 13, index === 13)), receipts: [...overlappingMasterReceipts, ...masterOnlyReceipts], catalog: catalog()
    }
  };
}
function acl(schema) {
  const table_acl = [...FENCE_CONTRACT.tables].sort().map((name) => ({ name, grants: [] }));
  const rpc_acl = [...FENCE_CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, grants: [{ grantee: 'authenticated', is_grantable: false }] }));
  const catalog = { tables: [...FENCE_CONTRACT.tables].sort().map((name) => ({ name, relkind: 'r', rls_enabled: true, force_rls: schema === 'mazer' })), rpcs: [...FENCE_CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, kind: 'f', security_definer: true, volatility: 'v' })) };
  return { schema, table_acl, rpc_acl, catalog, observed_at: iso(0) };
}

const fixture = rawFixture();
fixture.legacy.player[6].state = { legacySibling: 'preserved-missing-tracks' };
fixture.legacy.player[7].state = { legacySibling: 'preserved-nonobject-tracks', tracks: 'legacy-nonobject-tracks' };
fixture.master.player[0].state.masterRollbackSibling = 'preserved-master-preimage';
const plan = buildIdentityPlan(fixture.legacy, fixture.master);
assert.equal(plan.retained_edges.length, 2);
assert.equal(plan.new_edges.filter((edge) => edge.disposition === 'BIND_EXISTING').length, 14);
assert.equal(plan.imports.length, 3);
assert.ok(plan.imports.every((item) => item.user.raw_user_meta_data.app_namespace === undefined));
assert.deepEqual(plan.imports.at(-1).identities, [fixture.legacy.auth_identities.at(-1)]);

const source = producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: acl('public'), masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' });
const validated = validatePrivateSource(source);
const actionClassified = classifyCutover(validated.actionFenceInput);
const resetTargetUser = source.reset_era_ai.master_user_id;
const originalResetTarget = source.fence_input.target_snapshot.ai.find((row) => row.user_id === resetTargetUser && row.runner_key === 'menu-runner');
const actionResetTarget = validated.actionFenceInput.target_snapshot.ai.find((row) => row.user_id === resetTargetUser && row.runner_key === 'menu-runner');
const actionOverride = validated.actionFenceInput.desired_ai_overrides?.[0];
const expectedResetTarget = actionClassified.privatePlan.expected.ai.find((row) => row.user_id === resetTargetUser && row.runner_key === 'menu-runner');
const desiredResetTarget = actionClassified.privatePlan.desired.ai.find((row) => row.user_id === resetTargetUser && row.runner_key === 'menu-runner');
assert.deepEqual(actionResetTarget, originalResetTarget, 'action input changed the live target preimage');
assert.equal(actionOverride.payload_digest, sha256(actionOverride.row));
assert.notEqual(actionOverride.payload_digest, originalResetTarget.payload_digest);
assert.equal(expectedResetTarget.level, '39');
assert.equal(expectedResetTarget.completed_cycles, '108');
assert.equal(desiredResetTarget.level, '9');
assert.equal(desiredResetTarget.completed_cycles, '8');
assert.equal(actionClassified.receipt.monotonic_ai_merge, false, 'non-monotonic desired AI override was reported as monotonic');
assert.equal(classifyCutover(source.fence_input).receipt.monotonic_ai_merge, true, 'ordinary merged AI progression lost its monotonic receipt');
assert.equal(actionClassified.receipt.target_app_high_water_digest, classifyCutover(source.fence_input).receipt.target_app_high_water_digest);
const wrongOverride = structuredClone(validated.actionFenceInput); wrongOverride.desired_ai_overrides[0].row.updated_at = iso(1); wrongOverride.desired_ai_overrides[0].payload_digest = sha256(wrongOverride.desired_ai_overrides[0].row);
assert.throws(() => classifyCutover(wrongOverride), /DESIRED_AI_OVERRIDE_NOT_MAPPED_SOURCE/);
const duplicateOverride = structuredClone(validated.actionFenceInput); duplicateOverride.desired_ai_overrides.push(structuredClone(duplicateOverride.desired_ai_overrides[0]));
assert.throws(() => classifyCutover(duplicateOverride), /DESIRED_AI_OVERRIDE_DUPLICATE/);
const renderAuth = (auth) => renderOperationalSql({ auth, fenceInput: source.fence_input, catalogPreimage: source.catalog_preimage, reset: { quarantined_row: source.reset_era_ai.quarantined_row }, qa: source.qa, quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' });
const importUserExtraKey = structuredClone(source.auth); importUserExtraKey.imports[0].user.unexpected = true;
assert.throws(() => renderAuth(importUserExtraKey), /AUTH_USER_COLUMN_SHAPE_DRIFT/);
const boundUserMissingKey = structuredClone(source.auth); delete boundUserMissingKey.new_edges.find((edge) => edge.disposition === 'BIND_EXISTING').master_user.confirmed_at;
assert.throws(() => renderAuth(boundUserMissingKey), /AUTH_USER_COLUMN_SHAPE_DRIFT/);
const importIdentityExtraKey = structuredClone(source.auth); importIdentityExtraKey.imports[0].identities[0].unexpected = true;
assert.throws(() => renderAuth(importIdentityExtraKey), /AUTH_IDENTITY_COLUMN_SHAPE_DRIFT/);
const boundIdentityMissingKey = structuredClone(source.auth); delete boundIdentityMissingKey.new_edges.find((edge) => edge.disposition === 'BIND_EXISTING').master_identity.email;
assert.throws(() => renderAuth(boundIdentityMissingKey), /AUTH_IDENTITY_COLUMN_SHAPE_DRIFT/);
assert.deepEqual(source.fence_input.fence.legacy.acl_preimage, (({ schema, table_acl, rpc_acl, catalog }) => ({ schema, table_acl, rpc_acl, catalog }))(acl('public')));
assert.deepEqual(source.fence_input.fence.master.acl_preimage, (({ schema, table_acl, rpc_acl, catalog }) => ({ schema, table_acl, rpc_acl, catalog }))(acl('mazer')));
const missingTracksForward = source.fence_input.source_snapshot.player.find((row) => row.user_id === fixture.legacy.player[6].user_id).row;
const nonobjectTracksForward = source.fence_input.source_snapshot.player.find((row) => row.user_id === fixture.legacy.player[7].user_id).row;
assert.equal(missingTracksForward.state.legacySibling, 'preserved-missing-tracks');
assert.deepEqual(missingTracksForward.state.tracks.player, { level: missingTracksForward.player_level, completedCycles: missingTracksForward.player_completed_cycles });
assert.equal(nonobjectTracksForward.state.legacySibling, 'preserved-nonobject-tracks');
assert.deepEqual(nonobjectTracksForward.state.tracks.player, { level: nonobjectTracksForward.player_level, completedCycles: nonobjectTracksForward.player_completed_cycles });
assert.match(source.sql['postverify.sql'], /preserved-missing-tracks/);
assert.match(source.sql['postverify.sql'], /preserved-nonobject-tracks/);
assert.match(source.sql['rollback.sql'], /preserved-master-preimage/);
assert.doesNotMatch(source.sql['rollback.sql'], /preserved-missing-tracks|preserved-nonobject-tracks/);
const preM2MasterAcl = acl('mazer'); preM2MasterAcl.rpc_acl = []; preM2MasterAcl.catalog.rpcs = [];
const preM2Source = producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: acl('public'), masterAcl: preM2MasterAcl, quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' });
assert.equal(preM2Source.fence_input.fence.master.acl_basis, 'FRESH_LIVE_TABLES_PLUS_EXACT_M2_PLANNED_RPCS');
assert.equal(preM2Source.fence_input.fence.master.acl_preimage.rpc_acl.length, FENCE_CONTRACT.mutatingRpcs.length);
assert.deepEqual(preM2Source.fence_input.fence.master.acl_preimage.table_acl, preM2MasterAcl.table_acl);
assert.deepEqual(preM2Source.fence_input.fence.master.acl_preimage.catalog.tables, preM2MasterAcl.catalog.tables);
assert.equal(validated.allEdges.length, 19);
assert.deepEqual(validated.classified.desired_counts, { profiles: 13, player: 16, ai: 16, receipts: 1887 });
assert.equal(source.reset_era_ai.canonical_projection, '9/8/40/D');
assert.equal(source.reset_era_ai.legacy_receipts, 1716);
assert.equal(source.reset_era_ai.master_receipts, 1239);
assert.equal(source.reset_era_player.disposition, 'MASTER_DOMINATES_NO_OVERRIDE');
assert.equal(source.qa.personas, 4);
assert.equal(source.qa.rows.filter((row) => row.mode === 'generated').length, 1);
assert.match(source.sql['postverify.sql'], /R017_EXPLICIT_USERNAMES_CHANGED/);
assert.match(source.sql['postverify.sql'], /R017_GENERATED_USERNAME_REGENERATION_DRIFT/);
assert.match(source.sql['postverify.sql'], /username_origin/);
assert.match(source.sql['qa-apply.sql'], /R017_QA_GENERATED_USERNAME_DRIFT/);
assert.match(source.sql['rollback.sql'], /delete from vault\.secrets where name='mazer_username_handle_key'/);
assert.ok(source.sql['rollback.sql'].indexOf('drop column if exists username_origin') < source.sql['rollback.sql'].indexOf('insert into mazer.mazer_profiles'));
assert.equal(Object.keys(source.sql).length, 9);
for (const [name, sql] of Object.entries(source.sql)) {
  assert.match(sql, /^\\set ON_ERROR_STOP on\nbegin;/);
  assert.match(sql, /\ncommit;\n$/);
  assert.equal(source.sql_sha256[name], sha256(Buffer.from(sql, 'utf8')));
}

assert.match(SNAPSHOT_SQL('public'), /transaction isolation level serializable read only/i);
assert.match(SNAPSHOT_SQL('mazer'), /from mazer\.mazer_profiles/);
assert.throws(() => buildIdentityPlan({ ...fixture.legacy, auth_users: [...fixture.legacy.auth_users, fixture.legacy.auth_users[0]] }, fixture.master), /NORMALIZED_EMAIL_DUPLICATE/);
const identityCollision = { ...fixture.legacy, auth_identities: fixture.legacy.auth_identities.map((item) => structuredClone(item)) };
identityCollision.auth_identities.at(-1).id = fixture.master.auth_identities[0].id;
assert.throws(() => buildIdentityPlan(identityCollision, fixture.master), /IMPORT_IDENTITY_COLLISION/);
function importIdentityDrift(mutator) {
  const legacy = structuredClone(fixture.legacy);
  mutator(legacy.auth_identities.at(-1), legacy);
  return legacy;
}
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.provider = 'github'; }), fixture.master), /EMAIL_IDENTITY_PROVIDER_DRIFT/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.provider_id = uid(99999); }), fixture.master), /EMAIL_IDENTITY_PROVIDER_ID_DRIFT/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.provider_id = 'wrong@example.test'; }), fixture.master), /EMAIL_IDENTITY_PROVIDER_ID_MALFORMED/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.identity_data.sub = uid(99999); }), fixture.master), /EMAIL_IDENTITY_METADATA_SUB_DRIFT/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.identity_data.email = 'wrong@example.test'; }), fixture.master), /EMAIL_IDENTITY_METADATA_EMAIL_DRIFT/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.identity_data = null; }), fixture.master), /EMAIL_IDENTITY_METADATA_MALFORMED/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((_item, legacy) => { legacy.auth_identities.pop(); }), fixture.master), /EMAIL_IDENTITY_MISSING/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item, legacy) => { legacy.auth_identities.push({ ...structuredClone(item), id: uid(99998) }); }), fixture.master), /EMAIL_IDENTITY_MULTIPLE/);
assert.throws(() => buildIdentityPlan(importIdentityDrift((item) => { item.user_id = uid(99997); }), fixture.master), /EMAIL_IDENTITY_MISSING/);
const malformedPlayerState = structuredClone(fixture.legacy); malformedPlayerState.player[6].state = 'not-an-object';
assert.throws(() => producePrivateSource({ legacy: malformedPlayerState, master: fixture.master, legacyAcl: acl('public'), masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /PLAYER_STATE_MALFORMED/);
const aclExtra = { ...acl('public'), unexpected: true };
assert.throws(() => producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: aclExtra, masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /ACL_OBSERVATION_KEYS/);
const aclMissingTimestamp = acl('public'); delete aclMissingTimestamp.observed_at;
assert.throws(() => producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: aclMissingTimestamp, masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /ACL_OBSERVATION_KEYS/);
const aclMalformedTimestamp = { ...acl('public'), observed_at: 'not-a-timestamp' };
assert.throws(() => producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: aclMalformedTimestamp, masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /ACL_OBSERVATION_TIMESTAMP_DRIFT/);
const aclStaleTimestamp = { ...acl('public'), observed_at: iso(-360_000) };
assert.throws(() => producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: aclStaleTimestamp, masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /ACL_OBSERVATION_TIMESTAMP_DRIFT/);
assert.throws(() => producePrivateSource({ legacy: { ...fixture.legacy, receipts: fixture.legacy.receipts.slice(1) }, master: fixture.master, legacyAcl: acl('public'), masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /APP_DENOMINATOR_DRIFT|RESET_RECEIPT_DENOMINATOR_DRIFT/);
assert.throws(() => producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: acl('public'), masterAcl: acl('mazer'), quarantineKey: 'short', qaPassword: 'R017-fixture-password!' }), /PRIVATE_SECRET_INPUT_WEAK/);
assert.throws(() => producePrivateSource({ legacy: fixture.legacy, master: { ...fixture.master, catalog: { ...catalog(), columns: [...catalog().columns, { table: 'mazer_profiles', column: 'username' }] } }, legacyAcl: acl('public'), masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' }), /CATALOG_PREIMAGE_ALREADY_MIGRATED/);
const wrappedMigration = wrapMigrationTransaction(Buffer.from('select 1;\n'), 'M1').toString('utf8');
assert.match(wrappedMigration, /^\\set ON_ERROR_STOP on\nbegin;/);
assert.match(wrappedMigration, /M1_SINGLE_TRANSACTION/);
assert.equal((wrappedMigration.match(/\ncommit;/g) ?? []).length, 1);
assert.throws(() => wrapMigrationTransaction(Buffer.from('begin; select 1; commit;'), 'M2'), /MIGRATION_TRANSACTION_SHAPE/);

const producerPath = path.join(root, 'ops/atlas/produce_supabase_mazer_master_preparation_private_source_r017.mjs');
const materializerPath = path.join(root, 'ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs');
const producerText = fs.readFileSync(producerPath, 'utf8');
for (const forbidden of ['execute_sql', 'apply_migration', 'supabase db push', 'vercel deploy', 'git push']) assert.ok(!producerText.toLowerCase().includes(forbidden));
for (const token of ['PRIVATE_OUTPUT_MUST_BE_UNDER_SECRETS','EVIDENCE_DIGEST_DRIFT','IDENTITY_DENOMINATOR_DRIFT','RESET_RECEIPT_DENOMINATOR_DRIFT','transaction isolation level serializable read only']) assert.ok(producerText.includes(token));
assert.match(source.sql['auth-apply.sql'], /i\.provider_id=e->'user'->>'id'/);
assert.match(source.sql['auth-apply.sql'], /insert into auth\.users\("instance_id","id","aud","role","email","encrypted_password","email_confirmed_at"/);
assert.match(source.sql['auth-apply.sql'], /select \(r\)\."instance_id",\(r\)\."id",\(r\)\."aud",\(r\)\."role",\(r\)\."email"/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /insert into auth\.users\([^)]*"confirmed_at"[^)]*\)/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /insert into auth\.users select \(jsonb_populate_record\(null::auth\.users,value\)\)\.\*/);
assert.match(source.sql['auth-apply.sql'], /insert into auth\.identities\(id,user_id,provider_id,identity_data,provider,last_sign_in_at,created_at,updated_at\)/);
assert.match(source.sql['auth-apply.sql'], /select \(r\)\.id,\(r\)\.user_id,\(r\)\.provider_id,\(r\)\.identity_data,\(r\)\.provider,\(r\)\.last_sign_in_at,\(r\)\.created_at,\(r\)\.updated_at from records/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /insert into auth\.identities select \(jsonb_populate_record\(null::auth\.identities,value\)\)\.\*/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /insert into auth\.identities\([^)]*email[^)]*\)/);
for (const token of [
  'R017_BOUND_AUTH_USER_CARDINALITY_DRIFT','R017_BOUND_AUTH_USER_EMAIL_DRIFT','R017_BOUND_AUTH_IDENTITY_CARDINALITY_DRIFT',
  'R017_BOUND_AUTH_EMAIL_IDENTITY_MULTIPLE','R017_BOUND_AUTH_IDENTITY_OWNER_DRIFT','R017_BOUND_AUTH_IDENTITY_PROVIDER_DRIFT',
  'R017_BOUND_AUTH_IDENTITY_PROVIDER_ID_DRIFT','R017_BOUND_AUTH_IDENTITY_SUBJECT_DRIFT','R017_BOUND_AUTH_IDENTITY_EMAIL_DRIFT',
  'atlas_mazer_r017.auth_preimage','R017_AUTH_PREIMAGE_CARDINALITY_DRIFT','R017_BOUND_AUTH_USER_MUTATION_DRIFT','R017_BOUND_AUTH_IDENTITY_MUTATION_DRIFT'
]) assert.ok(source.sql['auth-apply.sql'].includes(token), `action-time Auth preimage contract missing ${token}`);
assert.match(source.sql['auth-apply.sql'], /jsonb_typeof\(i\.identity_data\) is distinct from 'object'/);
assert.match(source.sql['auth-apply.sql'], /i\.identity_data->>'sub' is distinct from e->'user'->>'id'/);
assert.match(source.sql['auth-apply.sql'], /lower\(i\.identity_data->>'email'\) is distinct from e->>'normalized_email'/);
assert.match(source.sql['auth-apply.sql'], /revoke all on atlas_mazer_r017\.auth_preimage from anon,authenticated,public/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /R017_EXISTING_AUTH_(USER|IDENTITY)_DIGEST_DRIFT/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /to_jsonb\(u\)=to_jsonb\(jsonb_populate_record\(null::auth\.users,e->'user'\)\)|to_jsonb\(i\)=to_jsonb\(jsonb_populate_record\(null::auth\.identities,e->'identity'\)\)/);
assert.match(source.sql['auth-apply.sql'], /jsonb_agg\(to_jsonb\(x\.r\) order by \(x\.r\)\.id\)/);
assert.doesNotMatch(source.sql['auth-apply.sql'], /to_jsonb\(u\)=e->'user'|to_jsonb\(i\)=e->'identity'/);
assert.match(source.sql['postverify.sql'], /jsonb_agg\(to_jsonb\(x\.r\) order by \(x\.r\)\.id\)/);
assert.match(source.sql['postverify.sql'], /jsonb_populate_record\(null::mazer\.mazer_profiles,value\)/);
assert.match(source.sql['postverify.sql'], /jsonb_populate_record\(null::mazer\.mazer_progression_states,value\)/);
assert.match(source.sql['postverify.sql'], /jsonb_populate_record\(null::mazer\.mazer_ai_progression_states,value\)/);
assert.match(source.sql['postverify.sql'], /jsonb_populate_record\(null::mazer\.mazer_cycle_receipts,value\)/);
assert.match(source.sql['postverify.sql'], /atlas_mazer_r017\.auth_preimage/);
assert.match(source.sql['postverify.sql'], /R017_BOUND_AUTH_USER_MUTATION_DRIFT/);
assert.match(source.sql['postverify.sql'], /R017_BOUND_AUTH_IDENTITY_MUTATION_DRIFT/);
assert.doesNotMatch(source.sql['postverify.sql'], /R017_BOUND_AUTH_(USERS|IDENTITIES)_FULL_DIGEST_DRIFT/);
assert.doesNotMatch(source.sql['postverify.sql'], /<> '\[[^']*T[^']*Z[^']*\]'::jsonb then raise exception 'R017_(PROFILES_CORE|PLAYER_FULL|AI_FULL|RECEIPT_CONSERVATION_FULL)_DIGEST_DRIFT'/);
assert.doesNotMatch(source.sql['postverify.sql'], /to_jsonb\(u\)=e->'user'|to_jsonb\(i\)=e->'identity'/);
assert.match(source.sql['qa-apply.sql'], /select gen_random_uuid\(\),id,id::text,jsonb_build_object\('sub',id::text,'email',email\)/);

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-r017-producer-'));
try {
  const privateFile = path.join(tmp, 'private-source.json'); fs.writeFileSync(privateFile, `${JSON.stringify(source)}\n`, { mode: 0o600 });
  const out = path.join(tmp, 'materialized');
  const child = spawnSync(process.execPath, [materializerPath, '--input', privateFile, '--output', out, '--mazer-repository', mazerRepository], { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 180_000 });
  assert.equal(child.status, 0, child.stdout + child.stderr);
  const resultLines = child.stdout.trim().split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
  assert.equal(resultLines.length, 1, 'materializer main executed more than once');
  assert.equal(resultLines[0].result, 'PRIVATE_R017_PACKET_SEALED');
  assert.equal(fs.readdirSync(out).length, 15);
  for (const name of ['m1.sql','m2.sql','m3.sql','m4.sql']) {
    const migration = fs.readFileSync(path.join(out, name), 'utf8');
    assert.match(migration, /^\\set ON_ERROR_STOP on\nbegin;/);
    assert.equal((migration.match(/\ncommit;/g) ?? []).length, 1);
  }
} finally { fs.rmSync(tmp, { recursive: true, force: true }); }

const privateWriteRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-r017-private-write-'));
try {
  fs.mkdirSync(path.join(privateWriteRoot, 'secrets'));
  const result = writePrivateSource(privateWriteRoot, undefined, { fixture: true });
  assert.ok(result.path.startsWith(path.join(privateWriteRoot, 'secrets')));
  assert.equal(fs.readFileSync(result.path, 'utf8'), '{"fixture":true}\n');
} finally { fs.rmSync(privateWriteRoot, { recursive: true, force: true }); }
const junctionRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-r017-private-junction-'));
const junctionOutside = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-r017-private-outside-'));
try {
  fs.mkdirSync(path.join(junctionRoot, 'secrets'));
  fs.symlinkSync(junctionOutside, path.join(junctionRoot, 'secrets', 'packet'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => writePrivateSource(junctionRoot, undefined, { fixture: true }), /REPARSE_COMPONENT_REJECTED/);
} finally { fs.rmSync(junctionRoot, { recursive: true, force: true }); fs.rmSync(junctionOutside, { recursive: true, force: true }); }

const sourceCheck = spawnSync(process.execPath, [producerPath, '--source-check', 'true'], { cwd: root, encoding: 'utf8', windowsHide: true });
assert.equal(sourceCheck.status, 0, sourceCheck.stderr);
assert.equal(JSON.parse(sourceCheck.stdout).result, 'PASS_R017_PRIVATE_SOURCE_PRODUCER_SOURCE');

const rendered = renderOperationalSql({ auth: source.auth, fenceInput: source.fence_input, catalogPreimage: source.catalog_preimage, reset: { quarantined_row: source.reset_era_ai.quarantined_row }, qa: source.qa, quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' });
assert.deepEqual(Object.keys(rendered.sql), [...Object.keys(source.sql)]);

console.log(JSON.stringify({ result: 'PASS_MAZER_MASTER_PREPARATION_PRIVATE_SOURCE_R017', identity_edges: 19, imports: 3, binds: 14, retained: 2, app_counts: validated.classified.desired_counts, sql_programs: 9, provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_private_output: 0 }));
