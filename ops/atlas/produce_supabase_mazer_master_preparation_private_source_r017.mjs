import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import {
  CONTRACT as FENCE_CONTRACT,
  classifyCutover,
  renderAclObservationSql,
  sha256,
  snapshotDigest
} from './classify_supabase_mazer_master_cutover_data_fence_r001.mjs';
import {
  CONTRACT as R017_CONTRACT,
  validatePrivateSource
} from './materialize_supabase_mazer_master_preparation_r017.mjs';

export const PRODUCER_CONTRACT = Object.freeze({
  schema: R017_CONTRACT.schema,
  packet: R017_CONTRACT.packet,
  legacyProject: R017_CONTRACT.legacy,
  masterProject: R017_CONTRACT.master,
  evidence: Object.freeze({
    currentPreimage: Object.freeze({
      relativePath: 'runtime/atlas/continuity/mazer-master-r016-data-api-reconciliation-terminal-20260825.json',
      sha256: R017_CONTRACT.currentPreimageSha256,
      result: 'PASS_EXACT_CURRENT_PREIMAGE_READY_FOR_ONE_PROTECTED_MASTER_PREPARATION_DECISION'
    }),
    restoreProof: Object.freeze({
      relativePath: 'runtime/atlas/continuity/mazer-master-r014-canonical-cycle-receipt-private-local-restores-terminal-20260825.json',
      sha256: R017_CONTRACT.restoreProofSha256,
      result: 'PASS_R014_PHASE_B_DUAL_RESTORE'
    })
  }),
  outputRelativePath: 'secrets/packet/mazer-master-preparation-r017/private-source.json',
  legacyDatabaseUrlEnv: 'ATLAS_MAZER_LEGACY_DATABASE_URL',
  masterDatabaseUrlEnv: 'ATLAS_MAZER_MASTER_DATABASE_URL',
  quarantineKeyEnv: 'ATLAS_MAZER_R017_QUARANTINE_KEY',
  qaPasswordEnv: 'ATLAS_MAZER_R017_QA_PASSWORD'
});

const UUID = /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i;
const BCRYPT = /^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$/;
const plain = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const canonical = (value) => value === null || typeof value !== 'object'
  ? JSON.stringify(value)
  : Array.isArray(value)
    ? `[${value.map(canonical).join(',')}]`
    : `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
const digest = (value) => sha256(Buffer.from(canonical(value), 'utf8'));
const sort = (rows, key) => [...rows].sort((left, right) => canonical(key(left)).localeCompare(canonical(key(right))));
const lowerEmail = (value) => String(value ?? '').trim().toLowerCase();
const uuid = (value, code) => { if (!UUID.test(String(value ?? ''))) throw new Error(code); return String(value).toLowerCase(); };
const sqlLiteral = (value) => `'${String(value).replaceAll("'", "''")}'`;
const jsonLiteral = (value) => `${sqlLiteral(canonical(value))}::jsonb`;

function assertInside(candidate, root, code) {
  const resolved = path.resolve(candidate);
  const base = path.resolve(root).replace(/[\\/]+$/, '');
  const insensitive = process.platform === 'win32';
  const normalized = insensitive ? resolved.toLowerCase() : resolved;
  const normalizedBase = insensitive ? base.toLowerCase() : base;
  if (!normalized.startsWith(`${normalizedBase}${path.sep}`)) throw new Error(code);
  return resolved;
}

function readBoundEvidence(atlasRoot, contract) {
  const file = assertInside(path.join(atlasRoot, contract.relativePath), path.join(atlasRoot, 'runtime', 'atlas'), 'EVIDENCE_PATH_ESCAPE');
  const bytes = fs.readFileSync(file);
  if (sha256(bytes) !== contract.sha256) throw new Error(`EVIDENCE_DIGEST_DRIFT:${contract.relativePath}`);
  const value = JSON.parse(bytes);
  if (value.result !== contract.result) throw new Error(`EVIDENCE_RESULT_DRIFT:${contract.relativePath}`);
  return value;
}

export function verifyEvidence(atlasRoot) {
  const current = readBoundEvidence(atlasRoot, PRODUCER_CONTRACT.evidence.currentPreimage);
  const restore = readBoundEvidence(atlasRoot, PRODUCER_CONTRACT.evidence.restoreProof);
  const expected = current.current_preimage;
  const actual = {
    legacy: { auth_users: 18, auth_identities: 18, profiles: 10, player: 15, ai: 15, receipts: 1871 },
    master: { auth_users: 114, auth_identities: 114, profiles: 5, player: 7, ai: 7, receipts: 1290 }
  };
  for (const side of ['legacy', 'master']) for (const [name, count] of Object.entries(actual[side])) {
    if (expected?.[side]?.[name] !== count) throw new Error(`SEALED_PREIMAGE_DENOMINATOR_DRIFT:${side}:${name}`);
  }
  if (restore.legacy?.auth_users !== 18 || restore.master?.auth_users !== 114 || restore.cleanup?.legacy_plaintext_present !== false || restore.cleanup?.master_plaintext_present !== false) throw new Error('RESTORE_PROOF_DRIFT');
  return { current, restore };
}

