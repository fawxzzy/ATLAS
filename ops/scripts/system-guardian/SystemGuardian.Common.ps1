Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertTo-PlainData {
  param(
    [Parameter(ValueFromPipeline = $true)]
    $InputObject
  )

  if ($null -eq $InputObject) {
    return $null
  }

  if ($InputObject -is [System.Collections.IDictionary]) {
    $table = @{}
    foreach ($key in $InputObject.Keys) {
      $table[$key] = ConvertTo-PlainData -InputObject $InputObject[$key]
    }
    return $table
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $items = @()
    foreach ($item in $InputObject) {
      $items += @(ConvertTo-PlainData -InputObject $item)
    }
    return $items
  }

  if ($InputObject -is [psobject]) {
    $table = @{}
    foreach ($property in $InputObject.PSObject.Properties) {
      $table[$property.Name] = ConvertTo-PlainData -InputObject $property.Value
    }
    return $table
  }

  return $InputObject
}

function Get-MapValue {
  param(
    $Map,
    [string]$Key,
    $Default = $null
  )

  if (Test-MapHasKey -Map $Map -Key $Key) {
    return $Map[$Key]
  }

  return $Default
}

function Test-MapHasKey {
  param(
    $Map,
    [string]$Key
  )

  if ($null -eq $Key) {
    return $false
  }

  if ($Map -is [hashtable]) {
    return $Map.ContainsKey($Key)
  }

  if (($Map -is [psobject]) -and ($Map.PSObject.Methods.Name -contains "ContainsKey")) {
    return $Map.ContainsKey($Key)
  }

  if ($Map -is [System.Collections.IDictionary]) {
    return $Map.Contains($Key)
  }

  return $false
}

function Test-HasValue {
  param($Value)

  if ($null -eq $Value) {
    return $false
  }

  if ($Value -is [string]) {
    return -not [string]::IsNullOrWhiteSpace($Value)
  }

  return $true
}

function ConvertTo-StringArray {
  param($Value)

  $items = @()
  foreach ($item in @($Value)) {
    if (-not (Test-HasValue $item)) {
      continue
    }
    $items += @([string]$item)
  }
  return $items
}

function Format-ThresholdSummary {
  param(
    $Thresholds
  )

  if ($null -eq $Thresholds) {
    return "thresholds unavailable"
  }

  return "workingSetMb>={0}; cpuSeconds>={1}; ageMinutes>={2}; repeatedBreaches>={3}" -f `
    (Get-MapValue -Map $Thresholds -Key "workingSetMb" -Default "n/a"), `
    (Get-MapValue -Map $Thresholds -Key "cpuSeconds" -Default "n/a"), `
    (Get-MapValue -Map $Thresholds -Key "ageMinutes" -Default "n/a"), `
    (Get-MapValue -Map $Thresholds -Key "repeatedBreaches" -Default "n/a")
}

function Get-AtlasRoot {
  $opsRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
  return Split-Path -Parent $opsRoot
}

function Get-SystemGuardianPaths {
  param(
    [string]$PolicyPath
  )

  $atlasRoot = Get-AtlasRoot
  $runtimeRoot = Join-Path $atlasRoot "runtime\atlas\system-guardian"
  $stateDir = Join-Path $runtimeRoot "state"
  $logDir = Join-Path $runtimeRoot "logs"
  $reportDir = Join-Path $runtimeRoot "reports"
  $receiptDir = Join-Path $runtimeRoot "receipts"
  $backupDir = Join-Path $runtimeRoot "backups"

  $resolvedPolicyPath = if (Test-HasValue $PolicyPath) {
    $PolicyPath
  }
  else {
    Join-Path $PSScriptRoot "system-guardian.policy.json"
  }

  return @{
    atlasRoot = $atlasRoot
    runtimeRoot = $runtimeRoot
    stateDir = $stateDir
    logDir = $logDir
    reportDir = $reportDir
    receiptDir = $receiptDir
    backupDir = $backupDir
    policyPath = $resolvedPolicyPath
    breachStatePath = Join-Path $stateDir "breaches.json"
    profileStatePath = Join-Path $stateDir "active-profile.json"
    killSwitchPath = Join-Path $stateDir "disabled.flag"
    rollbackPath = Join-Path $stateDir "rollback-latest.json"
    latestRunPath = Join-Path $stateDir "latest-run.json"
    latestReceiptPath = Join-Path $receiptDir "latest.md"
  }
}

