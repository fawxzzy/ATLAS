[CmdletBinding(DefaultParameterSetName = "Zip")]
param(
  [Parameter(ParameterSetName = "Zip", Mandatory = $true)]
  [string]$ZipPath,

  [Parameter(ParameterSetName = "Snapshot", Mandatory = $true)]
  [string]$SnapshotPath,

  [string[]]$RepoIds,
  [switch]$IncludeAllManagedRepos,
  [switch]$IncludeData,
  [switch]$IncludePackages,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$stackFile = Join-Path $atlasRoot "stack.yaml"

function Get-StackConfig {
  param([string]$StackFilePath, [string]$AtlasRootPath)
  $pythonCode = @"
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"$AtlasRootPath") / "ops" / "validation"))
import validate_stack
config = validate_stack.load_stack_config(Path(r"$StackFilePath"))
print(json.dumps(config))
"@
  $json = $pythonCode | & python -
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to parse stack.yaml."
  }
  return $json | ConvertFrom-Json
}

function Resolve-AtlasPath {
  param([string]$BaseDir, [string]$RawPath)
  if ([System.IO.Path]::IsPathRooted($RawPath)) {
    return [System.IO.Path]::GetFullPath($RawPath)
  }
  return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $RawPath))
}

function Get-RelativeUnixPath {
  param([string]$FullPath, [string]$BaseDir)
  $baseUri = [System.Uri](([System.IO.Path]::GetFullPath($BaseDir).TrimEnd('\') + '\'))
  $fileUri = [System.Uri]([System.IO.Path]::GetFullPath($FullPath))
  return ([System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($fileUri).ToString())).Replace('\', '/')
}

function Test-ExcludedPath {
  param([string]$RelativePath)
  $normalized = $RelativePath.Replace('\', '/')
  $patterns = @(
    '(^|/)\.git(/|$)',
    '(^|/)\.venv(/|$)',
    '(^|/)__pycache__(/|$)',
    '(^|/)\.pytest_cache(/|$)',
    '(^|/)\.mypy_cache(/|$)',
    '(^|/)\.ruff_cache(/|$)',
    '(^|/)\.cache(/|$)',
    '(^|/)\.turbo(/|$)',
    '(^|/)\.parcel-cache(/|$)',
    '(^|/)node_modules(/|$)',
    '(^|/)\.next(/|$)',
    '(^|/)dist(/|$)',
    '(^|/)coverage(/|$)',
    '(^|/)playwright-report(/|$)',
    '(^|/)test-results(/|$)',
    '(^|/)runtime(/|$)',
    '(^|/)tmp(/|$)',
    '(^|/)secrets(/|$)',
    '(^|/)\.vercel(/|$)',
    '(^|/)\.DS_Store$',
    '(^|/)Thumbs\.db$',
    '\.log$',
    '\.tmp$',
    '\.sqlite3?$',
    '\.db$',
    '\.db-shm$',
    '\.db-wal$',
    '(^|/)\.env$',
    '(^|/)\.env\.[^/]+$'
  )
  foreach ($pattern in $patterns) {
    if ($normalized -match $pattern) {
      return $true
    }
  }
  return $false
}

function Copy-IncludedTree {
  param(
    [string]$SourcePath,
    [string]$AtlasRootPath,
    [string]$StagingRoot,
    [System.Collections.Generic.List[object]]$ManifestItems
  )
  if (-not (Test-Path -LiteralPath $SourcePath)) {
    return
  }

  if (Test-Path -LiteralPath $SourcePath -PathType Leaf) {
    $relative = Get-RelativeUnixPath -FullPath $SourcePath -BaseDir $AtlasRootPath
    if (-not (Test-ExcludedPath -RelativePath $relative)) {
      $destination = Join-Path $StagingRoot $relative
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
      Copy-Item -LiteralPath $SourcePath -Destination $destination -Force
      $ManifestItems.Add([PSCustomObject]@{ relative_path = $relative; source = $SourcePath })
    }
    return
  }

  Get-ChildItem -LiteralPath $SourcePath -Recurse -File -Force | ForEach-Object {
    $relative = Get-RelativeUnixPath -FullPath $_.FullName -BaseDir $AtlasRootPath
    if (Test-ExcludedPath -RelativePath $relative) {
      return
    }
    $destination = Join-Path $StagingRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    $ManifestItems.Add([PSCustomObject]@{ relative_path = $relative; source = $_.FullName })
  }
}

$config = Get-StackConfig -StackFilePath $stackFile -AtlasRootPath $atlasRoot
$repoRegistry = $config.repo_registry

$selectedRepoIds = @()
if ($IncludeAllManagedRepos) {
  foreach ($property in $repoRegistry.PSObject.Properties) {
    if ($property.Value.status -eq "active" -or $property.Value.status -eq "incubating") {
      $selectedRepoIds += $property.Name
    }
  }
} elseif ($RepoIds) {
  $selectedRepoIds = $RepoIds
}

$includeRoots = New-Object System.Collections.Generic.List[string]
$includeRoots.Add((Join-Path $atlasRoot "stack.yaml"))
$includeRoots.Add((Join-Path $atlasRoot "README-STACK.md"))
$includeRoots.Add((Join-Path $atlasRoot "AGENTS.md"))
$includeRoots.Add((Join-Path $atlasRoot "docs"))
$includeRoots.Add((Join-Path $atlasRoot "ops"))
if ($IncludeData) { $includeRoots.Add((Join-Path $atlasRoot "data")) }
if ($IncludePackages) { $includeRoots.Add((Join-Path $atlasRoot "packages")) }
foreach ($repoId in $selectedRepoIds) {
  $property = $repoRegistry.PSObject.Properties[$repoId]
  if (-not $property) {
    throw "Unknown repo id: $repoId"
  }
  $includeRoots.Add((Resolve-AtlasPath -BaseDir $atlasRoot -RawPath $property.Value.path))
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stagingRoot = Join-Path $atlasRoot ("tmp\scratch\export-{0}" -f $timestamp)
if (Test-Path -LiteralPath $stagingRoot) {
  Remove-Item -LiteralPath $stagingRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

$manifestItems = New-Object System.Collections.Generic.List[object]
foreach ($rootPath in ($includeRoots | Sort-Object -Unique)) {
  Copy-IncludedTree -SourcePath $rootPath -AtlasRootPath $atlasRoot -StagingRoot $stagingRoot -ManifestItems $manifestItems
}

$manifest = [ordered]@{
  generated_at = (Get-Date).ToString("s")
  atlas_root = $atlasRoot
  mode = $PSCmdlet.ParameterSetName
  selected_repo_ids = $selectedRepoIds
  include_data = [bool]$IncludeData
  include_packages = [bool]$IncludePackages
  included_roots = ($includeRoots | Sort-Object -Unique)
  excluded_by_default = @(
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".cache", ".turbo", ".parcel-cache", "node_modules", ".next", "dist", "coverage",
    "playwright-report", "test-results", ".vercel", "*.log", "*.tmp", "*.sqlite*",
    "*.db*", ".env", ".env.*", "runtime/", "tmp/", "secrets/"
  )
  included_file_count = $manifestItems.Count
  included_files = $manifestItems
}

$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $stagingRoot "EXPORT-MANIFEST.json") -Encoding UTF8
$markdown = @(
  "# ATLAS Export Manifest",
  "",
  "- Generated: $($manifest.generated_at)",
  "- Mode: $($manifest.mode)",
  "- Selected repo ids: $(([string]::Join(', ', $selectedRepoIds)))",
  "",
  "## Included Roots",
  ""
)
foreach ($item in ($manifest.included_roots | Sort-Object)) { $markdown += "- $item" }
$markdown += ""
$markdown += "## Excluded By Default"
$markdown += ""
foreach ($item in $manifest.excluded_by_default) { $markdown += "- $item" }
$markdown += ""
$markdown += "## Included File Count"
$markdown += ""
$markdown += "- $($manifest.included_file_count)"
$markdown += ""
$markdown += "## What Is Not Included"
$markdown += ""
$markdown += "- secrets"
$markdown += "- runtime state"
$markdown += "- tmp outputs"
$markdown += "- dependency folders"
$markdown += "- build caches"
$markdown += "- logs and database files"
$markdown += "- OS junk files"
$markdown | Set-Content -LiteralPath (Join-Path $stagingRoot "EXPORT-MANIFEST.md") -Encoding UTF8

if ($PSCmdlet.ParameterSetName -eq "Zip") {
  $resolvedZip = [System.IO.Path]::GetFullPath((Join-Path $atlasRoot $ZipPath))
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $resolvedZip) | Out-Null
  if ((Test-Path -LiteralPath $resolvedZip) -and (-not $Force)) {
    throw "Zip output already exists. Use -Force to overwrite: $resolvedZip"
  }
  if (Test-Path -LiteralPath $resolvedZip) {
    Remove-Item -LiteralPath $resolvedZip -Force
  }
  [System.IO.Compression.ZipFile]::CreateFromDirectory($stagingRoot, $resolvedZip)
  Write-Host "Export zip created: $resolvedZip"
} else {
  $resolvedSnapshot = [System.IO.Path]::GetFullPath((Join-Path $atlasRoot $SnapshotPath))
  if ((Test-Path -LiteralPath $resolvedSnapshot) -and (-not $Force)) {
    throw "Snapshot directory already exists. Use -Force to overwrite: $resolvedSnapshot"
  }
  if (Test-Path -LiteralPath $resolvedSnapshot) {
    Remove-Item -LiteralPath $resolvedSnapshot -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $resolvedSnapshot | Out-Null
  Copy-Item -LiteralPath (Join-Path $stagingRoot "*") -Destination $resolvedSnapshot -Recurse -Force
  Write-Host "Snapshot directory created: $resolvedSnapshot"
}

Write-Host ("Included file count: {0}" -f $manifestItems.Count)
