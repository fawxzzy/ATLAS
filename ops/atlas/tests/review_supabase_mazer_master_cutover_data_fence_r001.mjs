import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import {
  CONTRACT,
  renderAclObservationSql,
  renderFenceSql,
  renderLockBarrierSql,
  renderRestoreSql,
  renderSignupAdmissionFenceSql,
  renderSignupAdmissionObservationSql,
  renderSignupAdmissionRestoreSql,
  renderWriterCaptureSql,
  renderWriterDrainSql,
  sha256
} from '../classify_supabase_mazer_master_cutover_data_fence_r001.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const hostPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_cutover_data_fence_r001.ps1');
const classifierPath = path.join(root, 'ops/atlas/classify_supabase_mazer_master_cutover_data_fence_r001.mjs');
const testPath = path.join(root, 'ops/atlas/tests/test_supabase_mazer_master_cutover_data_fence_r001.mjs');
const reviewPath = fileURLToPath(import.meta.url);
const host = fs.readFileSync(hostPath, 'utf8');
const classifier = fs.readFileSync(classifierPath, 'utf8');
const focused = fs.readFileSync(testPath, 'utf8');
const review = fs.readFileSync(reviewPath, 'utf8');
const findings = [];

function requireText(source, value, category) {
  if (!source.includes(value)) findings.push(category);
}

function requireOrder(source, needles, category) {
  let cursor = -1;
  for (const needle of needles) {
    const next = source.indexOf(needle, cursor + 1);
    if (next < 0 || next <= cursor) {
      findings.push(category);
      return;
    }
    cursor = next;
  }
}

function run(command, args) {
  const child = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    windowsHide: true,
    timeout: 120_000,
    env: { ...process.env }
  });
  if (child.error || child.status !== 0 || child.signal) {
    findings.push(`CHILD_FAILED:${path.basename(command)}`);
    return null;
  }
  if (child.stderr.trim() !== '') findings.push(`CHILD_STDERR:${path.basename(command)}`);
  return child.stdout.trim();
}

function reviewAclPreimage(schema) {
  return {
    schema,
    table_acl: [...CONTRACT.tables].sort().map((name) => ({
      name,
      grants: name === 'mazer_profiles'
        ? [
            { grantee: 'authenticated', privilege: 'INSERT', is_grantable: false },
            { grantee: 'authenticated', privilege: 'UPDATE', is_grantable: false }
          ]
        : name === 'mazer_cycle_receipts'
          ? [{ grantee: 'anon', privilege: 'DELETE', is_grantable: true }]
          : []
    })),
    rpc_acl: [...CONTRACT.mutatingRpcs].sort().map((signature) => ({
      signature,
      grants: [{ grantee: 'authenticated', is_grantable: false }]
    })),
    catalog: {
      tables: [...CONTRACT.tables].sort().map((name) => ({ name, relkind: 'r', rls_enabled: true, force_rls: false })),
      rpcs: [...CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, kind: 'f', security_definer: true, volatility: 'v' }))
    }
  };
}

assert.equal(CONTRACT.legacy.projectRef, 'geknvnrmktchljnyddwp');
assert.equal(CONTRACT.legacy.schema, 'public');
assert.equal(CONTRACT.master.projectRef, 'bxtcuhkotumitoqtrcej');
assert.equal(CONTRACT.master.schema, 'mazer');
assert.deepEqual(CONTRACT.tables, [
  'mazer_profiles',
  'mazer_progression_states',
  'mazer_ai_progression_states',
  'mazer_cycle_receipts'
]);

for (const source of [host, classifier]) {
  requireText(source, CONTRACT.legacy.projectRef, 'LEGACY_PROJECT_BINDING_MISSING');
  requireText(source, CONTRACT.master.projectRef, 'MASTER_PROJECT_BINDING_MISSING');
}
for (const table of CONTRACT.tables) {
  requireText(host, table, `HOST_TABLE_MISSING:${table}`);
  requireText(classifier, table, `CLASSIFIER_TABLE_MISSING:${table}`);
}
for (const rpc of CONTRACT.mutatingRpcs) {
  requireText(host, rpc, `HOST_RPC_MISSING:${rpc}`);
  requireText(classifier, rpc, `CLASSIFIER_RPC_MISSING:${rpc}`);
}