function Ensure-SystemGuardianDirectories {
  param($Paths)

  foreach ($path in @($Paths.runtimeRoot, $Paths.stateDir, $Paths.logDir, $Paths.reportDir, $Paths.receiptDir, $Paths.backupDir)) {
    if (-not (Test-Path -LiteralPath $path)) {
      New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
  }
}

function Read-JsonFile {
  param(
    [string]$Path,
    $Default = $null
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    return $Default
  }

  $raw = Get-Content -LiteralPath $Path -Raw
  if ([string]::IsNullOrWhiteSpace($raw)) {
    return $Default
  }

  return ConvertTo-PlainData -InputObject (ConvertFrom-Json -InputObject $raw)
}

function Write-JsonFile {
  param(
    [string]$Path,
    $Data
  )

  $directory = Split-Path -Parent $Path
  if (Test-HasValue $directory -and -not (Test-Path -LiteralPath $directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
  }

  $json = $Data | ConvertTo-Json -Depth 12
  Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

function Test-ValidMode {
  param(
    [string]$Mode
  )

  return @("observe", "notify", "cleanup") -contains $Mode
}

function Test-ValidAction {
  param(
    [string]$Action
  )

  return @("observe", "notify", "cleanup") -contains $Action
}

function Test-NonNegativeNumber {
  param($Value)

  if ($null -eq $Value) {
    return $false
  }

  $parsed = 0.0
  return [double]::TryParse([string]$Value, [ref]$parsed) -and $parsed -ge 0
}

function Get-ProfileThresholds {
  param(
    $Policy,
    [string]$ProfileName
  )

  return @{
    workingSetMb = Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "workingSetMb" -Rule @{}
    cpuSeconds = Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "cpuSeconds" -Rule @{}
    ageMinutes = Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "ageMinutes" -Rule @{}
    repeatedBreaches = Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "repeatedBreaches" -Rule @{}
  }
}

function Get-ProfileSummary {
  param(
    $Policy,
    [string]$ProfileName
  )

  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  $profile = Get-MapValue -Map $profiles -Key $ProfileName -Default @{}
  $mode = Get-ProfileMode -Policy $Policy -ProfileName $ProfileName -ModeOverride $null
  $summaryText = Get-MapValue -Map $profile -Key "summary" -Default ""
  $thresholds = Get-ProfileThresholds -Policy $Policy -ProfileName $ProfileName
  $cleanupCapable = @(
    Get-MapValue -Map $Policy -Key "candidates" -Default @() |
      Where-Object { (Get-MapValue -Map $_ -Key "defaultAction" -Default "notify") -eq "cleanup" }
  ).Count
  $notifyOnly = @(
    Get-MapValue -Map $Policy -Key "candidates" -Default @() |
      Where-Object { (Get-MapValue -Map $_ -Key "defaultAction" -Default "notify") -ne "cleanup" }
  ).Count

  return @{
    profile = $ProfileName
    mode = $mode
    summary = $summaryText
    thresholds = $thresholds
    thresholdSummary = Format-ThresholdSummary -Thresholds $thresholds
    cleanupCandidateCount = $cleanupCapable
    reviewCandidateCount = $notifyOnly
  }
}

function Get-AvailableProfileSummaries {
  param($Policy)

  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  $names = @($profiles.Keys | Sort-Object)
  $summaries = @()
  foreach ($name in $names) {
    $summaries += @(Get-ProfileSummary -Policy $Policy -ProfileName ([string]$name))
  }
  return $summaries
}

function Validate-SystemGuardianPolicy {
  param(
    $Policy
  )

  $errors = @()
  $version = Get-MapValue -Map $Policy -Key "version" -Default $null
  if (-not (Test-NonNegativeNumber $version)) {
    $errors += "Policy version must be a non-negative number."
  }

  $defaults = Get-MapValue -Map $Policy -Key "defaults" -Default @{}
  $defaultProfile = Get-MapValue -Map $defaults -Key "profile" -Default ""
  $defaultMode = Get-MapValue -Map $defaults -Key "mode" -Default ""
  if (-not (Test-HasValue $defaultProfile)) {
    $errors += "defaults.profile must be present."
  }
  if (-not (Test-ValidMode -Mode ([string]$defaultMode))) {
    $errors += "defaults.mode must be one of observe, notify, cleanup."
  }

  $defaultsThresholds = Get-MapValue -Map $defaults -Key "thresholds" -Default @{}
  foreach ($key in @("workingSetMb", "cpuSeconds", "ageMinutes", "repeatedBreaches")) {
    if (-not (Test-NonNegativeNumber (Get-MapValue -Map $defaultsThresholds -Key $key -Default $null))) {
      $errors += "defaults.thresholds.$key must be a non-negative number."
    }
  }

  $scheduledTask = Get-MapValue -Map $defaults -Key "scheduledTask" -Default @{}
  if (-not (Test-HasValue (Get-MapValue -Map $scheduledTask -Key "name" -Default ""))) {
    $errors += "defaults.scheduledTask.name must be present."
  }
  if (-not (Test-NonNegativeNumber (Get-MapValue -Map $scheduledTask -Key "intervalMinutes" -Default $null)) -or [double](Get-MapValue -Map $scheduledTask -Key "intervalMinutes" -Default 0) -lt 1) {
    $errors += "defaults.scheduledTask.intervalMinutes must be >= 1."
  }

  $protected = Get-MapValue -Map $Policy -Key "protected" -Default @{}
  foreach ($key in @("processNames", "commandLineContains", "browserProcessNames")) {
    $value = Get-MapValue -Map $protected -Key $key -Default @()
    if ($null -eq $value -or @($value).Count -eq 0) {
      $errors += "protected.$key must be a non-empty array."
    }
  }

  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  if ($null -eq $profiles -or @($profiles.Keys).Count -eq 0) {
    $errors += "profiles must define at least one profile."
  }
  elseif (-not (Test-MapHasKey -Map $profiles -Key $defaultProfile)) {
    $errors += "defaults.profile must reference an existing profile."
  }
  foreach ($profileName in @($profiles.Keys)) {
    $profile = Get-MapValue -Map $profiles -Key ([string]$profileName) -Default @{}
    $mode = Get-MapValue -Map $profile -Key "mode" -Default $defaultMode
    if (-not (Test-ValidMode -Mode ([string]$mode))) {
      $errors += "profiles.$profileName.mode must be one of observe, notify, cleanup."
    }
    if (-not (Test-HasValue (Get-MapValue -Map $profile -Key "summary" -Default ""))) {
      $errors += "profiles.$profileName.summary must be a non-empty string."
    }
    $thresholds = Get-MapValue -Map $profile -Key "thresholds" -Default @{}
    foreach ($key in @("workingSetMb", "cpuSeconds", "ageMinutes", "repeatedBreaches")) {
      if ((Test-MapHasKey -Map $thresholds -Key $key) -and -not (Test-NonNegativeNumber (Get-MapValue -Map $thresholds -Key $key -Default $null))) {
        $errors += "profiles.$profileName.thresholds.$key must be a non-negative number."
      }
    }
  }

  $candidateIds = @{}
  $candidates = Get-MapValue -Map $Policy -Key "candidates" -Default @()
  if ($null -eq $candidates -or @($candidates).Count -eq 0) {
    $errors += "candidates must define at least one rule."
  }
  $index = 0
  foreach ($candidate in @($candidates)) {
    $rulePath = "candidates[$index]"
    $ruleId = [string](Get-MapValue -Map $candidate -Key "id" -Default "")
    if (-not (Test-HasValue $ruleId)) {
      $errors += "$rulePath.id must be present."
    }
    elseif ($candidateIds.ContainsKey($ruleId)) {
      $errors += "$rulePath.id '$ruleId' is duplicated."
    }
    else {
      $candidateIds[$ruleId] = $true
    }
    if (-not (Test-HasValue (Get-MapValue -Map $candidate -Key "description" -Default ""))) {
      $errors += "$rulePath.description must be a non-empty string."
    }
    if (-not (Test-ValidAction -Action ([string](Get-MapValue -Map $candidate -Key "defaultAction" -Default "")))) {
      $errors += "$rulePath.defaultAction must be one of observe, notify, cleanup."
    }
    if (-not (Test-HasValue (Get-MapValue -Map $candidate -Key "operatorHint" -Default ""))) {
      $errors += "$rulePath.operatorHint must be a non-empty string."
    }
    $classification = Get-MapValue -Map $candidate -Key "classification" -Default @{}
    if (-not (Test-HasValue (Get-MapValue -Map $classification -Key "family" -Default ""))) {
      $errors += "$rulePath.classification.family must be present."
    }
    if (-not (Test-HasValue (Get-MapValue -Map $classification -Key "intent" -Default ""))) {
      $errors += "$rulePath.classification.intent must be present."
    }
    if (@(Get-MapValue -Map $candidate -Key "processNames" -Default @()).Count -eq 0 -and @(Get-MapValue -Map $candidate -Key "commandLineContains" -Default @()).Count -eq 0) {
      $errors += "$rulePath must declare processNames or commandLineContains."
    }
    $thresholds = Get-MapValue -Map $candidate -Key "thresholds" -Default @{}
    foreach ($key in @("workingSetMb", "cpuSeconds", "ageMinutes", "repeatedBreaches")) {
      if ((Test-MapHasKey -Map $thresholds -Key $key) -and -not (Test-NonNegativeNumber (Get-MapValue -Map $thresholds -Key $key -Default $null))) {
        $errors += "$rulePath.thresholds.$key must be a non-negative number."
      }
    }
    $index += 1
  }

  return $errors
}

function Get-SystemGuardianPolicy {
  param(
    [string]$PolicyPath
  )

  $policy = Read-JsonFile -Path $PolicyPath
  if ($null -eq $policy) {
    throw "System Guardian policy not found at '$PolicyPath'."
  }

  foreach ($requiredKey in @("defaults", "profiles", "protected", "candidates")) {
    if (-not (Test-MapHasKey -Map $policy -Key $requiredKey)) {
      throw "System Guardian policy is missing '$requiredKey'."
    }
  }

  $errors = Validate-SystemGuardianPolicy -Policy $policy
  if (@($errors).Count -gt 0) {
    throw "System Guardian policy validation failed: $([string]::Join('; ', $errors))"
  }

  return $policy
}

function Get-PolicyThreshold {
  param(
    $Policy,
    [string]$ProfileName,
    [string]$Key,
    $Rule
  )

  $defaults = Get-MapValue -Map (Get-MapValue -Map $Policy -Key "defaults" -Default @{}) -Key "thresholds" -Default @{}
  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  $profile = Get-MapValue -Map $profiles -Key $ProfileName -Default @{}
  $profileThresholds = Get-MapValue -Map $profile -Key "thresholds" -Default @{}
  $ruleThresholds = Get-MapValue -Map $Rule -Key "thresholds" -Default @{}

  if (Test-MapHasKey -Map $ruleThresholds -Key $Key) {
    return $ruleThresholds[$Key]
  }
  if (Test-MapHasKey -Map $profileThresholds -Key $Key) {
    return $profileThresholds[$Key]
  }
  if (Test-MapHasKey -Map $defaults -Key $Key) {
    return $defaults[$Key]
  }

  return $null
}

function Get-ActiveProfileName {
  param(
    $Policy,
    $Paths
  )

  $state = Read-JsonFile -Path $Paths.profileStatePath -Default @{}
  $stateProfile = Get-MapValue -Map $state -Key "profile"
  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}

  if ((Test-HasValue $stateProfile) -and (Test-MapHasKey -Map $profiles -Key $stateProfile)) {
    return $stateProfile
  }

  return Get-MapValue -Map (Get-MapValue -Map $Policy -Key "defaults" -Default @{}) -Key "profile" -Default "normal"
}

function Set-ActiveProfileName {
  param(
    $Policy,
    $Paths,
    [string]$ProfileName
  )

  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  if (-not (Test-MapHasKey -Map $profiles -Key $ProfileName)) {
    throw "Unknown System Guardian profile '$ProfileName'."
  }

  Write-JsonFile -Path $Paths.profileStatePath -Data @{
    profile = $ProfileName
    updatedAt = (Get-Date).ToString("o")
  }
}

function Test-KillSwitchEnabled {
  param($Paths)

  return Test-Path -LiteralPath $Paths.killSwitchPath
}

function Set-KillSwitchState {
  param(
    $Paths,
    [bool]$Disabled
  )

  if ($Disabled) {
    Set-Content -LiteralPath $Paths.killSwitchPath -Value ("disabled " + (Get-Date).ToString("o")) -Encoding UTF8
  }
  elseif (Test-Path -LiteralPath $Paths.killSwitchPath) {
    Remove-Item -LiteralPath $Paths.killSwitchPath -Force
  }
}

function Get-SystemGuardianTaskConfig {
  param($Policy)

  return Get-MapValue -Map (Get-MapValue -Map $Policy -Key "defaults" -Default @{}) -Key "scheduledTask" -Default @{}
}

function Get-ScheduledTaskSnapshot {
  param(
    $Policy
  )

  $taskConfig = Get-SystemGuardianTaskConfig -Policy $Policy
  $taskName = Get-MapValue -Map $taskConfig -Key "name" -Default "ATLAS System Guardian"
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($null -eq $task) {
    return @{
      installed = $false
      taskName = $taskName
      intervalMinutes = Get-MapValue -Map $taskConfig -Key "intervalMinutes" -Default 15
      runWithApply = $true
    }
  }

  $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
  return @{
    installed = $true
    taskName = $task.TaskName
    state = $task.State.ToString()
    lastRunTime = $taskInfo.LastRunTime.ToString("o")
    nextRunTime = $taskInfo.NextRunTime.ToString("o")
    intervalMinutes = Get-MapValue -Map $taskConfig -Key "intervalMinutes" -Default 15
    runWithApply = $true
  }
}

function Save-RollbackSnapshot {
  param(
    $Policy,
    $Paths,
    [string]$Reason
  )

  $snapshot = @{
    capturedAt = (Get-Date).ToString("o")
    reason = $Reason
    activeProfile = Get-ActiveProfileName -Policy $Policy -Paths $Paths
    killSwitchEnabled = Test-KillSwitchEnabled -Paths $Paths
    scheduledTask = Get-ScheduledTaskSnapshot -Policy $Policy
  }

  Write-JsonFile -Path $Paths.rollbackPath -Data $snapshot

  $backupPath = Join-Path $Paths.backupDir ("rollback-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
  Write-JsonFile -Path $backupPath -Data $snapshot

  return $snapshot
}

function Get-ScheduledTaskCommandLine {
  param(
    [string]$PolicyPath
  )

  $scriptPath = Join-Path $PSScriptRoot "system-guardian-run.ps1"
  $arguments = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    "`"$scriptPath`"",
    "-Apply"
  )

  if (Test-HasValue $PolicyPath) {
    $arguments += @("-PolicyPath", "`"$PolicyPath`"")
  }

  return [string]::Join(" ", $arguments)
}

function Register-SystemGuardianTask {
  param(
    $Policy,
    $Paths,
    [int]$IntervalMinutes
  )

  $taskConfig = Get-SystemGuardianTaskConfig -Policy $Policy
  $taskName = Get-MapValue -Map $taskConfig -Key "name" -Default "ATLAS System Guardian"
  $resolvedInterval = if ($IntervalMinutes -gt 0) { $IntervalMinutes } else { [int](Get-MapValue -Map $taskConfig -Key "intervalMinutes" -Default 15) }
  $currentUser = if (Test-HasValue $env:USERDOMAIN) { "$($env:USERDOMAIN)\$($env:USERNAME)" } else { $env:USERNAME }
  $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes $resolvedInterval) -RepetitionDuration (New-TimeSpan -Days 3650)
  $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
  $action = New-ScheduledTaskAction -Execute (Join-Path $PSHOME "powershell.exe") -Argument (Get-ScheduledTaskCommandLine -PolicyPath $Paths.policyPath) -WorkingDirectory $Paths.atlasRoot

  Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

  return Get-ScheduledTaskSnapshot -Policy $Policy
}

function Unregister-SystemGuardianTask {
  param(
    $Policy
  )

  $taskConfig = Get-SystemGuardianTaskConfig -Policy $Policy
  $taskName = Get-MapValue -Map $taskConfig -Key "name" -Default "ATLAS System Guardian"
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($null -ne $task) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
  }
}

