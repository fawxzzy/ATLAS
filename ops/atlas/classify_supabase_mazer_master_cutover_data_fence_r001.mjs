import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const CONTRACT = Object.freeze({
  inputSchema: 'atlas.supabase.mazer-master-cutover-data-fence-input.v1',
  classificationSchema: 'atlas.supabase.mazer-master-cutover-data-fence-classification.v1',
  privatePlanSchema: 'atlas.supabase.mazer-master-cutover-data-fence-private-plan.v1',
  legacy: Object.freeze({ projectRef: 'geknvnrmktchljnyddwp', schema: 'public' }),
  master: Object.freeze({ projectRef: 'bxtcuhkotumitoqtrcej', schema: 'mazer' }),
  tables: Object.freeze([
    'mazer_profiles',
    'mazer_progression_states',
    'mazer_ai_progression_states',
    'mazer_cycle_receipts'
  ]),
  mutatingRpcs: Object.freeze([
    'mazer_initialize_progression(uuid)',
    'mazer_complete_level(bigint,uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb)',
    'mazer_complete_ai_level(uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb)',
    'mazer_reset_progression(bigint,uuid)'
  ]),
  signupFence: Object.freeze({
    functionName: 'mazer_cutover_signup_admission_fence_r001',
    triggerName: 'mazer_cutover_signup_admission_fence_r001',
    claimFunction: 'mazer_claim_signup_username()',
    claimTrigger: 'mazer_claim_signup_username_after_insert'
  }),
  mutationGate: Object.freeze({
    functionName: 'mazer_cutover_mutation_gate_r001',
    triggerName: 'mazer_cutover_mutation_gate_r001',
    bypassGuc: 'atlas.mazer_cutover_writer_bypass',
    bypassValue: 'r001'
  })
});

const SIGNUP_FENCE_BODY = `
begin
  if coalesce(new.raw_user_meta_data, '{}'::jsonb) ->> 'app_namespace' = 'mazer' then
    raise exception using
      errcode = '55000',
      message = 'MAZER_SIGNUP_TEMPORARILY_UNAVAILABLE';
  end if;
  return new;
end;
`;

const MUTATION_GATE_BODY = `
begin
  if session_user = 'postgres'
    and pg_catalog.current_setting('atlas.mazer_cutover_writer_bypass', true) = 'r001'
  then
    if tg_op = 'DELETE' then
      return old;
    end if;
    return new;
  end if;
  raise exception using
    errcode = '55000',
    message = 'MAZER_CUTOVER_WRITES_FENCED';
end;
`;

const SHA256 = /^[a-f0-9]{64}$/;
const UUID = /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i;
const UNSIGNED_DECIMAL = /^(0|[1-9][0-9]*)$/;
const MAX_PG_BIGINT = 9223372036854775807n;
const RANKS = new Set(['E', 'D', 'C', 'B', 'A', 'S']);
const RANK_ORDER = new Map([...RANKS].map((rank, index) => [rank, index]));
const CLIENT_ROLES = new Set(['anon', 'authenticated', 'public']);
const TABLE_WRITE_PRIVILEGES = new Set(['INSERT', 'UPDATE', 'DELETE']);
const PHASES = Object.freeze({
  forward: ['PREFLIGHT', 'LEGACY_SIGNUP_FENCING', 'LEGACY_SIGNUP_FENCED', 'LEGACY_WRITERS_PREOBSERVING', 'LEGACY_WRITERS_PREOBSERVED', 'LEGACY_WRITERS_FENCING', 'LEGACY_WRITER_REVOKE_COMMITTED', 'LEGACY_WRITER_SET_CAPTURING', 'LEGACY_WRITER_SET_CAPTURED', 'LEGACY_WRITERS_DRAINING', 'LEGACY_WRITERS_DRAINED', 'LEGACY_LOCK_BARRIER_ACQUIRING', 'LEGACY_WRITERS_FENCED', 'SOURCE_HIGH_WATER_READ_1', 'SOURCE_HIGH_WATER_READ_2', 'PAUSED_AFTER_SOURCE_HIGH_WATER', 'CONTINUE_REVALIDATING', 'CONTINUE_SOURCE_HIGH_WATER_READ_1', 'CONTINUE_SOURCE_HIGH_WATER_READ_2', 'FORWARD_DELTA_APPLYING', 'FORWARD_DELTA_APPLIED', 'ZERO_DELTA_READ_1', 'ZERO_DELTA_READ_2', 'COMPLETE', 'LEGACY_RESTORING', 'LEGACY_RESTORED', 'PREPARATION_COMPLETE'],
  reverse: ['PREFLIGHT', 'MASTER_HOOK_DISABLING', 'MASTER_HOOK_DISABLED', 'MASTER_SIGNUP_PREOBSERVING', 'MASTER_SIGNUP_PREOBSERVED', 'MASTER_SIGNUP_FENCING', 'MASTER_SIGNUP_FENCED', 'MASTER_WRITERS_PREOBSERVING', 'MASTER_WRITERS_PREOBSERVED', 'MASTER_WRITERS_FENCING', 'MASTER_WRITER_REVOKE_COMMITTED', 'MASTER_WRITER_SET_CAPTURING', 'MASTER_WRITER_SET_CAPTURED', 'MASTER_WRITERS_DRAINING', 'MASTER_WRITERS_DRAINED', 'MASTER_LOCK_BARRIER_ACQUIRING', 'MASTER_WRITERS_FENCED', 'SOURCE_HIGH_WATER_READ_1', 'SOURCE_HIGH_WATER_READ_2', 'REVERSE_DELTA_APPLYING', 'REVERSE_DELTA_APPLIED', 'ZERO_DELTA_READ_1', 'ZERO_DELTA_READ_2', 'LEGACY_WRITERS_RESTORING', 'LEGACY_WRITERS_RESTORED', 'LEGACY_SIGNUP_RESTORING', 'MASTER_HOOK_RESTORING', 'MASTER_HOOK_RESTORED', 'MASTER_SIGNUP_RESTORING', 'COMPLETE']
});

export class CutoverHold extends Error {
  constructor(code) {
    super(code);
    this.name = 'CutoverHold';
    this.code = code;
  }
}

const hold = (code) => { throw new CutoverHold(code); };
const isPlain = (value) => value !== null
  && typeof value === 'object'
  && !Array.isArray(value)
  && Object.getPrototypeOf(value) === Object.prototype;

function requirePlain(value, code = 'INPUT_SHAPE') {
  if (!isPlain(value)) hold(code);
  return value;
}

function requireArray(value, code = 'INPUT_SHAPE') {
  if (!Array.isArray(value)) hold(code);
  return value;
}

function requireString(value, code = 'INPUT_SHAPE') {
  if (typeof value !== 'string' || value.length === 0) hold(code);
  return value;
}

function requireDigest(value, code) {
  if (typeof value !== 'string' || !SHA256.test(value)) hold(code);
  return value;
}

function requireUuid(value, code = 'IDENTITY_SHAPE') {
  if (typeof value !== 'string' || !UUID.test(value)) hold(code);
  return value.toLowerCase();
}

function requireUnsignedDecimal(value, code, { positive = false } = {}) {
  const decimal = typeof value === 'bigint' ? value.toString() : value;
  if (typeof decimal !== 'string' || !UNSIGNED_DECIMAL.test(decimal)) hold(code);
  const parsed = BigInt(decimal);
  if ((positive && parsed === 0n) || parsed > MAX_PG_BIGINT) hold(code);
  return decimal;
}

function stableValue(value) {
  if (typeof value === 'bigint') return value.toString();
  if (Array.isArray(value)) return value.map(stableValue);
  if (!isPlain(value)) return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
}

export function canonicalJson(value) {
  return JSON.stringify(stableValue(value));
}

export function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonicalJson(value));
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function sortRows(rows, key) {
  return [...rows].sort((left, right) => canonicalJson(key(left)).localeCompare(canonicalJson(key(right))));
}

export function snapshotDigest(snapshot) {
  const value = normalizeSnapshot(snapshot, { validateOnly: true });
  return sha256({
    auth: sortRows(value.auth, (row) => [row.user_id, row.email_digest]),
    profiles: sortRows(value.profiles, (row) => row.user_id),
    player: sortRows(value.player, (row) => row.user_id),
    ai: sortRows(value.ai, (row) => [row.user_id, row.runner_key]),
    receipts: sortRows(value.receipts, (row) => row.id)
  });
}

function normalizeRowEnvelope(value, kind, { mappedOwnerNeutral = false } = {}) {
  const row = requirePlain(value, `${kind.toUpperCase()}_ROW_SHAPE`);
  const userId = requireUuid(row.user_id);
  const claimedPayloadDigest = requireDigest(row.payload_digest, `${kind.toUpperCase()}_PAYLOAD_DIGEST`);
  const raw = structuredClone(requirePlain(row.row, `${kind.toUpperCase()}_PRIVATE_ROW_SHAPE`));
  if (requireUuid(raw.user_id) !== userId) hold(`${kind.toUpperCase()}_ROW_OWNER_MISMATCH`);
  if (kind === 'player') {
    raw.player_level = requireUnsignedDecimal(raw.player_level, 'PLAYER_RAW_LEVEL_SHAPE', { positive: true });
    raw.player_completed_cycles = requireUnsignedDecimal(raw.player_completed_cycles, 'PLAYER_RAW_CYCLES_SHAPE');
    const statePlayer = requirePlain(requirePlain(requirePlain(raw.state, 'PLAYER_RAW_STATE_SHAPE').tracks, 'PLAYER_RAW_STATE_SHAPE').player, 'PLAYER_RAW_STATE_SHAPE');
    statePlayer.level = requireUnsignedDecimal(statePlayer.level, 'PLAYER_STATE_LEVEL_SHAPE', { positive: true });
    statePlayer.completedCycles = requireUnsignedDecimal(statePlayer.completedCycles, 'PLAYER_STATE_CYCLES_SHAPE');
    if (statePlayer.level !== raw.player_level || statePlayer.completedCycles !== raw.player_completed_cycles) hold('PLAYER_RAW_STATE_PROJECTION_CONFLICT');
  }
  if (kind === 'ai') {
    raw.level = requireUnsignedDecimal(raw.level, 'AI_RAW_LEVEL_SHAPE', { positive: true });
    raw.completed_cycles = requireUnsignedDecimal(raw.completed_cycles, 'AI_RAW_CYCLES_SHAPE');
    const state = requirePlain(raw.state, 'AI_RAW_STATE_SHAPE');
    const summary = requirePlain(raw.summary, 'AI_RAW_SUMMARY_SHAPE');
    state.level = requireUnsignedDecimal(state.level, 'AI_STATE_LEVEL_SHAPE', { positive: true });
    state.completedCycles = requireUnsignedDecimal(state.completedCycles, 'AI_STATE_CYCLES_SHAPE');
    summary.level = requireUnsignedDecimal(summary.level, 'AI_SUMMARY_LEVEL_SHAPE', { positive: true });
    summary.completedCycles = requireUnsignedDecimal(summary.completedCycles, 'AI_SUMMARY_CYCLES_SHAPE');
    if (state.level !== raw.level || state.completedCycles !== raw.completed_cycles || summary.level !== raw.level || summary.completedCycles !== raw.completed_cycles) hold('AI_RAW_STATE_PROJECTION_CONFLICT');
  }
  const digestable = mappedOwnerNeutral ? { ...raw, user_id: '__mapped-owner__' } : raw;
  const recomputedPayloadDigest = sha256(digestable);
  if (claimedPayloadDigest !== recomputedPayloadDigest) hold(`${kind.toUpperCase()}_PAYLOAD_DIGEST_MISMATCH`);
  return { ...row, user_id: userId, payload_digest: recomputedPayloadDigest, row: raw };
}

function normalizeProfile(value) {
  const row = normalizeRowEnvelope(value, 'profile');
  if (!Number.isSafeInteger(row.revision) || row.revision < 0) hold('PROFILE_REVISION_SHAPE');
  if (row.row.revision !== row.revision) hold('PROFILE_REVISION_PROJECTION_CONFLICT');
  if (row.username_digest !== null) {
    requireDigest(row.username_digest, 'PROFILE_USERNAME_DIGEST');
    if (typeof row.row.username !== 'string' || sha256(row.row.username.toLowerCase()) !== row.username_digest) hold('PROFILE_USERNAME_DIGEST_MISMATCH');
  }
  if (typeof row.username_present !== 'boolean' || row.username_present !== (row.username_digest !== null)) hold('PROFILE_USERNAME_SHAPE');
  if (row.username_present !== (row.row.username !== null)) hold('PROFILE_USERNAME_PROJECTION_CONFLICT');
  return row;
}

function normalizePlayer(value) {
  const row = normalizeRowEnvelope(value, 'player');
  row.level = requireUnsignedDecimal(row.level, 'PLAYER_LEVEL_SHAPE', { positive: true });
  row.completed_cycles = requireUnsignedDecimal(row.completed_cycles, 'PLAYER_CYCLES_SHAPE');
  if (!Number.isSafeInteger(row.revision) || row.revision < 0) hold('PLAYER_REVISION_SHAPE');
  if (!Number.isInteger(row.target_complexity) || row.target_complexity < 8 || row.target_complexity > 400) hold('PLAYER_DIFFICULTY_SHAPE');
  if (!RANKS.has(row.rank) || row.state_projection_matches !== true) hold('PLAYER_PROJECTION_CONFLICT');
  if (row.row.player_level !== row.level || row.row.player_completed_cycles !== row.completed_cycles || row.row.player_rank !== row.rank || row.row.player_target_complexity !== row.target_complexity) hold('PLAYER_PROJECTION_CONFLICT');
  return row;
}

