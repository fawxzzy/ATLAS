import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtimeRoot = path.join(root, 'runtime/atlas');
const packetRoot = path.join(root, 'secrets/packet/mazer-master-preparation-r017');
const packet = 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001';
const sourcePath = path.join(packetRoot, 'private-source-pr201-final-71884498-20260826.json');
const manifestPath = path.join(packetRoot, 'materialized-pr201-final-20260826/manifest.json');
const hostPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_r017.ps1');
const launcherPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_credential_safe_r017.ps1');
const predecessorPath = path.join(runtimeRoot, 'mazer-master-r017-terminal-rollback-20260826-212608.json');
const sourceSha = '71884498b45cf0ab04cb71d6533bf9ddef6426a06f92cf77e67242eaf9665e60';
const manifestSha = 'dccfc0bb4e9cf0bc6904a7002ec8bc7acc8d2f392d76a62eb69b99872ad9d1de';
const hostSha = 'd3ec9c210e031ebd887e5f643939ebd584efe218e0db2b346586392bc280453d';
const predecessorSha = '5a20532f9b5e772c52dfe3869f52ed227c56c8e808d945d35a3ae7577483aae3';
const originatingTaskId = '019fa791-8d17-7c83-9c61-3e3c687e9dd7';
const effectClass = 'supabase_protected_master_preparation';
const effectTarget = 'supabase:geknvnrmktchljnyddwp/public+bxtcuhkotumitoqtrcej/mazer';
const maxEffectCount = 20;
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) && JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...keys].sort());
const uuid4 = value => typeof value === 'string' && /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(value);
const formatO = date => date.toISOString().replace('Z', '0000Z');

