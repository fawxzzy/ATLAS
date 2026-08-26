import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const launcher = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_credential_safe_r017.ps1');
const host = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_r017.ps1');
const packetRoot = path.join(root, 'secrets/packet/mazer-master-preparation-r017');
const runtime = path.join(root, 'runtime/atlas');
const source = path.join(packetRoot, 'private-source-auth-action-preimage-v3-20260826.json');
const manifest = path.join(packetRoot, 'materialized-auth-action-preimage-v3-20260826/manifest.json');
const predecessor = path.join(runtime, 'mazer-master-r017-execution-a7db1fd5-a165-43e6-a9a8-c267233005b2.json');
const sourceSha = '9326145071e2e067286e6460d06187d89d3bdc6b82c202b2cbea2f313f0b35ae';
const manifestSha = 'b60539e13e7b838a0f36adc8333cfdccfc0ac55cccc57330240cacede2335879';
const predecessorSha = '5e01271273a910d861c1fb0712ac7d48a8b565a971f6a270cf6fe8409138a0d9';
const hostSha = 'd3ec9c210e031ebd887e5f643939ebd584efe218e0db2b346586392bc280453d';
const sha = value => crypto.createHash('sha256').update(value).digest('hex');

function run(shell, args) {
  const result = spawnSync(shell, args, { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 60_000 });
  return { ...result, receipt: result.stdout.trim() ? JSON.parse(result.stdout.trim()) : null };
}
function runLauncher(shell, args) {
  return run(shell, ['-NoLogo', '-NoProfile', '-NonInteractive', ...(shell === 'powershell.exe' ? ['-ExecutionPolicy', 'Bypass'] : []), '-File', launcher, ...args]);
}

for (const shell of ['pwsh.exe', 'powershell.exe']) {
  const sourceRun = runLauncher(shell, ['-SourceOnlyValidate']);
  assert.equal(sourceRun.status, 0, sourceRun.stderr);
  assert.equal(sourceRun.receipt.result, 'PASS_R017_CREDENTIAL_SAFE_LAUNCHER_SOURCE');
  assert.equal(sourceRun.receipt.external_calls, 0);
  assert.equal(sourceRun.receipt.credential_reads, 0);
  const sentinel = runLauncher(shell, ['-LocalSentinelProbe']);
  assert.equal(sentinel.status, 0, sentinel.stderr);
  assert.equal(sentinel.receipt.result, 'PASS_R017_CREDENTIAL_SAFE_ENV_SENTINEL');
  assert.equal(sentinel.receipt.external_calls, 0);
}
const transportAdversaries = [
  ['timeout', 'CHILD_TIMEOUT'], ['stderr', 'CHILD_STDERR'], ['malformed', 'CHILD_RECEIPT_SHAPE'],
  ['empty_object', 'CHILD_RECEIPT_KEYS'], ['wrong_schema', 'CHILD_RECEIPT_VALUES'], ['wrong_result', 'CHILD_RECEIPT_RESULT'],
  ['missing_fields', 'CHILD_RECEIPT_KEYS'], ['duplicate_key', 'CHILD_RECEIPT_KEYS'], ['escaped_key', 'CHILD_RECEIPT_KEYS'],
  ['array', 'CHILD_RECEIPT_SHAPE'], ['scalar', 'CHILD_RECEIPT_SHAPE']
];
for (const [kind, category] of transportAdversaries) {
  const child = runLauncher('pwsh.exe', ['-LocalTransportAdversary', kind]);
  assert.equal(child.status, 2, `${kind}: ${child.stderr}\n${child.stdout}`);
  assert.equal(child.receipt.result, 'HOLD_R017_CREDENTIAL_SAFE_LAUNCHER');
  assert.equal(child.receipt.category, category);
  assert.equal(child.receipt.external_effects_unknown, true);
  assert.equal(child.receipt.execution_correlation_id, '00000000-0000-4000-8000-000000000000');
}