function Get-StringDigest {
  param(
    [string]$Text
  )

  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
  }
  finally {
    $sha.Dispose()
  }
}

function Get-ProcessInventory {
  $cimById = @{}
  foreach ($cimProcess in Get-CimInstance -ClassName Win32_Process) {
    $cimById[[int]$cimProcess.ProcessId] = $cimProcess
  }

  $inventory = @()
  foreach ($process in Get-Process) {
    $commandLine = ""
    if ($cimById.ContainsKey([int]$process.Id)) {
      $commandLine = [string]$cimById[[int]$process.Id].CommandLine
    }

    $startTime = $null
    try {
      $startTime = $process.StartTime
    }
    catch {
      $startTime = $null
    }

    $cpuSeconds = 0
    if ($null -ne $process.CPU) {
      $cpuSeconds = [double]$process.CPU
    }

    $mainWindowHandle = 0
    if ($null -ne $process.MainWindowHandle) {
      $mainWindowHandle = [int64]$process.MainWindowHandle
    }

    $inventory += @(@{
      id = [int]$process.Id
      name = [string]$process.ProcessName
      commandLine = $commandLine
      workingSetMb = [math]::Round(($process.WorkingSet64 / 1MB), 1)
      cpuSeconds = [math]::Round($cpuSeconds, 1)
      ageMinutes = if ($null -ne $startTime) { [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1) } else { $null }
      startTime = if ($null -ne $startTime) { $startTime.ToString("o") } else { $null }
      mainWindowHandle = $mainWindowHandle
    })
  }

  return $inventory
}