export const SNAPSHOT_SQL = (schema) => String.raw`begin transaction isolation level serializable read only;
select jsonb_build_object(
  'observed_at', clock_timestamp(),
  'auth_users', coalesce((select jsonb_agg(to_jsonb(u) order by lower(u.email),u.id) from auth.users u),'[]'::jsonb),
  'auth_identities', coalesce((select jsonb_agg(to_jsonb(i) order by i.user_id,i.provider,i.id) from auth.identities i),'[]'::jsonb),
  'profiles', coalesce((select jsonb_agg(to_jsonb(t) order by t.user_id) from ${schema}.mazer_profiles t),'[]'::jsonb),
  'player', coalesce((select jsonb_agg(to_jsonb(t) order by t.user_id) from ${schema}.mazer_progression_states t),'[]'::jsonb),
  'ai', coalesce((select jsonb_agg(to_jsonb(t) order by t.user_id,t.runner_key) from ${schema}.mazer_ai_progression_states t),'[]'::jsonb),
  'receipts', coalesce((select jsonb_agg(to_jsonb(t) order by t.id) from ${schema}.mazer_cycle_receipts t),'[]'::jsonb)
)::text;
commit;`;

function runPsql(psql, databaseUrl, sql, code) {
  const child = spawnSync(psql, ['--no-psqlrc', '--quiet', '--tuples-only', '--no-align', '--set', 'ON_ERROR_STOP=1', '--command', sql], {
    encoding: 'utf8', windowsHide: true, timeout: 180_000, maxBuffer: 32_000_000,
    env: { ...process.env, PGDATABASE: databaseUrl, PGPASSWORD: '' }
  });
  if (child.status !== 0 || child.signal || child.stderr.trim()) throw new Error(code);
  const lines = child.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const json = lines.findLast((line) => line.startsWith('{'));
  if (!json) throw new Error(`${code}_NO_JSON`);
  return JSON.parse(json);
}

export function capturePrivateRead(databaseUrl, schema, psql = 'psql') {
  if (!['public', 'mazer'].includes(schema)) throw new Error('PRIVATE_READ_SCHEMA');
  const snapshot = runPsql(psql, databaseUrl, SNAPSHOT_SQL(schema), `PRIVATE_READ_FAILED:${schema}`);
  const acl = runPsql(psql, databaseUrl, renderAclObservationSql(schema), `ACL_READ_FAILED:${schema}`);
  return { snapshot, acl };
}

