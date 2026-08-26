import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { DELTA_CONTRACT, writePrivateOutput } from '../transform_supabase_mazer_master_preparation_private_delta_r017.mjs';

const root=path.resolve(path.dirname(new URL(import.meta.url).pathname.slice(1)),'../../..');
const sourcePath=path.join(root,'ops/atlas/transform_supabase_mazer_master_preparation_private_delta_r017.mjs');
const source=fs.readFileSync(sourcePath,'utf8');
assert.equal(DELTA_CONTRACT.baseSha256,'f83141951ae342e1c9802ec291348b363dce9033d80b15b254889ca207919034');
assert.equal(DELTA_CONTRACT.deltaSha256,'1dfece38eea810733d82f4539db88898fbb0c98262368af7b807c51f69a47599');
for(const token of ['DELTA_KEYS','DELTA_SEMANTICS','DELTA_COLLISION','PLAYER_TIMESTAMP_DRIFT','OWNER_MAP_MISSING','CLIENT_RUN_DUPLICATE','TARGET_RECEIPT_OVERLAP','DELTA_DENOMINATOR','validatePrivateSource(out)','O_CREAT|fs.constants.O_EXCL'])assert.match(source,new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
assert.doesNotMatch(source,/console\.log\([^\n]*(new_profile|new_receipt|new_player)/);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'r017-delta-test-')),base=path.join(temp,'base.json'),delta=path.join(temp,'delta.json');fs.writeFileSync(base,'{}');fs.writeFileSync(delta,'{}');
const child=spawnSync(process.execPath,[sourcePath,base,delta,path.join(temp,'out.json')],{encoding:'utf8',windowsHide:true});assert.equal(child.status,2);const receipt=JSON.parse(child.stdout.trim());assert.equal(receipt.result,'HOLD_R017_PRIVATE_DELTA_TRANSFORM');assert.equal(receipt.category,'INPUT_SHA');assert.equal(receipt.raw_private_output,false);assert.equal(fs.existsSync(path.join(temp,'out.json')),false);
const privateRoot=path.join(temp,'private'),outside=path.join(temp,'outside'),junction=path.join(privateRoot,'escape');fs.mkdirSync(privateRoot);fs.mkdirSync(outside);fs.symlinkSync(outside,junction,process.platform==='win32'?'junction':'dir');assert.throws(()=>writePrivateOutput(path.join(junction,'escaped.json'),Buffer.from('private'),privateRoot),/OUTPUT_NOT_IMMEDIATE_CHILD/);assert.equal(fs.existsSync(path.join(outside,'escaped.json')),false);
const rootLink=path.join(temp,'private-root-link');fs.symlinkSync(outside,rootLink,process.platform==='win32'?'junction':'dir');assert.throws(()=>writePrivateOutput(path.join(rootLink,'escaped-root.json'),Buffer.from('private'),rootLink),/OUTPUT_REPARSE_ROOT/);assert.equal(fs.existsSync(path.join(outside,'escaped-root.json')),false);
console.log(JSON.stringify({result:'PASS_MAZER_MASTER_PREPARATION_PRIVATE_DELTA_R017',adversaries:3,strict_gates:12,provider_calls:0,provider_writes:0,auth_writes:0,live_data_writes:0,raw_private_output:0}));