function inside(candidate, boundary, code) {
  const value = path.resolve(candidate), rootPath = path.resolve(boundary).replace(/[\\/]+$/, '');
  if (value.toLowerCase() !== rootPath.toLowerCase() && !value.toLowerCase().startsWith(`${rootPath.toLowerCase()}${path.sep}`)) throw new Error(code);
  return value;
}
function assertNoReparse(candidate, boundary) {
  const base = path.resolve(boundary), target = inside(candidate, base, 'REPARSE_SCOPE');
  let cursor = base;
  for (const part of path.relative(base, target).split(path.sep).filter(Boolean)) {
    if (fs.lstatSync(cursor).isSymbolicLink()) throw new Error('REPARSE_COMPONENT');
    cursor = path.join(cursor, part);
  }
  if (fs.existsSync(cursor) && fs.lstatSync(cursor).isSymbolicLink()) throw new Error('REPARSE_COMPONENT');
}
function readJson(file, boundary, maxBytes = 262144) {
  const resolved = inside(file, boundary, 'INPUT_SCOPE'); assertNoReparse(resolved, boundary);
  const bytes = fs.readFileSync(resolved); if (bytes.length < 2 || bytes.length > maxBytes) throw new Error('INPUT_SIZE');
  if (!/^[\x09\x0a\x0d\x20-\x7e]+$/.test(bytes.toString('latin1'))) throw new Error('INPUT_ASCII');
  let value; try { value = JSON.parse(bytes.toString('utf8')); } catch { throw new Error('INPUT_JSON'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('INPUT_ROOT');
  return { path: resolved, bytes, sha256: sha256(bytes), value };
}
function atlasRelative(file) { return path.relative(root, file).split(path.sep).join('/'); }
function canonicalAliasPath(decisionPath) {
  let stem=path.parse(decisionPath).name;
  for(const suffix of ['-operator-decision-request','-decision-request'])if(stem.endsWith(suffix)){stem=stem.slice(0,-suffix.length);break;}
  return path.join(path.dirname(decisionPath),`${stem}-scoped-approval-alias.json`);
}
const canonicalAuthorizationPath = aliasPath => path.join(path.dirname(aliasPath),`${path.parse(aliasPath).name}-authorization.json`);
const canonicalConsumptionPath = aliasPath => path.join(path.dirname(aliasPath),`${path.parse(aliasPath).name}-consumption.json`);
function timestamp(value, code) { const ms = Date.parse(value); if (!Number.isFinite(ms)) throw new Error(code); return ms; }
function safeWrite(outputPath, bytes) {
  const output = inside(outputPath, packetRoot, 'OUTPUT_SCOPE');
  if (path.dirname(output).toLowerCase() !== packetRoot.toLowerCase()) throw new Error('OUTPUT_PARENT');
  if (!/^launcher-invocation-[a-f0-9-]{36}\.json$/.test(path.basename(output))) throw new Error('OUTPUT_NAME');
  assertNoReparse(packetRoot, packetRoot); if (fs.existsSync(output)) throw new Error('OUTPUT_EXISTS');
  const realRoot = fs.realpathSync.native(packetRoot); if (realRoot.toLowerCase() !== packetRoot.toLowerCase()) throw new Error('OUTPUT_ROOT_REALPATH');
  let fd, created = false, wrote = false;
  try {
    fd = fs.openSync(output, fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY, 0o600); created = true;
    if (!fs.fstatSync(fd).isFile() || fs.lstatSync(output).isSymbolicLink()) throw new Error('OUTPUT_HANDLE');
    const final = fs.realpathSync.native(output); inside(final, realRoot, 'OUTPUT_ESCAPE');
    if (final.toLowerCase() !== output.toLowerCase()) throw new Error('OUTPUT_PATH_DRIFT');
    fs.writeFileSync(fd, bytes); fs.fsyncSync(fd); wrote = true; assertNoReparse(packetRoot, packetRoot);
  } catch (error) {
    if (created && !wrote) { try { if (fd !== undefined) { fs.closeSync(fd); fd = undefined; } if (fs.existsSync(output) && !fs.lstatSync(output).isSymbolicLink()) fs.unlinkSync(output); } catch {} }
    throw error;
  } finally { if (fd !== undefined) fs.closeSync(fd); }
  return output;
}

export function sealInvocation({ decisionRequestPath, aliasPath, authorizationPath, consumptionPath, outputPath, now = new Date() }) {
  const decision = readJson(decisionRequestPath, runtimeRoot), alias = readJson(aliasPath, runtimeRoot), authorization = readJson(authorizationPath, runtimeRoot), consumption = readJson(consumptionPath, runtimeRoot);
  if (alias.path.toLowerCase() !== canonicalAliasPath(decision.path).toLowerCase()) throw new Error('ALIAS_PATH');
  if (authorization.path.toLowerCase() !== canonicalAuthorizationPath(alias.path).toLowerCase()) throw new Error('AUTHORIZATION_PATH');
  if (consumption.path.toLowerCase() !== canonicalConsumptionPath(alias.path).toLowerCase()) throw new Error('CONSUMPTION_PATH');
  const d = decision.value, a = alias.value, z = authorization.value, c = consumption.value;
  if (d.schema !== 'atlas.operator-decision-request.v1' || d.packet !== packet || d.status !== 'AWAITING_OPERATOR_DECISION' || d.execution_authority !== false) throw new Error('DECISION_CONTRACT');
  if (!exactKeys(a, ['allowed_effect','approval_code','decision_request','execution_authority','expected_operator_response','expires_at','intent_digest','issued_at','originating_task_id','packet','schema','semantic_objective','single_use','status'])) throw new Error('ALIAS_KEYS');
  if (a.schema !== 'atlas.scoped-approval-alias.v1' || a.packet !== packet || a.status !== 'OPEN' || a.single_use !== true || a.execution_authority !== false || a.originating_task_id !== originatingTaskId || a.expected_operator_response !== `APPROVE ${a.approval_code}`) throw new Error('ALIAS_CONTRACT');
  if (a.allowed_effect?.effect_class !== effectClass || a.allowed_effect?.target !== effectTarget || a.allowed_effect?.max_effect_count !== maxEffectCount) throw new Error('ALIAS_EFFECT');
  if (a.decision_request?.sha256 !== decision.sha256 || path.resolve(root, a.decision_request?.path ?? '') !== decision.path) throw new Error('ALIAS_DECISION_BINDING');
  if (sha256(Buffer.from(d.exact_authorization_phrase ?? '', 'utf8')) !== a.decision_request?.exact_authorization_phrase_sha256) throw new Error('ALIAS_PHRASE_BINDING');
  if (z.schema !== 'atlas.scoped-approval-authorization.v1' || z.packet !== packet || z.status !== 'AUTHORIZED_SINGLE_USE' || z.single_use !== true || z.execution_authority !== true || z.originating_task_id !== originatingTaskId || z.approval_code !== a.approval_code || z.alias?.sha256 !== alias.sha256 || path.resolve(root, z.alias?.path ?? '') !== alias.path || z.decision_request?.sha256 !== decision.sha256 || z.intent_digest !== a.intent_digest) throw new Error('AUTHORIZATION_BINDING');
  if (c.schema !== 'atlas.scoped-approval-consumption.v1' || c.packet !== packet || c.status !== 'CONSUMED' || c.reusable !== false || c.max_effect_count !== maxEffectCount || c.authorization_sha256 !== authorization.sha256 || c.intent_digest !== a.intent_digest || !uuid4(c.execution_correlation_id)) throw new Error('CONSUMPTION_BINDING');
  const nowMs = now.getTime(), aliasIssued = timestamp(a.issued_at, 'ALIAS_TIME'), authorized = timestamp(z.authorized_at, 'AUTHORIZATION_TIME'), consumed = timestamp(c.consumed_at, 'CONSUMPTION_TIME'), expires = timestamp(a.expires_at, 'ALIAS_TIME');
  if (aliasIssued > authorized || authorized > consumed || consumed > nowMs + 5000 || expires <= nowMs || expires > aliasIssued + 86400000) throw new Error('APPROVAL_TIME');
  if (d.expires_at !== a.expires_at || d.sealed_inputs?.execution_correlation_id !== c.execution_correlation_id) throw new Error('DECISION_EXECUTION_BINDING');
  const launcherSha = sha256(fs.readFileSync(launcherPath));
  if (d.sealed_inputs?.private_source_sha256 !== sourceSha || d.sealed_inputs?.manifest_sha256 !== manifestSha || d.sealed_inputs?.host_sha256 !== hostSha || d.sealed_inputs?.credential_safe_launcher_sha256 !== launcherSha) throw new Error('DECISION_SEALED_HASHES');
  for (const [file, expected] of [[sourcePath,sourceSha],[manifestPath,manifestSha],[hostPath,hostSha],[predecessorPath,predecessorSha]]) if (sha256(fs.readFileSync(file)) !== expected) throw new Error('SEALED_FILE_DIGEST');
  const correlation = c.execution_correlation_id, successor = path.join(runtimeRoot, `mazer-master-r017-execution-${correlation}.json`);
  if (fs.existsSync(successor)) throw new Error('SUCCESSOR_EXISTS');
  const issuedAt = formatO(now), envelope = {
    schema: 'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v2', packet,
    decision_request_path: decision.path, decision_request_sha256: decision.sha256,
    approval_alias_path: alias.path, approval_alias_sha256: alias.sha256,
    approval_authorization_path: authorization.path, approval_authorization_sha256: authorization.sha256,
    approval_consumption_path: consumption.path, approval_consumption_sha256: consumption.sha256,
    approval_expires_at: a.expires_at,
    predecessor_correlation_id: 'fde0a66f-a157-4258-a92f-e6af933ecc1c', predecessor_state_path: predecessorPath, predecessor_state_sha256: predecessorSha,
    execution_correlation_id: correlation,
    private_source_path: sourcePath, private_source_sha256: sourceSha,
    private_manifest_path: manifestPath, private_manifest_sha256: manifestSha,
    successor_state_path: successor,
    host_path: hostPath, host_sha256: hostSha,
    launcher_path: launcherPath, launcher_sha256: launcherSha,
    not_before: c.consumed_at, issued_at: issuedAt, expires_at: a.expires_at
  };
  const expectedOutput = path.join(packetRoot, `launcher-invocation-${correlation}.json`);
  if (path.resolve(outputPath).toLowerCase() !== expectedOutput.toLowerCase()) throw new Error('OUTPUT_CORRELATION');
  const bytes = Buffer.from(`${JSON.stringify(envelope, null, 2)}\n`, 'ascii'); safeWrite(outputPath, bytes);
  return { path: expectedOutput, sha256: sha256(bytes), execution_correlation_id: correlation, expires_at: a.expires_at };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const result = sealInvocation({ decisionRequestPath: process.argv[2], aliasPath: process.argv[3], authorizationPath: process.argv[4], consumptionPath: process.argv[5], outputPath: process.argv[6] });
    console.log(JSON.stringify({ schema:'atlas.supabase.mazer-master-preparation-invocation-seal-result.r017.v1', result:'PASS_R017_INVOCATION_SEALED', ...result, external_calls:0, credential_reads:0, secret_reads:0 }));
  } catch (error) {
    console.log(JSON.stringify({ schema:'atlas.supabase.mazer-master-preparation-invocation-seal-result.r017.v1', result:'HOLD_R017_INVOCATION_SEAL', category:String(error.message).replace(/[^A-Za-z0-9_]/g,'').slice(0,64), external_calls:0, credential_reads:0, secret_reads:0 })); process.exitCode = 2;
  }
}
