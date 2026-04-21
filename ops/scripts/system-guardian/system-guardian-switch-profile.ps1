[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Name,
  [string]$PolicyPath
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath
Save-RollbackSnapshot -Policy $policy -Paths $paths -Reason "switch-profile" | Out-Null
Set-ActiveProfileName -Policy $policy -Paths $paths -ProfileName $Name
$summary = Get-ProfileSummary -Policy $policy -ProfileName $Name

Write-Output ("active profile set to {0}" -f $Name)
Write-Output ("profileSummary={0}" -f $summary.summary)
Write-Output ("thresholds={0}" -f $summary.thresholdSummary)
