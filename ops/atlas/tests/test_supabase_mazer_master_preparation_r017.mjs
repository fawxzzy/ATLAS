import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { CONTRACT, HOST_PHASES, SQL_BYTE_LIMITS, assertSql, classifyHostRecovery } from '../materialize_supabase_mazer_master_preparation_r017.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const hostPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_r017.ps1');
const materializerPath = path.join(root, 'ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs');
const fenceHostPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_cutover_data_fence_r001.ps1');
const fenceClassifierPath = path.join(root, 'ops/atlas/classify_supabase_mazer_master_cutover_data_fence_r001.mjs');
const host = fs.readFileSync(hostPath, 'utf8');
const materializer = fs.readFileSync(materializerPath, 'utf8');
const fenceHost = fs.readFileSync(fenceHostPath, 'utf8');
const fenceClassifier = fs.readFileSync(fenceClassifierPath, 'utf8');
const state = (phase) => ({ schema: 'atlas.supabase.mazer-master-preparation-host-state.r017.v1', phase });
const adversarialCoverage = ['all live phase interruption','ambiguous drift','disable hook before SQL/fence','receipt conservation','Auth mapping','RLS/ACL/Data API','executor input hash binding'];
assert.equal(adversarialCoverage.length, 7);

assert.equal(classifyHostRecovery(null).action, 'START');
assert.deepEqual(classifyHostRecovery(state('PREPARATION_COMPLETE')), { action: 'NOOP', effect: 'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER' });
assert.deepEqual(classifyHostRecovery(state('ROLLED_BACK')), { action: 'REPLAY_REQUIRES_EXPLICIT_SWITCH', effect: 'TERMINAL_ROLLBACK' });
assert.deepEqual(classifyHostRecovery(state('ROLLED_BACK'), { replayExactRolledBack: true }), { action: 'START_EXACT_REPLAY', effect: 'ROLLED_BACK_PREIMAGE' });
for (const phase of HOST_PHASES) {
  const result = classifyHostRecovery(state(phase));
  assert.ok(['NOOP', 'RESUME_EXACT', 'ROLLBACK_REQUIRED', 'REPLAY_REQUIRES_EXPLICIT_SWITCH'].includes(result.action), `unclassified phase ${phase}`);
  if (phase.endsWith('_APPLYING') || phase.endsWith('_ACTIVATING') || phase.endsWith('_CLEANING') || phase.endsWith('VERIFYING') || phase.startsWith('ROLLBACK_') || phase === 'AMBIGUOUS_HOLD') assert.equal(result.action, 'ROLLBACK_REQUIRED', phase);
}
assert.throws(() => classifyHostRecovery(state('UNKNOWN')), /STATE_PHASE_DRIFT/);
assert.throws(() => classifyHostRecovery({ schema: 'wrong', phase: 'PREFLIGHT' }), /STATE_SCHEMA_DRIFT/);

