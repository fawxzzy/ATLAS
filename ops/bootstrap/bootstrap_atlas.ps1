[CmdletBinding()]
param(
  [string]$StackFile
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $StackFile) {
  $StackFile = Join-Path $atlasRoot "stack.yaml"
}

function Get-StackConfig {
  param([string]$StackFilePath, [string]$AtlasRootPath)
  $pythonCode = @"
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"$AtlasRootPath") / "ops" / "validation"))
import validate_stack
config = validate_stack.load_stack_config(Path(r"$StackFilePath"))
print(json.dumps(config))
"@
  $json = $pythonCode | & python -
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to parse stack.yaml."
  }
  return $json | ConvertFrom-Json
}

function Resolve-AtlasPath {
  param([string]$BaseDir, [string]$RawPath)
  if ([System.IO.Path]::IsPathRooted($RawPath)) {
    return [System.IO.Path]::GetFullPath($RawPath)
  }
  return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $RawPath))
}

$config = Get-StackConfig -StackFilePath $StackFile -AtlasRootPath $atlasRoot
$stackBase = Split-Path -Parent ([System.IO.Path]::GetFullPath($StackFile))

$targets = New-Object System.Collections.Generic.List[string]
foreach ($property in $config.paths.PSObject.Properties) {
  $targets.Add((Resolve-AtlasPath -BaseDir $stackBase -RawPath $property.Value))
}
foreach ($group in $config.subpaths.PSObject.Properties) {
  foreach ($property in $group.Value.PSObject.Properties) {
    $targets.Add((Resolve-AtlasPath -BaseDir $stackBase -RawPath $property.Value))
  }
}
$targets.Add((Join-Path $atlasRoot "docs\ops"))
$targets.Add((Join-Path $atlasRoot "runtime\receipts\validation"))

$created = New-Object System.Collections.Generic.List[string]
$existing = New-Object System.Collections.Generic.List[string]

foreach ($target in ($targets | Sort-Object -Unique)) {
  if (Test-Path -LiteralPath $target) {
    $existing.Add($target)
    continue
  }
  New-Item -ItemType Directory -Force -Path $target | Out-Null
  $created.Add($target)
}

Write-Host "ATLAS bootstrap complete."
Write-Host ("Created directories: {0}" -f $created.Count)
foreach ($path in $created) {
  Write-Host ("  + {0}" -f $path)
}
Write-Host ("Already present: {0}" -f $existing.Count)
