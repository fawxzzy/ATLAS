import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { CONTRACT as FENCE_CONTRACT, sha256 } from '../classify_supabase_mazer_master_cutover_data_fence_r001.mjs';
import { validatePrivateSource, wrapMigrationTransaction } from '../materialize_supabase_mazer_master_preparation_r017.mjs';
import {
  PRODUCER_CONTRACT,
  SNAPSHOT_SQL,
  buildIdentityPlan,
  producePrivateSource,
  renderOperationalSql,
  writePrivateSource
} from '../produce_supabase_mazer_master_preparation_private_source_r017.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
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
const sharedLegacy = Array.from({ length: 15 }, (_, index) => uid(index + 1));
const sharedMaster = sharedLegacy.map((id, index) => index < 2 ? id : uid(100 + index));
const legacyOnly = [uid(16), uid(17), uid(18)];
const unrelatedMaster = Array.from({ length: 99 }, (_, index) => uid(1000 + index));

function user(id, email, instance = uid(9000)) {
  return { id, instance_id: instance, aud: 'authenticated', role: 'authenticated', email, encrypted_password: verifier, email_confirmed_at: iso(-10000), raw_app_meta_data: { provider: 'email', providers: ['email'] }, raw_user_meta_data: {}, created_at: iso(-20000), updated_at: iso(-10000) };
}
function identity(id, email, index) { return { id: uid(20000 + index), user_id: id, provider_id: id, identity_data: { sub: id, email }, provider: 'email', created_at: iso(-20000), updated_at: iso(-10000), last_sign_in_at: iso(-10000) }; }
function profile(id, index) { return { user_id: id, display_name: null, selected_control_mode: 'stick', settings: { trailFade: true }, created_at: iso(-9000), updated_at: iso(-8000), revision: index, username: index % 2 ? null : `u${index + 10}` }; }
function player(id, reset = false) {
  const level = reset ? 5 : 2; const cycles = reset ? 4 : 1; const complexity = reset ? 24 : 12;
  return { user_id: id, schema_version: 1, state: { tracks: { player: { level, completedCycles: cycles, targetComplexity: complexity } } }, last_completed_cycle_at: iso(-7000), created_at: iso(-9000), updated_at: iso(-7000), player_level: level, player_rank: 'E', player_target_complexity: complexity, player_completed_cycles: cycles, revision: 0, level_reached_at: iso(-7000) };
}
function ai(id, reset, target = false) {
  const level = reset ? (target ? 39 : 7) : 2; const cycles = reset ? (target ? 108 : 6) : 1; const complexity = reset ? (target ? 161 : 32) : 12; const rank = reset ? (target ? 'S' : 'D') : 'E';
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
    ], indexes: [], functions: [], policies: [], triggers: [],
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
  const legacyOnlyReceipts = Array.from({ length: 592 }, (_, index) => receipt(uid(40000 + index), index < 475 ? resetLegacy : sharedLegacy[1], uid(60000 + index), 1281 + index));
  const masterOnlyReceipts = Array.from({ length: 9 }, (_, index) => receipt(uid(45000 + index), sharedMaster[2], uid(65000 + index), 2000 + index));
  const targetUsers = [0, 1, 2, 3, 4, 5, 13];
  return {
    legacy: {
      observed_at: iso(0), auth_users: legacyEmails.map(([email, id]) => user(id, email)), auth_identities: legacyEmails.map(([email, id], index) => identity(id, email, index)),
      profiles: sharedLegacy.slice(0, 10).map(profile), player: sharedLegacy.map((id, index) => player(id, index === 13)), ai: sharedLegacy.map((id, index) => ai(id, index === 13, false)), receipts: [...overlappingLegacyReceipts, ...legacyOnlyReceipts], catalog: catalog()
    },
    master: {
      observed_at: iso(-1000), auth_users: masterEmails.map(([email, id]) => user(id, email)), auth_identities: masterEmails.map(([email, id], index) => identity(id, email, 100 + index)),
      profiles: sharedMaster.slice(0, 5).map(profile), player: targetUsers.map((index) => player(sharedMaster[index], index === 13)), ai: targetUsers.map((index) => ai(sharedMaster[index], index === 13, index === 13)), receipts: [...overlappingMasterReceipts, ...masterOnlyReceipts], catalog: catalog()
    }
  };
}
function acl(schema) {
  const table_acl = [...FENCE_CONTRACT.tables].sort().map((name) => ({ name, grants: [] }));
  const rpc_acl = [...FENCE_CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, grants: [{ grantee: 'authenticated', is_grantable: false }] }));
  const catalog = { tables: [...FENCE_CONTRACT.tables].sort().map((name) => ({ name, relkind: 'r', rls_enabled: true, force_rls: schema === 'mazer' })), rpcs: [...FENCE_CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, kind: 'f', security_definer: true, volatility: 'v' })) };
  return { schema, table_acl, rpc_acl, catalog };
}

const fixture = rawFixture();
fixture.legacy.player[6].state = { legacySibling: 'preserved-missing-tracks' };
fixture.legacy.player[7].state = { legacySibling: 'preserved-nonobject-tracks', tracks: 'legacy-nonobject-tracks' };
fixture.master.player[0].state.masterRollbackSibling = 'preserved-master-preimage';
const plan = buildIdentityPlan(fixture.legacy, fixture.master);
assert.equal(plan.retained_edges.length, 2);
assert.equal(plan.new_edges.filter((edge) => edge.disposition === 'BIND_EXISTING').length, 13);
assert.equal(plan.imports.length, 3);
assert.ok(plan.imports.every((item) => item.user.raw_user_meta_data.app_namespace === undefined));
assert.deepEqual(plan.imports.at(-1).identities, [fixture.legacy.auth_identities.at(-1)]);

const source = producePrivateSource({ legacy: fixture.legacy, master: fixture.master, legacyAcl: acl('public'), masterAcl: acl('mazer'), quarantineKey: 'q'.repeat(64), qaPassword: 'R017-fixture-password!' });
const validated = validatePrivateSource(source);
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
assert.equal(validated.allEdges.length, 18);
assert.deepEqual(validated.classified.desired_counts, { profiles: 10, player: 15, ai: 15, receipts: 1882 });
assert.equal(source.reset_era_ai.canonical_projection, '7/6/32/D');
assert.equal(source.reset_era_ai.legacy_receipts, 1714);
assert.equal(source.reset_era_ai.master_receipts, 1239);
assert.equal(source.qa.personas, 4);
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
  assert.equal(fs.readdirSync(out).length, 14);
  for (const name of ['m1.sql','m2.sql','m3.sql']) {
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

console.log(JSON.stringify({ result: 'PASS_MAZER_MASTER_PREPARATION_PRIVATE_SOURCE_R017', identity_edges: 18, imports: 3, binds: 13, retained: 2, app_counts: validated.classified.desired_counts, sql_programs: 9, provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_private_output: 0 }));
