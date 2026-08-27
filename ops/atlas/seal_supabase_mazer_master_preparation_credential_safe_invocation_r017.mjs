import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtimeRoot = path.join(root, 'runtime/atlas');
const packetRoot = path.join(root, 'secrets/packet/mazer-master-preparation-r017');
const packet = 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001';
const hostPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_r017.ps1');
const launcherPath = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_credential_safe_r017.ps1');
const materializerPath = path.join(root, 'ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs');
const classifierPath = path.join(root, 'ops/atlas/classify_supabase_mazer_master_cutover_data_fence_r001.mjs');
const nodePath = fs.realpathSync.native(process.execPath);
const originatingTaskId = '019fa791-8d17-7c83-9c61-3e3c687e9dd7';
const effectClass = 'supabase_protected_master_preparation';
const effectTarget = 'supabase:geknvnrmktchljnyddwp/public+bxtcuhkotumitoqtrcej/mazer';
const maxEffectCount = 20;
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) && JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...keys].sort());
const uuid4 = value => typeof value === 'string' && /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(value);
const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const commit = value => typeof value === 'string' && /^[a-f0-9]{40}$/.test(value);
const positiveInteger = value => Number.isInteger(value) && value > 0;
const formatO = date => date.toISOString().replace('Z', '000Z');
const canonicalInstant = (value, code) => {
  const match = typeof value === 'string' && /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,7}))?Z$/.exec(value);
  if (!match) throw new Error(code);
  const [, year, month, day, hour, minute, second, fraction] = match;
  const seconds = Date.parse(`${year}-${month}-${day}T${hour}:${minute}:${second}Z`);
  if (!Number.isFinite(seconds)) throw new Error(code);
  const parsed = new Date(seconds);
  if (
    parsed.getUTCFullYear() !== Number(year) || parsed.getUTCMonth() + 1 !== Number(month) ||
    parsed.getUTCDate() !== Number(day) || parsed.getUTCHours() !== Number(hour) ||
    parsed.getUTCMinutes() !== Number(minute) || parsed.getUTCSeconds() !== Number(second)
  ) throw new Error(code);
  const micros = (fraction ?? '').padEnd(7, '0').slice(0, 6);
  return `${Math.trunc(seconds / 1000)}:${micros}`;
};

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
function readJson(file, boundary, maxBytes = 262144, asciiOnly = true) {
  const resolved = inside(file, boundary, 'INPUT_SCOPE'); assertNoReparse(resolved, boundary);
  const bytes = fs.readFileSync(resolved); if (bytes.length < 2 || bytes.length > maxBytes) throw new Error('INPUT_SIZE');
  if (asciiOnly && !/^[\x09\x0a\x0d\x20-\x7e]+$/.test(bytes.toString('latin1'))) throw new Error('INPUT_ASCII');
  let text; try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); } catch { throw new Error('INPUT_UTF8'); }
  let value; try { value = JSON.parse(text); } catch { throw new Error('INPUT_JSON'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('INPUT_ROOT');
  return { path: resolved, bytes, sha256: sha256(bytes), value };
}
function resolveRelative(relative, boundary, code) {
  if (typeof relative !== 'string' || relative.length < 3 || relative.includes('\\') || path.isAbsolute(relative) || relative.split('/').includes('..')) throw new Error(code);
  return inside(path.resolve(root, ...relative.split('/')), boundary, code);
}
function resolveApprovalReference(relative, code) {
  if (typeof relative !== 'string' || !/^runtime\/atlas\/[A-Za-z0-9._-]+\.json$/.test(relative)) throw new Error(code);
  const resolved = path.resolve(root, ...relative.split('/'));
  if (path.dirname(resolved).toLowerCase() !== runtimeRoot.toLowerCase()) throw new Error(code);
  return resolved;
}
function atlasRelative(file) { return path.relative(root, file).split(path.sep).join('/'); }
function canonicalAliasPath(decisionPath) {
  let stem=path.parse(decisionPath).name;
  for(const suffix of ['-operator-decision-request','-decision-request'])if(stem.endsWith(suffix)){stem=stem.slice(0,-suffix.length);break;}
  return path.join(path.dirname(decisionPath),`${stem}-scoped-approval-alias.json`);
}
const canonicalAuthorizationPath = aliasPath => path.join(path.dirname(aliasPath),`${path.parse(aliasPath).name}-authorization.json`);
const canonicalConsumptionPath = aliasPath => path.join(path.dirname(aliasPath),`${path.parse(aliasPath).name}-consumption.json`);
function timestamp(value, code) { canonicalInstant(value, code); const ms = Date.parse(value); if (!Number.isFinite(ms)) throw new Error(code); return ms; }
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
  if (a.decision_request?.sha256 !== decision.sha256 || resolveApprovalReference(a.decision_request?.path, 'ALIAS_DECISION_REFERENCE') !== decision.path) throw new Error('ALIAS_DECISION_BINDING');
  if (sha256(Buffer.from(d.exact_authorization_phrase ?? '', 'utf8')) !== a.decision_request?.exact_authorization_phrase_sha256) throw new Error('ALIAS_PHRASE_BINDING');
  if (z.schema !== 'atlas.scoped-approval-authorization.v1' || z.packet !== packet || z.status !== 'AUTHORIZED_SINGLE_USE' || z.single_use !== true || z.execution_authority !== true || z.originating_task_id !== originatingTaskId || z.approval_code !== a.approval_code || z.alias?.sha256 !== alias.sha256 || resolveApprovalReference(z.alias?.path, 'AUTHORIZATION_ALIAS_REFERENCE') !== alias.path || z.decision_request?.sha256 !== decision.sha256 || resolveApprovalReference(z.decision_request?.path, 'AUTHORIZATION_DECISION_REFERENCE') !== decision.path || z.intent_digest !== a.intent_digest) throw new Error('AUTHORIZATION_BINDING');
  if (c.schema !== 'atlas.scoped-approval-consumption.v1' || c.packet !== packet || c.status !== 'CONSUMED' || c.reusable !== false || c.max_effect_count !== maxEffectCount || c.authorization_sha256 !== authorization.sha256 || c.intent_digest !== a.intent_digest || !uuid4(c.execution_correlation_id)) throw new Error('CONSUMPTION_BINDING');
  const nowMs = now.getTime(), aliasIssued = timestamp(a.issued_at, 'ALIAS_TIME'), authorized = timestamp(z.authorized_at, 'AUTHORIZATION_TIME'), consumed = timestamp(c.consumed_at, 'CONSUMPTION_TIME'), expires = timestamp(a.expires_at, 'ALIAS_TIME');
  if (aliasIssued > authorized || authorized > consumed || consumed > nowMs + 5000 || expires <= nowMs || expires > aliasIssued + 86400000) throw new Error('APPROVAL_TIME');
  if (canonicalInstant(d.expires_at, 'DECISION_TIME') !== canonicalInstant(a.expires_at, 'ALIAS_TIME') || d.sealed_inputs?.execution_correlation_id !== c.execution_correlation_id) throw new Error('DECISION_EXECUTION_BINDING');
  const sealedKeys = ['execution_correlation_id','private_source_path','private_source_sha256','manifest_path','manifest_sha256','auth_apply_sha256','postverify_sha256','host_path','host_sha256','credential_safe_launcher_path','credential_safe_launcher_sha256','materializer_path','materializer_sha256','classifier_path','classifier_sha256','node_path','node_sha256','packet_merge_commit','jit_invocation_merge_commit','independent_review_checkpoint','prior_rollback_state_path','prior_rollback_receipt_sha256'];
  const effectKeys = ['execution_clusters','legacy_writer_fence_and_restore','master_migrations','auth_identity_edges','auth_user_imports','auth_existing_user_binds','auth_same_uuid_retained','profiles','player_rows','ai_rows','receipts','username_backfill_and_origin_contract','vault_key_create_and_rollback_delete','before_user_created_hook_activation','bounded_qa_and_cleanup','rollback_on_any_failed_gate','cutover','vercel_or_app_deployment','production_alias_change'];
  if (!exactKeys(d.sealed_inputs, sealedKeys) || !exactKeys(d.effect_ceiling, effectKeys)) throw new Error('DECISION_TUPLE_KEYS');
  const s = d.sealed_inputs, effects = d.effect_ceiling;
  for (const value of [s.private_source_sha256,s.manifest_sha256,s.auth_apply_sha256,s.postverify_sha256,s.host_sha256,s.credential_safe_launcher_sha256,s.materializer_sha256,s.classifier_sha256,s.node_sha256,s.prior_rollback_receipt_sha256]) if (!digest(value)) throw new Error('DECISION_TUPLE_DIGEST');
  if (!commit(s.packet_merge_commit) || !commit(s.jit_invocation_merge_commit) || typeof s.independent_review_checkpoint !== 'string' || !/^threadctx_[a-f0-9]{64}$/.test(s.independent_review_checkpoint)) throw new Error('DECISION_TUPLE_PROVENANCE');
  if (effects.execution_clusters !== 1 || effects.legacy_writer_fence_and_restore !== true || JSON.stringify(effects.master_migrations) !== JSON.stringify(['M1','M2','M3','M4']) || effects.username_backfill_and_origin_contract !== true || effects.vault_key_create_and_rollback_delete !== true || effects.before_user_created_hook_activation !== true || effects.bounded_qa_and_cleanup !== true || effects.rollback_on_any_failed_gate !== true || effects.cutover !== false || effects.vercel_or_app_deployment !== false || effects.production_alias_change !== false) throw new Error('DECISION_EFFECT_CONTRACT');
  for (const value of [effects.auth_identity_edges,effects.auth_user_imports,effects.auth_existing_user_binds,effects.auth_same_uuid_retained,effects.profiles,effects.player_rows,effects.ai_rows,effects.receipts]) if (!positiveInteger(value)) throw new Error('DECISION_EFFECT_COUNTS');
  if (effects.auth_identity_edges !== effects.auth_user_imports + effects.auth_existing_user_binds + effects.auth_same_uuid_retained || effects.auth_identity_edges > maxEffectCount) throw new Error('DECISION_AUTH_TOPOLOGY');
  const sourcePath = resolveRelative(s.private_source_path, packetRoot, 'SOURCE_PATH');
  const manifestPath = resolveRelative(s.manifest_path, packetRoot, 'MANIFEST_PATH');
  const predecessorPath = resolveRelative(s.prior_rollback_state_path, runtimeRoot, 'PREDECESSOR_PATH');
  const decisionHostPath = resolveRelative(s.host_path, path.dirname(hostPath), 'HOST_PATH');
  const decisionLauncherPath = resolveRelative(s.credential_safe_launcher_path, path.dirname(launcherPath), 'LAUNCHER_PATH');
  const decisionMaterializerPath = resolveRelative(s.materializer_path, path.dirname(materializerPath), 'MATERIALIZER_PATH');
  const decisionClassifierPath = resolveRelative(s.classifier_path, path.dirname(classifierPath), 'CLASSIFIER_PATH');
  const decisionNodePath = path.resolve(s.node_path ?? '');
  if (path.dirname(sourcePath).toLowerCase() !== packetRoot.toLowerCase() || !/^private-source(?:-[a-z0-9-]+)?\.json$/.test(path.basename(sourcePath))) throw new Error('SOURCE_PATH');
  if (path.basename(manifestPath) !== 'manifest.json' || !/^materialized-[a-z0-9-]+$/.test(path.basename(path.dirname(manifestPath)))) throw new Error('MANIFEST_PATH');
  if (decisionHostPath.toLowerCase() !== hostPath.toLowerCase() || decisionLauncherPath.toLowerCase() !== launcherPath.toLowerCase() || decisionMaterializerPath.toLowerCase() !== materializerPath.toLowerCase() || decisionClassifierPath.toLowerCase() !== classifierPath.toLowerCase() || decisionNodePath.toLowerCase() !== nodePath.toLowerCase()) throw new Error('CODE_PATH');
  if (!/^mazer-master-r017-terminal-rollback-[a-z0-9-]+\.json$/.test(path.basename(predecessorPath))) throw new Error('PREDECESSOR_PATH');
  const launcherSha = sha256(fs.readFileSync(launcherPath));
  if (s.credential_safe_launcher_sha256 !== launcherSha) throw new Error('DECISION_SEALED_HASHES');
  for (const [file, expected] of [[sourcePath,s.private_source_sha256],[manifestPath,s.manifest_sha256],[hostPath,s.host_sha256],[materializerPath,s.materializer_sha256],[classifierPath,s.classifier_sha256],[nodePath,s.node_sha256],[predecessorPath,s.prior_rollback_receipt_sha256]]) if (sha256(fs.readFileSync(file)) !== expected) throw new Error('SEALED_FILE_DIGEST');
  const source = readJson(sourcePath, packetRoot, 32_000_000, false).value, manifest = readJson(manifestPath, packetRoot, 262144).value;
  if (source.schema !== 'atlas.supabase.mazer-master-preparation-private-source.r017.v1' || source.packet !== packet || source.sql_sha256?.['auth-apply.sql'] !== s.auth_apply_sha256 || source.sql_sha256?.['postverify.sql'] !== s.postverify_sha256) throw new Error('SOURCE_CONTRACT');
  if (manifest.schema !== 'atlas.supabase.mazer-master-preparation-private-manifest.r017.v1' || manifest.packet !== packet || manifest.auth_counts?.final_edges !== effects.auth_identity_edges || manifest.auth_counts?.imports !== effects.auth_user_imports || manifest.auth_counts?.binds !== effects.auth_existing_user_binds || manifest.auth_counts?.retained_edges !== effects.auth_same_uuid_retained || manifest.app_counts?.profiles !== effects.profiles || manifest.app_counts?.player !== effects.player_rows || manifest.app_counts?.ai !== effects.ai_rows || manifest.app_counts?.receipts !== effects.receipts || manifest.receipt_conservation?.final !== effects.receipts) throw new Error('MANIFEST_COUNTS');
  const correlation = c.execution_correlation_id, successor = path.join(runtimeRoot, `mazer-master-r017-execution-${correlation}.json`);
  if (fs.existsSync(successor)) throw new Error('SUCCESSOR_EXISTS');
  const issuedAt = formatO(now), envelope = {
    schema: 'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v3', packet,
    decision_request_path: decision.path, decision_request_sha256: decision.sha256,
    approval_alias_path: alias.path, approval_alias_sha256: alias.sha256,
    approval_authorization_path: authorization.path, approval_authorization_sha256: authorization.sha256,
    approval_consumption_path: consumption.path, approval_consumption_sha256: consumption.sha256,
    approval_expires_at: a.expires_at,
    predecessor_state_path: predecessorPath, predecessor_state_sha256: s.prior_rollback_receipt_sha256,
    execution_correlation_id: correlation,
    private_source_path: sourcePath, private_source_sha256: s.private_source_sha256,
    private_manifest_path: manifestPath, private_manifest_sha256: s.manifest_sha256,
    successor_state_path: successor,
    host_path: hostPath, host_sha256: s.host_sha256,
    launcher_path: launcherPath, launcher_sha256: launcherSha,
    materializer_path: materializerPath, materializer_sha256: s.materializer_sha256,
    classifier_path: classifierPath, classifier_sha256: s.classifier_sha256,
    node_path: nodePath, node_sha256: s.node_sha256,
    terminal_final_identity_edges: effects.auth_identity_edges, terminal_profiles: effects.profiles,
    terminal_player: effects.player_rows, terminal_ai: effects.ai_rows, terminal_receipts: effects.receipts,
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
