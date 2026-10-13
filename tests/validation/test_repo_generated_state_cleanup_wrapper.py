from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "ops/validation/repo_generated_state_cleanup_wrapper.mjs"


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the cleanup wrapper")
class CleanupWrapperBoundaryTests(unittest.TestCase):
    def test_delete_boundaries_and_command_order_without_deleting(self):
        # Fixtures remain in the configured temporary directory. Removal is
        # always replaced with a recording stub; no cleanup command is run.
        script = r'''
import assert from 'node:assert/strict';
import { promises as fs, symlinkSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const { main, validateDeletePath } = await import(pathToFileURL(process.argv[2]));
const area = await fs.mkdtemp(path.join(os.tmpdir(), 'atlas-cleanup-boundary-'));
const root = path.join(area, 'repo');
const outside = path.join(area, 'outside');
await fs.mkdir(root); await fs.mkdir(outside);
await fs.mkdir(path.join(root, 'cache'));
await fs.mkdir(path.join(root, 'other'));
let calls = [];
const report = path.join(area, 'report.json');
const remove = async target => calls.push(['remove', target]);
const run = () => { calls.push(['run']); return { status: 0 }; };
const invalid = ['', '.', './', '..', '../outside', 'cache/../../outside',
  'cache/../other', '/outside', '\\outside', 'C:\\outside', 'C:outside',
  '\\\\server\\share', 'cache:stream', 'cache\u0000x', '..\\outside'];
for (const value of invalid) {
  calls = [];
  await assert.rejects(main({ repoRoot: root, args: ['--report-path', report,
    '--delete', 'cache', '--delete', value, '--run', 'never'], run, remove }));
  assert.deepEqual(calls, [], `effect before rejection of ${JSON.stringify(value)}`);
}
assert.equal(await validateDeletePath(root, 'cache'), path.join(root, 'cache'));
assert.equal(await validateDeletePath(root, 'missing/child'), path.join(root, 'missing', 'child'));
await fs.symlink(outside, path.join(root, 'link'), process.platform === 'win32' ? 'junction' : 'dir');
await assert.rejects(validateDeletePath(root, 'link'));
await assert.rejects(validateDeletePath(root, 'link/missing/child'));
await fs.symlink(path.join(root, 'cache'), path.join(root, 'internal-link'),
  process.platform === 'win32' ? 'junction' : 'dir');
await assert.rejects(validateDeletePath(root, 'internal-link'));
calls = [];
await main({ repoRoot: root, args: ['--report-path', report, '--delete', 'cache',
  '--delete', 'missing/child', '--run', 'stub'], run, remove });
assert.deepEqual(calls, [['run'], ['remove', path.join(root, 'cache')]]);
assert.deepEqual(JSON.parse(await fs.readFile(report, 'utf8')).cleaned_paths, ['cache']);
// The command introduces a link for the second target. Whole-batch rechecking
// must prevent even the earlier valid target's removal.
calls = [];
await assert.rejects(main({ repoRoot: root, args: ['--report-path', report,
  '--delete', 'cache', '--delete', 'new-link', '--run', 'stub'], remove,
  run: () => {
    calls.push(['run']);
    symlinkSync(outside, path.join(root, 'new-link'), process.platform === 'win32' ? 'junction' : 'dir');
    return { status: 0 };
  },
}));
assert.deepEqual(calls, [['run']]);
console.log(JSON.stringify({ fixture: area, invalid_cases: invalid.length,
  deletion_invocations: 0, wrapped_commands: 0 }));
'''
        result = subprocess.run(
            [shutil.which("node"), "--input-type=module", "-e", script, "boundary-test", str(WRAPPER)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        proof = json.loads(result.stdout.strip())
        self.assertEqual(proof["invalid_cases"], 15)
        self.assertEqual(proof["deletion_invocations"], 0)


if __name__ == "__main__":
    unittest.main()
