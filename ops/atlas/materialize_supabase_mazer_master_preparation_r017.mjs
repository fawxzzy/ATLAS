import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { classifyCutover, sha256 } from './classify_supabase_mazer_master_cutover_data_fence_r001.mjs';

export const CONTRACT = Object.freeze({
  schema: 'atlas.supabase.mazer-master-preparation-private-source.r017.v1',
  packet: 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001',
  legacy: 'geknvnrmktchljnyddwp',
  master: 'bxtcuhkotumitoqtrcej',
  currentPreimageSha256: 'ddaaaf9fc9f8a5da781287c2ae76c194af593484208fb3f4c480fc4603b798fe',
  restoreProofSha256: '54dee535bac3e02b7058fe644cd44af115cc3746ff1e40390521992dccd14971',
  predecessorFenceManifestSha256: '63f43d8c2f532b32e3453879e4ca49ffc2f5b382264a290ad9a3ea1225811ced',
  migrations: Object.freeze([
    Object.freeze({ phase: 'M1', blob: '2b8495a95fca9a860571343174bfb93bcad8c5e9', name: 'm1.sql' }),
    Object.freeze({ phase: 'M2', blob: '1bbf69cf8f38aa1e2b053d0b70d82a315317b58a', name: 'm2.sql' }),
    Object.freeze({ phase: 'M3', blob: '481ab55323afff53f5e841012684b7e26f689349', name: 'm3.sql' })
  ]),
  sqlNames: Object.freeze(['preflight.sql', 'master-fence.sql', 'master-refence.sql', 'auth-apply.sql', 'reset-era-apply.sql', 'postverify.sql', 'qa-apply.sql', 'qa-cleanup.sql', 'rollback.sql'])
});

