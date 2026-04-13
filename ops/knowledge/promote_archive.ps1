[CmdletBinding()]
param(
  [string]$ArchiveDir,
  [string]$SourceName,
  [string]$Slug,
  [ValidateSet("metadata_only", "derived_only", "full_text")]
  [string]$IndexingProfile,
  [ValidateSet("draft", "promoted")]
  [string]$PromotionStatus = "draft",
  [ValidateSet("ephemeral", "operational", "governed-audit", "regulated")]
  [string]$RetentionClass,
  [switch]$RefreshDerived,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\knowledge\promote_archive.py")
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
if ($IndexingProfile) {
  $pythonArgs += @("--indexing-profile", $IndexingProfile)
}
if ($PromotionStatus) {
  $pythonArgs += @("--promotion-status", $PromotionStatus)
}
if ($RetentionClass) {
  $pythonArgs += @("--retention-class", $RetentionClass)
}
if ($RefreshDerived) {
  $pythonArgs += "--refresh-derived"
}
if ($DryRun) {
  $pythonArgs += "--dry-run"
}

& python @pythonArgs
exit $LASTEXITCODE
