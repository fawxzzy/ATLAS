import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import {
  AI_RECEIPT_DELTA_CONTRACT,
  AI_RECEIPT_PRIVATE_ROOT,
  transformAiReceiptDelta,
  writeAiReceiptPrivateOutput
} from '../transform_supabase_mazer_master_preparation_ai_receipt_delta_r017.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const sourcePath = path.join(root, 'ops/atlas/transform_supabase_mazer_master_preparation_ai_receipt_delta_r017.mjs');
const source = fs.readFileSync(sourcePath, 'utf8');

assert.equal(AI_RECEIPT_DELTA_CONTRACT.baseSha256, 'd25a3e8f5a7e471983c5c2d1b1473274d2943f0dc58306f587cb02616641df57');
assert.equal(AI_RECEIPT_DELTA_CONTRACT.deltaSha256, '8f8f7d8bd1da0e0daa242ca3545c51a03f85185ed5b09ac23961996c47cc6281');
assert.equal(AI_RECEIPT_DELTA_CONTRACT.evidenceSha256, '97c205ec454853d783b734b94dca720cb4e89f4ea28287a7e911f877039dfb50');

for (const token of [
  'DELTA_SCHEMA', 'DELTA_OBSERVED_AT', 'DELTA_PROOF', 'DELTA_COUNTS',
  'AI_BINDING', 'AI_MONOTONIC', 'AI_DELTA_NOOP', 'RECEIPT_BINDING',
  'RESET_BINDING', 'RESET_TARGET', 'DELTA_DENOMINATOR',
  "receipts:1886", "canonical_projection='8/7/36/D'", 'reset.legacy_receipts=1715',
  'validatePrivateSource(out)', 'writeAiReceiptPrivateOutput(outputPath,bytes)'
]) assert.ok(source.includes(token), `MISSING_TRANSFORM_GATE:${token}`);

assert.doesNotMatch(source, /console\.log\([^\n]*(ai_rows|receipt_rows|quarantineKey|qaPassword)/);
assert.throws(() => transformAiReceiptDelta({}, {}), /DELTA_SCHEMA/);
assert.throws(() => transformAiReceiptDelta({}, {
  schema: 'atlas.supabase.mazer-master-r017-ai-receipt-delta.v1',
  observed_at: AI_RECEIPT_DELTA_CONTRACT.observedAt,
  proof: {}, ai_rows: [], receipt_rows: [], unexpected: true
}), /DELTA_SCHEMA/);

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'r017-ai-receipt-delta-'));
const base = path.join(temp, 'base.json');
const delta = path.join(temp, 'delta.json');
const output = path.join(temp, 'out.json');
fs.writeFileSync(base, '{}');
fs.writeFileSync(delta, '{}');
const child = spawnSync(process.execPath, [sourcePath, base, delta, output], { encoding: 'utf8', windowsHide: true });
assert.equal(child.status, 2);
assert.equal(child.stderr, '');
const receipt = JSON.parse(child.stdout.trim());
assert.equal(receipt.result, 'HOLD_R017_AI_RECEIPT_PRIVATE_DELTA_TRANSFORM');
assert.equal(receipt.category, 'INPUT_SHA');
assert.equal(receipt.raw_private_output, false);
assert.equal(fs.existsSync(output), false);

assert.ok(AI_RECEIPT_PRIVATE_ROOT.endsWith(path.join('secrets', 'packet', 'mazer-master-preparation-r017')));
const outsideOutput = path.join(temp, 'outside-private-source.json');
assert.throws(() => writeAiReceiptPrivateOutput(outsideOutput, Buffer.from('{"valid":"sealed-output"}\n')), /OUTPUT_ESCAPE/);
assert.equal(fs.existsSync(outsideOutput), false);

console.log(JSON.stringify({
  result: 'PASS_MAZER_MASTER_PREPARATION_AI_RECEIPT_DELTA_R017',
  strict_gates: 13,
  provider_calls: 0,
  provider_writes: 0,
  auth_writes: 0,
  live_data_writes: 0,
  raw_private_output: 0
}));