const UUID = /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i;
const DIGEST = /^[0-9a-f]{64}$/;
const BCRYPT = /^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$/;
const plain = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const requiredDigest = (value, code) => { if (!DIGEST.test(String(value ?? ''))) throw new Error(code); return value; };
const requiredUuid = (value, code) => { if (!UUID.test(String(value ?? ''))) throw new Error(code); return value.toLowerCase(); };
const canonical = (value) => value === null || typeof value !== 'object'
  ? JSON.stringify(value)
  : Array.isArray(value)
    ? `[${value.map(canonical).join(',')}]`
    : `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;

const SQL_TOKENS = Object.freeze({
  'preflight.sql': ['data_api', 'rls', 'acl', 'auth.users', '114', '10', '15', '1880'],
  'master-fence.sql': ['begin;', 'mazer_profiles', 'mazer_progression_states', 'mazer_ai_progression_states', 'mazer_cycle_receipts', 'revoke'],
  'master-refence.sql': ['begin;', 'mazer_initialize_progression', 'mazer_complete_level', 'mazer_complete_ai_level', 'mazer_reset_progression', 'revoke'],
  'auth-apply.sql': ['auth.users', 'auth.identities', 'create_and_bind', 'bind_existing', '3_auth_imports', '2_existing_binds'],
  'reset-era-apply.sql': ['whole_row_override', '5/4/24/e', '39/108/161/s', 'pgp_sym_encrypt', 'player_reset_disposition'],
  'postverify.sql': ['data_api', 'rls', 'acl', '117', '18', '10', '15', '1880', 'receipt_conservation'],
  'qa-apply.sql': ['qa_ttl', 'before_user_created', 'rollback_on_error'],
  'qa-cleanup.sql': ['qa_ttl', 'delete', 'auth.identities', 'auth.users'],
  'rollback.sql': ['disable_hook_first', 'master_preimage', 'receipt_conservation']
});

export function assertSql(name, sql) {
  if (typeof sql !== 'string' || sql.length < 16 || sql.length > 2_000_000) throw new Error(`SQL_SHAPE:${name}`);
  const lower = sql.toLowerCase();
  for (const forbidden of ['vercel', 'github', 'billing', 'drop database', 'alter project', 'geknvnrmktchljnyddwp.supabase.co']) {
    if (lower.includes(forbidden)) throw new Error(`SQL_SCOPE_DRIFT:${name}`);
  }
  if (!lower.includes('begin;') && !sql.includes('ON_ERROR_STOP')) throw new Error(`SQL_FAIL_CLOSED_MISSING:${name}`);
  for (const token of SQL_TOKENS[name] ?? []) if (!lower.includes(token)) throw new Error(`SQL_CONTRACT_TOKEN_MISSING:${name}:${token}`);
}

export const HOST_PHASES = Object.freeze(['PREFLIGHT','FENCE_APPLYING','FENCE_PAUSED','MASTER_FENCE_APPLYING','MASTER_FENCED','M1_APPLYING','M1_APPLIED','M2_APPLYING','M2_APPLIED','MASTER_REFENCE_APPLYING','MASTER_REFENCED','AUTH_APPLYING','AUTH_APPLIED','RESET_QUARANTINE_APPLYING','RESET_QUARANTINE_SEALED','DELTA_APPLYING','DELTA_APPLIED','M3_APPLYING','M3_APPLIED','POSTVERIFYING','POSTVERIFIED','HOOK_ACTIVATING','HOOK_ACTIVE','QA_APPLYING','QA_COMPLETE','QA_CLEANING','QA_CLEAN','LEGACY_RESTORING','LEGACY_RESTORED','PREPARATION_COMPLETE','ROLLBACK_DISABLING_HOOK','ROLLBACK_TARGET_RESTORING','ROLLBACK_LEGACY_RESTORING','ROLLED_BACK','AMBIGUOUS_HOLD']);

export function classifyHostRecovery(state) {
  if (state == null) return { action: 'START', effect: 'NONE' };
  if (!plain(state) || state.schema !== 'atlas.supabase.mazer-master-preparation-host-state.r017.v1') throw new Error('STATE_SCHEMA_DRIFT');
  if (state.phase === 'PREPARATION_COMPLETE') return { action: 'NOOP', effect: 'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER' };
  if (state.phase === 'ROLLED_BACK') return { action: 'NOOP', effect: 'TERMINAL_ROLLBACK' };
  if (!HOST_PHASES.includes(state.phase)) throw new Error('STATE_PHASE_DRIFT');
  if (state.phase === 'AMBIGUOUS_HOLD') return { action: 'ROLLBACK_REQUIRED', effect: 'AMBIGUOUS' };
  if (state.phase.endsWith('_APPLYING') || state.phase.endsWith('_ACTIVATING') || state.phase.endsWith('_CLEANING') || state.phase.endsWith('VERIFYING')) return { action: 'ROLLBACK_REQUIRED', effect: 'AMBIGUOUS' };
  if (state.phase.startsWith('ROLLBACK_') || state.phase === 'LEGACY_RESTORING') return { action: 'ROLLBACK_REQUIRED', effect: 'RESTORE_INCOMPLETE' };
  if (state.phase === 'FENCE_PAUSED' || state.phase === 'MASTER_FENCED' || state.phase === 'M1_APPLIED' || state.phase === 'M2_APPLIED' || state.phase === 'MASTER_REFENCED' || state.phase === 'AUTH_APPLIED') return { action: 'RESUME_EXACT', effect: 'LEGACY_FENCED' };
  if (state.phase === 'RESET_QUARANTINE_SEALED' || state.phase === 'DELTA_APPLIED' || state.phase === 'POSTVERIFIED' || state.phase === 'QA_COMPLETE') return { action: 'RESUME_EXACT', effect: 'MASTER_STAGED_LEGACY_FENCED' };
  if (state.phase === 'M3_APPLIED' || state.phase === 'HOOK_ACTIVE' || state.phase === 'QA_CLEAN' || state.phase === 'LEGACY_RESTORED') return { action: 'RESUME_EXACT', effect: 'MASTER_STAGED_LEGACY_FENCED' };
  if (state.phase === 'PREFLIGHT') return { action: 'RESUME_EXACT', effect: 'NONE' };
  throw new Error('STATE_PHASE_DRIFT');
}

function bindResetEraActionInput(raw, allEdges) {
  if (!plain(raw.reset_era_player)
    || raw.reset_era_player.disposition !== 'MAPPED_ROWS_EQUAL_NO_OVERRIDE'
    || raw.reset_era_player.source_row_digest !== raw.reset_era_player.target_row_digest) throw new Error('PLAYER_RESET_DISPOSITION_DRIFT');
  requiredDigest(raw.reset_era_player.source_row_digest, 'PLAYER_RESET_SOURCE_DIGEST');
  const sourceUser = requiredUuid(raw.reset_era_ai.legacy_user_id, 'RESET_AI_LEGACY_UUID');
  const targetUser = requiredUuid(raw.reset_era_ai.master_user_id, 'RESET_AI_MASTER_UUID');
  const edge = allEdges.find((item) => item.legacy_user_id.toLowerCase() === sourceUser && item.master_user_id.toLowerCase() === targetUser);
  if (!edge) throw new Error('RESET_AI_IDENTITY_EDGE_MISSING');
  const action = structuredClone(raw.fence_input);
  const sourceAi = action.source_snapshot?.ai?.find((item) => item.user_id.toLowerCase() === sourceUser && item.runner_key === 'menu-runner');
  const targetIndex = action.target_snapshot?.ai?.findIndex((item) => item.user_id.toLowerCase() === targetUser && item.runner_key === 'menu-runner');
  if (!sourceAi || targetIndex < 0) throw new Error('RESET_AI_ROW_MISSING');
  if (sha256(sourceAi) !== requiredDigest(raw.reset_era_ai.canonical_row_digest, 'RESET_AI_CANONICAL_DIGEST')
    || sha256(action.target_snapshot.ai[targetIndex]) !== requiredDigest(raw.reset_era_ai.quarantined_row_digest, 'RESET_AI_QUARANTINE_DIGEST')) throw new Error('RESET_AI_ROW_DIGEST_DRIFT');
  const mapped = structuredClone(sourceAi);
  mapped.user_id = targetUser;
  mapped.row.user_id = targetUser;
  mapped.payload_digest = sha256(mapped.row);
  action.target_snapshot.ai[targetIndex] = mapped;
  const sourcePlayer = action.source_snapshot?.player?.find((item) => item.user_id.toLowerCase() === sourceUser);
  const targetPlayer = action.target_snapshot?.player?.find((item) => item.user_id.toLowerCase() === targetUser);
  if (!sourcePlayer || !targetPlayer) throw new Error('PLAYER_RESET_ROW_MISSING');
  const mappedPlayer = structuredClone(sourcePlayer);
  mappedPlayer.user_id = targetUser;
  mappedPlayer.row.user_id = targetUser;
  mappedPlayer.payload_digest = sha256(mappedPlayer.row);
  if (mappedPlayer.payload_digest !== targetPlayer.payload_digest
    || mappedPlayer.payload_digest !== raw.reset_era_player.source_row_digest) throw new Error('PLAYER_RESET_EQUALITY_DRIFT');
  return action;
}

export function validatePrivateSource(raw) {
  if (!plain(raw) || raw.schema !== CONTRACT.schema || raw.packet !== CONTRACT.packet) throw new Error('PRIVATE_SOURCE_SCHEMA');
  if (!plain(raw.evidence)
    || raw.evidence.current_preimage_sha256 !== CONTRACT.currentPreimageSha256
    || raw.evidence.restore_proof_sha256 !== CONTRACT.restoreProofSha256
    || raw.evidence.predecessor_fence_manifest_sha256 !== CONTRACT.predecessorFenceManifestSha256) throw new Error('EVIDENCE_BINDING_DRIFT');
  if (!plain(raw.fence_input)) throw new Error('FENCE_INPUT_MISSING');
  if (!plain(raw.catalog_preimage) || !Array.isArray(raw.catalog_preimage.columns) || !Array.isArray(raw.catalog_preimage.constraints)
    || !Array.isArray(raw.catalog_preimage.indexes) || !Array.isArray(raw.catalog_preimage.functions) || !Array.isArray(raw.catalog_preimage.policies)
    || !Array.isArray(raw.catalog_preimage.triggers) || !Array.isArray(raw.catalog_preimage.schema_acl) || !Array.isArray(raw.catalog_preimage.rls)) throw new Error('CATALOG_PREIMAGE_SHAPE');
  if (requiredDigest(raw.catalog_preimage_sha256, 'CATALOG_PREIMAGE_DIGEST') !== sha256(raw.catalog_preimage)) throw new Error('CATALOG_PREIMAGE_DIGEST_DRIFT');
  const classified = classifyCutover(raw.fence_input).receipt;
  if (classified.direction !== 'forward') throw new Error('FENCE_DIRECTION_DRIFT');
  const counts = classified.desired_counts;
  if (counts.profiles !== 10 || counts.player !== 15 || counts.ai !== 15 || counts.receipts !== 1880) throw new Error('APP_DENOMINATOR_DRIFT');
  if (classified.receipt_conservation.primary_conflicts !== 0 || classified.receipt_conservation.client_run_conflicts !== 0) throw new Error('RECEIPT_CONFLICT');
  if (!plain(raw.auth) || !Array.isArray(raw.auth.imports) || !Array.isArray(raw.auth.new_edges) || !Array.isArray(raw.auth.retained_edges)) throw new Error('AUTH_PLAN_SHAPE');
  if (raw.auth.imports.length !== 3 || raw.auth.new_edges.length !== 5 || raw.auth.retained_edges.length !== 13) throw new Error('AUTH_DENOMINATOR_DRIFT');
  const allEdges = [...raw.auth.retained_edges, ...raw.auth.new_edges];
  const legacyIds = new Set();
  const masterIds = new Set();
  for (const edge of allEdges) {
    const legacy = requiredUuid(edge.legacy_user_id, 'EDGE_LEGACY_UUID');
    const master = requiredUuid(edge.master_user_id, 'EDGE_MASTER_UUID');
    requiredDigest(edge.evidence_digest, 'EDGE_EVIDENCE_DIGEST');
    if (legacyIds.has(legacy) || masterIds.has(master)) throw new Error('AMBIGUOUS_IDENTITY_MAP');
    legacyIds.add(legacy); masterIds.add(master);
  }
  if (legacyIds.size !== 18 || masterIds.size !== 18) throw new Error('IDENTITY_EDGE_DENOMINATOR_DRIFT');
  if (raw.auth.new_edges.filter((edge) => edge.disposition === 'BIND_EXISTING').length !== 2
    || raw.auth.new_edges.filter((edge) => edge.disposition === 'CREATE_AND_BIND').length !== 3) throw new Error('AUTH_DISPOSITION_DRIFT');
  for (const item of raw.auth.imports) {
    requiredUuid(item.user?.id, 'IMPORT_USER_UUID');
    if (typeof item.user?.email !== 'string' || !item.user.email.includes('@') || !BCRYPT.test(String(item.user?.encrypted_password ?? ''))) throw new Error('UNSUPPORTED_PASSWORD_VERIFIER');
    if (item.user.raw_user_meta_data?.app_namespace === 'mazer') throw new Error('IMPORT_WOULD_FIRE_SIGNUP_TRIGGER');
    if (!Array.isArray(item.identities) || item.identities.length !== 1 || item.identities[0].provider !== 'email') throw new Error('IMPORT_IDENTITY_SHAPE');
    if (requiredUuid(item.identities[0].user_id, 'IMPORT_IDENTITY_OWNER') !== item.user.id.toLowerCase()) throw new Error('IMPORT_IDENTITY_OWNER_DRIFT');
  }
  if (!plain(raw.reset_era_ai)
    || raw.reset_era_ai.canonical_projection !== '5/4/24/E'
    || raw.reset_era_ai.quarantined_projection !== '39/108/161/S'
    || raw.reset_era_ai.legacy_receipts !== 1712
    || raw.reset_era_ai.master_receipts !== 1239
    || raw.reset_era_ai.legacy_timestamps_newer !== true
    || raw.reset_era_ai.override_mode !== 'EXACT_WHOLE_ROW'
    || raw.reset_era_ai.quarantine_encryption !== 'PGP_SYM_ENCRYPT_AES256') throw new Error('RESET_ERA_DECISION_DRIFT');
  if (!plain(raw.qa) || raw.qa.personas < 1 || raw.qa.personas > 4 || raw.qa.auth_rows < 1 || raw.qa.auth_rows > 5 || raw.qa.ttl_minutes > 30) throw new Error('QA_CEILING_DRIFT');
  if (!plain(raw.sql)) throw new Error('SQL_PACKET_MISSING');
  if (!plain(raw.sql_sha256)) throw new Error('SQL_DIGESTS_MISSING');
  for (const name of CONTRACT.sqlNames) {
    assertSql(name, raw.sql[name]);
    if (requiredDigest(raw.sql_sha256[name], `SQL_DIGEST_MISSING:${name}`) !== sha256(Buffer.from(`${raw.sql[name].trim()}\n`, 'utf8'))) throw new Error(`SQL_DIGEST_DRIFT:${name}`);
  }
  const actionFenceInput = bindResetEraActionInput(raw, allEdges);
  const actionClassified = classifyCutover(actionFenceInput).receipt;
  if (actionClassified.desired_counts.profiles !== 10 || actionClassified.desired_counts.player !== 15 || actionClassified.desired_counts.ai !== 15 || actionClassified.desired_counts.receipts !== 1880) throw new Error('ACTION_APP_DENOMINATOR_DRIFT');
  const fenceInputSha256 = sha256(Buffer.from(canonical(actionFenceInput), 'utf8'));
  return { classified: actionClassified, fenceInputSha256, allEdges, actionFenceInput };
}

function gitBlob(mazerRepository, blob) {
  const child = spawnSync('git', ['-C', mazerRepository, 'cat-file', '-p', blob], { encoding: null, windowsHide: true, maxBuffer: 4_000_000 });
  if (child.status !== 0 || child.signal || !Buffer.isBuffer(child.stdout) || child.stdout.length < 16) throw new Error(`MIGRATION_BLOB_MISSING:${blob}`);
  return child.stdout;
}

export function wrapMigrationTransaction(bytes, phase) {
  const sql = bytes.toString('utf8');
  if (!['M1', 'M2', 'M3'].includes(phase) || !sql.trim() || /(^|\n)\s*(begin|start\s+transaction|commit|rollback)\s*;/im.test(sql)) throw new Error(`MIGRATION_TRANSACTION_SHAPE:${phase}`);
  return Buffer.from(`\\set ON_ERROR_STOP on\nbegin;\nset local lock_timeout = '120s';\nset local statement_timeout = '150s';\n-- ${phase}_SINGLE_TRANSACTION\n${sql.trim()}\ncommit;\n`, 'utf8');
}

function writeExclusive(file, bytes) {
  fs.writeFileSync(file, bytes, { flag: 'wx', mode: 0o600 });
}

export function materialize(raw, outputRoot, mazerRepository) {
  const { classified, fenceInputSha256, actionFenceInput } = validatePrivateSource(raw);
  fs.mkdirSync(outputRoot, { recursive: false, mode: 0o700 });
  const files = [];
  const add = (name, bytes) => { const file = path.join(outputRoot, name); writeExclusive(file, bytes); files.push({ name, sha256: sha256(bytes), bytes: bytes.length }); };
  add('fence-input.json', Buffer.from(`${canonical(actionFenceInput)}\n`, 'utf8'));
  for (const migration of CONTRACT.migrations) add(migration.name, wrapMigrationTransaction(gitBlob(mazerRepository, migration.blob), migration.phase));
  for (const name of CONTRACT.sqlNames) add(name, Buffer.from(`${raw.sql[name].trim()}\n`, 'utf8'));
  const manifest = {
    schema: 'atlas.supabase.mazer-master-preparation-private-manifest.r017.v1',
    packet: CONTRACT.packet,
    fence_input_sha256: fenceInputSha256,
    predecessor_fence_manifest_sha256: CONTRACT.predecessorFenceManifestSha256,
    app_counts: classified.desired_counts,
    receipt_conservation: classified.receipt_conservation,
    auth_counts: { imports: 3, binds: 2, retained_edges: 13, final_edges: 18, expected_target_users: 117 },
    reset_era_ai: { canonical: '5/4/24/E', quarantined: '39/108/161/S', override: 'EXACT_WHOLE_ROW', quarantine: 'PGP_SYM_ENCRYPT_AES256' },
    reset_era_player: { disposition: 'MAPPED_ROWS_EQUAL_NO_OVERRIDE', digest: raw.reset_era_player.source_row_digest },
    qa: { personas: raw.qa.personas, auth_rows: raw.qa.auth_rows, ttl_minutes: raw.qa.ttl_minutes },
    files
  };
  add('manifest.json', Buffer.from(`${canonical(manifest)}\n`, 'utf8'));
  return { manifest, manifestSha256: files.at(-1).sha256 };
}

async function main() {
  const args = Object.fromEntries(process.argv.slice(2).reduce((rows, value, index, all) => index % 2 === 0 ? [...rows, [value, all[index + 1]]] : rows, []));
  if (args['--source-check'] === 'true') {
    process.stdout.write(`${JSON.stringify({ result: 'PASS_R017_MATERIALIZER_SOURCE', provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_records_emitted: false })}\n`);
    return;
  }
  if (!args['--input'] || !args['--output'] || !args['--mazer-repository']) throw new Error('USAGE');
  const result = materialize(
    JSON.parse(fs.readFileSync(path.resolve(args['--input']), 'utf8')),
    path.resolve(args['--output']),
    path.resolve(args['--mazer-repository'])
  );
  process.stdout.write(`${JSON.stringify({ result: 'PRIVATE_R017_PACKET_SEALED', manifest_sha256: result.manifestSha256, files: result.manifest.files.length + 1, private_values_emitted: false })}\n`);
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main().catch((error) => { process.stdout.write(`${JSON.stringify({ result: 'HOLD_R017_MATERIALIZER', category: String(error.message).replace(/[^A-Za-z0-9_:.-]/g, '').slice(0, 120), private_values_emitted: false })}\n`); process.exitCode = 2; });
