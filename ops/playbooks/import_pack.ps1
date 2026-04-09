[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,
  [Parameter(Mandatory = $true)]
  [string]$SourceName,
  [string]$Slug,
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\playbooks\import_pack.py"),
  "--input-path",
  $InputPath,
  "--source-name",
  $SourceName
)

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