const sqlTokens = {
  'preflight.sql': ['data_api','rls','acl','auth.users','114','11','15','1882','mazer_username_handle_key'],
  'master-fence.sql': ['begin;','mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts','revoke'],
  'master-refence.sql': ['begin;','mazer_initialize_progression','mazer_complete_level','mazer_complete_ai_level','mazer_reset_progression','revoke'],
  'auth-apply.sql': ['begin;','auth.users','auth.identities','create_and_bind','bind_existing','3_auth_imports','13_existing_binds'],
  'reset-era-apply.sql': ['begin;','whole_row_override','7/6/32/d','39/108/161/s','pgp_sym_encrypt','player_reset_disposition','vault.create_secret','rollback_bound_username_key'],
  'postverify.sql': ['begin;','data_api','rls','acl','117','18','11','15','1882','receipt_conservation','username_origin','mazer-'],
  'qa-apply.sql': ['begin;','qa_ttl','before_user_created','rollback_on_error'],
  'qa-cleanup.sql': ['begin;','qa_ttl','delete','auth.identities','auth.users'],
  'rollback.sql': ['begin;','disable_hook_first','master_preimage','receipt_conservation']
};
for (const name of CONTRACT.sqlNames) {
  const valid = `begin;\n${sqlTokens[name].join('\n')}\ncommit;`;
  assert.doesNotThrow(() => assertSql(name, valid));
  assert.throws(() => assertSql(name, 'begin; select 1; select 2; commit;'), /SQL_CONTRACT_TOKEN_MISSING/);
}
assert.throws(() => assertSql('master-fence.sql', 'begin; mazer_profiles mazer_progression_states mazer_ai_progression_states mazer_cycle_receipts revoke; vercel; commit;'), /SQL_SCOPE_DRIFT/);
assert.deepEqual(SQL_BYTE_LIMITS, { default: 2_000_000, 'postverify.sql': 8_000_000, 'rollback.sql': 8_000_000 });
const largePostverify = `begin;\n${sqlTokens['postverify.sql'].join('\n')}\n${'x'.repeat(2_100_000)}\ncommit;`;
assert.doesNotThrow(() => assertSql('postverify.sql', largePostverify));
const largeOrdinary = `begin;\n${sqlTokens['master-fence.sql'].join('\n')}\n${'x'.repeat(2_100_000)}\ncommit;`;
assert.throws(() => assertSql('master-fence.sql', largeOrdinary), /SQL_SHAPE/);

function requireOrder(source, values) {
  let offset = -1;
  for (const value of values) {
    const next = source.indexOf(value, offset + 1);
    assert.ok(next > offset, `order missing ${value}`);
    offset = next;
  }
}

requireOrder(host, [
  "Invoke-Fence 'FenceOnly'", "'master-fence.sql'", "'m1.sql'", "'m2.sql'", "'master-refence.sql'",
  "'auth-apply.sql'", "'reset-era-apply.sql'", "Invoke-Fence 'Continue'", "'m3.sql'", "'m4.sql'", "'postverify.sql'",
  "'HOOK_ACTIVATING'", "'qa-apply.sql'", "'qa-cleanup.sql'", "Invoke-Fence 'ReleaseLegacy'", "'PREPARATION_COMPLETE'"
]);
const hostPhaseMatch = host.match(/\$Phases = @\(([\s\S]*?)\n\)/);
assert.ok(hostPhaseMatch, 'PowerShell phase list missing');
const hostPhases = [...hostPhaseMatch[1].matchAll(/'([A-Z0-9_]+)'/g)].map((match) => match[1]);
assert.deepEqual(hostPhases, HOST_PHASES, 'PowerShell and JS phase lists drifted');
const rollbackBlock = host.slice(host.indexOf("if ($Mode -ceq 'Rollback')"), host.indexOf('$stateJson'));
requireOrder(rollbackBlock, ['ROLLBACK_DISABLING_HOOK', 'hook_before_user_created_enabled = $false', 'qa-cleanup.sql', 'rollback.sql', 'ROLLBACK_LEGACY_RESTORING']);
const normalTail = host.slice(host.indexOf("Set-Phase $state 'HOOK_ACTIVATING'"), host.lastIndexOf('\ncatch {'));
assert.ok(!normalTail.includes('hook_before_user_created_enabled = $false'), 'normal path disabled master hook');
assert.ok(normalTail.includes('master_hook_enabled = $true'));

