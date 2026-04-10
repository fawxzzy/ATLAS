[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$IncludeRoot,
  [string[]]$RepoIds = @(),
  [string]$CommitMessage = "ATLAS stack sync",
  [string]$CommitMessagePrefix = "",
  [string]$CommitMessageSuffix = ""
)

$ErrorActionPreference = "Stop"

$canonical = Join-Path $PSScriptRoot "commit_stack_repos.ps1"
$arguments = @()
if ($DryRun) {
  $arguments += "-DryRun"
}
if ($IncludeRoot) {
  $arguments += "-IncludeRoot"
}
foreach ($repoId in $RepoIds) {
  $arguments += @("-RepoIds", $repoId)
}
$arguments += @("-CommitMessage", $CommitMessage)
if ($CommitMessagePrefix) {
  $arguments += @("-CommitMessagePrefix", $CommitMessagePrefix)
}
if ($CommitMessageSuffix) {
  $arguments += @("-CommitMessageSuffix", $CommitMessageSuffix)
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $canonical @arguments
exit $LASTEXITCODE