function Test-CommandPatternMatch {
  param(
    [string]$CommandLine,
    $Patterns
  )

  $patternList = @($Patterns)
  if ($null -eq $Patterns -or $patternList.Count -eq 0) {
    return $true
  }

  foreach ($pattern in $patternList) {
    if ([string]::IsNullOrWhiteSpace([string]$pattern)) {
      continue
    }
    if ($CommandLine -like ("*" + [string]$pattern + "*")) {
      return $true
    }
  }

  return $false
}

function Test-NamePatternMatch {
  param(
    [string]$ProcessName,
    $Names
  )

  $nameList = @($Names)
  if ($null -eq $Names -or $nameList.Count -eq 0) {
    return $true
  }

  foreach ($candidate in $nameList) {
    if ([string]::Equals([string]$ProcessName, [string]$candidate, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }

  return $false
}

function Test-ProtectedProcess {
  param(
    $Policy,
    $Process
  )

  if ([int]$Process.id -eq [int]$PID) {
    return $true
  }

  $protected = Get-MapValue -Map $Policy -Key "protected" -Default @{}
  $protectedNames = Get-MapValue -Map $protected -Key "processNames" -Default @()
  if (Test-NamePatternMatch -ProcessName $Process.name -Names $protectedNames) {
    return $true
  }

  $protectedPatterns = Get-MapValue -Map $protected -Key "commandLineContains" -Default @()
  if (Test-CommandPatternMatch -CommandLine $Process.commandLine -Patterns $protectedPatterns) {
    return $true
  }

  return $false
}

function Test-BrowserProcess {
  param(
    $Policy,
    $Process
  )

  $protected = Get-MapValue -Map $Policy -Key "protected" -Default @{}
  $browserNames = Get-MapValue -Map $protected -Key "browserProcessNames" -Default @()
  return Test-NamePatternMatch -ProcessName $Process.name -Names $browserNames
}

function Get-RuleClassification {
  param(
    $Rule
  )

  $classification = Get-MapValue -Map $Rule -Key "classification" -Default @{}
  $family = [string](Get-MapValue -Map $classification -Key "family" -Default "general")
  $intent = [string](Get-MapValue -Map $classification -Key "intent" -Default "review")
  return @{
    family = $family
    intent = $intent
    label = "$family/$intent"
    operatorHint = [string](Get-MapValue -Map $Rule -Key "operatorHint" -Default "")
  }
}

function Get-ReasonSummary {
  param(
    [string[]]$ReasonCodes
  )

  $codes = ConvertTo-StringArray -Value $ReasonCodes
  if ($codes.Count -eq 0) {
    return "no extra gates"
  }

  return [string]::Join(", ", $codes)
}

function Get-SystemGuardianReviewHelpers {
  param(
    $Findings
  )

  $helpers = @()
  $backgroundFamilies = @("browser", "communication")
  $startupFamilies = @("launcher")

  $backgroundCandidates = @($Findings | Where-Object { $backgroundFamilies -contains (Get-MapValue -Map $_.classification -Key "family" -Default "") })
  if ($backgroundCandidates.Count -gt 0) {
    $names = @($backgroundCandidates | ForEach-Object { $_.process.name } | Sort-Object -Unique)
    $helpers += @(
      @{
        category = "background-review"
        summary = "Background review: {0} candidate(s) across {1}." -f $backgroundCandidates.Count, ([string]::Join(", ", $names))
      }
    )
  }

  $startupCandidates = @($Findings | Where-Object { $startupFamilies -contains (Get-MapValue -Map $_.classification -Key "family" -Default "") })
  if ($startupCandidates.Count -gt 0) {
    $names = @($startupCandidates | ForEach-Object { $_.process.name } | Sort-Object -Unique)
    $helpers += @(
      @{
        category = "startup-review"
        summary = "Startup review: {0} launcher/background helper candidate(s) across {1}." -f $startupCandidates.Count, ([string]::Join(", ", $names))
      }
    )
  }

  return $helpers
}

function Get-RuleMatchKey {
  param(
    $Rule,
    $Process
  )

  $seed = "{0}|{1}|{2}" -f (Get-MapValue -Map $Rule -Key "id" -Default "rule"), $Process.name, $Process.commandLine
  return Get-StringDigest -Text $seed
}

function Get-ProfileMode {
  param(
    $Policy,
    [string]$ProfileName,
    [string]$ModeOverride
  )

  if (Test-HasValue $ModeOverride) {
    return $ModeOverride
  }

  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  $profile = Get-MapValue -Map $profiles -Key $ProfileName -Default @{}
  $mode = Get-MapValue -Map $profile -Key "mode"
  if (Test-HasValue $mode) {
    return $mode
  }

  return Get-MapValue -Map (Get-MapValue -Map $Policy -Key "defaults" -Default @{}) -Key "mode" -Default "observe"
}

function Evaluate-SystemGuardianRun {
  param(
    $Policy,
    $Paths,
    [string]$ProfileName,
    [string]$ModeOverride
  )

  $profiles = Get-MapValue -Map $Policy -Key "profiles" -Default @{}
  if (-not (Test-MapHasKey -Map $profiles -Key $ProfileName)) {
    throw "Unknown System Guardian profile '$ProfileName'."
  }

  $mode = Get-ProfileMode -Policy $Policy -ProfileName $ProfileName -ModeOverride $ModeOverride
  $profileSummary = Get-ProfileSummary -Policy $Policy -ProfileName $ProfileName
  $breachState = Read-JsonFile -Path $Paths.breachStatePath -Default @{ items = @{} }
  $breachItems = Get-MapValue -Map $breachState -Key "items" -Default @{}
  $now = Get-Date
  $inventory = Get-ProcessInventory
  $matchedKeys = @{}
  $findings = @()

  foreach ($process in $inventory) {
    if (Test-ProtectedProcess -Policy $Policy -Process $process) {
      continue
    }

    foreach ($rule in (Get-MapValue -Map $Policy -Key "candidates" -Default @())) {
      if (-not (Test-NamePatternMatch -ProcessName $process.name -Names (Get-MapValue -Map $rule -Key "processNames" -Default @()))) {
        continue
      }
      if (-not (Test-CommandPatternMatch -CommandLine $process.commandLine -Patterns (Get-MapValue -Map $rule -Key "commandLineContains" -Default @()))) {
        continue
      }

      $minWorkingSetMb = [double](Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "workingSetMb" -Rule $rule)
      $minCpuSeconds = [double](Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "cpuSeconds" -Rule $rule)
      $minAgeMinutes = [double](Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "ageMinutes" -Rule $rule)
      $minRepeatedBreaches = [int](Get-PolicyThreshold -Policy $Policy -ProfileName $ProfileName -Key "repeatedBreaches" -Rule $rule)
      $withinMemory = ($null -eq $minWorkingSetMb) -or ([double]$process.workingSetMb -ge $minWorkingSetMb)
      $withinCpu = ($null -eq $minCpuSeconds) -or ([double]$process.cpuSeconds -ge $minCpuSeconds)
      $withinAge = ($null -eq $minAgeMinutes) -or (($null -ne $process.ageMinutes) -and ([double]$process.ageMinutes -ge $minAgeMinutes))

      if (-not ($withinMemory -and $withinCpu -and $withinAge)) {
        continue
      }

      $matchKey = Get-RuleMatchKey -Rule $rule -Process $process
      $matchedKeys[$matchKey] = $true
      $prior = Get-MapValue -Map $breachItems -Key $matchKey -Default @{}
      $breachCount = [int](Get-MapValue -Map $prior -Key "count" -Default 0) + 1
      $breachItems[$matchKey] = @{
        count = $breachCount
        firstSeen = Get-MapValue -Map $prior -Key "firstSeen" -Default $now.ToString("o")
        lastSeen = $now.ToString("o")
        processName = $process.name
        ruleId = Get-MapValue -Map $rule -Key "id" -Default "candidate"
      }

      $defaultAction = Get-MapValue -Map $rule -Key "defaultAction" -Default "notify"
      $action = switch ($mode) {
        "observe" { "observe"; break }
        "notify" { if ($defaultAction -eq "cleanup") { "notify" } else { $defaultAction }; break }
        "cleanup" { $defaultAction; break }
        default { "observe" }
      }

      $notes = @()
      $reasonCodes = @(
        "mode:$mode",
        "defaultAction:$defaultAction"
      )
      $cleanupAllowed = [bool](Get-MapValue -Map $rule -Key "cleanupAllowed" -Default ($defaultAction -eq "cleanup"))
      if (Test-BrowserProcess -Policy $Policy -Process $process) {
        $browserCleanupAllowed = [bool](Get-MapValue -Map $rule -Key "browserCleanupAllowed" -Default $false)
        $requiresNoMainWindow = [bool](Get-MapValue -Map $rule -Key "requireNoMainWindow" -Default $true)
        if (-not $browserCleanupAllowed) {
          $notes += "browser-default-notify"
          $reasonCodes += "browser-background-review-only"
          $action = if ($mode -eq "observe") { "observe" } else { "notify" }
          $cleanupAllowed = $false
        }
        elseif ($requiresNoMainWindow -and [int64]$process.mainWindowHandle -ne 0) {
          $notes += "browser-main-window-open"
          $reasonCodes += "main-window-open"
          $action = if ($mode -eq "observe") { "observe" } else { "notify" }
          $cleanupAllowed = $false
        }
      }

      $meetsRepeatedThreshold = $breachCount -ge $minRepeatedBreaches
      if (-not $meetsRepeatedThreshold) {
        $notes += "breach-count-$breachCount-of-$minRepeatedBreaches"
        $reasonCodes += "awaiting-repeated-breach-threshold"
      }
      else {
        $reasonCodes += "repeated-breach-threshold-met"
      }

      if ($defaultAction -eq "cleanup" -and $mode -ne "cleanup") {
        $reasonCodes += "cleanup-downgraded-by-profile"
      }
      elseif ($action -eq "cleanup") {
        $reasonCodes += "cleanup-authorized"
      }
      else {
        $reasonCodes += "review-only"
      }

      $findings += @(@{
        ruleId = Get-MapValue -Map $rule -Key "id" -Default "candidate"
        description = Get-MapValue -Map $rule -Key "description" -Default ""
        classification = Get-RuleClassification -Rule $rule
        process = $process
        thresholds = @{
          workingSetMb = $minWorkingSetMb
          cpuSeconds = $minCpuSeconds
          ageMinutes = $minAgeMinutes
          repeatedBreaches = $minRepeatedBreaches
        }
        breachCount = $breachCount
        meetsRepeatedThreshold = $meetsRepeatedThreshold
        action = $action
        cleanupAllowed = $cleanupAllowed
        notes = $notes
        reasonCodes = $reasonCodes
        reasonSummary = Get-ReasonSummary -ReasonCodes $reasonCodes
      })
    }
  }

  $nextBreachItems = @{}
  foreach ($key in $breachItems.Keys) {
    if ($matchedKeys.ContainsKey($key)) {
      $nextBreachItems[$key] = $breachItems[$key]
    }
  }
  Write-JsonFile -Path $Paths.breachStatePath -Data @{
    updatedAt = $now.ToString("o")
    items = $nextBreachItems
  }

  return @{
    ranAt = $now.ToString("o")
    profile = $ProfileName
    mode = $mode
    profileSummary = $profileSummary
    killSwitchEnabled = Test-KillSwitchEnabled -Paths $Paths
    findings = @($findings)
    reviewHelpers = @(Get-SystemGuardianReviewHelpers -Findings $findings)
  }
}

function Invoke-SystemGuardianRun {
  param(
    $Policy,
    $Paths,
    [string]$ProfileName,
    [string]$ModeOverride,
    [bool]$ApplyChanges
  )

  $evaluation = Evaluate-SystemGuardianRun -Policy $Policy -Paths $Paths -ProfileName $ProfileName -ModeOverride $ModeOverride
  if ($evaluation.killSwitchEnabled) {
    $disabledRun = @{
      ranAt = $evaluation.ranAt
      profile = $evaluation.profile
      mode = $evaluation.mode
      profileSummary = $evaluation.profileSummary
      killSwitchEnabled = $true
      applyChanges = $ApplyChanges
      skipped = $true
      findings = @()
      actions = @()
      reviewHelpers = @()
      summary = @{
        findingCount = 0
        cleanupCount = 0
        notifyCount = 0
        observeCount = 0
      }
    }
    Save-SystemGuardianRun -Paths $Paths -Run $disabledRun
    return $disabledRun
  }

  $actions = @()
  foreach ($finding in $evaluation.findings) {
    $shouldCleanup = $ApplyChanges -and $evaluation.mode -eq "cleanup" -and $finding.action -eq "cleanup" -and $finding.cleanupAllowed -and $finding.meetsRepeatedThreshold
    if ($shouldCleanup) {
      try {
        Stop-Process -Id ([int]$finding.process.id) -Force -ErrorAction Stop
        $actions += @(@{
          action = "cleanup"
          result = "stopped"
          processId = $finding.process.id
          processName = $finding.process.name
          ruleId = $finding.ruleId
        })
      }
      catch {
        $actions += @(@{
          action = "cleanup"
          result = "failed"
          processId = $finding.process.id
          processName = $finding.process.name
          ruleId = $finding.ruleId
          error = $_.Exception.Message
        })
      }
    }
    elseif ($finding.action -eq "cleanup" -and -not $finding.meetsRepeatedThreshold) {
      $actions += @(@{
        action = "cleanup"
        result = "deferred"
        processId = $finding.process.id
        processName = $finding.process.name
        ruleId = $finding.ruleId
      })
    }
    elseif ($finding.action -eq "notify") {
      $actions += @(@{
        action = "notify"
        result = "logged"
        processId = $finding.process.id
        processName = $finding.process.name
        ruleId = $finding.ruleId
      })
    }
    else {
      $actions += @(@{
        action = "observe"
        result = "logged"
        processId = $finding.process.id
        processName = $finding.process.name
        ruleId = $finding.ruleId
      })
    }
  }

  $run = @{
    ranAt = $evaluation.ranAt
    profile = $evaluation.profile
    mode = $evaluation.mode
    profileSummary = $evaluation.profileSummary
    killSwitchEnabled = $false
    applyChanges = $ApplyChanges
    skipped = $false
    findings = @($evaluation.findings)
    actions = @($actions)
    reviewHelpers = @($evaluation.reviewHelpers)
    summary = @{
      findingCount = @($evaluation.findings).Count
      cleanupCount = (@($actions | Where-Object { $_.action -eq "cleanup" -and $_.result -eq "stopped" })).Count
      notifyCount = (@($actions | Where-Object { $_.action -eq "notify" })).Count
      observeCount = (@($actions | Where-Object { $_.action -eq "observe" })).Count
    }
  }

  Save-SystemGuardianRun -Paths $Paths -Run $run
  return $run
}

function Save-SystemGuardianRun {
  param(
    $Paths,
    $Run
  )

  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $logPath = Join-Path $Paths.logDir ("run-" + $stamp + ".json")
  $reportPath = Join-Path $Paths.reportDir ("run-" + $stamp + ".txt")
  $receiptPath = Join-Path $Paths.receiptDir ("run-" + $stamp + ".md")

  Write-JsonFile -Path $logPath -Data $Run
  Write-JsonFile -Path $Paths.latestRunPath -Data $Run

  $reportLines = @(
    "System Guardian Run",
    "ranAt: $($Run.ranAt)",
    "profile: $($Run.profile)",
    "mode: $($Run.mode)",
    "profileSummary: $($Run.profileSummary.summary)",
    "thresholds: $($Run.profileSummary.thresholdSummary)",
    "applyChanges: $($Run.applyChanges)",
    "killSwitchEnabled: $($Run.killSwitchEnabled)",
    "findings: $($Run.summary.findingCount)",
    "cleanupCount: $($Run.summary.cleanupCount)",
    "notifyCount: $($Run.summary.notifyCount)",
    "observeCount: $($Run.summary.observeCount)"
  )
  foreach ($finding in $Run.findings) {
    $reportLines += ("- [{0}] pid={1} name={2} class={3} ws={4}MB cpu={5}s age={6}m action={7} breaches={8} reasons={9}" -f $finding.ruleId, $finding.process.id, $finding.process.name, $finding.classification.label, $finding.process.workingSetMb, $finding.process.cpuSeconds, $finding.process.ageMinutes, $finding.action, $finding.breachCount, $finding.reasonSummary)
  }
  Set-Content -LiteralPath $reportPath -Value $reportLines -Encoding UTF8

  $receiptLines = @(
    "# ATLAS System Guardian Receipt",
    "",
    "- Ran At: $($Run.ranAt)",
    "- Profile: $($Run.profile)",
    "- Mode: $($Run.mode)",
    "- Profile Summary: $($Run.profileSummary.summary)",
    "- Thresholds: $($Run.profileSummary.thresholdSummary)",
    "- Apply Changes: $($Run.applyChanges)",
    "- Kill Switch Enabled: $($Run.killSwitchEnabled)",
    "- Findings: $($Run.summary.findingCount)",
    "- Cleanup Count: $($Run.summary.cleanupCount)",
    "- Notify Count: $($Run.summary.notifyCount)",
    "- Observe Count: $($Run.summary.observeCount)"
  )

  if (@($Run.reviewHelpers).Count -gt 0) {
    $receiptLines += @("", "## Review Helpers", "")
    foreach ($helper in $Run.reviewHelpers) {
      $receiptLines += "- $($helper.summary)"
    }
  }

  $receiptLines += @("", "## Findings", "")
  if (@($Run.findings).Count -eq 0) {
    $receiptLines += "- No findings."
  }
  else {
    foreach ($finding in $Run.findings) {
      $receiptLines += "- Rule $($finding.ruleId) on $($finding.process.name) (pid=$($finding.process.id)) classified as $($finding.classification.label) with action $($finding.action). Reasons: $($finding.reasonSummary)."
      $receiptLines += "  Hint: $($finding.classification.operatorHint)"
    }
  }

  $receiptLines += @("", "## Actions", "")
  if (@($Run.actions).Count -eq 0) {
    $receiptLines += "- No actions."
  }
  else {
    foreach ($action in $Run.actions) {
      $resultText = if (Test-HasValue (Get-MapValue -Map $action -Key "error" -Default "")) {
        "$($action.result): $($action.error)"
      }
      else {
        [string]$action.result
      }
      $receiptLines += "- $($action.action) on $($action.processName) (pid=$($action.processId)) -> $resultText"
    }
  }

  Set-Content -LiteralPath $receiptPath -Value $receiptLines -Encoding UTF8
  Set-Content -LiteralPath $Paths.latestReceiptPath -Value $receiptLines -Encoding UTF8
}

function Write-SystemGuardianRunSummary {
  param(
    $Run
  )

  Write-Output ("profile={0} mode={1} apply={2} findings={3} cleanup={4} notify={5} observe={6} killSwitch={7}" -f $Run.profile, $Run.mode, $Run.applyChanges, $Run.summary.findingCount, $Run.summary.cleanupCount, $Run.summary.notifyCount, $Run.summary.observeCount, $Run.killSwitchEnabled)
  Write-Output ("profileSummary={0}" -f $Run.profileSummary.summary)
  Write-Output ("thresholds={0}" -f $Run.profileSummary.thresholdSummary)
  foreach ($finding in $Run.findings) {
    $noteText = if (@($finding.notes).Count -gt 0) { [string]::Join(",", @($finding.notes)) } else { "none" }
    Write-Output ("[{0}] pid={1} name={2} class={3} action={4} ws={5}MB cpu={6}s age={7}m breaches={8} notes={9} reasons={10}" -f $finding.ruleId, $finding.process.id, $finding.process.name, $finding.classification.label, $finding.action, $finding.process.workingSetMb, $finding.process.cpuSeconds, $finding.process.ageMinutes, $finding.breachCount, $noteText, $finding.reasonSummary)
  }
  foreach ($helper in @($Run.reviewHelpers)) {
    Write-Output ("reviewHelper={0}" -f $helper.summary)
  }
}

function Get-SystemGuardianStatus {
  param(
    $Policy,
    $Paths
  )

  $taskSnapshot = Get-ScheduledTaskSnapshot -Policy $Policy
  $latestRun = Read-JsonFile -Path $Paths.latestRunPath -Default @{}
  return @{
    profile = Get-ActiveProfileName -Policy $Policy -Paths $Paths
    profileSummary = Get-ProfileSummary -Policy $Policy -ProfileName (Get-ActiveProfileName -Policy $Policy -Paths $Paths)
    availableProfiles = Get-AvailableProfileSummaries -Policy $Policy
    killSwitchEnabled = Test-KillSwitchEnabled -Paths $Paths
    policyPath = $Paths.policyPath
    runtimeRoot = $Paths.runtimeRoot
    scheduledTask = $taskSnapshot
    latestRun = $latestRun
    latestReceiptPath = $Paths.latestReceiptPath
    reviewHelpers = if ($latestRun -and (Test-MapHasKey -Map $latestRun -Key "reviewHelpers")) { @($latestRun.reviewHelpers) } else { @() }
  }
}

function Restore-SystemGuardianRollback {
  param(
    $Policy,
    $Paths
  )

  $snapshot = Read-JsonFile -Path $Paths.rollbackPath
  if ($null -eq $snapshot) {
    throw "No rollback snapshot is available."
  }

  $snapshotProfile = Get-MapValue -Map $snapshot -Key "activeProfile" -Default (Get-ActiveProfileName -Policy $Policy -Paths $Paths)
  Set-ActiveProfileName -Policy $Policy -Paths $paths -ProfileName $snapshotProfile
  Set-KillSwitchState -Paths $Paths -Disabled ([bool](Get-MapValue -Map $snapshot -Key "killSwitchEnabled" -Default $false))

  $scheduledTask = Get-MapValue -Map $snapshot -Key "scheduledTask" -Default @{}
  if ([bool](Get-MapValue -Map $scheduledTask -Key "installed" -Default $false)) {
    Register-SystemGuardianTask -Policy $Policy -Paths $Paths -IntervalMinutes ([int](Get-MapValue -Map $scheduledTask -Key "intervalMinutes" -Default 15)) | Out-Null
  }
  else {
    Unregister-SystemGuardianTask -Policy $Policy
  }

  return @{
    restoredAt = (Get-Date).ToString("o")
    snapshot = $snapshot
    currentStatus = Get-SystemGuardianStatus -Policy $Policy -Paths $Paths
  }
}