for (const value of [
  'IDENTITY_MAP_DIGEST_DRIFT',
  'APP_CONTRACT_DIGEST_DRIFT',
  'SOURCE_HIGH_WATER_DRIFT',
  'AMBIGUOUS_IDENTITY',
  'PARTIAL_WRITER_FENCE',
  'PARTIAL_WRITER_REVOKE',
  'POST_FENCE_LATE_WRITE',
  'TWO_ZERO_DELTA_READS_REQUIRED',
  'RECEIPT_ID_CONFLICT',
  'RECEIPT_CLIENT_RUN_CONFLICT',
  'normalizeSnapshot(input.baseline_source_snapshot)',
  'RECEIPT_HISTORY_CONFLICT',
  "if (!mappedUser) hold('AMBIGUOUS_IDENTITY')",
  'PASS_EXACT_REPLAY_NOOP',
  'pg_advisory_xact_lock',
  'pg_catalog.decode',
  'TARGET_PREIMAGE_DRIFT',
  'TARGET_POSTIMAGE_DRIFT',
  'is distinct from',
  'left join ${expectedName}',
  'where exists (select 1 from ${expectedName} guard',
  'SOURCE_AUTH_HIGH_WATER_DRIFT',
  'SOURCE_HIGH_WATER_DRIFT:',
  'PASS_SOURCE_HIGH_WATER',
  'begin transaction isolation level repeatable read',
  '_PAYLOAD_DIGEST_MISMATCH',
  'RECEIPT_MAPPED_PAYLOAD_DIGEST_MISMATCH',
  'ACL_PREIMAGE_DIGEST_DRIFT',
  'FENCE_CATALOG_DIGEST_DRIFT',
  'PASS_ACL_PREIMAGE_MATCH',
  'HOLD_ACL_PREIMAGE_DRIFT',
  'acl_observation_binding_digest',
  'renderAclObservationSql',
  'BigInt(left.level)',
  'MAX_PG_BIGINT',
  'PLAYER_RAW_STATE_PROJECTION_CONFLICT',
  'AI_RAW_STATE_PROJECTION_CONFLICT',
  'FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT',
  'LEGACY_DEDICATED_AUTH_SET_EXACT',
  'MASTER_MAZER_NAMESPACE_OR_PROFILE_OWNERSHIP',
  'atlas_observed_auth except select * from atlas_expected_auth',
  'atlas_expected_auth except select * from atlas_observed_auth',
  'PASS_ACL_PREIMAGE_ALREADY_PRESENT',
  'PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED',
  'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS',
  'JOURNALED_ACL_PACKET_DRIFT',
  'PASS_WRITER_REVOKE_COMMITTED',
  'PASS_WRITER_SET_CAPTURE',
  'PASS_WRITER_SET_CAPTURE_BOUND',
  'WAIT_CAPTURED_WRITERS',
  'PASS_CAPTURED_WRITERS_DRAINED',
  'CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED',
  'PASS_WRITER_LOCK_BARRIER',
  'pg_catalog.pg_stat_activity',
  'a.pid, a.backend_start, a.xact_start, a.query_start',
  'LOCK_BARRIER_POST_ACL_OR_CATALOG_DRIFT',
  'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT',
  'PASS_SIGNUP_ADMISSION_FENCED',
  'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED',
  'MAZER_SIGNUP_TEMPORARILY_UNAVAILABLE',
  'AUTH_USERS_WRITER_BARRIER_INCOMPLETE',
  'HOLD_SIGNUP_ADMISSION_STATE_AMBIGUOUS'
]) requireText(classifier, value, `CLASSIFIER_CONTRACT_MISSING:${value}`);

