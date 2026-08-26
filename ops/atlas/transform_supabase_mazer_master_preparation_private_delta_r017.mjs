import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { classifyCutover, sha256, snapshotDigest } from './classify_supabase_mazer_master_cutover_data_fence_r001.mjs';
import { renderOperationalSql } from './produce_supabase_mazer_master_preparation_private_source_r017.mjs';
import { CONTRACT, validatePrivateSource } from './materialize_supabase_mazer_master_preparation_r017.mjs';

export const DELTA_CONTRACT=Object.freeze({baseSha256:'f83141951ae342e1c9802ec291348b363dce9033d80b15b254889ca207919034',deltaSha256:'1dfece38eea810733d82f4539db88898fbb0c98262368af7b807c51f69a47599',observedAt:'2026-08-26T02:00:56.791816Z',evidenceSha256:CONTRACT.currentPreimageSha256});
const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}`;
const digest=v=>sha256(Buffer.from(canonical(v)));
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&canonical(Object.keys(v).sort())===canonical([...keys].sort());
const unquote=v=>v.replaceAll("''", "'");
const extract=(text,re,code)=>{const m=text.match(re);if(!m)throw new Error(code);return unquote(m[1]);};
const inside=(candidate,root,code='OUTPUT_ESCAPE')=>{const r=path.resolve(candidate),b=path.resolve(root).replace(/[\\/]+$/,'');if(r.toLowerCase()!==b.toLowerCase()&&!r.toLowerCase().startsWith(`${b.toLowerCase()}${path.sep}`))throw new Error(code);return r;};
function assertNoReparse(candidate,root){const base=path.resolve(root),target=inside(candidate,base,'REPARSE_SCOPE_ESCAPE');if(fs.lstatSync(base).isSymbolicLink())throw new Error('OUTPUT_REPARSE_ROOT');const relative=path.relative(base,target);let cursor=base;for(const part of relative.split(path.sep).filter(Boolean)){cursor=path.join(cursor,part);if(!fs.existsSync(cursor))continue;const stat=fs.lstatSync(cursor);if(stat.isSymbolicLink())throw new Error('OUTPUT_REPARSE_COMPONENT');}return target;}
export function writePrivateOutput(outputPath,bytes,privateRoot='C:/ATLAS/secrets/packet/mazer-master-preparation-r017'){
  const root=path.resolve(privateRoot),output=inside(outputPath,root);if(!fs.existsSync(root)||!fs.statSync(root).isDirectory())throw new Error('PRIVATE_ROOT');assertNoReparse(root,root);if(path.normalize(path.dirname(output)).toLowerCase()!==path.normalize(root).toLowerCase())throw new Error('OUTPUT_NOT_IMMEDIATE_CHILD');if(fs.existsSync(output))throw new Error('OUTPUT_EXISTS');
  const realRoot=fs.realpathSync.native(root);if(path.normalize(realRoot).toLowerCase()!==path.normalize(root).toLowerCase())throw new Error('OUTPUT_ROOT_REALPATH_DRIFT');const flags=fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_WRONLY;let fd,created=false,final=null,wrote=false;
  try{fd=fs.openSync(output,flags,0o600);created=true;if(!fs.fstatSync(fd).isFile())throw new Error('OUTPUT_HANDLE_NOT_FILE');if(fs.lstatSync(output).isSymbolicLink())throw new Error('OUTPUT_FINAL_REPARSE');final=fs.realpathSync.native(output);inside(final,realRoot,'OUTPUT_FINAL_ESCAPE');if(path.normalize(final).toLowerCase()!==path.normalize(output).toLowerCase())throw new Error('OUTPUT_FINAL_PATH_DRIFT');assertNoReparse(root,root);fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);wrote=true;const after=fs.realpathSync.native(output);if(path.normalize(after).toLowerCase()!==path.normalize(final).toLowerCase())throw new Error('OUTPUT_FINAL_PATH_DRIFT');assertNoReparse(root,root);}catch(error){if(created&&!wrote){try{if(fd!==undefined){fs.closeSync(fd);fd=undefined}if(final&&fs.existsSync(final))fs.unlinkSync(final);else if(fs.existsSync(output)&&!fs.lstatSync(output).isSymbolicLink())fs.unlinkSync(output)}catch{} }throw error}finally{if(fd!==undefined)fs.closeSync(fd);}
}

export function transformPrivateDelta(base,delta){
  if(!exact(delta,['new_profile','new_receipt','new_player']))throw new Error('DELTA_KEYS');
  if(base.schema!==CONTRACT.schema||base.packet!==CONTRACT.packet)throw new Error('BASE_SCHEMA');
  const profile={revision:0,username:null,...structuredClone(delta.new_profile)};
  const receipt={ruleset_id:null,recipe_version:null,recipe_hash:null,client_run_id:null,...structuredClone(delta.new_receipt)};
  const player={revision:0,level_reached_at:null,...structuredClone(delta.new_player)};
  if(profile.username!=null||receipt.surface!=='play'||!receipt.client_run_id)throw new Error('DELTA_SEMANTICS');
  const source=structuredClone(base.fence_input.source_snapshot);
  if(source.profiles.some(v=>v.user_id===String(profile.user_id).toLowerCase())||source.receipts.some(v=>v.id===String(receipt.id).toLowerCase()))throw new Error('DELTA_COLLISION');
  const playerIndex=source.player.findIndex(v=>v.user_id===String(player.user_id).toLowerCase());if(playerIndex<0)throw new Error('PLAYER_PREIMAGE_MISSING');
  if(String(player.user_id).toLowerCase()!==String(receipt.user_id).toLowerCase()||Date.parse(receipt.completed_at)>Date.parse(player.updated_at))throw new Error('PLAYER_TIMESTAMP_DRIFT');
  const mapped=new Map(base.fence_input.identity_map.map(v=>[v.legacy_user_id,v.master_user_id]));
  if(!mapped.has(String(profile.user_id).toLowerCase())||!mapped.has(String(receipt.user_id).toLowerCase()))throw new Error('OWNER_MAP_MISSING');
  if(source.receipts.some(v=>v.user_id===String(receipt.user_id).toLowerCase()&&v.client_run_id===String(receipt.client_run_id).toLowerCase()))throw new Error('CLIENT_RUN_DUPLICATE');
  if(base.fence_input.target_snapshot.receipts.some(v=>v.client_run_id===String(receipt.client_run_id).toLowerCase()))throw new Error('TARGET_RECEIPT_OVERLAP');
  const profileEnvelope={user_id:String(profile.user_id).toLowerCase(),revision:Number(profile.revision??0),username_present:false,username_digest:null,payload_digest:digest(profile),row:profile};
  player.player_level=String(player.player_level);player.player_completed_cycles=String(player.player_completed_cycles);
  if(!player.state||typeof player.state!=='object'||Array.isArray(player.state))throw new Error('PLAYER_STATE');
  const tracks=player.state.tracks&&typeof player.state.tracks==='object'&&!Array.isArray(player.state.tracks)?structuredClone(player.state.tracks):{};
  tracks.player={...(tracks.player&&typeof tracks.player==='object'&&!Array.isArray(tracks.player)?tracks.player:{}),level:player.player_level,completedCycles:player.player_completed_cycles};player.state={...player.state,tracks};
  const playerEnvelope={user_id:String(player.user_id).toLowerCase(),level:player.player_level,completed_cycles:player.player_completed_cycles,revision:Number(player.revision??0),target_complexity:Number(player.player_target_complexity),rank:player.player_rank,state_projection_matches:true,payload_digest:digest(player),row:player};
  const receiptEnvelope={id:String(receipt.id).toLowerCase(),user_id:String(receipt.user_id).toLowerCase(),client_run_id:String(receipt.client_run_id).toLowerCase(),payload_digest:digest({...receipt,user_id:'__mapped-owner__'}),row:receipt};
  source.profiles.push(profileEnvelope);source.profiles.sort((a,b)=>a.user_id.localeCompare(b.user_id));
  source.player[playerIndex]=playerEnvelope;source.player.sort((a,b)=>a.user_id.localeCompare(b.user_id));
  source.receipts.push(receiptEnvelope);source.receipts.sort((a,b)=>a.id.localeCompare(b.id));source.observed_at=DELTA_CONTRACT.observedAt;
  const fence=structuredClone(base.fence_input);fence.source_snapshot=source;fence.expected_source_high_water_digest=snapshotDigest(source);fence.zero_delta_reads=[1,2].map(ms=>({...structuredClone(source),observed_at:new Date(Date.parse(source.observed_at)+ms).toISOString()}));
  const classified=classifyCutover(fence),counts=classified.receipt.desired_counts;if(canonical(counts)!==canonical({profiles:13,player:16,ai:16,receipts:1884}))throw new Error(`DELTA_DENOMINATOR_${counts.profiles}_${counts.player}_${counts.ai}_${counts.receipts}`);
  const action=structuredClone(fence),reset=base.reset_era_ai,src=action.source_snapshot.ai.find(v=>v.user_id===reset.legacy_user_id&&v.runner_key==='menu-runner'),idx=action.target_snapshot.ai.findIndex(v=>v.user_id===reset.master_user_id&&v.runner_key==='menu-runner');if(!src||idx<0)throw new Error('RESET_BINDING');
  const mappedAi=structuredClone(src);mappedAi.user_id=reset.master_user_id;mappedAi.row.user_id=reset.master_user_id;mappedAi.payload_digest=digest(mappedAi.row);action.target_snapshot.ai[idx]=mappedAi;
  const quarantineKey=extract(base.sql['reset-era-apply.sql'],/pgp_sym_encrypt\('(?:''|[^'])*','((?:''|[^'])*)','cipher-algo=aes256'\)/,'QUARANTINE_KEY_PARSE');
  const qaPassword=extract(base.sql['qa-apply.sql'],/extensions\.crypt\('((?:''|[^'])*)',extensions\.gen_salt\('bf'\)\)/,'QA_PASSWORD_PARSE');
  const rendered=renderOperationalSql({auth:base.auth,fenceInput:fence,actionFenceInput:action,catalogPreimage:base.catalog_preimage,reset:{quarantined_row:base.reset_era_ai.quarantined_row},qa:base.qa,quarantineKey,qaPassword});
  const out={...structuredClone(base),evidence:{...base.evidence,current_preimage_sha256:CONTRACT.currentPreimageSha256},fence_input:fence,sql:rendered.sql,sql_sha256:rendered.sql_sha256};validatePrivateSource(out);return out;
}

export function transformFiles(basePath,deltaPath,outputPath){const bb=fs.readFileSync(basePath),db=fs.readFileSync(deltaPath);if(sha256(bb)!==DELTA_CONTRACT.baseSha256||sha256(db)!==DELTA_CONTRACT.deltaSha256)throw new Error('INPUT_SHA');const out=transformPrivateDelta(JSON.parse(bb),JSON.parse(db));const bytes=Buffer.from(`${canonical(out)}\n`),output=path.resolve(outputPath);writePrivateOutput(output,bytes);return{path:output,sha256:sha256(bytes),bytes:bytes.length};}
const isMain=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);if(isMain){try{const r=transformFiles(process.argv[2],process.argv[3],process.argv[4]);console.log(JSON.stringify({result:'PASS_R017_PRIVATE_DELTA_TRANSFORMED',private_source_sha256:r.sha256,private_source_bytes:r.bytes,raw_private_output:false}))}catch(e){console.log(JSON.stringify({result:'HOLD_R017_PRIVATE_DELTA_TRANSFORM',category:String(e.message).replace(/[^A-Za-z0-9_:.-]/g,''),raw_private_output:false}));process.exitCode=2}}