function normalizeAi(value) {
  const row = normalizeRowEnvelope(value, 'ai');
  if (row.runner_key !== 'menu-runner') hold('AI_RUNNER_KEY');
  row.level = requireUnsignedDecimal(row.level, 'AI_LEVEL_SHAPE', { positive: true });
  row.completed_cycles = requireUnsignedDecimal(row.completed_cycles, 'AI_CYCLES_SHAPE');
  if (!Number.isInteger(row.target_complexity) || row.target_complexity < 8 || row.target_complexity > 400) hold('AI_DIFFICULTY_SHAPE');
  if (!RANKS.has(row.rank) || row.state_projection_matches !== true) hold('AI_PROJECTION_CONFLICT');
  if (row.row.runner_key !== row.runner_key || row.row.level !== row.level || row.row.completed_cycles !== row.completed_cycles || row.row.rank !== row.rank || row.row.target_complexity !== row.target_complexity) hold('AI_PROJECTION_CONFLICT');
  return row;
}

function normalizeReceipt(value) {
  const row = normalizeRowEnvelope(value, 'receipt', { mappedOwnerNeutral: true });
  row.id = requireUuid(row.id, 'RECEIPT_ID_SHAPE');
  if (requireUuid(row.row.id, 'RECEIPT_ID_SHAPE') !== row.id) hold('RECEIPT_ROW_ID_MISMATCH');
  row.client_run_id = row.client_run_id === null ? null : requireUuid(row.client_run_id, 'CLIENT_RUN_ID_SHAPE');
  if ((row.row.client_run_id ?? null) !== row.client_run_id) hold('RECEIPT_CLIENT_RUN_ID_MISMATCH');
  return row;
}

function uniqueRows(rows, key, conflictCode) {
  const found = new Map();
  for (const row of rows) {
    const id = canonicalJson(key(row));
    if (found.has(id)) hold(conflictCode);
    found.set(id, row);
  }
  return [...found.values()];
}

function normalizeSnapshot(value, { validateOnly = false } = {}) {
  const snapshot = requirePlain(value, 'SNAPSHOT_SHAPE');
  const auth = uniqueRows(requireArray(snapshot.auth).map((entry) => {
    const row = requirePlain(entry, 'AUTH_ROW_SHAPE');
    return {
      user_id: requireUuid(row.user_id),
      email_digest: requireDigest(row.email_digest, 'AUTH_EMAIL_DIGEST'),
      identity_count: Number(row.identity_count),
      email_identity_count: Number(row.email_identity_count),
      ambiguous: row.ambiguous === true
    };
  }), (row) => row.user_id, 'DUPLICATE_AUTH_USER');
  for (const row of auth) {
    if (!Number.isInteger(row.identity_count) || row.identity_count !== 1 || row.email_identity_count !== 1 || row.ambiguous) hold('AMBIGUOUS_IDENTITY');
  }
  const normalized = {
    auth,
    profiles: uniqueRows(requireArray(snapshot.profiles).map(normalizeProfile), (row) => row.user_id, 'DUPLICATE_PROFILE'),
    player: uniqueRows(requireArray(snapshot.player).map(normalizePlayer), (row) => row.user_id, 'DUPLICATE_PLAYER'),
    ai: uniqueRows(requireArray(snapshot.ai).map(normalizeAi), (row) => [row.user_id, row.runner_key], 'DUPLICATE_AI'),
    receipts: uniqueRows(requireArray(snapshot.receipts).map(normalizeReceipt), (row) => row.id, 'DUPLICATE_RECEIPT')
  };
  if (!validateOnly && typeof snapshot.observed_at !== 'string') hold('SNAPSHOT_TIMESTAMP');
  return normalized;
}

function normalizeBindings(value) {
  const bindings = requirePlain(value, 'BINDING_SHAPE');
  for (const [name, exact] of [['legacy', CONTRACT.legacy], ['master', CONTRACT.master]]) {
    const binding = requirePlain(bindings[name], 'BINDING_SHAPE');
    if (binding.project_ref !== exact.projectRef || binding.schema !== exact.schema) hold('PROJECT_OR_SCHEMA_DRIFT');
  }
  return bindings;
}

function normalizeIdentityMap(value, direction) {
  const edges = requireArray(value, 'IDENTITY_MAP_SHAPE').map((entry) => {
    const edge = requirePlain(entry, 'IDENTITY_EDGE_SHAPE');
    if (edge.disposition !== 'BOUND' || edge.ambiguous === true) hold('AMBIGUOUS_IDENTITY');
    return {
      legacy_user_id: requireUuid(edge.legacy_user_id),
      master_user_id: requireUuid(edge.master_user_id),
      disposition: 'BOUND'
    };
  });
  uniqueRows(edges, (edge) => edge.legacy_user_id, 'IDENTITY_MAP_SOURCE_DUPLICATE');
  uniqueRows(edges, (edge) => edge.master_user_id, 'IDENTITY_MAP_TARGET_DUPLICATE');
  const map = new Map(edges.map((edge) => direction === 'forward'
    ? [edge.legacy_user_id, edge.master_user_id]
    : [edge.master_user_id, edge.legacy_user_id]));
  return { edges: sortRows(edges, (edge) => [edge.legacy_user_id, edge.master_user_id]), map };
}

function requireExactKeys(value, expected, code) {
  const actual = Object.keys(value).sort();
  if (canonicalJson(actual) !== canonicalJson([...expected].sort())) hold(code);
}

function normalizeAclPreimage(value, schema) {
  const preimage = requirePlain(value, 'ACL_PREIMAGE_SHAPE');
  requireExactKeys(preimage, ['schema', 'table_acl', 'rpc_acl', 'catalog'], 'ACL_PREIMAGE_KEYS');
  if (preimage.schema !== schema) hold('ACL_PREIMAGE_SCHEMA_DRIFT');
  const normalizeGrant = (entry, { table }) => {
    const grant = requirePlain(entry, 'ACL_GRANT_SHAPE');
    requireExactKeys(grant, table ? ['grantee', 'privilege', 'is_grantable'] : ['grantee', 'is_grantable'], 'ACL_GRANT_KEYS');
    if (!CLIENT_ROLES.has(grant.grantee) || typeof grant.is_grantable !== 'boolean') hold('ACL_GRANT_SHAPE');
    if (table && !TABLE_WRITE_PRIVILEGES.has(grant.privilege)) hold('ACL_GRANT_SHAPE');
    return table
      ? { grantee: grant.grantee, privilege: grant.privilege, is_grantable: grant.is_grantable }
      : { grantee: grant.grantee, is_grantable: grant.is_grantable };
  };
  const tableAcl = uniqueRows(requireArray(preimage.table_acl, 'TABLE_ACL_SHAPE').map((entry) => {
    const table = requirePlain(entry, 'TABLE_ACL_SHAPE');
    requireExactKeys(table, ['name', 'grants'], 'TABLE_ACL_KEYS');
    if (!CONTRACT.tables.includes(table.name)) hold('TABLE_ACL_NAME');
    const grants = uniqueRows(requireArray(table.grants).map((grant) => normalizeGrant(grant, { table: true })), (grant) => [grant.grantee, grant.privilege], 'TABLE_ACL_DUPLICATE_GRANT');
    return { name: table.name, grants: sortRows(grants, (grant) => [grant.grantee, grant.privilege, grant.is_grantable]) };
  }), (entry) => entry.name, 'TABLE_ACL_DUPLICATE_TABLE');
  if (tableAcl.length !== CONTRACT.tables.length || CONTRACT.tables.some((name) => !tableAcl.some((entry) => entry.name === name))) hold('TABLE_ACL_INCOMPLETE');
  const rpcAcl = uniqueRows(requireArray(preimage.rpc_acl, 'RPC_ACL_SHAPE').map((entry) => {
    const rpc = requirePlain(entry, 'RPC_ACL_SHAPE');
    requireExactKeys(rpc, ['signature', 'grants'], 'RPC_ACL_KEYS');
    if (!CONTRACT.mutatingRpcs.includes(rpc.signature)) hold('RPC_ACL_SIGNATURE');
    const grants = uniqueRows(requireArray(rpc.grants).map((grant) => normalizeGrant(grant, { table: false })), (grant) => grant.grantee, 'RPC_ACL_DUPLICATE_GRANT');
    return { signature: rpc.signature, grants: sortRows(grants, (grant) => [grant.grantee, grant.is_grantable]) };
  }), (entry) => entry.signature, 'RPC_ACL_DUPLICATE_RPC');
  if (rpcAcl.length !== CONTRACT.mutatingRpcs.length || CONTRACT.mutatingRpcs.some((signature) => !rpcAcl.some((entry) => entry.signature === signature))) hold('RPC_ACL_INCOMPLETE');
  const catalog = requirePlain(preimage.catalog, 'ACL_CATALOG_SHAPE');
  requireExactKeys(catalog, ['tables', 'rpcs'], 'ACL_CATALOG_KEYS');
  const catalogTables = uniqueRows(requireArray(catalog.tables).map((entry) => {
    const table = requirePlain(entry, 'ACL_CATALOG_TABLE_SHAPE');
    requireExactKeys(table, ['name', 'relkind', 'rls_enabled', 'force_rls'], 'ACL_CATALOG_TABLE_KEYS');
    if (!CONTRACT.tables.includes(table.name) || table.relkind !== 'r' || typeof table.rls_enabled !== 'boolean' || typeof table.force_rls !== 'boolean') hold('ACL_CATALOG_TABLE_SHAPE');
    return { name: table.name, relkind: table.relkind, rls_enabled: table.rls_enabled, force_rls: table.force_rls };
  }), (entry) => entry.name, 'ACL_CATALOG_DUPLICATE_TABLE');
  if (catalogTables.length !== CONTRACT.tables.length || CONTRACT.tables.some((name) => !catalogTables.some((entry) => entry.name === name))) hold('ACL_CATALOG_TABLE_INCOMPLETE');
  const catalogRpcs = uniqueRows(requireArray(catalog.rpcs).map((entry) => {
    const rpc = requirePlain(entry, 'ACL_CATALOG_RPC_SHAPE');
    requireExactKeys(rpc, ['signature', 'kind', 'security_definer', 'volatility'], 'ACL_CATALOG_RPC_KEYS');
    if (!CONTRACT.mutatingRpcs.includes(rpc.signature) || rpc.kind !== 'f' || typeof rpc.security_definer !== 'boolean' || !['i', 's', 'v'].includes(rpc.volatility)) hold('ACL_CATALOG_RPC_SHAPE');
    return { signature: rpc.signature, kind: rpc.kind, security_definer: rpc.security_definer, volatility: rpc.volatility };
  }), (entry) => entry.signature, 'ACL_CATALOG_DUPLICATE_RPC');
  if (catalogRpcs.length !== CONTRACT.mutatingRpcs.length || CONTRACT.mutatingRpcs.some((signature) => !catalogRpcs.some((entry) => entry.signature === signature))) hold('ACL_CATALOG_RPC_INCOMPLETE');
  return {
    schema,
    table_acl: sortRows(tableAcl, (entry) => entry.name),
    rpc_acl: sortRows(rpcAcl, (entry) => entry.signature),
    catalog: {
      tables: sortRows(catalogTables, (entry) => entry.name),
      rpcs: sortRows(catalogRpcs, (entry) => entry.signature)
    }
  };
}

function aclDigest(preimage) {
  return sha256({ schema: preimage.schema, table_acl: preimage.table_acl, rpc_acl: preimage.rpc_acl });
}

function catalogDigest(preimage) {
  return sha256({ schema: preimage.schema, catalog: preimage.catalog });
}

function validateFence(value, direction) {
  const fence = requirePlain(value, 'FENCE_SHAPE');
  const normalized = {};
  for (const [name, binding] of [['legacy', CONTRACT.legacy], ['master', CONTRACT.master]]) {
    const rawSide = requirePlain(fence[name], 'FENCE_SIDE_SHAPE');
    const preimage = normalizeAclPreimage(rawSide.acl_preimage, binding.schema);
    if (requireDigest(rawSide.acl_preimage_digest, 'ACL_PREIMAGE_DIGEST') !== aclDigest(preimage)) hold('ACL_PREIMAGE_DIGEST_DRIFT');
    if (requireDigest(rawSide.catalog_digest, 'FENCE_CATALOG_DIGEST') !== catalogDigest(preimage)) hold('FENCE_CATALOG_DIGEST_DRIFT');
    normalized[name] = { ...rawSide, acl_preimage: preimage };
  }
  const side = direction === 'forward' ? normalized.legacy : normalized.master;
  if (direction === 'forward' && side.signup_disabled !== true) hold('PARTIAL_WRITER_FENCE');
  if (direction === 'reverse' && normalized.master.before_user_created_hook_enabled !== false) hold('DISABLE_HOOK_FIRST_REQUIRED');
  const tableWriters = requirePlain(side.table_writers, 'FENCE_TABLE_SHAPE');
  const rpcWriters = requirePlain(side.rpc_writers, 'FENCE_RPC_SHAPE');
  for (const table of CONTRACT.tables) if (tableWriters[table] !== 'FENCED') hold('PARTIAL_WRITER_FENCE');
  for (const rpc of CONTRACT.mutatingRpcs) if (rpcWriters[rpc] !== 'FENCED') hold('PARTIAL_WRITER_FENCE');
  if (typeof side.fenced_at !== 'string' || Number.isNaN(Date.parse(side.fenced_at))) hold('FENCE_TIMESTAMP');
  return normalized;
}

