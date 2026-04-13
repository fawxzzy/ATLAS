[CmdletBinding()]
param(
  [string]$StackFile,
  [string]$OutputDir,
  [string]$BaselinePath,
  [switch]$WriteBaseline,
  [switch]$Ratchet
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
if ($BaselinePath) {
  $pythonArgs += @("--baseline-path", $BaselinePath)
}
if ($WriteBaseline) {
  $pythonArgs += "--write-baseline"
}
if ($Ratchet) {
  $pythonArgs += "--ratchet"
}

& python @pythonArgs
exit $LASTEXITCODE