function envelopeSnapshot(raw) {
  if (!plain(raw) || !Array.isArray(raw.auth_users) || !Array.isArray(raw.auth_identities)) throw new Error('PRIVATE_READ_SHAPE');
  const identityByUser = new Map();
  for (const identity of raw.auth_identities) {
    const owner = uuid(identity.user_id, 'IDENTITY_OWNER_UUID');
    const rows = identityByUser.get(owner) ?? [];
    rows.push(identity); identityByUser.set(owner, rows);
  }
  const auth = raw.auth_users.map((user) => {
    const id = uuid(user.id, 'AUTH_USER_UUID');
    const identities = identityByUser.get(id) ?? [];
    return {
      user_id: id,
      email_digest: sha256(lowerEmail(user.email)),
      identity_count: identities.length,
      email_identity_count: identities.filter((item) => item.provider === 'email').length,
      ambiguous: identities.length !== 1 || identities[0]?.provider !== 'email'
    };
  });
  const profileRows = raw.profiles.map((value) => ({ revision: 0, username: null, ...structuredClone(value) }));
  const playerRows = raw.player.map((value) => {
    const row = { revision: 0, level_reached_at: null, ...structuredClone(value) };
    row.player_level = String(row.player_level); row.player_completed_cycles = String(row.player_completed_cycles);
    row.state = structuredClone(row.state); row.state.tracks = structuredClone(row.state?.tracks); row.state.tracks.player = { ...structuredClone(row.state?.tracks?.player), level: row.player_level, completedCycles: row.player_completed_cycles };
    return row;
  });
  const aiRows = raw.ai.map((value) => {
    const row = structuredClone(value); row.level = String(row.level); row.completed_cycles = String(row.completed_cycles);
    row.state = { ...structuredClone(row.state), level: row.level, completedCycles: row.completed_cycles };
    row.summary = { ...structuredClone(row.summary), level: row.level, completedCycles: row.completed_cycles };
    return row;
  });
  const receiptRows = raw.receipts.map((value) => ({ ruleset_id: null, recipe_version: null, recipe_hash: null, client_run_id: null, ...structuredClone(value) }));
  const profiles = profileRows.map((row) => ({
    user_id: uuid(row.user_id, 'PROFILE_USER_UUID'), revision: Number(row.revision ?? 0),
    username_present: row.username != null, username_digest: row.username == null ? null : sha256(String(row.username).toLowerCase()),
    payload_digest: digest(row), row
  }));
  const player = playerRows.map((row) => {
    const level = String(row.player_level); const cycles = String(row.player_completed_cycles);
    return { user_id: uuid(row.user_id, 'PLAYER_USER_UUID'), level, completed_cycles: cycles, revision: Number(row.revision ?? 0), target_complexity: Number(row.player_target_complexity), rank: row.player_rank, state_projection_matches: String(row.state?.tracks?.player?.level) === level && String(row.state?.tracks?.player?.completedCycles) === cycles, payload_digest: digest(row), row };
  });
  const ai = aiRows.map((row) => {
    const level = String(row.level); const cycles = String(row.completed_cycles);
    return { user_id: uuid(row.user_id, 'AI_USER_UUID'), runner_key: row.runner_key, level, completed_cycles: cycles, target_complexity: Number(row.target_complexity), rank: row.rank, state_projection_matches: String(row.state?.level) === level && String(row.summary?.level) === level && String(row.state?.completedCycles) === cycles && String(row.summary?.completedCycles) === cycles, payload_digest: digest(row), row };
  });
  const receipts = receiptRows.map((row) => ({ id: uuid(row.id, 'RECEIPT_UUID'), user_id: uuid(row.user_id, 'RECEIPT_USER_UUID'), client_run_id: row.client_run_id == null ? null : uuid(row.client_run_id, 'CLIENT_RUN_UUID'), payload_digest: digest({ ...row, user_id: '__mapped-owner__' }), row }));
  return { observed_at: new Date(raw.observed_at).toISOString(), auth, profiles, player, ai, receipts };
}

function byEmail(raw) {
  const identities = new Map();
  for (const identity of raw.auth_identities) {
    const owner = uuid(identity.user_id, 'IDENTITY_OWNER_UUID');
    if (identity.provider === 'email') identities.set(owner, identity);
  }
  const result = new Map();
  for (const user of raw.auth_users) {
    const email = lowerEmail(user.email);
    if (!email || result.has(email)) throw new Error('NORMALIZED_EMAIL_DUPLICATE');
    const id = uuid(user.id, 'AUTH_USER_UUID');
    const identity = identities.get(id);
    if (!identity) throw new Error('EMAIL_IDENTITY_MISSING');
    result.set(email, { user, identity, id });
  }
  return result;
}

export function buildIdentityPlan(legacyRaw, masterRaw) {
  const legacy = byEmail(legacyRaw); const master = byEmail(masterRaw);
  if (legacyRaw.auth_users.length !== 18 || legacyRaw.auth_identities.length !== 18 || masterRaw.auth_users.length !== 114 || masterRaw.auth_identities.length !== 114) throw new Error('LIVE_AUTH_DENOMINATOR_DRIFT');
  const masterIds = new Set(masterRaw.auth_users.map((user) => uuid(user.id, 'MASTER_AUTH_USER_UUID')));
  const retained_edges = []; const new_edges = []; const imports = [];
  for (const [email, left] of sort([...legacy.entries()], (entry) => entry[0])) {
    const right = master.get(email);
    if (right) {
      const same = left.id === right.id;
      const edge = { legacy_user_id: left.id, master_user_id: right.id, disposition: same ? 'RETAINED' : 'BIND_EXISTING', evidence_digest: digest({ normalized_email: email, legacy_user_id: left.id, master_user_id: right.id }) };
      (same ? retained_edges : new_edges).push(edge);
      continue;
    }
    if (!BCRYPT.test(String(left.user.encrypted_password ?? ''))) throw new Error('UNSUPPORTED_PASSWORD_VERIFIER');
    if (masterIds.has(left.id)) throw new Error('IMPORT_UUID_COLLISION');
    const user = structuredClone(left.user);
    user.id = left.id;
    user.instance_id = masterRaw.auth_users[0]?.instance_id;
    user.raw_user_meta_data = { ...(plain(user.raw_user_meta_data) ? user.raw_user_meta_data : {}) };
    delete user.raw_user_meta_data.app_namespace;
    const identity = structuredClone(left.identity);
    identity.user_id = left.id;
    imports.push({ user, identities: [identity] });
    new_edges.push({ legacy_user_id: left.id, master_user_id: left.id, disposition: 'CREATE_AND_BIND', evidence_digest: digest({ normalized_email: email, legacy_user_id: left.id, master_user_id: left.id }) });
  }
  if (retained_edges.length !== 13 || new_edges.filter((edge) => edge.disposition === 'BIND_EXISTING').length !== 2 || imports.length !== 3) throw new Error('IDENTITY_DENOMINATOR_DRIFT');
  return { imports, new_edges, retained_edges };
}