function mapSnapshot(snapshot, identityMap) {
  const remap = (row, { preservePayloadDigest = false } = {}) => {
    const mappedUser = identityMap.get(row.user_id);
    if (!mappedUser) hold('AMBIGUOUS_IDENTITY');
    const mapped = { ...structuredClone(row), user_id: mappedUser, row: { ...structuredClone(row.row), user_id: mappedUser } };
    if (preservePayloadDigest) {
      const mappedNeutralDigest = sha256({ ...mapped.row, user_id: '__mapped-owner__' });
      if (mappedNeutralDigest !== row.payload_digest) hold('RECEIPT_MAPPED_PAYLOAD_DIGEST_MISMATCH');
      mapped.payload_digest = mappedNeutralDigest;
    } else mapped.payload_digest = sha256(mapped.row);
    return mapped;
  };
  return {
    auth: snapshot.auth.map((row) => {
      const mappedUser = identityMap.get(row.user_id);
      if (!mappedUser) hold('AMBIGUOUS_IDENTITY');
      return { ...row, user_id: mappedUser };
    }),
    profiles: snapshot.profiles.map((row) => remap(row)),
    player: snapshot.player.map((row) => remap(row)),
    ai: snapshot.ai.map((row) => remap(row)),
    receipts: snapshot.receipts.map((row) => remap(row, { preservePayloadDigest: true }))
  };
}

function byUser(rows) {
  return new Map(rows.map((row) => [row.user_id, row]));
}

function mergeProfiles(sourceRows, targetRows) {
  const source = byUser(sourceRows);
  const target = byUser(targetRows);
  const users = new Set([...source.keys(), ...target.keys()]);
  const rows = [];
  for (const userId of users) {
    const left = source.get(userId);
    const right = target.get(userId);
    if (!left) { rows.push(structuredClone(right)); continue; }
    if (!right) { rows.push(structuredClone(left)); continue; }
    if (left.payload_digest === right.payload_digest) { rows.push(structuredClone(right)); continue; }
    if (left.username_digest && right.username_digest && left.username_digest !== right.username_digest) hold('PROFILE_USERNAME_CONFLICT');
    const winner = left.revision > right.revision ? left : right;
    const merged = structuredClone(winner);
    merged.revision = Math.max(left.revision, right.revision) + 1;
    merged.row.revision = merged.revision;
    if (!right.username_digest && left.username_digest) {
      merged.username_digest = left.username_digest;
      merged.username_present = true;
      merged.row.username = left.row.username;
    }
    merged.payload_digest = sha256(merged.row);
    rows.push(merged);
  }
  uniqueRows(rows.filter((row) => row.username_digest), (row) => row.username_digest, 'PROFILE_USERNAME_COLLISION');
  return rows;
}

function mergeProgression(sourceRows, targetRows, kind) {
  const source = byUser(sourceRows);
  const target = byUser(targetRows);
  const users = new Set([...source.keys(), ...target.keys()]);
  const rows = [];
  for (const userId of users) {
    const left = source.get(userId);
    const right = target.get(userId);
    if (!left) { rows.push(structuredClone(right)); continue; }
    if (!right) { rows.push(structuredClone(left)); continue; }
    if (left.payload_digest === right.payload_digest) { rows.push(structuredClone(right)); continue; }
    const maxLevel = BigInt(left.level) >= BigInt(right.level) ? left.level : right.level;
    const maxCycles = BigInt(left.completed_cycles) >= BigInt(right.completed_cycles) ? left.completed_cycles : right.completed_cycles;
    const maxComplexity = Math.max(left.target_complexity, right.target_complexity);
    const maxRank = RANK_ORDER.get(left.rank) >= RANK_ORDER.get(right.rank) ? left.rank : right.rank;
    const dominates = (row) => row.level === maxLevel
      && row.completed_cycles === maxCycles
      && row.target_complexity === maxComplexity
      && row.rank === maxRank;
    const candidates = [left, right].filter(dominates);
    if (candidates.length === 0) hold(`${kind.toUpperCase()}_INCOMPATIBLE_HISTORY`);
    const winner = kind === 'player'
      ? candidates.reduce((best, row) => row.revision > best.revision ? row : best, candidates.includes(right) ? right : left)
      : candidates.includes(right) ? right : left;
    const merged = structuredClone(winner);
    merged.level = maxLevel;
    merged.completed_cycles = maxCycles;
    merged.target_complexity = maxComplexity;
    merged.rank = maxRank;
    merged.row[kind === 'player' ? 'player_level' : 'level'] = maxLevel;
    merged.row[kind === 'player' ? 'player_completed_cycles' : 'completed_cycles'] = maxCycles;
    merged.row[kind === 'player' ? 'player_target_complexity' : 'target_complexity'] = maxComplexity;
    merged.row[kind === 'player' ? 'player_rank' : 'rank'] = maxRank;
    if (kind === 'player') {
      merged.revision = Math.max(left.revision, right.revision) + 1;
      merged.row.revision = merged.revision;
    }
    merged.payload_digest = sha256(merged.row);
    rows.push(merged);
  }
  return rows;
}

function mergeReceipts(sourceRows, targetRows) {
  const primary = new Map();
  const secondary = new Map();
  let overlaps = 0;
  for (const row of [...targetRows, ...sourceRows]) {
    const existing = primary.get(row.id);
    if (existing) {
      if (existing.user_id !== row.user_id || existing.payload_digest !== row.payload_digest) hold('RECEIPT_ID_CONFLICT');
      overlaps += 1;
      continue;
    }
    if (row.client_run_id) {
      const key = `${row.user_id}:${row.client_run_id}`;
      const byRun = secondary.get(key);
      if (byRun && (byRun.id !== row.id || byRun.payload_digest !== row.payload_digest)) hold('RECEIPT_CLIENT_RUN_CONFLICT');
      secondary.set(key, row);
    }
    primary.set(row.id, structuredClone(row));
  }
  return { rows: [...primary.values()], overlaps };
}

function rowChanges(expectedRows, desiredRows, key) {
  const before = new Map(expectedRows.map((row) => [canonicalJson(key(row)), row.payload_digest]));
  let changed = 0;
  for (const row of desiredRows) if (before.get(canonicalJson(key(row))) !== row.payload_digest) changed += 1;
  return changed;
}

function mergeSnapshots(source, target) {
  const receipts = mergeReceipts(source.receipts, target.receipts);
  const desired = {
    profiles: mergeProfiles(source.profiles, target.profiles),
    player: mergeProgression(source.player, target.player, 'player'),
    ai: mergeProgression(source.ai, target.ai, 'ai'),
    receipts: receipts.rows
  };
  const changes = {
    profiles: rowChanges(target.profiles, desired.profiles, (row) => row.user_id),
    player: rowChanges(target.player, desired.player, (row) => row.user_id),
    ai: rowChanges(target.ai, desired.ai, (row) => [row.user_id, row.runner_key]),
    receipts: rowChanges(target.receipts, desired.receipts, (row) => row.id)
  };
  return { desired, changes, receiptOverlaps: receipts.overlaps };
}

function reverseDelta(source, baseline) {
  const changed = (rows, baselineRows, key, conflictCode = null) => {
    const prior = new Map(baselineRows.map((row) => [canonicalJson(key(row)), row]));
    const current = new Map(rows.map((row) => [canonicalJson(key(row)), row]));
    for (const [id, row] of prior) {
      const next = current.get(id);
      if (!next) hold('SOURCE_HISTORY_DELETION');
      if (conflictCode && next.payload_digest !== row.payload_digest) hold(conflictCode);
    }
    return rows.filter((row) => prior.get(canonicalJson(key(row)))?.payload_digest !== row.payload_digest);
  };
  return {
    auth: source.auth.filter((row) => !baseline.auth.some((prior) => prior.user_id === row.user_id)),
    profiles: changed(source.profiles, baseline.profiles, (row) => row.user_id),
    player: changed(source.player, baseline.player, (row) => row.user_id),
    ai: changed(source.ai, baseline.ai, (row) => [row.user_id, row.runner_key]),
    receipts: changed(source.receipts, baseline.receipts, (row) => row.id, 'RECEIPT_HISTORY_CONFLICT')
  };
}

function countSnapshot(snapshot) {
  return Object.fromEntries(['auth', 'profiles', 'player', 'ai', 'receipts'].map((name) => [name, snapshot[name].length]));
}

function sanitizePlanRows(snapshot) {
  return Object.fromEntries(['profiles', 'player', 'ai', 'receipts'].map((name) => [name, snapshot[name].map((entry) => structuredClone(entry.row))]));
}

function assertObservationConvergence(input, fencedSource) {
  const observations = requireArray(input.zero_delta_reads, 'ZERO_DELTA_READ_SHAPE');
  if (observations.length !== 2) hold('TWO_ZERO_DELTA_READS_REQUIRED');
  const expectedDigest = snapshotDigest(fencedSource);
  let previousTime = Date.parse(requireString(input.fence[`${input.direction === 'forward' ? 'legacy' : 'master'}`].fenced_at));
  for (const observation of observations) {
    const time = Date.parse(requireString(observation.observed_at, 'ZERO_DELTA_TIMESTAMP'));
    if (!Number.isFinite(time) || time <= previousTime) hold('ZERO_DELTA_OBSERVATION_ORDER');
    const digest = snapshotDigest(observation);
    if (digest !== expectedDigest) hold('POST_FENCE_LATE_WRITE');
    previousTime = time;
  }
  return expectedDigest;
}

function validateJournal(input) {
  if (input.journal === undefined || input.journal === null) return;
  const journal = requirePlain(input.journal, 'JOURNAL_SHAPE');
  if (journal.direction !== input.direction || !PHASES[input.direction].includes(journal.phase)) hold('JOURNAL_PHASE_DRIFT');
  if (journal.interrupted !== true) return;
  if (journal.phase === 'PREFLIGHT') hold(`INTERRUPTED_${input.direction.toUpperCase()}_NO_EFFECT_RESTART_REQUIRED`);
  if (journal.direction === 'reverse' && journal.phase.startsWith('LEGACY_')) hold('INTERRUPTED_REVERSE_ACTIVATION_REFENCE_REQUIRED');
  if (journal.phase.includes('DELTA_APPL') || journal.phase.startsWith('ZERO_DELTA_READ_')) hold(`INTERRUPTED_${input.direction.toUpperCase()}_VERIFY_OR_ROLLBACK_REQUIRED`);
  hold(`INTERRUPTED_${input.direction.toUpperCase()}_PREIMAGE_RESTORE_REQUIRED`);
}

export function classifyRecoveryState(state) {
  if (state === null || state === undefined) return { result: 'START', effect: 'NONE' };
  const journal = requirePlain(state, 'JOURNAL_SHAPE');
  if (!['forward', 'reverse'].includes(journal.direction) || !PHASES[journal.direction].includes(journal.phase)) hold('JOURNAL_PHASE_DRIFT');
  if (journal.phase === 'PREPARATION_COMPLETE') return { result: 'EXACT_REPLAY_NOOP', effect: 'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER' };
  if (journal.phase === 'COMPLETE') return { result: 'RELEASE_LEGACY_REQUIRED', effect: 'MASTER_PREPARED_LEGACY_FENCED' };
  if (journal.phase === 'PAUSED_AFTER_SOURCE_HIGH_WATER') return { result: 'CONTINUE_OR_ROLLBACK', effect: 'LEGACY_FENCED_EXACT_CONTINUATION' };
  if (['LEGACY_RESTORING', 'LEGACY_RESTORED'].includes(journal.phase)) return { result: 'RESUME_LEGACY_RESTORE', effect: 'LEGACY_RESTORE_INCOMPLETE' };
  if (journal.phase === 'PREFLIGHT') return { result: `RESTART_${journal.direction.toUpperCase()}`, effect: 'NONE' };
  if (journal.direction === 'reverse' && journal.phase.startsWith('LEGACY_')) {
    return { result: 'REFENCE_LEGACY_WRITERS', effect: 'DUAL_WRITER_RISK' };
  }
  if (journal.direction === 'reverse' && ['MASTER_SIGNUP_PREOBSERVING', 'MASTER_SIGNUP_PREOBSERVED'].includes(journal.phase)) {
    return { result: 'RESTORE_MASTER_HOOK_PREIMAGE', effect: 'AUTH_CONFIG_ONLY' };
  }
  if (journal.direction === 'reverse' && journal.phase === 'MASTER_SIGNUP_FENCING') {
    return { result: 'OBSERVE_SIGNUP_ADMISSION_THEN_RESTORE', effect: 'SIGNUP_FENCE_COMMIT_UNKNOWN_HOOK_DISABLED' };
  }
  if (journal.direction === 'reverse' && ['MASTER_SIGNUP_FENCED', 'MASTER_WRITERS_PREOBSERVING', 'MASTER_WRITERS_PREOBSERVED'].includes(journal.phase)) {
    return { result: 'RESTORE_MASTER_HOOK_THEN_SIGNUP_ADMISSION_PREIMAGE', effect: 'MAZER_SIGNUPS_FENCED' };
  }
  if (journal.direction === 'reverse' && ['MASTER_HOOK_RESTORING', 'MASTER_HOOK_RESTORED', 'MASTER_SIGNUP_RESTORING'].includes(journal.phase)) {
    return { result: 'RESUME_OVERLAPPED_SIGNUP_PREIMAGE_RESTORE', effect: 'MAZER_SIGNUPS_FENCED_OR_HOOK_RESTORED' };
  }
  if (journal.phase.endsWith('_WRITERS_PREOBSERVING') || journal.phase.endsWith('_WRITERS_PREOBSERVED')) {
    return {
      result: journal.direction === 'forward' ? 'RESTORE_LEGACY_SIGNUP_PREIMAGE' : 'RESTORE_MASTER_HOOK_PREIMAGE',
      effect: 'AUTH_CONFIG_ONLY'
    };
  }
  if (journal.phase.endsWith('_WRITERS_FENCING')) {
    return { result: 'OBSERVE_REVOKE_THEN_DRAIN_OR_RESTORE', effect: 'REVOKE_COMMIT_UNKNOWN' };
  }
  if (journal.phase.includes('_WRITER_REVOKE_COMMITTED') || journal.phase.includes('_WRITER_SET_') || journal.phase.endsWith('_WRITERS_DRAINING') || journal.phase.endsWith('_WRITERS_DRAINED') || journal.phase.endsWith('_LOCK_BARRIER_ACQUIRING')) {
    return { result: 'RESUME_EXACT_WRITER_DRAIN_BEFORE_RESTORE', effect: 'ACL_REVOKED_HOLD_FENCED' };
  }
  if (journal.phase.endsWith('_WRITERS_FENCED')) {
    return { result: 'RESTORE_JOURNALED_ACL_AND_AUTH_PREIMAGE', effect: 'DRAIN_AND_LOCK_BARRIER_PROVEN' };
  }
  if (journal.phase.includes('DELTA_APPL') || journal.phase.startsWith('ZERO_DELTA_READ_')) {
    return { result: `RESUME_${journal.direction.toUpperCase()}_VERIFICATION`, effect: 'DELTA_MAY_BE_COMMITTED' };
  }
  return {
    result: journal.direction === 'forward' ? 'ROLLBACK_FORWARD_FENCE' : 'RESTORE_MASTER_PREIMAGE',
    effect: 'FENCE_ONLY'
  };
}

