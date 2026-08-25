import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const producerPath = path.join(root, 'ops/atlas/produce_supabase_mazer_master_preparation_private_source_r017.mjs');
const materializerPath = path.join(root, 'ops/atlas/materialize_supabase_mazer_master_preparation_r017.mjs');
const testPath = path.join(root, 'ops/atlas/tests/test_supabase_mazer_master_preparation_private_source_r017.mjs');
const producer = fs.readFileSync(producerPath, 'utf8');
const materializer = fs.readFileSync(materializerPath, 'utf8');
const focused = fs.readFileSync(testPath, 'utf8');
const findings = [];
const requireToken = (source, token, finding) => { if (!source.includes(token)) findings.push(finding); };

for (const token of [
  'transaction isolation level serializable read only','PGDATABASE: databaseUrl','PRIVATE_OUTPUT_MUST_BE_UNDER_SECRETS','O_NOFOLLOW','O_EXCL',
  'EVIDENCE_DIGEST_DRIFT','SEALED_PREIMAGE_DENOMINATOR_DRIFT','IDENTITY_DENOMINATOR_DRIFT','NORMALIZED_EMAIL_DUPLICATE',
  'UNSUPPORTED_PASSWORD_VERIFIER','RESET_RECEIPT_DENOMINATOR_DRIFT','FRESH_LIVE_TABLES_PLUS_EXACT_M2_PLANNED_RPCS',
  'auth.users','auth.identities','mazer_identity_map','master_preimage','disable_hook_first','receipt_conservation',
  'CATALOG_PREIMAGE_ALREADY_MIGRATED','CATALOG_PREIMAGE_CONSTRAINT_MISSING','R017_EXISTING_AUTH_USER_DIGEST_DRIFT',
  'R017_IMPORT_USER_COLLISION','R017_IMPORTED_AUTH_USERS_DIGEST_DRIFT','R017_PROFILES_FULL_DIGEST_DRIFT',
  'R017_RECEIPT_CONSERVATION_FULL_DIGEST_DRIFT','R017_ROLLBACK_COLUMNS_DRIFT','REPARSE_COMPONENT_REJECTED',
  'PRIVATE_OUTPUT_FINAL_PATH_ESCAPE','drop function if exists mazer.mazer_before_user_created',
  'EMAIL_IDENTITY_PROVIDER_DRIFT','EMAIL_IDENTITY_PROVIDER_ID_DRIFT','EMAIL_IDENTITY_METADATA_SUB_DRIFT',
  'EMAIL_IDENTITY_METADATA_EMAIL_DRIFT','EMAIL_IDENTITY_METADATA_MALFORMED','EMAIL_IDENTITY_MULTIPLE'
]) requireToken(producer, token, `PRODUCER_CONTRACT_MISSING:${token}`);
for (const name of ['preflight.sql','master-fence.sql','master-refence.sql','auth-apply.sql','reset-era-apply.sql','postverify.sql','qa-apply.sql','qa-cleanup.sql','rollback.sql']) requireToken(producer, `sql['${name}']`, `SQL_RENDERER_MISSING:${name}`);
for (const token of ['source_snapshot?.ai','target_snapshot?.ai','source_snapshot?.player','target_snapshot?.player','wrapMigrationTransaction','MIGRATION_TRANSACTION_SHAPE']) requireToken(materializer, token, `MATERIALIZER_CONTRACT_MISSING:${token}`);
for (const token of ['identity_edges: 18','sql_programs: 9','materializer main executed more than once','NORMALIZED_EMAIL_DUPLICATE','PRIVATE_SECRET_INPUT_WEAK','IMPORT_IDENTITY_COLLISION','CATALOG_PREIMAGE_ALREADY_MIGRATED','MIGRATION_TRANSACTION_SHAPE','junction','EMAIL_IDENTITY_PROVIDER_DRIFT','EMAIL_IDENTITY_PROVIDER_ID_DRIFT','EMAIL_IDENTITY_METADATA_SUB_DRIFT','EMAIL_IDENTITY_METADATA_EMAIL_DRIFT','EMAIL_IDENTITY_METADATA_MALFORMED','EMAIL_IDENTITY_MISSING','EMAIL_IDENTITY_MULTIPLE']) requireToken(focused, token, `ADVERSARY_MISSING:${token}`);

for (const forbidden of ['apply_migration','execute_sql','supabase db push','vercel deploy','vercel promote','git push']) {
  if (producer.toLowerCase().includes(forbidden)) findings.push(`OUT_OF_SCOPE_EFFECT:${forbidden}`);
}
if (/console\.(log|error)\([^)]*(legacy|master|auth|email|password)/i.test(producer)) findings.push('POSSIBLE_PRIVATE_CONSOLE_OUTPUT');
if (producer.includes("spawnSync(psql, ['--no-psqlrc', '--quiet', '--tuples-only', '--no-align', '--set', 'ON_ERROR_STOP=1', databaseUrl")) findings.push('DATABASE_URL_EXPOSED_IN_ARGV');

function runFocused() {
  const child = spawnSync(process.execPath, [testPath], { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 300_000 });
  if (child.status !== 0 || child.signal || child.stderr.trim()) findings.push(`FOCUSED_FAILED:${child.status}:${child.signal ?? 'none'}`);
  return child.stdout.trim();
}
const first = runFocused(); const second = runFocused();
if (!first || first !== second) findings.push('FOCUSED_NONDETERMINISTIC');
if (first) {
  const result = JSON.parse(first);
  assert.equal(result.result, 'PASS_MAZER_MASTER_PREPARATION_PRIVATE_SOURCE_R017');
  assert.equal(result.provider_calls, 0); assert.equal(result.auth_writes, 0); assert.equal(result.raw_private_output, 0);
}

assert.deepEqual(findings, []);
console.log(JSON.stringify({ result: 'PASS_MAZER_MASTER_PREPARATION_PRIVATE_SOURCE_R017_REVIEW_NO_FINDINGS', findings: 0, focused_runs: 2, provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, deployments: 0 }));
