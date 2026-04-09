[CmdletBinding()]
param(
  [string]$PackDir,
  [string]$SourceName,
  [string]$Slug,
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\playbooks\normalize_pack.py")
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
if ($Force) {
  $pythonArgs += "--force"
}

& python @pythonArgs
exit $LASTEXITCODE
