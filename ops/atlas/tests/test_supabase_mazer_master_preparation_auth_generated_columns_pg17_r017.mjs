import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const pgBin = process.env.ATLAS_PG17_BIN || (process.platform === 'win32' ? 'C:\\Program Files\\PostgreSQL\\17\\bin' : '');
const executable = (name) => path.join(pgBin, process.platform === 'win32' ? `${name}.exe` : name);
if (!pgBin || !fs.existsSync(executable('initdb')) || !fs.existsSync(executable('pg_ctl')) || !fs.existsSync(executable('psql'))) {
  console.log(JSON.stringify({ result: 'SKIP_R017_AUTH_GENERATED_COLUMNS_PG17', reason: 'PG17_BIN_UNAVAILABLE', external_writes: 0 }));
  process.exit(0);
}

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-r017-auth-users-pg17-'));
const data = path.join(root, 'data');
const log = path.join(root, 'postgres.log');
const port = 56000 + (process.pid % 7000);
let started = false;
const run = (file, args, options = {}) => spawnSync(file, args, {
  encoding: 'utf8', windowsHide: true, timeout: options.timeout ?? 60_000,
  env: { ...process.env, PGHOST: '127.0.0.1', PGPORT: String(port), PGUSER: 'postgres', PGDATABASE: 'postgres' },
  maxBuffer: 4 * 1024 * 1024
});
const psql = (sql) => run(executable('psql'), ['-X', '--no-psqlrc', '--no-align', '--tuples-only', '--set', 'ON_ERROR_STOP=1', '--command', sql]);
const stderrDigest = (value) => crypto.createHash('sha256').update(value, 'utf8').digest('hex');

const schemaSql = String.raw`
create schema auth;
create table auth.users(
  instance_id uuid,id uuid primary key,aud varchar(255),"role" varchar(255),email varchar(255),encrypted_password varchar(255),
  email_confirmed_at timestamptz,invited_at timestamptz,confirmation_token varchar(255),confirmation_sent_at timestamptz,
  recovery_token varchar(255),recovery_sent_at timestamptz,email_change_token_new varchar(255),email_change varchar(255),
  email_change_sent_at timestamptz,last_sign_in_at timestamptz,raw_app_meta_data jsonb,raw_user_meta_data jsonb,
  is_super_admin boolean,created_at timestamptz,updated_at timestamptz,phone text,phone_confirmed_at timestamptz,
  phone_change text,phone_change_token varchar(255),phone_change_sent_at timestamptz,email_change_token_current varchar(255),
  email_change_confirm_status smallint,banned_until timestamptz,reauthentication_token varchar(255),
  reauthentication_sent_at timestamptz,is_sso_user boolean,deleted_at timestamptz,is_anonymous boolean,
  confirmed_at timestamptz generated always as (least(email_confirmed_at,phone_confirmed_at)) stored
);`;
const row = {
  instance_id: '00000000-0000-0000-0000-000000000000', id: '10000000-0000-0000-0000-000000000001', aud: 'authenticated', role: 'authenticated',
  email: 'fixture@example.test', encrypted_password: '$2a$10$00000000000000000000000000000000000000000000000000000',
  email_confirmed_at: '2026-08-26T00:00:00Z', invited_at: null, confirmation_token: '', confirmation_sent_at: null,
  recovery_token: '', recovery_sent_at: null, email_change_token_new: '', email_change: '', email_change_sent_at: null,
  last_sign_in_at: null, raw_app_meta_data: { provider: 'email', providers: ['email'] }, raw_user_meta_data: {},
  is_super_admin: false, created_at: '2026-08-26T00:00:00Z', updated_at: '2026-08-26T00:00:00Z', phone: null,
  phone_confirmed_at: null, phone_change: '', phone_change_token: '', phone_change_sent_at: null,
  email_change_token_current: '', email_change_confirm_status: 0, banned_until: null, reauthentication_token: '',
  reauthentication_sent_at: null, is_sso_user: false, deleted_at: null, is_anonymous: false,
  confirmed_at: '2026-08-26T00:00:00Z'
};
const literal = `'${JSON.stringify([row]).replaceAll("'", "''")}'::jsonb`;
const writable = [
  'instance_id','id','aud','role','email','encrypted_password','email_confirmed_at','invited_at','confirmation_token',
  'confirmation_sent_at','recovery_token','recovery_sent_at','email_change_token_new','email_change','email_change_sent_at',
  'last_sign_in_at','raw_app_meta_data','raw_user_meta_data','is_super_admin','created_at','updated_at','phone','phone_confirmed_at',
  'phone_change','phone_change_token','phone_change_sent_at','email_change_token_current','email_change_confirm_status','banned_until',
  'reauthentication_token','reauthentication_sent_at','is_sso_user','deleted_at','is_anonymous'
];
const ident = (value) => `"${value}"`;

try {
  const init = run(executable('initdb'), ['-D', data, '--username=postgres', '--auth=trust', '--no-locale']);
  assert.equal(init.status, 0, `INITDB_FAILED:${stderrDigest(init.stderr ?? '')}`);
  const start = run(executable('pg_ctl'), ['-D', data, '-l', log, '-o', `-F -h 127.0.0.1 -p ${port}`, '-w', 'start']);
  assert.equal(start.status, 0, `PG_START_FAILED:${stderrDigest(start.stderr ?? '')}`);
  started = true;
  const schema = psql(schemaSql);
  assert.equal(schema.status, 0, `SCHEMA_FAILED:${stderrDigest(schema.stderr ?? '')}`);

  const old = psql(`with rows as (select jsonb_array_elements(${literal}) value) insert into auth.users select (jsonb_populate_record(null::auth.users,value)).* from rows;`);
  assert.notEqual(old.status, 0, 'FULL_ROW_INSERT_UNEXPECTEDLY_PASSED');
  assert.match(old.stderr, /generated column "confirmed_at"|cannot insert a non-DEFAULT value into column "confirmed_at"/i);

  const corrected = psql(`with rows as (select jsonb_array_elements(${literal}) value),records as (select jsonb_populate_record(null::auth.users,value) r from rows) insert into auth.users(${writable.map(ident).join(',')}) select ${writable.map((name) => `(r).${ident(name)}`).join(',')} from records;`);
  assert.equal(corrected.status, 0, `CORRECTED_INSERT_FAILED:${stderrDigest(corrected.stderr ?? '')}`);
  const proof = psql("select count(*)::text||':'||bool_and(confirmed_at=email_confirmed_at)::text||':'||bool_and(confirmed_at='2026-08-26T00:00:00Z'::timestamptz)::text from auth.users;");
  assert.equal(proof.status, 0, `POSTCHECK_FAILED:${stderrDigest(proof.stderr ?? '')}`);
  assert.equal(proof.stdout.trim(), '1:true:true');

  console.log(JSON.stringify({
    result: 'PASS_R017_AUTH_USERS_GENERATED_COLUMN_PG17',
    old_full_row_exit: old.status,
    old_stderr_bytes: Buffer.byteLength(old.stderr ?? '', 'utf8'),
    old_stderr_sha256: stderrDigest(old.stderr ?? ''),
    corrected_exit: corrected.status,
    imported_rows: 1,
    confirmed_at_generated_exactly: true,
    external_writes: 0
  }));
} finally {
  if (started) run(executable('pg_ctl'), ['-D', data, '-m', 'immediate', '-w', 'stop']);
  fs.rmSync(root, { recursive: true, force: true });
}
