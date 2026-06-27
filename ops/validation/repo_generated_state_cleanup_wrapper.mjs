#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';

const rawArgs = process.argv.slice(2);

function takeOption(flag) {
  const index = rawArgs.indexOf(flag);
  if (index < 0) {
    return null;
  }
  if (index + 1 >= rawArgs.length) {
    throw new Error(`Missing value for ${flag}`);
  }
  return rawArgs[index + 1];
}

function collectOption(flag) {
  const values = [];
  for (let index = 0; index < rawArgs.length; index += 1) {
    if (rawArgs[index] === flag) {
      if (index + 1 >= rawArgs.length) {
        throw new Error(`Missing value for ${flag}`);
      }
      values.push(rawArgs[index + 1]);
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

async function main() {
  const repoRoot = process.cwd();
  const reportArg = takeOption('--report-path');
  if (!reportArg) {
    throw new Error('Missing required --report-path');
  }
  const reportPath = path.resolve(repoRoot, reportArg);
  const runCommand = takeOption('--run');
  const deletePaths = collectOption('--delete').map((item) => String(item).trim()).filter(Boolean);
  const retainSpecs = collectOption('--retain').map(parseRetainSpec).filter(Boolean);

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
    const result = spawnSync(runCommand, {
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

  for (const relativePath of deletePaths) {
    const absolutePath = path.resolve(repoRoot, relativePath);
    if (!(await exists(absolutePath))) {
      continue;
    }
    await removePath(absolutePath);
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