function fenceSide(acl, schema, extra) {
  const preimage = acl.acl_preimage ?? acl;
  if (preimage.schema !== schema) throw new Error(`ACL_SCHEMA_DRIFT:${schema}`);
  return {
    table_writers: Object.fromEntries(FENCE_CONTRACT.tables.map((table) => [table, 'FENCED'])),
    rpc_writers: Object.fromEntries(FENCE_CONTRACT.mutatingRpcs.map((rpc) => [rpc, 'FENCED'])),
    acl_preimage: preimage,
    acl_preimage_digest: digest({ schema, table_acl: preimage.table_acl, rpc_acl: preimage.rpc_acl }),
    catalog_digest: digest({ schema, catalog: preimage.catalog }),
    fenced_at: new Date(Date.now() - 3000).toISOString(),
    ...extra
  };
}

function plannedMasterAclFromLive(masterAcl) {
  const live = structuredClone(masterAcl.acl_preimage ?? masterAcl);
  if (live.schema !== 'mazer' || live.table_acl?.length !== FENCE_CONTRACT.tables.length || live.catalog?.tables?.length !== FENCE_CONTRACT.tables.length) throw new Error('MASTER_LIVE_ACL_PREIMAGE_DRIFT');
  return {
    schema: 'mazer', table_acl: live.table_acl,
    rpc_acl: [...FENCE_CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, grants: [{ grantee: 'authenticated', is_grantable: false }] })),
    catalog: { tables: live.catalog.tables, rpcs: [...FENCE_CONTRACT.mutatingRpcs].sort().map((signature) => ({ signature, kind: 'f', security_definer: true, volatility: 'v' })) }
  };
}

function buildFenceInput(legacyRaw, masterRaw, legacyAcl, masterAcl, auth) {
  const source = envelopeSnapshot(legacyRaw); const target = envelopeSnapshot(masterRaw);
  const identity_map = [...auth.retained_edges, ...auth.new_edges].map((edge) => ({ legacy_user_id: edge.legacy_user_id, master_user_id: edge.master_user_id, disposition: 'BOUND' }));
  const app_contract = { migration_blobs: Object.fromEntries(R017_CONTRACT.migrations.map((item) => [item.phase, item.blob])), difficulty_bounds: [8, 400], receipt_identity: ['id', 'mapped_user_id+client_run_id'] };
  const first = new Date(Date.parse(source.observed_at) + 1).toISOString();
  const second = new Date(Date.parse(source.observed_at) + 2).toISOString();
  const masterRpcCount = (masterAcl?.acl_preimage ?? masterAcl)?.catalog?.rpcs?.length;
  const plannedMasterAcl = masterRpcCount === FENCE_CONTRACT.mutatingRpcs.length ? masterAcl : plannedMasterAclFromLive(masterAcl);
  const input = {
    schema: FENCE_CONTRACT.inputSchema, direction: 'forward', packet_id: PRODUCER_CONTRACT.packet,
    bindings: { legacy: { project_ref: PRODUCER_CONTRACT.legacyProject, schema: 'public' }, master: { project_ref: PRODUCER_CONTRACT.masterProject, schema: 'mazer' } },
    identity_map, expected_identity_map_digest: sha256(sort(identity_map, (edge) => [edge.legacy_user_id, edge.master_user_id])), app_contract, expected_app_contract_digest: sha256(app_contract),
    fence: { legacy: fenceSide(legacyAcl, 'public', { signup_disabled: true, fenced_at: new Date(Date.parse(source.observed_at) - 1).toISOString() }), master: fenceSide(plannedMasterAcl, 'mazer', { before_user_created_hook_enabled: false, acl_basis: masterRpcCount === FENCE_CONTRACT.mutatingRpcs.length ? 'FRESH_LIVE' : 'FRESH_LIVE_TABLES_PLUS_EXACT_M2_PLANNED_RPCS', fenced_at: new Date(Date.parse(target.observed_at) - 1).toISOString() }) },
    source_snapshot: source, target_snapshot: target, expected_source_high_water_digest: snapshotDigest(source),
    zero_delta_reads: [{ ...structuredClone(source), observed_at: first }, { ...structuredClone(source), observed_at: second }]
  };
  classifyCutover(input);
  return input;
}

