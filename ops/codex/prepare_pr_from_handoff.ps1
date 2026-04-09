[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$HandoffFile,
  [string]$RepoId = "",
  [string]$SchemaFile = "ops/codex/schemas/change_handoff.schema.json",
  [string]$DetectScript = "ops/codex/detect_target_repo.py",
  [string]$PreviewRoot = "tmp/previews",
  [string]$OutputPath = "",
  [ValidateSet("preview", "open")]
  [string]$Mode = "preview",
  [string]$BaseBranch = "",
  [string]$HeadBranch = "",
  [switch]$Draft
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

function Write-Utf8File {
  param(
    [string]$Path,
    [string]$Content
  )

  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function New-PreviewStem {
  param(
    [string]$HandoffAbsolute,
    [string]$RepoLabel
  )

  $stem = [System.IO.Path]::GetFileNameWithoutExtension([System.IO.Path]::GetFileNameWithoutExtension($HandoffAbsolute))
  if ([string]::IsNullOrWhiteSpace($RepoLabel)) {
    return $stem
  }
  return "{0}.{1}" -f $stem, $RepoLabel
}

function Invoke-CapturedCommand {
  param([string[]]$Arguments)

  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $output = & $Arguments[0] @($Arguments | Select-Object -Skip 1) 2>&1
    $exitCode = $LASTEXITCODE
  }
  finally {
    $ErrorActionPreference = $previousPreference
  }
  return @{
    output = @($output | ForEach-Object { "$_" })
    exit_code = $exitCode
  }
}

$handoffAbsolute = Resolve-AtlasPath -Candidate $HandoffFile
$schemaAbsolute = Resolve-AtlasPath -Candidate $SchemaFile
$detectAbsolute = Resolve-AtlasPath -Candidate $DetectScript
$previewRootAbsolute = Resolve-AtlasPath -Candidate $PreviewRoot

& python (Join-Path $atlasRoot "ops\codex\validate_handoff.py") --schema-file $schemaAbsolute --handoff-file $handoffAbsolute
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$handoff = Get-Content -Raw -LiteralPath $handoffAbsolute | ConvertFrom-Json
$detectArgs = @($detectAbsolute, "--handoff-file", $handoffAbsolute)
if ($RepoId) {
  $detectArgs += @("--repo-id", $RepoId)
}
$detectRaw = & python @detectArgs
if (-not $detectRaw) {
  throw "Repo detection produced no output."
}
$target = $detectRaw | ConvertFrom-Json

New-Item -ItemType Directory -Force -Path $previewRootAbsolute | Out-Null
$repoLabel = if ($target.repo_id) { $target.repo_id } else { "unresolved" }
$previewStem = New-PreviewStem -HandoffAbsolute $handoffAbsolute -RepoLabel $repoLabel

if (-not $OutputPath) {
  $renderPath = Join-Path $previewRootAbsolute ("{0}.pr.md" -f $previewStem)
}
else {
  $renderPath = Resolve-AtlasPath -Candidate $OutputPath
}
$previewJsonPath = Join-Path $previewRootAbsolute ("{0}.pr-preview.json" -f $previewStem)

$renderDirectory = Split-Path -Parent $renderPath
if ($renderDirectory) {
  New-Item -ItemType Directory -Force -Path $renderDirectory | Out-Null
}

$lines = @(
  "# PR Title",
  "",
  $handoff.pr_title,
  "",
  "# PR Body",
  "",
  $handoff.pr_body.Trim(),
  "",
  "# Source Handoff",
  "",
  (Get-AtlasRelativePath -Candidate $handoffAbsolute)
)

Write-Utf8File -Path $renderPath -Content ($lines -join "`r`n")

$ghCommand = @("gh", "pr", "create", "--title", $handoff.pr_title, "--body-file", $renderPath)
if ($BaseBranch) {
  $ghCommand += @("--base", $BaseBranch)
}
if ($HeadBranch) {
  $ghCommand += @("--head", $HeadBranch)
}
if ($Draft) {
  $ghCommand += "--draft"
}

$preview = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  mode = $Mode
  handoff = [ordered]@{
    path = Get-AtlasRelativePath -Candidate $handoffAbsolute
    handoff_id = $handoff.handoff_id
    task_name = $handoff.task_name
  }
  repo_detection = $target
  render_file = Get-AtlasRelativePath -Candidate $renderPath
  preview_file = Get-AtlasRelativePath -Candidate $previewJsonPath
  pr_title = $handoff.pr_title
  pr_body = $handoff.pr_body.Trim()
  gh_command = if ($target.repo_root) { $ghCommand } else { @() }
}
Write-Utf8File -Path $previewJsonPath -Content ($preview | ConvertTo-Json -Depth 8)

Write-Host ("Handoff    : {0}" -f (Get-AtlasRelativePath -Candidate $handoffAbsolute))
Write-Host ("Repo status: {0}" -f $target.status)
Write-Host ("Repo id    : {0}" -f ($(if ($target.repo_id) { $target.repo_id } else { "<none>" })))
if ($target.repo_root_atlas_path) {
  Write-Host ("Repo root  : {0}" -f $target.repo_root_atlas_path)
}
Write-Host ("PR output  : {0}" -f (Get-AtlasRelativePath -Candidate $renderPath))
Write-Host ("Preview    : {0}" -f (Get-AtlasRelativePath -Candidate $previewJsonPath))
Write-Host ("PR title   : {0}" -f $handoff.pr_title)

if ($Mode -eq "preview") {
  exit 0
}

if ($target.status -eq "no_repo_detected") {
  throw "PR creation is blocked because the handoff does not map to a registered repo. ATLAS will not assume C:\ATLAS is the git target."
}
if ($target.status -eq "git_unavailable") {
  throw "PR creation is blocked because the resolved repo path does not expose a usable .git checkout."
}
if ($target.status -ne "resolved") {
  throw ("PR creation is blocked because target repo detection returned '{0}'." -f $target.status)
}

$authCapture = Invoke-CapturedCommand -Arguments @("gh", "auth", "status")
$preview.auth_output = $authCapture.output
$preview.auth_exit_code = $authCapture.exit_code
Write-Utf8File -Path $previewJsonPath -Content ($preview | ConvertTo-Json -Depth 8)
if ($authCapture.exit_code -ne 0) {
  throw "gh auth status failed. PR execution is blocked until GitHub CLI authentication is available."
}

Push-Location $target.repo_root
try {
  $openCapture = Invoke-CapturedCommand -Arguments $ghCommand
}
finally {
  Pop-Location
}

$preview.open_output = $openCapture.output
$preview.open_exit_code = $openCapture.exit_code
Write-Utf8File -Path $previewJsonPath -Content ($preview | ConvertTo-Json -Depth 8)

if ($openCapture.exit_code -ne 0) {
  $joined = ($openCapture.output -join "`n")
  if ($joined -match "authentication failed|not logged into|requires authentication|permission denied") {
    throw "gh pr create failed because authentication or repo permission is missing. See the preview JSON for details."
  }
  throw "gh pr create failed. See the preview JSON for captured stdout/stderr."
}

Write-Host "PR created."
exit 0