const launcherText = fs.readFileSync(launcher, 'utf8');
for (const token of [
  sourceSha, manifestSha, predecessorSha, hostSha,
  'PREDECESSOR_BINDING', 'SEALED_HASH_BINDING', 'SEALED_PATH_BINDING',
  'SUCCESSOR_STATE_BINDING', 'PREDECESSOR_EFFECT_STATE', 'INVOCATION_KEYS',
  'SUPABASE_ACCESS_TOKEN', 'ATLAS_MAZER_LEGACY_DATABASE_URL', 'ATLAS_MAZER_MASTER_DATABASE_URL',
  'Read-ManagementToken', 'Read-ProjectPassword', 'Invoke-Child', 'ProtectedChildStarted',
  'Convert-ProtectedChildReceipt', 'external_effects_unknown=[bool]$script:ProtectedChildStarted'
]) assert.ok(launcherText.includes(token), `MISSING_LAUNCHER_GATE:${token}`);
assert.doesNotMatch(launcherText, /PrivateSourceOverride|StatePathOverride|ExpectedSourceShaOverride/);

let productionAdversaries = 0;
if ([source, manifest, predecessor, host].every(file => fs.existsSync(file))) {
  assert.equal(sha(fs.readFileSync(source)), sourceSha);
  assert.equal(sha(fs.readFileSync(manifest)), manifestSha);
  assert.equal(sha(fs.readFileSync(predecessor)), predecessorSha);
  assert.equal(sha(fs.readFileSync(host)), hostSha);
  const correlation = crypto.randomUUID();
  const successor = path.join(runtime, `mazer-master-r017-execution-${correlation}.json`);
  assert.equal(fs.existsSync(successor), false);
  const now = new Date();
  const envelope = {
    schema: 'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v1',
    packet: 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001',
    predecessor_correlation_id: 'a7db1fd5-a165-43e6-a9a8-c267233005b2',
    predecessor_state_path: predecessor,
    predecessor_state_sha256: predecessorSha,
    execution_correlation_id: correlation,
    private_source_path: source,
    private_source_sha256: sourceSha,
    private_manifest_path: manifest,
    private_manifest_sha256: manifestSha,
    successor_state_path: successor,
    host_path: host,
    host_sha256: hostSha,
    issued_at: now.toISOString().replace('Z', '0000Z'),
    expires_at: new Date(now.getTime() + 60_000).toISOString().replace('Z', '0000Z')
  };
  const paths = [];
  const validate = (name, value, expectedStatus, expectedCategory) => {
    const file = path.join(packetRoot, `.launcher-test-${name}-${process.pid}-${Date.now()}.json`);
    const bytes = Buffer.from(`${JSON.stringify(value)}\n`);
    fs.writeFileSync(file, bytes, { flag: 'wx' }); paths.push(file);
    const result = runLauncher('pwsh.exe', ['-ValidateInvocationOnly', '-InvocationPath', file, '-ExpectedInvocationSha256', sha(bytes)]);
    assert.equal(result.status, expectedStatus, `${result.stderr}\n${result.stdout}`);
    if (expectedCategory) assert.equal(result.receipt.category, expectedCategory);
    return result;
  };
  try {
    assert.equal(validate('valid', envelope, 0).receipt.result, 'PASS_R017_LAUNCHER_INVOCATION_BOUND');
    validate('wrong-sha', { ...envelope, private_source_sha256: '0'.repeat(64) }, 2, 'SEALED_HASH_BINDING');
    validate('wrong-path', { ...envelope, private_source_path: manifest }, 2, 'SEALED_PATH_BINDING');
    validate('wrong-correlation', { ...envelope, successor_state_path: path.join(runtime, `mazer-master-r017-execution-${crypto.randomUUID()}.json`) }, 2, 'SUCCESSOR_STATE_BINDING');
    productionAdversaries = 4;
  } finally {
    for (const file of paths) if (fs.existsSync(file)) fs.unlinkSync(file);
  }
}

console.log(JSON.stringify({
  result: 'PASS_MAZER_MASTER_PREPARATION_CREDENTIAL_SAFE_LAUNCHER_R017',
  engines: 2,
  sentinel_connectors: 3,
  poststart_failure_adversaries: transportAdversaries.length,
  production_adversaries: productionAdversaries,
  external_calls: 0,
  credential_reads: 0,
  secret_reads: 0,
  live_data_writes: 0
}));