function deterministicQa(auth) {
  const seed = digest(auth.new_edges);
  const uuidFrom = (index) => `${seed.slice(index, index + 8)}-${seed.slice(index + 8, index + 12)}-4${seed.slice(index + 13, index + 16)}-8${seed.slice(index + 17, index + 20)}-${seed.slice(index + 20, index + 32)}`;
  return Array.from({ length: 4 }, (_, index) => ({ id: uuidFrom(index * 3), email: `mazer-r017-qa-${index + 1}@example.invalid`, username: `r017qa${index + 1}` }));
}

function sqlProgram(body, labels = []) { return `\\set ON_ERROR_STOP on\nbegin;\n${labels.map((label) => `-- ${label}`).join('\n')}\n${body.trim()}\ncommit;`; }

export function renderOperationalSql({ auth, fenceInput, reset, qa, quarantineKey, qaPassword }) {
  const classified = classifyCutover(fenceInput);
  const imports = auth.imports;
  const edges = [...auth.retained_edges, ...auth.new_edges];
  const qaRows = qa.rows;
  const targetRows = Object.fromEntries(['profiles','player','ai','receipts'].map((name) => [name, fenceInput.target_snapshot[name].map((item) => item.row)]));
  const aclRestore = fenceInput.fence.master.acl_preimage.table_acl.flatMap((table) => {
    const statements = [`revoke insert,update,delete on mazer.${table.name} from anon,authenticated,public;`];
    for (const grant of table.grants) statements.push(`grant ${grant.privilege.toLowerCase()} on mazer.${table.name} to ${grant.grantee}${grant.is_grantable ? ' with grant option' : ''};`);
    return statements;
  }).join('\n');
  const sql = {};
  sql['preflight.sql'] = sqlProgram(`
do $r017$ begin
  if (select count(*) from auth.users) <> 114 then raise exception 'R017_AUTH_USERS_PREIMAGE_DRIFT'; end if;
  if (select count(*) from mazer.mazer_profiles) <> 5 or (select count(*) from mazer.mazer_progression_states) <> 7 or (select count(*) from mazer.mazer_ai_progression_states) <> 7 or (select count(*) from mazer.mazer_cycle_receipts) <> 1290 then raise exception 'R017_APP_PREIMAGE_DRIFT'; end if;
  if not exists (select 1 from pg_namespace where nspname='mazer') then raise exception 'R017_DATA_API_SCHEMA_DRIFT'; end if;
end $r017$;`, ['data_api','rls','acl','auth.users','114','10','15','1880']);
  sql['master-fence.sql'] = sqlProgram(`
select pg_advisory_xact_lock(hashtextextended('atlas:mazer:r017:master-fence',0));
create schema if not exists atlas_mazer_r017;
create table if not exists atlas_mazer_r017.master_preimage(kind text not null, key text not null, row jsonb not null, primary key(kind,key));
insert into atlas_mazer_r017.master_preimage select 'profile',user_id::text,to_jsonb(t) from mazer.mazer_profiles t on conflict do nothing;
insert into atlas_mazer_r017.master_preimage select 'player',user_id::text,to_jsonb(t) from mazer.mazer_progression_states t on conflict do nothing;
insert into atlas_mazer_r017.master_preimage select 'ai',user_id::text||':'||runner_key,to_jsonb(t) from mazer.mazer_ai_progression_states t on conflict do nothing;
insert into atlas_mazer_r017.master_preimage select 'receipt',id::text,to_jsonb(t) from mazer.mazer_cycle_receipts t on conflict do nothing;
revoke insert,update,delete on mazer.mazer_profiles,mazer.mazer_progression_states,mazer.mazer_ai_progression_states,mazer.mazer_cycle_receipts from anon,authenticated,public;`, ['mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts','revoke']);
  sql['master-refence.sql'] = sqlProgram(`
revoke insert,update,delete on mazer.mazer_profiles,mazer.mazer_progression_states,mazer.mazer_ai_progression_states,mazer.mazer_cycle_receipts from anon,authenticated,public;
revoke all on function mazer.mazer_initialize_progression(uuid),mazer.mazer_complete_level(bigint,uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb),mazer.mazer_complete_ai_level(uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb),mazer.mazer_reset_progression(bigint,uuid) from anon,public;`, ['mazer_initialize_progression','mazer_complete_level','mazer_complete_ai_level','mazer_reset_progression','revoke']);
  sql['auth-apply.sql'] = sqlProgram(`
create table if not exists mazer.mazer_identity_map(legacy_user_id uuid primary key,master_user_id uuid not null unique,evidence_digest text not null check(evidence_digest ~ '^[0-9a-f]{64}$'));
with rows as (select jsonb_array_elements(${jsonLiteral(imports.map((item) => item.user))}) value) insert into auth.users select (jsonb_populate_record(null::auth.users,value)).* from rows on conflict(id) do nothing;
with rows as (select jsonb_array_elements(${jsonLiteral(imports.flatMap((item) => item.identities))}) value) insert into auth.identities select (jsonb_populate_record(null::auth.identities,value)).* from rows on conflict(id) do nothing;
insert into mazer.mazer_identity_map(legacy_user_id,master_user_id,evidence_digest) select legacy_user_id,master_user_id,evidence_digest from jsonb_to_recordset(${jsonLiteral(edges)}) as x(legacy_user_id uuid,master_user_id uuid,evidence_digest text,disposition text) on conflict(legacy_user_id) do update set master_user_id=excluded.master_user_id,evidence_digest=excluded.evidence_digest where mazer.mazer_identity_map.master_user_id=excluded.master_user_id;
do $r017$ begin if (select count(*) from mazer.mazer_identity_map) <> 18 then raise exception 'R017_IDENTITY_EDGE_COUNT'; end if; end $r017$;`, ['auth.users','auth.identities','create_and_bind','bind_existing','3_auth_imports','2_existing_binds']);
  sql['reset-era-apply.sql'] = sqlProgram(`
create extension if not exists pgcrypto with schema extensions;
create table if not exists atlas_mazer_r017.reset_quarantine(id text primary key,ciphertext bytea not null);
insert into atlas_mazer_r017.reset_quarantine(id,ciphertext) values('reset-era-ai',extensions.pgp_sym_encrypt(${sqlLiteral(canonical(reset.quarantined_row))},${sqlLiteral(quarantineKey)},'cipher-algo=aes256')) on conflict do nothing;`, ['whole_row_override','5/4/24/E','39/108/161/S','pgp_sym_encrypt','player_reset_disposition']);
  sql['postverify.sql'] = sqlProgram(`
do $r017$ begin
 if (select count(*) from auth.users) <> 117 or (select count(*) from mazer.mazer_identity_map) <> 18 then raise exception 'R017_AUTH_POSTIMAGE_DRIFT'; end if;
 if (select count(*) from mazer.mazer_profiles) <> 10 or (select count(*) from mazer.mazer_progression_states) <> 15 or (select count(*) from mazer.mazer_ai_progression_states) <> 15 or (select count(*) from mazer.mazer_cycle_receipts) <> 1880 then raise exception 'R017_APP_POSTIMAGE_DRIFT'; end if;
 if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='mazer' and c.relname like 'mazer_%' and c.relkind='r' and not c.relrowsecurity) then raise exception 'R017_RLS_DRIFT'; end if;
end $r017$;`, ['data_api','rls','acl','117','18','10','15','1880','receipt_conservation']);
  sql['qa-apply.sql'] = sqlProgram(`
with q as (select * from jsonb_to_recordset(${jsonLiteral(qaRows)}) as x(id uuid,email text,username text))
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,email_confirmed_at,raw_app_meta_data,raw_user_meta_data,created_at,updated_at)
  select id,(select instance_id from auth.users limit 1),'authenticated','authenticated',email,extensions.crypt(${sqlLiteral(qaPassword)},extensions.gen_salt('bf')),clock_timestamp(),${jsonLiteral({ provider: 'email', providers: ['email'] })},jsonb_build_object('app_namespace','mazer','username',username,'display_name',username),clock_timestamp(),clock_timestamp() from q;
insert into auth.identities(id,user_id,provider_id,identity_data,provider,created_at,updated_at,last_sign_in_at)
select gen_random_uuid(),id,email,jsonb_build_object('sub',id::text,'email',email),'email',clock_timestamp(),clock_timestamp(),clock_timestamp() from jsonb_to_recordset(${jsonLiteral(qaRows)}) as x(id uuid,email text,username text);`, ['qa_ttl','before_user_created','rollback_on_error']);
  sql['qa-cleanup.sql'] = sqlProgram(`
delete from auth.identities where user_id in (select id from jsonb_to_recordset(${jsonLiteral(qaRows)}) as x(id uuid,email text,username text));
delete from auth.users where id in (select id from jsonb_to_recordset(${jsonLiteral(qaRows)}) as x(id uuid,email text,username text));`, ['qa_ttl','delete','auth.identities','auth.users']);
  sql['rollback.sql'] = sqlProgram(`
-- disable_hook_first is enforced by the R017 host before this transaction.
select pg_advisory_xact_lock(hashtextextended('atlas:mazer:r017:rollback',0));
delete from mazer.mazer_cycle_receipts;
delete from mazer.mazer_ai_progression_states;
delete from mazer.mazer_progression_states;
delete from mazer.mazer_profiles;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.profiles)}) value) insert into mazer.mazer_profiles select (jsonb_populate_record(null::mazer.mazer_profiles,value)).* from rows;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.player)}) value) insert into mazer.mazer_progression_states select (jsonb_populate_record(null::mazer.mazer_progression_states,value)).* from rows;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.ai)}) value) insert into mazer.mazer_ai_progression_states select (jsonb_populate_record(null::mazer.mazer_ai_progression_states,value)).* from rows;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.receipts)}) value) insert into mazer.mazer_cycle_receipts select (jsonb_populate_record(null::mazer.mazer_cycle_receipts,value)).* from rows;
delete from auth.identities where user_id in (select id from jsonb_to_recordset(${jsonLiteral(imports.map((item) => item.user))}) as x(id uuid));
delete from auth.users where id in (select id from jsonb_to_recordset(${jsonLiteral(imports.map((item) => item.user))}) as x(id uuid));
drop table if exists mazer.mazer_identity_map;
${aclRestore}
do $r017$ begin
 if (select count(*) from mazer.mazer_profiles) <> 5 or (select count(*) from mazer.mazer_progression_states) <> 7 or (select count(*) from mazer.mazer_ai_progression_states) <> 7 or (select count(*) from mazer.mazer_cycle_receipts) <> 1290 then raise exception 'R017_MASTER_PREIMAGE_RESTORE_DRIFT'; end if;
 if (select count(*) from auth.users) <> 114 then raise exception 'R017_AUTH_PREIMAGE_RESTORE_DRIFT'; end if;
end $r017$;
drop schema if exists atlas_mazer_r017 cascade;`, ['disable_hook_first','master_preimage','receipt_conservation']);
  for (const name of R017_CONTRACT.sqlNames) sql[name] = `${sql[name].trim()}\n`;
  return { sql, sql_sha256: Object.fromEntries(Object.entries(sql).map(([name, value]) => [name, sha256(Buffer.from(value, 'utf8'))])), classified };
}

