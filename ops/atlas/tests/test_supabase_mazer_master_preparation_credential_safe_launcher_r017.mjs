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
const source = path.join(packetRoot, 'private-source-pr201-final-71884498-20260826.json');
const manifest = path.join(packetRoot, 'materialized-pr201-final-20260826/manifest.json');
const predecessor = path.join(runtime, 'mazer-master-r017-terminal-rollback-20260826-212608.json');
const materializer = path.join(root, 'ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs');
const classifier = path.join(root, 'ops/atlas/classify_supabase_mazer_master_cutover_data_fence_r001.mjs');
const fence = path.join(root, 'ops/atlas/invoke_supabase_mazer_master_cutover_data_fence_r001.ps1');
const nodePath = fs.realpathSync.native(process.execPath);
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const sourceSha = fs.existsSync(source) ? sha(fs.readFileSync(source)) : null;
const manifestSha = fs.existsSync(manifest) ? sha(fs.readFileSync(manifest)) : null;
const predecessorSha = fs.existsSync(predecessor) ? sha(fs.readFileSync(predecessor)) : null;
const hostSha = sha(fs.readFileSync(host));
const materializerSha = sha(fs.readFileSync(materializer));
const classifierSha = sha(fs.readFileSync(classifier));
const fenceSha = sha(fs.readFileSync(fence));
const nodeSha = sha(fs.readFileSync(nodePath));

function run(shell, args, env = process.env) {
  const result = spawnSync(shell, args, { cwd: root, env, encoding: 'utf8', windowsHide: true, timeout: 60_000 });
  return { ...result, receipt: result.stdout.trim() ? JSON.parse(result.stdout.trim()) : null };
}
function runLauncher(shell, args, env = process.env) {
  return run(shell, ['-NoLogo', '-NoProfile', '-NonInteractive', ...(shell === 'powershell.exe' ? ['-ExecutionPolicy', 'Bypass'] : []), '-File', launcher, ...args], env);
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
  const replacementRace = runLauncher(shell, ['-LocalHostReplacementAdversary']);
  assert.equal(replacementRace.status, 0, replacementRace.stderr);
  assert.equal(replacementRace.receipt.result, 'PASS_R017_SAME_BUFFER_HOST_REPLACEMENT_ADVERSARY');
  assert.equal(replacementRace.receipt.replacement_executed, false);
  assert.equal(replacementRace.receipt.credential_reads, 0);
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
  'DECISION_TUPLE_KEYS', 'TERMINAL_DENOMINATORS', 'SEALED_PATH_BINDING',
  'SUCCESSOR_STATE_BINDING', 'PREDECESSOR_EFFECT_STATE', 'INVOCATION_KEYS',
  'SUPABASE_ACCESS_TOKEN', 'ATLAS_MAZER_LEGACY_DATABASE_URL', 'ATLAS_MAZER_MASTER_DATABASE_URL',
  'Read-ManagementToken', 'Read-ProjectPassword', 'Invoke-Child', 'ProtectedChildStarted',
  'Convert-ProtectedChildReceipt', 'Get-VerifiedHostBootstrapEncoded', 'Invoke-VerifiedHostChild',
  'ATLAS_R017_VERIFIED_HOST_SHA256', 'external_effects_unknown=[bool]$script:ProtectedChildStarted'
]) assert.ok(launcherText.includes(token), `MISSING_LAUNCHER_GATE:${token}`);
for (const token of ['launcher-invocation.r017.v3','decision_request_sha256','approval_consumption_sha256','terminal_final_identity_edges','INVOCATION_NOT_YET_VALID','INVOCATION_EXPIRED','Read-JsonSnapshot']) assert.ok(launcherText.includes(token), `MISSING_JIT_GATE:${token}`);
for (const token of ['materializer_path','materializer_sha256','classifier_path','classifier_sha256','fence_path','fence_sha256','node_path','node_sha256','ATLAS_R017_VERIFIED_MATERIALIZER_PATH','ATLAS_R017_VERIFIED_CLASSIFIER_PATH','ATLAS_R017_VERIFIED_FENCE_PATH','ATLAS_R017_VERIFIED_NODE_PATH']) assert.ok(launcherText.includes(token), `MISSING_PORTABLE_MATERIALIZER_GATE:${token}`);
for (const stale of ['r017-node-shim-reviewed2','4053ed27750a4e4593959a7caa7ea2562ebd56912852454547f12889a9b8d3c9']) assert.ok(!launcherText.includes(stale), `STALE_NODE_SHIM:${stale}`);
for (const stale of ['71884498b45cf0ab04cb71d6533bf9ddef6426a06f92cf77e67242eaf9665e60','dccfc0bb4e9cf0bc6904a7002ec8bc7acc8d2f392d76a62eb69b99872ad9d1de','d3ec9c210e031ebd887e5f643939ebd584efe218e0db2b346586392bc280453d','final_identity_edges-ne19','player-ne16','ai-ne16']) assert.ok(!launcherText.includes(stale), `STALE_TUPLE:${stale}`);
assert.doesNotMatch(launcherText, /PrivateSourceOverride|StatePathOverride|ExpectedSourceShaOverride/);

