[CmdletBinding()]
param(
  [string]$PolicyPath,
  [int]$IntervalMinutes = 0
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath
Save-RollbackSnapshot -Policy $policy -Paths $paths -Reason "install-task" | Out-Null
$task = Register-SystemGuardianTask -Policy $policy -Paths $paths -IntervalMinutes $IntervalMinutes
$status = Get-SystemGuardianStatus -Policy $policy -Paths $paths

Write-Output ("installed task={0} intervalMinutes={1} profile={2}" -f $task.taskName, $task.intervalMinutes, $status.profile)
