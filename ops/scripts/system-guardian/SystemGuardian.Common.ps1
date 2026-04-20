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
    backupDir = $backupDir
    policyPath = $resolvedPolicyPath
    breachStatePath = Join-Path $stateDir "breaches.json"
    profileStatePath = Join-Path $stateDir "active-profile.json"
    killSwitchPath = Join-Path $stateDir "disabled.flag"
    rollbackPath = Join-Path $stateDir "rollback-latest.json"
    latestRunPath = Join-Path $stateDir "latest-run.json"
  }
}

function Ensure-SystemGuardianDirectories {
  param($Paths)

  foreach ($path in @($Paths.runtimeRoot, $Paths.stateDir, $Paths.logDir, $Paths.reportDir, $Paths.backupDir)) {
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
      $cleanupAllowed = [bool](Get-MapValue -Map $rule -Key "cleanupAllowed" -Default ($defaultAction -eq "cleanup"))
      if (Test-BrowserProcess -Policy $Policy -Process $process) {
        $browserCleanupAllowed = [bool](Get-MapValue -Map $rule -Key "browserCleanupAllowed" -Default $false)
        $requiresNoMainWindow = [bool](Get-MapValue -Map $rule -Key "requireNoMainWindow" -Default $true)
        if (-not $browserCleanupAllowed) {
          $notes += "browser-default-notify"
          $action = if ($mode -eq "observe") { "observe" } else { "notify" }
          $cleanupAllowed = $false
        }
        elseif ($requiresNoMainWindow -and [int64]$process.mainWindowHandle -ne 0) {
          $notes += "browser-main-window-open"
          $action = if ($mode -eq "observe") { "observe" } else { "notify" }
          $cleanupAllowed = $false
        }
      }

      $meetsRepeatedThreshold = $breachCount -ge $minRepeatedBreaches
      if (-not $meetsRepeatedThreshold) {
        $notes += "breach-count-$breachCount-of-$minRepeatedBreaches"
      }

      $findings += @(@{
        ruleId = Get-MapValue -Map $rule -Key "id" -Default "candidate"
        description = Get-MapValue -Map $rule -Key "description" -Default ""
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
    killSwitchEnabled = Test-KillSwitchEnabled -Paths $Paths
    findings = $findings
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
      killSwitchEnabled = $true
      applyChanges = $ApplyChanges
      skipped = $true
      findings = @()
      actions = @()
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
    killSwitchEnabled = $false
    applyChanges = $ApplyChanges
    skipped = $false
    findings = $evaluation.findings
    actions = $actions
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

  Write-JsonFile -Path $logPath -Data $Run
  Write-JsonFile -Path $Paths.latestRunPath -Data $Run

  $reportLines = @(
    "System Guardian Run",
    "ranAt: $($Run.ranAt)",
    "profile: $($Run.profile)",
    "mode: $($Run.mode)",
    "applyChanges: $($Run.applyChanges)",
    "killSwitchEnabled: $($Run.killSwitchEnabled)",
    "findings: $($Run.summary.findingCount)",
    "cleanupCount: $($Run.summary.cleanupCount)",
    "notifyCount: $($Run.summary.notifyCount)",
    "observeCount: $($Run.summary.observeCount)"
  )
  foreach ($finding in $Run.findings) {
    $reportLines += ("- [{0}] pid={1} name={2} ws={3}MB cpu={4}s age={5}m action={6} breaches={7}" -f $finding.ruleId, $finding.process.id, $finding.process.name, $finding.process.workingSetMb, $finding.process.cpuSeconds, $finding.process.ageMinutes, $finding.action, $finding.breachCount)
  }
  Set-Content -LiteralPath $reportPath -Value $reportLines -Encoding UTF8
}

function Write-SystemGuardianRunSummary {
  param(
    $Run
  )

  Write-Output ("profile={0} mode={1} apply={2} findings={3} cleanup={4} notify={5} observe={6} killSwitch={7}" -f $Run.profile, $Run.mode, $Run.applyChanges, $Run.summary.findingCount, $Run.summary.cleanupCount, $Run.summary.notifyCount, $Run.summary.observeCount, $Run.killSwitchEnabled)
  foreach ($finding in $Run.findings) {
    $noteText = if (@($finding.notes).Count -gt 0) { [string]::Join(",", @($finding.notes)) } else { "none" }
    Write-Output ("[{0}] pid={1} name={2} action={3} ws={4}MB cpu={5}s age={6}m breaches={7} notes={8}" -f $finding.ruleId, $finding.process.id, $finding.process.name, $finding.action, $finding.process.workingSetMb, $finding.process.cpuSeconds, $finding.process.ageMinutes, $finding.breachCount, $noteText)
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
    killSwitchEnabled = Test-KillSwitchEnabled -Paths $Paths
    policyPath = $Paths.policyPath
    runtimeRoot = $Paths.runtimeRoot
    scheduledTask = $taskSnapshot
    latestRun = $latestRun
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