const q = (identifier) => `"${identifier.replaceAll('"', '""')}"`;
const encodedJson = (value) => `pg_catalog.convert_from(pg_catalog.decode('${Buffer.from(JSON.stringify(value), 'utf8').toString('base64')}', 'base64'), 'UTF8')::jsonb`;

const TABLE_COLUMNS = Object.freeze({
  mazer_profiles: ['user_id', 'display_name', 'selected_control_mode', 'settings', 'created_at', 'updated_at', 'revision', 'username'],
  mazer_progression_states: ['user_id', 'schema_version', 'state', 'last_completed_cycle_at', 'created_at', 'updated_at', 'player_level', 'player_rank', 'player_target_complexity', 'player_completed_cycles', 'revision', 'level_reached_at'],
  mazer_ai_progression_states: ['user_id', 'runner_key', 'schema_version', 'state', 'summary', 'level', 'rank', 'target_complexity', 'completed_cycles', 'last_completed_cycle_at', 'created_at', 'updated_at'],
  mazer_cycle_receipts: ['id', 'user_id', 'surface', 'maze_seed', 'maze_size', 'route_quality', 'start_cell', 'goal_cell', 'path_length', 'wrong_turns', 'backtracks', 'completion_time_ms', 'reset_used', 'control_mode', 'average_frame_ms', 'receipt', 'completed_at', 'created_at', 'ruleset_id', 'recipe_version', 'recipe_hash', 'client_run_id']
});

const TABLE_KEYS = Object.freeze({
  mazer_profiles: ['user_id'],
  mazer_progression_states: ['user_id'],
  mazer_ai_progression_states: ['user_id', 'runner_key'],
  mazer_cycle_receipts: ['id']
});

export function renderTransactionalSql(plan) {
  requirePlain(plan, 'PRIVATE_PLAN_SHAPE');
  const schema = plan.target.schema;
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const blocks = [
    '\\set ON_ERROR_STOP on',
    'begin;',
    "set local lock_timeout = '5s';",
    "set local statement_timeout = '120s';",
    `set local ${CONTRACT.mutationGate.bypassGuc} = '${CONTRACT.mutationGate.bypassValue}';`,
    `do $atlas_executor_role$ begin if session_user <> 'postgres' then raise exception 'EXECUTOR_SESSION_ROLE_DRIFT'; end if; end $atlas_executor_role$;`,
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:${plan.direction}:${plan.packet_input_digest}', 0));`
  ];
  for (const [table, rowsName] of [
    ['mazer_profiles', 'profiles'],
    ['mazer_progression_states', 'player'],
    ['mazer_ai_progression_states', 'ai'],
    ['mazer_cycle_receipts', 'receipts']
  ]) {
    const expectedName = `atlas_expected_${rowsName}`;
    const desiredName = `atlas_desired_${rowsName}`;
    blocks.push(`create temporary table ${expectedName} on commit drop as select * from ${q(schema)}.${q(table)} with no data;`);
    blocks.push(`insert into ${expectedName} select * from pg_catalog.jsonb_populate_recordset(null::${q(schema)}.${q(table)}, ${encodedJson(plan.expected[rowsName])});`);
    blocks.push(`create temporary table ${desiredName} on commit drop as select * from ${q(schema)}.${q(table)} with no data;`);
    blocks.push(`insert into ${desiredName} select * from pg_catalog.jsonb_populate_recordset(null::${q(schema)}.${q(table)}, ${encodedJson(plan.desired[rowsName])});`);
    blocks.push(`do $atlas_precondition$ begin if exists ((select pg_catalog.to_jsonb(t) from ${q(schema)}.${q(table)} t except select pg_catalog.to_jsonb(e) from ${expectedName} e) union all (select pg_catalog.to_jsonb(e) from ${expectedName} e except select pg_catalog.to_jsonb(t) from ${q(schema)}.${q(table)} t)) then raise exception 'TARGET_PREIMAGE_DRIFT:${table}'; end if; end $atlas_precondition$;`);
    const columns = TABLE_COLUMNS[table];
    const keys = new Set(TABLE_KEYS[table]);
    const updates = columns.filter((column) => !keys.has(column)).map((column) => `${q(column)} = excluded.${q(column)}`).join(', ');
    const join = TABLE_KEYS[table].map((column) => `e.${q(column)} = d.${q(column)}`).join(' and ');
    const projection = columns.map((column) => `d.${q(column)}`).join(', ');
    const conflictGuard = TABLE_KEYS[table].map((column) => `guard.${q(column)} = live.${q(column)}`).join(' and ');
    blocks.push(`insert into ${q(schema)}.${q(table)} as live (${columns.map(q).join(', ')}) select ${projection} from ${desiredName} d left join ${expectedName} e on ${join} where e.${q(TABLE_KEYS[table][0])} is null or pg_catalog.to_jsonb(e) is distinct from pg_catalog.to_jsonb(d) on conflict (${TABLE_KEYS[table].map(q).join(', ')}) do update set ${updates} where exists (select 1 from ${expectedName} guard where ${conflictGuard} and pg_catalog.to_jsonb(live) = pg_catalog.to_jsonb(guard));`);
    blocks.push(`do $atlas_postimage$ begin if exists ((select pg_catalog.to_jsonb(t) from ${q(schema)}.${q(table)} t except select pg_catalog.to_jsonb(d) from ${desiredName} d) union all (select pg_catalog.to_jsonb(d) from ${desiredName} d except select pg_catalog.to_jsonb(t) from ${q(schema)}.${q(table)} t)) then raise exception 'TARGET_POSTIMAGE_DRIFT:${table}'; end if; end $atlas_postimage$;`);
  }
  blocks.push('commit;');
  return `${blocks.join('\n')}\n`;
}

export function renderSourceObservationSql(plan) {
  requirePlain(plan, 'PRIVATE_PLAN_SHAPE');
  const schema = plan.source_binding.schema;
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const authScope = schema === CONTRACT.legacy.schema
    ? 'true /* LEGACY_DEDICATED_AUTH_SET_EXACT */'
    : `(coalesce(u.raw_user_meta_data ->> 'app_namespace', '') = 'mazer' or exists (select 1 from ${q(schema)}.${q('mazer_profiles')} ownership_profile where ownership_profile.user_id = u.id)) /* MASTER_MAZER_NAMESPACE_OR_PROFILE_OWNERSHIP; routing scope only, never authorization */`;
  const authScopeName = schema === CONTRACT.legacy.schema ? 'LEGACY_DEDICATED_EXACT' : 'MASTER_MAZER_NAMESPACE_OR_PROFILE';
  const blocks = [
    '\\set ON_ERROR_STOP on',
    'begin transaction isolation level repeatable read;',
    "set local lock_timeout = '5s';",
    "set local statement_timeout = '120s';",
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:source-high-water:${plan.direction}:${plan.packet_input_digest}', 0));`,
    'create temporary table atlas_expected_auth (user_id uuid primary key, email_digest text not null, identity_count integer not null, email_identity_count integer not null) on commit drop;',
    `insert into atlas_expected_auth select * from pg_catalog.jsonb_to_recordset(${encodedJson(plan.source_auth)}) as x(user_id uuid, email_digest text, identity_count integer, email_identity_count integer);`,
    'create temporary table atlas_observed_auth (user_id uuid primary key, email_digest text not null, identity_count integer not null, email_identity_count integer not null) on commit drop;',
    `insert into atlas_observed_auth select u.id, pg_catalog.encode(extensions.digest(pg_catalog.convert_to(pg_catalog.lower(coalesce(u.email, '')), 'UTF8'), 'sha256'), 'hex'), c.identity_count, c.email_identity_count from auth.users u left join lateral (select pg_catalog.count(*)::integer as identity_count, (pg_catalog.count(*) filter (where i.provider = 'email'))::integer as email_identity_count from auth.identities i where i.user_id = u.id) c on true where ${authScope};`,
    `do $atlas_auth_preimage$ begin if exists ((select * from atlas_observed_auth except select * from atlas_expected_auth) union all (select * from atlas_expected_auth except select * from atlas_observed_auth)) then raise exception 'SOURCE_AUTH_HIGH_WATER_DRIFT:${authScopeName}'; end if; end $atlas_auth_preimage$;`
  ];
  for (const [table, rowsName] of [
    ['mazer_profiles', 'profiles'],
    ['mazer_progression_states', 'player'],
    ['mazer_ai_progression_states', 'ai'],
    ['mazer_cycle_receipts', 'receipts']
  ]) {
    const expectedName = `atlas_source_${rowsName}`;
    blocks.push(`create temporary table ${expectedName} on commit drop as select * from ${q(schema)}.${q(table)} with no data;`);
    blocks.push(`insert into ${expectedName} select * from pg_catalog.jsonb_populate_recordset(null::${q(schema)}.${q(table)}, ${encodedJson(plan.source[rowsName])});`);
    blocks.push(`do $atlas_source_preimage$ begin if exists ((select pg_catalog.to_jsonb(t) from ${q(schema)}.${q(table)} t except select pg_catalog.to_jsonb(e) from ${expectedName} e) union all (select pg_catalog.to_jsonb(e) from ${expectedName} e except select pg_catalog.to_jsonb(t) from ${q(schema)}.${q(table)} t)) then raise exception 'SOURCE_HIGH_WATER_DRIFT:${table}'; end if; end $atlas_source_preimage$;`);
  }
  blocks.push(`select pg_catalog.jsonb_build_object('result', 'PASS_SOURCE_HIGH_WATER', 'source_high_water_digest', '${plan.source_high_water_digest}', 'observed_at', pg_catalog.clock_timestamp())::text;`);
  blocks.push('commit;');
  return `${blocks.join('\n')}\n`;
}

function signupAdmissionStateSelect() {
  const fenceFunction = `${CONTRACT.master.schema}.${CONTRACT.signupFence.functionName}()`;
  const claimFunction = `${CONTRACT.master.schema}.${CONTRACT.signupFence.claimFunction}`;
  const fenceBody = `${encodedJson(SIGNUP_FENCE_BODY)} #>> '{}'`;
  return `with claim_function as (select p.oid, p.prosecdef, p.provolatile, p.proconfig, l.lanname, pg_catalog.pg_get_userbyid(p.proowner) as owner_name from pg_catalog.pg_proc p join pg_catalog.pg_language l on l.oid = p.prolang where p.oid = pg_catalog.to_regprocedure('${claimFunction}')), claim_trigger as (select t.oid from pg_catalog.pg_trigger t where t.tgrelid = pg_catalog.to_regclass('auth.users') and t.tgname = '${CONTRACT.signupFence.claimTrigger}' and not t.tgisinternal and t.tgenabled = 'O' and t.tgtype::integer = 5 and t.tgfoid = pg_catalog.to_regprocedure('${claimFunction}')), fence_function as (select p.oid, p.prosecdef, p.provolatile, p.proconfig, p.prosrc, l.lanname, pg_catalog.pg_get_userbyid(p.proowner) as owner_name from pg_catalog.pg_proc p join pg_catalog.pg_language l on l.oid = p.prolang where p.oid = pg_catalog.to_regprocedure('${fenceFunction}')), fence_trigger as (select t.oid from pg_catalog.pg_trigger t where t.tgrelid = pg_catalog.to_regclass('auth.users') and t.tgname = '${CONTRACT.signupFence.triggerName}' and not t.tgisinternal), facts as (select (select pg_catalog.count(*) = 1 and pg_catalog.bool_and(prosecdef and provolatile = 'v' and proconfig = array['search_path=""']::text[] and lanname = 'plpgsql' and owner_name = 'postgres') from claim_function) and (select pg_catalog.count(*) = 1 from claim_trigger) as claim_path_exact, (select pg_catalog.count(*) = 0 from fence_function) and (select pg_catalog.count(*) = 0 from fence_trigger) as fence_absent, (select pg_catalog.count(*) = 1 and pg_catalog.bool_and(not prosecdef and provolatile = 'v' and proconfig = array['search_path=""']::text[] and prosrc = ${fenceBody} and lanname = 'plpgsql' and owner_name = 'postgres') from fence_function) and (select pg_catalog.count(*) = 1 and pg_catalog.bool_and(tgenabled = 'O' and tgtype::integer = 7 and tgfoid = pg_catalog.to_regprocedure('${fenceFunction}')) from pg_catalog.pg_trigger where tgrelid = pg_catalog.to_regclass('auth.users') and tgname = '${CONTRACT.signupFence.triggerName}' and not tgisinternal) as fence_exact) select pg_catalog.jsonb_build_object('schema', 'atlas.supabase.mazer-master-signup-admission-fence-observation.v1', 'result', case when not claim_path_exact then 'HOLD_MAZER_SIGNUP_CLAIM_PATH_DRIFT' when fence_absent then 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT' when fence_exact then 'PASS_SIGNUP_ADMISSION_FENCED' else 'HOLD_SIGNUP_ADMISSION_STATE_AMBIGUOUS' end, 'state', case when fence_absent then 'ABSENT' when fence_exact then 'FENCED' else 'AMBIGUOUS' end, 'claim_path_verified', claim_path_exact, 'observed_at', pg_catalog.clock_timestamp()) from facts`;
}

