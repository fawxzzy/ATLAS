[CmdletBinding(DefaultParameterSetName = 'Source')]
param(
  [Parameter(Mandatory = $true, ParameterSetName = 'Source')][switch]$SourceOnlyValidate,
  [Parameter(Mandatory = $true, ParameterSetName = 'MaterializerProbe')][switch]$LocalMaterializerPortabilityProbe,
  [Parameter(Mandatory = $true, ParameterSetName = 'FenceProbe')][switch]$LocalFenceReplacementAdversary,
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
$script:VerifiedHostSourceText = if($null-ne(Get-Variable -Name ATLAS_R017_VERIFIED_HOST_SOURCE_TEXT -Scope Global -ErrorAction SilentlyContinue)){[string]$global:ATLAS_R017_VERIFIED_HOST_SOURCE_TEXT}else{$null}
$HostDirectory = if($null-ne$script:VerifiedHostSourceText){[IO.Path]::GetFullPath($env:ATLAS_R017_VERIFIED_HOST_DIR)}else{[IO.Path]::GetFullPath($PSScriptRoot)}
$script:HostScriptPath = if($null-ne$script:VerifiedHostSourceText){[IO.Path]::GetFullPath($env:ATLAS_R017_VERIFIED_HOST_PATH)}else{$PSCommandPath}
$Root = [IO.Path]::GetFullPath([IO.Path]::Combine($HostDirectory, '..', '..'))
$Runtime = Join-Path $Root 'runtime\atlas'
$Secrets = Join-Path $Root 'secrets'
$PacketRoot = Join-Path $Secrets 'packet\mazer-master-preparation-r017'
$Materializer = Join-Path $HostDirectory 'materialize_supabase_mazer_master_preparation_r017.mjs'
$Fence = Join-Path $HostDirectory 'invoke_supabase_mazer_master_cutover_data_fence_r001.ps1'
$FenceClassifier = Join-Path $HostDirectory 'classify_supabase_mazer_master_cutover_data_fence_r001.mjs'
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

function Get-LockedStreamSha256([IO.FileStream]$Stream) {
  $Stream.Position = 0
  $hasher = [Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($hasher.ComputeHash($Stream))).Replace('-', '').ToLowerInvariant() }
  finally { $hasher.Dispose(); $Stream.Position = 0 }
}

