import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const launcher = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_preparation_credential_safe_r017.ps1');
const sealer = path.join(root, 'ops/atlas/seal_supabase_mazer_master_preparation_credential_safe_invocation_r017.mjs');
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
for (const token of ['launcher-invocation.r017.v2','decision_request_sha256','approval_consumption_sha256','INVOCATION_NOT_YET_VALID','INVOCATION_EXPIRED','Read-JsonSnapshot']) assert.ok(launcherText.includes(token), `MISSING_JIT_GATE:${token}`);
assert.doesNotMatch(launcherText, /PrivateSourceOverride|StatePathOverride|ExpectedSourceShaOverride/);

let productionAdversaries = 0;
if ([source, manifest, predecessor, host].every(file => fs.existsSync(file))) {
  assert.equal(sha(fs.readFileSync(source)), sourceSha);
  assert.equal(sha(fs.readFileSync(manifest)), manifestSha);
  assert.equal(sha(fs.readFileSync(predecessor)), predecessorSha);
  assert.equal(sha(fs.readFileSync(host)), hostSha);
  const launcherSha = sha(fs.readFileSync(launcher));
  const paths = [], packet = 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001', task = '019fa791-8d17-7c83-9c61-3e3c687e9dd7', target = 'supabase:geknvnrmktchljnyddwp/public+bxtcuhkotumitoqtrcej/mazer';
  const o = date => date.toISOString().replace('Z','0000Z');
  const write = (file, value) => { const bytes=Buffer.from(`${JSON.stringify(value,null,2)}\n`); fs.writeFileSync(file,bytes,{flag:'wx'}); paths.push(file); return {file,bytes,sha:sha(bytes)}; };
  const lineage = (name, { aliasIssued, authorized, consumed, expires, envelopeIssued = new Date(), notBefore = consumed, successorExists = false }) => {
    const correlation=crypto.randomUUID(), phrase=`AUTHORIZE ${name} ${correlation}`, intent=`sha256:${sha(Buffer.from(`intent:${name}:${correlation}`))}`;
    const prefix=`.launcher-test-${name}-${process.pid}-${Date.now()}`, decisionPath=path.join(runtime,`${prefix}-decision-request.json`), aliasPath=path.join(runtime,`${prefix}-scoped-approval-alias.json`), authPath=path.join(runtime,`${prefix}-scoped-approval-alias-authorization.json`), consumptionPath=path.join(runtime,`${prefix}-scoped-approval-alias-consumption.json`);
    const decision=write(decisionPath,{schema:'atlas.operator-decision-request.v1',packet,status:'AWAITING_OPERATOR_DECISION',execution_authority:false,expires_at:o(expires),sealed_inputs:{execution_correlation_id:correlation,private_source_sha256:sourceSha,manifest_sha256:manifestSha,host_sha256:hostSha,credential_safe_launcher_sha256:launcherSha},exact_authorization_phrase:phrase});
    const alias=write(aliasPath,{allowed_effect:{effect_class:'supabase_protected_master_preparation',max_effect_count:20,target},approval_code:'R017-TEST-TEST-TEST-TEST',decision_request:{exact_authorization_phrase_sha256:sha(Buffer.from(phrase)),path:path.relative(root,decisionPath).split(path.sep).join('/'),sha256:decision.sha},execution_authority:false,expected_operator_response:'APPROVE R017-TEST-TEST-TEST-TEST',expires_at:o(expires),intent_digest:intent,issued_at:o(aliasIssued),originating_task_id:task,packet,schema:'atlas.scoped-approval-alias.v1',semantic_objective:'jit-test',single_use:true,status:'OPEN'});
    const auth=write(authPath,{alias:{path:path.relative(root,aliasPath).split(path.sep).join('/'),sha256:alias.sha},allowed_effect:{effect_class:'supabase_protected_master_preparation',max_effect_count:20,target},approval_code:'R017-TEST-TEST-TEST-TEST',authorization_digest:`sha256:${sha(Buffer.from(`auth:${name}`))}`,authorized_at:o(authorized),decision_request:{exact_authorization_phrase_sha256:sha(Buffer.from(phrase)),path:path.relative(root,decisionPath).split(path.sep).join('/'),sha256:decision.sha},execution_authority:true,full_phrase_replay_required:false,intent_digest:intent,originating_task_id:task,packet,schema:'atlas.scoped-approval-authorization.v1',single_use:true,status:'AUTHORIZED_SINGLE_USE'});
    const consumption=write(consumptionPath,{approval_code:'R017-TEST-TEST-TEST-TEST',authorization_sha256:auth.sha,consumed_at:o(consumed),consumption_digest:`sha256:${sha(Buffer.from(`consume:${name}`))}`,execution_correlation_id:correlation,intent_digest:intent,max_effect_count:20,packet,reusable:false,schema:'atlas.scoped-approval-consumption.v1',status:'CONSUMED'});
    const successor=path.join(runtime,`mazer-master-r017-execution-${correlation}.json`);
    if(successorExists){fs.writeFileSync(successor,'{}\n',{flag:'wx'});paths.push(successor);}
    return { correlation, decision, alias, auth, consumption, successor, envelope:{schema:'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v2',packet,decision_request_path:decisionPath,decision_request_sha256:decision.sha,approval_alias_path:aliasPath,approval_alias_sha256:alias.sha,approval_authorization_path:authPath,approval_authorization_sha256:auth.sha,approval_consumption_path:consumptionPath,approval_consumption_sha256:consumption.sha,approval_expires_at:o(expires),predecessor_correlation_id:'a7db1fd5-a165-43e6-a9a8-c267233005b2',predecessor_state_path:predecessor,predecessor_state_sha256:predecessorSha,execution_correlation_id:correlation,private_source_path:source,private_source_sha256:sourceSha,private_manifest_path:manifest,private_manifest_sha256:manifestSha,successor_state_path:successor,host_path:host,host_sha256:hostSha,launcher_path:launcher,launcher_sha256:launcherSha,not_before:o(notBefore),issued_at:o(envelopeIssued),expires_at:o(expires)}};
  };
  const validate = (shell, name, value, expectedStatus, expectedCategory) => {
    const file = path.join(packetRoot, `launcher-invocation-${value.execution_correlation_id}.json`);
    const bytes = Buffer.from(`${JSON.stringify(value)}\n`);
    fs.writeFileSync(file, bytes, { flag: 'wx' }); paths.push(file);
    const result = runLauncher(shell, ['-ValidateInvocationOnly', '-InvocationPath', file, '-ExpectedInvocationSha256', sha(bytes)]);
    assert.equal(result.status, expectedStatus, `${result.stderr}\n${result.stdout}`);
    if (expectedCategory) assert.equal(result.receipt.category, expectedCategory);
    return result;
  };
  try {
    for(const shell of ['pwsh.exe','powershell.exe']){
      const now=new Date(), delayed=lineage(`delayed-${shell}`,{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),envelopeIssued:now});
      assert.equal(validate(shell,'delayed',delayed.envelope,0).receipt.result,'PASS_R017_LAUNCHER_INVOCATION_BOUND');
      const exact=lineage(`exact-expiry-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now)});validate(shell,'exact-expiry',exact.envelope,2,'INVOCATION_EXPIRED');
      const expired=lineage(`post-expiry-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now-1000)});validate(shell,'post-expiry',expired.envelope,2,'INVOCATION_EXPIRED');
      const future=lineage(`future-${shell}`,{aliasIssued:now,authorized:new Date(now.getTime()+1000),consumed:new Date(now.getTime()+2000),expires:new Date(now.getTime()+3600000),envelopeIssued:new Date(now.getTime()+60000),notBefore:new Date(now.getTime()+2000)});validate(shell,'future',future.envelope,2,'INVOCATION_NOT_YET_VALID');
      const replay=lineage(`replay-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),successorExists:true});validate(shell,'replay',replay.envelope,2,'SUCCESSOR_STATE_BINDING');
      for(const [kind,key] of [['alias','approval_alias_path'],['authorization','approval_authorization_path'],['consumption','approval_consumption_path']]){
        const wrong=lineage(`wrong-${kind}-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)}), original=wrong.envelope[key], copy=path.join(runtime,`.launcher-test-wrong-${kind}-${crypto.randomUUID()}.json`);fs.copyFileSync(original,copy,fs.constants.COPYFILE_EXCL);paths.push(copy);validate(shell,`wrong-${kind}`,{...wrong.envelope,[key]:copy},2,'APPROVAL_PATH_BINDING');
      }
      productionAdversaries += 8;
    }
    const now=new Date(), sealed=lineage('sealer-valid',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)}), output=path.join(packetRoot,`launcher-invocation-${sealed.correlation}.json`);
    const sealRun=run('node',[sealer,sealed.decision.file,sealed.alias.file,sealed.auth.file,sealed.consumption.file,output]);assert.equal(sealRun.status,0,`${sealRun.stderr}\n${sealRun.stdout}`);paths.push(output);assert.equal(sealRun.receipt.result,'PASS_R017_INVOCATION_SEALED');assert.equal(sealRun.receipt.execution_correlation_id,sealed.correlation);assert.equal(sealRun.receipt.external_calls,0);
    const second=run('node',[sealer,sealed.decision.file,sealed.alias.file,sealed.auth.file,sealed.consumption.file,output]);assert.equal(second.status,2);assert.equal(second.receipt.category,'OUTPUT_EXISTS');
    for(const [kind,index,category] of [['alias',1,'ALIAS_PATH'],['authorization',2,'AUTHORIZATION_PATH'],['consumption',3,'CONSUMPTION_PATH']]){const wrong=path.join(runtime,`.launcher-test-sealer-wrong-${kind}-${crypto.randomUUID()}.json`),args=[sealed.decision.file,sealed.alias.file,sealed.auth.file,sealed.consumption.file];fs.copyFileSync(args[index],wrong,fs.constants.COPYFILE_EXCL);paths.push(wrong);args[index]=wrong;const rejected=run('node',[sealer,...args,path.join(packetRoot,`launcher-invocation-${sealed.correlation}.json`)]);assert.equal(rejected.status,2);assert.equal(rejected.receipt.category,category);}
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
