[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$TaskName,
  [Parameter(Mandatory = $true)]
  [string[]]$CodexCommand,
  [string]$TaskSummary = "",
  [string]$Workspace = ".",
  [string[]]$ScopePaths = @("."),
  [string[]]$RepoIds = @("stack"),
  [ValidateSet("read_only", "scoped_write", "stack_only")]
  [string]$MutationMode = "stack_only",
  [string[]]$ValidationCommand = @(),
  [string]$ExportType = "",
  [string]$ExportArtifactPath = "",
  [string]$ExportManifestPath = "",
  [string]$SessionId = "",
  [string]$TaskId = ""
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$scratchRoot = Join-Path $atlasRoot "tmp\scratch\codex-wrapper"
New-Item -ItemType Directory -Force -Path $scratchRoot | Out-Null

function Get-RelativeAtlasPath {
  param([string]$Candidate)

  $resolved = Resolve-Path -LiteralPath $Candidate -ErrorAction SilentlyContinue
  if (-not $resolved) {
    $resolved = Resolve-Path -LiteralPath (Join-Path $atlasRoot $Candidate) -ErrorAction SilentlyContinue
  }
  if (-not $resolved) {
    return ($Candidate -replace "\\", "/")
  }

  $resolvedPath = $resolved.Path
  $rootPrefix = $atlasRoot.TrimEnd("\")
  if ($resolvedPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    $relative = $resolvedPath.Substring($rootPrefix.Length).TrimStart("\")
    if ([string]::IsNullOrWhiteSpace($relative)) {
      return "."
    }
    return ($relative -replace "\\", "/")
  }

  return ($resolvedPath -replace "\\", "/")
}

function New-AtlasId {
  param([string]$Prefix)

  $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ")
  $suffix = [System.Guid]::NewGuid().ToString("N").Substring(0, 6)
  return "$Prefix-$stamp-$suffix"
}

if (-not $SessionId) {
  $SessionId = New-AtlasId -Prefix "session"
}

if (-not $TaskId) {
  $TaskId = New-AtlasId -Prefix "task"
}

$workspacePath = Get-RelativeAtlasPath -Candidate $Workspace
$scopePathsRelative = @()
foreach ($pathItem in $ScopePaths) {
  $scopePathsRelative += Get-RelativeAtlasPath -Candidate $pathItem
}

$producer = @{
  kind = "wrapper"
  name = "atlas-codex-wrapper"
  version = "1"
}

$session = @{
  session_id = $SessionId
  workspace_root = $workspacePath
  operator = "human"
}

$task = @{
  task_id = $TaskId
  task_name = $TaskName
  scope_paths = $scopePathsRelative
  repo_ids = $RepoIds
  mutation_mode = $MutationMode
}

function Invoke-AtlasEvent {
  param(
    [ValidateSet("session_start", "task_start", "pre_command", "post_command", "validation_complete", "export_complete", "session_stop")]
    [string]$EventType,
    [hashtable]$Payload,
    [switch]$IncludeTask
  )

  $eventBody = @{
    contract_version = "atlas.event.v1"
    event_type = $EventType
    event_id = New-AtlasId -Prefix $EventType
    occurred_at = (Get-Date).ToUniversalTime().ToString("o")
    producer = $producer
    session = $session
    payload = $Payload
  }

  if ($IncludeTask) {
    $eventBody.task = $task
  }

  $tempPath = Join-Path $scratchRoot "$EventType-$([System.Guid]::NewGuid().ToString('N')).json"
  $eventBody | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $tempPath
  try {
    & (Join-Path $atlasRoot "ops\events\invoke_event.ps1") -PayloadFile $tempPath -EventType $EventType -SkipHandler | Out-Host
    return $LASTEXITCODE
  }
  finally {
    Remove-Item -LiteralPath $tempPath -ErrorAction SilentlyContinue
  }
}

$sessionSummary = "Task '$TaskName' was not started."
$sessionStatus = "failed"
$receiptCount = 0

Invoke-AtlasEvent -EventType "session_start" -Payload @{
  trigger = "wrapper"
  intent = if ($TaskSummary) { $TaskSummary } else { "Run scoped Codex task '$TaskName'." }
  workspace_scope = $scopePathsRelative
  metadata = @{
    command = $CodexCommand
  }
} | Out-Null
$receiptCount++

$taskStartPayload = @{
  task_summary = if ($TaskSummary) { $TaskSummary } else { "Run scoped Codex task '$TaskName'." }
  scoped_paths = $scopePathsRelative
  mutation_mode = $MutationMode
}
if ($ValidationCommand.Count -gt 0) {
  $taskStartPayload["validation_plan"] = @([string]::Join(" ", $ValidationCommand))
}

Invoke-AtlasEvent -EventType "task_start" -IncludeTask -Payload $taskStartPayload | Out-Null
$receiptCount++

$commandPreview = @($CodexCommand)
Invoke-AtlasEvent -EventType "pre_command" -IncludeTask -Payload @{
  command = $commandPreview
  cwd = $workspacePath
  intent = "Run Codex through the explicit ATLAS wrapper."
} | Out-Null
$receiptCount++

$commandStatus = "failed"
$commandExit = 1
$durationMs = 0
$workspaceAbsolute = Join-Path $atlasRoot $Workspace
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

try {
  Push-Location $workspaceAbsolute
  & $CodexCommand[0] @($CodexCommand | Select-Object -Skip 1)
  $commandExit = $LASTEXITCODE
}
finally {
  $stopwatch.Stop()
  $durationMs = [int][math]::Round($stopwatch.Elapsed.TotalMilliseconds)
  Pop-Location
}

if ($commandExit -eq 0) {
  $commandStatus = "succeeded"
  $sessionStatus = "completed"
  $sessionSummary = "Task '$TaskName' completed."
}
else {
  $commandStatus = "failed"
  $sessionStatus = "failed"
  $sessionSummary = "Task '$TaskName' failed."
}

Invoke-AtlasEvent -EventType "post_command" -IncludeTask -Payload @{
  command = $commandPreview
  cwd = $workspacePath
  status = $commandStatus
  exit_code = $commandExit
  duration_ms = $durationMs
  stdout_summary = "See console output from the wrapped command."
  stderr_summary = ""
} | Out-Null
$receiptCount++

if ($ValidationCommand.Count -gt 0) {
  $validationExit = 1
  $validationSummary = "Validation command did not run."
  Push-Location $atlasRoot
  try {
    & $ValidationCommand[0] @($ValidationCommand | Select-Object -Skip 1)
    $validationExit = $LASTEXITCODE
  }
  finally {
    Pop-Location
  }
  if ($validationExit -eq 0) {
    $validationSummary = "Validation command completed successfully."
  }
  else {
    $validationSummary = "Validation command reported a failure."
    if ($sessionStatus -eq "completed") {
      $sessionStatus = "failed"
      $sessionSummary = "Task '$TaskName' completed, but validation failed."
    }
  }
  Invoke-AtlasEvent -EventType "validation_complete" -IncludeTask -Payload @{
    validator = [string]::Join(" ", $ValidationCommand)
    status = if ($validationExit -eq 0) { "passed" } else { "failed" }
    summary = $validationSummary
    artifacts = @(
      "runtime/receipts/validation/event-contract-validation.latest.json"
    )
    finding_counts = @{
      critical = 0
      error = if ($validationExit -eq 0) { 0 } else { 1 }
      warning = 0
      info = 0
    }
  } | Out-Null
  $receiptCount++
}

if ($ExportType -and $ExportArtifactPath) {
  Invoke-AtlasEvent -EventType "export_complete" -IncludeTask -Payload @{
    export_type = $ExportType
    status = "created"
    artifact_path = $ExportArtifactPath
    manifest_path = $ExportManifestPath
    summary = "Wrapper recorded an explicit export artifact."
  } | Out-Null
  $receiptCount++
}

Invoke-AtlasEvent -EventType "session_stop" -Payload @{
  status = $sessionStatus
  summary = $sessionSummary
  task_ids = @($TaskId)
  receipt_count = $receiptCount + 1
} | Out-Null

exit $commandExit