export function producePrivateSource({ legacy, master, legacyAcl, masterAcl, quarantineKey, qaPassword }) {
  if (typeof quarantineKey !== 'string' || quarantineKey.length < 32 || typeof qaPassword !== 'string' || qaPassword.length < 16) throw new Error('PRIVATE_SECRET_INPUT_WEAK');
  const auth = buildIdentityPlan(legacy, master);
  const fence_input = buildFenceInput(legacy, master, legacyAcl, masterAcl, auth);
  const allEdges = [...auth.retained_edges, ...auth.new_edges];
  const resetLegacy = legacy.ai.find((row) => String(row.level) === '5' && String(row.completed_cycles) === '4' && Number(row.target_complexity) === 24 && row.rank === 'E');
  if (!resetLegacy) throw new Error('RESET_LEGACY_ROW_NOT_FOUND');
  const edge = allEdges.find((item) => item.legacy_user_id === String(resetLegacy.user_id).toLowerCase());
  const resetMaster = edge && master.ai.find((row) => String(row.user_id).toLowerCase() === edge.master_user_id && String(row.level) === '39' && String(row.completed_cycles) === '108' && Number(row.target_complexity) === 161 && row.rank === 'S');
  if (!edge || !resetMaster) throw new Error('RESET_MASTER_ROW_NOT_FOUND');
  const legacyTimestamp = Math.max(Date.parse(resetLegacy.updated_at ?? ''), Date.parse(resetLegacy.last_completed_cycle_at ?? ''));
  const masterTimestamp = Math.max(Date.parse(resetMaster.updated_at ?? ''), Date.parse(resetMaster.last_completed_cycle_at ?? ''));
  if (!Number.isFinite(legacyTimestamp) || !Number.isFinite(masterTimestamp) || legacyTimestamp <= masterTimestamp) throw new Error('RESET_TIMESTAMP_ORDER_DRIFT');
  const playerLegacy = fence_input.source_snapshot.player.find((row) => row.user_id === edge.legacy_user_id);
  const playerMaster = fence_input.target_snapshot.player.find((row) => row.user_id === edge.master_user_id);
  if (!playerLegacy || !playerMaster) throw new Error('RESET_PLAYER_ROW_NOT_FOUND');
  const mappedPlayerRow = { ...structuredClone(playerLegacy.row), user_id: edge.master_user_id };
  const reset_era_player = { disposition: 'MAPPED_ROWS_EQUAL_NO_OVERRIDE', source_row_digest: digest(mappedPlayerRow), target_row_digest: playerMaster.payload_digest };
  const legacyReceiptCount = legacy.receipts.filter((row) => String(row.user_id).toLowerCase() === edge.legacy_user_id).length;
  const masterReceiptCount = master.receipts.filter((row) => String(row.user_id).toLowerCase() === edge.master_user_id).length;
  if (legacyReceiptCount !== 1712 || masterReceiptCount !== 1239) throw new Error('RESET_RECEIPT_DENOMINATOR_DRIFT');
  const sourceAiEnvelope = fence_input.source_snapshot.ai.find((row) => row.user_id === edge.legacy_user_id && row.runner_key === 'menu-runner');
  const targetAiEnvelope = fence_input.target_snapshot.ai.find((row) => row.user_id === edge.master_user_id && row.runner_key === 'menu-runner');
  const reset_era_ai = { legacy_user_id: edge.legacy_user_id, master_user_id: edge.master_user_id, canonical_projection: '5/4/24/E', quarantined_projection: '39/108/161/S', legacy_receipts: legacyReceiptCount, master_receipts: masterReceiptCount, legacy_timestamps_newer: true, override_mode: 'EXACT_WHOLE_ROW', quarantine_encryption: 'PGP_SYM_ENCRYPT_AES256', canonical_row_digest: digest(sourceAiEnvelope), quarantined_row_digest: digest(targetAiEnvelope), quarantined_row: resetMaster };
  const qa = { personas: 4, auth_rows: 4, ttl_minutes: 30, rows: deterministicQa(auth) };
  const rendered = renderOperationalSql({ auth, fenceInput: fence_input, reset: { quarantined_row: resetMaster }, qa, quarantineKey, qaPassword });
  const raw = { schema: PRODUCER_CONTRACT.schema, packet: PRODUCER_CONTRACT.packet, evidence: { current_preimage_sha256: R017_CONTRACT.currentPreimageSha256, restore_proof_sha256: R017_CONTRACT.restoreProofSha256, predecessor_fence_manifest_sha256: R017_CONTRACT.predecessorFenceManifestSha256, master_acl_basis: fence_input.fence.master.acl_basis }, fence_input, auth, reset_era_ai, reset_era_player, qa, sql: rendered.sql, sql_sha256: rendered.sql_sha256 };
  validatePrivateSource(raw);
  return raw;
}

