[CmdletBinding(DefaultParameterSetName = 'Source')]
param(
  [Parameter(Mandatory = $true, ParameterSetName = 'Source')][switch]$SourceOnlyValidate,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][ValidateSet('Prepare', 'Rollback', 'Watchdog')][string]$Mode,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][string]$PrivateSourcePath,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedPrivateSourceSha256,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][string]$StatePath,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][switch]$ExecuteProtected,
  [Parameter(ParameterSetName = 'Execute')][switch]$ReplayExactRolledBack
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$script:HostScriptPath = $PSCommandPath
$Root = [IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot, '..', '..'))
$Runtime = Join-Path $Root 'runtime\atlas'
$Secrets = Join-Path $Root 'secrets'
$PacketRoot = Join-Path $Secrets 'packet\mazer-master-preparation-r017'
$Materializer = Join-Path $PSScriptRoot 'materialize_supabase_mazer_master_preparation_r017.mjs'
$Fence = Join-Path $PSScriptRoot 'invoke_supabase_mazer_master_cutover_data_fence_r001.ps1'
$FenceClassifier = Join-Path $PSScriptRoot 'classify_supabase_mazer_master_cutover_data_fence_r001.mjs'
$ExpectedHookUri = 'pg-functions://postgres/mazer/mazer_before_user_created'
$Legacy = 'geknvnrmktchljnyddwp'
$Master = 'bxtcuhkotumitoqtrcej'
$ApiBase = 'https://api.supabase.com'
$RollbackDeadlineSeconds = 600
$HardFenceLeaseSeconds = 900
$Phases = @(
  'PREFLIGHT','FENCE_APPLYING','FENCE_PAUSED','MASTER_FENCE_APPLYING','MASTER_FENCED',
  'M1_APPLYING','M1_APPLIED','M2_APPLYING','M2_APPLIED','MASTER_REFENCE_APPLYING','MASTER_REFENCED',
  'AUTH_APPLYING','AUTH_APPLIED','RESET_QUARANTINE_APPLYING','RESET_QUARANTINE_SEALED','DELTA_APPLYING','DELTA_APPLIED',
  'M3_APPLYING','M3_APPLIED','M4_APPLYING','M4_APPLIED','POSTVERIFYING','POSTVERIFIED','HOOK_ACTIVATING','HOOK_ACTIVE',
  'QA_APPLYING','QA_COMPLETE','QA_CLEANING','QA_CLEAN',
  'LEGACY_RESTORING','LEGACY_RESTORED','PREPARATION_COMPLETE','ROLLBACK_DISABLING_HOOK',
  'ROLLBACK_TARGET_RESTORING','ROLLBACK_LEGACY_RESTORING','ROLLED_BACK','AMBIGUOUS_HOLD'
)

function Get-Sha256([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'HASH_TARGET_MISSING' }
  $stream = [IO.File]::OpenRead($Path)
  try {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
  }
  finally { $stream.Dispose() }
}

