[CmdletBinding(DefaultParameterSetName = "Status")]
param(
  [Parameter(ParameterSetName = "Disable")]
  [switch]$Disable,
  [Parameter(ParameterSetName = "Enable")]
  [switch]$Enable,
  [string]$PolicyPath
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath

if ($Disable) {
  Save-RollbackSnapshot -Policy $policy -Paths $paths -Reason "disable-kill-switch" | Out-Null
  Set-KillSwitchState -Paths $paths -Disabled $true
}
elseif ($Enable) {
  Save-RollbackSnapshot -Policy $policy -Paths $paths -Reason "enable-kill-switch" | Out-Null
  Set-KillSwitchState -Paths $paths -Disabled $false
}

Write-Output ("killSwitchEnabled={0}" -f (Test-KillSwitchEnabled -Paths $paths))
