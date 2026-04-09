[CmdletBinding()]
param(
  [ValidateSet("session_start", "task_start", "pre_command", "post_command", "validation_complete", "export_complete", "session_stop")]
  [string]$EventType,
  [string]$PayloadFile,
  [string]$PayloadJson,
  [string]$ReceiptDir,
  [switch]$ReadFromStdin,
  [switch]$SkipHandler
)

$ErrorActionPreference = "Stop"

$atlasRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonArgs = @(
  (Join-Path $atlasRoot "ops\events\invoke_event.py")
)

if ($EventType) {
  $pythonArgs += @("--event-type", $EventType)
}

if ($PayloadFile) {
  $pythonArgs += @("--payload-file", $PayloadFile)
}
elseif ($PayloadJson) {
  $pythonArgs += @("--payload-json", $PayloadJson)
}
elseif ($ReadFromStdin) {
  $pythonArgs += "--stdin"
}
else {
  throw "One of -PayloadFile, -PayloadJson, or -ReadFromStdin is required."
}

if ($ReceiptDir) {
  $pythonArgs += @("--receipt-dir", $ReceiptDir)
}

if ($SkipHandler) {
  $pythonArgs += "--skip-handler"
}

& python @pythonArgs
exit $LASTEXITCODE