export function renderSignupAdmissionObservationSql() {
  return [
    '\\set ON_ERROR_STOP on',
    'begin transaction isolation level repeatable read read only;',
    "set local lock_timeout = '5s';",
    "set local statement_timeout = '30s';",
    `select observation::text from (${signupAdmissionStateSelect()}) observed(observation);`,
    'commit;'
  ].join('\n') + '\n';
}

function signupWriterCaptureSelect() {
  return `select distinct a.pid, a.backend_start, a.xact_start, a.query_start from pg_catalog.pg_locks l join pg_catalog.pg_stat_activity a on a.pid = l.pid where l.locktype = 'relation' and l.relation = pg_catalog.to_regclass('auth.users') and l.granted and l.mode in ('RowExclusiveLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock') and a.datid = (select oid from pg_catalog.pg_database where datname = pg_catalog.current_database()) and a.pid <> pg_catalog.pg_backend_pid() and a.xact_start is not null order by a.pid, a.backend_start, a.xact_start, a.query_start`;
}

function dynamicInstallBlock(tag, stateTable, absentResult, fencedResult, driftError, statements) {
  const sqlTag = `$atlas_${tag}_sql$`;
  const installs = statements.map((statement) => `execute ${sqlTag}${statement}${sqlTag};`).join(' ');
  return `do $atlas_${tag}$ declare atlas_gate_result text := (select payload ->> 'result' from ${stateTable}); begin if atlas_gate_result = '${absentResult}' then ${installs} elsif atlas_gate_result = '${fencedResult}' then null; else raise exception '${driftError}'; end if; end $atlas_${tag}$;`;
}

