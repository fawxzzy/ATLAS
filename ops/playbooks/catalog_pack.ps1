[CmdletBinding()]
param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\playbooks\catalog_pack.py")
)

if ($DryRun) {
  $pythonArgs += "--dry-run"
}

& python @pythonArgs
exit $LASTEXITCODE
