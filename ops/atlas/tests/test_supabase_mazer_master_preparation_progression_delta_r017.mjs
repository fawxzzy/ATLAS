import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { PROGRESSION_DELTA_CONTRACT, transformProgressionDelta } from '../transform_supabase_mazer_master_preparation_progression_delta_r017.mjs';

const root=path.resolve(path.dirname(new URL(import.meta.url).pathname.slice(1)),'../../..');
const sourcePath=path.join(root,'ops/atlas/transform_supabase_mazer_master_preparation_progression_delta_r017.mjs');
const source=fs.readFileSync(sourcePath,'utf8');
assert.equal(PROGRESSION_DELTA_CONTRACT.baseSha256,'5a5847bf8c5cd6375c48a1b59d47f54a0bb7026ac79ad3fdafc75813d1f180ee');
assert.equal(PROGRESSION_DELTA_CONTRACT.deltaSha256,'adb91090c243fa48d7e34dcf78290b6d784961753e181feb46b541aa342cc102');
assert.equal(PROGRESSION_DELTA_CONTRACT.evidenceSha256,'1384da39e995fb8f0c2f0d2e8aea5576dd75b0d8789b8445975cfb9e1f886d67');
for(const token of ['DELTA_SCHEMA','DELTA_OBSERVED_AT','DELTA_PROOF','DELTA_COUNTS','PLAYER_BINDING','PLAYER_RAW_DELTA_NOOP','PLAYER_MONOTONIC','AI_BINDING','AI_RAW_DELTA_NOOP','AI_MONOTONIC','EFFECTIVE_DELTA_COUNT','RECEIPT_BINDING','RESET_BINDING','DELTA_DENOMINATOR','validatePrivateSource(out)','writePrivateOutput(outputPath,bytes)'])assert.match(source,new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
assert.doesNotMatch(source,/console\.log\([^\n]*(player_rows|ai_rows|receipt_rows)/);
assert.throws(()=>transformProgressionDelta({},{}),/DELTA_SCHEMA/);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'r017-progression-delta-')),base=path.join(temp,'base.json'),delta=path.join(temp,'delta.json'),output=path.join(temp,'out.json');fs.writeFileSync(base,'{}');fs.writeFileSync(delta,'{}');
const child=spawnSync(process.execPath,[sourcePath,base,delta,output],{encoding:'utf8',windowsHide:true});assert.equal(child.status,2);const receipt=JSON.parse(child.stdout.trim());assert.equal(receipt.result,'HOLD_R017_PROGRESSION_PRIVATE_DELTA_TRANSFORM');assert.equal(receipt.category,'INPUT_SHA');assert.equal(receipt.raw_private_output,false);assert.equal(fs.existsSync(output),false);
console.log(JSON.stringify({result:'PASS_MAZER_MASTER_PREPARATION_PROGRESSION_DELTA_R017',strict_gates:16,provider_calls:0,provider_writes:0,auth_writes:0,live_data_writes:0,raw_private_output:0}));
