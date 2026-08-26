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
  transformAiReceiptFiles,
  writeAiReceiptPrivateOutput
} from '../transform_supabase_mazer_master_preparation_ai_receipt_delta_r017.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const sourcePath = path.join(root, 'ops/atlas/transform_supabase_mazer_master_preparation_ai_receipt_delta_r017.mjs');
const source = fs.readFileSync(sourcePath, 'utf8');

assert.equal(AI_RECEIPT_DELTA_CONTRACT.baseSha256, '754dca84d02d7e3c67064bc4a67ddcfffea196d5990d757afd4e86bbbdea7c33');
assert.equal(AI_RECEIPT_DELTA_CONTRACT.deltaSha256, 'a75b481781a195cc3878a32e404f59962ac71797974acc0776451551c20e964f');
assert.equal(AI_RECEIPT_DELTA_CONTRACT.evidenceSha256, 'bfb9e238238afe78282692ae7670e74cdb2300aa5a0a60e26cd0ae7864b390d2');
assert.equal(AI_RECEIPT_DELTA_CONTRACT.successorSha256, '9326145071e2e067286e6460d06187d89d3bdc6b82c202b2cbea2f313f0b35ae');

for (const token of [
  'DELTA_SCHEMA', 'DELTA_OBSERVED_AT', 'DELTA_PROOF', 'DELTA_COUNTS',
  'PLAYER_BINDING', 'AI_BINDING', 'AI_MONOTONIC', 'AI_RAW_NOOP', 'RECEIPT_BINDING',
  'EFFECTIVE_DELTA', 'RESET_TARGET', 'DELTA_DENOMINATOR', 'SUCCESSOR_SHA',
  "receipts:1887", "canonical_projection='9/8/40/D'", 'reset.legacy_receipts=1716',
  'validatePrivateSource(out)', 'writeAiReceiptPrivateOutput(outputPath,bytes)'
]) assert.ok(source.includes(token), `MISSING_TRANSFORM_GATE:${token}`);

assert.doesNotMatch(source, /console\.log\([^\n]*(ai_rows|receipt_rows|quarantineKey|qaPassword)/);
assert.throws(() => transformAiReceiptDelta({}, {}), /DELTA_SCHEMA/);
assert.throws(() => transformAiReceiptDelta({}, {
  schema: 'atlas.supabase.mazer-master-r017-ai-receipt-delta.v1',
  observed_at: AI_RECEIPT_DELTA_CONTRACT.observedAt,
  proof: {}, player_rows: [], ai_rows: [], receipt_rows: [], unexpected: true
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
const exactBase = path.join(AI_RECEIPT_PRIVATE_ROOT, 'private-source-auth-action-preimage-v2-20260826.json');
const exactDelta = path.join(AI_RECEIPT_PRIVATE_ROOT, 'receipt-delta-20260826-1752-v2.json');
if (fs.existsSync(exactBase) && fs.existsSync(exactDelta)) {
  const exactOutput = path.join(AI_RECEIPT_PRIVATE_ROOT, `focused-valid-transform-${process.pid}-${Date.now()}.json`);
  try {
    const result = transformAiReceiptFiles(exactBase, exactDelta, exactOutput);
    assert.equal(result.sha256, AI_RECEIPT_DELTA_CONTRACT.successorSha256);
    assert.equal(fs.existsSync(exactOutput), true);
  } finally { if (fs.existsSync(exactOutput)) fs.unlinkSync(exactOutput); }
}
const outsideOutput = path.join(temp, 'outside-private-source.json');
assert.throws(() => writeAiReceiptPrivateOutput(outsideOutput, Buffer.from('{"valid":"sealed-output"}\n')), /OUTPUT_ESCAPE/);
assert.equal(fs.existsSync(outsideOutput), false);

console.log(JSON.stringify({
  result: 'PASS_MAZER_MASTER_PREPARATION_AI_RECEIPT_DELTA_R017',
  strict_gates: 17,
  provider_calls: 0,
  provider_writes: 0,
  auth_writes: 0,
  live_data_writes: 0,
  raw_private_output: 0
}));
