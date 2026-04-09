[CmdletBinding()]
param(
  [string]$ArchiveDir,
  [string]$SourceName,
  [string]$Slug,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\knowledge\evaluate_archive.py")
)

if ($ArchiveDir) {
  $pythonArgs += @("--archive-dir", $ArchiveDir)
}
if ($SourceName) {
  $pythonArgs += @("--source-name", $SourceName)
}
if ($Slug) {
  $pythonArgs += @("--slug", $Slug)
}
if ($DryRun) {
  $pythonArgs += "--dry-run"
}

& python @pythonArgs
exit $LASTEXITCODE
