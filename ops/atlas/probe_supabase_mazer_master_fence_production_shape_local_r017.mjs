import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const host = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_cutover_data_fence_r001.ps1');
const parentHost = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_r017.ps1');
const input = path.join(root, 'secrets/packet/mazer-master-preparation-r017/launcher-preflight-materialized/fence-input.json');
const packetRoot = path.join(root, 'secrets/packet/mazer-master-preparation-r017/local-production-shape-probes');
const runtimeRoot = path.join(root, 'runtime/atlas');
const id = crypto.randomUUID().replaceAll('-', '');
const captureRoot = path.join(packetRoot, id);
const effectiveHost = path.join(root, `ops/atlas/.r017-local-effective-${id}.ps1`);
const state = path.join(runtimeRoot, `.r017-local-production-shape-${id}.json`);
const credentialMockSentinel = path.join(captureRoot, 'credential-provider-mock-invoked');
const connectorSentinel = path.join(captureRoot, 'external-connector-invoked');
const sha = (value) => crypto.createHash('sha256').update(value).digest('hex');
const roundtrip = (value) => value.toISOString().replace(/(\.\d{3})Z$/, '$10000+00:00');

if (!fs.existsSync(host)) throw new Error('LOCAL_PROBE_HOST_MISSING');
if (process.argv.includes('--source-check')) {
  const checked = fs.readFileSync(host, 'utf8');
  const order = ['\ntrap {','function Initialize-WindowsCredentialInterop','function Read-ManagementToken','Initialize-WindowsCredentialInterop','function Invoke-AuthConfig','function Read-ProtectedInvocationEnvelope','$invocation = Read-ProtectedInvocationEnvelope','$managementToken = Read-ManagementToken'];
  let cursor = -1;
  for (const token of order) {
    const next = checked.indexOf(token, cursor + 1);
    if (next < 0) throw new Error(`LOCAL_PROBE_SOURCE_ORDER:${token}`);
    cursor = next;
  }
  console.log(JSON.stringify({ result: 'PASS_R017_LOCAL_PRODUCTION_SHAPE_SOURCE', credential_reads: 0, external_calls: 0, writes: 0 }));
  process.exit(0);
}
if (!fs.existsSync(input)) throw new Error('LOCAL_PROBE_INPUT_MISSING');
fs.mkdirSync(captureRoot, { recursive: true });
let source = fs.readFileSync(host, 'utf8');
const credentialStart = source.indexOf('function Initialize-WindowsCredentialInterop');
const authStart = source.indexOf('function Invoke-AuthConfig');
if (credentialStart < 0 || authStart <= credentialStart) throw new Error('CREDENTIAL_INJECTION_SEAM_DRIFT');
source = source.slice(0, credentialStart) + `function Read-ManagementToken {\n  [IO.File]::WriteAllText($env:ATLAS_R017_CREDENTIAL_MOCK_SENTINEL, 'mock-only')\n  throw 'LOCAL_CREDENTIAL_PROVIDER_MOCK_STOP'\n}\n\n` + source.slice(authStart);
const trapIndex = source.indexOf('\ntrap {');
if (trapIndex < 0) throw new Error('TRAP_SEAM_DRIFT');
const connectorMocks = `
function Invoke-AuthConfig { [IO.File]::WriteAllText($env:ATLAS_R017_CONNECTOR_SENTINEL, 'auth'); throw 'LOCAL_EXTERNAL_CONNECTOR_BLOCKED' }
function Invoke-PsqlPrivate { [IO.File]::WriteAllText($env:ATLAS_R017_CONNECTOR_SENTINEL, 'psql'); throw 'LOCAL_EXTERNAL_CONNECTOR_BLOCKED' }
function Invoke-PsqlJsonPrivate { [IO.File]::WriteAllText($env:ATLAS_R017_CONNECTOR_SENTINEL, 'psql-json'); throw 'LOCAL_EXTERNAL_CONNECTOR_BLOCKED' }
function Invoke-PsqlObservation { [IO.File]::WriteAllText($env:ATLAS_R017_CONNECTOR_SENTINEL, 'psql-observation'); throw 'LOCAL_EXTERNAL_CONNECTOR_BLOCKED' }
`;
source = source.slice(0, trapIndex) + connectorMocks + source.slice(trapIndex);
if (source.includes('CredRead(') || source.includes('CredReadW')) throw new Error('CREDENTIAL_LOOKUP_REMAINS_REACHABLE');
fs.writeFileSync(effectiveHost, source, { encoding: 'utf8', flag: 'wx' });

