[CmdletBinding()]
param(
  [string]$PolicyPath
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath
$result = Restore-SystemGuardianRollback -Policy $policy -Paths $paths

$result | ConvertTo-Json -Depth 10
