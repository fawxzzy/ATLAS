[CmdletBinding()]
param(
  [string]$PackDir,
  [string]$SourceName,
  [string]$Slug,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\playbooks\evaluate_pack.py")
)

if ($PackDir) {
  $pythonArgs += @("--pack-dir", $PackDir)
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
