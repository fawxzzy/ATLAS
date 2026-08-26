import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { classifyCutover, sha256, snapshotDigest } from './classify_supabase_mazer_master_cutover_data_fence_r001.mjs';
import { renderOperationalSql } from './produce_supabase_mazer_master_preparation_private_source_r017.mjs';
import { CONTRACT, validatePrivateSource } from './materialize_supabase_mazer_master_preparation_r017.mjs';
import { writePrivateOutput } from './transform_supabase_mazer_master_preparation_private_delta_r017.mjs';

export const AI_RECEIPT_DELTA_CONTRACT=Object.freeze({
  baseSha256:'d25a3e8f5a7e471983c5c2d1b1473274d2943f0dc58306f587cb02616641df57',
  deltaSha256:'8f8f7d8bd1da0e0daa242ca3545c51a03f85185ed5b09ac23961996c47cc6281',
  observedAt:'2026-08-26T16:34:43.828Z',
  evidenceSha256:CONTRACT.currentPreimageSha256
});
export const AI_RECEIPT_PRIVATE_ROOT=path.join(path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),'secrets','packet','mazer-master-preparation-r017');
const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}`;
const digest=v=>sha256(Buffer.from(canonical(v)));
const plain=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const exact=(v,keys)=>plain(v)&&canonical(Object.keys(v).sort())===canonical([...keys].sort());
const lower=v=>String(v).toLowerCase();
const unquote=v=>v.replaceAll("''", "'");
const extract=(text,re,code)=>{const match=text.match(re);if(!match)throw new Error(code);return unquote(match[1]);};
const comparable=v=>BigInt(String(v));

function aiEnvelope(value){
  const row=structuredClone(value);row.level=String(row.level);row.completed_cycles=String(row.completed_cycles);
  if(!plain(row.state)||!plain(row.summary))throw new Error('AI_STATE');
  row.state={...structuredClone(row.state),level:row.level,completedCycles:row.completed_cycles};
  row.summary={...structuredClone(row.summary),level:row.level,completedCycles:row.completed_cycles};
  return{user_id:lower(row.user_id),runner_key:row.runner_key,level:row.level,completed_cycles:row.completed_cycles,target_complexity:Number(row.target_complexity),rank:row.rank,state_projection_matches:true,payload_digest:digest(row),row};
}
function receiptEnvelope(value){const row={ruleset_id:null,recipe_version:null,recipe_hash:null,client_run_id:null,...structuredClone(value)};return{id:lower(row.id),user_id:lower(row.user_id),client_run_id:row.client_run_id==null?null:lower(row.client_run_id),payload_digest:digest({...row,user_id:'__mapped-owner__'}),row};}
function assertAiMonotonic(before,after){const rank=['E','D','C','B','A','S'];const prior=before.row;if(comparable(after.level)<comparable(prior.level)||comparable(after.completed_cycles)<comparable(prior.completed_cycles)||Number(after.target_complexity)<Number(prior.target_complexity)||rank.indexOf(after.rank)<rank.indexOf(prior.rank)||Date.parse(after.updated_at)<Date.parse(prior.updated_at))throw new Error('AI_MONOTONIC');}

export function transformAiReceiptDelta(base,delta){
  if(!exact(delta,['schema','observed_at','proof','ai_rows','receipt_rows'])||delta.schema!=='atlas.supabase.mazer-master-r017-ai-receipt-delta.v1')throw new Error('DELTA_SCHEMA');
  if(new Date(delta.observed_at).toISOString()!==AI_RECEIPT_DELTA_CONTRACT.observedAt)throw new Error('DELTA_OBSERVED_AT');
  const proof=delta.proof,proofKeys=['ai_count','changed_ai','new_receipts','receipt_count','ai_owner_orphans','receipt_after_ai','receipt_owner_orphans','receipt_client_run_missing','receipt_client_run_duplicates'];
  if(!exact(proof,proofKeys)||proof.ai_count!==16||proof.changed_ai!==1||proof.new_receipts!==1||proof.receipt_count!==1877||proofKeys.slice(4).some(k=>proof[k]!==0))throw new Error('DELTA_PROOF');
  if(!Array.isArray(delta.ai_rows)||delta.ai_rows.length!==1||!Array.isArray(delta.receipt_rows)||delta.receipt_rows.length!==1)throw new Error('DELTA_COUNTS');
  if(base.schema!==CONTRACT.schema||base.packet!==CONTRACT.packet)throw new Error('BASE_SCHEMA');
  const source=structuredClone(base.fence_input.source_snapshot),mapped=new Set(base.fence_input.identity_map.map(v=>v.legacy_user_id));
  const rawAi=delta.ai_rows[0],aiKey=`${lower(rawAi.user_id)}:${rawAi.runner_key}`,aiIndex=source.ai.findIndex(v=>`${v.user_id}:${v.runner_key}`===aiKey);
  if(aiIndex<0||!mapped.has(lower(rawAi.user_id)))throw new Error('AI_BINDING');assertAiMonotonic(source.ai[aiIndex],rawAi);const ai=aiEnvelope(rawAi);if(canonical(ai.row)===canonical(source.ai[aiIndex].row))throw new Error('AI_DELTA_NOOP');source.ai[aiIndex]=ai;
  const receipt=receiptEnvelope(delta.receipt_rows[0]);
  if(!mapped.has(receipt.user_id)||!receipt.client_run_id||source.receipts.some(v=>v.id===receipt.id)||source.receipts.some(v=>v.user_id===receipt.user_id&&v.client_run_id===receipt.client_run_id)||base.fence_input.target_snapshot.receipts.some(v=>v.client_run_id===receipt.client_run_id)||Date.parse(receipt.row.completed_at)>Date.parse(ai.row.updated_at))throw new Error('RECEIPT_BINDING');
  source.receipts.push(receipt);source.ai.sort((a,b)=>canonical([a.user_id,a.runner_key]).localeCompare(canonical([b.user_id,b.runner_key])));source.receipts.sort((a,b)=>a.id.localeCompare(b.id));source.observed_at=AI_RECEIPT_DELTA_CONTRACT.observedAt;
  const fence=structuredClone(base.fence_input);fence.source_snapshot=source;fence.expected_source_high_water_digest=snapshotDigest(source);fence.zero_delta_reads=[1,2].map(ms=>({...structuredClone(source),observed_at:new Date(Date.parse(source.observed_at)+ms).toISOString()}));
  const classified=classifyCutover(fence),counts=classified.receipt.desired_counts;if(canonical(counts)!==canonical({profiles:13,player:16,ai:16,receipts:1886}))throw new Error(`DELTA_DENOMINATOR_${counts.profiles}_${counts.player}_${counts.ai}_${counts.receipts}`);
  const reset=structuredClone(base.reset_era_ai);if(reset.legacy_user_id!==ai.user_id||reset.master_receipts!==1239)throw new Error('RESET_BINDING');reset.canonical_projection='8/7/36/D';reset.legacy_receipts=1715;reset.canonical_row_digest=digest(ai);
  const action=structuredClone(fence),targetIndex=action.target_snapshot.ai.findIndex(v=>v.user_id===reset.master_user_id&&v.runner_key==='menu-runner');if(targetIndex<0)throw new Error('RESET_TARGET');const mappedAi=structuredClone(ai);mappedAi.user_id=reset.master_user_id;mappedAi.row.user_id=reset.master_user_id;mappedAi.payload_digest=digest(mappedAi.row);action.target_snapshot.ai[targetIndex]=mappedAi;
  const quarantineKey=extract(base.sql['reset-era-apply.sql'],/pgp_sym_encrypt\('(?:''|[^'])*','((?:''|[^'])*)','cipher-algo=aes256'\)/,'QUARANTINE_KEY_PARSE');
  const qaPassword=extract(base.sql['qa-apply.sql'],/extensions\.crypt\('((?:''|[^'])*)',extensions\.gen_salt\('bf'\)\)/,'QA_PASSWORD_PARSE');
  const rendered=renderOperationalSql({auth:base.auth,fenceInput:fence,actionFenceInput:action,catalogPreimage:base.catalog_preimage,reset:{quarantined_row:reset.quarantined_row},qa:base.qa,quarantineKey,qaPassword});
  const out={...structuredClone(base),evidence:{...base.evidence,current_preimage_sha256:CONTRACT.currentPreimageSha256},fence_input:fence,reset_era_ai:reset,sql:rendered.sql,sql_sha256:rendered.sql_sha256};validatePrivateSource(out);return out;
}
export function writeAiReceiptPrivateOutput(outputPath,bytes){writePrivateOutput(outputPath,bytes,AI_RECEIPT_PRIVATE_ROOT);}
export function transformAiReceiptFiles(basePath,deltaPath,outputPath){const baseBytes=fs.readFileSync(basePath),deltaBytes=fs.readFileSync(deltaPath);if(sha256(baseBytes)!==AI_RECEIPT_DELTA_CONTRACT.baseSha256||sha256(deltaBytes)!==AI_RECEIPT_DELTA_CONTRACT.deltaSha256)throw new Error('INPUT_SHA');const out=transformAiReceiptDelta(JSON.parse(baseBytes),JSON.parse(deltaBytes));const bytes=Buffer.from(`${canonical(out)}\n`);writeAiReceiptPrivateOutput(outputPath,bytes);return{path:path.resolve(outputPath),sha256:sha256(bytes),bytes:bytes.length};}
const isMain=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);if(isMain){try{const r=transformAiReceiptFiles(process.argv[2],process.argv[3],process.argv[4]);console.log(JSON.stringify({result:'PASS_R017_AI_RECEIPT_PRIVATE_DELTA_TRANSFORMED',private_source_sha256:r.sha256,private_source_bytes:r.bytes,raw_private_output:false}))}catch(error){console.log(JSON.stringify({result:'HOLD_R017_AI_RECEIPT_PRIVATE_DELTA_TRANSFORM',category:String(error.message).replace(/[^A-Za-z0-9_:.-]/g,''),raw_private_output:false}));process.exitCode=2;}}