export function renderSignupAdmissionFenceSql() {
  const qualifiedFunction = `${q(CONTRACT.master.schema)}.${q(CONTRACT.signupFence.functionName)}()`;
  const capturedWriters = signupWriterCaptureSelect();
  const installStatements = [
    `create function ${qualifiedFunction} returns trigger language plpgsql volatile security invoker set search_path = '' as $atlas_signup_fence$${SIGNUP_FENCE_BODY}$atlas_signup_fence$;`,
    `alter function ${qualifiedFunction} owner to postgres;`,
    `revoke all on function ${qualifiedFunction} from public;`,
    `do $atlas_signup_roles$ begin if pg_catalog.to_regrole('anon') is not null then execute 'revoke all on function ${qualifiedFunction} from anon'; end if; if pg_catalog.to_regrole('authenticated') is not null then execute 'revoke all on function ${qualifiedFunction} from authenticated'; end if; if pg_catalog.to_regrole('service_role') is not null then execute 'revoke all on function ${qualifiedFunction} from service_role'; end if; end $atlas_signup_roles$;`,
    `comment on function ${qualifiedFunction} is 'Temporary reverse-cutover admission fence. Rejects only explicit Mazer signups; non-Mazer Auth users pass through.';`,
    `create trigger ${q(CONTRACT.signupFence.triggerName)} before insert on auth.users for each row execute function ${qualifiedFunction};`
  ];
  return [
    '\\set ON_ERROR_STOP on',
    'begin;',
    "set local lock_timeout = '120s';",
    "set local statement_timeout = '150s';",
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:mazer-signup-admission-fence:${CONTRACT.master.schema}', 0));`,
    'create temporary table atlas_signup_preimage (payload jsonb not null) on commit drop;',
    `insert into atlas_signup_preimage (payload) ${signupAdmissionStateSelect()};`,
    `do $atlas_signup_preimage$ begin if (select payload ->> 'result' from atlas_signup_preimage) not in ('PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT','PASS_SIGNUP_ADMISSION_FENCED') then raise exception 'SIGNUP_ADMISSION_PREIMAGE_DRIFT'; end if; end $atlas_signup_preimage$;`,
    `create temporary table atlas_admitted_signup_writers on commit drop as ${capturedWriters};`,
    `create temporary table atlas_admitted_signup_summary (payload jsonb not null) on commit drop;`,
    `insert into atlas_admitted_signup_summary (payload) select pg_catalog.jsonb_build_object('captured_at', pg_catalog.clock_timestamp(), 'writers', coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('pid', pid, 'backend_start', backend_start, 'xact_start', xact_start, 'query_start', query_start) order by pid, backend_start, xact_start, query_start), '[]'::jsonb)) from atlas_admitted_signup_writers;`,
    'lock table auth.users in share row exclusive mode;',
    'select pg_catalog.pg_stat_clear_snapshot();',
    `do $atlas_signup_drain$ begin if exists (select 1 from atlas_admitted_signup_writers w join pg_catalog.pg_stat_activity a on a.pid = w.pid and a.backend_start = w.backend_start and a.xact_start = w.xact_start and a.query_start = w.query_start) then raise exception 'ADMITTED_SIGNUP_WRITER_NOT_DRAINED'; end if; if exists (${capturedWriters}) then raise exception 'AUTH_USERS_WRITER_BARRIER_INCOMPLETE'; end if; end $atlas_signup_drain$;`,
    dynamicInstallBlock('signup_admission_reconcile', 'atlas_signup_preimage', 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT', 'PASS_SIGNUP_ADMISSION_FENCED', 'SIGNUP_ADMISSION_PREIMAGE_DRIFT', installStatements),
    'create temporary table atlas_signup_postimage (payload jsonb not null) on commit drop;',
    `insert into atlas_signup_postimage (payload) ${signupAdmissionStateSelect()};`,
    `do $atlas_signup_postimage$ begin if (select payload ->> 'result' from atlas_signup_postimage) is distinct from 'PASS_SIGNUP_ADMISSION_FENCED' then raise exception 'SIGNUP_ADMISSION_POSTIMAGE_DRIFT'; end if; end $atlas_signup_postimage$;`,
    `select pg_catalog.jsonb_build_object('schema', 'atlas.supabase.mazer-master-signup-admission-fence-receipt.v1', 'result', 'PASS_SIGNUP_ADMISSION_FENCED', 'state', 'FENCED', 'claim_path_verified', true, 'install_disposition', case when (select payload ->> 'result' from atlas_signup_preimage) = 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT' then 'INSTALLED_FROM_ABSENT' else 'RECONCILED_EXACT_FENCED' end, 'captured_at', payload ->> 'captured_at', 'writer_count', pg_catalog.jsonb_array_length(payload -> 'writers'), 'writer_set_digest', pg_catalog.encode(extensions.digest(pg_catalog.convert_to((payload -> 'writers')::text, 'UTF8'), 'sha256'), 'hex'), 'barrier_at', pg_catalog.clock_timestamp())::text from atlas_admitted_signup_summary;`,
    'commit;'
  ].join('\n') + '\n';
}

export function renderSignupAdmissionRestoreSql() {
  const qualifiedFunction = `${q(CONTRACT.master.schema)}.${q(CONTRACT.signupFence.functionName)}()`;
  return [
    '\\set ON_ERROR_STOP on',
    'begin;',
    "set local lock_timeout = '120s';",
    "set local statement_timeout = '150s';",
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:mazer-signup-admission-fence:${CONTRACT.master.schema}', 0));`,
    'lock table auth.users in share row exclusive mode;',
    'create temporary table atlas_signup_current (payload jsonb not null) on commit drop;',
    `insert into atlas_signup_current (payload) ${signupAdmissionStateSelect()};`,
    `do $atlas_signup_restore_precondition$ begin if (select payload ->> 'result' from atlas_signup_current) not in ('PASS_SIGNUP_ADMISSION_FENCED','PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT') then raise exception 'SIGNUP_ADMISSION_RESTORE_STATE_AMBIGUOUS'; end if; end $atlas_signup_restore_precondition$;`,
    `drop trigger if exists ${q(CONTRACT.signupFence.triggerName)} on auth.users;`,
    `drop function if exists ${qualifiedFunction};`,
    'commit;',
    `select pg_catalog.jsonb_build_object('schema', 'atlas.supabase.mazer-master-signup-admission-fence-receipt.v1', 'result', case when observation ->> 'result' = 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT' then 'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED' else 'HOLD_SIGNUP_ADMISSION_RESTORE_POSTIMAGE' end, 'state', observation ->> 'state', 'claim_path_verified', (observation ->> 'claim_path_verified')::boolean, 'restored_at', pg_catalog.clock_timestamp())::text from (${signupAdmissionStateSelect()}) observed(observation);`
  ].join('\n') + '\n';
}

export function renderFenceSql(schema, journaledPreimage) {
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const expectedPreimage = normalizeAclPreimage(journaledPreimage, schema);
  const expectedFencedPostimage = fencedAclPostimage(expectedPreimage);
  const qualified = (name) => `${q(schema)}.${q(name)}`;
  return [
    '\\set ON_ERROR_STOP on',
    'begin;',
    "set local lock_timeout = '5s';",
    "set local statement_timeout = '30s';",
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:mazer-writer-fence:${schema}', 0));`,
    'create temporary table atlas_acl_preimage (payload jsonb not null) on commit drop;',
    `insert into atlas_acl_preimage (payload) ${aclObservationSelect(schema)};`,
    `do $atlas_acl_binding$ begin if (select payload - 'observed_at' from atlas_acl_preimage) is distinct from ${encodedJson(expectedPreimage)} then raise exception 'FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT'; end if; end $atlas_acl_binding$;`,
    ...CONTRACT.tables.map((table) => `revoke insert, update, delete on table ${qualified(table)} from authenticated, anon, public;`),
    ...CONTRACT.mutatingRpcs.map((rpc) => `revoke execute on function ${q(schema)}.${rpc} from authenticated, anon, public;`),
    'create temporary table atlas_acl_postimage (payload jsonb not null) on commit drop;',
    `insert into atlas_acl_postimage (payload) ${aclObservationSelect(schema)};`,
    `do $atlas_revoke$ begin if (select payload - 'observed_at' from atlas_acl_postimage) is distinct from ${encodedJson(expectedFencedPostimage)} then raise exception 'PARTIAL_WRITER_REVOKE'; end if; end $atlas_revoke$;`,
    'commit;',
    `select pg_catalog.jsonb_build_object('result', 'PASS_WRITER_REVOKE_COMMITTED', 'schema', '${schema}', 'acl_preimage_digest', '${aclDigest(expectedPreimage)}', 'revoked_at', pg_catalog.clock_timestamp())::text;`
  ].join('\n') + '\n';
}

function activeWriterSelect(schema) {
  const relations = CONTRACT.tables.map((table) => `pg_catalog.to_regclass('${schema}.${table}')`).join(',');
  return `select distinct a.pid, a.backend_start, a.xact_start, a.query_start from pg_catalog.pg_locks l join pg_catalog.pg_stat_activity a on a.pid = l.pid where l.locktype = 'relation' and l.relation in (${relations}) and l.granted and l.mode in ('RowExclusiveLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock') and a.datid = (select oid from pg_catalog.pg_database where datname = pg_catalog.current_database()) and a.pid <> pg_catalog.pg_backend_pid() and a.xact_start is not null and a.state in ('active','idle in transaction','idle in transaction (aborted)') order by a.pid, a.backend_start, a.xact_start, a.query_start`;
}

export function renderWriterCaptureSql(schema, journaledPreimage) {
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const expectedFencedPostimage = fencedAclPostimage(normalizeAclPreimage(journaledPreimage, schema));
  return [
    '\\set ON_ERROR_STOP on',
    'begin transaction isolation level read committed;',
    "set local lock_timeout = '5s';",
    "set local statement_timeout = '30s';",
    'create temporary table atlas_capture_acl (payload jsonb not null) on commit drop;',
    `insert into atlas_capture_acl (payload) ${aclObservationSelect(schema)};`,
    `do $atlas_capture_acl$ begin if (select payload - 'observed_at' from atlas_capture_acl) is distinct from ${encodedJson(expectedFencedPostimage)} then raise exception 'WRITER_CAPTURE_ACL_OR_CATALOG_DRIFT'; end if; end $atlas_capture_acl$;`,
    `with writer_rows as (${activeWriterSelect(schema)}) select pg_catalog.jsonb_build_object('result', 'PASS_WRITER_SET_CAPTURE', 'schema', '${schema}', 'captured_at', pg_catalog.clock_timestamp(), 'fenced_acl', ${encodedJson(expectedFencedPostimage)}, 'writers', coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('pid', pid, 'backend_start', backend_start, 'xact_start', xact_start, 'query_start', query_start) order by pid, backend_start, xact_start, query_start), '[]'::jsonb))::text from writer_rows;`,
    'commit;'
  ].join('\n') + '\n';
}

function normalizeWriterIdentity(raw) {
  const writer = requirePlain(structuredClone(raw), 'WRITER_IDENTITY_SHAPE');
  if (!Number.isInteger(writer.pid) || writer.pid <= 0 || writer.pid > 2147483647) hold('WRITER_IDENTITY_PID');
  const normalized = { pid: writer.pid };
  for (const key of ['backend_start', 'xact_start', 'query_start']) {
    const value = requireString(writer[key], 'WRITER_IDENTITY_TIMESTAMP');
    if (Number.isNaN(Date.parse(value))) hold('WRITER_IDENTITY_TIMESTAMP');
    normalized[key] = value;
  }
  if (Object.keys(writer).sort().join(',') !== 'backend_start,pid,query_start,xact_start') hold('WRITER_IDENTITY_DISCLOSURE');
  return normalized;
}

function normalizeWriterCapture(rawCapture, schema) {
  const capture = requirePlain(structuredClone(rawCapture), 'WRITER_CAPTURE_SHAPE');
  if (capture.result !== 'PASS_WRITER_SET_CAPTURE' || capture.schema !== schema) hold('WRITER_CAPTURE_BINDING');
  const capturedAt = requireString(capture.captured_at, 'WRITER_CAPTURE_TIMESTAMP');
  if (Number.isNaN(Date.parse(capturedAt))) hold('WRITER_CAPTURE_TIMESTAMP');
  const fencedAcl = normalizeAclPreimage(capture.fenced_acl, schema);
  const writers = requireArray(capture.writers, 'WRITER_CAPTURE_SHAPE').map(normalizeWriterIdentity)
    .sort((left, right) => canonicalJson(left).localeCompare(canonicalJson(right)));
  if (new Set(writers.map(canonicalJson)).size !== writers.length) hold('WRITER_CAPTURE_DUPLICATE');
  if (Object.keys(capture).sort().join(',') !== 'captured_at,fenced_acl,result,schema,writers') hold('WRITER_CAPTURE_DISCLOSURE');
  return { capturedAt, fencedAcl, writers };
}

function capturedWriterActiveCountSql(writers) {
  if (writers.length === 0) return '0';
  const rows = writers.map((writer) => `(${writer.pid}, ${encodedJson(writer.backend_start)} #>> '{}', ${encodedJson(writer.xact_start)} #>> '{}', ${encodedJson(writer.query_start)} #>> '{}')`).join(',');
  return `(select pg_catalog.count(*)::integer from (values ${rows}) w(pid, backend_start, xact_start, query_start) join pg_catalog.pg_stat_activity a on a.pid = w.pid and a.backend_start = w.backend_start::timestamp with time zone and a.xact_start = w.xact_start::timestamp with time zone and a.query_start = w.query_start::timestamp with time zone)`;
}

function capturedWriterStillActiveSql(writers) {
  return `${capturedWriterActiveCountSql(writers)} > 0`;
}

export function renderWriterDrainSql(schema, writers, writerSetDigest) {
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  requireDigest(writerSetDigest, 'WRITER_SET_DIGEST');
  const normalized = requireArray(writers, 'WRITER_CAPTURE_SHAPE').map(normalizeWriterIdentity);
  const activeCount = capturedWriterActiveCountSql(normalized);
  return [
    '\\set ON_ERROR_STOP on',
    'begin transaction isolation level read committed read only;',
    "set local statement_timeout = '30s';",
    `-- The host repeats this exact identity observation. Its 120-second bound terminates as CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED and leaves ACLs revoked.`,
    `select pg_catalog.jsonb_build_object('result', case when ${activeCount} > 0 then 'WAIT_CAPTURED_WRITERS' else 'PASS_CAPTURED_WRITERS_DRAINED' end, 'schema', '${schema}', 'writer_count', ${normalized.length}, 'remaining_writer_count', ${activeCount}, 'writer_set_digest', '${writerSetDigest}', 'observed_at', pg_catalog.clock_timestamp())::text;`,
    'commit;'
  ].join('\n') + '\n';
}

function mutationGateDigest(schema) {
  return sha256({
    schema,
    function_name: CONTRACT.mutationGate.functionName,
    trigger_name: CONTRACT.mutationGate.triggerName,
    tables: [...CONTRACT.tables].sort(),
    body: MUTATION_GATE_BODY,
    bypass: {
      session_user: 'postgres',
      guc: CONTRACT.mutationGate.bypassGuc,
      value: CONTRACT.mutationGate.bypassValue
    }
  });
}

function mutationGateStateSelect(schema) {
  const signature = `${schema}.${CONTRACT.mutationGate.functionName}()`;
  const body = `${encodedJson(MUTATION_GATE_BODY)} #>> '{}'`;
  const triggerAbsent = CONTRACT.tables.map((table) => `(select pg_catalog.count(*) = 0 from pg_catalog.pg_trigger t where t.tgrelid = pg_catalog.to_regclass('${schema}.${table}') and t.tgname = '${CONTRACT.mutationGate.triggerName}' and not t.tgisinternal)`).join(' and ');
  const triggerExact = CONTRACT.tables.map((table) => `(select pg_catalog.count(*) = 1 and pg_catalog.bool_and(t.tgenabled = 'O' and t.tgtype::integer = 31 and t.tgfoid = pg_catalog.to_regprocedure('${signature}')) from pg_catalog.pg_trigger t where t.tgrelid = pg_catalog.to_regclass('${schema}.${table}') and t.tgname = '${CONTRACT.mutationGate.triggerName}' and not t.tgisinternal)`).join(' and ');
  return `with gate_function as (select p.oid, p.prosecdef, p.provolatile, p.proconfig, p.prosrc, l.lanname, pg_catalog.pg_get_userbyid(p.proowner) as owner_name from pg_catalog.pg_proc p join pg_catalog.pg_language l on l.oid = p.prolang where p.oid = pg_catalog.to_regprocedure('${signature}')), facts as (select ((select pg_catalog.count(*) = 0 from gate_function) and ${triggerAbsent}) as gate_absent, ((select pg_catalog.count(*) = 1 and pg_catalog.bool_and(not prosecdef and provolatile = 'v' and proconfig = array['search_path=""']::text[] and prosrc = ${body} and lanname = 'plpgsql' and owner_name = 'postgres') from gate_function) and ${triggerExact}) as gate_exact) select pg_catalog.jsonb_build_object('schema', '${schema}', 'result', case when gate_absent then 'PASS_MUTATION_GATE_PREIMAGE_ABSENT' when gate_exact then 'PASS_MUTATION_GATE_FENCED' else 'HOLD_MUTATION_GATE_STATE_AMBIGUOUS' end, 'state', case when gate_absent then 'ABSENT' when gate_exact then 'FENCED' else 'AMBIGUOUS' end, 'mutation_gate_digest', '${mutationGateDigest(schema)}', 'observed_at', pg_catalog.clock_timestamp()) from facts`;
}

function mutationGateInstallStatements(schema) {
  const qualifiedFunction = `${q(schema)}.${q(CONTRACT.mutationGate.functionName)}()`;
  return [
    `create function ${qualifiedFunction} returns trigger language plpgsql volatile security invoker set search_path = '' as $atlas_mutation_gate$${MUTATION_GATE_BODY}$atlas_mutation_gate$;`,
    `alter function ${qualifiedFunction} owner to postgres;`,
    `revoke all on function ${qualifiedFunction} from public;`,
    `do $atlas_mutation_gate_roles$ begin if pg_catalog.to_regrole('anon') is not null then execute 'revoke all on function ${qualifiedFunction} from anon'; end if; if pg_catalog.to_regrole('authenticated') is not null then execute 'revoke all on function ${qualifiedFunction} from authenticated'; end if; if pg_catalog.to_regrole('service_role') is not null then execute 'revoke all on function ${qualifiedFunction} from service_role'; end if; end $atlas_mutation_gate_roles$;`,
    `comment on function ${qualifiedFunction} is 'Temporary cutover mutation gate. Rejects every non-executor INSERT, UPDATE, and DELETE on exact Mazer source tables regardless of SQL or protocol form.';`,
    ...[...CONTRACT.tables].sort().map((table) => `create trigger ${q(CONTRACT.mutationGate.triggerName)} before insert or update or delete on ${q(schema)}.${q(table)} for each row execute function ${qualifiedFunction};`)
  ];
}

function mutationGateRestoreStatements(schema) {
  const qualifiedFunction = `${q(schema)}.${q(CONTRACT.mutationGate.functionName)}()`;
  return [
    ...[...CONTRACT.tables].sort().map((table) => `drop trigger if exists ${q(CONTRACT.mutationGate.triggerName)} on ${q(schema)}.${q(table)};`),
    `drop function if exists ${qualifiedFunction};`
  ];
}

export function renderLockBarrierSql(schema, journaledPreimage, writers, writerSetDigest) {
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const expectedFencedPostimage = fencedAclPostimage(normalizeAclPreimage(journaledPreimage, schema));
  const normalized = requireArray(writers, 'WRITER_CAPTURE_SHAPE').map(normalizeWriterIdentity);
  requireDigest(writerSetDigest, 'WRITER_SET_DIGEST');
  const qualified = [...CONTRACT.tables].sort().map((table) => `${q(schema)}.${q(table)}`);
  return [
    '\\set ON_ERROR_STOP on',
    'begin;',
    "set local lock_timeout = '120s';",
    "set local statement_timeout = '150s';",
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:mazer-writer-mutation-gate:${schema}', 0));`,
    `do $atlas_mutation_gate_executor$ begin if session_user <> 'postgres' then raise exception 'EXECUTOR_SESSION_ROLE_DRIFT'; end if; end $atlas_mutation_gate_executor$;`,
    'create temporary table atlas_prebarrier_acl (payload jsonb not null) on commit drop;',
    `insert into atlas_prebarrier_acl (payload) ${aclObservationSelect(schema)};`,
    `do $atlas_prebarrier_acl$ begin if (select payload - 'observed_at' from atlas_prebarrier_acl) is distinct from ${encodedJson(expectedFencedPostimage)} then raise exception 'LOCK_BARRIER_ACL_OR_CATALOG_DRIFT'; end if; if ${capturedWriterStillActiveSql(normalized)} then raise exception 'CAPTURED_WRITER_REAPPEARED'; end if; end $atlas_prebarrier_acl$;`,
    ...qualified.map((table) => `lock table ${table} in share row exclusive mode;`),
    `-- Relation-lock capture drains every transaction already mutating an exact Mazer table. The mutation-point gate below rejects delayed prepared or extended-protocol work that reaches DML only after this ordered barrier.`,
    'create temporary table atlas_mutation_gate_preimage (payload jsonb not null) on commit drop;',
    `insert into atlas_mutation_gate_preimage (payload) ${mutationGateStateSelect(schema)};`,
    `do $atlas_mutation_gate_preimage$ begin if (select payload ->> 'result' from atlas_mutation_gate_preimage) not in ('PASS_MUTATION_GATE_PREIMAGE_ABSENT','PASS_MUTATION_GATE_FENCED') then raise exception 'MUTATION_GATE_PREIMAGE_DRIFT'; end if; end $atlas_mutation_gate_preimage$;`,
    dynamicInstallBlock('mutation_gate_reconcile', 'atlas_mutation_gate_preimage', 'PASS_MUTATION_GATE_PREIMAGE_ABSENT', 'PASS_MUTATION_GATE_FENCED', 'MUTATION_GATE_PREIMAGE_DRIFT', mutationGateInstallStatements(schema)),
    'create temporary table atlas_mutation_gate_postimage (payload jsonb not null) on commit drop;',
    `insert into atlas_mutation_gate_postimage (payload) ${mutationGateStateSelect(schema)};`,
    `do $atlas_mutation_gate_postimage$ begin if (select payload ->> 'result' from atlas_mutation_gate_postimage) is distinct from 'PASS_MUTATION_GATE_FENCED' then raise exception 'MUTATION_GATE_POSTIMAGE_DRIFT'; end if; end $atlas_mutation_gate_postimage$;`,
    'create temporary table atlas_postbarrier_acl (payload jsonb not null) on commit drop;',
    `insert into atlas_postbarrier_acl (payload) ${aclObservationSelect(schema)};`,
    `do $atlas_postbarrier_acl$ begin if (select payload - 'observed_at' from atlas_postbarrier_acl) is distinct from ${encodedJson(expectedFencedPostimage)} then raise exception 'LOCK_BARRIER_POST_ACL_OR_CATALOG_DRIFT'; end if; if ${capturedWriterStillActiveSql(normalized)} then raise exception 'CAPTURED_WRITER_NOT_DRAINED'; end if; end $atlas_postbarrier_acl$;`,
    `select pg_catalog.jsonb_build_object('result', 'PASS_WRITER_LOCK_BARRIER', 'schema', '${schema}', 'writer_count', ${normalized.length}, 'writer_set_digest', '${writerSetDigest}', 'mutation_gate_state', 'FENCED', 'mutation_gate_digest', '${mutationGateDigest(schema)}', 'install_disposition', case when (select payload ->> 'result' from atlas_mutation_gate_preimage) = 'PASS_MUTATION_GATE_PREIMAGE_ABSENT' then 'INSTALLED_FROM_ABSENT' else 'RECONCILED_EXACT_FENCED' end, 'barrier_at', pg_catalog.clock_timestamp())::text;`,
    'commit;'
  ].join('\n') + '\n';
}

function aclObservationSelect(schema) {
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const tableValues = CONTRACT.tables.map((table) => `('${table}')`).join(',');
  const rpcValues = CONTRACT.mutatingRpcs.map((signature) => `('${signature}')`).join(',');
  const tableGrantJson = `coalesce((select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('grantee', case when a.grantee = 0 then 'public' else pg_catalog.pg_get_userbyid(a.grantee) end, 'privilege', a.privilege_type, 'is_grantable', a.is_grantable) order by case when a.grantee = 0 then 'public' else pg_catalog.pg_get_userbyid(a.grantee) end, a.privilege_type, a.is_grantable) from pg_catalog.aclexplode(coalesce(c.relacl, pg_catalog.acldefault('r', c.relowner))) a where (a.grantee = 0 or a.grantee in (pg_catalog.to_regrole('authenticated'), pg_catalog.to_regrole('anon'))) and a.privilege_type in ('INSERT','UPDATE','DELETE')), '[]'::jsonb)`;
  const rpcGrantJson = `coalesce((select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('grantee', case when a.grantee = 0 then 'public' else pg_catalog.pg_get_userbyid(a.grantee) end, 'is_grantable', a.is_grantable) order by case when a.grantee = 0 then 'public' else pg_catalog.pg_get_userbyid(a.grantee) end, a.is_grantable) from pg_catalog.aclexplode(coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))) a where (a.grantee = 0 or a.grantee in (pg_catalog.to_regrole('authenticated'), pg_catalog.to_regrole('anon'))) and a.privilege_type = 'EXECUTE'), '[]'::jsonb)`;
  return `with table_rows as (select v.name, c.relkind::text as relkind, c.relrowsecurity as rls_enabled, c.relforcerowsecurity as force_rls, ${tableGrantJson} as grants from (values ${tableValues}) v(name) join pg_catalog.pg_namespace n on n.nspname = '${schema}' join pg_catalog.pg_class c on c.relnamespace = n.oid and c.relname = v.name), rpc_rows as (select v.signature, p.prokind::text as kind, p.prosecdef as security_definer, p.provolatile::text as volatility, ${rpcGrantJson} as grants from (values ${rpcValues}) v(signature) join pg_catalog.pg_proc p on p.oid = pg_catalog.to_regprocedure('${schema}.' || v.signature)), observed as (select '${schema}'::text as schema, coalesce((select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('name', name, 'grants', grants) order by name) from table_rows), '[]'::jsonb) as table_acl, coalesce((select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('signature', signature, 'grants', grants) order by signature) from rpc_rows), '[]'::jsonb) as rpc_acl, pg_catalog.jsonb_build_object('tables', coalesce((select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('name', name, 'relkind', relkind, 'rls_enabled', rls_enabled, 'force_rls', force_rls) order by name) from table_rows), '[]'::jsonb), 'rpcs', coalesce((select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('signature', signature, 'kind', kind, 'security_definer', security_definer, 'volatility', volatility) order by signature) from rpc_rows), '[]'::jsonb)) as catalog) select pg_catalog.to_jsonb(observed) || pg_catalog.jsonb_build_object('observed_at', pg_catalog.clock_timestamp()) from observed`;
}

export function renderAclObservationSql(schema) {
  return [
    '\\set ON_ERROR_STOP on',
    'begin transaction isolation level repeatable read read only;',
    "set local lock_timeout = '5s';",
    "set local statement_timeout = '30s';",
    `${aclObservationSelect(schema)};`,
    'commit;'
  ].join('\n') + '\n';
}

export function renderRestoreSql(schema, capturedPreimage) {
  if (![CONTRACT.legacy.schema, CONTRACT.master.schema].includes(schema)) hold('PROJECT_OR_SCHEMA_DRIFT');
  const preimage = normalizeAclPreimage(capturedPreimage, schema);
  const roleSql = (role) => role === 'public' ? 'public' : q(role);
  const grants = [];
  for (const table of preimage.table_acl) {
    for (const role of [...CLIENT_ROLES].sort()) {
      for (const grantable of [false, true]) {
        const privileges = table.grants.filter((grant) => grant.grantee === role && grant.is_grantable === grantable).map((grant) => grant.privilege).sort();
        if (privileges.length > 0) grants.push(`grant ${privileges.join(', ')} on table ${q(schema)}.${q(table.name)} to ${roleSql(role)}${grantable ? ' with grant option' : ''};`);
      }
    }
  }
  for (const rpc of preimage.rpc_acl) {
    for (const grant of rpc.grants) grants.push(`grant execute on function ${q(schema)}.${rpc.signature} to ${roleSql(grant.grantee)}${grant.is_grantable ? ' with grant option' : ''};`);
  }
  return [
    '\\set ON_ERROR_STOP on',
    'begin;',
    "set local lock_timeout = '120s';",
    "set local statement_timeout = '150s';",
    `select pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('atlas:mazer-writer-mutation-gate:${schema}', 0));`,
    `do $atlas_mutation_gate_restore_executor$ begin if session_user <> 'postgres' then raise exception 'EXECUTOR_SESSION_ROLE_DRIFT'; end if; end $atlas_mutation_gate_restore_executor$;`,
    ...[...CONTRACT.tables].sort().map((table) => `lock table ${q(schema)}.${q(table)} in share row exclusive mode;`),
    'create temporary table atlas_mutation_gate_current (payload jsonb not null) on commit drop;',
    `insert into atlas_mutation_gate_current (payload) ${mutationGateStateSelect(schema)};`,
    `do $atlas_mutation_gate_restore_precondition$ begin if (select payload ->> 'result' from atlas_mutation_gate_current) not in ('PASS_MUTATION_GATE_FENCED','PASS_MUTATION_GATE_PREIMAGE_ABSENT') then raise exception 'MUTATION_GATE_RESTORE_STATE_AMBIGUOUS'; end if; end $atlas_mutation_gate_restore_precondition$;`,
    ...CONTRACT.tables.map((table) => `revoke insert, update, delete on table ${q(schema)}.${q(table)} from authenticated, anon, public;`),
    ...CONTRACT.mutatingRpcs.map((rpc) => `revoke execute on function ${q(schema)}.${rpc} from authenticated, anon, public;`),
    ...grants,
    ...mutationGateRestoreStatements(schema),
    'create temporary table atlas_mutation_gate_restored (payload jsonb not null) on commit drop;',
    `insert into atlas_mutation_gate_restored (payload) ${mutationGateStateSelect(schema)};`,
    `do $atlas_mutation_gate_restore_postimage$ begin if (select payload ->> 'result' from atlas_mutation_gate_restored) is distinct from 'PASS_MUTATION_GATE_PREIMAGE_ABSENT' then raise exception 'MUTATION_GATE_RESTORE_POSTIMAGE_DRIFT'; end if; end $atlas_mutation_gate_restore_postimage$;`,
    'commit;'
  ].join('\n') + '\n';
}

export function classifyCutover(rawInput) {
  const input = requirePlain(structuredClone(rawInput));
  if (input.schema !== CONTRACT.inputSchema) hold('INPUT_SCHEMA');
  if (!['forward', 'reverse'].includes(input.direction)) hold('DIRECTION');
  validateJournal(input);
  normalizeBindings(input.bindings);
  requireString(input.packet_id, 'PACKET_ID');
  const map = normalizeIdentityMap(input.identity_map, input.direction);
  const computedMapDigest = sha256(map.edges);
  if (requireDigest(input.expected_identity_map_digest, 'IDENTITY_MAP_DIGEST') !== computedMapDigest) hold('IDENTITY_MAP_DIGEST_DRIFT');
  const computedAppDigest = sha256(requirePlain(input.app_contract, 'APP_CONTRACT_SHAPE'));
  if (requireDigest(input.expected_app_contract_digest, 'APP_CONTRACT_DIGEST') !== computedAppDigest) hold('APP_CONTRACT_DIGEST_DRIFT');
  const validatedFence = validateFence(input.fence, input.direction);
  const source = normalizeSnapshot(input.source_snapshot);
  const target = normalizeSnapshot(input.target_snapshot);
  const highWaterDigest = snapshotDigest(source);
  if (requireDigest(input.expected_source_high_water_digest, 'SOURCE_HIGH_WATER_DIGEST') !== highWaterDigest) hold('SOURCE_HIGH_WATER_DRIFT');
  assertObservationConvergence(input, source);
  const classifiedSource = input.direction === 'reverse'
    ? reverseDelta(source, normalizeSnapshot(input.baseline_source_snapshot))
    : source;
  const mappedSource = mapSnapshot(classifiedSource, map.map);
  const merged = mergeSnapshots(mappedSource, target);
  const targetCounts = countSnapshot(target);
  const sourceCounts = countSnapshot(source);
  const desiredCounts = {
    profiles: merged.desired.profiles.length,
    player: merged.desired.player.length,
    ai: merged.desired.ai.length,
    receipts: merged.desired.receipts.length
  };
  const changeTotal = Object.values(merged.changes).reduce((sum, value) => sum + value, 0);
  const packetInputDigest = sha256(input);
  const primarySideName = input.direction === 'forward' ? 'legacy' : 'master';
  const primaryBinding = input.direction === 'forward' ? CONTRACT.legacy : CONTRACT.master;
  const primaryAclPreimage = validatedFence[primarySideName].acl_preimage;
  const legacyAclPreimage = validatedFence.legacy.acl_preimage;
  const plan = {
    schema: CONTRACT.privatePlanSchema,
    direction: input.direction,
    packet_id: input.packet_id,
    packet_input_digest: packetInputDigest,
    identity_map_digest: computedMapDigest,
    app_contract_digest: computedAppDigest,
    source_high_water_digest: highWaterDigest,
    source_binding: input.direction === 'forward' ? CONTRACT.legacy : CONTRACT.master,
    source_auth: structuredClone(source.auth),
    source: sanitizePlanRows(source),
    target: input.direction === 'forward' ? CONTRACT.master : CONTRACT.legacy,
    expected: sanitizePlanRows(target),
    desired: sanitizePlanRows(merged.desired),
    changes: merged.changes,
    primary_acl_preimage: primaryAclPreimage,
    legacy_acl_preimage: legacyAclPreimage,
    auth_high_water_scope: input.direction === 'forward' ? 'LEGACY_DEDICATED_EXACT' : 'MASTER_MAZER_NAMESPACE_OR_PROFILE',
    fence_sql: renderFenceSql(primaryBinding.schema, primaryAclPreimage),
    writer_capture_sql: renderWriterCaptureSql(primaryBinding.schema, primaryAclPreimage),
    acl_observation_sql: renderAclObservationSql(primaryBinding.schema),
    restore_sql: renderRestoreSql(primaryBinding.schema, primaryAclPreimage),
    legacy_fence_sql: renderFenceSql(CONTRACT.legacy.schema, legacyAclPreimage),
    legacy_writer_capture_sql: renderWriterCaptureSql(CONTRACT.legacy.schema, legacyAclPreimage),
    legacy_acl_observation_sql: renderAclObservationSql(CONTRACT.legacy.schema),
    legacy_restore_sql: renderRestoreSql(CONTRACT.legacy.schema, legacyAclPreimage),
    signup_admission_observation_sql: renderSignupAdmissionObservationSql(),
    signup_admission_fence_sql: renderSignupAdmissionFenceSql(),
    signup_admission_restore_sql: renderSignupAdmissionRestoreSql()
  };
  plan.transactional_sql = renderTransactionalSql(plan);
  plan.source_observation_sql = renderSourceObservationSql(plan);
  const privatePlanDigest = sha256(plan);
  const result = changeTotal === 0 ? 'PASS_EXACT_REPLAY_NOOP' : input.direction === 'forward' ? 'PASS_FORWARD_DELTA' : 'PASS_REVERSE_DELTA';
  const receipt = {
    schema: CONTRACT.classificationSchema,
    result,
    direction: input.direction,
    legacy_project_ref: CONTRACT.legacy.projectRef,
    legacy_schema: CONTRACT.legacy.schema,
    master_project_ref: CONTRACT.master.projectRef,
    master_schema: CONTRACT.master.schema,
    packet_input_digest: packetInputDigest,
    identity_map_digest: computedMapDigest,
    app_contract_digest: computedAppDigest,
    source_high_water_digest: highWaterDigest,
    auth_high_water_scope: plan.auth_high_water_scope,
    primary_acl_preimage_digest: aclDigest(primaryAclPreimage),
    primary_catalog_digest: catalogDigest(primaryAclPreimage),
    legacy_acl_preimage_digest: aclDigest(legacyAclPreimage),
    legacy_catalog_digest: catalogDigest(legacyAclPreimage),
    private_plan_digest: privatePlanDigest,
    fence_plan_validated: true,
    fence_complete: false,
    hook_disabled_first: input.direction === 'forward' ? null : true,
    signup_admission_fence_required: input.direction === 'reverse',
    non_mazer_signup_passthrough_required: input.direction === 'reverse',
    mutation_point_gate_required: true,
    writer_capture_basis: 'TARGET_RELATION_LOCKS_PLUS_MUTATION_POINT_GATE',
    executor_bypass_profile: 'SESSION_USER_POSTGRES_AND_TRANSACTION_LOCAL_GUC',
    zero_delta_reads: 2,
    source_counts: sourceCounts,
    target_counts: targetCounts,
    desired_counts: desiredCounts,
    changed_rows: merged.changes,
    receipt_conservation: {
      source: sourceCounts.receipts,
      target: targetCounts.receipts,
      overlap: merged.receiptOverlaps,
      final: desiredCounts.receipts,
      primary_conflicts: 0,
      client_run_conflicts: 0
    },
    monotonic_player_merge: true,
    monotonic_ai_merge: true,
    quarantined_accounts: 0,
    raw_identifiers_emitted: false,
    raw_records_emitted: false,
    pii_emitted: false,
    secrets_emitted: false,
    retries: 0
  };
  return { receipt, privatePlan: plan };
}

function normalizeObservedAcl(rawObservation, schema) {
  const observation = requirePlain(structuredClone(rawObservation), 'ACL_OBSERVATION_SHAPE');
  const observedAt = requireString(observation.observed_at, 'ACL_OBSERVATION_TIMESTAMP');
  if (Number.isNaN(Date.parse(observedAt))) hold('ACL_OBSERVATION_TIMESTAMP');
  delete observation.observed_at;
  return { observedAt, preimage: normalizeAclPreimage(observation, schema) };
}

export function classifyAclObservation(rawInput, rawObservation, side = 'primary', rawExpectedObservation = null) {
  if (!['primary', 'legacy'].includes(side)) hold('ACL_OBSERVATION_SIDE');
  const { receipt: cutoverReceipt, privatePlan } = classifyCutover(rawInput);
  const packetExpected = side === 'primary' ? privatePlan.primary_acl_preimage : privatePlan.legacy_acl_preimage;
  const { observedAt, preimage: actual } = normalizeObservedAcl(rawObservation, packetExpected.schema);
  const expected = rawExpectedObservation === null
    ? packetExpected
    : normalizeObservedAcl(rawExpectedObservation, packetExpected.schema).preimage;
  const actualAclDigest = aclDigest(actual);
  const actualCatalogDigest = catalogDigest(actual);
  const expectedAclDigest = aclDigest(expected);
  const expectedCatalogDigest = catalogDigest(expected);
  const observationBindingDigest = sha256({
    packet_input_digest: cutoverReceipt.packet_input_digest,
    side,
    observed_at: observedAt,
    actual_acl_preimage_digest: actualAclDigest,
    actual_catalog_digest: actualCatalogDigest
  });
  return {
    matched: canonicalJson(actual) === canonicalJson(expected),
    fenceSql: renderFenceSql(expected.schema, actual),
    restoreSql: renderRestoreSql(expected.schema, actual),
    receipt: {
      schema: 'atlas.supabase.mazer-master-cutover-acl-observation.v1',
      result: canonicalJson(actual) === canonicalJson(expected) ? 'PASS_ACL_PREIMAGE_MATCH' : 'HOLD_ACL_PREIMAGE_DRIFT',
      side,
      direction: cutoverReceipt.direction,
      packet_input_digest: cutoverReceipt.packet_input_digest,
      actual_acl_preimage_digest: actualAclDigest,
      expected_acl_preimage_digest: expectedAclDigest,
      actual_catalog_digest: actualCatalogDigest,
      expected_catalog_digest: expectedCatalogDigest,
      acl_observation_binding_digest: observationBindingDigest,
      observed_at: observedAt,
      raw_identifiers_emitted: false,
      raw_records_emitted: false,
      pii_emitted: false,
      secrets_emitted: false,
      retries: 0
    }
  };
}

function fencedAclPostimage(preimage) {
  return {
    ...structuredClone(preimage),
    table_acl: preimage.table_acl.map((table) => ({ ...table, grants: [] })),
    rpc_acl: preimage.rpc_acl.map((rpc) => ({ ...rpc, grants: [] }))
  };
}

export function classifyWriterCapture(rawInput, rawCapture, side = 'primary') {
  if (!['primary', 'legacy'].includes(side)) hold('WRITER_CAPTURE_SIDE');
  const { receipt: cutoverReceipt, privatePlan } = classifyCutover(rawInput);
  const journaled = side === 'primary' ? privatePlan.primary_acl_preimage : privatePlan.legacy_acl_preimage;
  const { capturedAt, fencedAcl, writers } = normalizeWriterCapture(rawCapture, journaled.schema);
  const expectedFenced = fencedAclPostimage(journaled);
  if (canonicalJson(fencedAcl) !== canonicalJson(expectedFenced)) hold('WRITER_CAPTURE_ACL_OR_CATALOG_DRIFT');
  const writerSetDigest = sha256(writers);
  const captureBindingDigest = sha256({
    packet_input_digest: cutoverReceipt.packet_input_digest,
    side,
    captured_at: capturedAt,
    writer_set_digest: writerSetDigest,
    fenced_acl_digest: aclDigest(fencedAcl),
    fenced_catalog_digest: catalogDigest(fencedAcl)
  });
  return {
    drainSql: renderWriterDrainSql(journaled.schema, writers, writerSetDigest),
    lockBarrierSql: renderLockBarrierSql(journaled.schema, journaled, writers, writerSetDigest),
    receipt: {
      schema: 'atlas.supabase.mazer-master-cutover-writer-capture.v1',
      result: 'PASS_WRITER_SET_CAPTURE_BOUND',
      side,
      direction: cutoverReceipt.direction,
      packet_input_digest: cutoverReceipt.packet_input_digest,
      captured_at: capturedAt,
      writer_count: writers.length,
      writer_set_digest: writerSetDigest,
      fenced_acl_digest: aclDigest(fencedAcl),
      fenced_catalog_digest: catalogDigest(fencedAcl),
      writer_capture_binding_digest: captureBindingDigest,
      raw_identifiers_emitted: false,
      raw_records_emitted: false,
      pii_emitted: false,
      secrets_emitted: false,
      retries: 0
    }
  };
}

export function classifyAclRecoveryObservation(rawInput, rawJournaledObservation, rawCurrentObservation, side = 'primary') {
  if (!['primary', 'legacy'].includes(side)) hold('ACL_OBSERVATION_SIDE');
  const { receipt: cutoverReceipt, privatePlan } = classifyCutover(rawInput);
  const packetExpected = side === 'primary' ? privatePlan.primary_acl_preimage : privatePlan.legacy_acl_preimage;
  const { observedAt: journaledObservedAt, preimage: journaled } = normalizeObservedAcl(rawJournaledObservation, packetExpected.schema);
  const { observedAt: currentObservedAt, preimage: current } = normalizeObservedAcl(rawCurrentObservation, packetExpected.schema);
  if (canonicalJson(journaled) !== canonicalJson(packetExpected)) hold('JOURNALED_ACL_PACKET_DRIFT');
  const fenced = fencedAclPostimage(journaled);
  const currentJson = canonicalJson(current);
  const result = currentJson === canonicalJson(journaled)
    ? 'PASS_ACL_PREIMAGE_ALREADY_PRESENT'
    : currentJson === canonicalJson(fenced)
      ? 'PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED'
      : 'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS';
  return {
    recoverable: result !== 'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS',
    restoreRequired: result === 'PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED',
    restoreSql: renderRestoreSql(journaled.schema, journaled),
    receipt: {
      schema: 'atlas.supabase.mazer-master-cutover-acl-recovery.v1',
      result,
      side,
      direction: cutoverReceipt.direction,
      packet_input_digest: cutoverReceipt.packet_input_digest,
      journaled_acl_preimage_digest: aclDigest(journaled),
      journaled_catalog_digest: catalogDigest(journaled),
      current_acl_preimage_digest: aclDigest(current),
      current_catalog_digest: catalogDigest(current),
      journaled_observed_at: journaledObservedAt,
      current_observed_at: currentObservedAt,
      raw_identifiers_emitted: false,
      raw_records_emitted: false,
      pii_emitted: false,
      secrets_emitted: false,
      retries: 0
    }
  };
}

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith('--') || value === undefined) hold('CLI_ARGUMENTS');
    result[key.slice(2)] = value;
  }
  return result;
}