for (const value of [
  '/v1/projects/$ProjectRef/config/auth',
  'disable_signup',
  'hook_before_user_created_enabled',
  'TRANSACTION_POOLER_NOT_ALLOWED',
  'DATABASE_PORT_BINDING',
  'pooler\\.supabase\\.com',
  'db.$ExpectedProjectRef.supabase.co',
  'PGDATABASE',
  'ExpectedInputSha256',
  'INPUT_FILE_DIGEST_DRIFT',
  'STATE_INPUT_FILE_DIGEST_DRIFT',
  'LOCAL_PATH_REPARSE_POINT',
  'INPUT_FILE_COPY_DIGEST_DRIFT',
  'STATE_IDENTITY_MAP_DIGEST_DRIFT',
  'STATE_APP_CONTRACT_DIGEST_DRIFT',
  'STATE_HIGH_WATER_DIGEST_DRIFT',
  'FORWARD_DELTA_APPLYING',
  'REVERSE_DELTA_APPLYING',
  'DELTA_QUARANTINED_PREIMAGE_RESTORED',
  'LEGACY_SIGNUP_FENCING',
  'MASTER_HOOK_DISABLING',
  'MASTER_SIGNUP_PREOBSERVING',
  'MASTER_SIGNUP_PREOBSERVED',
  'MASTER_SIGNUP_FENCING',
  'MASTER_SIGNUP_FENCED',
  'MASTER_HOOK_RESTORING',
  'MASTER_HOOK_RESTORED',
  'MASTER_SIGNUP_RESTORING',
  'LEGACY_WRITERS_RESTORING',
  'LegacyFenceSql',
  'AclObservationSql',
  'LegacyAclObservationSql',
  'ObservedRestoreSql',
  'ObservedFenceSql',
  'Invoke-AclVerifier',
  'Invoke-AclRecoveryClassifier',
  'Invoke-ExactAclRecovery',
  'LEGACY_WRITERS_PREOBSERVING',
  'LEGACY_WRITERS_PREOBSERVED',
  'LEGACY_WRITERS_FENCING',
  'MASTER_WRITERS_PREOBSERVING',
  'MASTER_WRITERS_PREOBSERVED',
  'MASTER_WRITERS_FENCING',
  'LEGACY_WRITER_REVOKE_COMMITTED',
  'LEGACY_WRITER_SET_CAPTURED',
  'LEGACY_WRITERS_DRAINING',
  'LEGACY_WRITERS_DRAINED',
  'LEGACY_LOCK_BARRIER_ACQUIRING',
  'MASTER_WRITER_REVOKE_COMMITTED',
  'MASTER_WRITER_SET_CAPTURED',
  'MASTER_WRITERS_DRAINING',
  'MASTER_WRITERS_DRAINED',
  'MASTER_LOCK_BARRIER_ACQUIRING',
  'Invoke-WriterCaptureVerifier',
  'Invoke-ExactWriterDrainBarrier',
  'Read-WriterDrainReceipt',
  '[Diagnostics.Stopwatch]::StartNew()',
  'CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED',
  'LEGACY_ACL_REVOKED_WRITER_DRAIN_INCOMPLETE_HOLD_FENCED',
  'MASTER_ACL_REVOKED_WRITER_DRAIN_INCOMPLETE_HOLD_FENCED',
  'STATE_PRIMARY_ACL_DIGEST_DRIFT',
  'STATE_PRIMARY_CATALOG_DIGEST_DRIFT',
  'journaled_primary_acl_preimage',
  'journaled_primary_acl_binding_digest',
  'ROLLBACK_ACL_PREIMAGE_MISSING',
  'SourceObservationSql',
  'Invoke-PsqlObservation',
  'REVERSE_ACTIVATION_FAILED_BOTH_SIDES_FENCED_DELTA_QUARANTINED'
]) requireText(host, value, `HOST_CONTRACT_MISSING:${value}`);

