import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const paths = {
  host: path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_r017.ps1'),
  materializer: path.join(root, 'ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs'),
  focused: path.join(root, 'ops/atlas/tests/test_supabase_mazer_master_preparation_r017.mjs'),
  fenceHost: path.join(root, 'ops/atlas/invoke_supabase_mazer_master_cutover_data_fence_r001.ps1'),
  fenceClassifier: path.join(root, 'ops/atlas/classify_supabase_mazer_master_cutover_data_fence_r001.mjs')
};
const source = Object.fromEntries(Object.entries(paths).map(([key, value]) => [key, fs.readFileSync(value, 'utf8')]));
const findings = [];
const requireText = (where, token, category) => { if (!where.includes(token)) findings.push(category); };

for (const token of [
  '2b8495a95fca9a860571343174bfb93bcad8c5e9','1bbf69cf8f38aa1e2b053d0b70d82a315317b58a','481ab55323afff53f5e841012684b7e26f689349',
  '5618f3050fb31b52d8241446b4cc4e477b07250c45dfaadffd7eb7ebd8d01806','9e39b18246699405fc1651f64995a8526d5750e5bebcc85e880f4f295b12a308','54dee535bac3e02b7058fe644cd44af115cc3746ff1e40390521992dccd14971',
  '63f43d8c2f532b32e3453879e4ca49ffc2f5b382264a290ad9a3ea1225811ced','gitBlob','cat-file','SQL_DIGEST_DRIFT',
  'AMBIGUOUS_IDENTITY_MAP','UNSUPPORTED_PASSWORD_VERIFIER','IMPORT_WOULD_FIRE_SIGNUP_TRIGGER','PLAYER_RESET_DOMINANCE_DRIFT',
  'PGP_SYM_ENCRYPT_AES256','EXACT_WHOLE_ROW','MASTER_DOMINATES_NO_OVERRIDE','receipt_conservation','data_api','rls','acl'
]) requireText(source.materializer, token, `MATERIALIZER_CONTRACT_MISSING:${token}`);
for (const token of [
  'FENCE_PAUSED','MASTER_FENCE_APPLYING','M1_APPLYING','M2_APPLYING','MASTER_REFENCE_APPLYING','AUTH_APPLYING',
  'RESET_QUARANTINE_APPLYING','DELTA_APPLYING','M3_APPLYING','POSTVERIFYING','HOOK_ACTIVATING','QA_APPLYING','QA_CLEANING',
  'LEGACY_RESTORING','LEGACY_RESTORED','PREPARATION_COMPLETE','ROLLBACK_DISABLING_HOOK','rollback_initiated_at',
  'RollbackDeadlineSeconds = 600','HardFenceLeaseSeconds = 900','Start-RollbackWatchdog','WindowStyle Hidden'
]) requireText(source.host, token, `HOST_LIFECYCLE_MISSING:${token}`);
for (const token of ['AUTH_TOPOLOGY_MANIFEST_DRIFT','auth_counts.binds -ne 14','auth_counts.final_edges -ne 19','auth_counts.retained_edges -ne 2','final_identity_edges = 19','profiles = 12','player = 16','ai = 16','receipts = 1883']) requireText(source.host, token, `HOST_TOPOLOGY_VERIFICATION_MISSING:${token}`);
for (const stale of ['auth_counts.binds -ne 13','auth_counts.final_edges -ne 18','final_identity_edges = 18','profiles = 11','player = 15','ai = 15','receipts = 1882']) if (source.host.includes(stale)) findings.push(`HOST_STALE_REBOUND_DENOMINATOR:${stale}`);
for (const token of ['all live phase interruption','ambiguous drift','disable hook before SQL/fence','receipt conservation','Auth mapping','RLS/ACL/Data API','executor input hash binding','fence child failure receipt','fence rollback failure receipt','fence prestate terminal receipt']) requireText(source.focused, token, `ADVERSARY_LABEL_MISSING:${token}`);
for (const token of ['Write-FenceChildReceipt','stdout_sha256','stderr_sha256','terminal_category','FENCE_CHILD_FAILURE_RECEIPT_CONTRACT','FENCE_CHILD_ROLLBACK_RECEIPT_CONTRACT']) requireText(source.host, token, `FENCE_CHILD_RECEIPT_MISSING:${token}`);
for (const token of ["PSObject.Properties['ArgumentList']",'ArgumentList.Add','ConvertTo-ProcessArgument']) requireText(source.host, token, `STRUCTURED_CHILD_TRANSPORT_MISSING:${token}`);
for (const token of ['Assert-StructuredFenceChildTransportContract','FENCE_CHILD_TRANSPORT_EXIT','FENCE_CHILD_TRANSPORT_STDERR','FENCE_CHILD_TRANSPORT_STDOUT','FENCE_CHILD_TRANSPORT_RECEIPT','FENCE_CHILD_TRANSPORT_EFFECT']) requireText(source.host, token, `STRUCTURED_FENCE_CHILD_ADVERSARY_MISSING:${token}`);
for (const token of ['NO_EFFECT_PRESTATE','PRESTATE_EXECUTION_HOLD','Write-FailClosedPrestateResult','Get-SafeFailureCategory']) requireText(source.fenceHost, token, `FENCE_PRESTATE_RECEIPT_MISSING:${token}`);
if (/trap \{[\s\S]{0,256}Write-SafeResult/.test(source.fenceHost)) findings.push('FENCE_PRESTATE_DISCLOSURE_RECURSION');

const sourceOnlyHost = source.host.slice(source.host.indexOf("if ($PSCmdlet.ParameterSetName -ceq 'Source')"), source.host.indexOf("if (-not $ExecuteProtected)"));
if (/Invoke-RestMethod|Invoke-Psql|Start-RollbackWatchdog/.test(sourceOnlyHost)) findings.push('SOURCE_ONLY_MUTATION_PATH');
if (source.host.includes('vercel deploy') || source.host.includes('vercel promote') || source.host.includes('git push')) findings.push('OUT_OF_SCOPE_ACTION');

function runFocused() {
  const child = spawnSync(process.execPath, [paths.focused], { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 300_000 });
  if (child.status !== 0 || child.signal || child.stderr.trim()) findings.push('FOCUSED_TEST_FAILED');
  return child.stdout.trim();
}
const first = runFocused();
const second = runFocused();
if (first !== second) findings.push('FOCUSED_TEST_NONDETERMINISTIC');
if (first) {
  const result = JSON.parse(first);
  assert.equal(result.result, 'PASS_MAZER_MASTER_PREPARATION_R017');
  assert.equal(result.provider_calls, 0);
  assert.equal(result.live_data_writes, 0);
}

assert.deepEqual(findings, []);
console.log(JSON.stringify({ result: 'PASS_MAZER_MASTER_PREPARATION_R017_REVIEW_NO_FINDINGS', findings: 0, focused_runs: 2, provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, deployments: 0 }));