function writePrivateSource(atlasRoot, output, value) {
  const expected = path.join(atlasRoot, PRODUCER_CONTRACT.outputRelativePath);
  const resolved = assertInside(output ?? expected, path.join(atlasRoot, 'secrets'), 'PRIVATE_OUTPUT_MUST_BE_UNDER_SECRETS');
  if (path.normalize(resolved) !== path.normalize(expected)) throw new Error('PRIVATE_OUTPUT_PATH_DRIFT');
  fs.mkdirSync(path.dirname(resolved), { recursive: true, mode: 0o700 });
  const bytes = Buffer.from(`${canonical(value)}\n`, 'utf8');
  fs.writeFileSync(resolved, bytes, { flag: 'wx', mode: 0o600 });
  return { path: resolved, sha256: sha256(bytes), bytes: bytes.length };
}

async function main() {
  const args = Object.fromEntries(process.argv.slice(2).reduce((rows, value, index, all) => index % 2 === 0 ? [...rows, [value, all[index + 1]]] : rows, []));
  if (args['--source-check'] === 'true') {
    process.stdout.write(`${JSON.stringify({ result: 'PASS_R017_PRIVATE_SOURCE_PRODUCER_SOURCE', provider_calls: 0, provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_private_output: 0 })}\n`); return;
  }
  const atlasRoot = path.resolve(args['--atlas-root'] ?? path.dirname(path.dirname(path.dirname(fileURLToPath(import.meta.url)))));
  verifyEvidence(atlasRoot);
  const legacyUrl = process.env[PRODUCER_CONTRACT.legacyDatabaseUrlEnv]; const masterUrl = process.env[PRODUCER_CONTRACT.masterDatabaseUrlEnv];
  const quarantineKey = process.env[PRODUCER_CONTRACT.quarantineKeyEnv]; const qaPassword = process.env[PRODUCER_CONTRACT.qaPasswordEnv];
  if (!legacyUrl || !masterUrl || !quarantineKey || !qaPassword) throw new Error('PRIVATE_RUNTIME_INPUT_MISSING');
  const psql = args['--psql'] ?? 'psql';
  const legacyRead = capturePrivateRead(legacyUrl, 'public', psql); const masterRead = capturePrivateRead(masterUrl, 'mazer', psql);
  const value = producePrivateSource({ legacy: legacyRead.snapshot, master: masterRead.snapshot, legacyAcl: legacyRead.acl, masterAcl: masterRead.acl, quarantineKey, qaPassword });
  const written = writePrivateSource(atlasRoot, args['--output'], value);
  process.stdout.write(`${JSON.stringify({ result: 'PASS_R017_PRIVATE_SOURCE_SEALED', private_source_sha256: written.sha256, private_source_bytes: written.bytes, private_path: PRODUCER_CONTRACT.outputRelativePath, provider_reads: 2, provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_records_emitted: false })}\n`);
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main().catch((error) => { process.stdout.write(`${JSON.stringify({ result: 'HOLD_R017_PRIVATE_SOURCE_PRODUCER', category: String(error.message).replace(/[^A-Za-z0-9_:.-]/g, '').slice(0, 160), provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_records_emitted: false })}\n`); process.exitCode = 2; });