function Invoke-VerifiedMaterializerNode([string]$NodePath,[string]$ExpectedNodeSha,[string]$MaterializerPath,[string]$ExpectedMaterializerSha,[string]$ClassifierPath,[string]$ExpectedClassifierSha,[string[]]$Arguments,[Collections.IDictionary]$Environment=@{},[int]$TimeoutMs=120000,[scriptblock]$BeforeInvoke=$null,[string]$CanonicalMaterializerPath=$Materializer,[string]$CanonicalClassifierPath=$FenceClassifier) {
  $resolvedNode=[IO.Path]::GetFullPath($NodePath);$resolvedMaterializer=[IO.Path]::GetFullPath($MaterializerPath);$resolvedClassifier=[IO.Path]::GetFullPath($ClassifierPath)
  if($resolvedMaterializer-cne[IO.Path]::GetFullPath($CanonicalMaterializerPath)-or$resolvedClassifier-cne[IO.Path]::GetFullPath($CanonicalClassifierPath)-or$ExpectedNodeSha-cnotmatch'^[a-f0-9]{64}$'-or$ExpectedMaterializerSha-cnotmatch'^[a-f0-9]{64}$'-or$ExpectedClassifierSha-cnotmatch'^[a-f0-9]{64}$'){throw 'MATERIALIZER_BINDING'}
  $nodeStream=New-Object IO.FileStream($resolvedNode,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  $materializerStream=New-Object IO.FileStream($resolvedMaterializer,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  $classifierStream=New-Object IO.FileStream($resolvedClassifier,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  try {
    if((Get-LockedStreamSha256 $nodeStream)-cne$ExpectedNodeSha){throw 'NODE_DIGEST_DRIFT'}
    if((Get-LockedStreamSha256 $materializerStream)-cne$ExpectedMaterializerSha){throw 'MATERIALIZER_DIGEST_DRIFT'}
    if((Get-LockedStreamSha256 $classifierStream)-cne$ExpectedClassifierSha){throw 'CLASSIFIER_DIGEST_DRIFT'}
    if($null-ne$BeforeInvoke){&$BeforeInvoke}
    return Invoke-Child $resolvedNode $Arguments $Environment $TimeoutMs
  }
  finally{$classifierStream.Dispose();$materializerStream.Dispose();$nodeStream.Dispose()}
}

function Remove-OwnedPrivateRoot([string]$Path,[string]$OwnerToken) {
  if([string]::IsNullOrWhiteSpace($Path)-or$OwnerToken-cnotmatch'^[a-f0-9]{32}$'-or-not(Test-Path -LiteralPath $Path -PathType Container)){return $false}
  $safe=Assert-Under $Path $PacketRoot;Assert-NoReparse $safe $Secrets
  $marker=Join-Path $safe '.atlas-r017-owner'
  if(-not(Test-Path -LiteralPath $marker -PathType Leaf)){return $false}
  Assert-NoReparse $marker $Secrets
  if(([IO.File]::ReadAllText($marker,(New-Object Text.UTF8Encoding($false,$true))).Trim())-cne$OwnerToken){return $false}
  Remove-Item -LiteralPath $safe -Recurse -Force
  return $true
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
    child_host_sha256 = [string]$script:VerifiedFenceSha
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

function Get-VerifiedFenceBootstrapEncoded {
  $bootstrap=@'
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';$p=[IO.Path]::GetFullPath($env:ATLAS_R017_VERIFIED_FENCE_PATH);$s=New-Object IO.FileStream($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$b=$null
try{if($s.Length-lt2-or$s.Length-gt2097152){exit 81};$b=New-Object byte[] ([int]$s.Length);$o=0;while($o-lt$b.Length){$r=$s.Read($b,$o,$b.Length-$o);if($r-le0){exit 82};$o+=$r};$h=[Security.Cryptography.SHA256]::Create();try{$a=([BitConverter]::ToString($h.ComputeHash($b))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()};if($a-cne$env:ATLAS_R017_VERIFIED_FENCE_SHA256){exit 83};$t=(New-Object Text.UTF8Encoding($false,$true)).GetString($b)}finally{$s.Dispose();if($null-ne$b){[Array]::Clear($b,0,$b.Length)}}
$global:ATLAS_R017_VERIFIED_FENCE_SOURCE_TEXT=$t;if($env:ATLAS_R017_VERIFIED_FENCE_MODE-ceq'Synthetic'-and-not[string]::IsNullOrWhiteSpace($env:ATLAS_R017_VERIFIED_FENCE_TEST_REPLACEMENT_PATH)){[IO.File]::Copy($env:ATLAS_R017_VERIFIED_FENCE_TEST_REPLACEMENT_PATH,$p,$true)};$sb=[ScriptBlock]::Create($t)
if($env:ATLAS_R017_VERIFIED_FENCE_MODE-ceq'Source'){. $sb -SourceOnlyValidate}elseif($env:ATLAS_R017_VERIFIED_FENCE_MODE-ceq'Execute'){. $sb -InvocationPath $env:ATLAS_R017_FENCE_INVOCATION_PATH -ExpectedInvocationSha256 $env:ATLAS_R017_FENCE_INVOCATION_SHA256 -ExecuteProtected}else{. $sb};exit 0
'@
  return [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($bootstrap))
}

function Initialize-VerifiedFenceBinding([bool]$RequireSealed) {
  if($RequireSealed-and([string]::IsNullOrWhiteSpace($env:ATLAS_R017_VERIFIED_FENCE_PATH)-or[string]::IsNullOrWhiteSpace($env:ATLAS_R017_VERIFIED_FENCE_SHA256))){throw 'FENCE_BINDING_MISSING'}
  $path=if([string]::IsNullOrWhiteSpace($env:ATLAS_R017_VERIFIED_FENCE_PATH)){[IO.Path]::GetFullPath($Fence)}else{[IO.Path]::GetFullPath([string]$env:ATLAS_R017_VERIFIED_FENCE_PATH)}
  $sha=if([string]::IsNullOrWhiteSpace($env:ATLAS_R017_VERIFIED_FENCE_SHA256)){Get-Sha256 $path}else{[string]$env:ATLAS_R017_VERIFIED_FENCE_SHA256}
  if($path-cne[IO.Path]::GetFullPath($Fence)-or$sha-cnotmatch'^[a-f0-9]{64}$'){throw 'FENCE_BINDING'}
  Assert-NoReparse $path $HostDirectory
  if((Get-Sha256 $path)-cne$sha){throw 'FENCE_DIGEST_DRIFT'}
  $script:VerifiedFencePath=$path;$script:VerifiedFenceSha=$sha
}

function Invoke-VerifiedFenceChild([string]$ShellPath,[string]$VerifiedMode,[string]$InvocationPath,[string]$InvocationSha,[int]$TimeoutMs,[string]$SourcePath,[string]$ExpectedSha,[string]$TestReplacementPath) {
  $environment=@{ATLAS_R017_VERIFIED_FENCE_PATH=[IO.Path]::GetFullPath($SourcePath);ATLAS_R017_VERIFIED_FENCE_SHA256=$ExpectedSha;ATLAS_R017_VERIFIED_FENCE_DIR=[IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($SourcePath));ATLAS_R017_VERIFIED_FENCE_MODE=$VerifiedMode;ATLAS_R017_FENCE_INVOCATION_PATH=$InvocationPath;ATLAS_R017_FENCE_INVOCATION_SHA256=$InvocationSha;ATLAS_R017_VERIFIED_FENCE_TEST_REPLACEMENT_PATH=if($VerifiedMode-ceq'Synthetic'){$TestReplacementPath}else{''}}
  return Invoke-Child $ShellPath @('-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',(Get-VerifiedFenceBootstrapEncoded)) $environment $TimeoutMs
}

function Assert-StructuredFenceChildTransportContract([string]$ShellPath) {
  $probeRoot = Join-Path $Runtime ('r017 transport probe ' + [Guid]::NewGuid().ToString('N'))
  [IO.Directory]::CreateDirectory($probeRoot) | Out-Null
  $missingInput = Join-Path $probeRoot 'missing private input.json'
  $statePath = Join-Path $probeRoot 'fence state.json'
  $envelope = New-FenceInvocationEnvelope 'Forward' 'FenceOnly' $missingInput ('0' * 64) $statePath 'FP-MAZER-MASTER-R017-SOURCE-VALIDATION-001'
  $child = Invoke-VerifiedFenceChild $ShellPath 'Execute' $envelope.Path $envelope.Sha256 120000 $script:VerifiedFencePath $script:VerifiedFenceSha ''
  if ([int]$child.ExitCode -ne 2) { throw 'FENCE_CHILD_TRANSPORT_EXIT' }
  if (-not [string]::IsNullOrEmpty([string]$child.Stderr)) { throw 'FENCE_CHILD_TRANSPORT_STDERR' }
  try { $receipt = [string]$child.Stdout | ConvertFrom-Json } catch { throw 'FENCE_CHILD_TRANSPORT_STDOUT' }
  if ([string]$receipt.result -cne 'HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE' -or [string]$receipt.category -cne 'INPUT_MISSING' -or [string]$receipt.effect_status -cne 'NO_EFFECT_PRESTATE') { throw 'FENCE_CHILD_TRANSPORT_RECEIPT' }
  if ([int]$receipt.provider_writes -ne 0 -or [int]$receipt.database_transactions -ne 0 -or (Test-Path -LiteralPath $statePath)) { throw 'FENCE_CHILD_TRANSPORT_EFFECT' }
  Remove-Item -LiteralPath $envelope.Path -Force
  Remove-Item -LiteralPath $probeRoot -Force
}

function Assert-StructuredFenceChildSuccessReturnContract([string]$ShellPath) {
  $probeRoot = Join-Path $Runtime ('r017 fence success return probe ' + [Guid]::NewGuid().ToString('N'))
  [IO.Directory]::CreateDirectory($probeRoot) | Out-Null
  $source = Join-Path $probeRoot 'strict-mode success child.ps1'
  try {
    $receipt = '{"result":"PASS_R017_FENCE_CHILD_SUCCESS_RETURN","raw_records_emitted":false,"pii_emitted":false,"secrets_emitted":false}'
    $sourceText = "Set-StrictMode -Version Latest`r`n[Console]::Out.WriteLine('$receipt')`r`n"
    [IO.File]::WriteAllText($source, $sourceText, (New-Object Text.UTF8Encoding($false)))
    $child = Invoke-VerifiedFenceChild $ShellPath 'Synthetic' '' '' 30000 $source (Get-Sha256 $source) ''
    if ([int]$child.ExitCode -ne 0) { throw 'FENCE_CHILD_SUCCESS_RETURN_EXIT' }
    if (-not [string]::IsNullOrEmpty([string]$child.Stderr)) { throw 'FENCE_CHILD_SUCCESS_RETURN_STDERR' }
    try { $parsed = [string]$child.Stdout | ConvertFrom-Json } catch { throw 'FENCE_CHILD_SUCCESS_RETURN_STDOUT' }
    if ([string]$parsed.result -cne 'PASS_R017_FENCE_CHILD_SUCCESS_RETURN' -or [bool]$parsed.raw_records_emitted -ne $false -or [bool]$parsed.pii_emitted -ne $false -or [bool]$parsed.secrets_emitted -ne $false) { throw 'FENCE_CHILD_SUCCESS_RETURN_RECEIPT' }
  }
  finally { if (Test-Path -LiteralPath $probeRoot) { Remove-Item -LiteralPath $probeRoot -Recurse -Force } }
}

function Invoke-Fence([string]$Step, [string]$FenceInputPath, [string]$InputSha, [string]$FenceState, [string]$Packet) {
  $envelope = New-FenceInvocationEnvelope 'Forward' $Step $FenceInputPath $InputSha $FenceState $Packet
  $child = Invoke-VerifiedFenceChild (Get-ShellPath) 'Execute' $envelope.Path $envelope.Sha256 900000 $script:VerifiedFencePath $script:VerifiedFenceSha ''
  [void](Write-FenceChildReceipt $Step $child $FenceState)
  if ($child.ExitCode -ne 0) { throw ('FENCE_' + $Step.ToUpperInvariant() + '_FAILED') }
  try { return $child.Stdout | ConvertFrom-Json } catch { throw 'FENCE_OUTPUT_SHAPE' }
}

function Invoke-FenceRollback([string]$FenceInputPath, [string]$InputSha, [string]$FenceState, [string]$Packet) {
  $envelope = New-FenceInvocationEnvelope 'Rollback' 'All' $FenceInputPath $InputSha $FenceState $Packet
  $child = Invoke-VerifiedFenceChild (Get-ShellPath) 'Execute' $envelope.Path $envelope.Sha256 900000 $script:VerifiedFencePath $script:VerifiedFenceSha ''
  [void](Write-FenceChildReceipt 'Rollback' $child $FenceState)
  if ($child.ExitCode -ne 0) { throw 'FENCE_ROLLBACK_FAILED' }
}

function Assert-SourceContract {
  foreach ($path in @($Materializer, $Fence, $FenceClassifier)) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'SOURCE_MISSING' } }
  $tokens = $null; $errors = $null
  if($null-ne$script:VerifiedHostSourceText){[void][Management.Automation.Language.Parser]::ParseInput($script:VerifiedHostSourceText,[ref]$tokens,[ref]$errors)}else{[void][Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$tokens,[ref]$errors)}
  if ($errors.Count -ne 0) { throw 'POWERSHELL_PARSE' }
  $node = (Get-Command node -ErrorAction Stop).Source
  if ((Invoke-Child $node @('--check', $Materializer) @{} 30000).ExitCode -ne 0) { throw 'MATERIALIZER_PARSE' }
  if ((Invoke-Child $node @($Materializer, '--source-check', 'true') @{} 30000).ExitCode -ne 0) { throw 'MATERIALIZER_SOURCE' }
  foreach ($shell in @((Get-Command pwsh -ErrorAction SilentlyContinue), (Get-Command powershell -ErrorAction SilentlyContinue))) {
    if ($null -ne $shell) {
      if ((Invoke-VerifiedFenceChild $shell.Source 'Source' '' '' 120000 $script:VerifiedFencePath $script:VerifiedFenceSha '').ExitCode -ne 0) { throw 'FENCE_SOURCE_VALIDATION' }
      Assert-StructuredFenceChildTransportContract $shell.Source
      Assert-StructuredFenceChildSuccessReturnContract $shell.Source
    }
  }
  Assert-FenceChildReceiptContract
  $safeAuthFailure = "psql:C:\safe\auth-apply.sql:9: ERROR:  R017_BOUND_AUTH_USER_EMAIL_DRIFT`nCONTEXT:  PL/pgSQL function inline_code_block line 1 at RAISE`n"
  if ((Get-SafePsqlStepFailureCategory $safeAuthFailure) -cne 'R017_BOUND_AUTH_USER_EMAIL_DRIFT') { throw 'PSQL_SAFE_CATEGORY_DRIFT' }
  foreach ($unsafeAuthFailure in @('R017_BOUND_AUTH_USER_EMAIL_DRIFT', "${safeAuthFailure}DETAIL: password=synthetic`n", "psql:C:\safe\auth-apply.sql:9: ERROR: R017_UNKNOWN_DRIFT`nCONTEXT: PL/pgSQL function inline_code_block line 1 at RAISE`n", ('A' * 4097))) {
    if ($null -ne (Get-SafePsqlStepFailureCategory $unsafeAuthFailure)) { throw 'PSQL_SAFE_CATEGORY_FAIL_CLOSED_DRIFT' }
  }
}

function Get-VerifiedSelfBootstrapEncoded {
  $bootstrap=@'
$ErrorActionPreference='Stop';$p=[IO.Path]::GetFullPath($env:ATLAS_R017_VERIFIED_HOST_PATH);$s=New-Object IO.FileStream($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$b=$null
try{if($s.Length-lt2-or$s.Length-gt2097152){exit 81};$b=New-Object byte[] ([int]$s.Length);$o=0;while($o-lt$b.Length){$r=$s.Read($b,$o,$b.Length-$o);if($r-le0){exit 82};$o+=$r};$h=[Security.Cryptography.SHA256]::Create();try{$a=([BitConverter]::ToString($h.ComputeHash($b))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()};if($a-cne$env:ATLAS_R017_VERIFIED_HOST_SHA256){exit 83};$t=(New-Object Text.UTF8Encoding($false,$true)).GetString($b)}finally{$s.Dispose();if($null-ne$b){[Array]::Clear($b,0,$b.Length)}}
$global:ATLAS_R017_VERIFIED_HOST_SOURCE_TEXT=$t;$sb=[ScriptBlock]::Create($t);. $sb -Mode $env:ATLAS_R017_CHILD_MODE -PrivateSourcePath $env:ATLAS_R017_CHILD_SOURCE -ExpectedPrivateSourceSha256 $env:ATLAS_R017_CHILD_SOURCE_SHA -StatePath $env:ATLAS_R017_CHILD_STATE -ExecuteProtected;exit $LASTEXITCODE
'@
  return [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($bootstrap))
}

function Get-VerifiedSelfEnvironment([string]$ChildMode,[string]$SourcePath,[string]$SourceSha,[string]$HostState) {
  if($null-eq$script:VerifiedHostSourceText){return $null}
  return @{ATLAS_R017_VERIFIED_HOST_PATH=$script:HostScriptPath;ATLAS_R017_VERIFIED_HOST_SHA256=$env:ATLAS_R017_VERIFIED_HOST_SHA256;ATLAS_R017_VERIFIED_HOST_DIR=$HostDirectory;ATLAS_R017_VERIFIED_MODE='Execute';ATLAS_R017_CHILD_MODE=$ChildMode;ATLAS_R017_CHILD_SOURCE=$SourcePath;ATLAS_R017_CHILD_SOURCE_SHA=$SourceSha;ATLAS_R017_CHILD_STATE=$HostState;ATLAS_R017_VERIFIED_MATERIALIZER_PATH=$env:ATLAS_R017_VERIFIED_MATERIALIZER_PATH;ATLAS_R017_VERIFIED_MATERIALIZER_SHA256=$env:ATLAS_R017_VERIFIED_MATERIALIZER_SHA256;ATLAS_R017_VERIFIED_CLASSIFIER_PATH=$env:ATLAS_R017_VERIFIED_CLASSIFIER_PATH;ATLAS_R017_VERIFIED_CLASSIFIER_SHA256=$env:ATLAS_R017_VERIFIED_CLASSIFIER_SHA256;ATLAS_R017_VERIFIED_FENCE_PATH=$env:ATLAS_R017_VERIFIED_FENCE_PATH;ATLAS_R017_VERIFIED_FENCE_SHA256=$env:ATLAS_R017_VERIFIED_FENCE_SHA256;ATLAS_R017_VERIFIED_NODE_PATH=$env:ATLAS_R017_VERIFIED_NODE_PATH;ATLAS_R017_VERIFIED_NODE_SHA256=$env:ATLAS_R017_VERIFIED_NODE_SHA256;ATLAS_R017_VERIFIED_TEST_REPLACEMENT_PATH=''}
}

function Start-RollbackWatchdog([string]$SourcePath, [string]$SourceSha, [string]$HostState) {
  $verified=Get-VerifiedSelfEnvironment 'Watchdog' $SourcePath $SourceSha $HostState
  if($null-ne$verified){$start=New-Object Diagnostics.ProcessStartInfo;$start.FileName=Get-ShellPath;$start.UseShellExecute=$false;$start.CreateNoWindow=$true;$arguments=@('-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',(Get-VerifiedSelfBootstrapEncoded));if($null-ne$start.PSObject.Properties['ArgumentList']){foreach($argument in $arguments){[void]$start.ArgumentList.Add([string]$argument)}}else{$start.Arguments=(($arguments|ForEach-Object{ConvertTo-ProcessArgument([string]$_)})-join' ')};foreach($key in $verified.Keys){$start.EnvironmentVariables[[string]$key]=[string]$verified[$key]};$process=New-Object Diagnostics.Process;$process.StartInfo=$start;if(-not$process.Start()){throw 'WATCHDOG_START'};return $process.Id}
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$PSCommandPath,'-Mode','Watchdog','-PrivateSourcePath',$SourcePath,'-ExpectedPrivateSourceSha256',$SourceSha,'-StatePath',$HostState,'-ExecuteProtected')
  return (Start-Process -FilePath (Get-ShellPath) -ArgumentList $arguments -WindowStyle Hidden -PassThru).Id
}

function Invoke-SelfRollback([string]$SourcePath, [string]$SourceSha, [string]$HostState) {
  $verified=Get-VerifiedSelfEnvironment 'Rollback' $SourcePath $SourceSha $HostState
  if($null-ne$verified){return Invoke-Child (Get-ShellPath) @('-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',(Get-VerifiedSelfBootstrapEncoded)) $verified 900000}
  $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$PSCommandPath,'-Mode','Rollback','-PrivateSourcePath',$SourcePath,'-ExpectedPrivateSourceSha256',$SourceSha,'-StatePath',$HostState,'-ExecuteProtected')
  return Invoke-Child (Get-ShellPath) $arguments @{} 900000
}

if ($PSCmdlet.ParameterSetName -ceq 'Source') {
  Initialize-VerifiedFenceBinding $false
  Assert-SourceContract
  Write-Result 'PASS_MAZER_MASTER_PREPARATION_R017_SOURCE' ([ordered]@{ materializer_sha256 = Get-Sha256 $Materializer; fence_host_sha256 = Get-Sha256 $Fence; credential_reads = 0; provider_reads = 0; provider_writes = 0; auth_writes = 0; live_data_writes = 0; state_writes = 0; private_files = 0 })
  exit 0
}

if($PSCmdlet.ParameterSetName-ceq'FenceProbe'){
  $probeRoot=Join-Path $Runtime ('r017 fence replacement probe '+[Guid]::NewGuid().ToString('N'));[IO.Directory]::CreateDirectory($probeRoot)|Out-Null
  $original=Join-Path $probeRoot 'fence original.ps1';$replacement=Join-Path $probeRoot 'fence replacement.ps1'
  try{[IO.File]::WriteAllText($original,'[Console]::Out.Write("R017_ORIGINAL_FENCE_BYTES")',(New-Object Text.UTF8Encoding($false)));[IO.File]::WriteAllText($replacement,'[Console]::Out.Write("R017_REPLACEMENT_MUST_NOT_RUN")',(New-Object Text.UTF8Encoding($false)));$shellPath=(Get-Process -Id $PID).Path;$probe=Invoke-VerifiedFenceChild $shellPath 'Synthetic' '' '' 30000 $original (Get-Sha256 $original) $replacement;if($probe.ExitCode-ne0-or-not[string]::IsNullOrEmpty($probe.Stderr)-or[string]$probe.Stdout.Trim()-cne'R017_ORIGINAL_FENCE_BYTES'-or(Get-Content -Raw -LiteralPath $original)-notmatch'REPLACEMENT_MUST_NOT_RUN'){throw 'FENCE_REPLACEMENT_RACE'};Write-Result 'PASS_R017_SAME_BUFFER_FENCE_REPLACEMENT_ADVERSARY' ([ordered]@{replacement_executed=$false;credential_reads=0;external_calls=0;live_data_writes=0});exit 0}finally{if(Test-Path -LiteralPath $probeRoot){Remove-Item -LiteralPath $probeRoot -Recurse -Force}}
}

if($PSCmdlet.ParameterSetName-ceq'MaterializerProbe'){
  $probeRoot=Join-Path $Root ('tmp\r017 moved worktree with spaces '+[Guid]::NewGuid().ToString('N'));[IO.Directory]::CreateDirectory($probeRoot)|Out-Null
  $probeScript=Join-Path $probeRoot 'materializer probe.mjs';$probeClassifier=Join-Path $probeRoot 'classifier dependency.mjs';$replacement=Join-Path $probeRoot 'replacement.mjs';$probeState=[pscustomobject]@{ReplacementBlocked=$false;ClassifierReplacementBlocked=$false}
  try{
    [IO.File]::WriteAllText($probeScript,"console.log(JSON.stringify({result:'PASS_ORIGINAL_MATERIALIZER_BUFFER'}));`n",(New-Object Text.UTF8Encoding($false)))
    [IO.File]::WriteAllText($probeClassifier,"export const marker='PASS_ORIGINAL_CLASSIFIER_BUFFER';`n",(New-Object Text.UTF8Encoding($false)))
    [IO.File]::WriteAllText($replacement,"console.log(JSON.stringify({result:'REPLACEMENT_EXECUTED'}));`n",(New-Object Text.UTF8Encoding($false)))
    $node=(Get-Command node -ErrorAction Stop).Source;$nodeSha=Get-Sha256 $node;$probeSha=Get-Sha256 $probeScript;$classifierSha=Get-Sha256 $probeClassifier
    $before={try{[IO.File]::Copy($replacement,$probeScript,$true)}catch{$probeState.ReplacementBlocked=$true};try{[IO.File]::Copy($replacement,$probeClassifier,$true)}catch{$probeState.ClassifierReplacementBlocked=$true}}
    $child=Invoke-VerifiedMaterializerNode $node $nodeSha $probeScript $probeSha $probeClassifier $classifierSha @($probeScript) @{} 30000 $before $probeScript $probeClassifier
    if(-not$probeState.ReplacementBlocked-or-not$probeState.ClassifierReplacementBlocked-or$child.ExitCode-ne0-or-not[string]::IsNullOrEmpty($child.Stderr)-or$child.Stdout-notmatch'PASS_ORIGINAL_MATERIALIZER_BUFFER'-or$child.Stdout-match'REPLACEMENT_EXECUTED'){throw 'MATERIALIZER_REPLACEMENT_ADVERSARY'}
    $foreign=Join-Path $PacketRoot ([Guid]::NewGuid().ToString('N'));[IO.Directory]::CreateDirectory($foreign)|Out-Null;$sentinel=Join-Path $foreign 'foreign-owner-sentinel';[IO.File]::WriteAllText($sentinel,'preserve',(New-Object Text.UTF8Encoding($false)))
    if((Remove-OwnedPrivateRoot $foreign ([Guid]::NewGuid().ToString('N')))-or-not(Test-Path -LiteralPath $sentinel -PathType Leaf)){throw 'FOREIGN_OUTPUT_REMOVED'}
    Remove-Item -LiteralPath $foreign -Recurse -Force
    [Console]::Out.WriteLine('{"result":"PASS_R017_PORTABLE_MATERIALIZER_LOCK_PROBE","moved_worktree":true,"spaces":true,"replacement_blocked":true,"classifier_replacement_blocked":true,"replacement_executed":false,"foreign_output_preserved":true,"external_calls":0,"credential_reads":0,"live_data_writes":0}');exit 0
  }finally{if(Test-Path -LiteralPath $probeRoot){Remove-Item -LiteralPath $probeRoot -Recurse -Force}}
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
$privateRootOwnerToken = $null
$managementToken = $null
$masterDatabaseUrl = $null
$verifiedMaterializerPath = $null
$verifiedMaterializerSha = $null
$verifiedClassifierPath = $null
$verifiedClassifierSha = $null
$verifiedNodePath = $null
$verifiedNodeSha = $null
$verifiedFencePath = $null
$verifiedFenceSha = $null
$state = $null
$providerWrites = 0
$databaseTransactions = 0
$fenceHasEffects = $false
try {
  Initialize-VerifiedFenceBinding $true
  Assert-SourceContract
  $verifiedMaterializerPath=[IO.Path]::GetFullPath([string]$env:ATLAS_R017_VERIFIED_MATERIALIZER_PATH);$verifiedMaterializerSha=[string]$env:ATLAS_R017_VERIFIED_MATERIALIZER_SHA256
  $verifiedClassifierPath=[IO.Path]::GetFullPath([string]$env:ATLAS_R017_VERIFIED_CLASSIFIER_PATH);$verifiedClassifierSha=[string]$env:ATLAS_R017_VERIFIED_CLASSIFIER_SHA256
  $verifiedNodePath=[IO.Path]::GetFullPath([string]$env:ATLAS_R017_VERIFIED_NODE_PATH);$verifiedNodeSha=[string]$env:ATLAS_R017_VERIFIED_NODE_SHA256
  $verifiedFencePath=$script:VerifiedFencePath;$verifiedFenceSha=$script:VerifiedFenceSha
  if($verifiedMaterializerPath-cne[IO.Path]::GetFullPath($Materializer)-or$verifiedClassifierPath-cne[IO.Path]::GetFullPath($FenceClassifier)-or$verifiedFencePath-cne[IO.Path]::GetFullPath($Fence)-or$verifiedMaterializerSha-cnotmatch'^[a-f0-9]{64}$'-or$verifiedClassifierSha-cnotmatch'^[a-f0-9]{64}$'-or$verifiedFenceSha-cnotmatch'^[a-f0-9]{64}$'-or$verifiedNodeSha-cnotmatch'^[a-f0-9]{64}$'){throw 'MATERIALIZER_BINDING'}
  if (-not (Test-Path -LiteralPath $PacketRoot)) { [IO.Directory]::CreateDirectory($PacketRoot) | Out-Null }
  Assert-NoReparse $PacketRoot $Secrets
  $privateRoot = Join-Path $PacketRoot ([Guid]::NewGuid().ToString('N'))
  $privateRootOwnerToken = [Guid]::NewGuid().ToString('N')
  if(Test-Path -LiteralPath $privateRoot){throw 'PRIVATE_OUTPUT_PREEXISTS'}
  $mazerRepository = Find-MazerRepository
  $materialized = Invoke-VerifiedMaterializerNode $verifiedNodePath $verifiedNodeSha $verifiedMaterializerPath $verifiedMaterializerSha $verifiedClassifierPath $verifiedClassifierSha @($verifiedMaterializerPath,'--input',$sourcePath,'--output',$privateRoot,'--mazer-repository',$mazerRepository,'--owner-token',$privateRootOwnerToken) @{} 120000
  if ($materialized.ExitCode -ne 0) { throw 'PRIVATE_MATERIALIZATION_FAILED' }
  if(-not(Test-Path -LiteralPath $privateRoot -PathType Container)){throw 'PRIVATE_MATERIALIZATION_MISSING'}
  Assert-NoReparse $privateRoot $Secrets
  $manifestPath = Join-Path $privateRoot 'manifest.json'
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  if ([int]$manifest.auth_counts.imports -ne 4 -or [int]$manifest.auth_counts.binds -ne 14 -or [int]$manifest.auth_counts.retained_edges -ne 2 -or [int]$manifest.auth_counts.final_edges -ne 20 -or [int]$manifest.auth_counts.expected_target_users -ne 118) { throw 'AUTH_TOPOLOGY_MANIFEST_DRIFT' }
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
  $materializerUri = ([Uri]$verifiedMaterializerPath).AbsoluteUri
  $recovery = Invoke-VerifiedMaterializerNode $verifiedNodePath $verifiedNodeSha $verifiedMaterializerPath $verifiedMaterializerSha $verifiedClassifierPath $verifiedClassifierSha @('-e', "import(process.argv[1]).then(m=>console.log(JSON.stringify(m.classifyHostRecovery(JSON.parse(process.argv[2])))))", $materializerUri, $stateJson) @{} 30000
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
  Write-Result 'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER' ([ordered]@{ phase = [string]$state.phase; master_hook_enabled = $true; legacy_signup_and_acl_restored = $true; fresh_dual_refence_and_catchup_required_for_cutover = $true; fence_lease_seconds = $HardFenceLeaseSeconds; rollback_initiation_deadline_seconds = $RollbackDeadlineSeconds; provider_writes = $providerWrites; database_transactions = $databaseTransactions; final_identity_edges = 20; profiles = 13; player = 17; ai = 17; receipts = 1887 })
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
  [void](Remove-OwnedPrivateRoot $privateRoot $privateRootOwnerToken)
}
