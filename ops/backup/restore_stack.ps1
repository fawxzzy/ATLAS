[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$SourcePath,

  [string]$DestinationRoot,
  [switch]$Overwrite
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $DestinationRoot) {
  $DestinationRoot = $atlasRoot
}

$resolvedSource = [System.IO.Path]::GetFullPath((Join-Path $atlasRoot $SourcePath))
$resolvedDestination = [System.IO.Path]::GetFullPath((Join-Path $atlasRoot $DestinationRoot))

if (-not (Test-Path -LiteralPath $resolvedSource)) {
  throw "Restore source not found: $resolvedSource"
}

$stagingRoot = $resolvedSource
$cleanupStaging = $false
if ((Get-Item -LiteralPath $resolvedSource).PSIsContainer -eq $false) {
  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $stagingRoot = Join-Path $atlasRoot ("tmp\scratch\restore-{0}" -f $timestamp)
  if (Test-Path -LiteralPath $stagingRoot) {
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null
  [System.IO.Compression.ZipFile]::ExtractToDirectory($resolvedSource, $stagingRoot)
  $cleanupStaging = $true
}

$restored = 0
$skipped = 0
$secretSkipped = 0

Get-ChildItem -LiteralPath $stagingRoot -Recurse -File -Force | ForEach-Object {
  $relative = $_.FullName.Substring($stagingRoot.Length).TrimStart('\')
  $normalizedRelative = $relative.Replace('\', '/')
  if ($normalizedRelative -match '(^|/)secrets(/|$)') {
    $secretSkipped += 1
    return
  }

  $destination = Join-Path $resolvedDestination $relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null

  if ((Test-Path -LiteralPath $destination) -and (-not $Overwrite)) {
    $skipped += 1
    return
  }

  Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
  $restored += 1
}

if ($cleanupStaging -and (Test-Path -LiteralPath $stagingRoot)) {
  Remove-Item -LiteralPath $stagingRoot -Recurse -Force
}

Write-Host "Restore complete."
Write-Host ("Restored files: {0}" -f $restored)
Write-Host ("Skipped existing files: {0}" -f $skipped)
Write-Host ("Skipped secrets files: {0}" -f $secretSkipped)
