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
  RECEIPT_CATCHUP_CONTRACT,
  validatePrivateSource
} from './materialize_supabase_mazer_master_preparation_r017.mjs';

export const PRODUCER_CONTRACT = Object.freeze({
  schema: R017_CONTRACT.schema,
  packet: R017_CONTRACT.packet,
  legacyProject: R017_CONTRACT.legacy,
  masterProject: R017_CONTRACT.master,
  evidence: Object.freeze({
    currentPreimage: Object.freeze({
      relativePath: 'runtime/atlas/continuity/mazer-master-r017-bounded-auth-progression-delta-evidence-20260826.json',
      sha256: R017_CONTRACT.currentPreimageSha256,
      result: 'PASS_EXACT_BOUNDED_AUTH_AND_PROGRESSION_DELTA_READY_FOR_R017_REPLAY'
    }),
    topology: Object.freeze({
      relativePath: 'runtime/atlas/continuity/mazer-master-r017-postrollback-auth-identity-topology-evidence-20260826.json',
      sha256: R017_CONTRACT.topologyEvidenceSha256,
      result: 'PASS_EXACT_POSTROLLBACK_AUTH_IDENTITY_TOPOLOGY_READY_FOR_R017_REPLAY'
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

function sqlStringValue(sql, pattern, code) {
  const match = pattern.exec(sql);
  if (!match) throw new Error(code);
  return match[1].replaceAll("''", "'");
}

export function readRuntimeSecretsFromBase(atlasRoot, file, expectedSha256) {
  if (!file || !/^[0-9a-f]{64}$/.test(String(expectedSha256 ?? ''))) throw new Error('SECRET_BASE_BINDING_MISSING');
  const packetRoot = path.join(atlasRoot, 'secrets', 'packet', 'mazer-master-preparation-r017');
  const resolved = assertInside(file, packetRoot, 'SECRET_BASE_PATH_ESCAPE');
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) throw new Error('SECRET_BASE_MISSING');
  assertNoReparseComponents(resolved, path.join(atlasRoot, 'secrets'));
  const bytes = fs.readFileSync(resolved);
  if (sha256(bytes) !== expectedSha256) throw new Error('SECRET_BASE_DIGEST_DRIFT');
  const raw = JSON.parse(bytes.toString('utf8'));
  if (!plain(raw.sql) || typeof raw.sql['reset-era-apply.sql'] !== 'string' || typeof raw.sql['qa-apply.sql'] !== 'string') throw new Error('SECRET_BASE_SHAPE');
  return {
    quarantineKey: sqlStringValue(raw.sql['reset-era-apply.sql'], /pgp_sym_encrypt\('(?:''|[^'])*','((?:''|[^'])*)','cipher-algo=aes256'\)/, 'QUARANTINE_KEY_PARSE'),
    qaPassword: sqlStringValue(raw.sql['qa-apply.sql'], /extensions\.crypt\('((?:''|[^'])*)',extensions\.gen_salt\('bf'\)\)/, 'QA_PASSWORD_PARSE'),
    resetBinding: {
      legacy_user_id: uuid(raw.reset_era_ai?.legacy_user_id, 'SECRET_BASE_RESET_LEGACY_UUID'),
      master_user_id: uuid(raw.reset_era_ai?.master_user_id, 'SECRET_BASE_RESET_MASTER_UUID')
    }
  };
}

function assertInside(candidate, root, code) {
  const resolved = path.resolve(candidate);
  const base = path.resolve(root).replace(/[\\/]+$/, '');
  const insensitive = process.platform === 'win32';
  const normalized = insensitive ? resolved.toLowerCase() : resolved;
  const normalizedBase = insensitive ? base.toLowerCase() : base;
  if (!normalized.startsWith(`${normalizedBase}${path.sep}`)) throw new Error(code);
  return resolved;
}

export function assertNoReparseComponents(candidate, stopAt) {
  const resolved = path.resolve(candidate); const stop = path.resolve(stopAt);
  assertInside(resolved, path.dirname(stop), 'REPARSE_SCOPE_ESCAPE');
  const relative = path.relative(path.dirname(stop), resolved);
  let cursor = path.dirname(stop);
  for (const component of relative.split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, component);
    if (!fs.existsSync(cursor)) continue;
    const stat = fs.lstatSync(cursor, { bigint: false });
    if (stat.isSymbolicLink()) throw new Error('REPARSE_COMPONENT_REJECTED');
    const real = fs.realpathSync.native(cursor);
    if (path.normalize(real) !== path.normalize(cursor)) throw new Error('REPARSE_COMPONENT_REJECTED');
  }
  return resolved;
}

function mkdirPrivateChain(directory, secretsRoot) {
  const root = assertNoReparseComponents(secretsRoot, secretsRoot);
  if (!fs.existsSync(root)) throw new Error('SECRETS_ROOT_MISSING');
  const relative = path.relative(root, path.resolve(directory));
  let cursor = root;
  for (const component of relative.split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, component);
    if (!fs.existsSync(cursor)) fs.mkdirSync(cursor, { mode: 0o700 });
    assertNoReparseComponents(cursor, root);
    if (!fs.statSync(cursor).isDirectory()) throw new Error('PRIVATE_PARENT_NOT_DIRECTORY');
  }
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
  const topology = readBoundEvidence(atlasRoot, PRODUCER_CONTRACT.evidence.topology);
  const restore = readBoundEvidence(atlasRoot, PRODUCER_CONTRACT.evidence.restoreProof);
  const expected = current.live_high_water;
  const stableAuth = { legacy: { auth_users: 20, auth_identities: 20 }, master: { auth_users: 114, auth_identities: 114 } };
  for (const side of ['legacy', 'master']) for (const [name, count] of Object.entries(stableAuth[side])) {
    if (expected?.[side]?.[name] !== count) throw new Error(`SEALED_AUTH_DENOMINATOR_DRIFT:${side}:${name}`);
  }
  if (restore.legacy?.auth_users !== 18 || restore.master?.auth_users !== 114 || restore.cleanup?.legacy_plaintext_present !== false || restore.cleanup?.master_plaintext_present !== false) throw new Error('RESTORE_PROOF_DRIFT');
  const aggregate = topology.aggregate_topology;
  if (aggregate?.legacy_users !== 20 || aggregate?.master_users !== 114 || aggregate?.shared_normalized_emails !== 16
    || aggregate?.retained_same_uuid !== 2 || aggregate?.bind_existing_different_uuid !== 14 || aggregate?.imports !== 4
    || aggregate?.final_edges !== 20 || aggregate?.expected_target_users !== 118
    || aggregate?.provider_id_conflicts !== 0 || aggregate?.identity_owner_conflicts !== 0
    || aggregate?.identity_subject_conflicts !== 0 || aggregate?.identity_email_conflicts !== 0) throw new Error('TOPOLOGY_EVIDENCE_DRIFT');
  return { current, topology, restore };
}

const MIGRATION_FUNCTIONS = Object.freeze(['mazer_is_username_available','mazer_initialize_progression','mazer_complete_level','mazer_complete_ai_level','mazer_reset_progression','mazer_leaderboard_page','mazer_leaderboard_self_rank','mazer_before_user_created','mazer_claim_signup_username','mazer_generated_username','mazer_enforce_username_origin']);
const MIGRATION_INDEXES = Object.freeze(['mazer_profiles_username_unique_idx','mazer_cycle_receipts_user_client_run_id_unique_idx','mazer_progression_states_leaderboard_order_idx']);
const AUTH_USER_WRITABLE_COLUMNS = Object.freeze([
  'instance_id','id','aud','role','email','encrypted_password','email_confirmed_at','invited_at',
  'confirmation_token','confirmation_sent_at','recovery_token','recovery_sent_at','email_change_token_new',
  'email_change','email_change_sent_at','last_sign_in_at','raw_app_meta_data','raw_user_meta_data',
  'is_super_admin','created_at','updated_at','phone','phone_confirmed_at','phone_change','phone_change_token',
  'phone_change_sent_at','email_change_token_current','email_change_confirm_status','banned_until',
  'reauthentication_token','reauthentication_sent_at','is_sso_user','deleted_at','is_anonymous'
]);
const AUTH_USER_COLUMNS = Object.freeze([...AUTH_USER_WRITABLE_COLUMNS, 'confirmed_at']);
const AUTH_IDENTITY_WRITABLE_COLUMNS = Object.freeze(['id','user_id','provider_id','identity_data','provider','last_sign_in_at','created_at','updated_at']);
const AUTH_IDENTITY_COLUMNS = Object.freeze([...AUTH_IDENTITY_WRITABLE_COLUMNS, 'email']);
const sqlIdentifier = (value) => `"${String(value).replaceAll('"', '""')}"`;

export const SNAPSHOT_SQL = (schema) => String.raw`begin transaction isolation level serializable read only;
select jsonb_build_object(
  'observed_at', clock_timestamp(),
  'auth_users', coalesce((select jsonb_agg(to_jsonb(u) order by lower(u.email),u.id) from auth.users u),'[]'::jsonb),
  'auth_identities', coalesce((select jsonb_agg(to_jsonb(i) order by i.user_id,i.provider,i.id) from auth.identities i),'[]'::jsonb),
  'profiles', coalesce((select jsonb_agg(to_jsonb(t) order by t.user_id) from ${schema}.mazer_profiles t),'[]'::jsonb),
  'player', coalesce((select jsonb_agg(to_jsonb(t) order by t.user_id) from ${schema}.mazer_progression_states t),'[]'::jsonb),
  'ai', coalesce((select jsonb_agg(to_jsonb(t) order by t.user_id,t.runner_key) from ${schema}.mazer_ai_progression_states t),'[]'::jsonb),
  'receipts', coalesce((select jsonb_agg(to_jsonb(t) order by t.id) from ${schema}.mazer_cycle_receipts t),'[]'::jsonb),
  'catalog', jsonb_build_object(
    'columns',coalesce((select jsonb_agg(jsonb_build_object('table',c.table_name,'column',c.column_name,'ordinal',c.ordinal_position,'data_type',c.data_type,'udt_name',c.udt_name,'nullable',c.is_nullable,'default',c.column_default) order by c.table_name,c.ordinal_position) from information_schema.columns c where c.table_schema=${sqlLiteral(schema)} and c.table_name in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')),'[]'::jsonb),
    'constraints',coalesce((select jsonb_agg(jsonb_build_object('table',cl.relname,'name',co.conname,'type',co.contype,'definition',pg_get_constraintdef(co.oid,true)) order by cl.relname,co.conname) from pg_constraint co join pg_class cl on cl.oid=co.conrelid join pg_namespace n on n.oid=cl.relnamespace where n.nspname=${sqlLiteral(schema)} and cl.relname in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')),'[]'::jsonb),
    'indexes',coalesce((select jsonb_agg(jsonb_build_object('name',i.indexname,'definition',i.indexdef) order by i.indexname) from pg_indexes i where i.schemaname=${sqlLiteral(schema)}),'[]'::jsonb),
    'functions',coalesce((select jsonb_agg(jsonb_build_object('name',p.proname,'identity_args',pg_get_function_identity_arguments(p.oid),'result',pg_get_function_result(p.oid),'owner',pg_get_userbyid(p.proowner),'security_definer',p.prosecdef,'volatility',p.provolatile,'acl',coalesce(p.proacl::text,'NULL'),'definition',pg_get_functiondef(p.oid)) order by p.proname,pg_get_function_identity_arguments(p.oid)) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname=${sqlLiteral(schema)} and p.proname=any(array[${MIGRATION_FUNCTIONS.map(sqlLiteral).join(',')}])),'[]'::jsonb),
    'policies',coalesce((select jsonb_agg(to_jsonb(p) order by p.tablename,p.policyname) from pg_policies p where p.schemaname=${sqlLiteral(schema)}),'[]'::jsonb),
    'triggers',coalesce((select jsonb_agg(jsonb_build_object('table_schema',event_object_schema,'table',event_object_table,'name',trigger_name,'timing',action_timing,'event',event_manipulation,'statement',action_statement) order by event_object_schema,event_object_table,trigger_name,event_manipulation) from information_schema.triggers where (event_object_schema=${sqlLiteral(schema)} or event_object_schema='auth') and trigger_name in ('mazer_claim_signup_username_after_insert','mazer_enforce_username_origin_before_update')),'[]'::jsonb),
    'username_secret_named_count',case when to_regclass('vault.secrets') is null then null else (select count(*) from vault.secrets where name='mazer_username_handle_key') end,
    'schema_acl',coalesce((select jsonb_agg(jsonb_build_object('grantee',case when x.grantee=0 then 'public' else pg_get_userbyid(x.grantee) end,'privilege',x.privilege_type,'grantable',x.is_grantable) order by case when x.grantee=0 then 'public' else pg_get_userbyid(x.grantee) end,x.privilege_type) from pg_namespace n cross join lateral aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x where n.nspname=${sqlLiteral(schema)}),'[]'::jsonb),
    'rls',coalesce((select jsonb_agg(jsonb_build_object('table',c.relname,'enabled',c.relrowsecurity,'forced',c.relforcerowsecurity) order by c.relname) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname=${sqlLiteral(schema)} and c.relname in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')),'[]'::jsonb)
  )
)::text;
commit;`;

export function normalizePsqlCommandSql(sql) {
  if (typeof sql !== 'string' || !sql.trim()) throw new Error('PSQL_COMMAND_SQL_SHAPE');
  return sql.replace(/^\\set ON_ERROR_STOP on\r?\n/, '');
}

function runPsql(psql, databaseUrl, sql, code) {
  const commandSql = normalizePsqlCommandSql(sql);
  const child = spawnSync(psql, ['--no-psqlrc', '--quiet', '--tuples-only', '--no-align', '--set', 'ON_ERROR_STOP=1', '--command', commandSql], {
    encoding: 'utf8', windowsHide: true, timeout: 300_000, maxBuffer: 64_000_000,
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
    if (!plain(row.state)) throw new Error('PLAYER_STATE_MALFORMED');
    const tracks = plain(row.state.tracks) ? structuredClone(row.state.tracks) : {};
    tracks.player = { ...(plain(tracks.player) ? structuredClone(tracks.player) : {}), level: row.player_level, completedCycles: row.player_completed_cycles };
    row.state = { ...structuredClone(row.state), tracks };
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
    const owned = identities.get(owner) ?? [];
    owned.push(identity);
    identities.set(owner, owned);
  }
  const result = new Map();
  for (const user of raw.auth_users) {
    const email = lowerEmail(user.email);
    if (!email || result.has(email)) throw new Error('NORMALIZED_EMAIL_DUPLICATE');
    const id = uuid(user.id, 'AUTH_USER_UUID');
    const owned = identities.get(id) ?? [];
    if (owned.length === 0) throw new Error('EMAIL_IDENTITY_MISSING');
    if (owned.length !== 1) throw new Error('EMAIL_IDENTITY_MULTIPLE');
    const identity = owned[0];
    if (identity.provider !== 'email') throw new Error('EMAIL_IDENTITY_PROVIDER_DRIFT');
    if (uuid(identity.provider_id, 'EMAIL_IDENTITY_PROVIDER_ID_MALFORMED') !== id) throw new Error('EMAIL_IDENTITY_PROVIDER_ID_DRIFT');
    if (!plain(identity.identity_data)) throw new Error('EMAIL_IDENTITY_METADATA_MALFORMED');
    if (uuid(identity.identity_data.sub, 'EMAIL_IDENTITY_METADATA_SUB_MALFORMED') !== id) throw new Error('EMAIL_IDENTITY_METADATA_SUB_DRIFT');
    if (typeof identity.identity_data.email !== 'string' || lowerEmail(identity.identity_data.email) !== email) throw new Error('EMAIL_IDENTITY_METADATA_EMAIL_DRIFT');
    result.set(email, { user, identity, id });
  }
  if ([...identities.keys()].some((owner) => !raw.auth_users.some((user) => String(user.id).toLowerCase() === owner))) throw new Error('EMAIL_IDENTITY_ORPHAN');
  return result;
}

export function buildIdentityPlan(legacyRaw, masterRaw) {
  const legacy = byEmail(legacyRaw); const master = byEmail(masterRaw);
  if (legacyRaw.auth_users.length !== 20 || legacyRaw.auth_identities.length !== 20 || masterRaw.auth_users.length !== 114 || masterRaw.auth_identities.length !== 114) throw new Error('LIVE_AUTH_DENOMINATOR_DRIFT');
  const masterIds = new Set(masterRaw.auth_users.map((user) => uuid(user.id, 'MASTER_AUTH_USER_UUID')));
  const masterIdentityIds = new Set(masterRaw.auth_identities.map((identity) => String(identity.id).toLowerCase()));
  const masterProviderIds = new Set(masterRaw.auth_identities.filter((identity) => identity.provider === 'email').map((identity) => uuid(identity.provider_id, 'MASTER_EMAIL_IDENTITY_PROVIDER_ID_MALFORMED')));
  const retained_edges = []; const new_edges = []; const imports = [];
  for (const [email, left] of sort([...legacy.entries()], (entry) => entry[0])) {
    const right = master.get(email);
    if (right) {
      const same = left.id === right.id;
      if (uuid(right.identity.provider_id, 'MASTER_EMAIL_IDENTITY_PROVIDER_ID_MALFORMED') !== right.id || lowerEmail(right.user.email) !== email || uuid(right.identity.user_id, 'MASTER_IDENTITY_OWNER') !== right.id) throw new Error('EXISTING_AUTH_BINDING_DRIFT');
      const edge = { legacy_user_id: left.id, master_user_id: right.id, disposition: same ? 'RETAINED' : 'BIND_EXISTING', normalized_email: email, master_user: structuredClone(right.user), master_identity: structuredClone(right.identity), evidence_digest: digest({ normalized_email: email, legacy_user_id: left.id, master_user_id: right.id }) };
      (same ? retained_edges : new_edges).push(edge);
      continue;
    }
    if (!BCRYPT.test(String(left.user.encrypted_password ?? ''))) throw new Error('UNSUPPORTED_PASSWORD_VERIFIER');
    if (masterIds.has(left.id)) throw new Error('IMPORT_UUID_COLLISION');
    if (masterIdentityIds.has(String(left.identity.id).toLowerCase()) || masterProviderIds.has(left.id)) throw new Error('IMPORT_IDENTITY_COLLISION');
    const user = structuredClone(left.user);
    user.id = left.id;
    user.instance_id = masterRaw.auth_users[0]?.instance_id;
    user.raw_user_meta_data = { ...(plain(user.raw_user_meta_data) ? user.raw_user_meta_data : {}) };
    delete user.raw_user_meta_data.app_namespace;
    const identity = structuredClone(left.identity);
    identity.user_id = left.id;
    imports.push({ user, identities: [identity] });
    new_edges.push({ legacy_user_id: left.id, master_user_id: left.id, disposition: 'CREATE_AND_BIND', normalized_email: email, evidence_digest: digest({ normalized_email: email, legacy_user_id: left.id, master_user_id: left.id }) });
  }
  if (retained_edges.length !== 2 || new_edges.filter((edge) => edge.disposition === 'BIND_EXISTING').length !== 14 || imports.length !== 4) throw new Error('IDENTITY_DENOMINATOR_DRIFT');
  return { imports, new_edges, retained_edges };
}

function normalizeAclObservation(acl) {
  if (!plain(acl) || canonical(Object.keys(acl).sort()) !== canonical(['catalog','observed_at','rpc_acl','schema','table_acl'])) throw new Error('ACL_OBSERVATION_KEYS');
  const observedAt = Date.parse(acl.observed_at);
  if (!Number.isFinite(observedAt) || observedAt < Date.now() - 300_000 || observedAt > Date.now() + 30_000) throw new Error('ACL_OBSERVATION_TIMESTAMP_DRIFT');
  return { schema: acl.schema, table_acl: structuredClone(acl.table_acl), rpc_acl: structuredClone(acl.rpc_acl), catalog: structuredClone(acl.catalog) };
}

function fenceSide(preimage, schema, extra) {
  if (!plain(preimage) || canonical(Object.keys(preimage).sort()) !== canonical(['catalog','rpc_acl','schema','table_acl'])) throw new Error('ACL_PREIMAGE_KEYS');
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
  const legacyPreimage = normalizeAclObservation(legacyAcl); const masterPreimage = normalizeAclObservation(masterAcl);
  const identity_map = [...auth.retained_edges, ...auth.new_edges].map((edge) => ({ legacy_user_id: edge.legacy_user_id, master_user_id: edge.master_user_id, disposition: 'BOUND' }));
  const app_contract = { migration_blobs: Object.fromEntries(R017_CONTRACT.migrations.map((item) => [item.phase, item.blob])), difficulty_bounds: [8, 400], receipt_identity: ['id', 'mapped_user_id+client_run_id'] };
  const first = new Date(Date.parse(source.observed_at) + 1).toISOString();
  const second = new Date(Date.parse(source.observed_at) + 2).toISOString();
  const masterRpcCount = masterPreimage.catalog?.rpcs?.length;
  const plannedMasterAcl = masterRpcCount === FENCE_CONTRACT.mutatingRpcs.length ? masterPreimage : plannedMasterAclFromLive(masterPreimage);
  const input = {
    schema: FENCE_CONTRACT.inputSchema, direction: 'forward', packet_id: PRODUCER_CONTRACT.packet,
    bindings: { legacy: { project_ref: PRODUCER_CONTRACT.legacyProject, schema: 'public' }, master: { project_ref: PRODUCER_CONTRACT.masterProject, schema: 'mazer' } },
    identity_map, expected_identity_map_digest: sha256(sort(identity_map, (edge) => [edge.legacy_user_id, edge.master_user_id])), app_contract, expected_app_contract_digest: sha256(app_contract),
    fence: { legacy: fenceSide(legacyPreimage, 'public', { signup_disabled: true, fenced_at: new Date(Date.parse(source.observed_at) - 1).toISOString() }), master: fenceSide(plannedMasterAcl, 'mazer', { before_user_created_hook_enabled: false, acl_basis: masterRpcCount === FENCE_CONTRACT.mutatingRpcs.length ? 'FRESH_LIVE' : 'FRESH_LIVE_TABLES_PLUS_EXACT_M2_PLANNED_RPCS', fenced_at: new Date(Date.parse(target.observed_at) - 1).toISOString() }) },
    source_snapshot: source, target_snapshot: target, expected_source_high_water_digest: snapshotDigest(source),
    zero_delta_reads: [{ ...structuredClone(source), observed_at: first }, { ...structuredClone(source), observed_at: second }]
  };
  classifyCutover(input);
  return input;
}

function deterministicQa(auth) {
  const seed = digest(auth.new_edges);
  const uuidFrom = (index) => `${seed.slice(index, index + 8)}-${seed.slice(index + 8, index + 12)}-4${seed.slice(index + 13, index + 16)}-8${seed.slice(index + 17, index + 20)}-${seed.slice(index + 20, index + 32)}`;
  return Array.from({ length: 4 }, (_, index) => ({ id: uuidFrom(index * 3), email: `mazer-r017-qa-${index + 1}@example.invalid`, username: index === 0 ? null : `r017qa${index + 1}`, mode: index === 0 ? 'generated' : 'claimed' }));
}

function validateCatalogPreimage(catalog) {
  for (const key of ['columns','constraints','indexes','functions','policies','triggers','schema_acl','rls']) if (!Array.isArray(catalog?.[key])) throw new Error('CATALOG_PREIMAGE_SHAPE');
  const addedColumns = new Set(['mazer_profiles:revision','mazer_profiles:username','mazer_profiles:username_origin','mazer_progression_states:revision','mazer_progression_states:level_reached_at','mazer_cycle_receipts:ruleset_id','mazer_cycle_receipts:recipe_version','mazer_cycle_receipts:recipe_hash','mazer_cycle_receipts:client_run_id']);
  if (catalog.username_secret_named_count !== 0) throw new Error('USERNAME_SECRET_PREIMAGE_DRIFT');
  if (catalog.columns.some((item) => addedColumns.has(`${item.table}:${item.column}`))) throw new Error('CATALOG_PREIMAGE_ALREADY_MIGRATED');
  if (catalog.indexes.some((item) => MIGRATION_INDEXES.includes(item.name)) || catalog.functions.some((item) => MIGRATION_FUNCTIONS.includes(item.name)) || catalog.triggers.some((item) => ['mazer_claim_signup_username_after_insert','mazer_enforce_username_origin_before_update'].includes(item.name)) || catalog.policies.some((item) => item.policyname === 'Mazer Auth hook can inspect usernames')) throw new Error('CATALOG_PREIMAGE_ALREADY_MIGRATED');
  const requiredConstraints = ['mazer_progression_states_player_level_check','mazer_progression_states_player_target_complexity_check','mazer_ai_progression_states_level_check','mazer_ai_progression_states_target_complexity_check'];
  for (const name of requiredConstraints) if (!catalog.constraints.some((item) => item.name === name && typeof item.definition === 'string')) throw new Error(`CATALOG_PREIMAGE_CONSTRAINT_MISSING:${name}`);
  if (catalog.rls.length !== 4 || catalog.rls.some((item) => item.enabled !== true || item.forced !== true)) throw new Error('CATALOG_PREIMAGE_RLS_DRIFT');
  return catalog;
}

function sqlProgram(body, labels = []) { return `\\set ON_ERROR_STOP on\nbegin;\n${labels.map((label) => `-- ${label}`).join('\n')}\n${body.trim()}\ncommit;`; }

function reverseCatalogSql(catalog) {
  validateCatalogPreimage(catalog);
  const constraintNames = new Set(['mazer_progression_states_player_level_check','mazer_progression_states_player_target_complexity_check','mazer_ai_progression_states_level_check','mazer_ai_progression_states_target_complexity_check']);
  const constraints = catalog.constraints.filter((item) => constraintNames.has(item.name));
  for (const item of constraints) if (!/^[A-Za-z0-9_]+$/.test(item.table) || !/^[A-Za-z0-9_]+$/.test(item.name) || !/^CHECK \(/.test(item.definition)) throw new Error('CATALOG_CONSTRAINT_UNSAFE');
  const priorClientRunIndex = catalog.indexes.find((item) => item.name === 'mazer_cycle_receipts_client_run_id_unique_idx');
  if (priorClientRunIndex && !/^CREATE UNIQUE INDEX mazer_cycle_receipts_client_run_id_unique_idx ON mazer\.mazer_cycle_receipts USING btree /.test(priorClientRunIndex.definition)) throw new Error('CATALOG_INDEX_UNSAFE');
  const schemaRoles = ['anon','authenticated','service_role','supabase_auth_admin'];
  const schemaGrants = catalog.schema_acl.filter((item) => schemaRoles.includes(item.grantee) && item.privilege === 'USAGE').map((item) => `grant usage on schema mazer to ${item.grantee}${item.grantable ? ' with grant option' : ''};`);
  const rls = catalog.rls.map((item) => `alter table mazer.${item.table} ${item.enabled ? 'enable' : 'disable'} row level security;\nalter table mazer.${item.table} ${item.forced ? 'force' : 'no force'} row level security;`).join('\n');
  return `
drop trigger if exists mazer_claim_signup_username_after_insert on auth.users;
drop trigger if exists mazer_enforce_username_origin_before_update on mazer.mazer_profiles;
drop policy if exists "Mazer Auth hook can inspect usernames" on mazer.mazer_profiles;
drop function if exists mazer.mazer_before_user_created(jsonb);
drop function if exists mazer.mazer_claim_signup_username();
drop function if exists mazer.mazer_enforce_username_origin();
drop function if exists mazer.mazer_generated_username(uuid,integer);
drop function if exists mazer.mazer_leaderboard_self_rank();
drop function if exists mazer.mazer_leaderboard_page(integer,integer);
drop function if exists mazer.mazer_reset_progression(bigint,uuid);
drop function if exists mazer.mazer_complete_ai_level(uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb);
drop function if exists mazer.mazer_complete_level(bigint,uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb);
drop function if exists mazer.mazer_initialize_progression(uuid);
drop function if exists mazer.mazer_is_username_available(text);
drop index if exists mazer.mazer_progression_states_leaderboard_order_idx;
drop index if exists mazer.mazer_profiles_username_unique_idx;
drop index if exists mazer.mazer_cycle_receipts_user_client_run_id_unique_idx;
alter table mazer.mazer_progression_states drop constraint if exists mazer_progression_states_player_level_check;
alter table mazer.mazer_progression_states drop constraint if exists mazer_progression_states_player_target_complexity_check;
alter table mazer.mazer_ai_progression_states drop constraint if exists mazer_ai_progression_states_level_check;
alter table mazer.mazer_ai_progression_states drop constraint if exists mazer_ai_progression_states_target_complexity_check;
alter table mazer.mazer_progression_states alter column player_level type integer using player_level::integer,alter column player_completed_cycles type integer using player_completed_cycles::integer;
alter table mazer.mazer_ai_progression_states alter column level type integer using level::integer,alter column completed_cycles type integer using completed_cycles::integer;
${constraints.map((item) => `alter table mazer.${item.table} add constraint ${item.name} ${item.definition};`).join('\n')}
alter table mazer.mazer_profiles drop constraint if exists mazer_profiles_username_origin_check;
alter table mazer.mazer_profiles drop column if exists username_origin,drop column if exists username,drop column if exists revision;
alter table mazer.mazer_progression_states drop column if exists level_reached_at,drop column if exists revision;
alter table mazer.mazer_cycle_receipts drop column if exists client_run_id,drop column if exists recipe_hash,drop column if exists recipe_version,drop column if exists ruleset_id;
${priorClientRunIndex ? `${priorClientRunIndex.definition};` : ''}
revoke usage on schema mazer from anon,authenticated,service_role,supabase_auth_admin;
${schemaGrants.join('\n')}
${rls}
delete from vault.secrets where name='mazer_username_handle_key';`;
}

function catalogEqualityAssertions(catalog) {
  return `
if (select coalesce(jsonb_agg(jsonb_build_object('table',c.table_name,'column',c.column_name,'ordinal',c.ordinal_position,'data_type',c.data_type,'udt_name',c.udt_name,'nullable',c.is_nullable,'default',c.column_default) order by c.table_name,c.ordinal_position),'[]'::jsonb) from information_schema.columns c where c.table_schema='mazer' and c.table_name in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')) <> ${jsonLiteral(catalog.columns)} then raise exception 'R017_ROLLBACK_COLUMNS_DRIFT'; end if;
if (select coalesce(jsonb_agg(jsonb_build_object('table',cl.relname,'name',co.conname,'type',co.contype,'definition',pg_get_constraintdef(co.oid,true)) order by cl.relname,co.conname),'[]'::jsonb) from pg_constraint co join pg_class cl on cl.oid=co.conrelid join pg_namespace n on n.oid=cl.relnamespace where n.nspname='mazer' and cl.relname in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')) <> ${jsonLiteral(catalog.constraints)} then raise exception 'R017_ROLLBACK_CONSTRAINTS_DRIFT'; end if;
if (select coalesce(jsonb_agg(jsonb_build_object('name',i.indexname,'definition',i.indexdef) order by i.indexname),'[]'::jsonb) from pg_indexes i where i.schemaname='mazer') <> ${jsonLiteral(catalog.indexes)} then raise exception 'R017_ROLLBACK_INDEXES_DRIFT'; end if;
if (select coalesce(jsonb_agg(jsonb_build_object('name',p.proname,'identity_args',pg_get_function_identity_arguments(p.oid),'result',pg_get_function_result(p.oid),'owner',pg_get_userbyid(p.proowner),'security_definer',p.prosecdef,'volatility',p.provolatile,'acl',coalesce(p.proacl::text,'NULL'),'definition',pg_get_functiondef(p.oid)) order by p.proname,pg_get_function_identity_arguments(p.oid)),'[]'::jsonb) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='mazer' and p.proname=any(array[${MIGRATION_FUNCTIONS.map(sqlLiteral).join(',')}])) <> ${jsonLiteral(catalog.functions)} then raise exception 'R017_ROLLBACK_FUNCTIONS_DRIFT'; end if;
if (select coalesce(jsonb_agg(to_jsonb(p) order by p.tablename,p.policyname),'[]'::jsonb) from pg_policies p where p.schemaname='mazer') <> ${jsonLiteral(catalog.policies)} then raise exception 'R017_ROLLBACK_POLICIES_DRIFT'; end if;
if (select coalesce(jsonb_agg(jsonb_build_object('table_schema',event_object_schema,'table',event_object_table,'name',trigger_name,'timing',action_timing,'event',event_manipulation,'statement',action_statement) order by event_object_schema,event_object_table,trigger_name,event_manipulation),'[]'::jsonb) from information_schema.triggers where (event_object_schema='mazer' or event_object_schema='auth') and trigger_name in ('mazer_claim_signup_username_after_insert','mazer_enforce_username_origin_before_update')) <> ${jsonLiteral(catalog.triggers)} then raise exception 'R017_ROLLBACK_TRIGGERS_DRIFT'; end if;
if (select count(*) from vault.secrets where name='mazer_username_handle_key') <> ${Number(0)} then raise exception 'R017_ROLLBACK_USERNAME_SECRET_DRIFT'; end if;
if (select coalesce(jsonb_agg(jsonb_build_object('grantee',case when x.grantee=0 then 'public' else pg_get_userbyid(x.grantee) end,'privilege',x.privilege_type,'grantable',x.is_grantable) order by case when x.grantee=0 then 'public' else pg_get_userbyid(x.grantee) end,x.privilege_type),'[]'::jsonb) from pg_namespace n cross join lateral aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x where n.nspname='mazer') <> ${jsonLiteral(catalog.schema_acl)} then raise exception 'R017_ROLLBACK_SCHEMA_ACL_DRIFT'; end if;
if (select coalesce(jsonb_agg(jsonb_build_object('table',c.relname,'enabled',c.relrowsecurity,'forced',c.relforcerowsecurity) order by c.relname),'[]'::jsonb) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='mazer' and c.relname in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')) <> ${jsonLiteral(catalog.rls)} then raise exception 'R017_ROLLBACK_RLS_DRIFT'; end if;`;
}

export function renderOperationalSql({ auth, fenceInput, actionFenceInput = fenceInput, catalogPreimage, reset, qa, quarantineKey, qaPassword }) {
  validateCatalogPreimage(catalogPreimage);
  const classified = classifyCutover(fenceInput);
  const actionClassified = classifyCutover(actionFenceInput);
  const imports = auth.imports;
  const edges = [...auth.retained_edges, ...auth.new_edges];
  const existingBindings = edges.filter((edge) => edge.disposition !== 'CREATE_AND_BIND').map((edge) => ({ normalized_email: edge.normalized_email, user: edge.master_user, identity: edge.master_identity }));
  const importUsers = imports.map((item) => item.user); const importIdentities = imports.flatMap((item) => item.identities);
  const expectedAuthUserKeys = canonical([...AUTH_USER_COLUMNS].sort());
  const expectedAuthIdentityKeys = canonical([...AUTH_IDENTITY_COLUMNS].sort());
  if ([...importUsers, ...existingBindings.map((item) => item.user)].some((item) => canonical(Object.keys(item).sort()) !== expectedAuthUserKeys)) throw new Error('AUTH_USER_COLUMN_SHAPE_DRIFT');
  if ([...importIdentities, ...existingBindings.map((item) => item.identity)].some((item) => canonical(Object.keys(item).sort()) !== expectedAuthIdentityKeys)) throw new Error('AUTH_IDENTITY_COLUMN_SHAPE_DRIFT');
  const authUserInsertColumns = AUTH_USER_WRITABLE_COLUMNS.map(sqlIdentifier).join(',');
  const authUserInsertProjection = AUTH_USER_WRITABLE_COLUMNS.map((name) => `(r).${sqlIdentifier(name)}`).join(',');
  const typedAuthRowsSql = (relation, rows) => `(select coalesce(jsonb_agg(to_jsonb(x.r) order by (x.r).id),'[]'::jsonb) from (select jsonb_populate_record(null::${relation},value) r from jsonb_array_elements(${jsonLiteral(sort(rows, (item) => item.id))}) value) x)`;
  const expectedAuthUsersSql = typedAuthRowsSql('auth.users', importUsers);
  const expectedAuthIdentitiesSql = typedAuthRowsSql('auth.identities', importIdentities);
  const expectedMap = sort(edges.map((edge) => ({ legacy_user_id: edge.legacy_user_id, master_user_id: edge.master_user_id, evidence_digest: edge.evidence_digest })), (edge) => edge.legacy_user_id);
  const qaRows = qa.rows;
  const usernameHandleKey = crypto.createHmac('sha256', Buffer.from(quarantineKey, 'utf8')).update('atlas:mazer:r017:username-handle:v1').digest('hex');
  const desiredRows = actionClassified.privatePlan.desired;
  const expectedProfileCoreSql = `(select coalesce(jsonb_agg(to_jsonb(x.r)-'username'-'username_origin' order by (x.r).user_id),'[]'::jsonb) from (select jsonb_populate_record(null::mazer.mazer_profiles,value) r from jsonb_array_elements(${jsonLiteral(sort(desiredRows.profiles, (row) => row.user_id))}) value) x)`;
  const expectedPlayerRowsSql = `(select coalesce(jsonb_agg(to_jsonb(x.r) order by (x.r).user_id),'[]'::jsonb) from (select jsonb_populate_record(null::mazer.mazer_progression_states,value) r from jsonb_array_elements(${jsonLiteral(sort(desiredRows.player, (row) => row.user_id))}) value) x)`;
  const expectedAiRowsSql = `(select coalesce(jsonb_agg(to_jsonb(x.r) order by (x.r).user_id,(x.r).runner_key),'[]'::jsonb) from (select jsonb_populate_record(null::mazer.mazer_ai_progression_states,value) r from jsonb_array_elements(${jsonLiteral(sort(desiredRows.ai, (row) => [row.user_id,row.runner_key]))}) value) x)`;
  const expectedReceiptRowsSql = typedAuthRowsSql('mazer.mazer_cycle_receipts', sort(desiredRows.receipts, (row) => row.id));
  const explicitProfiles = sort(desiredRows.profiles.filter((row) => row.username != null && String(row.username).trim() !== '').map((row) => ({ user_id: row.user_id, username: row.username })), (row) => row.user_id);
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
  if to_regclass('vault.decrypted_secrets') is null or (select count(*) from vault.secrets where name='mazer_username_handle_key') <> 0 then raise exception 'R017_MAZER_USERNAME_HANDLE_KEY_PREIMAGE_DRIFT'; end if;
  if not exists (select 1 from pg_namespace where nspname='mazer') then raise exception 'R017_DATA_API_SCHEMA_DRIFT'; end if;
end $r017$;`, ['data_api','rls','acl','auth.users','114','13','16','1887']);
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
do $r017_auth_precheck$ begin
 if (select count(*) from auth.users u join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on u.id=(e->'user'->>'id')::uuid) <> ${existingBindings.length} then raise exception 'R017_BOUND_AUTH_USER_CARDINALITY_DRIFT'; end if;
 if exists(select 1 from auth.users u join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on u.id=(e->'user'->>'id')::uuid where u.email is null or lower(u.email)<>e->>'normalized_email') then raise exception 'R017_BOUND_AUTH_USER_EMAIL_DRIFT'; end if;
 if (select count(*) from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid) <> ${existingBindings.length} then raise exception 'R017_BOUND_AUTH_IDENTITY_CARDINALITY_DRIFT'; end if;
 if (select count(*) from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.user_id=(e->'user'->>'id')::uuid where i.provider='email') <> ${existingBindings.length} then raise exception 'R017_BOUND_AUTH_EMAIL_IDENTITY_MULTIPLE'; end if;
 if exists(select 1 from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid where i.user_id<>(e->'user'->>'id')::uuid) then raise exception 'R017_BOUND_AUTH_IDENTITY_OWNER_DRIFT'; end if;
 if exists(select 1 from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid where i.provider<>'email') then raise exception 'R017_BOUND_AUTH_IDENTITY_PROVIDER_DRIFT'; end if;
 if exists(select 1 from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid where not (i.provider_id=e->'user'->>'id')) then raise exception 'R017_BOUND_AUTH_IDENTITY_PROVIDER_ID_DRIFT'; end if;
 if exists(select 1 from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid where jsonb_typeof(i.identity_data) is distinct from 'object' or i.identity_data->>'sub' is distinct from e->'user'->>'id') then raise exception 'R017_BOUND_AUTH_IDENTITY_SUBJECT_DRIFT'; end if;
 if exists(select 1 from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid where lower(i.email) is distinct from e->>'normalized_email' or lower(i.identity_data->>'email') is distinct from e->>'normalized_email') then raise exception 'R017_BOUND_AUTH_IDENTITY_EMAIL_DRIFT'; end if;
 if exists(select 1 from auth.users u join jsonb_array_elements(${jsonLiteral(importUsers)}) e on u.id=(e->>'id')::uuid or lower(u.email)=lower(e->>'email')) then raise exception 'R017_IMPORT_USER_COLLISION'; end if;
 if exists(select 1 from auth.identities i join jsonb_array_elements(${jsonLiteral(importIdentities)}) e on i.id=(e->>'id')::uuid or (i.provider=e->>'provider' and lower(i.provider_id)=lower(e->>'provider_id'))) then raise exception 'R017_IMPORT_IDENTITY_COLLISION'; end if;
end $r017_auth_precheck$;
create table atlas_mazer_r017.auth_preimage(kind text not null check(kind in ('user','identity')),key text not null,row jsonb not null,primary key(kind,key));
revoke all on atlas_mazer_r017.auth_preimage from anon,authenticated,public;
insert into atlas_mazer_r017.auth_preimage(kind,key,row) select 'user',u.id::text,to_jsonb(u) from auth.users u join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on u.id=(e->'user'->>'id')::uuid;
insert into atlas_mazer_r017.auth_preimage(kind,key,row) select 'identity',i.id::text,to_jsonb(i) from auth.identities i join jsonb_array_elements(${jsonLiteral(existingBindings)}) e on i.id=(e->'identity'->>'id')::uuid;
do $r017_auth_preimage$ begin
 if (select count(*) from atlas_mazer_r017.auth_preimage where kind='user') <> ${existingBindings.length} or (select count(*) from atlas_mazer_r017.auth_preimage where kind='identity') <> ${existingBindings.length} then raise exception 'R017_AUTH_PREIMAGE_CARDINALITY_DRIFT'; end if;
end $r017_auth_preimage$;
 with rows as (select jsonb_array_elements(${jsonLiteral(importUsers)}) value), records as (select jsonb_populate_record(null::auth.users,value) r from rows)
 insert into auth.users(${authUserInsertColumns})
 select ${authUserInsertProjection} from records;
with rows as (select jsonb_array_elements(${jsonLiteral(importIdentities)}) value), records as (select jsonb_populate_record(null::auth.identities,value) r from rows)
insert into auth.identities(id,user_id,provider_id,identity_data,provider,last_sign_in_at,created_at,updated_at)
select (r).id,(r).user_id,(r).provider_id,(r).identity_data,(r).provider,(r).last_sign_in_at,(r).created_at,(r).updated_at from records;
insert into mazer.mazer_identity_map(legacy_user_id,master_user_id,evidence_digest) select legacy_user_id,master_user_id,evidence_digest from jsonb_to_recordset(${jsonLiteral(edges)}) as x(legacy_user_id uuid,master_user_id uuid,evidence_digest text,disposition text) on conflict(legacy_user_id) do update set master_user_id=excluded.master_user_id,evidence_digest=excluded.evidence_digest where mazer.mazer_identity_map.master_user_id=excluded.master_user_id;
do $r017_auth_postcheck$ begin
 if (select coalesce(jsonb_agg(to_jsonb(u) order by u.id),'[]'::jsonb) from auth.users u where u.id in (select (e->>'id')::uuid from jsonb_array_elements(${jsonLiteral(importUsers)}) e)) <> ${expectedAuthUsersSql} then raise exception 'R017_IMPORTED_AUTH_USERS_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(to_jsonb(i) order by i.id),'[]'::jsonb) from auth.identities i where i.id in (select (e->>'id')::uuid from jsonb_array_elements(${jsonLiteral(importIdentities)}) e)) <> ${expectedAuthIdentitiesSql} then raise exception 'R017_IMPORTED_AUTH_IDENTITIES_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(jsonb_build_object('legacy_user_id',legacy_user_id,'master_user_id',master_user_id,'evidence_digest',evidence_digest) order by legacy_user_id),'[]'::jsonb) from mazer.mazer_identity_map) <> ${jsonLiteral(expectedMap)} then raise exception 'R017_IDENTITY_MAP_DIGEST_DRIFT'; end if;
 if exists(select 1 from atlas_mazer_r017.auth_preimage p left join auth.users u on p.kind='user' and u.id=p.key::uuid where p.kind='user' and to_jsonb(u) is distinct from p.row) then raise exception 'R017_BOUND_AUTH_USER_MUTATION_DRIFT'; end if;
 if exists(select 1 from atlas_mazer_r017.auth_preimage p left join auth.identities i on p.kind='identity' and i.id=p.key::uuid where p.kind='identity' and to_jsonb(i) is distinct from p.row) then raise exception 'R017_BOUND_AUTH_IDENTITY_MUTATION_DRIFT'; end if;
end $r017_auth_postcheck$;`, ['auth.users','auth.identities','create_and_bind','bind_existing','4_auth_imports','14_existing_binds']);
  sql['reset-era-apply.sql'] = sqlProgram(`
create extension if not exists pgcrypto with schema extensions;
create table if not exists atlas_mazer_r017.reset_quarantine(id text primary key,ciphertext bytea not null);
insert into atlas_mazer_r017.reset_quarantine(id,ciphertext) values('reset-era-ai',extensions.pgp_sym_encrypt(${sqlLiteral(canonical(reset.quarantined_row))},${sqlLiteral(quarantineKey)},'cipher-algo=aes256')) on conflict do nothing;
do $username_key$ begin
 if exists(select 1 from vault.secrets where name='mazer_username_handle_key') then raise exception 'R017_MAZER_USERNAME_HANDLE_KEY_PREEXISTS'; end if;
 perform vault.create_secret(${sqlLiteral(usernameHandleKey)},'mazer_username_handle_key','R017 protected deterministic Mazer username key',null);
 if (select count(*) from vault.secrets where name='mazer_username_handle_key') <> 1 then raise exception 'R017_MAZER_USERNAME_HANDLE_KEY_CREATE_FAILED'; end if;
end $username_key$;`, ['whole_row_override',`canonical_projection:${reset.canonical_projection}`,'39/108/161/S','pgp_sym_encrypt','player_reset_disposition','vault.create_secret','rollback_bound_username_key']);
  sql['postverify.sql'] = sqlProgram(`
do $r017$ begin
 if (select coalesce(jsonb_agg(to_jsonb(t)-'username'-'username_origin' order by t.user_id),'[]'::jsonb) from mazer.mazer_profiles t) <> ${expectedProfileCoreSql} then raise exception 'R017_PROFILES_CORE_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(jsonb_build_object('user_id',t.user_id,'username',t.username) order by t.user_id),'[]'::jsonb) from mazer.mazer_profiles t join jsonb_to_recordset(${jsonLiteral(explicitProfiles)}) x(user_id uuid,username text) on x.user_id=t.user_id where t.username=x.username and t.username_origin='claimed') <> ${jsonLiteral(explicitProfiles)} then raise exception 'R017_EXPLICIT_USERNAMES_CHANGED'; end if;
 if (select count(*) from mazer.mazer_profiles where username_origin='generated') <> ${desiredRows.profiles.length - explicitProfiles.length} then raise exception 'R017_GENERATED_USERNAME_DENOMINATOR_DRIFT'; end if;
 if exists(select 1 from mazer.mazer_profiles t where t.username_origin='generated' and (t.username !~ '^Mazer-[0-9]{6}$' or not exists(select 1 from generate_series(0,999999) attempt where mazer.mazer_generated_username(t.user_id,attempt)=t.username))) then raise exception 'R017_GENERATED_USERNAME_REGENERATION_DRIFT'; end if;
 if exists(select 1 from mazer.mazer_profiles group by lower(username) having count(*)<>1) then raise exception 'R017_USERNAME_CASEFOLD_COLLISION'; end if;
 if exists(select 1 from mazer.mazer_profiles where username_origin not in ('generated','claimed') or username is null) then raise exception 'R017_USERNAME_ORIGIN_DRIFT'; end if;
 if (select count(*) from vault.secrets where name='mazer_username_handle_key') <> 1 then raise exception 'R017_MAZER_USERNAME_HANDLE_KEY_DRIFT'; end if;
 if (select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from mazer.mazer_progression_states t) <> ${expectedPlayerRowsSql} then raise exception 'R017_PLAYER_FULL_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id,t.runner_key),'[]'::jsonb) from mazer.mazer_ai_progression_states t) <> ${expectedAiRowsSql} then raise exception 'R017_AI_FULL_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from mazer.mazer_cycle_receipts t) <> ${expectedReceiptRowsSql} then raise exception 'R017_RECEIPT_CONSERVATION_FULL_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(jsonb_build_object('legacy_user_id',legacy_user_id,'master_user_id',master_user_id,'evidence_digest',evidence_digest) order by legacy_user_id),'[]'::jsonb) from mazer.mazer_identity_map) <> ${jsonLiteral(expectedMap)} then raise exception 'R017_MAP_FULL_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(to_jsonb(u) order by u.id),'[]'::jsonb) from auth.users u where u.id in (select (e->>'id')::uuid from jsonb_array_elements(${jsonLiteral(importUsers)}) e)) <> ${expectedAuthUsersSql} then raise exception 'R017_AUTH_USERS_FULL_DIGEST_DRIFT'; end if;
 if (select coalesce(jsonb_agg(to_jsonb(i) order by i.id),'[]'::jsonb) from auth.identities i where i.id in (select (e->>'id')::uuid from jsonb_array_elements(${jsonLiteral(importIdentities)}) e)) <> ${expectedAuthIdentitiesSql} then raise exception 'R017_AUTH_IDENTITIES_FULL_DIGEST_DRIFT'; end if;
 if (select count(*) from atlas_mazer_r017.auth_preimage where kind='user') <> ${existingBindings.length} or (select count(*) from atlas_mazer_r017.auth_preimage where kind='identity') <> ${existingBindings.length} then raise exception 'R017_AUTH_PREIMAGE_CARDINALITY_DRIFT'; end if;
 if exists(select 1 from atlas_mazer_r017.auth_preimage p left join auth.users u on p.kind='user' and u.id=p.key::uuid where p.kind='user' and to_jsonb(u) is distinct from p.row) then raise exception 'R017_BOUND_AUTH_USER_MUTATION_DRIFT'; end if;
 if exists(select 1 from atlas_mazer_r017.auth_preimage p left join auth.identities i on p.kind='identity' and i.id=p.key::uuid where p.kind='identity' and to_jsonb(i) is distinct from p.row) then raise exception 'R017_BOUND_AUTH_IDENTITY_MUTATION_DRIFT'; end if;
 if (select jsonb_agg(jsonb_build_object('table',c.relname,'enabled',c.relrowsecurity,'forced',c.relforcerowsecurity) order by c.relname) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='mazer' and c.relname in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')) <> '[{"table":"mazer_ai_progression_states","enabled":true,"forced":true},{"table":"mazer_cycle_receipts","enabled":true,"forced":true},{"table":"mazer_profiles","enabled":true,"forced":true},{"table":"mazer_progression_states","enabled":true,"forced":true}]'::jsonb then raise exception 'R017_RLS_FULL_CATALOG_DRIFT'; end if;
 if not has_schema_privilege('anon','mazer','USAGE') or not has_schema_privilege('authenticated','mazer','USAGE') or not has_schema_privilege('service_role','mazer','USAGE') then raise exception 'R017_DATA_API_SCHEMA_ACL_DRIFT'; end if;
 if exists(select 1 from information_schema.role_table_grants where table_schema='mazer' and grantee in ('anon','authenticated','public') and privilege_type in ('INSERT','UPDATE','DELETE') and table_name in ('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')) then raise exception 'R017_TABLE_ACL_DRIFT'; end if;
 if (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='mazer' and p.proname=any(array[${MIGRATION_FUNCTIONS.map(sqlLiteral).join(',')}])) <> 11 then raise exception 'R017_FUNCTION_CATALOG_DRIFT'; end if;
 if (select count(*) from pg_indexes where schemaname='mazer' and indexname=any(array[${MIGRATION_INDEXES.map(sqlLiteral).join(',')}])) <> 3 then raise exception 'R017_INDEX_CATALOG_DRIFT'; end if;
 if not exists(select 1 from pg_policies where schemaname='mazer' and tablename='mazer_profiles' and policyname='Mazer Auth hook can inspect usernames' and cmd='SELECT' and roles='{supabase_auth_admin}') then raise exception 'R017_POLICY_CATALOG_DRIFT'; end if;
 if not exists(select 1 from information_schema.triggers where event_object_schema='auth' and event_object_table='users' and trigger_name='mazer_claim_signup_username_after_insert' and action_timing='AFTER' and event_manipulation='INSERT') or not exists(select 1 from information_schema.triggers where event_object_schema='mazer' and event_object_table='mazer_profiles' and trigger_name='mazer_enforce_username_origin_before_update' and action_timing='BEFORE' and event_manipulation='UPDATE') then raise exception 'R017_TRIGGER_CATALOG_DRIFT'; end if;
end $r017$;`, ['data_api','rls','acl','118','20','13','17','1887','receipt_conservation']);
  sql['qa-apply.sql'] = sqlProgram(`
with q as (select * from jsonb_to_recordset(${jsonLiteral(qaRows)}) as x(id uuid,email text,username text,mode text))
insert into auth.users(id,instance_id,aud,role,email,encrypted_password,email_confirmed_at,raw_app_meta_data,raw_user_meta_data,created_at,updated_at)
  select id,(select instance_id from auth.users limit 1),'authenticated','authenticated',email,extensions.crypt(${sqlLiteral(qaPassword)},extensions.gen_salt('bf')),clock_timestamp(),${jsonLiteral({ provider: 'email', providers: ['email'] })},case when mode='generated' then jsonb_build_object('app_namespace','mazer') else jsonb_build_object('app_namespace','mazer','username',username,'display_name',username) end,clock_timestamp(),clock_timestamp() from q;
insert into auth.identities(id,user_id,provider_id,identity_data,provider,created_at,updated_at,last_sign_in_at)
select gen_random_uuid(),id,id::text,jsonb_build_object('sub',id::text,'email',email),'email',clock_timestamp(),clock_timestamp(),clock_timestamp() from jsonb_to_recordset(${jsonLiteral(qaRows)}) as x(id uuid,email text,username text,mode text);
do $qa$ begin
 if (select count(*) from mazer.mazer_profiles p join jsonb_to_recordset(${jsonLiteral(qaRows)}) q(id uuid,email text,username text,mode text) on q.id=p.user_id where q.mode='generated' and p.username_origin='generated' and p.username ~ '^Mazer-[0-9]{6}$') <> 1 then raise exception 'R017_QA_GENERATED_USERNAME_DRIFT'; end if;
 if (select count(*) from mazer.mazer_profiles p join jsonb_to_recordset(${jsonLiteral(qaRows)}) q(id uuid,email text,username text,mode text) on q.id=p.user_id where q.mode='claimed' and p.username_origin='claimed' and p.username=q.username) <> 3 then raise exception 'R017_QA_CLAIMED_USERNAME_DRIFT'; end if;
end $qa$;`, ['qa_ttl','before_user_created','rollback_on_error']);
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
delete from auth.identities where user_id in (select id from jsonb_to_recordset(${jsonLiteral(imports.map((item) => item.user))}) as x(id uuid));
delete from auth.users where id in (select id from jsonb_to_recordset(${jsonLiteral(imports.map((item) => item.user))}) as x(id uuid));
drop table if exists mazer.mazer_identity_map;
${reverseCatalogSql(catalogPreimage)}
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.profiles)}) value) insert into mazer.mazer_profiles select (jsonb_populate_record(null::mazer.mazer_profiles,value)).* from rows;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.player)}) value) insert into mazer.mazer_progression_states select (jsonb_populate_record(null::mazer.mazer_progression_states,value)).* from rows;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.ai)}) value) insert into mazer.mazer_ai_progression_states select (jsonb_populate_record(null::mazer.mazer_ai_progression_states,value)).* from rows;
with rows as (select jsonb_array_elements(${jsonLiteral(targetRows.receipts)}) value) insert into mazer.mazer_cycle_receipts select (jsonb_populate_record(null::mazer.mazer_cycle_receipts,value)).* from rows;
${aclRestore}
do $r017$ begin
 if (select count(*) from mazer.mazer_profiles) <> 5 or (select count(*) from mazer.mazer_progression_states) <> 7 or (select count(*) from mazer.mazer_ai_progression_states) <> 7 or (select count(*) from mazer.mazer_cycle_receipts) <> 1290 then raise exception 'R017_MASTER_PREIMAGE_RESTORE_DRIFT'; end if;
 if (select count(*) from auth.users) <> 114 then raise exception 'R017_AUTH_PREIMAGE_RESTORE_DRIFT'; end if;
 ${catalogEqualityAssertions(catalogPreimage)}
