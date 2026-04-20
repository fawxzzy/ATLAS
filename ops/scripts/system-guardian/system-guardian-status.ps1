[CmdletBinding()]
param(
  [string]$PolicyPath
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath
$status = Get-SystemGuardianStatus -Policy $policy -Paths $paths

$status | ConvertTo-Json -Depth 10
