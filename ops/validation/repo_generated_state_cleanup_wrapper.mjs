#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const rawArgs = process.argv.slice(2);

function takeOption(flag, args = rawArgs) {
  const index = args.indexOf(flag);
  if (index < 0) {
    return null;
  }
  if (index + 1 >= args.length) {
    throw new Error(`Missing value for ${flag}`);
  }
  return args[index + 1];
}

function collectOption(flag, args = rawArgs) {
  const values = [];
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === flag) {
      if (index + 1 >= args.length) {
        throw new Error(`Missing value for ${flag}`);
      }
      values.push(args[index + 1]);
    }
  }
  return values;
}

function parseRetainSpec(spec) {
  const trimmed = String(spec || '').trim();
  if (!trimmed) {
    return null;
  }
  const separator = trimmed.indexOf('=');
  if (separator < 0) {
    return { path: trimmed, reason: 'retained_policy' };
  }
  const retainedPath = trimmed.slice(0, separator).trim();
  const reason = trimmed.slice(separator + 1).trim() || 'retained_policy';
  if (!retainedPath) {
    return null;
  }
  return { path: retainedPath, reason };
}

async function exists(targetPath) {
  try {
    await fs.stat(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function ensureDir(targetPath) {
  await fs.mkdir(targetPath, { recursive: true });
}

async function loadReport(reportPath) {
  if (!(await exists(reportPath))) {
    return null;
  }
  try {
    const payload = JSON.parse(await fs.readFile(reportPath, 'utf8'));
    return payload && typeof payload === 'object' ? payload : null;
  } catch {
    return null;
  }
}

function createEmptyReport(repoRoot) {
  return {
    contract_version: 'atlas.repo.generated-state-cleanup.report.v1',
    generated_at: new Date().toISOString(),
    repo_name: path.basename(repoRoot),
    status: 'clean',
    planned_paths: [],
    cleaned_paths: [],
    archived_paths: [],
    relocated_paths: [],
    retained_paths: [],
  };
}

function normalizeList(value) {
  return Array.isArray(value) ? value : [];
}

function mergeReport(baseReport, incomingReport) {
  if (!incomingReport || typeof incomingReport !== 'object') {
    return baseReport;
  }
  for (const key of ['planned_paths', 'cleaned_paths', 'archived_paths', 'relocated_paths', 'retained_paths']) {
    baseReport[key] = normalizeList(incomingReport[key]);
  }
  if (typeof incomingReport.status === 'string' && incomingReport.status.trim()) {
    baseReport.status = incomingReport.status.trim();
  }
  if (typeof incomingReport.repo_name === 'string' && incomingReport.repo_name.trim()) {
    baseReport.repo_name = incomingReport.repo_name.trim();
  }
  return baseReport;
}

function appendUniquePath(list, value) {
  if (!list.includes(value)) {
    list.push(value);
  }
}

async function writeReport(reportPath, report) {
  await ensureDir(path.dirname(reportPath));
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
}

async function removePath(targetPath) {
  await fs.rm(targetPath, {
    recursive: true,
    force: true,
    maxRetries: 2,
    retryDelay: 200,
  });
}

function isStrictDescendant(root, target) {
  const relative = path.relative(root, target);
  return relative !== '' && !path.isAbsolute(relative)
    && relative !== '..' && !relative.startsWith(`..${path.sep}`);
}

// Cleanup requires an admitted, stable owner boundary. These checks prevent
// path escapes; they do not lock out concurrent filesystem writers.
export async function validateDeletePath(repoRoot, relativePath) {
  const normalized = String(relativePath).trim().replaceAll('\\', '/');
  const segments = normalized.split('/');
  if (!normalized || normalized.includes('\0') || normalized.includes(':')
      || path.posix.isAbsolute(normalized) || path.win32.isAbsolute(normalized)
      || segments.includes('..')) {
    throw new Error(`Unsafe cleanup path: ${relativePath}`);
  }
  const absolutePath = path.resolve(repoRoot, normalized);
  if (!isStrictDescendant(repoRoot, absolutePath)) {
    throw new Error(`Cleanup path must stay below the repository: ${relativePath}`);
  }
  const realRoot = await fs.realpath(repoRoot);
  let ancestor = repoRoot;
  for (const segment of path.relative(repoRoot, absolutePath).split(path.sep)) {
    ancestor = path.join(ancestor, segment);
    let metadata;
    try {
      metadata = await fs.lstat(ancestor);
    } catch (error) {
      if (error.code === 'ENOENT') {
        break;
      }
      throw error;
    }
    if (metadata.isSymbolicLink()
        || !isStrictDescendant(realRoot, await fs.realpath(ancestor))) {
      throw new Error(`Cleanup path crosses a link or repository boundary: ${relativePath}`);
    }
  }
  return absolutePath;
}

export async function main({
  repoRoot = process.cwd(), args = rawArgs, run = spawnSync, remove = removePath,
} = {}) {
  const reportArg = takeOption('--report-path', args);
  if (!reportArg) {
    throw new Error('Missing required --report-path');
  }
  const reportPath = path.resolve(repoRoot, reportArg);
  const runCommand = takeOption('--run', args);
  const deletePaths = collectOption('--delete', args).map((item) => String(item).trim());
  const retainSpecs = collectOption('--retain', args).map(parseRetainSpec).filter(Boolean);

  // Validate the entire batch before the wrapped command can have any effect.
  for (const relativePath of deletePaths) {
    await validateDeletePath(repoRoot, relativePath);
  }

  let report = createEmptyReport(repoRoot);
  const planned = new Set();
  for (const relativePath of deletePaths) {
    planned.add(relativePath);
  }
  for (const retained of retainSpecs) {
    planned.add(retained.path);
  }
  report.planned_paths = [...planned];

  if (runCommand) {
    const result = run(runCommand, {
      cwd: repoRoot,
      shell: true,
      encoding: 'utf8',
    });
    if (result.stdout) {
      process.stdout.write(result.stdout);
    }
    if (result.stderr) {
      process.stderr.write(result.stderr);
    }

    report = mergeReport(report, await loadReport(reportPath));
    report.generated_at = new Date().toISOString();

    if ((result.status ?? 1) !== 0) {
      report.status = 'failed';
      report.error_code = result.status ?? 1;
      report.error_message = `Wrapped cleanup command failed: ${runCommand}`;
      await writeReport(reportPath, report);
      process.exit(result.status ?? 1);
    }
  }

  // A wrapped command may replace a directory with a link. Recheck the whole
  // batch before deleting anything, and each path immediately before removal.
  for (const relativePath of deletePaths) {
    await validateDeletePath(repoRoot, relativePath);
  }
  for (const relativePath of deletePaths) {
    const absolutePath = await validateDeletePath(repoRoot, relativePath);
    if (!(await exists(absolutePath))) {
      continue;
    }
    await remove(absolutePath);
    appendUniquePath(report.cleaned_paths, relativePath);
  }

  for (const retained of retainSpecs) {
    const absolutePath = path.resolve(repoRoot, retained.path);
    if (!(await exists(absolutePath))) {
      continue;
    }
    const retainedPaths = normalizeList(report.retained_paths);
    const existing = retainedPaths.find(
      (item) => item && typeof item === 'object' && String(item.path || '').trim() === retained.path,
    );
    if (existing) {
      existing.reason = existing.reason || retained.reason;
      existing.suppress_validation_warning = true;
    } else {
      retainedPaths.push({
        path: retained.path,
        reason: retained.reason,
        suppress_validation_warning: true,
      });
    }
    report.retained_paths = retainedPaths;
  }

  report.generated_at = new Date().toISOString();
  if (normalizeList(report.retained_paths).length > 0) {
    report.status = 'retained_policy';
  } else if (normalizeList(report.cleaned_paths).length > 0) {
    report.status = 'cleaned';
  } else if (!report.status || report.status === 'failed') {
    report.status = 'clean';
  }

  await writeReport(reportPath, report);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(async (error) => {
  const repoRoot = process.cwd();
  const reportArg = takeOption('--report-path');
  if (reportArg) {
    const reportPath = path.resolve(repoRoot, reportArg);
    const report = createEmptyReport(repoRoot);
    report.status = 'failed';
    report.error_message = error instanceof Error ? error.message : String(error);
    await writeReport(reportPath, report).catch(() => {});
  }
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
  });
}