end $r017$;
drop schema if exists atlas_mazer_r017 cascade;`, ['disable_hook_first','master_preimage','receipt_conservation']);
  for (const name of R017_CONTRACT.sqlNames) sql[name] = `${sql[name].trim()}\n`;
  return { sql, sql_sha256: Object.fromEntries(Object.entries(sql).map(([name, value]) => [name, sha256(Buffer.from(value, 'utf8'))])), classified };
}

export function producePrivateSource({ legacy, master, legacyAcl, masterAcl, quarantineKey, qaPassword, resetBinding = null }) {
  if (typeof quarantineKey !== 'string' || quarantineKey.length < 32 || typeof qaPassword !== 'string' || qaPassword.length < 16) throw new Error('PRIVATE_SECRET_INPUT_WEAK');
  const auth = buildIdentityPlan(legacy, master);
  const catalog_preimage = validateCatalogPreimage(master.catalog);
  const fence_input = buildFenceInput(legacy, master, legacyAcl, masterAcl, auth);
  const allEdges = [...auth.retained_edges, ...auth.new_edges];
  const receiptBoundEdges = allEdges.filter((item) => master.receipts.filter((row) => String(row.user_id).toLowerCase() === item.master_user_id).length === RECEIPT_CATCHUP_CONTRACT.resetMasterExact
    && legacy.receipts.filter((row) => String(row.user_id).toLowerCase() === item.legacy_user_id).length >= RECEIPT_CATCHUP_CONTRACT.resetLegacyBaseline);
  const boundLegacy = resetBinding == null ? null : uuid(resetBinding.legacy_user_id, 'RESET_BINDING_LEGACY_UUID');
  const boundMaster = resetBinding == null ? null : uuid(resetBinding.master_user_id, 'RESET_BINDING_MASTER_UUID');
  const candidates = resetBinding == null ? receiptBoundEdges : receiptBoundEdges.filter((item) => item.legacy_user_id === boundLegacy && item.master_user_id === boundMaster);
  if (candidates.length !== 1) throw new Error('RESET_IDENTITY_RECEIPT_BINDING_DRIFT');
  const [edge] = candidates;
  const resetMaster = master.ai.find((row) => String(row.user_id).toLowerCase() === edge.master_user_id && row.runner_key === 'menu-runner');
  if (!resetMaster || String(resetMaster.level) !== '39' || String(resetMaster.completed_cycles) !== '108' || Number(resetMaster.target_complexity) !== 161 || resetMaster.rank !== 'S') throw new Error('RESET_MASTER_ROW_DRIFT');
  const resetLegacy = edge && legacy.ai.find((row) => String(row.user_id).toLowerCase() === edge.legacy_user_id && row.runner_key === 'menu-runner');
  if (!edge || !resetLegacy) throw new Error('RESET_LEGACY_ROW_NOT_FOUND');
  const legacyTimestamp = Math.max(Date.parse(resetLegacy.updated_at ?? ''), Date.parse(resetLegacy.last_completed_cycle_at ?? ''));
  const masterTimestamp = Math.max(Date.parse(resetMaster.updated_at ?? ''), Date.parse(resetMaster.last_completed_cycle_at ?? ''));
  if (!Number.isFinite(legacyTimestamp) || !Number.isFinite(masterTimestamp) || legacyTimestamp <= masterTimestamp) throw new Error('RESET_TIMESTAMP_ORDER_DRIFT');
  const playerLegacy = fence_input.source_snapshot.player.find((row) => row.user_id === edge.legacy_user_id);
  const playerMaster = fence_input.target_snapshot.player.find((row) => row.user_id === edge.master_user_id);
  if (!playerLegacy || !playerMaster) throw new Error('RESET_PLAYER_ROW_NOT_FOUND');
  const mappedPlayerRow = { ...structuredClone(playerLegacy.row), user_id: edge.master_user_id };
  const reset_era_player = { disposition: 'MASTER_DOMINATES_NO_OVERRIDE', source_row_digest: digest(mappedPlayerRow), target_row_digest: playerMaster.payload_digest };
  const legacyReceiptCount = legacy.receipts.filter((row) => String(row.user_id).toLowerCase() === edge.legacy_user_id).length;
  const masterReceiptCount = master.receipts.filter((row) => String(row.user_id).toLowerCase() === edge.master_user_id).length;
  if (legacyReceiptCount < RECEIPT_CATCHUP_CONTRACT.resetLegacyBaseline
    || legacyReceiptCount > RECEIPT_CATCHUP_CONTRACT.resetLegacyBaseline + RECEIPT_CATCHUP_CONTRACT.maxDelta
    || legacyReceiptCount > legacy.receipts.length
    || masterReceiptCount !== RECEIPT_CATCHUP_CONTRACT.resetMasterExact) throw new Error('RESET_RECEIPT_DENOMINATOR_DRIFT');
  const sourceAiEnvelope = fence_input.source_snapshot.ai.find((row) => row.user_id === edge.legacy_user_id && row.runner_key === 'menu-runner');
  const targetAiEnvelope = fence_input.target_snapshot.ai.find((row) => row.user_id === edge.master_user_id && row.runner_key === 'menu-runner');
  if (!sourceAiEnvelope || !targetAiEnvelope) throw new Error('RESET_AI_ENVELOPE_NOT_FOUND');
  const canonicalProjection = `${sourceAiEnvelope.level}/${sourceAiEnvelope.completed_cycles}/${sourceAiEnvelope.target_complexity}/${sourceAiEnvelope.rank}`;
  const reset_era_ai = { legacy_user_id: edge.legacy_user_id, master_user_id: edge.master_user_id, canonical_projection: canonicalProjection, quarantined_projection: '39/108/161/S', legacy_receipts: legacyReceiptCount, master_receipts: masterReceiptCount, legacy_timestamps_newer: true, override_mode: 'EXACT_WHOLE_ROW', quarantine_encryption: 'PGP_SYM_ENCRYPT_AES256', canonical_row_digest: digest(sourceAiEnvelope), quarantined_row_digest: digest(targetAiEnvelope), quarantined_row: resetMaster };
  const qa = { personas: 4, auth_rows: 4, ttl_minutes: 30, rows: deterministicQa(auth) };
  const actionFenceInput = structuredClone(fence_input);
  if (actionFenceInput.desired_ai_overrides !== undefined) throw new Error('RESET_AI_OVERRIDE_PREEXISTS');
  const mappedSourceAi = structuredClone(sourceAiEnvelope); mappedSourceAi.user_id = edge.master_user_id; mappedSourceAi.row.user_id = edge.master_user_id; mappedSourceAi.payload_digest = digest(mappedSourceAi.row);
  const actionTargetIndex = actionFenceInput.target_snapshot.ai.findIndex((row) => row.user_id === edge.master_user_id && row.runner_key === 'menu-runner');
  if (actionTargetIndex < 0) throw new Error('RESET_ACTION_TARGET_MISSING');
  actionFenceInput.desired_ai_overrides = [mappedSourceAi];
  const rendered = renderOperationalSql({ auth, fenceInput: fence_input, actionFenceInput, catalogPreimage: catalog_preimage, reset: { quarantined_row: resetMaster, canonical_projection: canonicalProjection }, qa, quarantineKey, qaPassword });
  const raw = { schema: PRODUCER_CONTRACT.schema, packet: PRODUCER_CONTRACT.packet, evidence: { current_preimage_sha256: R017_CONTRACT.currentPreimageSha256, topology_evidence_sha256: R017_CONTRACT.topologyEvidenceSha256, restore_proof_sha256: R017_CONTRACT.restoreProofSha256, predecessor_fence_manifest_sha256: R017_CONTRACT.predecessorFenceManifestSha256, master_acl_basis: fence_input.fence.master.acl_basis }, catalog_preimage, catalog_preimage_sha256: sha256(catalog_preimage), fence_input, auth, reset_era_ai, reset_era_player, qa, sql: rendered.sql, sql_sha256: rendered.sql_sha256 };
  validatePrivateSource(raw);
  return raw;
}

export function writePrivateSource(atlasRoot, output, value) {
  const expected = path.join(atlasRoot, PRODUCER_CONTRACT.outputRelativePath);
  const secretsRoot = path.join(atlasRoot, 'secrets');
  const resolved = assertInside(output ?? expected, secretsRoot, 'PRIVATE_OUTPUT_MUST_BE_UNDER_SECRETS');
  const packetRoot = path.dirname(expected);
  if (path.normalize(path.dirname(resolved)) !== path.normalize(packetRoot) || !/^private-source(?:-[a-z0-9-]+)?\.json$/.test(path.basename(resolved))) throw new Error('PRIVATE_OUTPUT_PATH_DRIFT');
  assertNoReparseComponents(secretsRoot, secretsRoot);
  mkdirPrivateChain(path.dirname(resolved), secretsRoot);
  assertNoReparseComponents(path.dirname(resolved), secretsRoot);
  const bytes = Buffer.from(`${canonical(value)}\n`, 'utf8');
  const flags = fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY | (fs.constants.O_NOFOLLOW ?? 0);
  const fd = fs.openSync(resolved, flags, 0o600);
  try {
    const opened = fs.fstatSync(fd); if (!opened.isFile()) throw new Error('PRIVATE_OUTPUT_HANDLE_NOT_FILE');
    const finalPath = fs.realpathSync.native(resolved);
    const realRoot = fs.realpathSync.native(secretsRoot);
    assertInside(finalPath, realRoot, 'PRIVATE_OUTPUT_FINAL_PATH_ESCAPE');
    if (path.normalize(finalPath) !== path.normalize(resolved)) throw new Error('PRIVATE_OUTPUT_FINAL_PATH_DRIFT');
    fs.writeFileSync(fd, bytes); fs.fsyncSync(fd);
    const finalAfterWrite = fs.realpathSync.native(resolved);
    if (path.normalize(finalAfterWrite) !== path.normalize(finalPath)) throw new Error('PRIVATE_OUTPUT_FINAL_PATH_DRIFT');
  } finally { fs.closeSync(fd); }
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
  let quarantineKey = process.env[PRODUCER_CONTRACT.quarantineKeyEnv]; let qaPassword = process.env[PRODUCER_CONTRACT.qaPasswordEnv]; let resetBinding = null;
  if ((!quarantineKey || !qaPassword) && args['--secret-base']) {
    const retained = readRuntimeSecretsFromBase(atlasRoot, args['--secret-base'], args['--secret-base-sha256']);
    quarantineKey ||= retained.quarantineKey; qaPassword ||= retained.qaPassword; resetBinding = retained.resetBinding;
  }
  if (!legacyUrl || !masterUrl || !quarantineKey || !qaPassword) throw new Error('PRIVATE_RUNTIME_INPUT_MISSING');
  const psql = args['--psql'] ?? 'psql';
  const legacyRead = capturePrivateRead(legacyUrl, 'public', psql); const masterRead = capturePrivateRead(masterUrl, 'mazer', psql);
  const value = producePrivateSource({ legacy: legacyRead.snapshot, master: masterRead.snapshot, legacyAcl: legacyRead.acl, masterAcl: masterRead.acl, quarantineKey, qaPassword, resetBinding });
  const written = writePrivateSource(atlasRoot, args['--output'], value);
  process.stdout.write(`${JSON.stringify({ result: 'PASS_R017_PRIVATE_SOURCE_SEALED', private_source_sha256: written.sha256, private_source_bytes: written.bytes, private_path: path.relative(atlasRoot, written.path).split(path.sep).join('/'), provider_reads: 2, provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_records_emitted: false })}\n`);
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main().catch((error) => { process.stdout.write(`${JSON.stringify({ result: 'HOLD_R017_PRIVATE_SOURCE_PRODUCER', category: String(error.message).replace(/[^A-Za-z0-9_:.-]/g, '').slice(0, 160), provider_writes: 0, auth_writes: 0, live_data_writes: 0, raw_records_emitted: false })}\n`); process.exitCode = 2; });