const engine = spawnSync('where.exe', ['pwsh.exe'], { encoding: 'utf8' }).stdout.split(/\r?\n/).find(Boolean);
if (!engine || !path.isAbsolute(engine)) throw new Error('PWSH_ENGINE_MISSING');
const issued = new Date();
const correlation = `r017-${sha(Buffer.from(path.resolve(state).toLowerCase())).slice(0, 32)}`;
const invocation = path.join(captureRoot, `.fence-invocation-${correlation}-${id}.json`);
const envelope = {
  schema: 'atlas.supabase.mazer-master-fence-invocation.r017.v1',
  packet: 'FP-MAZER-MASTER-R017-LOCAL-PRODUCTION-SHAPE-001',
  correlation_id: correlation,
  mode: 'Forward',
  input_path: path.resolve(input),
  state_path: path.resolve(state),
  expected_input_sha256: sha(fs.readFileSync(input)),
  execution_step: 'FenceOnly',
  execute_protected: true,
  parent_host_path: path.resolve(parentHost),
  parent_host_sha256: sha(fs.readFileSync(parentHost)),
  child_host_sha256: sha(fs.readFileSync(effectiveHost)),
  issued_at: roundtrip(issued),
  expires_at: roundtrip(new Date(issued.getTime() + 300_000))
};
fs.writeFileSync(invocation, `${JSON.stringify(envelope)}\n`, { encoding: 'ascii', flag: 'wx' });
const arguments_ = ['-NoLogo','-NoProfile','-NonInteractive','-File',effectiveHost,'-InvocationPath',invocation,'-ExpectedInvocationSha256',sha(fs.readFileSync(invocation)),'-ExecuteProtected'];
const environment = {
  ...process.env,
  ATLAS_MAZER_LEGACY_DATABASE_URL: 'postgresql://postgres.geknvnrmktchljnyddwp:local-only@aws-0-us-west-2.pooler.supabase.com:5432/postgres',
  ATLAS_MAZER_MASTER_DATABASE_URL: 'postgresql://postgres.bxtcuhkotumitoqtrcej:local-only@aws-0-ca-central-1.pooler.supabase.com:5432/postgres',
  ATLAS_R017_CREDENTIAL_MOCK_SENTINEL: credentialMockSentinel,
  ATLAS_R017_CONNECTOR_SENTINEL: connectorSentinel,
  HTTP_PROXY: 'http://127.0.0.1:1',
  HTTPS_PROXY: 'http://127.0.0.1:1',
  NO_PROXY: ''
};

let child;
try {
  child = spawnSync(engine, arguments_, { cwd: root, env: environment, encoding: 'utf8', timeout: 120000, windowsHide: true });
  fs.writeFileSync(path.join(captureRoot, 'stdout.bin'), child.stdout ?? '', 'utf8');
  fs.writeFileSync(path.join(captureRoot, 'stderr.bin'), child.stderr ?? '', 'utf8');
  if (child.error) throw child.error;
  if (child.status !== 2) throw new Error(`LOCAL_PROBE_EXIT:${child.status}`);
  if ((child.stderr ?? '').length !== 0) throw new Error('LOCAL_PROBE_STDERR');
  const receipt = JSON.parse((child.stdout ?? '').trim());
  if (receipt.result !== 'HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE' || receipt.category !== 'LOCAL_CREDENTIAL_PROVIDER_MOCK_STOP') throw new Error('LOCAL_PROBE_RECEIPT');
  if (!fs.existsSync(credentialMockSentinel) || fs.existsSync(connectorSentinel)) throw new Error('LOCAL_PROBE_ISOLATION');
  console.log(JSON.stringify({
    result: 'PASS_R017_LOCAL_PRODUCTION_SHAPE',
    root_cause: 'POWERSHELL_AUTOMATIC_INPUT_VARIABLE_COLLISION_REMOVED_CHILD_INPUT_PATH',
    original_host_sha256: sha(fs.readFileSync(host)),
    effective_host_sha256: sha(fs.readFileSync(effectiveHost)),
    engine_sha256: sha(fs.readFileSync(engine)),
    argv_sha256: sha(Buffer.from(arguments_.join('\0'))),
    input_sha256: sha(fs.readFileSync(input)),
    stdout_sha256: sha(Buffer.from(child.stdout ?? '')),
    stderr_sha256: sha(Buffer.from(child.stderr ?? '')),
    exit_code: child.status,
    terminal_category: receipt.category,
    credential_lookup_count: 0,
    credential_provider_mock_calls: 1,
    external_connector_calls: 0,
    provider_reads: 0,
    provider_writes: 0,
    auth_writes: 0,
    live_data_writes: 0,
    capture_root_sha256: sha(Buffer.from(captureRoot.toLowerCase()))
  }));
} finally {
  for (const candidate of [effectiveHost, state, `${state}.tmp`]) {
    try { fs.rmSync(candidate, { force: true }); } catch {}
  }
}
