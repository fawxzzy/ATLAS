[CmdletBinding()]
param(
  [string]$PolicyPath
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath
Save-RollbackSnapshot -Policy $policy -Paths $paths -Reason "uninstall-task" | Out-Null
Unregister-SystemGuardianTask -Policy $policy

Write-Output "uninstalled task"
