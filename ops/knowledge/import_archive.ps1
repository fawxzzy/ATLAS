[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,
  [Parameter(Mandatory = $true)]
  [string]$SourceName,
  [string]$Slug,
  [ValidateSet("private", "mixed", "shareable")]
  [string]$PrivacyFlag = "private",
  [string]$ProvenanceNote,
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\knowledge\import_archive.py"),
  "--input-path",
  $InputPath,
  "--source-name",
  $SourceName,
  "--privacy-flag",
  $PrivacyFlag
)

if ($Slug) {
  $pythonArgs += @("--slug", $Slug)
}
if ($ProvenanceNote) {
  $pythonArgs += @("--provenance-note", $ProvenanceNote)
}
if ($DryRun) {
  $pythonArgs += "--dry-run"
}
if ($Force) {
  $pythonArgs += "--force"
}

& python @pythonArgs
exit $LASTEXITCODE