function readJsonNoDuplicateKeys(file) {
  const text = fs.readFileSync(file, 'utf8');
  // JSON.parse cannot detect duplicate keys. This conservative scanner rejects
  // duplicate object keys without evaluating strings or accepting comments.
  const stack = [];
  let index = 0;
  const skip = () => { while (/\s/.test(text[index] ?? '')) index += 1; };
  const string = () => {
    if (text[index] !== '"') hold('INPUT_JSON');
    let value = '';
    index += 1;
    while (index < text.length) {
      const char = text[index++];
      if (char === '"') return value;
      if (char === '\\') {
        const escaped = text[index++];
        if (escaped === 'u') { value += JSON.parse(`"\\u${text.slice(index, index + 4)}"`); index += 4; }
        else value += JSON.parse(`"\\${escaped}"`);
      } else value += char;
    }
    hold('INPUT_JSON');
  };
  // Duplicate detection is done with a reviver-independent token walk; JSON.parse
  // remains the authoritative syntax parser afterward.
  while (index < text.length) {
    skip();
    if (text[index] === '{') { stack.push({ kind: 'object', keys: new Set(), expectingKey: true }); index += 1; continue; }
    if (text[index] === '[') { stack.push({ kind: 'array' }); index += 1; continue; }
    if (text[index] === '}' || text[index] === ']') { stack.pop(); index += 1; continue; }
    if (text[index] === '"') {
      const start = index;
      const value = string();
      skip();
      const top = stack.at(-1);
      if (top?.kind === 'object' && text[index] === ':') {
        if (top.keys.has(value)) hold('DUPLICATE_JSON_KEY');
        top.keys.add(value);
      }
      if (index === start) hold('INPUT_JSON');
      continue;
    }
    index += 1;
  }
  try { return JSON.parse(text); } catch { hold('INPUT_JSON'); }
}