requireOrder(host, [
  "Set-StatePhase $state 'LEGACY_SIGNUP_FENCING'",
  "@{ disable_signup = $true }",
  "Set-StatePhase $state 'LEGACY_WRITERS_PREOBSERVING'",
  'Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.AclObservationSql',
  '$state.journaled_primary_acl_preimage',
  "Set-StatePhase $state 'LEGACY_WRITERS_PREOBSERVED'",
  "Set-StatePhase $state 'LEGACY_WRITERS_FENCING'",
  'Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.ObservedFenceSql',
  "Set-StatePhase $state 'LEGACY_WRITER_REVOKE_COMMITTED'",
  'Invoke-ExactWriterDrainBarrier $legacyDatabaseUrl',
  'Invoke-PsqlObservation $legacyDatabaseUrl $classification.SourceObservationSql',
  "Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_1'",
  'Invoke-PsqlObservation $legacyDatabaseUrl $classification.SourceObservationSql',
  "Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_2'",
  "Set-StatePhase $state 'FORWARD_DELTA_APPLYING'",
  'Invoke-PsqlPrivate $masterDatabaseUrl $classification.TransactionSql'
], 'FORWARD_FENCE_ORDER_DRIFT');
requireOrder(host, [
  "Set-StatePhase $state 'MASTER_HOOK_DISABLING'",
  '@{ hook_before_user_created_enabled = $false }',
  "Set-StatePhase $state 'MASTER_SIGNUP_PREOBSERVING'",
  'Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionObservationSql',
  "Set-StatePhase $state 'MASTER_SIGNUP_PREOBSERVED'",
  "Set-StatePhase $state 'MASTER_SIGNUP_FENCING'",
  'Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionFenceSql',
  "Set-StatePhase $state 'MASTER_SIGNUP_FENCED'",
  "Set-StatePhase $state 'MASTER_WRITERS_PREOBSERVING'",
  'Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.AclObservationSql',
  '$state.journaled_primary_acl_preimage',
  "Set-StatePhase $state 'MASTER_WRITERS_PREOBSERVED'",
  "Set-StatePhase $state 'MASTER_WRITERS_FENCING'",
  'Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.ObservedFenceSql',
  "Set-StatePhase $state 'MASTER_WRITER_REVOKE_COMMITTED'",
  'Invoke-ExactWriterDrainBarrier $masterDatabaseUrl',
  'Invoke-PsqlObservation $masterDatabaseUrl $classification.SourceObservationSql',
  "Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_1'",
  'Invoke-PsqlObservation $masterDatabaseUrl $classification.SourceObservationSql',
  "Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_2'",
  "Set-StatePhase $state 'REVERSE_DELTA_APPLYING'",
  'Invoke-PsqlPrivate $legacyDatabaseUrl $classification.TransactionSql',
  'Invoke-PsqlPrivate $legacyDatabaseUrl $classification.LegacyRestoreSql',
  'Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.LegacyAclObservationSql',
  '@{ disable_signup = $false }'
], 'DISABLE_HOOK_FIRST_REVERSE_ORDER_DRIFT');

requireOrder(host, [
  "Set-StatePhase $state 'MASTER_HOOK_RESTORING'",
  '@{ hook_before_user_created_enabled = [bool]$state.master_hook_enabled_preimage }',
  "Set-StatePhase $state 'MASTER_HOOK_RESTORED'",
  "Set-StatePhase $state 'MASTER_SIGNUP_RESTORING'",
  'Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionRestoreSql'
], 'OVERLAPPED_SIGNUP_ROLLBACK_ORDER_DRIFT');

const drainHelper = host.slice(
  host.indexOf('function Invoke-ExactWriterDrainBarrier'),
  host.indexOf('function Invoke-ExactAclRecovery')
);
requireOrder(drainHelper, [
  "'_WRITER_SET_CAPTURING'",
  'Invoke-PsqlJsonPrivate $DatabaseUrl $WriterCaptureSql',
  'journaled_primary_writer_capture',
  "'_WRITER_SET_CAPTURED'",
  "'_WRITERS_DRAINING'",
  'Read-WriterDrainReceipt',
  'CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED',
  "'_WRITERS_DRAINED'",
  "'_LOCK_BARRIER_ACQUIRING'",
  'Invoke-PsqlJsonPrivate $DatabaseUrl $lockBarrierSql',
  "'_WRITERS_FENCED'"
], 'EXACT_WRITER_DRAIN_PHASE_ORDER_DRIFT');

