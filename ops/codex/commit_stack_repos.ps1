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

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptRoot "commit_stack_repos.py"

function Resolve-PythonCommand {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return $python.Path
  }

  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    return $py.Path
  }

  throw "Python runtime not found on PATH."
}

$pythonCommand = Resolve-PythonCommand
$pythonArgs = @($pythonScript)

if ($DryRun) {
  $pythonArgs += "--dry-run"
}
if ($IncludeRoot) {
  $pythonArgs += "--include-root"
}

foreach ($repoId in $RepoIds) {
  if ([string]::IsNullOrWhiteSpace($repoId)) {
    continue
  }
  foreach ($chunk in ($repoId -split ",")) {
    $normalized = $chunk.Trim()
    if ($normalized) {
      $pythonArgs += @("--repo-id", $normalized)
    }
  }
}

if ($CommitMessage) {
  $pythonArgs += @("--commit-message", $CommitMessage)
}
if ($CommitMessagePrefix) {
  $pythonArgs += @("--commit-message-prefix", $CommitMessagePrefix)
}
if ($CommitMessageSuffix) {
  $pythonArgs += @("--commit-message-suffix", $CommitMessageSuffix)
}

& $pythonCommand @pythonArgs
exit $LASTEXITCODE
