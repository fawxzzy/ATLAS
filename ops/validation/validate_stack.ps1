[CmdletBinding()]
param(
  [string]$StackFile,
  [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $StackFile) {
  $StackFile = Join-Path $atlasRoot "stack.yaml"
}

$pythonArgs = @(
  (Join-Path $atlasRoot "ops\validation\validate_stack.py"),
  "--stack-file",
  $StackFile
)

if ($OutputDir) {
  $pythonArgs += @("--output-dir", $OutputDir)
}

& python @pythonArgs
exit $LASTEXITCODE