const transactionRenderer = classifier.slice(
  classifier.indexOf('export function renderTransactionalSql'),
  classifier.indexOf('export function renderSignupAdmissionObservationSql')
).toLowerCase();
for (const forbidden of ['delete from', 'truncate ', 'drop table']) {
  if (transactionRenderer.includes(forbidden)) findings.push(`DESTRUCTIVE_DELTA_SQL:${forbidden}`);
}

const signupObservation = renderSignupAdmissionObservationSql();
const signupFence = renderSignupAdmissionFenceSql();
const signupRestore = renderSignupAdmissionRestoreSql();
requireText(signupObservation, 'mazer_claim_signup_username_after_insert', 'M3_SIGNUP_CLAIM_BINDING_MISSING');
requireText(signupObservation, 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT', 'SIGNUP_PREIMAGE_OBSERVATION_MISSING');
requireText(signupObservation, 'HOLD_SIGNUP_ADMISSION_STATE_AMBIGUOUS', 'SIGNUP_AMBIGUOUS_HOLD_MISSING');
requireText(signupFence, "->> 'app_namespace' = 'mazer'", 'MAZER_SIGNUP_ROUTING_FENCE_MISSING');
requireText(signupFence, 'MAZER_SIGNUP_TEMPORARILY_UNAVAILABLE', 'MAZER_SIGNUP_REJECTION_MISSING');
requireText(signupFence, 'security invoker', 'SIGNUP_FENCE_INVOKER_MISSING');
if (signupFence.includes('security definer')) findings.push('SIGNUP_FENCE_SECURITY_DEFINER');
requireText(signupFence, 'pg_catalog.pg_locks', 'AUTH_WRITER_CAPTURE_MISSING');
requireText(signupFence, 'ADMITTED_SIGNUP_WRITER_NOT_DRAINED', 'ADMITTED_SIGNUP_DRAIN_MISSING');
requireText(signupFence, 'lock table auth.users in share row exclusive mode', 'AUTH_USERS_BARRIER_MISSING');
requireOrder(signupFence, ['atlas_admitted_signup_writers', 'lock table auth.users', 'create function', 'create trigger', 'PASS_SIGNUP_ADMISSION_FENCED', 'commit;'], 'SIGNUP_ADMISSION_BARRIER_ORDER_DRIFT');
requireText(signupRestore, 'SIGNUP_ADMISSION_RESTORE_STATE_AMBIGUOUS', 'SIGNUP_RESTORE_AMBIGUOUS_HOLD_MISSING');
requireText(signupFence, 'atlas:mazer-signup-admission-fence:mazer', 'SIGNUP_INSTALL_SERIALIZER_MISSING');
requireText(signupRestore, 'atlas:mazer-signup-admission-fence:mazer', 'SIGNUP_RESTORE_SERIALIZER_MISSING');
const signupFenceAdvisory = signupFence.match(/hashtextextended\('([^']+)'/)?.[1];
const signupRestoreAdvisory = signupRestore.match(/hashtextextended\('([^']+)'/)?.[1];
if (!signupFenceAdvisory || signupFenceAdvisory !== signupRestoreAdvisory) findings.push('SIGNUP_INSTALL_RESTORE_SERIALIZER_DRIFT');
requireOrder(signupRestore, ['pg_advisory_xact_lock', 'lock table auth.users', 'atlas_signup_current', 'SIGNUP_ADMISSION_RESTORE_STATE_AMBIGUOUS', 'drop trigger', 'drop function', 'commit;', 'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED'], 'SIGNUP_RESTORE_BARRIER_ORDER_DRIFT');
requireText(focused, 'ORPHAN_INSTALL_BLOCKER_READY', 'ORPHAN_INSTALL_RESTORE_REGRESSION_MISSING');
requireText(focused, "wait_event = 'advisory'", 'ORPHAN_INSTALL_SERIALIZER_PROOF_MISSING');
const legacyFence = renderFenceSql('public', reviewAclPreimage('public'));
const masterFence = renderFenceSql('mazer', reviewAclPreimage('mazer'));
for (const sql of [legacyFence, masterFence]) {
  const schema = sql === legacyFence ? 'public' : 'mazer';
  for (const table of CONTRACT.tables) requireText(sql, `revoke insert, update, delete on table "${schema}"."${table}"`, `TABLE_FENCE_MISSING:${table}`);
  for (const rpc of CONTRACT.mutatingRpcs) requireText(sql, `revoke execute on function "${schema}".${rpc}`, `RPC_FENCE_MISSING:${rpc}`);
  requireText(sql, 'begin;', 'FENCE_TRANSACTION_MISSING');
  requireText(sql, 'commit;', 'FENCE_COMMIT_MISSING');
  requireOrder(sql, ['FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT', 'revoke insert, update, delete', 'PARTIAL_WRITER_REVOKE', 'commit;', 'PASS_WRITER_REVOKE_COMMITTED'], 'REVOKE_COMMIT_VISIBILITY_ORDER_DRIFT');
  if (sql.includes('lock table')) findings.push('LOCK_BEFORE_REVOKE_COMMIT_RACE_RETAINED');

  const writers = [{ pid: 4101, backend_start: '2026-08-24T19:01:00.000Z', xact_start: '2026-08-24T19:02:00.000Z', query_start: '2026-08-24T19:03:00.000Z' }];
  const writerDigest = sha256(writers);
  const capture = renderWriterCaptureSql(schema, reviewAclPreimage(schema));
  const drain = renderWriterDrainSql(schema, writers, writerDigest);
  const barrier = renderLockBarrierSql(schema, reviewAclPreimage(schema), writers, writerDigest);
  requireText(capture, 'pg_catalog.pg_stat_activity', 'POST_COMMIT_WRITER_CAPTURE_MISSING');
  requireText(capture, 'a.pid, a.backend_start, a.xact_start, a.query_start', 'EXACT_WRITER_IDENTITY_MISSING');
  requireText(capture, 'mazer_complete_level(', 'OLD_ACL_RPC_SCOPE_MISSING');
  requireText(capture, `insertinto"${schema}"."mazer_profiles"`, 'DIRECT_DML_SCOPE_MISSING');
  requireText(drain, 'WAIT_CAPTURED_WRITERS', 'EXACT_WRITER_WAIT_MISSING');
  requireText(drain, 'PASS_CAPTURED_WRITERS_DRAINED', 'EXACT_WRITER_DRAIN_PASS_MISSING');
  requireText(drain, 'CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED', 'DRAIN_TIMEOUT_FENCED_HOLD_MISSING');
  requireOrder(barrier, ['CAPTURED_WRITER_REAPPEARED', 'lock table', 'LOCK_BARRIER_POST_ACL_OR_CATALOG_DRIFT', 'PASS_WRITER_LOCK_BARRIER', 'commit;'], 'LOCK_BARRIER_ORDER_DRIFT');
  for (const table of [...CONTRACT.tables].sort()) requireText(barrier, `lock table "${schema}"."${table}" in share row exclusive mode`, `ORDERED_TABLE_BARRIER_MISSING:${table}`);
}
for (const schema of ['public', 'mazer']) {
  const sql = renderRestoreSql(schema, reviewAclPreimage(schema));
  requireText(sql, 'grant INSERT, UPDATE on table', 'PROFILE_WRITER_RESTORE_MISSING');
  requireText(sql, 'grant execute on function', 'RPC_WRITER_RESTORE_MISSING');
  requireText(sql, `grant DELETE on table "${schema}"."mazer_cycle_receipts" to "anon" with grant option`, 'CAPTURED_GRANT_OPTION_RESTORE_MISSING');
  if (/grant\s+(?:insert|update|delete)[^;]+mazer_(?:progression_states|ai_progression_states)/i.test(sql)) findings.push('UNCAPTURED_DIRECT_DURABLE_WRITER_RESTORED');
  requireText(renderAclObservationSql(schema), 'pg_catalog.aclexplode', 'CANONICAL_ACL_OBSERVATION_MISSING');
}

for (const forbidden of [
  'Invoke-Expression',
  'git push',
  'supabase db push',
  'vercel deploy',
  'vercel promote',
  'Start-Sleep',
  'for (;;'
]) {
  if (host.includes(forbidden) || classifier.includes(forbidden) || focused.includes(forbidden)) findings.push(`FORBIDDEN_ACTION:${forbidden}`);
}
requireText(host, "Remove-Item -LiteralPath $resolvedPrivate -Recurse -Force", 'PRIVATE_PACKET_CLEANUP_MISSING');
requireText(host, 'raw_identifiers_emitted = $false', 'SAFE_OUTPUT_IDENTIFIER_FLAG_MISSING');
requireText(host, 'secrets_emitted = $false', 'SAFE_OUTPUT_SECRET_FLAG_MISSING');
requireText(classifier, "mode: 0o600, flag: 'wx'", 'PRIVATE_FILE_EXCLUSIVE_CREATE_MISSING');

const focusedOne = run(process.execPath, [testPath]);
const focusedTwo = run(process.execPath, [testPath]);
if (focusedOne !== focusedTwo) findings.push('FOCUSED_TEST_NONDETERMINISTIC');
if (focusedOne) {
  const value = JSON.parse(focusedOne);
  assert.equal(value.result, 'PASS_MAZER_MASTER_CUTOVER_DATA_FENCE_R001');
  assert.equal(value.scenarios, 88);
  assert.equal(value.postgresql17_concurrency, 'SKIPPED_EXPLICIT_OPT_IN_REQUIRED');
  assert.equal(value.provider_calls, 0);
  assert.equal(value.live_data_writes, 0);
}

const sourceArgs = ['-NoLogo', '-NoProfile', '-NonInteractive', '-File', hostPath, '-SourceOnlyValidate'];
const shellRuns = process.platform === 'win32'
  ? [
      ['pwsh.exe', sourceArgs],
      ['pwsh.exe', sourceArgs],
      ['powershell.exe', ['-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', hostPath, '-SourceOnlyValidate']],
      ['powershell.exe', ['-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', hostPath, '-SourceOnlyValidate']]
    ]
  : [['pwsh', sourceArgs], ['pwsh', sourceArgs]];
const shellOutputs = shellRuns.map(([command, args]) => run(command, args));
for (let index = 0; index < shellOutputs.length; index += 2) {
  if (shellOutputs[index] !== shellOutputs[index + 1]) findings.push(`SOURCE_VALIDATION_NONDETERMINISTIC:${index / 2}`);
}
for (const output of shellOutputs.filter(Boolean)) {
  const value = JSON.parse(output);
  assert.equal(value.result, 'PASS_MAZER_MASTER_CUTOVER_DATA_FENCE_SOURCE');
  assert.equal(value.credential_reads, 0);
  assert.equal(value.provider_writes, 0);
  assert.equal(value.live_data_writes, 0);
  assert.equal(value.state_writes, 0);
  assert.equal(value.private_files, 0);
}

assert.deepEqual(findings, []);
console.log(JSON.stringify({
  result: 'PASS_MAZER_MASTER_CUTOVER_DATA_FENCE_R001_REVIEW_NO_FINDINGS',
  assertions: 266,
  focused_runs: 2,
  source_validation_runs: shellRuns.length,
  findings: 0,
  provider_calls: 0,
  provider_writes: 0,
  auth_writes: 0,
  live_data_writes: 0,
  deployments: 0
}));