function writePrivate(file, bytes) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  fs.writeFileSync(file, bytes, { encoding: 'utf8', mode: 0o600, flag: 'wx' });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args['verify-writer-capture']) {
    if (!args.input || !args['writer-side'] || !args['private-writer-drain-sql'] || !args['private-lock-barrier-sql']) hold('CLI_ARGUMENTS');
    const classified = classifyWriterCapture(
      readJsonNoDuplicateKeys(path.resolve(args.input)),
      readJsonNoDuplicateKeys(path.resolve(args['verify-writer-capture'])),
      args['writer-side']
    );
    writePrivate(path.resolve(args['private-writer-drain-sql']), classified.drainSql);
    writePrivate(path.resolve(args['private-lock-barrier-sql']), classified.lockBarrierSql);
    process.stdout.write(`${canonicalJson(classified.receipt)}\n`);
    return;
  }
  if (args['classify-acl-recovery']) {
    if (!args.input || !args['acl-side'] || !args['journaled-acl-observation']) hold('CLI_ARGUMENTS');
    const classified = classifyAclRecoveryObservation(
      readJsonNoDuplicateKeys(path.resolve(args.input)),
      readJsonNoDuplicateKeys(path.resolve(args['journaled-acl-observation'])),
      readJsonNoDuplicateKeys(path.resolve(args['classify-acl-recovery'])),
      args['acl-side']
    );
    if (args['private-observed-restore-sql']) writePrivate(path.resolve(args['private-observed-restore-sql']), classified.restoreSql);
    process.stdout.write(`${canonicalJson(classified.receipt)}\n`);
    if (!classified.recoverable) process.exitCode = 2;
    return;
  }
  if (args['verify-acl-observation']) {
    if (!args.input || !args['acl-side']) hold('CLI_ARGUMENTS');
    const classified = classifyAclObservation(
      readJsonNoDuplicateKeys(path.resolve(args.input)),
      readJsonNoDuplicateKeys(path.resolve(args['verify-acl-observation'])),
      args['acl-side'],
      args['expected-acl-observation'] ? readJsonNoDuplicateKeys(path.resolve(args['expected-acl-observation'])) : null
    );
    if (args['private-observed-fence-sql']) writePrivate(path.resolve(args['private-observed-fence-sql']), classified.fenceSql);
    if (args['private-observed-restore-sql']) writePrivate(path.resolve(args['private-observed-restore-sql']), classified.restoreSql);
    process.stdout.write(`${canonicalJson(classified.receipt)}\n`);
    if (!classified.matched) process.exitCode = 2;
    return;
  }
  if (!args.input || !args['private-plan'] || !args['private-sql'] || !args['private-source-observation-sql'] || !args['private-fence-sql'] || !args['private-writer-capture-sql'] || !args['private-acl-observation-sql'] || !args['private-restore-sql'] || !args['private-legacy-fence-sql'] || !args['private-legacy-writer-capture-sql'] || !args['private-legacy-acl-observation-sql'] || !args['private-legacy-restore-sql'] || !args['private-signup-admission-observation-sql'] || !args['private-signup-admission-fence-sql'] || !args['private-signup-admission-restore-sql']) hold('CLI_ARGUMENTS');
  const { receipt, privatePlan } = classifyCutover(readJsonNoDuplicateKeys(path.resolve(args.input)));
  writePrivate(path.resolve(args['private-plan']), `${canonicalJson(privatePlan)}\n`);
  writePrivate(path.resolve(args['private-sql']), privatePlan.transactional_sql);
  writePrivate(path.resolve(args['private-source-observation-sql']), privatePlan.source_observation_sql);
  writePrivate(path.resolve(args['private-fence-sql']), privatePlan.fence_sql);
  writePrivate(path.resolve(args['private-writer-capture-sql']), privatePlan.writer_capture_sql);
  writePrivate(path.resolve(args['private-acl-observation-sql']), privatePlan.acl_observation_sql);
  writePrivate(path.resolve(args['private-restore-sql']), privatePlan.restore_sql);
  writePrivate(path.resolve(args['private-legacy-fence-sql']), privatePlan.legacy_fence_sql);
  writePrivate(path.resolve(args['private-legacy-writer-capture-sql']), privatePlan.legacy_writer_capture_sql);
  writePrivate(path.resolve(args['private-legacy-acl-observation-sql']), privatePlan.legacy_acl_observation_sql);
  writePrivate(path.resolve(args['private-legacy-restore-sql']), privatePlan.legacy_restore_sql);
  writePrivate(path.resolve(args['private-signup-admission-observation-sql']), privatePlan.signup_admission_observation_sql);
  writePrivate(path.resolve(args['private-signup-admission-fence-sql']), privatePlan.signup_admission_fence_sql);
  writePrivate(path.resolve(args['private-signup-admission-restore-sql']), privatePlan.signup_admission_restore_sql);
  process.stdout.write(`${canonicalJson(receipt)}\n`);
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  main().catch((error) => {
    const code = error instanceof CutoverHold ? error.code : 'CLASSIFIER_INTERNAL_HOLD';
    process.stdout.write(`${canonicalJson({
      schema: CONTRACT.classificationSchema,
      result: 'HOLD',
      category: code,
      raw_identifiers_emitted: false,
      raw_records_emitted: false,
      pii_emitted: false,
      secrets_emitted: false,
      retries: 0
    })}\n`);
    process.exitCode = 2;
  });
}
