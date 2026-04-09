[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$TaskName,
  [Parameter(Mandatory = $true)]
  [string[]]$CodexCommand,
  [string]$Workspace = ".",
  [string]$RepoId = "",
  [string]$SchemaFile = "ops/codex/schemas/change_handoff.schema.json",
  [string]$HandoffRoot = "runtime/receipts/handoffs",
  [string]$HandoffName = "",
  [string]$PreviewRoot = "tmp/previews",
  [switch]$PreviewOnly,
  [switch]$SkipValidation,
  [switch]$SkipCommitPreview,
  [switch]$SkipPrPreview
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Resolve-AtlasPath {
  param([string]$Candidate)

  if ([System.IO.Path]::IsPathRooted($Candidate)) {
    $path = $Candidate
  }
  else {
    $path = Join-Path $atlasRoot $Candidate
  }
  return [System.IO.Path]::GetFullPath($path)
}

function Get-AtlasRelativePath {
  param([string]$Candidate)

  $absolute = Resolve-AtlasPath -Candidate $Candidate
  $root = [System.IO.Path]::GetFullPath($atlasRoot).TrimEnd("\")
  if ($absolute.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    $relative = $absolute.Substring($root.Length).TrimStart("\")
    if ([string]::IsNullOrWhiteSpace($relative)) {
      return "."
    }
    return $relative -replace "\\", "/"
  }
  return $absolute -replace "\\", "/"
}

function New-Slug {
  param([string]$Value)

  $slug = $Value.ToLowerInvariant()
  $slug = [System.Text.RegularExpressions.Regex]::Replace($slug, "[^a-z0-9]+", "-")
  $slug = $slug.Trim("-")
  if ([string]::IsNullOrWhiteSpace($slug)) {
    return "codex-task"
  }
  return $slug
}

$schemaAbsolute = Resolve-AtlasPath -Candidate $SchemaFile
if (-not (Test-Path -LiteralPath $schemaAbsolute)) {
  throw "Schema file not found: $SchemaFile"
}

$workspaceAbsolute = Resolve-AtlasPath -Candidate $Workspace
if (-not (Test-Path -LiteralPath $workspaceAbsolute)) {
  throw "Workspace not found: $Workspace"
}

$handoffRootAbsolute = Resolve-AtlasPath -Candidate $HandoffRoot
New-Item -ItemType Directory -Force -Path $handoffRootAbsolute | Out-Null

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$handoffStem = if ($HandoffName) { $HandoffName } else { "{0}-{1}" -f (New-Slug -Value $TaskName), $timestamp }
$handoffFilename = "{0}.handoff.json" -f (New-Slug -Value $handoffStem)
$handoffAbsolute = Join-Path $handoffRootAbsolute $handoffFilename
$handoffAtlasRelative = Get-AtlasRelativePath -Candidate $handoffAbsolute

$tokens = @(
  [ordered]@{ key = "{HANDOFF_PATH}"; value = $handoffAbsolute; capture = $true },
  [ordered]@{ key = "{HANDOFF_ATLAS_PATH}"; value = $handoffAtlasRelative; capture = $true },
  [ordered]@{ key = "{SCHEMA_PATH}"; value = $schemaAbsolute; capture = $false },
  [ordered]@{ key = "{SCHEMA_ATLAS_PATH}"; value = (Get-AtlasRelativePath -Candidate $schemaAbsolute); capture = $false },
  [ordered]@{ key = "{WORKSPACE_PATH}"; value = $workspaceAbsolute; capture = $false },
  [ordered]@{ key = "{WORKSPACE_ATLAS_PATH}"; value = (Get-AtlasRelativePath -Candidate $workspaceAbsolute); capture = $false }
)

$captureTokenPresent = $false
$resolvedCommand = foreach ($part in $CodexCommand) {
  $resolved = $part
  foreach ($token in $tokens) {
    if ($resolved.Contains($token.key)) {
      if ($token.capture) {
        $captureTokenPresent = $true
      }
      $resolved = $resolved.Replace($token.key, $token.value)
    }
  }
  $resolved
}

if (-not $captureTokenPresent) {
  throw "CodexCommand must include {HANDOFF_PATH} or {HANDOFF_ATLAS_PATH} so final output capture stays explicit."
}

Write-Host ("Task name      : {0}" -f $TaskName)
Write-Host ("Workspace      : {0}" -f (Get-AtlasRelativePath -Candidate $workspaceAbsolute))
Write-Host ("Schema         : {0}" -f (Get-AtlasRelativePath -Candidate $schemaAbsolute))
Write-Host ("Handoff output : {0}" -f $handoffAtlasRelative)
Write-Host ("Resolved cmd   : {0}" -f ([string]::Join(" ", $resolvedCommand)))

if ($PreviewOnly) {
  Write-Host "Preview only requested. Codex was not executed."
  exit 0
}

Push-Location $workspaceAbsolute
try {
  & $resolvedCommand[0] @($resolvedCommand | Select-Object -Skip 1)
  $commandExit = $LASTEXITCODE
}
finally {
  Pop-Location
}

if (-not (Test-Path -LiteralPath $handoffAbsolute)) {
  Write-Error ("Expected Codex final-output handoff was not created: {0}" -f $handoffAtlasRelative)
  exit 1
}

if (-not $SkipValidation) {
  & python (Join-Path $atlasRoot "ops\codex\validate_handoff.py") --schema-file $schemaAbsolute --handoff-file $handoffAbsolute
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

Write-Host ("Validated handoff: {0}" -f $handoffAtlasRelative)

if (-not $SkipCommitPreview) {
  $commitArgs = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $atlasRoot "ops\codex\commit_from_handoff.ps1"),
    "-HandoffFile",
    $handoffAbsolute,
    "-PreviewRoot",
    (Resolve-AtlasPath -Candidate $PreviewRoot),
    "-Mode",
    "preview"
  )
  if ($RepoId) {
    $commitArgs += @("-RepoId", $RepoId)
  }
  & powershell @commitArgs
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

if (-not $SkipPrPreview) {
  $prArgs = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $atlasRoot "ops\codex\prepare_pr_from_handoff.ps1"),
    "-HandoffFile",
    $handoffAbsolute,
    "-PreviewRoot",
    (Resolve-AtlasPath -Candidate $PreviewRoot),
    "-Mode",
    "preview"
  )
  if ($RepoId) {
    $prArgs += @("-RepoId", $RepoId)
  }
  & powershell @prArgs
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

exit $commandExit