function Get-TextSha256([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($(if ($null -eq $Value) { '' } else { $Value }))
  try {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
  }
  finally { [Array]::Clear($bytes, 0, $bytes.Length) }
}

function Assert-Under([string]$Path, [string]$Boundary) {
  $candidate = [IO.Path]::GetFullPath($Path)
  $rootPath = [IO.Path]::GetFullPath($Boundary).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
  if (-not $candidate.StartsWith($rootPath, [StringComparison]::OrdinalIgnoreCase)) { throw 'PATH_SCOPE' }
  return $candidate
}

function Assert-NoReparse([string]$Path, [string]$Boundary) {
  $candidate = [IO.Path]::GetFullPath($Path)
  $stop = [IO.Path]::GetFullPath($Boundary).TrimEnd('\', '/')
  while ($true) {
    if (Test-Path -LiteralPath $candidate) {
      if (((Get-Item -LiteralPath $candidate -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'REPARSE_POINT' }
    }
    if ($candidate.TrimEnd('\', '/').Equals($stop, [StringComparison]::OrdinalIgnoreCase)) { return }
    $parent = Split-Path -Parent $candidate
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -ceq $candidate) { throw 'PATH_BOUNDARY' }
    $candidate = $parent
  }
}

function Find-MazerRepository {
  $candidate = [IO.DirectoryInfo][IO.Path]::GetFullPath($Root)
  while ($null -ne $candidate) {
    $repository = Join-Path $candidate.FullName 'repos\mazer'
    if (Test-Path -LiteralPath (Join-Path $repository '.git')) {
      return [IO.Path]::GetFullPath($repository)
    }
    $candidate = $candidate.Parent
  }
  throw 'MAZER_REPOSITORY_MISSING'
}

function ConvertTo-SafeJson([object]$Value) {
  $json = $Value | ConvertTo-Json -Compress -Depth 10
  if ($json -match '(?i)password|access[_-]?token|refresh[_-]?token|service[_-]?role|sb_secret_|postgres(?:ql)?://|@') { throw 'OUTPUT_DISCLOSURE' }
  return $json
}

function Write-Result([string]$Result, [Collections.IDictionary]$Extra = @{}) {
  $value = [ordered]@{ schema = 'atlas.supabase.mazer-master-preparation-host-result.r017.v1'; result = $Result; legacy_project_ref = $Legacy; master_project_ref = $Master; raw_records_emitted = $false; pii_emitted = $false; secrets_emitted = $false; environment_changes = 0; deployments = 0; production_changes = 0 }
  foreach ($key in $Extra.Keys) { $value[$key] = $Extra[$key] }
  [Console]::Out.WriteLine((ConvertTo-SafeJson $value))
}

function ConvertTo-ProcessArgument([string]$Argument) {
  if ([string]::IsNullOrEmpty($Argument)) { return '""' }
  if ($Argument -notmatch '[\s"]') { return $Argument }
  return '"' + ($Argument -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Invoke-Child([string]$FileName, [string[]]$Arguments, [Collections.IDictionary]$Environment = @{}, [int]$TimeoutMs = 120000) {
  $start = New-Object Diagnostics.ProcessStartInfo
  $start.FileName = $FileName
  $start.UseShellExecute = $false
  $start.CreateNoWindow = $true
  $start.RedirectStandardOutput = $true
  $start.RedirectStandardError = $true
  if ($null -ne $start.PSObject.Properties['ArgumentList']) {
    foreach ($argument in $Arguments) { [void]$start.ArgumentList.Add([string]$argument) }
  }
  else {
    $start.Arguments = (($Arguments | ForEach-Object { ConvertTo-ProcessArgument ([string]$_) }) -join ' ')
  }
  foreach ($key in $Environment.Keys) { $start.EnvironmentVariables[[string]$key] = [string]$Environment[$key] }
  $process = New-Object Diagnostics.Process
  $process.StartInfo = $start
  try {
    if (-not $process.Start()) { throw 'CHILD_START' }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($TimeoutMs)) { try { $process.Kill() } catch {}; throw 'CHILD_TIMEOUT' }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    return [pscustomobject]@{ ExitCode = $process.ExitCode; Stdout = $stdout; Stderr = $stderr }
  }
  finally { $process.Dispose() }
}

function Get-ShellPath {
  $shell = Get-Command pwsh -ErrorAction SilentlyContinue
  if ($null -eq $shell) { $shell = Get-Command powershell -ErrorAction Stop }
  return $shell.Source
}

function Write-State([object]$State, [string]$Path) {
  $State.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  $temp = $Path + '.tmp.' + [Guid]::NewGuid().ToString('N')
  [IO.File]::WriteAllText($temp, (($State | ConvertTo-Json -Compress -Depth 12) + "`n"), (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $temp -Destination $Path -Force
}

function Set-Phase([object]$State, [string]$Phase, [string]$Path) {
  if ($Phase -notin $Phases) { throw 'PHASE_DRIFT' }
  $State.phase = $Phase
  Write-State $State $Path
}

function Read-State([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
  try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw 'STATE_JSON' }
}

function Assert-Lease([object]$State, [string]$Path) {
  if ($null -eq $State.fence_started_at) { return }
  $fresh = Read-State $Path
  if ($null -ne $fresh.rollback_initiated_at) { throw 'ROLLBACK_ALREADY_INITIATED' }
  $now = [DateTimeOffset]::UtcNow
  if ($now -ge [DateTimeOffset]::Parse([string]$State.hard_fence_deadline_at)) { throw 'HARD_FENCE_LEASE_EXPIRED' }
  if ($now -ge [DateTimeOffset]::Parse([string]$State.rollback_deadline_at)) { throw 'FENCE_ROLLBACK_DEADLINE' }
}

function Get-SafePsqlStepFailureCategory([string]$Stderr) {
  if ([string]::IsNullOrEmpty($Stderr) -or [Text.Encoding]::UTF8.GetByteCount($Stderr) -gt 4096) { return $null }
  $allowed = 'R017_(?:BOUND_AUTH_USER_CARDINALITY_DRIFT|BOUND_AUTH_USER_EMAIL_DRIFT|BOUND_AUTH_IDENTITY_CARDINALITY_DRIFT|BOUND_AUTH_EMAIL_IDENTITY_MULTIPLE|BOUND_AUTH_IDENTITY_OWNER_DRIFT|BOUND_AUTH_IDENTITY_PROVIDER_DRIFT|BOUND_AUTH_IDENTITY_PROVIDER_ID_DRIFT|BOUND_AUTH_IDENTITY_SUBJECT_DRIFT|BOUND_AUTH_IDENTITY_EMAIL_DRIFT|IMPORT_USER_COLLISION|IMPORT_IDENTITY_COLLISION|AUTH_PREIMAGE_CARDINALITY_DRIFT|IMPORTED_AUTH_USERS_DIGEST_DRIFT|IMPORTED_AUTH_IDENTITIES_DIGEST_DRIFT|IDENTITY_MAP_DIGEST_DRIFT|BOUND_AUTH_USER_MUTATION_DRIFT|BOUND_AUTH_IDENTITY_MUTATION_DRIFT)'
  $match = [regex]::Match($Stderr, ('\Apsql:[^\r\n]{1,1024}:[0-9]+:\s+ERROR:\s+(' + $allowed + ')\r?\nCONTEXT:\s+PL/pgSQL function inline_code_block line [0-9]+ at RAISE\r?\n?\z'))
  if (-not $match.Success) { return $null }
  return $match.Groups[1].Value
}

function Invoke-Psql([string]$DatabaseUrl, [string]$SqlPath) {
  $child = Invoke-Child (Get-Command psql -ErrorAction Stop).Source @('-X','--no-psqlrc','--set','ON_ERROR_STOP=1','--file',$SqlPath) @{ PGDATABASE = $DatabaseUrl; PGCONNECT_TIMEOUT = '15'; PGAPPNAME = 'atlas-mazer-master-preparation-r017' } 120000
  if ($child.ExitCode -ne 0) {
    $safeCategory = Get-SafePsqlStepFailureCategory ([string]$child.Stderr)
    if ($null -ne $safeCategory) { throw $safeCategory }
    throw 'PSQL_STEP_FAILED'
  }
}

function Get-MasterDatabaseUrl {
  $value = [Environment]::GetEnvironmentVariable('ATLAS_MAZER_MASTER_DATABASE_URL', 'Process')
  if ([string]::IsNullOrWhiteSpace($value)) { throw 'MASTER_DATABASE_URL_MISSING' }
  try { $uri = [Uri]$value } catch { throw 'MASTER_DATABASE_URL_SHAPE' }
  $user = ([string]$uri.UserInfo -split ':', 2)[0]
  $direct = $uri.Host -ceq "db.$Master.supabase.co"
  $pooler = $uri.Host -match '^[a-z0-9-]+\.pooler\.supabase\.com$' -and $user -ceq "postgres.$Master"
  if ((-not $direct -and -not $pooler) -or $uri.Port -ne 5432) { throw 'MASTER_DATABASE_URL_BINDING' }
  return $value
}

function Read-ManagementToken {
  $value = [Environment]::GetEnvironmentVariable('SUPABASE_ACCESS_TOKEN', 'Process')
  if ([string]::IsNullOrWhiteSpace($value)) { throw 'MANAGEMENT_TOKEN_MISSING' }
  return $value
}

function Invoke-MasterAuthConfig([string]$Token, [Collections.IDictionary]$Patch = $null) {
  $headers = @{ Authorization = "Bearer $Token" }
  $uri = "$ApiBase/v1/projects/$Master/config/auth"
  if ($null -eq $Patch) { return Invoke-RestMethod -Method Get -Uri $uri -Headers $headers }
  return Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -ContentType 'application/json' -Body ($Patch | ConvertTo-Json -Compress)
}

function New-FenceChildReceipt([string]$Step, [object]$Child, [string]$FenceState) {
  $terminalResult = 'NO_CHILD_RECEIPT'
  $terminalCategory = 'NO_CHILD_RECEIPT'
  if (-not [string]::IsNullOrWhiteSpace([string]$Child.Stdout)) {
    try {
      $parsed = [string]$Child.Stdout | ConvertFrom-Json
      $candidateResult = ([string]$parsed.result -replace '[^A-Za-z0-9_]', '').ToUpperInvariant()
      $candidateCategory = ([string]$parsed.category -replace '[^A-Za-z0-9_]', '').ToUpperInvariant()
      if (-not [string]::IsNullOrWhiteSpace($candidateResult)) { $terminalResult = $candidateResult }
      if (-not [string]::IsNullOrWhiteSpace($candidateCategory)) { $terminalCategory = $candidateCategory }
      elseif ([int]$Child.ExitCode -eq 0) { $terminalCategory = 'NONE' }
    }
    catch { $terminalCategory = 'CHILD_OUTPUT_UNPARSEABLE' }
  }
  $fenceStateExists = Test-Path -LiteralPath $FenceState -PathType Leaf
  $fencePhase = $null
  $fenceStateSha = $null
  if ($fenceStateExists) {
    try { $fencePhase = [string](Read-State $FenceState).phase } catch { $fencePhase = 'UNREADABLE' }
    try { $fenceStateSha = Get-Sha256 $FenceState } catch { $fenceStateSha = $null }
  }
  return [ordered]@{
    schema = 'atlas.supabase.mazer-master-preparation-fence-child-receipt.r017.v1'
    step = $Step
    exit_code = [int]$Child.ExitCode
    terminal_result = $terminalResult
    terminal_category = $terminalCategory
    stdout_sha256 = Get-TextSha256 ([string]$Child.Stdout)
    stderr_sha256 = Get-TextSha256 ([string]$Child.Stderr)
    stdout_bytes = [Text.Encoding]::UTF8.GetByteCount([string]$Child.Stdout)
    stderr_bytes = [Text.Encoding]::UTF8.GetByteCount([string]$Child.Stderr)
    fence_state_exists = $fenceStateExists
    fence_state_sha256 = $fenceStateSha
    fence_phase = $fencePhase
    raw_records_emitted = $false
    pii_emitted = $false
    secrets_emitted = $false
    updated_at = $null
  }
}

function Write-FenceChildReceipt([string]$Step, [object]$Child, [string]$FenceState) {
  $safeStep = ($Step -replace '[^A-Za-z0-9_-]', '').ToLowerInvariant()
  if ([string]::IsNullOrWhiteSpace($safeStep)) { throw 'FENCE_CHILD_STEP_SHAPE' }
  $receiptPath = $FenceState + ".$safeStep.child-receipt.json"
  Write-State (New-FenceChildReceipt $Step $Child $FenceState) $receiptPath
  return $receiptPath
}

function Assert-FenceChildReceiptContract {
  $missing = Join-Path $Runtime ('missing-fence-state-' + [Guid]::NewGuid().ToString('N') + '.json')
  $forwardJson = '{"result":"HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE","category":"ACL_PREIMAGE_DRIFT"}'
  $forward = New-FenceChildReceipt 'FenceOnly' ([pscustomobject]@{ ExitCode = 2; Stdout = $forwardJson; Stderr = 'forward-safe-error' }) $missing
  if ([string]$forward.terminal_category -cne 'ACL_PREIMAGE_DRIFT' -or [int]$forward.exit_code -ne 2 -or [string]$forward.stdout_sha256 -cne (Get-TextSha256 $forwardJson) -or [string]$forward.stderr_sha256 -cne (Get-TextSha256 'forward-safe-error') -or [bool]$forward.fence_state_exists) { throw 'FENCE_CHILD_FAILURE_RECEIPT_CONTRACT' }
  $rollbackJson = '{"result":"HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE","category":"ROLLBACK_ACL_PREIMAGE_MISSING"}'
  $rollback = New-FenceChildReceipt 'Rollback' ([pscustomobject]@{ ExitCode = 3; Stdout = $rollbackJson; Stderr = 'rollback-safe-error' }) $missing
  if ([string]$rollback.terminal_category -cne 'ROLLBACK_ACL_PREIMAGE_MISSING' -or [int]$rollback.exit_code -ne 3 -or [string]$rollback.stdout_sha256 -cne (Get-TextSha256 $rollbackJson) -or [string]$rollback.stderr_sha256 -cne (Get-TextSha256 'rollback-safe-error')) { throw 'FENCE_CHILD_ROLLBACK_RECEIPT_CONTRACT' }
}

function New-FenceInvocationEnvelope([string]$ModeValue, [string]$Step, [string]$FenceInputPath, [string]$InputSha, [string]$FenceState, [string]$Packet) {
  $issued = [DateTimeOffset]::UtcNow
  if ([string]::IsNullOrWhiteSpace($FenceInputPath)) { throw 'FENCE_INVOCATION_INPUT_MISSING' }
  if ([string]::IsNullOrWhiteSpace($FenceState)) { throw 'FENCE_INVOCATION_STATE_MISSING' }
  if ([string]::IsNullOrWhiteSpace($script:HostScriptPath)) { throw 'FENCE_INVOCATION_PARENT_MISSING' }
  if ([string]::IsNullOrWhiteSpace($script:Fence)) { throw 'FENCE_INVOCATION_CHILD_MISSING' }
  $resolvedInput = [IO.Path]::GetFullPath($FenceInputPath)
  $resolvedState = Assert-Under $FenceState $Runtime
  $inputBoundary = $null
  foreach ($boundary in @($Runtime, $Secrets)) {
    $prefix = [IO.Path]::GetFullPath($boundary).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if ($resolvedInput.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { $inputBoundary = [IO.Path]::GetFullPath($boundary); break }
  }
  if ($null -eq $inputBoundary) { throw 'FENCE_INVOCATION_INPUT_SCOPE' }
  Assert-NoReparse (Split-Path -Parent $resolvedInput) $inputBoundary
  Assert-NoReparse (Split-Path -Parent $resolvedState) $Runtime
  $correlation = 'r017-' + (Get-TextSha256 $resolvedState.ToLowerInvariant()).Substring(0, 32)
  $value = [ordered]@{
    schema = 'atlas.supabase.mazer-master-fence-invocation.r017.v1'
    packet = $Packet
    correlation_id = $correlation
    mode = $ModeValue
    input_path = $resolvedInput
    state_path = $resolvedState
    expected_input_sha256 = $InputSha
    execution_step = $Step
    execute_protected = $true
    parent_host_path = [IO.Path]::GetFullPath($script:HostScriptPath)
    parent_host_sha256 = Get-Sha256 $script:HostScriptPath
    child_host_sha256 = Get-Sha256 $script:Fence
    issued_at = $issued.ToString('o')
    expires_at = $issued.AddMinutes(5).ToString('o')
  }
  $json = $value | ConvertTo-Json -Compress
  if ($json -match '[^\x00-\x7f]') { throw 'FENCE_INVOCATION_ASCII' }
  $directory = Split-Path -Parent $resolvedInput
  $path = Join-Path $directory ('.fence-invocation-' + $correlation + '-' + [Guid]::NewGuid().ToString('N') + '.json')
  $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($json + "`n")
  $stream = New-Object IO.FileStream($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
  try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
  finally { $stream.Dispose(); [Array]::Clear($bytes, 0, $bytes.Length) }
  return [pscustomobject]@{ Path = $path; Sha256 = Get-Sha256 $path; CorrelationId = $correlation }
}

function Assert-StructuredFenceChildTransportContract([string]$ShellPath) {
  $probeRoot = Join-Path $Runtime ('r017 transport probe ' + [Guid]::NewGuid().ToString('N'))
  [IO.Directory]::CreateDirectory($probeRoot) | Out-Null
  $missingInput = Join-Path $probeRoot 'missing private input.json'
  $statePath = Join-Path $probeRoot 'fence state.json'
  $envelope = New-FenceInvocationEnvelope 'Forward' 'FenceOnly' $missingInput ('0' * 64) $statePath 'FP-MAZER-MASTER-R017-SOURCE-VALIDATION-001'
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$Fence,'-InvocationPath',$envelope.Path,'-ExpectedInvocationSha256',$envelope.Sha256,'-ExecuteProtected')
  $child = Invoke-Child $ShellPath $arguments @{} 120000
  if ([int]$child.ExitCode -ne 2) { throw 'FENCE_CHILD_TRANSPORT_EXIT' }
  if (-not [string]::IsNullOrEmpty([string]$child.Stderr)) { throw 'FENCE_CHILD_TRANSPORT_STDERR' }
  try { $receipt = [string]$child.Stdout | ConvertFrom-Json } catch { throw 'FENCE_CHILD_TRANSPORT_STDOUT' }
  if ([string]$receipt.result -cne 'HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE' -or [string]$receipt.category -cne 'INPUT_MISSING' -or [string]$receipt.effect_status -cne 'NO_EFFECT_PRESTATE') { throw 'FENCE_CHILD_TRANSPORT_RECEIPT' }
  if ([int]$receipt.provider_writes -ne 0 -or [int]$receipt.database_transactions -ne 0 -or (Test-Path -LiteralPath $statePath)) { throw 'FENCE_CHILD_TRANSPORT_EFFECT' }
  Remove-Item -LiteralPath $envelope.Path -Force
  Remove-Item -LiteralPath $probeRoot -Force
}

function Invoke-Fence([string]$Step, [string]$FenceInputPath, [string]$InputSha, [string]$FenceState, [string]$Packet) {
  $envelope = New-FenceInvocationEnvelope 'Forward' $Step $FenceInputPath $InputSha $FenceState $Packet
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$Fence,'-InvocationPath',$envelope.Path,'-ExpectedInvocationSha256',$envelope.Sha256,'-ExecuteProtected')
  $child = Invoke-Child (Get-ShellPath) $arguments @{} 900000
  [void](Write-FenceChildReceipt $Step $child $FenceState)
  if ($child.ExitCode -ne 0) { throw ('FENCE_' + $Step.ToUpperInvariant() + '_FAILED') }
  try { return $child.Stdout | ConvertFrom-Json } catch { throw 'FENCE_OUTPUT_SHAPE' }
}

function Invoke-FenceRollback([string]$FenceInputPath, [string]$InputSha, [string]$FenceState, [string]$Packet) {
  $envelope = New-FenceInvocationEnvelope 'Rollback' 'All' $FenceInputPath $InputSha $FenceState $Packet
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$Fence,'-InvocationPath',$envelope.Path,'-ExpectedInvocationSha256',$envelope.Sha256,'-ExecuteProtected')
  $child = Invoke-Child (Get-ShellPath) $arguments @{} 900000
  [void](Write-FenceChildReceipt 'Rollback' $child $FenceState)
  if ($child.ExitCode -ne 0) { throw 'FENCE_ROLLBACK_FAILED' }
}

function Assert-SourceContract {
  foreach ($path in @($Materializer, $Fence, $FenceClassifier)) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'SOURCE_MISSING' } }
  $tokens = $null; $errors = $null
  [void][Management.Automation.Language.Parser]::ParseFile($PSCommandPath, [ref]$tokens, [ref]$errors)
  if ($errors.Count -ne 0) { throw 'POWERSHELL_PARSE' }
  $node = (Get-Command node -ErrorAction Stop).Source
  if ((Invoke-Child $node @('--check', $Materializer) @{} 30000).ExitCode -ne 0) { throw 'MATERIALIZER_PARSE' }
  if ((Invoke-Child $node @($Materializer, '--source-check', 'true') @{} 30000).ExitCode -ne 0) { throw 'MATERIALIZER_SOURCE' }
  foreach ($shell in @((Get-Command pwsh -ErrorAction SilentlyContinue), (Get-Command powershell -ErrorAction SilentlyContinue))) {
    if ($null -ne $shell) {
      if ((Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-File',$Fence,'-SourceOnlyValidate') @{} 120000).ExitCode -ne 0) { throw 'FENCE_SOURCE_VALIDATION' }
      Assert-StructuredFenceChildTransportContract $shell.Source
    }
  }
  Assert-FenceChildReceiptContract
  $safeAuthFailure = "psql:C:\safe\auth-apply.sql:9: ERROR:  R017_BOUND_AUTH_USER_EMAIL_DRIFT`nCONTEXT:  PL/pgSQL function inline_code_block line 1 at RAISE`n"
  if ((Get-SafePsqlStepFailureCategory $safeAuthFailure) -cne 'R017_BOUND_AUTH_USER_EMAIL_DRIFT') { throw 'PSQL_SAFE_CATEGORY_DRIFT' }
  foreach ($unsafeAuthFailure in @('R017_BOUND_AUTH_USER_EMAIL_DRIFT', "${safeAuthFailure}DETAIL: password=synthetic`n", "psql:C:\safe\auth-apply.sql:9: ERROR: R017_UNKNOWN_DRIFT`nCONTEXT: PL/pgSQL function inline_code_block line 1 at RAISE`n", ('A' * 4097))) {
    if ($null -ne (Get-SafePsqlStepFailureCategory $unsafeAuthFailure)) { throw 'PSQL_SAFE_CATEGORY_FAIL_CLOSED_DRIFT' }
  }
}

function Start-RollbackWatchdog([string]$SourcePath, [string]$SourceSha, [string]$HostState) {
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$PSCommandPath,'-Mode','Watchdog','-PrivateSourcePath',$SourcePath,'-ExpectedPrivateSourceSha256',$SourceSha,'-StatePath',$HostState,'-ExecuteProtected')
  return (Start-Process -FilePath (Get-ShellPath) -ArgumentList $arguments -WindowStyle Hidden -PassThru).Id
}

function Invoke-SelfRollback([string]$SourcePath, [string]$SourceSha, [string]$HostState) {
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$PSCommandPath,'-Mode','Rollback','-PrivateSourcePath',$SourcePath,'-ExpectedPrivateSourceSha256',$SourceSha,'-StatePath',$HostState,'-ExecuteProtected')
  return Invoke-Child (Get-ShellPath) $arguments @{} 900000
}

if ($PSCmdlet.ParameterSetName -ceq 'Source') {
  Assert-SourceContract
  Write-Result 'PASS_MAZER_MASTER_PREPARATION_R017_SOURCE' ([ordered]@{ materializer_sha256 = Get-Sha256 $Materializer; fence_host_sha256 = Get-Sha256 $Fence; credential_reads = 0; provider_reads = 0; provider_writes = 0; auth_writes = 0; live_data_writes = 0; state_writes = 0; private_files = 0 })
  exit 0
}

if (-not $ExecuteProtected) { throw 'PROTECTED_EXECUTION_SWITCH_REQUIRED' }
$sourcePath = Assert-Under $PrivateSourcePath $Secrets
$statePath = Assert-Under $StatePath $Runtime
Assert-NoReparse $sourcePath $Secrets
Assert-NoReparse (Split-Path -Parent $statePath) $Runtime
if ((Get-Sha256 $sourcePath) -cne $ExpectedPrivateSourceSha256) { throw 'PRIVATE_SOURCE_DIGEST_DRIFT' }

if ($Mode -ceq 'Watchdog') {
  while ($true) {
    $watchState = Read-State $statePath
    if ($null -eq $watchState -or [string]$watchState.phase -in @('PREPARATION_COMPLETE','ROLLED_BACK')) { exit 0 }
    if ($null -ne $watchState.rollback_deadline_at -and [DateTimeOffset]::UtcNow -ge [DateTimeOffset]::Parse([string]$watchState.rollback_deadline_at)) {
      if ($null -eq $watchState.rollback_initiated_at) { $watchState.rollback_initiated_at = [DateTimeOffset]::UtcNow.ToString('o'); Write-State $watchState $statePath }
      $rollback = Invoke-SelfRollback $sourcePath $ExpectedPrivateSourceSha256 $statePath
      if ($rollback.ExitCode -ne 0) { exit 3 }
      exit 0
    }
    Start-Sleep -Seconds 5
  }
}

$privateRoot = $null
$managementToken = $null
$masterDatabaseUrl = $null
$state = $null
$providerWrites = 0
$databaseTransactions = 0
$fenceHasEffects = $false
try {
  Assert-SourceContract
  if (-not (Test-Path -LiteralPath $PacketRoot)) { [IO.Directory]::CreateDirectory($PacketRoot) | Out-Null }
  Assert-NoReparse $PacketRoot $Secrets
  $privateRoot = Join-Path $PacketRoot ([Guid]::NewGuid().ToString('N'))
  [IO.Directory]::CreateDirectory($privateRoot) | Out-Null
  Assert-NoReparse $privateRoot $Secrets
  $mazerRepository = Find-MazerRepository
  $materialized = Invoke-Child (Get-Command node -ErrorAction Stop).Source @($Materializer,'--input',$sourcePath,'--output',$privateRoot,'--mazer-repository',$mazerRepository) @{} 120000
  if ($materialized.ExitCode -ne 0) { throw 'PRIVATE_MATERIALIZATION_FAILED' }
  $manifestPath = Join-Path $privateRoot 'manifest.json'
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  if ([int]$manifest.auth_counts.imports -ne 3 -or [int]$manifest.auth_counts.binds -ne 14 -or [int]$manifest.auth_counts.retained_edges -ne 2 -or [int]$manifest.auth_counts.final_edges -ne 19 -or [int]$manifest.auth_counts.expected_target_users -ne 117) { throw 'AUTH_TOPOLOGY_MANIFEST_DRIFT' }
  $input = Join-Path $privateRoot 'fence-input.json'
  $inputSha = Get-Sha256 $input
  $manifestSha = Get-Sha256 $manifestPath
  $state = Read-State $statePath
  if ($null -eq $state) {
    if ($Mode -ceq 'Rollback') { throw 'ROLLBACK_STATE_MISSING' }
    $state = [ordered]@{ schema = 'atlas.supabase.mazer-master-preparation-host-state.r017.v1'; packet = [string]$manifest.packet; phase = 'PREFLIGHT'; private_source_sha256 = $ExpectedPrivateSourceSha256; private_manifest_sha256 = $manifestSha; fence_input_sha256 = $inputSha; replay_generation = 0; master_hook_preimage = $null; fence_started_at = $null; rollback_deadline_at = $null; hard_fence_deadline_at = $null; rollback_initiated_at = $null; watchdog_pid = $null; updated_at = $null }
    Write-State $state $statePath
  }
  elseif ([string]$state.schema -cne 'atlas.supabase.mazer-master-preparation-host-state.r017.v1' -or [string]$state.private_source_sha256 -cne $ExpectedPrivateSourceSha256 -or [string]$state.private_manifest_sha256 -cne $manifestSha -or [string]$state.fence_input_sha256 -cne $inputSha) { throw 'STATE_BINDING_DRIFT' }
  $replayGeneration = if ($state.PSObject.Properties.Name -contains 'replay_generation') { [int]$state.replay_generation } else { 0 }
  $fenceState = if ($replayGeneration -eq 0) { $statePath + '.fence.json' } else { $statePath + ".fence.replay-$replayGeneration.json" }
  if ([string]$state.phase -ceq 'PREPARATION_COMPLETE') { Write-Result 'PASS_EXACT_REPLAY_NOOP' ([ordered]@{ phase = [string]$state.phase; provider_writes = 0; database_transactions = 0 }); exit 0 }
  if ([string]$state.phase -ceq 'ROLLED_BACK') {
    if (-not $ReplayExactRolledBack) { Write-Result 'PASS_EXACT_ROLLBACK_TERMINAL' ([ordered]@{ phase = [string]$state.phase; replay_requires_explicit_switch = $true; provider_writes = 0; database_transactions = 0 }); exit 0 }
    if ($Mode -cne 'Prepare') { throw 'ROLLED_BACK_REPLAY_REQUIRES_PREPARE' }
    $replayGeneration += 1
    $state.replay_generation = $replayGeneration
    $state.master_hook_preimage = $null
    $state.fence_started_at = $null
    $state.rollback_deadline_at = $null
    $state.hard_fence_deadline_at = $null
    $state.rollback_initiated_at = $null
    $state.watchdog_pid = $null
    $state.phase = 'PREFLIGHT'
    Write-State $state $statePath
    $fenceState = $statePath + ".fence.replay-$replayGeneration.json"
  }

  $managementToken = Read-ManagementToken
  $masterDatabaseUrl = Get-MasterDatabaseUrl
  if ($Mode -ceq 'Rollback') {
    if ($null -eq $state.rollback_initiated_at) { $state.rollback_initiated_at = [DateTimeOffset]::UtcNow.ToString('o'); Write-State $state $statePath }
    Set-Phase $state 'ROLLBACK_DISABLING_HOOK' $statePath
    $disabled = Invoke-MasterAuthConfig $managementToken @{ hook_before_user_created_enabled = $false }
    $providerWrites += 1
    if ([bool]$disabled.hook_before_user_created_enabled) { throw 'ROLLBACK_HOOK_DISABLE_FAILED' }
    Set-Phase $state 'ROLLBACK_TARGET_RESTORING' $statePath
    Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot 'qa-cleanup.sql')
    Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot 'rollback.sql')
    $databaseTransactions += 2
    Set-Phase $state 'ROLLBACK_LEGACY_RESTORING' $statePath
    if (Test-Path -LiteralPath $fenceState -PathType Leaf) {
      $currentFence = Read-State $fenceState
      if ([string]$currentFence.phase -ceq 'COMPLETE') { [void](Invoke-Fence 'ReleaseLegacy' $input $inputSha $fenceState ([string]$state.packet)) }
      elseif ([string]$currentFence.phase -notin @('PREPARATION_COMPLETE','ROLLED_BACK','PREFLIGHT')) { Invoke-FenceRollback $input $inputSha $fenceState ([string]$state.packet) }
    }
    Set-Phase $state 'ROLLED_BACK' $statePath
    Write-Result 'EXACT_R017_ROLLBACK_COMPLETE' ([ordered]@{ phase = [string]$state.phase; hook_disabled_first = $true; provider_writes = $providerWrites; database_transactions = $databaseTransactions })
    exit 0
  }

  $stateJson = $state | ConvertTo-Json -Compress -Depth 12
  $materializerUri = ([Uri]$Materializer).AbsoluteUri
  $recovery = Invoke-Child (Get-Command node -ErrorAction Stop).Source @('-e', "import(process.argv[1]).then(m=>console.log(JSON.stringify(m.classifyHostRecovery(JSON.parse(process.argv[2])))))", $materializerUri, $stateJson) @{} 30000
  if ($recovery.ExitCode -ne 0) { throw 'STATE_RECOVERY_CLASSIFICATION_FAILED' }
  $disposition = $recovery.Stdout | ConvertFrom-Json
  if ([string]$disposition.action -ceq 'ROLLBACK_REQUIRED') { throw 'AMBIGUOUS_STATE_REQUIRES_ROLLBACK' }

  if ([string]$state.phase -ceq 'PREFLIGHT') {
    Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot 'preflight.sql')
    $databaseTransactions += 1
    $config = Invoke-MasterAuthConfig $managementToken
    if ([bool]$config.hook_before_user_created_enabled) { throw 'MASTER_HOOK_PREIMAGE_DRIFT' }
    $state.master_hook_preimage = $false
    $started = [DateTimeOffset]::UtcNow
    $state.fence_started_at = $started.ToString('o')
    $state.rollback_deadline_at = $started.AddSeconds($RollbackDeadlineSeconds).ToString('o')
    $state.hard_fence_deadline_at = $started.AddSeconds($HardFenceLeaseSeconds).ToString('o')
    Set-Phase $state 'FENCE_APPLYING' $statePath
    $state.watchdog_pid = Start-RollbackWatchdog $sourcePath $ExpectedPrivateSourceSha256 $statePath
    Write-State $state $statePath
    $fenceHasEffects = $true
    [void](Invoke-Fence 'FenceOnly' $input $inputSha $fenceState ([string]$state.packet))
    Set-Phase $state 'FENCE_PAUSED' $statePath
    Write-State $state $statePath
  }
  else { $fenceHasEffects = $true }

  $steps = @(
    @('MASTER_FENCE_APPLYING','MASTER_FENCED','master-fence.sql'), @('M1_APPLYING','M1_APPLIED','m1.sql'),
    @('M2_APPLYING','M2_APPLIED','m2.sql'), @('MASTER_REFENCE_APPLYING','MASTER_REFENCED','master-refence.sql'),
    @('AUTH_APPLYING','AUTH_APPLIED','auth-apply.sql')
  )
  foreach ($step in $steps) {
    if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf($step[1])) {
      Assert-Lease $state $statePath
      Set-Phase $state $step[0] $statePath
      Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot $step[2])
      $databaseTransactions += 1
      Set-Phase $state $step[1] $statePath
    }
  }
  if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf('RESET_QUARANTINE_SEALED')) {
    Assert-Lease $state $statePath
    Set-Phase $state 'RESET_QUARANTINE_APPLYING' $statePath
    Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot 'reset-era-apply.sql')
    $databaseTransactions += 1
    Set-Phase $state 'RESET_QUARANTINE_SEALED' $statePath
  }
  if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf('DELTA_APPLIED')) {
    Assert-Lease $state $statePath
    Set-Phase $state 'DELTA_APPLYING' $statePath
    [void](Invoke-Fence 'Continue' $input $inputSha $fenceState ([string]$state.packet))
    Set-Phase $state 'DELTA_APPLIED' $statePath
  }
  foreach ($step in @(@('M3_APPLYING','M3_APPLIED','m3.sql'), @('M4_APPLYING','M4_APPLIED','m4.sql'), @('POSTVERIFYING','POSTVERIFIED','postverify.sql'))) {
    if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf($step[1])) {
      Assert-Lease $state $statePath
      Set-Phase $state $step[0] $statePath
      Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot $step[2])
      $databaseTransactions += 1
      Set-Phase $state $step[1] $statePath
    }
  }
  if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf('HOOK_ACTIVE')) {
    Assert-Lease $state $statePath
    Set-Phase $state 'HOOK_ACTIVATING' $statePath
    $enabled = Invoke-MasterAuthConfig $managementToken @{ hook_before_user_created_enabled = $true; hook_before_user_created_uri = $ExpectedHookUri }
    $providerWrites += 1
    if (-not [bool]$enabled.hook_before_user_created_enabled -or [string]$enabled.hook_before_user_created_uri -cne $ExpectedHookUri) { throw 'HOOK_ACTIVATION_FAILED' }
    Set-Phase $state 'HOOK_ACTIVE' $statePath
  }
  if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf('QA_COMPLETE')) {
    Assert-Lease $state $statePath
    Set-Phase $state 'QA_APPLYING' $statePath
    Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot 'qa-apply.sql')
    $databaseTransactions += 1
    Set-Phase $state 'QA_COMPLETE' $statePath
  }
  if ($Phases.IndexOf([string]$state.phase) -lt $Phases.IndexOf('QA_CLEAN')) {
    Assert-Lease $state $statePath
    Set-Phase $state 'QA_CLEANING' $statePath
    Invoke-Psql $masterDatabaseUrl (Join-Path $privateRoot 'qa-cleanup.sql')
    $databaseTransactions += 1
    Set-Phase $state 'QA_CLEAN' $statePath
  }
  Assert-Lease $state $statePath
  Set-Phase $state 'LEGACY_RESTORING' $statePath
  [void](Invoke-Fence 'ReleaseLegacy' $input $inputSha $fenceState ([string]$state.packet))
  Set-Phase $state 'LEGACY_RESTORED' $statePath
  Set-Phase $state 'PREPARATION_COMPLETE' $statePath
  Write-Result 'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER' ([ordered]@{ phase = [string]$state.phase; master_hook_enabled = $true; legacy_signup_and_acl_restored = $true; fresh_dual_refence_and_catchup_required_for_cutover = $true; fence_lease_seconds = $HardFenceLeaseSeconds; rollback_initiation_deadline_seconds = $RollbackDeadlineSeconds; provider_writes = $providerWrites; database_transactions = $databaseTransactions; final_identity_edges = 19; profiles = 13; player = 16; ai = 16; receipts = 1887 })
}
catch {
  $category = ([string]$_.Exception.Message -replace '[^A-Za-z0-9_]', '').ToUpperInvariant()
  if ($category.Length -gt 96) { $category = $category.Substring(0, 96) }
  $rollbackResult = 'NO_EFFECT_CONFIRMED'
  if ($Mode -ceq 'Prepare' -and $fenceHasEffects -and $null -ne $state) {
    try {
      if ($null -eq $state.rollback_initiated_at) { $state.rollback_initiated_at = [DateTimeOffset]::UtcNow.ToString('o'); Write-State $state $statePath }
      $rollback = Invoke-SelfRollback $sourcePath $ExpectedPrivateSourceSha256 $statePath
      $rollbackResult = if ($rollback.ExitCode -eq 0) { 'EXACT_ROLLBACK_COMPLETED' } else { 'ROLLBACK_FAILED' }
    }
    catch { $rollbackResult = 'ROLLBACK_FAILED' }
  }
  elseif ($null -ne $state -and [string]$state.phase -notin @('PREPARATION_COMPLETE','ROLLED_BACK')) {
    try { $state.previous_phase = $state.phase; Set-Phase $state 'AMBIGUOUS_HOLD' $statePath } catch {}
  }
  Write-Result 'HOLD_MAZER_MASTER_PREPARATION_R017' ([ordered]@{ category = $category; rollback_disposition = $rollbackResult; provider_writes = $providerWrites; database_transactions = $databaseTransactions })
  exit 2
}
finally {
  $managementToken = $null
  $masterDatabaseUrl = $null
  if ($null -ne $privateRoot -and (Test-Path -LiteralPath $privateRoot -PathType Container)) {
    $safePrivateRoot = Assert-Under $privateRoot $PacketRoot
    Remove-Item -LiteralPath $safePrivateRoot -Recurse -Force
  }
}