for (const token of [
  'RollbackDeadlineSeconds = 600','HardFenceLeaseSeconds = 900','Start-RollbackWatchdog','-WindowStyle Hidden',
  'rollback_initiated_at','Assert-Lease','ExpectedPrivateSourceSha256','PRIVATE_SOURCE_DIGEST_DRIFT','private_manifest_sha256',
  'fence_input_sha256','MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER','fresh_dual_refence_and_catchup_required_for_cutover',
  '18','117','1882','7/6/32/D','PGP_SYM_ENCRYPT_AES256','MASTER_DOMINATES_NO_OVERRIDE','PLAYER_RESET_DOMINANCE_DRIFT',
  'Mazer-######','SUPABASE_VAULT','bounded_delta_catchups',
  'currentPreimageSha256','restoreProofSha256','predecessorFenceManifestSha256'
]) assert.ok(host.includes(token) || materializer.includes(token), `missing ${token}`);
assert.ok(host.includes('AUTH_TOPOLOGY_MANIFEST_DRIFT'));
for (const token of ['ReplayExactRolledBack','PASS_EXACT_ROLLBACK_TERMINAL','replay_requires_explicit_switch','fence.replay-','START_EXACT_REPLAY']) assert.ok(host.includes(token) || materializer.includes(token), `rollback replay seam missing ${token}`);
const replayReset = host.slice(host.indexOf("if ([string]$state.phase -ceq 'ROLLED_BACK')"), host.indexOf('$managementToken = Read-ManagementToken'));
requireOrder(replayReset, ['ReplayExactRolledBack', "phase = 'PREFLIGHT'", 'Write-State', 'fence.replay-']);
const producer = fs.readFileSync(path.join(root, 'ops/atlas/produce_supabase_mazer_master_preparation_private_source_r017.mjs'), 'utf8');
for (const token of ["crypto.createHmac('sha256'", "vault.create_secret", "delete from vault.secrets where name='mazer_username_handle_key'"]) assert.ok(producer.includes(token), `deterministic replay contract missing ${token}`);
assert.ok(host.includes('auth_counts.binds -ne 13'));
assert.ok(host.includes('auth_counts.retained_edges -ne 2'));
assert.ok(materializer.includes('topologyEvidenceSha256'));

assert.ok(host.includes('Find-MazerRepository'));
assert.ok(host.includes("'--mazer-repository',$mazerRepository"));
assert.ok(host.includes('import(process.argv[1])'));
assert.ok(host.includes('([Uri]$Materializer).AbsoluteUri'));
assert.ok(!host.includes("import('./ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs')"));
assert.ok(host.includes('[string]$enabled.hook_before_user_created_uri -cne $ExpectedHookUri'));
assert.ok(materializer.includes("args['--mazer-repository']"));
assert.ok(!materializer.includes("path.join(root, 'repos', 'mazer')"));

for (const token of ['ExecutionStep', 'FenceOnly', 'Continue', 'ReleaseLegacy', 'PAUSED_AFTER_SOURCE_HIGH_WATER', 'CONTINUE_ACL_NOT_EXACT_FENCED_POSTIMAGE', 'INPUT_FILE_DIGEST_DRIFT', 'STATE_INPUT_FILE_DIGEST_DRIFT']) assert.ok(fenceHost.includes(token), `fence seam missing ${token}`);
for (const token of ['CONTINUE_OR_ROLLBACK', 'RELEASE_LEGACY_REQUIRED', 'PREPARATION_COMPLETE']) assert.ok(fenceClassifier.includes(token), `classifier seam missing ${token}`);
for (const forbidden of ['vercel deploy', 'vercel promote', 'git push', 'supabase db push']) assert.ok(!host.toLowerCase().includes(forbidden) && !materializer.toLowerCase().includes(forbidden));

function sourceRun(command, args) {
  const child = spawnSync(command, args, { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 180_000 });
  assert.equal(child.status, 0, child.stderr);
  const result = JSON.parse(child.stdout.trim());
  assert.equal(result.result, 'PASS_MAZER_MASTER_PREPARATION_R017_SOURCE');
  assert.equal(result.provider_writes, 0);
  assert.equal(result.live_data_writes, 0);
}
if (process.platform === 'win32') {
  sourceRun('pwsh.exe', ['-NoLogo','-NoProfile','-NonInteractive','-File',hostPath,'-SourceOnlyValidate']);
  sourceRun('powershell.exe', ['-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',hostPath,'-SourceOnlyValidate']);
}

console.log(JSON.stringify({ result: 'PASS_MAZER_MASTER_PREPARATION_R017', phases: HOST_PHASES.length, sql_contracts: CONTRACT.sqlNames.length, pg17_concurrency: 'COVERED_BY_INHERITED_FENCE_SUITE_EXPLICIT_OPT_IN', provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, deployments: 0 }));
