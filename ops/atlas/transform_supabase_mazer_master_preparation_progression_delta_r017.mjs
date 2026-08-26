import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { classifyCutover, sha256, snapshotDigest } from './classify_supabase_mazer_master_cutover_data_fence_r001.mjs';
import { renderOperationalSql } from './produce_supabase_mazer_master_preparation_private_source_r017.mjs';
import { CONTRACT, validatePrivateSource } from './materialize_supabase_mazer_master_preparation_r017.mjs';
import { writePrivateOutput } from './transform_supabase_mazer_master_preparation_private_delta_r017.mjs';

export const PROGRESSION_DELTA_CONTRACT=Object.freeze({
  baseSha256:'5a5847bf8c5cd6375c48a1b59d47f54a0bb7026ac79ad3fdafc75813d1f180ee',
  deltaSha256:'adb91090c243fa48d7e34dcf78290b6d784961753e181feb46b541aa342cc102',
  observedAt:'2026-08-26T06:59:09.883Z',
  evidenceSha256:CONTRACT.currentPreimageSha256
});
const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}`;
const digest=v=>sha256(Buffer.from(canonical(v)));
const plain=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const exact=(v,keys)=>plain(v)&&canonical(Object.keys(v).sort())===canonical([...keys].sort());
const lower=v=>String(v).toLowerCase();
const unquote=v=>v.replaceAll("''", "'");
const extract=(text,re,code)=>{const match=text.match(re);if(!match)throw new Error(code);return unquote(match[1]);};
const comparable=v=>BigInt(String(v));

function playerEnvelope(value){
  const row={revision:0,level_reached_at:null,...structuredClone(value)};
  row.player_level=String(row.player_level);row.player_completed_cycles=String(row.player_completed_cycles);
  if(!plain(row.state))throw new Error('PLAYER_STATE');
  const tracks=plain(row.state.tracks)?structuredClone(row.state.tracks):{};
  tracks.player={...(plain(tracks.player)?structuredClone(tracks.player):{}),level:row.player_level,completedCycles:row.player_completed_cycles};
  row.state={...structuredClone(row.state),tracks};
  return{user_id:lower(row.user_id),level:row.player_level,completed_cycles:row.player_completed_cycles,revision:Number(row.revision??0),target_complexity:Number(row.player_target_complexity),rank:row.player_rank,state_projection_matches:true,payload_digest:digest(row),row};
}
function aiEnvelope(value){
  const row=structuredClone(value);row.level=String(row.level);row.completed_cycles=String(row.completed_cycles);
  if(!plain(row.state)||!plain(row.summary))throw new Error('AI_STATE');
  row.state={...structuredClone(row.state),level:row.level,completedCycles:row.completed_cycles};
  row.summary={...structuredClone(row.summary),level:row.level,completedCycles:row.completed_cycles};
  return{user_id:lower(row.user_id),runner_key:row.runner_key,level:row.level,completed_cycles:row.completed_cycles,target_complexity:Number(row.target_complexity),rank:row.rank,state_projection_matches:true,payload_digest:digest(row),row};
}
function receiptEnvelope(value){
  const row={ruleset_id:null,recipe_version:null,recipe_hash:null,client_run_id:null,...structuredClone(value)};
  return{id:lower(row.id),user_id:lower(row.user_id),client_run_id:row.client_run_id==null?null:lower(row.client_run_id),payload_digest:digest({...row,user_id:'__mapped-owner__'}),row};
}
function assertMonotonic(before,after,kind){
  const rank=['E','D','C','B','A','S'];
  const prior=before.row;
  if(kind==='PLAYER'&&(comparable(after.player_level)<comparable(prior.player_level)||comparable(after.player_completed_cycles)<comparable(prior.player_completed_cycles)||Number(after.player_target_complexity)<Number(prior.player_target_complexity)||rank.indexOf(after.player_rank)<rank.indexOf(prior.player_rank)))throw new Error('PLAYER_MONOTONIC');
  if(kind==='AI'&&(comparable(after.level)<comparable(prior.level)||comparable(after.completed_cycles)<comparable(prior.completed_cycles)||Number(after.target_complexity)<Number(prior.target_complexity)||rank.indexOf(after.rank)<rank.indexOf(prior.rank)))throw new Error('AI_MONOTONIC');
  if(Date.parse(after.updated_at)<Date.parse(prior.updated_at))throw new Error(`${kind}_TIMESTAMP`);
}

export function transformProgressionDelta(base,delta){
  if(!exact(delta,['schema','observed_at','proof','player_rows','ai_rows','receipt_rows'])||delta.schema!=='atlas.supabase.mazer-master-r017-progression-receipt-delta.v1')throw new Error('DELTA_SCHEMA');
  if(new Date(delta.observed_at).toISOString()!==PROGRESSION_DELTA_CONTRACT.observedAt)throw new Error('DELTA_OBSERVED_AT');
  const proof=delta.proof,proofKeys=['ai_changed','player_changed','receipts_added','ai_owner_orphans','ai_shape_violations','player_owner_orphans','receipt_owner_orphans','ai_monotonic_violations','ai_timestamp_violations','player_shape_violations','receipt_client_run_missing','player_monotonic_violations','player_timestamp_violations','receipt_client_run_duplicates'];
  if(!exact(proof,proofKeys)||proof.ai_changed!==13||proof.player_changed!==13||proof.receipts_added!==1||proofKeys.slice(3).some(k=>proof[k]!==0))throw new Error('DELTA_PROOF');
  if(!Array.isArray(delta.player_rows)||delta.player_rows.length!==13||!Array.isArray(delta.ai_rows)||delta.ai_rows.length!==13||!Array.isArray(delta.receipt_rows)||delta.receipt_rows.length!==1)throw new Error('DELTA_COUNTS');
  if(base.schema!==CONTRACT.schema||base.packet!==CONTRACT.packet)throw new Error('BASE_SCHEMA');
  const source=structuredClone(base.fence_input.source_snapshot),mapped=new Set(base.fence_input.identity_map.map(v=>v.legacy_user_id));
  const changedPlayers=new Set(),effectivePlayers=new Set();
  for(const raw of delta.player_rows){const id=lower(raw.user_id),index=source.player.findIndex(v=>v.user_id===id);if(index<0||changedPlayers.has(id)||!mapped.has(id))throw new Error('PLAYER_BINDING');changedPlayers.add(id);const before=source.player[index];if(canonical(raw)===canonical(before.row))throw new Error('PLAYER_RAW_DELTA_NOOP');assertMonotonic(before,raw,'PLAYER');const after=playerEnvelope(raw);if(canonical(after.row)===canonical(before.row))continue;effectivePlayers.add(id);source.player[index]=after;}
  const changedAi=new Set(),effectiveAi=new Set();
  for(const raw of delta.ai_rows){const id=lower(raw.user_id),key=`${id}:${raw.runner_key}`,index=source.ai.findIndex(v=>v.user_id===id&&v.runner_key===raw.runner_key);if(index<0||changedAi.has(key)||!mapped.has(id))throw new Error('AI_BINDING');changedAi.add(key);const before=source.ai[index];if(canonical(raw)===canonical(before.row))throw new Error('AI_RAW_DELTA_NOOP');assertMonotonic(before,raw,'AI');const after=aiEnvelope(raw);if(canonical(after.row)===canonical(before.row))continue;effectiveAi.add(key);source.ai[index]=after;}
  if(changedPlayers.size!==13||changedAi.size!==13||effectivePlayers.size!==1||effectiveAi.size!==0)throw new Error(`EFFECTIVE_DELTA_COUNT_${changedPlayers.size}_${changedAi.size}_${effectivePlayers.size}_${effectiveAi.size}`);
  const added=receiptEnvelope(delta.receipt_rows[0]);
  if(!mapped.has(added.user_id)||!added.client_run_id||source.receipts.some(v=>v.id===added.id)||source.receipts.some(v=>v.user_id===added.user_id&&v.client_run_id===added.client_run_id)||base.fence_input.target_snapshot.receipts.some(v=>v.client_run_id===added.client_run_id))throw new Error('RECEIPT_BINDING');
  source.receipts.push(added);source.player.sort((a,b)=>a.user_id.localeCompare(b.user_id));source.ai.sort((a,b)=>canonical([a.user_id,a.runner_key]).localeCompare(canonical([b.user_id,b.runner_key])));source.receipts.sort((a,b)=>a.id.localeCompare(b.id));source.observed_at=PROGRESSION_DELTA_CONTRACT.observedAt;
  const fence=structuredClone(base.fence_input);fence.source_snapshot=source;fence.expected_source_high_water_digest=snapshotDigest(source);fence.zero_delta_reads=[1,2].map(ms=>({...structuredClone(source),observed_at:new Date(Date.parse(source.observed_at)+ms).toISOString()}));
  const classified=classifyCutover(fence),counts=classified.receipt.desired_counts;if(canonical(counts)!==canonical({profiles:13,player:16,ai:16,receipts:1885}))throw new Error(`DELTA_DENOMINATOR_${counts.profiles}_${counts.player}_${counts.ai}_${counts.receipts}`);
  const action=structuredClone(fence),reset=base.reset_era_ai,src=action.source_snapshot.ai.find(v=>v.user_id===reset.legacy_user_id&&v.runner_key==='menu-runner'),index=action.target_snapshot.ai.findIndex(v=>v.user_id===reset.master_user_id&&v.runner_key==='menu-runner');if(!src||index<0||digest(src)!==base.reset_era_ai.canonical_row_digest)throw new Error('RESET_BINDING');
  const mappedAi=structuredClone(src);mappedAi.user_id=reset.master_user_id;mappedAi.row.user_id=reset.master_user_id;mappedAi.payload_digest=digest(mappedAi.row);action.target_snapshot.ai[index]=mappedAi;
  const quarantineKey=extract(base.sql['reset-era-apply.sql'],/pgp_sym_encrypt\('(?:''|[^'])*','((?:''|[^'])*)','cipher-algo=aes256'\)/,'QUARANTINE_KEY_PARSE');
  const qaPassword=extract(base.sql['qa-apply.sql'],/extensions\.crypt\('((?:''|[^'])*)',extensions\.gen_salt\('bf'\)\)/,'QA_PASSWORD_PARSE');
  const rendered=renderOperationalSql({auth:base.auth,fenceInput:fence,actionFenceInput:action,catalogPreimage:base.catalog_preimage,reset:{quarantined_row:base.reset_era_ai.quarantined_row},qa:base.qa,quarantineKey,qaPassword});
  const out={...structuredClone(base),evidence:{...base.evidence,current_preimage_sha256:CONTRACT.currentPreimageSha256},fence_input:fence,sql:rendered.sql,sql_sha256:rendered.sql_sha256};validatePrivateSource(out);return out;
}

export function transformProgressionFiles(basePath,deltaPath,outputPath){const baseBytes=fs.readFileSync(basePath),deltaBytes=fs.readFileSync(deltaPath);if(sha256(baseBytes)!==PROGRESSION_DELTA_CONTRACT.baseSha256||sha256(deltaBytes)!==PROGRESSION_DELTA_CONTRACT.deltaSha256)throw new Error('INPUT_SHA');const out=transformProgressionDelta(JSON.parse(baseBytes),JSON.parse(deltaBytes));const bytes=Buffer.from(`${canonical(out)}\n`);writePrivateOutput(outputPath,bytes);return{path:path.resolve(outputPath),sha256:sha256(bytes),bytes:bytes.length};}
const isMain=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);if(isMain){try{const result=transformProgressionFiles(process.argv[2],process.argv[3],process.argv[4]);console.log(JSON.stringify({result:'PASS_R017_PROGRESSION_PRIVATE_DELTA_TRANSFORMED',private_source_sha256:result.sha256,private_source_bytes:result.bytes,raw_private_output:false}))}catch(error){console.log(JSON.stringify({result:'HOLD_R017_PROGRESSION_PRIVATE_DELTA_TRANSFORM',category:String(error.message).replace(/[^A-Za-z0-9_:.-]/g,''),raw_private_output:false}));process.exitCode=2;}}
