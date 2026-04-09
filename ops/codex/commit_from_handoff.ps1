[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$HandoffFile,
  [string]$RepoId = "",
  [string]$SchemaFile = "ops/codex/schemas/change_handoff.schema.json",
  [string]$DetectScript = "ops/codex/detect_target_repo.py",
  [string]$PreviewRoot = "tmp/previews",
  [ValidateSet("preview", "commit")]
  [string]$Mode = "preview",
  [switch]$StageAll,
  [string]$MessageFile = ""
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

if (-not $MessageFile) {
  $messagePath = Join-Path $previewRootAbsolute ("{0}.commit-message.txt" -f $previewStem)
}
else {
  $messagePath = Resolve-AtlasPath -Candidate $MessageFile
}
$previewJsonPath = Join-Path $previewRootAbsolute ("{0}.commit-preview.json" -f $previewStem)

$commitMessage = "{0}`r`n`r`n{1}" -f $handoff.commit_title, $handoff.commit_body.Trim()
$messageDirectory = Split-Path -Parent $messagePath
if ($messageDirectory) {
  New-Item -ItemType Directory -Force -Path $messageDirectory | Out-Null
}
$commitMessage | Set-Content -Encoding UTF8 -LiteralPath $messagePath

$preview = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  mode = $Mode
  handoff = [ordered]@{
    path = Get-AtlasRelativePath -Candidate $handoffAbsolute
    handoff_id = $handoff.handoff_id
    task_name = $handoff.task_name
  }
  repo_detection = $target
  stage_all = [bool]$StageAll
  message_file = Get-AtlasRelativePath -Candidate $messagePath
  preview_file = Get-AtlasRelativePath -Candidate $previewJsonPath
  commit_title = $handoff.commit_title
  commit_body = $handoff.commit_body.Trim()
  git_command = if ($target.repo_root) {
    @("git", "-C", $target.repo_root, "commit", "-F", $messagePath)
  }
  else {
    @()
  }
}

if ($target.status -eq "resolved") {
  $statusCapture = Invoke-CapturedCommand -Arguments @("git", "-C", $target.repo_root, "status", "--short")
  $preview.git_status = $statusCapture.output
}

$preview | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $previewJsonPath

Write-Host ("Handoff       : {0}" -f (Get-AtlasRelativePath -Candidate $handoffAbsolute))
Write-Host ("Repo status   : {0}" -f $target.status)
Write-Host ("Repo id       : {0}" -f ($(if ($target.repo_id) { $target.repo_id } else { "<none>" })))
if ($target.repo_root_atlas_path) {
  Write-Host ("Repo root     : {0}" -f $target.repo_root_atlas_path)
}
Write-Host ("Message file  : {0}" -f (Get-AtlasRelativePath -Candidate $messagePath))
Write-Host ("Preview file  : {0}" -f (Get-AtlasRelativePath -Candidate $previewJsonPath))
Write-Host ("Commit title  : {0}" -f $handoff.commit_title)

if ($Mode -eq "preview") {
  Write-Host ""
  Write-Host "Preview commit message:"
  Write-Host "----------------------------------------"
  Get-Content -LiteralPath $messagePath | Out-Host
  Write-Host "----------------------------------------"
  exit 0
}

if ($target.status -eq "no_repo_detected") {
  throw "Commit execution is blocked because the handoff does not map to a registered repo. ATLAS will not assume C:\ATLAS is the git target."
}
if ($target.status -eq "git_unavailable") {
  throw "Commit execution is blocked because the resolved repo path does not expose a usable .git checkout."
}
if ($target.status -ne "resolved") {
  throw ("Commit execution is blocked because target repo detection returned '{0}'." -f $target.status)
}

if ($StageAll) {
  $stageCapture = Invoke-CapturedCommand -Arguments @("git", "-C", $target.repo_root, "add", "-A")
  $preview.stage_command = @("git", "-C", $target.repo_root, "add", "-A")
  $preview.stage_output = $stageCapture.output
  $preview.stage_exit_code = $stageCapture.exit_code
  $preview | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $previewJsonPath
  if ($stageCapture.exit_code -ne 0) {
    throw "git add failed. See the preview JSON for the captured error output."
  }
}

$commitCapture = Invoke-CapturedCommand -Arguments @("git", "-C", $target.repo_root, "commit", "-F", $messagePath)
$preview.commit_output = $commitCapture.output
$preview.commit_exit_code = $commitCapture.exit_code
$preview | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $previewJsonPath

if ($commitCapture.exit_code -ne 0) {
  $joined = ($commitCapture.output -join "`n")
  if ($joined -match "permission denied|access is denied|could not open .*\\.git|index\\.lock") {
    throw "git commit failed because .git access is blocked or locked. See the preview JSON for details."
  }
  throw "git commit failed. See the preview JSON for captured stdout/stderr."
}

Write-Host "Commit completed."
exit 0
