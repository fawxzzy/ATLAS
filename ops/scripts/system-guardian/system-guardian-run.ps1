[CmdletBinding(DefaultParameterSetName = "DryRun")]
param(
  [Parameter(ParameterSetName = "DryRun")]
  [switch]$DryRun,
  [Parameter(ParameterSetName = "Apply")]
  [switch]$Apply,
  [ValidateSet("observe", "notify", "cleanup")]
  [string]$Mode,
  [string]$Profile,
  [string]$PolicyPath
)

$commonPath = Join-Path $PSScriptRoot "SystemGuardian.Common.ps1"
. $commonPath

$paths = Get-SystemGuardianPaths -PolicyPath $PolicyPath
Ensure-SystemGuardianDirectories -Paths $paths
$policy = Get-SystemGuardianPolicy -PolicyPath $paths.policyPath
$selectedProfile = if (Test-HasValue $Profile) { $Profile } else { Get-ActiveProfileName -Policy $policy -Paths $paths }
$run = Invoke-SystemGuardianRun -Policy $policy -Paths $paths -ProfileName $selectedProfile -ModeOverride $Mode -ApplyChanges ([bool]$Apply)
Write-SystemGuardianRunSummary -Run $run
