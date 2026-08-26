import assert from 'node:assert/strict';
import crypto from 'node:crypto';
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
const localFenceProbePath = path.join(root, 'ops/atlas/probe_supabase_mazer_master_fence_production_shape_local_r017.mjs');
const localFenceProbe = fs.readFileSync(localFenceProbePath, 'utf8');
const fenceClassifier = fs.readFileSync(fenceClassifierPath, 'utf8');
const state = (phase) => ({ schema: 'atlas.supabase.mazer-master-preparation-host-state.r017.v1', phase });
const adversarialCoverage = ['all live phase interruption','ambiguous drift','disable hook before SQL/fence','receipt conservation','Auth mapping','RLS/ACL/Data API','executor input hash binding','fence child failure receipt','fence rollback failure receipt','fence prestate terminal receipt'];
assert.equal(adversarialCoverage.length, 10);

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
  'preflight.sql': ['data_api','rls','acl','auth.users','114','13','16','1885','mazer_username_handle_key'],
  'master-fence.sql': ['begin;','mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts','revoke'],
  'master-refence.sql': ['begin;','mazer_initialize_progression','mazer_complete_level','mazer_complete_ai_level','mazer_reset_progression','revoke'],
  'auth-apply.sql': ['begin;','auth.users','auth.identities','create_and_bind','bind_existing','3_auth_imports','14_existing_binds'],
  'reset-era-apply.sql': ['begin;','whole_row_override','7/6/32/d','39/108/161/s','pgp_sym_encrypt','player_reset_disposition','vault.create_secret','rollback_bound_username_key'],
  'postverify.sql': ['begin;','data_api','rls','acl','117','19','13','16','1885','receipt_conservation','username_origin','mazer-'],
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
  '19','117','1885','7/6/32/D','PGP_SYM_ENCRYPT_AES256','MASTER_DOMINATES_NO_OVERRIDE','PLAYER_RESET_DOMINANCE_DRIFT',
  'Mazer-######','SUPABASE_VAULT','bounded_delta_catchups',
  'currentPreimageSha256','restoreProofSha256','predecessorFenceManifestSha256'
]) assert.ok(host.includes(token) || materializer.includes(token), `missing ${token}`);
assert.ok(host.includes('AUTH_TOPOLOGY_MANIFEST_DRIFT'));
for (const token of ["PSObject.Properties['ArgumentList']",'ArgumentList.Add','ConvertTo-ProcessArgument']) assert.ok(host.includes(token), `structured child transport missing ${token}`);
for (const token of ['Assert-StructuredFenceChildTransportContract','FENCE_CHILD_TRANSPORT_EXIT','FENCE_CHILD_TRANSPORT_STDERR','FENCE_CHILD_TRANSPORT_STDOUT','FENCE_CHILD_TRANSPORT_RECEIPT','FENCE_CHILD_TRANSPORT_EFFECT']) assert.ok(host.includes(token), `structured fence child adversary missing ${token}`);
requireOrder(host.slice(host.indexOf('function Invoke-Child'), host.indexOf('function Get-ShellPath')), ["PSObject.Properties['ArgumentList']",'ArgumentList.Add','else {','ConvertTo-ProcessArgument']);
for (const token of ['ReplayExactRolledBack','PASS_EXACT_ROLLBACK_TERMINAL','replay_requires_explicit_switch','fence.replay-','START_EXACT_REPLAY']) assert.ok(host.includes(token) || materializer.includes(token), `rollback replay seam missing ${token}`);
for (const token of ['Write-FenceChildReceipt','New-FenceChildReceipt','stdout_sha256','stderr_sha256','terminal_category','FENCE_CHILD_FAILURE_RECEIPT_CONTRACT','FENCE_CHILD_ROLLBACK_RECEIPT_CONTRACT']) assert.ok(host.includes(token), `fence child receipt seam missing ${token}`);
for (const token of ["trap {",'NO_EFFECT_PRESTATE','PRESTATE_EXECUTION_HOLD','Write-FailClosedPrestateResult','Get-SafeFailureCategory']) assert.ok(fenceHost.includes(token), `fence prestate receipt seam missing ${token}`);
requireOrder(fenceHost, ['\ntrap {','function Initialize-WindowsCredentialInterop','function Read-ManagementToken','Initialize-WindowsCredentialInterop','function Invoke-AuthConfig','function Read-ProtectedInvocationEnvelope','$invocation = Read-ProtectedInvocationEnvelope','$managementToken = Read-ManagementToken']);
for (const token of ['CREDENTIAL_LOOKUP_REMAINS_REACHABLE','ATLAS_R017_CREDENTIAL_MOCK_SENTINEL','ATLAS_R017_CONNECTOR_SENTINEL','credential_lookup_count: 0','external_connector_calls: 0']) assert.ok(localFenceProbe.includes(token), `local fence isolation seam missing ${token}`);
for (const token of ['New-FenceInvocationEnvelope','ExpectedInvocationSha256','FENCE_INVOCATION_INPUT_SCOPE','Assert-NoReparse (Split-Path -Parent $resolvedInput)','INVOCATION_STATE_CORRELATION','INVOCATION_PARENT_HOST_DRIFT','INVOCATION_CHILD_HOST_DRIFT','INVOCATION_STALE']) assert.ok(host.includes(token) || fenceHost.includes(token), `protected invocation envelope seam missing ${token}`);
assert.ok(!/function\s+[A-Za-z0-9_-]+\([^)]*\[string\]\$Input(?:[,)]|\s)/i.test(host), 'PowerShell automatic $input collision may erase a protected child argument');
assert.ok(!host.includes("'-Mode',$ModeValue") && !host.includes("'-InputPath',$FenceInputPath") && !host.includes("'-StatePath',$FenceState"), 'protected child argv must carry only the sealed invocation envelope');
{
  const localProbeRun = spawnSync(process.execPath, [localFenceProbePath, '--source-check'], { cwd: root, encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(localProbeRun.status, 0, localProbeRun.stderr);
  const localProbeReceipt = JSON.parse(localProbeRun.stdout.trim());
  assert.equal(localProbeReceipt.result, 'PASS_R017_LOCAL_PRODUCTION_SHAPE_SOURCE');
  assert.equal(localProbeReceipt.credential_reads, 0);
  assert.equal(localProbeReceipt.external_calls, 0);
  assert.equal(localProbeReceipt.writes, 0);
}

if (process.platform === 'win32') {
  const envelopeRoot = path.join(root, 'runtime/atlas', `r017 envelope adversary ${crypto.randomUUID().replaceAll('-', '')}`);
  fs.mkdirSync(envelopeRoot, { recursive: true });
  const digest = (value) => crypto.createHash('sha256').update(value).digest('hex');
  const roundtrip = (value) => value.toISOString().replace(/(\.\d{3})Z$/, '$10000+00:00');
  const statePath = path.join(envelopeRoot, 'fence state.json');
  const missingInputPath = path.join(envelopeRoot, 'missing private input.json');
  const correlation = `r017-${digest(Buffer.from(path.resolve(statePath).toLowerCase())).slice(0, 32)}`;
  const issued = new Date();
  const baseEnvelope = {
    schema: 'atlas.supabase.mazer-master-fence-invocation.r017.v1',
    packet: 'FP-MAZER-MASTER-R017-ENVELOPE-ADVERSARY-001',
    correlation_id: correlation,
    mode: 'Forward',
    input_path: path.resolve(missingInputPath),
    state_path: path.resolve(statePath),
    expected_input_sha256: '0'.repeat(64),
    execution_step: 'FenceOnly',
    execute_protected: true,
    parent_host_path: path.resolve(hostPath),
    parent_host_sha256: digest(fs.readFileSync(hostPath)),
    child_host_sha256: digest(fs.readFileSync(fenceHostPath)),
    issued_at: roundtrip(issued),
    expires_at: roundtrip(new Date(issued.getTime() + 300_000))
  };

  function runEnvelope(name, expectedCategory, options = {}) {
    const invocationPath = options.invocationPath ?? path.join(envelopeRoot, `.invocation-${name}.json`);
    const text = options.text ?? `${JSON.stringify(options.value ?? baseEnvelope)}\n`;
    if (!options.missing) fs.writeFileSync(invocationPath, text, { encoding: 'utf8', flag: 'wx' });
    const expectedSha = options.expectedSha ?? digest(Buffer.from(text));
    const shell = options.shell ?? 'pwsh.exe';
    const shellArgs = ['-NoLogo','-NoProfile','-NonInteractive',...(shell === 'powershell.exe' ? ['-ExecutionPolicy','Bypass'] : []),'-File',fenceHostPath,'-InvocationPath',invocationPath,'-ExpectedInvocationSha256',expectedSha,'-ExecuteProtected'];
    const child = spawnSync(shell, shellArgs, { cwd: root, encoding: 'utf8', timeout: 30_000, windowsHide: true });
    assert.equal(child.status, 2, `${name}: ${child.stderr}`);
    assert.equal(child.stderr, '', `${name}: unexpected stderr`);
    const receipt = JSON.parse(child.stdout.trim());
    assert.equal(receipt.result, 'HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE', name);
    assert.equal(receipt.category, expectedCategory, name);
    assert.equal(receipt.effect_status, 'NO_EFFECT_PRESTATE', name);
    assert.equal(receipt.provider_reads, 0, name);
    assert.equal(receipt.provider_writes, 0, name);
    assert.equal(receipt.database_transactions, 0, name);
    assert.equal(fs.existsSync(statePath), false, name);
  }

  try {
    runEnvelope('spaces', 'INPUT_MISSING');
    runEnvelope('rollback', 'INPUT_MISSING', { value: { ...baseEnvelope, mode: 'Rollback', execution_step: 'All' } });
    runEnvelope('digest-drift', 'INVOCATION_DIGEST_DRIFT', { expectedSha: 'f'.repeat(64) });
    runEnvelope('extra-key', 'INVOCATION_KEYS', { value: { ...baseEnvelope, extra: 'reject' } });
    runEnvelope('duplicate-key', 'INVOCATION_KEYS', { text: `${JSON.stringify(baseEnvelope).replace('"packet":', '"packet":"FP-MAZER-MASTER-R017-DUPLICATE-001","packet":')}\n` });
    const escapedUnknown = `${JSON.stringify(baseEnvelope).slice(0, -1)},"\\u0065xtra":"reject"}\n`;
    const escapedDuplicate = `${JSON.stringify(baseEnvelope).slice(0, -1)},"\\u0070acket":"FP-MAZER-MASTER-R017-ESCAPED-DUPLICATE-001"}\n`;
    runEnvelope('escaped-unknown-ps7', 'INVOCATION_KEYS', { text: escapedUnknown });
    runEnvelope('escaped-duplicate-ps7', 'INVOCATION_KEYS', { text: escapedDuplicate });
    runEnvelope('escaped-unknown-ps51', 'INVOCATION_KEYS', { text: escapedUnknown, shell: 'powershell.exe' });
    runEnvelope('escaped-duplicate-ps51', 'INVOCATION_KEYS', { text: escapedDuplicate, shell: 'powershell.exe' });
    const arrayRoot = `[${JSON.stringify(baseEnvelope)}]\n`;
    runEnvelope('array-root-ps7', 'INVOCATION_ROOT_OBJECT', { text: arrayRoot });
    runEnvelope('array-root-ps51', 'INVOCATION_ROOT_OBJECT', { text: arrayRoot, shell: 'powershell.exe' });
    runEnvelope('null-root', 'INVOCATION_ROOT_OBJECT', { text: 'null\n' });
    runEnvelope('scalar-root', 'INVOCATION_ROOT_OBJECT', { text: '42\n' });
    runEnvelope('null-packet', 'INVOCATION_VALUE_TYPES', { value: { ...baseEnvelope, packet: null } });
    runEnvelope('string-switch', 'INVOCATION_VALUE_TYPES', { value: { ...baseEnvelope, execute_protected: 'true' } });
    runEnvelope('unicode', 'INVOCATION_ASCII', { value: { ...baseEnvelope, packet: 'FP-MAZER-MASTER-R017-UNICODE-é' } });
    runEnvelope('wrong-correlation', 'INVOCATION_STATE_CORRELATION', { value: { ...baseEnvelope, correlation_id: 'r017-wrongcorrelation0000000000000000' } });
    runEnvelope('wrong-parent-hash', 'INVOCATION_PARENT_HOST_DRIFT', { value: { ...baseEnvelope, parent_host_sha256: '1'.repeat(64) } });
    runEnvelope('wrong-child-hash', 'INVOCATION_CHILD_HOST_DRIFT', { value: { ...baseEnvelope, child_host_sha256: '2'.repeat(64) } });
    const stale = new Date(issued.getTime() - 20 * 60_000);
    runEnvelope('stale', 'INVOCATION_STALE', { value: { ...baseEnvelope, issued_at: roundtrip(stale), expires_at: roundtrip(new Date(stale.getTime() + 300_000)) } });
    const absentPath = path.join(envelopeRoot, 'missing invocation.json');
    runEnvelope('missing', 'INVOCATION_MISSING', { invocationPath: absentPath, missing: true, expectedSha: '0'.repeat(64), text: '' });

    const realRoot = path.join(envelopeRoot, 'real');
    const junctionRoot = path.join(envelopeRoot, 'junction');
    fs.mkdirSync(realRoot);
    fs.symlinkSync(realRoot, junctionRoot, 'junction');
    const reparsePath = path.join(junctionRoot, 'invocation.json');
    runEnvelope('reparse', 'LOCAL_PATH_REPARSE_POINT', { invocationPath: reparsePath });
  } finally {
    fs.rmSync(envelopeRoot, { recursive: true, force: true });
  }
}
assert.ok(!/trap \{[\s\S]{0,256}Write-SafeResult/.test(fenceHost), 'prestate trap must not recurse through disclosure validation');
const replayReset = host.slice(host.indexOf("if ([string]$state.phase -ceq 'ROLLED_BACK')"), host.indexOf('$managementToken = Read-ManagementToken'));
requireOrder(replayReset, ['ReplayExactRolledBack', "phase = 'PREFLIGHT'", 'Write-State', 'fence.replay-']);
const producer = fs.readFileSync(path.join(root, 'ops/atlas/produce_supabase_mazer_master_preparation_private_source_r017.mjs'), 'utf8');
for (const token of ["crypto.createHmac('sha256'", "vault.create_secret", "delete from vault.secrets where name='mazer_username_handle_key'"]) assert.ok(producer.includes(token), `deterministic replay contract missing ${token}`);
assert.ok(host.includes('auth_counts.binds -ne 14'));
assert.ok(host.includes('auth_counts.final_edges -ne 19'));
assert.ok(!host.includes('auth_counts.binds -ne 13'));
assert.ok(!host.includes('auth_counts.final_edges -ne 18'));
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