let productionAdversaries = 0;
let nodeIndirectionPasses = 0;
if ([source, manifest, predecessor, host].every(file => fs.existsSync(file))) {
  assert.equal(sha(fs.readFileSync(source)), sourceSha);
  assert.equal(sha(fs.readFileSync(manifest)), manifestSha);
  assert.equal(sha(fs.readFileSync(predecessor)), predecessorSha);
  assert.equal(sha(fs.readFileSync(host)), hostSha);
  const launcherSha = sha(fs.readFileSync(launcher));
  const paths = [], directories = [], packet = 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001', task = '019fa791-8d17-7c83-9c61-3e3c687e9dd7', target = 'supabase:geknvnrmktchljnyddwp/public+bxtcuhkotumitoqtrcej/mazer';
  const nodeJunction=path.join(path.dirname(packetRoot),`.launcher-test-node-junction-${crypto.randomUUID()}`);fs.symlinkSync(path.dirname(nodePath),nodeJunction,'junction');directories.push(nodeJunction);
  const o = date => date.toISOString().replace('Z','000Z');
  const write = (file, value) => { const bytes=Buffer.from(`${JSON.stringify(value,null,2)}\n`); fs.writeFileSync(file,bytes,{flag:'wx'}); paths.push(file); return {file,bytes,sha:sha(bytes)}; };
  const baseTuple={source,sourceSha,manifest,manifestSha,hostSha,predecessor,predecessorSha,authApplySha:JSON.parse(fs.readFileSync(source,'utf8')).sql_sha256['auth-apply.sql'],postverifySha:JSON.parse(fs.readFileSync(source,'utf8')).sql_sha256['postverify.sql'],counts:{edges:19,imports:3,binds:14,retained:2,profiles:13,player:16,ai:16,receipts:1887}};
  const evolutionId=crypto.randomUUID(), evolutionSource=path.join(packetRoot,`private-source-pr203-${evolutionId}.json`), evolutionDirectory=path.join(packetRoot,`materialized-pr203-${evolutionId}`), evolutionManifest=path.join(evolutionDirectory,'manifest.json'), evolutionAuth=sha(Buffer.from('auth-pr203')), evolutionPost=sha(Buffer.from('post-pr203'));
  fs.mkdirSync(evolutionDirectory);directories.push(evolutionDirectory);
  const evolutionSourceWritten=write(evolutionSource,{schema:'atlas.supabase.mazer-master-preparation-private-source.r017.v1',packet,sql_sha256:{'auth-apply.sql':evolutionAuth,'postverify.sql':evolutionPost}});
  const evolutionManifestWritten=write(evolutionManifest,{schema:'atlas.supabase.mazer-master-preparation-private-manifest.r017.v1',packet,auth_counts:{final_edges:20,imports:4,binds:14,retained_edges:2},app_counts:{profiles:13,player:17,ai:17,receipts:1887},receipt_conservation:{final:1887}});
  const evolutionTuple={source:evolutionSource,sourceSha:evolutionSourceWritten.sha,manifest:evolutionManifest,manifestSha:evolutionManifestWritten.sha,hostSha,predecessor,predecessorSha,authApplySha:evolutionAuth,postverifySha:evolutionPost,counts:{edges:20,imports:4,binds:14,retained:2,profiles:13,player:17,ai:17,receipts:1887}};
  const lineage = (name, { aliasIssued, authorized, consumed, expires, envelopeIssued = new Date(), notBefore = consumed, successorExists = false, tuple = baseTuple, decisionExpiresRaw, aliasExpiresRaw, approvalReferenceMode = 'canonical', sealedOverrides = {} }) => {
    const correlation=crypto.randomUUID(), phrase=`AUTHORIZE ${name} ${correlation}`, intent=`sha256:${sha(Buffer.from(`intent:${name}:${correlation}`))}`;
    const prefix=`.launcher-test-${name}-${process.pid}-${Date.now()}`, decisionPath=path.join(runtime,`${prefix}-decision-request.json`), aliasPath=path.join(runtime,`${prefix}-scoped-approval-alias.json`), authPath=path.join(runtime,`${prefix}-scoped-approval-alias-authorization.json`), consumptionPath=path.join(runtime,`${prefix}-scoped-approval-alias-consumption.json`);
    const rel=file=>path.relative(root,file).split(path.sep).join('/');
    const approvalRef=file=>approvalReferenceMode === 'absolute' ? path.resolve(file) : rel(file);
    const sealed_inputs={execution_correlation_id:correlation,private_source_path:rel(tuple.source),private_source_sha256:tuple.sourceSha,manifest_path:rel(tuple.manifest),manifest_sha256:tuple.manifestSha,auth_apply_sha256:tuple.authApplySha,postverify_sha256:tuple.postverifySha,host_path:rel(host),host_sha256:tuple.hostSha,credential_safe_launcher_path:rel(launcher),credential_safe_launcher_sha256:launcherSha,materializer_path:rel(materializer),materializer_sha256:materializerSha,classifier_path:rel(classifier),classifier_sha256:classifierSha,fence_path:rel(fence),fence_sha256:fenceSha,node_path:nodePath,node_sha256:nodeSha,packet_merge_commit:'1'.repeat(40),jit_invocation_merge_commit:'2'.repeat(40),independent_review_checkpoint:`threadctx_${'3'.repeat(64)}`,prior_rollback_state_path:rel(tuple.predecessor),prior_rollback_receipt_sha256:tuple.predecessorSha};
    Object.assign(sealed_inputs,sealedOverrides);
    const effect_ceiling={execution_clusters:1,legacy_writer_fence_and_restore:true,master_migrations:['M1','M2','M3','M4'],auth_identity_edges:tuple.counts.edges,auth_user_imports:tuple.counts.imports,auth_existing_user_binds:tuple.counts.binds,auth_same_uuid_retained:tuple.counts.retained,profiles:tuple.counts.profiles,player_rows:tuple.counts.player,ai_rows:tuple.counts.ai,receipts:tuple.counts.receipts,username_backfill_and_origin_contract:true,vault_key_create_and_rollback_delete:true,before_user_created_hook_activation:true,bounded_qa_and_cleanup:true,rollback_on_any_failed_gate:true,cutover:false,vercel_or_app_deployment:false,production_alias_change:false};
    const decisionExpiry=decisionExpiresRaw??o(expires), aliasExpiry=aliasExpiresRaw??o(expires);
    const decision=write(decisionPath,{schema:'atlas.operator-decision-request.v1',packet,status:'AWAITING_OPERATOR_DECISION',execution_authority:false,expires_at:decisionExpiry,sealed_inputs,effect_ceiling,exact_authorization_phrase:phrase});
    const alias=write(aliasPath,{allowed_effect:{effect_class:'supabase_protected_master_preparation',max_effect_count:20,target},approval_code:'R017-TEST-TEST-TEST-TEST',decision_request:{exact_authorization_phrase_sha256:sha(Buffer.from(phrase)),path:approvalRef(decisionPath),sha256:decision.sha},execution_authority:false,expected_operator_response:'APPROVE R017-TEST-TEST-TEST-TEST',expires_at:aliasExpiry,intent_digest:intent,issued_at:o(aliasIssued),originating_task_id:task,packet,schema:'atlas.scoped-approval-alias.v1',semantic_objective:'jit-test',single_use:true,status:'OPEN'});
    const auth=write(authPath,{alias:{path:approvalRef(aliasPath),sha256:alias.sha},allowed_effect:{effect_class:'supabase_protected_master_preparation',max_effect_count:20,target},approval_code:'R017-TEST-TEST-TEST-TEST',authorization_digest:`sha256:${sha(Buffer.from(`auth:${name}`))}`,authorized_at:o(authorized),decision_request:{exact_authorization_phrase_sha256:sha(Buffer.from(phrase)),path:approvalRef(decisionPath),sha256:decision.sha},execution_authority:true,full_phrase_replay_required:false,intent_digest:intent,originating_task_id:task,packet,schema:'atlas.scoped-approval-authorization.v1',single_use:true,status:'AUTHORIZED_SINGLE_USE'});
    const consumption=write(consumptionPath,{approval_code:'R017-TEST-TEST-TEST-TEST',authorization_sha256:auth.sha,consumed_at:o(consumed),consumption_digest:`sha256:${sha(Buffer.from(`consume:${name}`))}`,execution_correlation_id:correlation,intent_digest:intent,max_effect_count:20,packet,reusable:false,schema:'atlas.scoped-approval-consumption.v1',status:'CONSUMED'});
    const successor=path.join(runtime,`mazer-master-r017-execution-${correlation}.json`);
    if(successorExists){fs.writeFileSync(successor,'{}\n',{flag:'wx'});paths.push(successor);}
    return { correlation, decision, alias, auth, consumption, successor, envelope:{schema:'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v3',packet,decision_request_path:decisionPath,decision_request_sha256:decision.sha,approval_alias_path:aliasPath,approval_alias_sha256:alias.sha,approval_authorization_path:authPath,approval_authorization_sha256:auth.sha,approval_consumption_path:consumptionPath,approval_consumption_sha256:consumption.sha,approval_expires_at:aliasExpiry,predecessor_state_path:tuple.predecessor,predecessor_state_sha256:tuple.predecessorSha,execution_correlation_id:correlation,private_source_path:tuple.source,private_source_sha256:tuple.sourceSha,private_manifest_path:tuple.manifest,private_manifest_sha256:tuple.manifestSha,successor_state_path:successor,host_path:host,host_sha256:tuple.hostSha,launcher_path:launcher,launcher_sha256:launcherSha,materializer_path:materializer,materializer_sha256:materializerSha,classifier_path:classifier,classifier_sha256:classifierSha,fence_path:fence,fence_sha256:fenceSha,node_path:nodePath,node_sha256:nodeSha,terminal_final_identity_edges:tuple.counts.edges,terminal_profiles:tuple.counts.profiles,terminal_player:tuple.counts.player,terminal_ai:tuple.counts.ai,terminal_receipts:tuple.counts.receipts,not_before:o(notBefore),issued_at:o(envelopeIssued),expires_at:aliasExpiry}};
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
      const evolved=lineage(`pr203-evolution-${shell}`,{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),envelopeIssued:now,tuple:evolutionTuple});
      assert.equal(validate(shell,'pr203-evolution',evolved.envelope,0).receipt.result,'PASS_R017_LAUNCHER_INVOCATION_BOUND');
      const evolvedBytes=Buffer.from(`${JSON.stringify(evolved.envelope)}\n`), evolvedFile=path.join(packetRoot,`launcher-invocation-${evolved.correlation}.json`), productionProbe=runLauncher(shell,['-LocalProductionShapeProbe','-InvocationPath',evolvedFile,'-ExpectedInvocationSha256',sha(evolvedBytes)]);
      assert.equal(productionProbe.status,0,`${productionProbe.stderr}\n${productionProbe.stdout}`);assert.equal(productionProbe.receipt.result,'PASS_R017_CREDENTIAL_SAFE_PRODUCTION_SHAPE_SENTINEL');assert.equal(productionProbe.receipt.execution_correlation_id,evolved.correlation);assert.equal(productionProbe.receipt.credential_reads,0);
      const indirect=lineage(`node-indirection-${shell}`,{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),envelopeIssued:now,tuple:evolutionTuple}), indirectBytes=Buffer.from(`${JSON.stringify(indirect.envelope)}\n`), indirectFile=path.join(packetRoot,`launcher-invocation-${indirect.correlation}.json`);fs.writeFileSync(indirectFile,indirectBytes,{flag:'wx'});paths.push(indirectFile);const indirectRun=runLauncher(shell,['-ValidateInvocationOnly','-InvocationPath',indirectFile,'-ExpectedInvocationSha256',sha(indirectBytes)],{...process.env,PATH:`${nodeJunction}${path.delimiter}${process.env.PATH}`});assert.equal(indirectRun.status,0,`${indirectRun.stderr}\n${indirectRun.stdout}`);assert.equal(indirectRun.receipt.result,'PASS_R017_LAUNCHER_INVOCATION_BOUND');nodeIndirectionPasses++;
      const exact=lineage(`exact-expiry-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now)});validate(shell,'exact-expiry',exact.envelope,2,'INVOCATION_EXPIRED');
      const expired=lineage(`post-expiry-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now-1000)});validate(shell,'post-expiry',expired.envelope,2,'INVOCATION_EXPIRED');
      const future=lineage(`future-${shell}`,{aliasIssued:now,authorized:new Date(now.getTime()+600000),consumed:new Date(now.getTime()+601000),expires:new Date(now.getTime()+3600000),envelopeIssued:new Date(now.getTime()+602000),notBefore:new Date(now.getTime()+601000)});validate(shell,'future',future.envelope,2,'INVOCATION_NOT_YET_VALID');
      const replay=lineage(`replay-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),successorExists:true});validate(shell,'replay',replay.envelope,2,'SUCCESSOR_STATE_BINDING');
      const absoluteApprovalReference=lineage(`absolute-approval-reference-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),approvalReferenceMode:'absolute'});validate(shell,'absolute-approval-reference',absoluteApprovalReference.envelope,2,'ALIAS_REFERENCE');
      for(const [kind,raw] of [['day','2026-02-30T00:00:00.000000Z'],['month','2026-13-01T00:00:00.000000Z'],['hour','2026-01-01T25:00:00.000000Z']]){
        const invalid=lineage(`invalid-${kind}-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),decisionExpiresRaw:raw});
        validate(shell,`invalid-${kind}`,invalid.envelope,2,'APPROVAL_TIMESTAMP');
      }
      for(const [kind,key] of [['alias','approval_alias_path'],['authorization','approval_authorization_path'],['consumption','approval_consumption_path']]){
        const wrong=lineage(`wrong-${kind}-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)}), original=wrong.envelope[key], copy=path.join(runtime,`.launcher-test-wrong-${kind}-${crypto.randomUUID()}.json`);fs.copyFileSync(original,copy,fs.constants.COPYFILE_EXCL);paths.push(copy);validate(shell,`wrong-${kind}`,{...wrong.envelope,[key]:copy},2,'APPROVAL_PATH_BINDING');
      }
      const wrongDecisionHash=lineage(`wrong-decision-hash-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'wrong-decision-hash',{...wrongDecisionHash.envelope,decision_request_sha256:'0'.repeat(64)},2,'APPROVAL_FILE_DIGEST');
      const wrongAuthorizationHash=lineage(`wrong-authorization-hash-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'wrong-authorization-hash',{...wrongAuthorizationHash.envelope,approval_authorization_sha256:'0'.repeat(64)},2,'APPROVAL_FILE_DIGEST');
      const staleSourceHash=lineage(`stale-source-hash-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-source-hash',{...staleSourceHash.envelope,private_source_sha256:'9326145071e2e067286e6460d06187d89d3bdc6b82c202b2cbea2f313f0b35ae'},2,'SEALED_FILE_DIGEST_DRIFT');
      const staleSourcePath=lineage(`stale-source-path-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)}), staleSourceCopy=path.join(packetRoot,`.launcher-test-stale-source-${crypto.randomUUID()}.json`);fs.linkSync(source,staleSourceCopy);paths.push(staleSourceCopy);validate(shell,'stale-source-path',{...staleSourcePath.envelope,private_source_path:staleSourceCopy},2,'SEALED_PATH_BINDING');
      const staleCount=lineage(`stale-terminal-count-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-terminal-count',{...staleCount.envelope,terminal_player:17},2,'TERMINAL_DENOMINATORS');
      const stalePredecessorPath=lineage(`stale-predecessor-path-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)}), stalePredecessorCopy=path.join(runtime,`.launcher-test-stale-predecessor-${crypto.randomUUID()}.json`);fs.linkSync(predecessor,stalePredecessorCopy);paths.push(stalePredecessorCopy);validate(shell,'stale-predecessor-path',{...stalePredecessorPath.envelope,predecessor_state_path:stalePredecessorCopy},2,'PREDECESSOR_PATH_BINDING');
      const stalePredecessorSha=lineage(`stale-predecessor-sha-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-predecessor-sha',{...stalePredecessorSha.envelope,predecessor_state_sha256:'5e01271273a910d861c1fb0712ac7d48a8b565a971f6a270cf6fe8409138a0d9'},2,'SEALED_FILE_DIGEST_DRIFT');
      const staleMaterializer=lineage(`stale-materializer-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-materializer',{...staleMaterializer.envelope,materializer_sha256:'0'.repeat(64)},2,'SEALED_FILE_DIGEST_DRIFT');
      const staleClassifier=lineage(`stale-classifier-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-classifier',{...staleClassifier.envelope,classifier_sha256:'0'.repeat(64)},2,'SEALED_FILE_DIGEST_DRIFT');
      const staleFence=lineage(`stale-fence-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-fence',{...staleFence.envelope,fence_sha256:'0'.repeat(64)},2,'SEALED_FILE_DIGEST_DRIFT');
      const wrongFencePath=lineage(`wrong-fence-path-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'wrong-fence-path',{...wrongFencePath.envelope,fence_path:classifier,fence_sha256:classifierSha},2,'HOST_PATH_BINDING');
      const staleDecisionFence=lineage(`stale-decision-fence-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),sealedOverrides:{fence_sha256:'0'.repeat(64)}});validate(shell,'stale-decision-fence',staleDecisionFence.envelope,2,'DECISION_EXECUTION_BINDING');
      const wrongDecisionFencePath=lineage(`wrong-decision-fence-path-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),sealedOverrides:{fence_path:path.relative(root,classifier).split(path.sep).join('/'),fence_sha256:classifierSha}});validate(shell,'wrong-decision-fence-path',wrongDecisionFencePath.envelope,2,'DECISION_EXECUTION_BINDING');
      const staleNode=lineage(`stale-node-${shell}`,{aliasIssued:new Date(now-3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)});validate(shell,'stale-node',{...staleNode.envelope,node_sha256:'0'.repeat(64)},2,'NODE_RUNTIME_DIGEST');
      productionAdversaries += 24;
    }
    const now=new Date(), sealed=lineage('sealer-valid',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000)}), output=path.join(packetRoot,`launcher-invocation-${sealed.correlation}.json`);
    const sealRun=run('node',[sealer,sealed.decision.file,sealed.alias.file,sealed.auth.file,sealed.consumption.file,output]);assert.equal(sealRun.status,0,`${sealRun.stderr}\n${sealRun.stdout}`);paths.push(output);assert.equal(sealRun.receipt.result,'PASS_R017_INVOCATION_SEALED');assert.equal(sealRun.receipt.execution_correlation_id,sealed.correlation);assert.equal(sealRun.receipt.external_calls,0);
    const second=run('node',[sealer,sealed.decision.file,sealed.alias.file,sealed.auth.file,sealed.consumption.file,output]);assert.equal(second.status,2);assert.equal(second.receipt.category,'OUTPUT_EXISTS');
    const evolvedSealed=lineage('sealer-pr203-evolution',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),tuple:evolutionTuple}), evolvedOutput=path.join(packetRoot,`launcher-invocation-${evolvedSealed.correlation}.json`), evolvedRun=run('node',[sealer,evolvedSealed.decision.file,evolvedSealed.alias.file,evolvedSealed.auth.file,evolvedSealed.consumption.file,evolvedOutput]);assert.equal(evolvedRun.status,0,`${evolvedRun.stderr}\n${evolvedRun.stdout}`);paths.push(evolvedOutput);assert.equal(evolvedRun.receipt.result,'PASS_R017_INVOCATION_SEALED');
    const staleFenceSealed=lineage('sealer-stale-fence',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),sealedOverrides:{fence_sha256:'0'.repeat(64)}}), staleFenceOutput=path.join(packetRoot,`launcher-invocation-${staleFenceSealed.correlation}.json`), staleFenceRun=run('node',[sealer,staleFenceSealed.decision.file,staleFenceSealed.alias.file,staleFenceSealed.auth.file,staleFenceSealed.consumption.file,staleFenceOutput]);assert.equal(staleFenceRun.status,2);assert.equal(staleFenceRun.receipt.category,'SEALED_FILE_DIGEST');assert.equal(fs.existsSync(staleFenceOutput),false);
    const wrongFenceSealed=lineage('sealer-wrong-fence-path',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),sealedOverrides:{fence_path:path.relative(root,classifier).split(path.sep).join('/'),fence_sha256:classifierSha}}), wrongFenceOutput=path.join(packetRoot,`launcher-invocation-${wrongFenceSealed.correlation}.json`), wrongFenceRun=run('node',[sealer,wrongFenceSealed.decision.file,wrongFenceSealed.alias.file,wrongFenceSealed.auth.file,wrongFenceSealed.consumption.file,wrongFenceOutput]);assert.equal(wrongFenceRun.status,2);assert.equal(wrongFenceRun.receipt.category,'CODE_PATH');assert.equal(fs.existsSync(wrongFenceOutput),false);
    const absoluteSealed=lineage('sealer-absolute-approval-reference',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),approvalReferenceMode:'absolute'}), absoluteOutput=path.join(packetRoot,`launcher-invocation-${absoluteSealed.correlation}.json`), absoluteRun=run('node',[sealer,absoluteSealed.decision.file,absoluteSealed.alias.file,absoluteSealed.auth.file,absoluteSealed.consumption.file,absoluteOutput]);assert.equal(absoluteRun.status,2);assert.equal(absoluteRun.receipt.category,'ALIAS_DECISION_REFERENCE');assert.equal(fs.existsSync(absoluteOutput),false);
    const equivalentExpiry=new Date(now.getTime()+3600000), equivalentSix=o(equivalentExpiry), equivalentSeven=equivalentSix.replace(/Z$/, '9Z'), equivalent=lineage('sealer-seven-to-six-equivalent',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:equivalentExpiry,decisionExpiresRaw:equivalentSeven}), equivalentOutput=path.join(packetRoot,`launcher-invocation-${equivalent.correlation}.json`), equivalentRun=run('node',[sealer,equivalent.decision.file,equivalent.alias.file,equivalent.auth.file,equivalent.consumption.file,equivalentOutput]);assert.equal(equivalentRun.status,0,`${equivalentRun.stderr}\n${equivalentRun.stdout}`);paths.push(equivalentOutput);assert.equal(equivalentRun.receipt.result,'PASS_R017_INVOCATION_SEALED');
    const different=lineage('sealer-different-instant',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:equivalentExpiry,decisionExpiresRaw:o(new Date(equivalentExpiry.getTime()+1))}), differentOutput=path.join(packetRoot,`launcher-invocation-${different.correlation}.json`), differentRun=run('node',[sealer,different.decision.file,different.alias.file,different.auth.file,different.consumption.file,differentOutput]);assert.equal(differentRun.status,2);assert.equal(differentRun.receipt.category,'DECISION_EXECUTION_BINDING');assert.equal(fs.existsSync(differentOutput),false);
    const offset=lineage('sealer-offset-policy',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:equivalentExpiry,decisionExpiresRaw:equivalentSix.replace(/Z$/,'+00:00')}), offsetOutput=path.join(packetRoot,`launcher-invocation-${offset.correlation}.json`), offsetRun=run('node',[sealer,offset.decision.file,offset.alias.file,offset.auth.file,offset.consumption.file,offsetOutput]);assert.equal(offsetRun.status,2);assert.equal(offsetRun.receipt.category,'DECISION_TIME');assert.equal(fs.existsSync(offsetOutput),false);
    for(const [kind,raw] of [['day','2026-02-30T00:00:00.000000Z'],['month','2026-13-01T00:00:00.000000Z'],['hour','2026-01-01T25:00:00.000000Z']]){
      const invalid=lineage(`sealer-invalid-${kind}`,{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:equivalentExpiry,decisionExpiresRaw:raw}), invalidOutput=path.join(packetRoot,`launcher-invocation-${invalid.correlation}.json`), invalidRun=run('node',[sealer,invalid.decision.file,invalid.alias.file,invalid.auth.file,invalid.consumption.file,invalidOutput]);
      assert.equal(invalidRun.status,2);assert.equal(invalidRun.receipt.category,'DECISION_TIME');assert.equal(fs.existsSync(invalidOutput),false);
    }
    const rejectedManifestDirectory=path.join(packetRoot,`materialized_pr203-${crypto.randomUUID()}`), rejectedManifest=path.join(rejectedManifestDirectory,'manifest.json');fs.mkdirSync(rejectedManifestDirectory);directories.push(rejectedManifestDirectory);fs.copyFileSync(evolutionManifest,rejectedManifest);paths.push(rejectedManifest);const rejectedManifestTuple={...evolutionTuple,manifest:rejectedManifest}, rejectedManifestLineage=lineage('sealer-manifest-directory-shape',{aliasIssued:new Date(now-2*3600000),authorized:new Date(now-120000),consumed:new Date(now-60000),expires:new Date(now.getTime()+3600000),tuple:rejectedManifestTuple}), rejectedManifestOutput=path.join(packetRoot,`launcher-invocation-${rejectedManifestLineage.correlation}.json`), rejectedManifestRun=run('node',[sealer,rejectedManifestLineage.decision.file,rejectedManifestLineage.alias.file,rejectedManifestLineage.auth.file,rejectedManifestLineage.consumption.file,rejectedManifestOutput]);assert.equal(rejectedManifestRun.status,2);assert.equal(rejectedManifestRun.receipt.category,'MANIFEST_PATH');assert.equal(fs.existsSync(rejectedManifestOutput),false);
    for(const [kind,index,category] of [['alias',1,'ALIAS_PATH'],['authorization',2,'AUTHORIZATION_PATH'],['consumption',3,'CONSUMPTION_PATH']]){const wrong=path.join(runtime,`.launcher-test-sealer-wrong-${kind}-${crypto.randomUUID()}.json`),args=[sealed.decision.file,sealed.alias.file,sealed.auth.file,sealed.consumption.file];fs.copyFileSync(args[index],wrong,fs.constants.COPYFILE_EXCL);paths.push(wrong);args[index]=wrong;const rejected=run('node',[sealer,...args,path.join(packetRoot,`launcher-invocation-${sealed.correlation}.json`)]);assert.equal(rejected.status,2);assert.equal(rejected.receipt.category,category);}
  } finally {
    for (const file of paths) if (fs.existsSync(file)) fs.unlinkSync(file);
    for (const directory of directories) if (fs.existsSync(directory)) fs.rmdirSync(directory);
  }
}

console.log(JSON.stringify({
  result: 'PASS_MAZER_MASTER_PREPARATION_CREDENTIAL_SAFE_LAUNCHER_R017',
  engines: 2,
  sentinel_connectors: 3,
  poststart_failure_adversaries: transportAdversaries.length,
  same_buffer_host_replacement_adversaries: 2,
  production_adversaries: productionAdversaries,
  node_indirection_passes: nodeIndirectionPasses,
  external_calls: 0,
  credential_reads: 0,
  secret_reads: 0,
  live_data_writes: 0
}));
