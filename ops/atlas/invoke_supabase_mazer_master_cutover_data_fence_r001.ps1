[CmdletBinding(DefaultParameterSetName = 'Source')]
param(
  [Parameter(Mandatory = $true, ParameterSetName = 'Source')]
  [switch]$SourceOnlyValidate,

  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')]
  [ValidateSet('Forward', 'Reverse', 'Rollback')]
  [string]$Mode,

  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')]
  [string]$InputPath,

  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')]
  [string]$StatePath,

  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')]
  [ValidatePattern('^[a-f0-9]{64}$')]
  [string]$ExpectedInputSha256,

  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')]
  [switch]$ExecuteProtected
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$RunningOnWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$PathComparison = if ($RunningOnWindows) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
$DirectorySeparators = [char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)

$AtlasRoot = [IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot, '..', '..'))
$Classifier = Join-Path $PSScriptRoot 'classify_supabase_mazer_master_cutover_data_fence_r001.mjs'
$LegacyProjectRef = 'geknvnrmktchljnyddwp'
$LegacySchema = 'public'
$MasterProjectRef = 'bxtcuhkotumitoqtrcej'
$MasterSchema = 'mazer'
$CredentialTarget = 'Supabase CLI:supabase'
$ApiBase = 'https://api.supabase.com'
$SecretPacketRoot = [IO.Path]::Combine($AtlasRoot, 'secrets', 'packet', 'mazer-master-cutover-data-fence-r001')
$RuntimeRoot = [IO.Path]::Combine($AtlasRoot, 'runtime', 'atlas')
$SecretRoot = [IO.Path]::Combine($AtlasRoot, 'secrets')
$RequiredResultSchema = 'atlas.supabase.mazer-master-cutover-data-fence-classification.v1'
$ExpectedTables = @('mazer_profiles','mazer_progression_states','mazer_ai_progression_states','mazer_cycle_receipts')
$ExpectedMutatingRpcs = @(
  'mazer_initialize_progression(uuid)',
  'mazer_complete_level(bigint,uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb)',
  'mazer_complete_ai_level(uuid,text,integer,integer,uuid,text,integer,text,timestamp with time zone,jsonb)',
  'mazer_reset_progression(bigint,uuid)'
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

function Get-CanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or $Path.IndexOf([char]0) -ge 0) { throw 'LOCAL_PATH_SHAPE' }
  return [IO.Path]::GetFullPath($Path)
}

function Remove-TrailingDirectorySeparators([string]$Path) {
  return $Path.TrimEnd($DirectorySeparators)
}

function Test-CanonicalPathUnder([string]$Candidate, [string]$Root) {
  $canonicalCandidate = Get-CanonicalPath $Candidate
  $prefix = (Remove-TrailingDirectorySeparators (Get-CanonicalPath $Root)) + [IO.Path]::DirectorySeparatorChar
  return $canonicalCandidate.StartsWith($prefix, $PathComparison)
}

function Assert-PathUnder([string]$Path, [string[]]$Roots) {
  $candidate = Get-CanonicalPath $Path
  foreach ($root in $Roots) {
    if (Test-CanonicalPathUnder $candidate $root) { return $candidate }
  }
  throw 'LOCAL_PATH_OUTSIDE_ALLOWED_ROOT'
}

function Assert-NoReparseComponents([string]$Path, [string]$Boundary) {
  $candidate = Get-CanonicalPath $Path
  $stop = Remove-TrailingDirectorySeparators (Get-CanonicalPath $Boundary)
  while ($true) {
    if (Test-Path -LiteralPath $candidate) {
      $item = Get-Item -LiteralPath $candidate -Force
      if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'LOCAL_PATH_REPARSE_POINT' }
    }
    if ((Remove-TrailingDirectorySeparators $candidate).Equals($stop, $PathComparison)) { return }
    $parent = Split-Path -Parent $candidate
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -ceq $candidate) { throw 'LOCAL_PATH_BOUNDARY_DRIFT' }
    $candidate = $parent
  }
}

function ConvertTo-SafeJson([object]$Value) {
  $text = $Value | ConvertTo-Json -Compress -Depth 8
  if ($text -match '(?i)access[_-]?token|refresh[_-]?token|service[_-]?role|sb_secret_|authorization|password|postgres(?:ql)?://|@') {
    throw 'OUTPUT_DISCLOSURE'
  }
  return $text
}

function Assert-PlatformPathContract {
  $probeBase = Get-CanonicalPath ([IO.Path]::Combine([IO.Path]::GetTempPath(), 'atlas-path-contract-r001'))
  $probeChild = [IO.Path]::Combine($probeBase, 'child', 'packet.json')
  $probeSibling = $probeBase + '-sibling' + [IO.Path]::DirectorySeparatorChar + 'packet.json'
  if ((Assert-PathUnder $probeChild @($probeBase)) -cne (Get-CanonicalPath $probeChild)) { throw 'LOCAL_PATH_PLATFORM_CONTAINMENT' }
  try { $null = Assert-PathUnder $probeSibling @($probeBase); throw 'LOCAL_PATH_SIBLING_ACCEPTED' } catch { if ($_.Exception.Message -cne 'LOCAL_PATH_OUTSIDE_ALLOWED_ROOT') { throw } }
  $traversal = [IO.Path]::Combine($probeBase, 'child', '..', '..', 'escape.json')
  try { $null = Assert-PathUnder $traversal @($probeBase); throw 'LOCAL_PATH_TRAVERSAL_ACCEPTED' } catch { if ($_.Exception.Message -cne 'LOCAL_PATH_OUTSIDE_ALLOWED_ROOT') { throw } }
  if ($RunningOnWindows) {
    if (-not (Test-CanonicalPathUnder $probeChild $probeBase.ToUpperInvariant())) { throw 'LOCAL_PATH_WINDOWS_CASE_BEHAVIOR' }
  }
  elseif (Test-CanonicalPathUnder $probeChild $probeBase.ToUpperInvariant()) {
    throw 'LOCAL_PATH_POSIX_CASE_BEHAVIOR'
  }
  $tempBoundary = Get-CanonicalPath ([IO.Path]::GetTempPath())
  $probeId = [Guid]::NewGuid().ToString('N')
  $reparseRoot = [IO.Path]::Combine($tempBoundary, 'atlas-path-reparse-r001-' + $probeId)
  $reparseOutside = [IO.Path]::Combine($tempBoundary, 'atlas-path-reparse-outside-r001-' + $probeId)
  $reparseLink = [IO.Path]::Combine($reparseRoot, 'link')
  if (-not (Test-CanonicalPathUnder $reparseRoot $tempBoundary) -or -not (Test-CanonicalPathUnder $reparseOutside $tempBoundary)) { throw 'LOCAL_PATH_TEST_SCOPE' }
  try {
    [IO.Directory]::CreateDirectory($reparseRoot) | Out-Null
    [IO.Directory]::CreateDirectory($reparseOutside) | Out-Null
    $linkType = if ($RunningOnWindows) { 'Junction' } else { 'SymbolicLink' }
    New-Item -ItemType $linkType -Path $reparseLink -Target $reparseOutside -ErrorAction Stop | Out-Null
    try { Assert-NoReparseComponents ([IO.Path]::Combine($reparseLink, 'packet.json')) $reparseRoot; throw 'LOCAL_PATH_REPARSE_ACCEPTED' } catch { if ($_.Exception.Message -cne 'LOCAL_PATH_REPARSE_POINT') { throw } }
  }
  finally {
    if (Test-Path -LiteralPath $reparseLink) { Remove-Item -LiteralPath $reparseLink -Force }
    if (Test-Path -LiteralPath $reparseRoot) { Remove-Item -LiteralPath $reparseRoot -Recurse -Force }
    if (Test-Path -LiteralPath $reparseOutside) { Remove-Item -LiteralPath $reparseOutside -Recurse -Force }
  }
}

function Write-SafeResult([string]$Result, [System.Collections.IDictionary]$Extra = @{}) {
  $value = [ordered]@{
    schema = 'atlas.supabase.mazer-master-cutover-data-fence-host-result.v1'
    result = $Result
    legacy_project_ref = $LegacyProjectRef
    legacy_schema = $LegacySchema
    master_project_ref = $MasterProjectRef
    master_schema = $MasterSchema
    retries = 0
    raw_identifiers_emitted = $false
    raw_records_emitted = $false
    pii_emitted = $false
    secrets_emitted = $false
  }
  foreach ($key in $Extra.Keys) { $value[$key] = $Extra[$key] }
  [Console]::Out.WriteLine((ConvertTo-SafeJson $value))
}

function ConvertTo-ProcessArgument([string]$Argument) {
  if ([string]::IsNullOrEmpty($Argument)) { return '""' }
  if ($Argument -notmatch '[\s"]') { return $Argument }
  $builder = New-Object Text.StringBuilder
  [void]$builder.Append('"')
  $backslashes = 0
  foreach ($character in $Argument.ToCharArray()) {
    if ($character -eq '\') {
      $backslashes += 1
      continue
    }
    if ($character -eq '"') {
      [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
      [void]$builder.Append('"')
      $backslashes = 0
      continue
    }
    if ($backslashes -gt 0) { [void]$builder.Append(('\' * $backslashes)); $backslashes = 0 }
    [void]$builder.Append($character)
  }
  if ($backslashes -gt 0) { [void]$builder.Append(('\' * ($backslashes * 2))) }
  [void]$builder.Append('"')
  return $builder.ToString()
}

function Invoke-ProcessSanitized(
  [string]$FileName,
  [string[]]$Arguments,
  [System.Collections.IDictionary]$Environment = @{},
  [int]$TimeoutMs = 180000
) {
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = $FileName
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  if ($null -ne $psi.PSObject.Properties['ArgumentList']) {
    foreach ($argument in $Arguments) { [void]$psi.ArgumentList.Add($argument) }
  }
  else {
    $psi.Arguments = (($Arguments | ForEach-Object { ConvertTo-ProcessArgument ([string]$_) }) -join ' ')
  }
  $processEnvironment = if ($null -ne $psi.PSObject.Properties['Environment']) { $psi.Environment } else { $psi.EnvironmentVariables }
  foreach ($key in $Environment.Keys) { $processEnvironment[[string]$key] = [string]$Environment[$key] }
  $process = New-Object Diagnostics.Process
  $process.StartInfo = $psi
  try {
    if (-not $process.Start()) { throw 'CHILD_START_FAILED' }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($TimeoutMs)) {
      try { $process.Kill() } catch {}
      throw 'CHILD_TIMEOUT'
    }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    [void]$stderrTask.GetAwaiter().GetResult()
    return [pscustomobject]@{ ExitCode = $process.ExitCode; Stdout = $stdout }
  }
  finally {
    foreach ($key in $Environment.Keys) { [void]$processEnvironment.Remove([string]$key) }
    $process.Dispose()
  }
}

function Invoke-Classifier(
  [string]$PrivateRoot,
  [string]$ResolvedInput
) {
  $plan = Join-Path $PrivateRoot 'private-plan.json'
  $transaction = Join-Path $PrivateRoot 'transaction.sql'
  $sourceObservation = Join-Path $PrivateRoot 'source-observation.sql'
  $fence = Join-Path $PrivateRoot 'fence.sql'
  $writerCapture = Join-Path $PrivateRoot 'writer-capture.sql'
  $aclObservation = Join-Path $PrivateRoot 'acl-observation.sql'
  $restore = Join-Path $PrivateRoot 'restore.sql'
  $observedFence = Join-Path $PrivateRoot 'observed-fence.sql'
  $observedRestore = Join-Path $PrivateRoot 'observed-restore.sql'
  $legacyFence = Join-Path $PrivateRoot 'legacy-fence.sql'
  $legacyWriterCapture = Join-Path $PrivateRoot 'legacy-writer-capture.sql'
  $legacyAclObservation = Join-Path $PrivateRoot 'legacy-acl-observation.sql'
  $legacyRestore = Join-Path $PrivateRoot 'legacy-restore.sql'
  $signupAdmissionObservation = Join-Path $PrivateRoot 'signup-admission-observation.sql'
  $signupAdmissionFence = Join-Path $PrivateRoot 'signup-admission-fence.sql'
  $signupAdmissionRestore = Join-Path $PrivateRoot 'signup-admission-restore.sql'
  $arguments = @(
    $Classifier,
    '--input', $ResolvedInput,
    '--private-plan', $plan,
    '--private-sql', $transaction,
    '--private-source-observation-sql', $sourceObservation,
    '--private-fence-sql', $fence,
    '--private-writer-capture-sql', $writerCapture,
    '--private-acl-observation-sql', $aclObservation,
    '--private-restore-sql', $restore,
    '--private-legacy-fence-sql', $legacyFence,
    '--private-legacy-writer-capture-sql', $legacyWriterCapture,
    '--private-legacy-acl-observation-sql', $legacyAclObservation,
    '--private-legacy-restore-sql', $legacyRestore,
    '--private-signup-admission-observation-sql', $signupAdmissionObservation,
    '--private-signup-admission-fence-sql', $signupAdmissionFence,
    '--private-signup-admission-restore-sql', $signupAdmissionRestore
  )
  $child = Invoke-ProcessSanitized -FileName (Get-Command node -ErrorAction Stop).Source -Arguments $arguments -TimeoutMs 30000
  if ([string]::IsNullOrWhiteSpace($child.Stdout) -or $child.Stdout.Length -gt 65536) { throw 'CLASSIFIER_OUTPUT_SHAPE' }
  try { $receipt = $child.Stdout | ConvertFrom-Json } catch { throw 'CLASSIFIER_OUTPUT_JSON' }
  if ($receipt.schema -cne $RequiredResultSchema) { throw 'CLASSIFIER_OUTPUT_SCHEMA' }
  if ($child.ExitCode -ne 0 -or [string]$receipt.result -notmatch '^PASS_') {
    throw ('CLASSIFIER_HOLD_' + ([string]$receipt.category -replace '[^A-Z0-9_]', ''))
  }
  if ($receipt.raw_identifiers_emitted -ne $false -or $receipt.raw_records_emitted -ne $false -or $receipt.pii_emitted -ne $false -or $receipt.secrets_emitted -ne $false) {
    throw 'CLASSIFIER_DISCLOSURE'
  }
  foreach ($file in @($plan,$transaction,$sourceObservation,$fence,$writerCapture,$aclObservation,$restore,$legacyFence,$legacyWriterCapture,$legacyAclObservation,$legacyRestore,$signupAdmissionObservation,$signupAdmissionFence,$signupAdmissionRestore)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-Item -LiteralPath $file).Length -lt 16) { throw 'PRIVATE_PLAN_MISSING' }
  }
  return [pscustomobject]@{
    Receipt = $receipt
    Plan = $plan
    TransactionSql = $transaction
    SourceObservationSql = $sourceObservation
    FenceSql = $fence
    WriterCaptureSql = $writerCapture
    AclObservationSql = $aclObservation
    RestoreSql = $restore
    ObservedFenceSql = $observedFence
    ObservedRestoreSql = $observedRestore
    LegacyFenceSql = $legacyFence
    LegacyWriterCaptureSql = $legacyWriterCapture
    LegacyAclObservationSql = $legacyAclObservation
    LegacyRestoreSql = $legacyRestore
    SignupAdmissionObservationSql = $signupAdmissionObservation
    SignupAdmissionFenceSql = $signupAdmissionFence
    SignupAdmissionRestoreSql = $signupAdmissionRestore
  }
}

function Assert-DatabaseUrl([string]$Value, [string]$ExpectedProjectRef) {
  if ([string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt 8192) { throw 'DATABASE_URL_MISSING' }
  try { $uri = [Uri]$Value } catch { throw 'DATABASE_URL_SHAPE' }
  if ($uri.Scheme -notin @('postgres','postgresql')) { throw 'DATABASE_URL_BINDING' }
  $directHost = "db.$ExpectedProjectRef.supabase.co"
  $isDirect = $uri.Host -ceq $directHost
  $poolerUser = ([string]$uri.UserInfo -split ':', 2)[0]
  $isSessionPooler = $uri.Host -match '^[a-z0-9-]+\.pooler\.supabase\.com$' -and $poolerUser -ceq "postgres.$ExpectedProjectRef"
  if (-not $isDirect -and -not $isSessionPooler) { throw 'DATABASE_URL_BINDING' }
  if ($uri.Port -eq 6543) { throw 'TRANSACTION_POOLER_NOT_ALLOWED' }
  if ($uri.Port -ne 5432) { throw 'DATABASE_PORT_BINDING' }
  return $Value
}

function Invoke-PsqlPrivate([string]$DatabaseUrl, [string]$SqlPath) {
  $psql = (Get-Command psql -ErrorAction Stop).Source
  $environment = @{
    PGDATABASE = $DatabaseUrl
    PGCONNECT_TIMEOUT = '15'
    PGAPPNAME = 'atlas-mazer-master-cutover-data-fence-r001'
  }
  $child = Invoke-ProcessSanitized -FileName $psql -Arguments @('-X','--no-psqlrc','--set','ON_ERROR_STOP=1','--file',$SqlPath) -Environment $environment -TimeoutMs 180000
  if ($child.ExitCode -ne 0) { throw 'PSQL_TRANSACTION_FAILED' }
}

function Invoke-PsqlJsonPrivate([string]$DatabaseUrl, [string]$SqlPath, [string]$OutputPath, [string]$FailureCategory) {
  $psql = (Get-Command psql -ErrorAction Stop).Source
  $environment = @{
    PGDATABASE = $DatabaseUrl
    PGCONNECT_TIMEOUT = '15'
    PGAPPNAME = 'atlas-mazer-master-cutover-acl-r001'
  }
  $child = Invoke-ProcessSanitized -FileName $psql -Arguments @('-X','--no-psqlrc','--quiet','--no-align','--tuples-only','--set','ON_ERROR_STOP=1','--file',$SqlPath) -Environment $environment -TimeoutMs 180000
  if ($child.ExitCode -ne 0) { throw $FailureCategory }
  if ([string]::IsNullOrWhiteSpace($child.Stdout) -or $child.Stdout.Length -gt 1048576) { throw ($FailureCategory + '_OUTPUT_SHAPE') }
  $lines = @($child.Stdout -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  if ($lines.Count -ne 1) { throw ($FailureCategory + '_OUTPUT_CARDINALITY') }
  try { $null = $lines[0] | ConvertFrom-Json } catch { throw ($FailureCategory + '_OUTPUT_JSON') }
  $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($lines[0] + "`n")
  $stream = New-Object IO.FileStream($OutputPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
  try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}

function Invoke-AclVerifier(
  [string]$ResolvedInput,
  [string]$ObservationPath,
  [ValidateSet('primary','legacy')][string]$Side,
  [string]$ObservedRestorePath = $null,
  [string]$ObservedFencePath = $null,
  [string]$ExpectedObservationPath = $null
) {
  $arguments = @($Classifier, '--input', $ResolvedInput, '--verify-acl-observation', $ObservationPath, '--acl-side', $Side)
  if (-not [string]::IsNullOrWhiteSpace($ObservedRestorePath)) { $arguments += @('--private-observed-restore-sql', $ObservedRestorePath) }
  if (-not [string]::IsNullOrWhiteSpace($ObservedFencePath)) { $arguments += @('--private-observed-fence-sql', $ObservedFencePath) }
  if (-not [string]::IsNullOrWhiteSpace($ExpectedObservationPath)) { $arguments += @('--expected-acl-observation', $ExpectedObservationPath) }
  $child = Invoke-ProcessSanitized -FileName (Get-Command node -ErrorAction Stop).Source -Arguments $arguments -TimeoutMs 30000
  if ([string]::IsNullOrWhiteSpace($child.Stdout) -or $child.Stdout.Length -gt 65536) { throw 'ACL_VERIFIER_OUTPUT_SHAPE' }
  try { $receipt = $child.Stdout | ConvertFrom-Json } catch { throw 'ACL_VERIFIER_OUTPUT_JSON' }
  if ([string]$receipt.schema -cne 'atlas.supabase.mazer-master-cutover-acl-observation.v1') { throw 'ACL_VERIFIER_OUTPUT_SCHEMA' }
  if ($receipt.raw_identifiers_emitted -ne $false -or $receipt.raw_records_emitted -ne $false -or $receipt.pii_emitted -ne $false -or $receipt.secrets_emitted -ne $false) { throw 'ACL_VERIFIER_DISCLOSURE' }
  if ($child.ExitCode -ne 0 -or [string]$receipt.result -cne 'PASS_ACL_PREIMAGE_MATCH') { throw 'LIVE_ACL_OR_CATALOG_PREIMAGE_DRIFT' }
  return $receipt
}

function Invoke-AclRecoveryClassifier(
  [string]$ResolvedInput,
  [string]$JournaledObservationPath,
  [string]$CurrentObservationPath,
  [ValidateSet('primary','legacy')][string]$Side
) {
  $arguments = @(
    $Classifier,
    '--input', $ResolvedInput,
    '--classify-acl-recovery', $CurrentObservationPath,
    '--journaled-acl-observation', $JournaledObservationPath,
    '--acl-side', $Side
  )
  $child = Invoke-ProcessSanitized -FileName (Get-Command node -ErrorAction Stop).Source -Arguments $arguments -TimeoutMs 30000
  if ([string]::IsNullOrWhiteSpace($child.Stdout) -or $child.Stdout.Length -gt 65536) { throw 'ACL_RECOVERY_OUTPUT_SHAPE' }
  try { $receipt = $child.Stdout | ConvertFrom-Json } catch { throw 'ACL_RECOVERY_OUTPUT_JSON' }
  if ([string]$receipt.schema -cne 'atlas.supabase.mazer-master-cutover-acl-recovery.v1') { throw 'ACL_RECOVERY_OUTPUT_SCHEMA' }
  if ($receipt.raw_identifiers_emitted -ne $false -or $receipt.raw_records_emitted -ne $false -or $receipt.pii_emitted -ne $false -or $receipt.secrets_emitted -ne $false) { throw 'ACL_RECOVERY_DISCLOSURE' }
  if ($child.ExitCode -ne 0 -or [string]$receipt.result -ceq 'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS') { throw 'ACL_RECOVERY_STATE_AMBIGUOUS' }
  if ([string]$receipt.result -notin @('PASS_ACL_PREIMAGE_ALREADY_PRESENT','PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED')) { throw 'ACL_RECOVERY_RESULT' }
  return $receipt
}

function Invoke-WriterCaptureVerifier(
  [string]$ResolvedInput,
  [string]$CapturePath,
  [ValidateSet('primary','legacy')][string]$Side,
  [string]$DrainSqlPath,
  [string]$LockBarrierSqlPath
) {
  $arguments = @(
    $Classifier,
    '--input', $ResolvedInput,
    '--verify-writer-capture', $CapturePath,
    '--writer-side', $Side,
    '--private-writer-drain-sql', $DrainSqlPath,
    '--private-lock-barrier-sql', $LockBarrierSqlPath
  )
  $child = Invoke-ProcessSanitized -FileName (Get-Command node -ErrorAction Stop).Source -Arguments $arguments -TimeoutMs 30000
  if ([string]::IsNullOrWhiteSpace($child.Stdout) -or $child.Stdout.Length -gt 65536) { throw 'WRITER_CAPTURE_VERIFIER_OUTPUT_SHAPE' }
  try { $receipt = $child.Stdout | ConvertFrom-Json } catch { throw 'WRITER_CAPTURE_VERIFIER_OUTPUT_JSON' }
  if ([string]$receipt.schema -cne 'atlas.supabase.mazer-master-cutover-writer-capture.v1') { throw 'WRITER_CAPTURE_VERIFIER_OUTPUT_SCHEMA' }
  if ($receipt.raw_identifiers_emitted -ne $false -or $receipt.raw_records_emitted -ne $false -or $receipt.pii_emitted -ne $false -or $receipt.secrets_emitted -ne $false) { throw 'WRITER_CAPTURE_VERIFIER_DISCLOSURE' }
  if ($child.ExitCode -ne 0 -or [string]$receipt.result -cne 'PASS_WRITER_SET_CAPTURE_BOUND') { throw 'WRITER_CAPTURE_BINDING_FAILED' }
  foreach ($file in @($DrainSqlPath,$LockBarrierSqlPath)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-Item -LiteralPath $file).Length -lt 16) { throw 'WRITER_CAPTURE_PLAN_MISSING' }
  }
  return $receipt
}

function Assert-WriterStepReceipt(
  [string]$Path,
  [string]$ExpectedResult,
  [string]$ExpectedDigest,
  [int]$ExpectedCount,
  [string]$TimestampProperty
) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'WRITER_STEP_RECEIPT_MISSING' }
  try { $receipt = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw 'WRITER_STEP_RECEIPT_JSON' }
  if ([string]$receipt.result -cne $ExpectedResult -or [string]$receipt.writer_set_digest -cne $ExpectedDigest -or [int]$receipt.writer_count -ne $ExpectedCount) { throw 'WRITER_STEP_RECEIPT_BINDING' }
  if ($ExpectedResult -ceq 'PASS_WRITER_LOCK_BARRIER' -and ([string]$receipt.mutation_gate_state -cne 'FENCED' -or [string]$receipt.mutation_gate_digest -notmatch '^[a-f0-9]{64}$' -or [string]$receipt.install_disposition -notin @('INSTALLED_FROM_ABSENT','RECONCILED_EXACT_FENCED'))) { throw 'MUTATION_GATE_BARRIER_BINDING' }
  try { $observedAt = [DateTimeOffset]::Parse([string]$receipt.$TimestampProperty, [Globalization.CultureInfo]::InvariantCulture) } catch { throw 'WRITER_STEP_RECEIPT_TIMESTAMP' }
  return [pscustomobject]@{ Receipt = $receipt; ObservedAt = $observedAt }
}

function Assert-WriterRevokeReceipt(
  [string]$Path,
  [string]$ExpectedSchema,
  [string]$ExpectedAclDigest
) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'WRITER_REVOKE_RECEIPT_MISSING' }
  try { $receipt = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw 'WRITER_REVOKE_RECEIPT_JSON' }
  if ([string]$receipt.result -cne 'PASS_WRITER_REVOKE_COMMITTED' -or [string]$receipt.schema -cne $ExpectedSchema -or [string]$receipt.acl_preimage_digest -cne $ExpectedAclDigest) { throw 'WRITER_REVOKE_RECEIPT_BINDING' }
  try { $revokedAt = [DateTimeOffset]::Parse([string]$receipt.revoked_at, [Globalization.CultureInfo]::InvariantCulture) } catch { throw 'WRITER_REVOKE_RECEIPT_TIMESTAMP' }
  return $revokedAt
}

function Assert-SignupAdmissionReceipt(
  [string]$Path,
  [ValidateSet('PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT','PASS_SIGNUP_ADMISSION_FENCED','PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED')]
  [string]$ExpectedResult
) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'SIGNUP_ADMISSION_RECEIPT_MISSING' }
  try { $receipt = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw 'SIGNUP_ADMISSION_RECEIPT_JSON' }
  $expectedSchema = if ($ExpectedResult -ceq 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT') { 'atlas.supabase.mazer-master-signup-admission-fence-observation.v1' } else { 'atlas.supabase.mazer-master-signup-admission-fence-receipt.v1' }
  if ([string]$receipt.schema -cne $expectedSchema -or [string]$receipt.result -cne $ExpectedResult -or $receipt.claim_path_verified -ne $true) { throw 'SIGNUP_ADMISSION_RECEIPT_BINDING' }
  if ($ExpectedResult -ceq 'PASS_SIGNUP_ADMISSION_FENCED') {
    if ([string]$receipt.state -cne 'FENCED' -or [int]$receipt.writer_count -lt 0 -or [string]$receipt.writer_set_digest -notmatch '^[a-f0-9]{64}$' -or [string]$receipt.install_disposition -notin @('INSTALLED_FROM_ABSENT','RECONCILED_EXACT_FENCED')) { throw 'SIGNUP_ADMISSION_FENCE_PROOF' }
    try { $timestamp = [DateTimeOffset]::Parse([string]$receipt.barrier_at, [Globalization.CultureInfo]::InvariantCulture) } catch { throw 'SIGNUP_ADMISSION_BARRIER_TIMESTAMP' }
  }
  elseif ($ExpectedResult -ceq 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT') {
    if ([string]$receipt.state -cne 'ABSENT') { throw 'SIGNUP_ADMISSION_PREIMAGE_DRIFT' }
    try { $timestamp = [DateTimeOffset]::Parse([string]$receipt.observed_at, [Globalization.CultureInfo]::InvariantCulture) } catch { throw 'SIGNUP_ADMISSION_OBSERVATION_TIMESTAMP' }
  }
  else {
    if ([string]$receipt.state -cne 'ABSENT') { throw 'SIGNUP_ADMISSION_RESTORE_POSTIMAGE' }
    try { $timestamp = [DateTimeOffset]::Parse([string]$receipt.restored_at, [Globalization.CultureInfo]::InvariantCulture) } catch { throw 'SIGNUP_ADMISSION_RESTORE_TIMESTAMP' }
  }
  return [pscustomobject]@{ Receipt = $receipt; ObservedAt = $timestamp }
}

function Read-WriterDrainReceipt(
  [string]$Path,
  [string]$ExpectedDigest,
  [int]$ExpectedCount
) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'WRITER_DRAIN_RECEIPT_MISSING' }
  try { $receipt = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw 'WRITER_DRAIN_RECEIPT_JSON' }
  $remaining = [int]$receipt.remaining_writer_count
  if ([string]$receipt.writer_set_digest -cne $ExpectedDigest -or [int]$receipt.writer_count -ne $ExpectedCount -or $remaining -lt 0 -or $remaining -gt $ExpectedCount) { throw 'WRITER_DRAIN_RECEIPT_BINDING' }
  if (($remaining -eq 0 -and [string]$receipt.result -cne 'PASS_CAPTURED_WRITERS_DRAINED') -or ($remaining -gt 0 -and [string]$receipt.result -cne 'WAIT_CAPTURED_WRITERS')) { throw 'WRITER_DRAIN_RECEIPT_RESULT' }
  try { $observedAt = [DateTimeOffset]::Parse([string]$receipt.observed_at, [Globalization.CultureInfo]::InvariantCulture) } catch { throw 'WRITER_DRAIN_RECEIPT_TIMESTAMP' }
  return [pscustomobject]@{ Receipt = $receipt; ObservedAt = $observedAt; Remaining = $remaining }
}

function Invoke-ExactWriterDrainBarrier(
  [string]$DatabaseUrl,
  [string]$ResolvedInput,
  [string]$WriterCaptureSql,
  [string]$PrivateRoot,
  [ValidateSet('LEGACY','MASTER')][string]$PhasePrefix,
  [object]$State,
  [string]$ResolvedStatePath,
  [ValidateSet('primary','legacy')][string]$Side = 'primary',
  [switch]$NoPhaseJournal
) {
  if (-not $NoPhaseJournal) { Set-StatePhase $State ($PhasePrefix + '_WRITER_SET_CAPTURING') $ResolvedStatePath }
  $capturePath = Join-Path $PrivateRoot (($PhasePrefix.ToLowerInvariant()) + '-writer-capture.json')
  Invoke-PsqlJsonPrivate $DatabaseUrl $WriterCaptureSql $capturePath ($PhasePrefix + '_WRITER_CAPTURE_FAILED')
  $drainSql = Join-Path $PrivateRoot (($PhasePrefix.ToLowerInvariant()) + '-writer-drain.sql')
  $lockBarrierSql = Join-Path $PrivateRoot (($PhasePrefix.ToLowerInvariant()) + '-lock-barrier.sql')
  $captureReceipt = Invoke-WriterCaptureVerifier $ResolvedInput $capturePath $Side $drainSql $lockBarrierSql
  if (-not $NoPhaseJournal -and $null -ne $State.primary_writer_revoke_committed_at) {
    try {
      $revokedAt = [DateTimeOffset]::Parse([string]$State.primary_writer_revoke_committed_at, [Globalization.CultureInfo]::InvariantCulture)
      $capturedAt = [DateTimeOffset]::Parse([string]$captureReceipt.captured_at, [Globalization.CultureInfo]::InvariantCulture)
    }
    catch { throw 'WRITER_CAPTURE_ORDER_TIMESTAMP' }
    if ($capturedAt -lt $revokedAt) { throw 'WRITER_CAPTURE_BEFORE_REVOKE_COMMIT' }
  }
  if (-not $NoPhaseJournal) {
    $State.journaled_primary_writer_capture = Get-Content -LiteralPath $capturePath -Raw | ConvertFrom-Json
    $State.journaled_primary_writer_count = [int]$captureReceipt.writer_count
    $State.journaled_primary_writer_set_digest = [string]$captureReceipt.writer_set_digest
    $State.journaled_primary_writer_capture_binding_digest = [string]$captureReceipt.writer_capture_binding_digest
    $State.primary_writer_set_captured_at = [string]$captureReceipt.captured_at
    Set-StatePhase $State ($PhasePrefix + '_WRITER_SET_CAPTURED') $ResolvedStatePath
  }

  if (-not $NoPhaseJournal) { Set-StatePhase $State ($PhasePrefix + '_WRITERS_DRAINING') $ResolvedStatePath }
  $drainStopwatch = [Diagnostics.Stopwatch]::StartNew()
  $drainAttempt = 0
  do {
    $drainProof = Join-Path $PrivateRoot (($PhasePrefix.ToLowerInvariant()) + '-writer-drain-proof-' + $drainAttempt + '.json')
    Invoke-PsqlJsonPrivate $DatabaseUrl $drainSql $drainProof ($PhasePrefix + '_WRITER_DRAIN_OBSERVATION_FAILED_HOLD_FENCED')
    $drained = Read-WriterDrainReceipt $drainProof ([string]$captureReceipt.writer_set_digest) ([int]$captureReceipt.writer_count)
    if ($drained.Remaining -eq 0) { break }
    if ($drainStopwatch.Elapsed.TotalSeconds -ge 120) { throw 'CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED' }
    [Threading.Thread]::Sleep(50)
    $drainAttempt += 1
  } while ($true)
  $drainStopwatch.Stop()
  if (-not $NoPhaseJournal) {
    $State.primary_writers_drained_at = $drained.ObservedAt.ToString('o')
    Set-StatePhase $State ($PhasePrefix + '_WRITERS_DRAINED') $ResolvedStatePath
  }

  if (-not $NoPhaseJournal) { Set-StatePhase $State ($PhasePrefix + '_LOCK_BARRIER_ACQUIRING') $ResolvedStatePath }
  $barrierProof = Join-Path $PrivateRoot (($PhasePrefix.ToLowerInvariant()) + '-lock-barrier-proof.json')
  Invoke-PsqlJsonPrivate $DatabaseUrl $lockBarrierSql $barrierProof ($PhasePrefix + '_LOCK_BARRIER_FAILED_HOLD_FENCED')
  $barrier = Assert-WriterStepReceipt $barrierProof 'PASS_WRITER_LOCK_BARRIER' ([string]$captureReceipt.writer_set_digest) ([int]$captureReceipt.writer_count) 'barrier_at'
  if ($barrier.ObservedAt -lt $drained.ObservedAt) { throw 'LOCK_BARRIER_BEFORE_WRITER_DRAIN' }
  if (-not $NoPhaseJournal) {
    $State.primary_lock_barrier_at = $barrier.ObservedAt.ToString('o')
    $State.primary_mutation_gate_fenced_at = $barrier.ObservedAt.ToString('o')
    $State.primary_mutation_gate_digest = [string]$barrier.Receipt.mutation_gate_digest
    $State.primary_mutation_gate_install_disposition = [string]$barrier.Receipt.install_disposition
    Set-StatePhase $State ($PhasePrefix + '_WRITERS_FENCED') $ResolvedStatePath
  }
  return [pscustomobject]@{ CaptureReads = 1; DrainReads = ($drainAttempt + 1); LockBarriers = 1; WriterCount = [int]$captureReceipt.writer_count; MutationGateDigest = [string]$barrier.Receipt.mutation_gate_digest; InstallDisposition = [string]$barrier.Receipt.install_disposition }
}

function Invoke-ExactAclRecovery(
  [string]$DatabaseUrl,
  [string]$ResolvedInput,
  [string]$ObservationSql,
  [string]$JournaledObservationPath,
  [string]$RestoreSql,
  [string]$PrivateRoot,
  [string]$Prefix,
  [string]$WriterCaptureSql = $null,
  [ValidateSet('LEGACY','MASTER')][string]$PhasePrefix = $null,
  [object]$State = $null,
  [string]$ResolvedStatePath = $null,
  [switch]$DrainBeforeRestore
) {
  if (-not (Test-Path -LiteralPath $JournaledObservationPath -PathType Leaf) -or -not (Test-Path -LiteralPath $RestoreSql -PathType Leaf)) { throw 'JOURNALED_ACL_RECOVERY_MATERIAL_MISSING' }
  $current = Join-Path $PrivateRoot ($Prefix + '-acl-current.json')
  Invoke-PsqlJsonPrivate $DatabaseUrl $ObservationSql $current 'ACL_RECOVERY_READ_FAILED'
  $receipt = Invoke-AclRecoveryClassifier $ResolvedInput $JournaledObservationPath $current 'primary'
  if ([string]$receipt.result -ceq 'PASS_ACL_PREIMAGE_ALREADY_PRESENT') {
    Invoke-PsqlPrivate $DatabaseUrl $RestoreSql
    $postRestore = Join-Path $PrivateRoot ($Prefix + '-acl-post-restore.json')
    Invoke-PsqlJsonPrivate $DatabaseUrl $ObservationSql $postRestore 'ACL_POST_RESTORE_READ_FAILED'
    $null = Invoke-AclVerifier $ResolvedInput $postRestore 'primary' $null $null $JournaledObservationPath
    return [pscustomobject]@{ DatabaseTransactions = 1; RestoreVerifications = 1; Restored = $true; CaptureReads = 0; DrainReads = 0; LockBarriers = 0 }
  }
  $writerFence = [pscustomobject]@{ CaptureReads = 0; DrainReads = 0; LockBarriers = 0 }
  if ($DrainBeforeRestore) {
    if ([string]::IsNullOrWhiteSpace($WriterCaptureSql) -or [string]::IsNullOrWhiteSpace($PhasePrefix) -or $null -eq $State -or [string]::IsNullOrWhiteSpace($ResolvedStatePath)) { throw 'SAFE_ACL_RECOVERY_DRAIN_MATERIAL_MISSING' }
    $writerFence = Invoke-ExactWriterDrainBarrier $DatabaseUrl $ResolvedInput $WriterCaptureSql $PrivateRoot $PhasePrefix $State $ResolvedStatePath
  }
  Invoke-PsqlPrivate $DatabaseUrl $RestoreSql
  $postRestore = Join-Path $PrivateRoot ($Prefix + '-acl-post-restore.json')
  Invoke-PsqlJsonPrivate $DatabaseUrl $ObservationSql $postRestore 'ACL_POST_RESTORE_READ_FAILED'
  $null = Invoke-AclVerifier $ResolvedInput $postRestore 'primary' $null $null $JournaledObservationPath
  return [pscustomobject]@{ DatabaseTransactions = (1 + [int]$writerFence.LockBarriers); RestoreVerifications = 1; Restored = $true; CaptureReads = [int]$writerFence.CaptureReads; DrainReads = [int]$writerFence.DrainReads; LockBarriers = [int]$writerFence.LockBarriers }
}

function Invoke-PsqlObservation([string]$DatabaseUrl, [string]$SqlPath, [string]$ExpectedDigest) {
  $psql = (Get-Command psql -ErrorAction Stop).Source
  $environment = @{
    PGDATABASE = $DatabaseUrl
    PGCONNECT_TIMEOUT = '15'
    PGAPPNAME = 'atlas-mazer-master-cutover-high-water-r001'
  }
  $child = Invoke-ProcessSanitized -FileName $psql -Arguments @('-X','--no-psqlrc','--quiet','--no-align','--tuples-only','--set','ON_ERROR_STOP=1','--file',$SqlPath) -Environment $environment -TimeoutMs 180000
  if ($child.ExitCode -ne 0) { throw 'SOURCE_HIGH_WATER_READ_FAILED' }
  if ([string]::IsNullOrWhiteSpace($child.Stdout) -or $child.Stdout.Length -gt 4096) { throw 'SOURCE_HIGH_WATER_OUTPUT_SHAPE' }
  $lines = @($child.Stdout -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  if ($lines.Count -ne 1) { throw 'SOURCE_HIGH_WATER_OUTPUT_CARDINALITY' }
  try { $observation = $lines[0] | ConvertFrom-Json } catch { throw 'SOURCE_HIGH_WATER_OUTPUT_JSON' }
  if ([string]$observation.result -cne 'PASS_SOURCE_HIGH_WATER' -or [string]$observation.source_high_water_digest -cne $ExpectedDigest) { throw 'SOURCE_HIGH_WATER_DRIFT' }
  try { $observedAt = [DateTimeOffset]::ParseExact([string]$observation.observed_at, 'yyyy-MM-ddTHH:mm:ss.FFFFFFzzz', [Globalization.CultureInfo]::InvariantCulture) }
  catch {
    try { $observedAt = [DateTimeOffset]::Parse([string]$observation.observed_at, [Globalization.CultureInfo]::InvariantCulture) }
    catch { throw 'SOURCE_HIGH_WATER_TIMESTAMP' }
  }
  return [pscustomobject]@{ ObservedAt = $observedAt; Digest = $ExpectedDigest }
}

if (-not ('AtlasMazerMasterFenceCredentialR001' -as [type]) -and $RunningOnWindows) {
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct AtlasMazerMasterFenceCredentialR001 {
  public UInt32 Flags; public UInt32 Type; public string TargetName; public string Comment;
  public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
  public UInt32 CredentialBlobSize; public IntPtr CredentialBlob; public UInt32 Persist;
  public UInt32 AttributeCount; public IntPtr Attributes; public string TargetAlias; public string UserName;
}
public static class AtlasMazerMasterFenceNativeR001 {
  [DllImport("advapi32.dll", EntryPoint="CredReadW", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredRead(string target, UInt32 type, UInt32 flags, out IntPtr credential);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern void CredFree(IntPtr credential);
}
'@
}

function Read-ManagementToken {
  if (-not $RunningOnWindows) {
    $token = [Environment]::GetEnvironmentVariable('SUPABASE_ACCESS_TOKEN', [EnvironmentVariableTarget]::Process)
    if ([string]::IsNullOrWhiteSpace($token)) { throw 'MANAGEMENT_CREDENTIAL_MISSING' }
    return $token
  }
  $pointer = [IntPtr]::Zero
  try {
    if (-not [AtlasMazerMasterFenceNativeR001]::CredRead($CredentialTarget, 1, 0, [ref]$pointer) -or $pointer -eq [IntPtr]::Zero) { throw 'MANAGEMENT_CREDENTIAL_MISSING' }
    $credential = [Runtime.InteropServices.Marshal]::PtrToStructure($pointer, [type][AtlasMazerMasterFenceCredentialR001])
    if ($credential.CredentialBlobSize -lt 16 -or $credential.CredentialBlobSize -gt 8192 -or $credential.CredentialBlob -eq [IntPtr]::Zero) { throw 'MANAGEMENT_CREDENTIAL_SHAPE' }
    $bytes = New-Object byte[] $credential.CredentialBlobSize
    [Runtime.InteropServices.Marshal]::Copy($credential.CredentialBlob, $bytes, 0, $bytes.Length)
    try {
      $unicode = ($bytes.Length % 2 -eq 0)
      if ($unicode) { for ($i = 1; $i -lt $bytes.Length; $i += 2) { if ($bytes[$i] -ne 0) { $unicode = $false; break } } }
      $token = if ($unicode) { [Text.Encoding]::Unicode.GetString($bytes).TrimEnd([char]0) } else { (New-Object Text.UTF8Encoding($false, $true)).GetString($bytes).TrimEnd([char]0) }
      if ($token.Length -lt 16 -or $token.Length -gt 4096 -or $token -match '[\x00-\x20\x7f]') { throw 'MANAGEMENT_CREDENTIAL_FORMAT' }
      return $token
    }
    finally { [Array]::Clear($bytes, 0, $bytes.Length) }
  }
  finally { if ($pointer -ne [IntPtr]::Zero) { [AtlasMazerMasterFenceNativeR001]::CredFree($pointer) } }
}

function Invoke-AuthConfig([string]$Token, [string]$ProjectRef, [System.Collections.IDictionary]$Patch = $null) {
  $request = [Net.HttpWebRequest]::Create("$ApiBase/v1/projects/$ProjectRef/config/auth")
  $request.Method = if ($null -eq $Patch) { 'GET' } else { 'PATCH' }
  $request.Timeout = 30000
  $request.ReadWriteTimeout = 30000
  $request.Accept = 'application/json'
  $request.Headers['Authorization'] = 'Bearer ' + $Token
  if ($null -ne $Patch) {
    $body = [Text.Encoding]::UTF8.GetBytes(($Patch | ConvertTo-Json -Compress))
    $request.ContentType = 'application/json'
    $request.ContentLength = $body.Length
    $stream = $request.GetRequestStream()
    try { $stream.Write($body, 0, $body.Length) } finally { $stream.Dispose(); [Array]::Clear($body, 0, $body.Length) }
  }
  try { $response = [Net.HttpWebResponse]$request.GetResponse() }
  catch { if ($_.Exception.Response) { $_.Exception.Response.Close() }; throw 'AUTH_CONFIG_REQUEST_FAILED' }
  try {
    if ([int]$response.StatusCode -ne 200) { throw 'AUTH_CONFIG_STATUS' }
    $reader = New-Object IO.StreamReader($response.GetResponseStream(), (New-Object Text.UTF8Encoding($false, $true)), $true, 4096, $false)
    try { $text = $reader.ReadToEnd() } finally { $reader.Dispose() }
  }
  finally { $response.Dispose() }
  if ([string]::IsNullOrWhiteSpace($text) -or $text.Length -gt 1048576) { throw 'AUTH_CONFIG_RESPONSE_SIZE' }
  try { return $text | ConvertFrom-Json } catch { throw 'AUTH_CONFIG_RESPONSE_JSON' }
}

function Write-State([string]$ResolvedStatePath, [object]$State) {
  $parent = Split-Path -Parent $ResolvedStatePath
  [IO.Directory]::CreateDirectory($parent) | Out-Null
  $temporary = "$ResolvedStatePath.tmp-$PID"
  $json = $State | ConvertTo-Json -Depth 8
  [IO.File]::WriteAllText($temporary, $json, (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $temporary -Destination $ResolvedStatePath -Force
}

function Read-State([string]$ResolvedStatePath) {
  if (-not (Test-Path -LiteralPath $ResolvedStatePath -PathType Leaf)) { return $null }
  try { return (Get-Content -LiteralPath $ResolvedStatePath -Raw | ConvertFrom-Json) } catch { throw 'STATE_JSON' }
}

function Set-StatePhase([object]$State, [string]$Phase, [string]$ResolvedStatePath) {
  if ([string]$State.phase -cne $Phase) {
    if ($State -is [System.Collections.IDictionary]) { $State['previous_phase'] = [string]$State.phase }
    elseif ($null -eq $State.PSObject.Properties['previous_phase']) { $State | Add-Member -NotePropertyName previous_phase -NotePropertyValue ([string]$State.phase) }
    else { $State.previous_phase = [string]$State.phase }
  }
  $State.phase = $Phase
  $State.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  Write-State $ResolvedStatePath $State
}

function Assert-StateBinding([object]$State, [object]$Receipt, [string]$InputDigest, [string]$InputFileDigest) {
  if ($null -eq $State -or [string]$State.schema -cne 'atlas.supabase.mazer-master-cutover-data-fence-host-state.v1') { throw 'STATE_SCHEMA_DRIFT' }
  if ([string]$State.packet_input_digest -cne $InputDigest) { throw 'STATE_INPUT_DIGEST_DRIFT' }
  if ([string]$State.input_file_sha256 -cne $InputFileDigest) { throw 'STATE_INPUT_FILE_DIGEST_DRIFT' }
  if ([string]$State.direction -cne [string]$Receipt.direction) { throw 'STATE_DIRECTION_DRIFT' }
  if ([string]$State.identity_map_digest -cne [string]$Receipt.identity_map_digest) { throw 'STATE_IDENTITY_MAP_DIGEST_DRIFT' }
  if ([string]$State.app_contract_digest -cne [string]$Receipt.app_contract_digest) { throw 'STATE_APP_CONTRACT_DIGEST_DRIFT' }
  if ([string]$State.source_high_water_digest -cne [string]$Receipt.source_high_water_digest) { throw 'STATE_HIGH_WATER_DIGEST_DRIFT' }
  if ([string]$State.primary_acl_preimage_digest -cne [string]$Receipt.primary_acl_preimage_digest) { throw 'STATE_PRIMARY_ACL_DIGEST_DRIFT' }
  if ([string]$State.primary_catalog_digest -cne [string]$Receipt.primary_catalog_digest) { throw 'STATE_PRIMARY_CATALOG_DIGEST_DRIFT' }
  if ([string]$State.legacy_acl_preimage_digest -cne [string]$Receipt.legacy_acl_preimage_digest) { throw 'STATE_LEGACY_ACL_DIGEST_DRIFT' }
  if ([string]$State.legacy_catalog_digest -cne [string]$Receipt.legacy_catalog_digest) { throw 'STATE_LEGACY_CATALOG_DIGEST_DRIFT' }
  if ([string]$State.executor_bypass_profile -cne [string]$Receipt.executor_bypass_profile) { throw 'STATE_EXECUTOR_BYPASS_PROFILE_DRIFT' }
}

function Assert-SourceContract {
  if (-not (Test-Path -LiteralPath $Classifier -PathType Leaf)) { throw 'CLASSIFIER_MISSING' }
  $tokens = $null
  $errors = $null
  [void][Management.Automation.Language.Parser]::ParseFile($PSCommandPath, [ref]$tokens, [ref]$errors)
  if ($errors.Count -ne 0) { throw 'POWERSHELL_PARSE_FAILED' }
  $node = Invoke-ProcessSanitized -FileName (Get-Command node -ErrorAction Stop).Source -Arguments @('--check',$Classifier) -TimeoutMs 30000
  if ($node.ExitCode -ne 0) { throw 'CLASSIFIER_PARSE_FAILED' }
  $source = [IO.File]::ReadAllText($Classifier)
  foreach ($needle in @(
    $LegacyProjectRef,$MasterProjectRef,$LegacySchema,$MasterSchema,
    'IDENTITY_MAP_DIGEST_DRIFT','APP_CONTRACT_DIGEST_DRIFT','POST_FENCE_LATE_WRITE',
    'RECEIPT_ID_CONFLICT','RECEIPT_CLIENT_RUN_CONFLICT','DISABLE_HOOK_FIRST_REQUIRED',
    'pg_advisory_xact_lock','TARGET_PREIMAGE_DRIFT','PASS_EXACT_REPLAY_NOOP',
    '_PAYLOAD_DIGEST_MISMATCH','ACL_PREIMAGE_DIGEST_DRIFT','FENCE_CATALOG_DIGEST_DRIFT',
    'PASS_ACL_PREIMAGE_MATCH','share row exclusive mode','MAX_PG_BIGINT',
    'FENCE_ACL_OR_CATALOG_PREIMAGE_DRIFT','LEGACY_DEDICATED_AUTH_SET_EXACT',
    'MASTER_MAZER_NAMESPACE_OR_PROFILE_OWNERSHIP','atlas_observed_auth',
    'PASS_ACL_PREIMAGE_ALREADY_PRESENT','PASS_ACL_FENCED_POSTIMAGE_RESTORE_REQUIRED',
    'HOLD_ACL_RECOVERY_STATE_AMBIGUOUS','PASS_WRITER_REVOKE_COMMITTED',
    'PASS_WRITER_SET_CAPTURE','CAPTURED_WRITER_DRAIN_TIMEOUT_HOLD_FENCED',
    'PASS_WRITER_LOCK_BARRIER','pid, a.backend_start, a.xact_start, a.query_start',
    'MAZER_SIGNUP_TEMPORARILY_UNAVAILABLE','PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT',
    'PASS_SIGNUP_ADMISSION_FENCED','AUTH_USERS_WRITER_BARRIER_INCOMPLETE',
    'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED','app_namespace',
    'PASS_MUTATION_GATE_FENCED','MAZER_CUTOVER_WRITES_FENCED',
    'TARGET_RELATION_LOCKS_PLUS_MUTATION_POINT_GATE','pg_catalog.pg_locks',
    'atlas.mazer_cutover_writer_bypass','MUTATION_GATE_RESTORE_POSTIMAGE_DRIFT',
    'RECONCILED_EXACT_FENCED','INSTALLED_FROM_ABSENT'
  )) { if (-not $source.Contains($needle)) { throw 'CLASSIFIER_CONTRACT_DRIFT' } }
  foreach ($table in $ExpectedTables) { if (-not $source.Contains($table)) { throw 'CLASSIFIER_TABLE_DRIFT' } }
  foreach ($rpc in $ExpectedMutatingRpcs) { if (-not $source.Contains($rpc)) { throw 'CLASSIFIER_RPC_DRIFT' } }
}

if ($PSCmdlet.ParameterSetName -eq 'Source') {
  Assert-SourceContract
  Assert-PlatformPathContract
  Write-SafeResult 'PASS_MAZER_MASTER_CUTOVER_DATA_FENCE_SOURCE' ([ordered]@{
    classifier_sha256 = Get-Sha256 $Classifier
    credential_reads = 0
    provider_reads = 0
    provider_writes = 0
    auth_writes = 0
    live_data_writes = 0
    state_writes = 0
    private_files = 0
  })
  exit 0
}

if (-not $ExecuteProtected) { throw 'PROTECTED_EXECUTION_SWITCH_REQUIRED' }
$resolvedInput = Assert-PathUnder $InputPath @($RuntimeRoot,$SecretRoot)
$resolvedState = Assert-PathUnder $StatePath @($RuntimeRoot)
if (-not (Test-Path -LiteralPath $resolvedInput -PathType Leaf)) { throw 'INPUT_MISSING' }
Assert-NoReparseComponents $resolvedInput $(if (Test-CanonicalPathUnder $resolvedInput $RuntimeRoot) { $RuntimeRoot } else { $SecretRoot })
Assert-NoReparseComponents (Split-Path -Parent $resolvedState) $RuntimeRoot
$inputFileDigest = Get-Sha256 $resolvedInput
if ($inputFileDigest -cne $ExpectedInputSha256) { throw 'INPUT_FILE_DIGEST_DRIFT' }

$privateRoot = $null
$managementToken = $null
$legacyDatabaseUrl = $null
$masterDatabaseUrl = $null
$classification = $null
$state = $null
$providerReads = 0
$providerWrites = 0
$databaseTransactions = 0
$sourceObservationReads = 0
$aclPreimageReads = 0
$aclRestoreVerifications = 0
$writerCaptureReads = 0
$writerDrainReads = 0
$writerLockBarriers = 0
$signupAdmissionReads = 0
$signupAdmissionBarriers = 0
$signupAdmissionRestores = 0
$rollbackActions = 0
$primaryAclPreobserve = $null
try {
  Assert-SourceContract
  Assert-NoReparseComponents $SecretPacketRoot $SecretRoot
  $privateRoot = Join-Path $SecretPacketRoot ([Guid]::NewGuid().ToString('N'))
  [IO.Directory]::CreateDirectory($privateRoot) | Out-Null
  Assert-NoReparseComponents $privateRoot $SecretRoot
  $privateInput = Join-Path $privateRoot 'bound-input.json'
  [IO.File]::Copy($resolvedInput, $privateInput, $false)
  if ((Get-Sha256 $privateInput) -cne $ExpectedInputSha256) { throw 'INPUT_FILE_COPY_DIGEST_DRIFT' }
  $classification = Invoke-Classifier -PrivateRoot $privateRoot -ResolvedInput $privateInput
  $inputDigest = [string]$classification.Receipt.packet_input_digest
  $existing = Read-State $resolvedState
  $direction = [string]$classification.Receipt.direction
  if ($Mode -eq 'Rollback') {
    if ($null -eq $existing) { throw 'ROLLBACK_STATE_MISSING' }
    Assert-StateBinding $existing $classification.Receipt $inputDigest $inputFileDigest
    $state = $existing
    if ([string]$state.phase -ceq 'ROLLED_BACK') {
      Write-SafeResult 'PASS_EXACT_REPLAY_NOOP' ([ordered]@{
        direction = $direction
        packet_input_digest = $inputDigest
        provider_reads = 0
        provider_writes = 0
        database_transactions = 0
        rollback_actions = 0
      })
      exit 0
    }
    if ([string]$state.phase -ceq 'COMPLETE') { throw 'COMPLETED_STATE_REQUIRES_REVERSE_PACKET' }
    if ([string]$state.phase -ceq 'PREFLIGHT') {
      Set-StatePhase $state 'ROLLED_BACK' $resolvedState
      Write-SafeResult 'NO_EFFECT_PREFLIGHT_ROLLED_BACK' ([ordered]@{
        direction = $direction
        packet_input_digest = $inputDigest
        provider_reads = 0
        provider_writes = 0
        database_transactions = 0
        rollback_actions = 0
      })
      exit 0
    }
  }
  else {
    if ($Mode.ToLowerInvariant() -cne $direction) { throw 'MODE_DIRECTION_DRIFT' }
    if ($null -ne $existing) {
      Assert-StateBinding $existing $classification.Receipt $inputDigest $inputFileDigest
      if ([string]$existing.phase -ceq 'COMPLETE') {
        Write-SafeResult 'PASS_EXACT_REPLAY_NOOP' ([ordered]@{
          direction = $direction
          packet_input_digest = $inputDigest
          provider_reads = 0
          provider_writes = 0
          database_transactions = 0
          rollback_actions = 0
        })
        exit 0
      }
      throw 'INTERRUPTED_STATE_REQUIRES_EXPLICIT_ROLLBACK'
    }
    $state = [ordered]@{
      schema = 'atlas.supabase.mazer-master-cutover-data-fence-host-state.v1'
      direction = $direction
      phase = 'PREFLIGHT'
      packet_input_digest = $inputDigest
      input_file_sha256 = $inputFileDigest
      identity_map_digest = [string]$classification.Receipt.identity_map_digest
      app_contract_digest = [string]$classification.Receipt.app_contract_digest
      source_high_water_digest = [string]$classification.Receipt.source_high_water_digest
      primary_acl_preimage_digest = [string]$classification.Receipt.primary_acl_preimage_digest
      primary_catalog_digest = [string]$classification.Receipt.primary_catalog_digest
      legacy_acl_preimage_digest = [string]$classification.Receipt.legacy_acl_preimage_digest
      legacy_catalog_digest = [string]$classification.Receipt.legacy_catalog_digest
      executor_bypass_profile = [string]$classification.Receipt.executor_bypass_profile
      primary_acl_preobserved_at = $null
      journaled_primary_acl_preimage = $null
      journaled_primary_acl_digest = $null
      journaled_primary_catalog_digest = $null
      journaled_primary_acl_binding_digest = $null
      primary_writer_revoke_committed_at = $null
      journaled_primary_writer_capture = $null
      journaled_primary_writer_count = $null
      journaled_primary_writer_set_digest = $null
      journaled_primary_writer_capture_binding_digest = $null
      primary_writer_set_captured_at = $null
      primary_writers_drained_at = $null
      primary_lock_barrier_at = $null
      primary_mutation_gate_fenced_at = $null
      primary_mutation_gate_digest = $null
      primary_mutation_gate_install_disposition = $null
      legacy_disable_signup_preimage = $null
      master_hook_enabled_preimage = $null
      master_signup_admission_preobserved_at = $null
      master_signup_admission_fenced_at = $null
      master_signup_admission_writer_count = $null
      master_signup_admission_writer_set_digest = $null
      master_signup_admission_install_disposition = $null
      source_observation_1_at = $null
      source_observation_2_at = $null
      updated_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    Write-State $resolvedState $state
  }

  $legacyDatabaseUrl = Assert-DatabaseUrl ([Environment]::GetEnvironmentVariable('ATLAS_MAZER_LEGACY_DATABASE_URL', 'Process')) $LegacyProjectRef
  $masterDatabaseUrl = Assert-DatabaseUrl ([Environment]::GetEnvironmentVariable('ATLAS_MAZER_MASTER_DATABASE_URL', 'Process')) $MasterProjectRef
  $managementToken = Read-ManagementToken

  if ($Mode -eq 'Rollback') {
    $effectivePhase = if ([string]$state.phase -in @('AMBIGUOUS_HOLD','QUARANTINED_HOLD')) { [string]$state.previous_phase } else { [string]$state.phase }
    if ([string]::IsNullOrWhiteSpace($effectivePhase)) { throw 'ROLLBACK_PHASE_AMBIGUOUS' }
    $rollbackRestoreSql = $null
    $rollbackExpectedAcl = $null
    if ($null -ne $state.journaled_primary_acl_preimage) {
      $rollbackExpectedAcl = Join-Path $privateRoot 'recovered-primary-acl.json'
      [IO.File]::WriteAllText($rollbackExpectedAcl, (($state.journaled_primary_acl_preimage | ConvertTo-Json -Depth 12 -Compress) + "`n"), (New-Object Text.UTF8Encoding($false)))
      $recoveredRestore = Join-Path $privateRoot 'recovered-observed-restore.sql'
      $recoveredReceipt = Invoke-AclVerifier $privateInput $rollbackExpectedAcl 'primary' $recoveredRestore $null $rollbackExpectedAcl
      if ([string]$recoveredReceipt.actual_acl_preimage_digest -cne [string]$state.journaled_primary_acl_digest -or [string]$recoveredReceipt.actual_catalog_digest -cne [string]$state.journaled_primary_catalog_digest -or [string]$recoveredReceipt.acl_observation_binding_digest -cne [string]$state.journaled_primary_acl_binding_digest) { throw 'RECOVERED_ACL_JOURNAL_DIGEST_DRIFT' }
      $rollbackRestoreSql = $recoveredRestore
    }
    if ($direction -ceq 'forward') {
      $forwardFencePhases = @('LEGACY_WRITERS_FENCING','LEGACY_WRITER_REVOKE_COMMITTED','LEGACY_WRITER_SET_CAPTURING','LEGACY_WRITER_SET_CAPTURED','LEGACY_WRITERS_DRAINING','LEGACY_WRITERS_DRAINED','LEGACY_LOCK_BARRIER_ACQUIRING','LEGACY_WRITERS_FENCED','SOURCE_HIGH_WATER_READ_1','SOURCE_HIGH_WATER_READ_2','FORWARD_DELTA_APPLYING','FORWARD_DELTA_APPLIED')
      $forwardDrainRequired = @('LEGACY_WRITERS_FENCING','LEGACY_WRITER_REVOKE_COMMITTED','LEGACY_WRITER_SET_CAPTURING','LEGACY_WRITER_SET_CAPTURED','LEGACY_WRITERS_DRAINING','LEGACY_WRITERS_DRAINED','LEGACY_LOCK_BARRIER_ACQUIRING')
      if ($effectivePhase -notin (@('LEGACY_SIGNUP_FENCING','LEGACY_SIGNUP_FENCED','LEGACY_WRITERS_PREOBSERVING','LEGACY_WRITERS_PREOBSERVED') + $forwardFencePhases)) { throw 'ROLLBACK_PHASE_DRIFT' }
      if ($null -eq $state.legacy_disable_signup_preimage) { throw 'ROLLBACK_PREIMAGE_MISSING' }
      if ($effectivePhase -in $forwardFencePhases) {
        if ([string]::IsNullOrWhiteSpace($rollbackRestoreSql) -or $null -eq $rollbackExpectedAcl) { throw 'ROLLBACK_ACL_PREIMAGE_MISSING' }
        $recovery = Invoke-ExactAclRecovery $legacyDatabaseUrl $privateInput $classification.AclObservationSql $rollbackExpectedAcl $rollbackRestoreSql $privateRoot 'rollback-primary' -WriterCaptureSql $classification.WriterCaptureSql -PhasePrefix 'LEGACY' -State $state -ResolvedStatePath $resolvedState -DrainBeforeRestore:($effectivePhase -in $forwardDrainRequired)
        $databaseTransactions += [int]$recovery.DatabaseTransactions
        $aclRestoreVerifications += [int]$recovery.RestoreVerifications
        $writerCaptureReads += [int]$recovery.CaptureReads
        $writerDrainReads += [int]$recovery.DrainReads
        $writerLockBarriers += [int]$recovery.LockBarriers
      }
      $restored = Invoke-AuthConfig $managementToken $LegacyProjectRef @{ disable_signup = [bool]$state.legacy_disable_signup_preimage }
      $providerWrites += 1
      if ([bool]$restored.disable_signup -ne [bool]$state.legacy_disable_signup_preimage) { throw 'LEGACY_SIGNUP_RESTORE_FAILED' }
    }
    else {
      $reverseFencePhases = @('MASTER_WRITERS_FENCING','MASTER_WRITER_REVOKE_COMMITTED','MASTER_WRITER_SET_CAPTURING','MASTER_WRITER_SET_CAPTURED','MASTER_WRITERS_DRAINING','MASTER_WRITERS_DRAINED','MASTER_LOCK_BARRIER_ACQUIRING','MASTER_WRITERS_FENCED','SOURCE_HIGH_WATER_READ_1','SOURCE_HIGH_WATER_READ_2','REVERSE_DELTA_APPLYING','REVERSE_DELTA_APPLIED')
      $reverseDrainRequired = @('MASTER_WRITERS_FENCING','MASTER_WRITER_REVOKE_COMMITTED','MASTER_WRITER_SET_CAPTURING','MASTER_WRITER_SET_CAPTURED','MASTER_WRITERS_DRAINING','MASTER_WRITERS_DRAINED','MASTER_LOCK_BARRIER_ACQUIRING')
      $reverseSignupPhases = @('MASTER_SIGNUP_FENCING','MASTER_SIGNUP_FENCED','MASTER_HOOK_RESTORING','MASTER_HOOK_RESTORED','MASTER_SIGNUP_RESTORING')
      if ($effectivePhase -notin (@('MASTER_HOOK_DISABLING','MASTER_HOOK_DISABLED','MASTER_SIGNUP_PREOBSERVING','MASTER_SIGNUP_PREOBSERVED','MASTER_WRITERS_PREOBSERVING','MASTER_WRITERS_PREOBSERVED') + $reverseSignupPhases + $reverseFencePhases)) { throw 'ROLLBACK_PHASE_DRIFT' }
      if ($null -eq $state.master_hook_enabled_preimage) { throw 'ROLLBACK_PREIMAGE_MISSING' }
      if ($effectivePhase -in $reverseFencePhases) {
        if ([string]::IsNullOrWhiteSpace($rollbackRestoreSql) -or $null -eq $rollbackExpectedAcl) { throw 'ROLLBACK_ACL_PREIMAGE_MISSING' }
        $recovery = Invoke-ExactAclRecovery $masterDatabaseUrl $privateInput $classification.AclObservationSql $rollbackExpectedAcl $rollbackRestoreSql $privateRoot 'rollback-primary' -WriterCaptureSql $classification.WriterCaptureSql -PhasePrefix 'MASTER' -State $state -ResolvedStatePath $resolvedState -DrainBeforeRestore:($effectivePhase -in $reverseDrainRequired)
        $databaseTransactions += [int]$recovery.DatabaseTransactions
        $aclRestoreVerifications += [int]$recovery.RestoreVerifications
        $writerCaptureReads += [int]$recovery.CaptureReads
        $writerDrainReads += [int]$recovery.DrainReads
        $writerLockBarriers += [int]$recovery.LockBarriers
      }
      Set-StatePhase $state 'MASTER_HOOK_RESTORING' $resolvedState
      $restored = Invoke-AuthConfig $managementToken $MasterProjectRef @{ hook_before_user_created_enabled = [bool]$state.master_hook_enabled_preimage }
      $providerWrites += 1
      if ([bool]$restored.hook_before_user_created_enabled -ne [bool]$state.master_hook_enabled_preimage) { throw 'MASTER_HOOK_RESTORE_FAILED' }
      Set-StatePhase $state 'MASTER_HOOK_RESTORED' $resolvedState
      $signupFenceMayExist = $effectivePhase -in ($reverseSignupPhases + $reverseFencePhases) -or $null -ne $state.master_signup_admission_fenced_at
      if ($signupFenceMayExist) {
        Set-StatePhase $state 'MASTER_SIGNUP_RESTORING' $resolvedState
        $signupRestoreProof = Join-Path $privateRoot 'master-signup-admission-restored.json'
        Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionRestoreSql $signupRestoreProof 'MASTER_SIGNUP_ADMISSION_RESTORE_FAILED'
        $null = Assert-SignupAdmissionReceipt $signupRestoreProof 'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED'
        $databaseTransactions += 1
        $signupAdmissionRestores += 1
      }
    }
    $rollbackActions += 1
    Set-StatePhase $state 'ROLLED_BACK' $resolvedState
    Write-SafeResult 'EXACT_FENCE_PREIMAGE_RESTORED' ([ordered]@{
      direction = $direction
      packet_input_digest = $inputDigest
      effect_status = $(if ($effectivePhase -match 'DELTA_APPLYING|DELTA_APPLIED|ZERO_DELTA') { 'DELTA_QUARANTINED_PREIMAGE_RESTORED' } else { 'EXACT_PREIMAGE_RESTORED' })
      provider_reads = $providerReads
      provider_writes = $providerWrites
      database_transactions = $databaseTransactions
      rollback_actions = $rollbackActions
      acl_restore_verifications = $aclRestoreVerifications
      writer_capture_reads = $writerCaptureReads
      writer_drain_reads = $writerDrainReads
      writer_lock_barriers = $writerLockBarriers
      signup_admission_reads = $signupAdmissionReads
      signup_admission_barriers = $signupAdmissionBarriers
      signup_admission_restores = $signupAdmissionRestores
    })
    exit 0
  }

  if ($direction -ceq 'forward') {
    $preimage = Invoke-AuthConfig $managementToken $LegacyProjectRef
    $providerReads += 1
    $state.legacy_disable_signup_preimage = [bool]$preimage.disable_signup
    if ($state.legacy_disable_signup_preimage) { throw 'LEGACY_SIGNUP_ALREADY_DISABLED_PREIMAGE_DRIFT' }
    Set-StatePhase $state 'LEGACY_SIGNUP_FENCING' $resolvedState
    $fenced = Invoke-AuthConfig $managementToken $LegacyProjectRef @{ disable_signup = $true }
    $providerWrites += 1
    if ([bool]$fenced.disable_signup -ne $true) { throw 'LEGACY_SIGNUP_FENCE_FAILED' }
    Set-StatePhase $state 'LEGACY_SIGNUP_FENCED' $resolvedState
    Set-StatePhase $state 'LEGACY_WRITERS_PREOBSERVING' $resolvedState
    $primaryAclPreobserve = Join-Path $privateRoot 'primary-acl-preobserve.json'
    Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.AclObservationSql $primaryAclPreobserve 'LEGACY_ACL_PREOBSERVATION_FAILED'
    $aclPreimageReads += 1
    $primaryAclReceipt = Invoke-AclVerifier $privateInput $primaryAclPreobserve 'primary' $classification.ObservedRestoreSql $classification.ObservedFenceSql
    $state.primary_acl_preobserved_at = [string]$primaryAclReceipt.observed_at
    $state.journaled_primary_acl_preimage = Get-Content -LiteralPath $primaryAclPreobserve -Raw | ConvertFrom-Json
    $state.journaled_primary_acl_digest = [string]$primaryAclReceipt.actual_acl_preimage_digest
    $state.journaled_primary_catalog_digest = [string]$primaryAclReceipt.actual_catalog_digest
    $state.journaled_primary_acl_binding_digest = [string]$primaryAclReceipt.acl_observation_binding_digest
    Set-StatePhase $state 'LEGACY_WRITERS_PREOBSERVED' $resolvedState
    Set-StatePhase $state 'LEGACY_WRITERS_FENCING' $resolvedState
    $primaryFenceProof = Join-Path $privateRoot 'primary-writer-revoke-proof.json'
    Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.ObservedFenceSql $primaryFenceProof 'LEGACY_WRITER_REVOKE_FAILED'
    $databaseTransactions += 1
    $state.primary_writer_revoke_committed_at = (Assert-WriterRevokeReceipt $primaryFenceProof $LegacySchema ([string]$state.journaled_primary_acl_digest)).ToString('o')
    Set-StatePhase $state 'LEGACY_WRITER_REVOKE_COMMITTED' $resolvedState
    $writerFence = Invoke-ExactWriterDrainBarrier $legacyDatabaseUrl $privateInput $classification.WriterCaptureSql $privateRoot 'LEGACY' $state $resolvedState
    $writerCaptureReads += [int]$writerFence.CaptureReads
    $writerDrainReads += [int]$writerFence.DrainReads
    $writerLockBarriers += [int]$writerFence.LockBarriers
    $databaseTransactions += [int]$writerFence.LockBarriers
    $observation1 = Invoke-PsqlObservation $legacyDatabaseUrl $classification.SourceObservationSql ([string]$classification.Receipt.source_high_water_digest)
    $sourceObservationReads += 1
    $state.source_observation_1_at = $observation1.ObservedAt.ToString('o')
    Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_1' $resolvedState
    $observation2 = Invoke-PsqlObservation $legacyDatabaseUrl $classification.SourceObservationSql ([string]$classification.Receipt.source_high_water_digest)
    $sourceObservationReads += 1
    if ($observation2.ObservedAt -le $observation1.ObservedAt) { throw 'SOURCE_HIGH_WATER_OBSERVATION_ORDER' }
    $state.source_observation_2_at = $observation2.ObservedAt.ToString('o')
    Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_2' $resolvedState
    Set-StatePhase $state 'FORWARD_DELTA_APPLYING' $resolvedState
    Invoke-PsqlPrivate $masterDatabaseUrl $classification.TransactionSql
    $databaseTransactions += 1
    Set-StatePhase $state 'FORWARD_DELTA_APPLIED' $resolvedState
    if ($sourceObservationReads -ne 2 -or [int]$classification.Receipt.zero_delta_reads -ne 2) { throw 'TWO_ZERO_DELTA_READS_REQUIRED' }
    Set-StatePhase $state 'COMPLETE' $resolvedState
  }
  else {
    $preimage = Invoke-AuthConfig $managementToken $MasterProjectRef
    $providerReads += 1
    $state.master_hook_enabled_preimage = [bool]$preimage.hook_before_user_created_enabled
    if (-not $state.master_hook_enabled_preimage) { throw 'MASTER_HOOK_ALREADY_DISABLED_PREIMAGE_DRIFT' }
    Set-StatePhase $state 'MASTER_HOOK_DISABLING' $resolvedState
    $disabled = Invoke-AuthConfig $managementToken $MasterProjectRef @{ hook_before_user_created_enabled = $false }
    $providerWrites += 1
    if ([bool]$disabled.hook_before_user_created_enabled -ne $false) { throw 'MASTER_HOOK_DISABLE_FAILED' }
    Set-StatePhase $state 'MASTER_HOOK_DISABLED' $resolvedState
    Set-StatePhase $state 'MASTER_SIGNUP_PREOBSERVING' $resolvedState
    $signupPreobserve = Join-Path $privateRoot 'master-signup-admission-preobserve.json'
    Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionObservationSql $signupPreobserve 'MASTER_SIGNUP_ADMISSION_PREOBSERVATION_FAILED'
    $signupPreimageReceipt = Assert-SignupAdmissionReceipt $signupPreobserve 'PASS_SIGNUP_ADMISSION_PREIMAGE_ABSENT'
    $signupAdmissionReads += 1
    $state.master_signup_admission_preobserved_at = $signupPreimageReceipt.ObservedAt.ToString('o')
    Set-StatePhase $state 'MASTER_SIGNUP_PREOBSERVED' $resolvedState
    Set-StatePhase $state 'MASTER_SIGNUP_FENCING' $resolvedState
    $signupFenceProof = Join-Path $privateRoot 'master-signup-admission-fenced.json'
    Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionFenceSql $signupFenceProof 'MASTER_SIGNUP_ADMISSION_FENCE_FAILED_HOLD_HOOK_DISABLED'
    $signupFenceReceipt = Assert-SignupAdmissionReceipt $signupFenceProof 'PASS_SIGNUP_ADMISSION_FENCED'
    $databaseTransactions += 1
    $signupAdmissionBarriers += 1
    $state.master_signup_admission_fenced_at = $signupFenceReceipt.ObservedAt.ToString('o')
    $state.master_signup_admission_writer_count = [int]$signupFenceReceipt.Receipt.writer_count
    $state.master_signup_admission_writer_set_digest = [string]$signupFenceReceipt.Receipt.writer_set_digest
    $state.master_signup_admission_install_disposition = [string]$signupFenceReceipt.Receipt.install_disposition
    Set-StatePhase $state 'MASTER_SIGNUP_FENCED' $resolvedState
    Set-StatePhase $state 'MASTER_WRITERS_PREOBSERVING' $resolvedState
    $primaryAclPreobserve = Join-Path $privateRoot 'primary-acl-preobserve.json'
    Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.AclObservationSql $primaryAclPreobserve 'MASTER_ACL_PREOBSERVATION_FAILED'
    $aclPreimageReads += 1
    $primaryAclReceipt = Invoke-AclVerifier $privateInput $primaryAclPreobserve 'primary' $classification.ObservedRestoreSql $classification.ObservedFenceSql
    $state.primary_acl_preobserved_at = [string]$primaryAclReceipt.observed_at
    $state.journaled_primary_acl_preimage = Get-Content -LiteralPath $primaryAclPreobserve -Raw | ConvertFrom-Json
    $state.journaled_primary_acl_digest = [string]$primaryAclReceipt.actual_acl_preimage_digest
    $state.journaled_primary_catalog_digest = [string]$primaryAclReceipt.actual_catalog_digest
    $state.journaled_primary_acl_binding_digest = [string]$primaryAclReceipt.acl_observation_binding_digest
    Set-StatePhase $state 'MASTER_WRITERS_PREOBSERVED' $resolvedState
    Set-StatePhase $state 'MASTER_WRITERS_FENCING' $resolvedState
    $primaryFenceProof = Join-Path $privateRoot 'primary-writer-revoke-proof.json'
    Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.ObservedFenceSql $primaryFenceProof 'MASTER_WRITER_REVOKE_FAILED'
    $databaseTransactions += 1
    $state.primary_writer_revoke_committed_at = (Assert-WriterRevokeReceipt $primaryFenceProof $MasterSchema ([string]$state.journaled_primary_acl_digest)).ToString('o')
    Set-StatePhase $state 'MASTER_WRITER_REVOKE_COMMITTED' $resolvedState
    $writerFence = Invoke-ExactWriterDrainBarrier $masterDatabaseUrl $privateInput $classification.WriterCaptureSql $privateRoot 'MASTER' $state $resolvedState
    $writerCaptureReads += [int]$writerFence.CaptureReads
    $writerDrainReads += [int]$writerFence.DrainReads
    $writerLockBarriers += [int]$writerFence.LockBarriers
    $databaseTransactions += [int]$writerFence.LockBarriers
    $observation1 = Invoke-PsqlObservation $masterDatabaseUrl $classification.SourceObservationSql ([string]$classification.Receipt.source_high_water_digest)
    $sourceObservationReads += 1
    $state.source_observation_1_at = $observation1.ObservedAt.ToString('o')
    Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_1' $resolvedState
    $observation2 = Invoke-PsqlObservation $masterDatabaseUrl $classification.SourceObservationSql ([string]$classification.Receipt.source_high_water_digest)
    $sourceObservationReads += 1
    if ($observation2.ObservedAt -le $observation1.ObservedAt) { throw 'SOURCE_HIGH_WATER_OBSERVATION_ORDER' }
    $state.source_observation_2_at = $observation2.ObservedAt.ToString('o')
    Set-StatePhase $state 'SOURCE_HIGH_WATER_READ_2' $resolvedState
    Set-StatePhase $state 'REVERSE_DELTA_APPLYING' $resolvedState
    Invoke-PsqlPrivate $legacyDatabaseUrl $classification.TransactionSql
    $databaseTransactions += 1
    Set-StatePhase $state 'REVERSE_DELTA_APPLIED' $resolvedState
    if ($sourceObservationReads -ne 2 -or [int]$classification.Receipt.zero_delta_reads -ne 2) { throw 'TWO_ZERO_DELTA_READS_REQUIRED' }
    # Reverse succeeds only after the exact target-era delta converged. Restore
    # legacy client writes and signup last; master remains fenced and its hook
    # remains disabled until the separately governed environment rollback.
    Set-StatePhase $state 'LEGACY_WRITERS_RESTORING' $resolvedState
    Invoke-PsqlPrivate $legacyDatabaseUrl $classification.LegacyRestoreSql
    $databaseTransactions += 1
    $legacyAclRestored = Join-Path $privateRoot 'legacy-acl-restored.json'
    Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.LegacyAclObservationSql $legacyAclRestored 'LEGACY_ACL_POST_RESTORE_READ_FAILED'
    $null = Invoke-AclVerifier $privateInput $legacyAclRestored 'legacy'
    $aclRestoreVerifications += 1
    Set-StatePhase $state 'LEGACY_WRITERS_RESTORED' $resolvedState
    $legacyConfig = Invoke-AuthConfig $managementToken $LegacyProjectRef
    $providerReads += 1
    if ([bool]$legacyConfig.disable_signup -ne $true) { throw 'LEGACY_SIGNUP_FENCE_PREIMAGE_DRIFT' }
    Set-StatePhase $state 'LEGACY_SIGNUP_RESTORING' $resolvedState
    $legacyRestored = Invoke-AuthConfig $managementToken $LegacyProjectRef @{ disable_signup = $false }
    $providerWrites += 1
    if ([bool]$legacyRestored.disable_signup -ne $false) { throw 'LEGACY_SIGNUP_RESTORE_FAILED' }
    Set-StatePhase $state 'COMPLETE' $resolvedState
  }

  Write-SafeResult ($(if ($direction -ceq 'forward') { 'FORWARD_FENCE_DELTA_CONVERGED' } else { 'REVERSE_DELTA_CONVERGED_LEGACY_WRITES_RESTORED' })) ([ordered]@{
    direction = $direction
    packet_input_digest = $inputDigest
    identity_map_digest = [string]$classification.Receipt.identity_map_digest
    source_high_water_digest = [string]$classification.Receipt.source_high_water_digest
    zero_delta_reads = 2
    source_observation_reads = $sourceObservationReads
    acl_preimage_reads = $aclPreimageReads
    acl_restore_verifications = $aclRestoreVerifications
    writer_capture_reads = $writerCaptureReads
    writer_drain_reads = $writerDrainReads
    writer_lock_barriers = $writerLockBarriers
    signup_admission_reads = $signupAdmissionReads
    signup_admission_barriers = $signupAdmissionBarriers
    signup_admission_restores = $signupAdmissionRestores
    provider_reads = $providerReads
    provider_writes = $providerWrites
    database_transactions = $databaseTransactions
    rollback_actions = $rollbackActions
    target_environment_changes = 0
    deployments = 0
    production_changes = 0
  })
}
catch {
  $category = ([string]$_.Exception.Message -replace '[^A-Za-z0-9_]', '').ToUpperInvariant()
  if ($category.Length -gt 96) { $category = $category.Substring(0, 96) }
  $effect = 'NO_EFFECT_CONFIRMED'
  try {
    if ($null -ne $state -and $null -ne $classification -and $null -ne $managementToken) {
      if ([string]$state.direction -ceq 'reverse' -and [string]$state.phase -in @('LEGACY_WRITERS_RESTORING','LEGACY_WRITERS_RESTORED','LEGACY_SIGNUP_RESTORING')) {
        $refenceFailed = $false
        try {
          $legacyRefenced = Invoke-AuthConfig $managementToken $LegacyProjectRef @{ disable_signup = $true }
          $providerWrites += 1
          if ([bool]$legacyRefenced.disable_signup -ne $true) { $refenceFailed = $true }
        }
        catch { $refenceFailed = $true }
        try {
          $legacyRefenceProof = Join-Path $privateRoot 'legacy-refence-revoke-proof.json'
          Invoke-PsqlJsonPrivate $legacyDatabaseUrl $classification.LegacyFenceSql $legacyRefenceProof 'LEGACY_REFENCE_REVOKE_FAILED'
          $databaseTransactions += 1
          $null = Assert-WriterRevokeReceipt $legacyRefenceProof $LegacySchema ([string]$classification.Receipt.legacy_acl_preimage_digest)
          $legacyRefence = Invoke-ExactWriterDrainBarrier $legacyDatabaseUrl $privateInput $classification.LegacyWriterCaptureSql $privateRoot 'LEGACY' $state $resolvedState -Side 'legacy' -NoPhaseJournal
          $writerCaptureReads += [int]$legacyRefence.CaptureReads
          $writerDrainReads += [int]$legacyRefence.DrainReads
          $writerLockBarriers += [int]$legacyRefence.LockBarriers
          $databaseTransactions += [int]$legacyRefence.LockBarriers
        }
        catch { $refenceFailed = $true }
        if ($refenceFailed) { throw 'REVERSE_ACTIVATION_REFENCE_FAILED' }
        $rollbackActions += 1
        $effect = 'REVERSE_ACTIVATION_FAILED_BOTH_SIDES_FENCED_DELTA_QUARANTINED'
        Set-StatePhase $state 'QUARANTINED_HOLD' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'forward' -and [string]$state.phase -in @('LEGACY_SIGNUP_FENCING','LEGACY_SIGNUP_FENCED','LEGACY_WRITERS_PREOBSERVING','LEGACY_WRITERS_PREOBSERVED')) {
        $restored = Invoke-AuthConfig $managementToken $LegacyProjectRef @{ disable_signup = [bool]$state.legacy_disable_signup_preimage }
        $providerWrites += 1
        if ([bool]$restored.disable_signup -ne [bool]$state.legacy_disable_signup_preimage) { throw 'LEGACY_PREIMAGE_RESTORE_FAILED' }
        $rollbackActions += 1
        $effect = 'EXACT_PREIMAGE_RESTORED'
        Set-StatePhase $state 'ROLLED_BACK' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'reverse' -and [string]$state.phase -in @('MASTER_HOOK_DISABLING','MASTER_HOOK_DISABLED','MASTER_SIGNUP_PREOBSERVING','MASTER_SIGNUP_PREOBSERVED')) {
        $restored = Invoke-AuthConfig $managementToken $MasterProjectRef @{ hook_before_user_created_enabled = [bool]$state.master_hook_enabled_preimage }
        $providerWrites += 1
        if ([bool]$restored.hook_before_user_created_enabled -ne [bool]$state.master_hook_enabled_preimage) { throw 'MASTER_PREIMAGE_RESTORE_FAILED' }
        $rollbackActions += 1
        $effect = 'EXACT_PREIMAGE_RESTORED'
        Set-StatePhase $state 'ROLLED_BACK' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'reverse' -and [string]$state.phase -in @('MASTER_SIGNUP_FENCING','MASTER_SIGNUP_FENCED','MASTER_WRITERS_PREOBSERVING','MASTER_WRITERS_PREOBSERVED','MASTER_HOOK_RESTORING','MASTER_HOOK_RESTORED','MASTER_SIGNUP_RESTORING')) {
        $restored = Invoke-AuthConfig $managementToken $MasterProjectRef @{ hook_before_user_created_enabled = [bool]$state.master_hook_enabled_preimage }
        $providerWrites += 1
        if ([bool]$restored.hook_before_user_created_enabled -ne [bool]$state.master_hook_enabled_preimage) { throw 'MASTER_PREIMAGE_RESTORE_FAILED' }
        $signupRestoreProof = Join-Path $privateRoot 'catch-master-signup-admission-restored.json'
        Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionRestoreSql $signupRestoreProof 'MASTER_SIGNUP_ADMISSION_RESTORE_FAILED'
        $null = Assert-SignupAdmissionReceipt $signupRestoreProof 'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED'
        $databaseTransactions += 1
        $signupAdmissionRestores += 1
        $rollbackActions += 1
        $effect = 'EXACT_PREIMAGE_RESTORED'
        Set-StatePhase $state 'ROLLED_BACK' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'forward' -and [string]$state.phase -in @('LEGACY_WRITER_REVOKE_COMMITTED','LEGACY_WRITER_SET_CAPTURING','LEGACY_WRITER_SET_CAPTURED','LEGACY_WRITERS_DRAINING','LEGACY_WRITERS_DRAINED','LEGACY_LOCK_BARRIER_ACQUIRING')) {
        $effect = 'LEGACY_ACL_REVOKED_WRITER_DRAIN_INCOMPLETE_HOLD_FENCED'
        Set-StatePhase $state 'QUARANTINED_HOLD' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'reverse' -and [string]$state.phase -in @('MASTER_WRITER_REVOKE_COMMITTED','MASTER_WRITER_SET_CAPTURING','MASTER_WRITER_SET_CAPTURED','MASTER_WRITERS_DRAINING','MASTER_WRITERS_DRAINED','MASTER_LOCK_BARRIER_ACQUIRING')) {
        $effect = 'MASTER_ACL_REVOKED_WRITER_DRAIN_INCOMPLETE_HOLD_FENCED'
        Set-StatePhase $state 'QUARANTINED_HOLD' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'forward' -and [string]$state.phase -in @('LEGACY_WRITERS_FENCING','LEGACY_WRITERS_FENCED','SOURCE_HIGH_WATER_READ_1','SOURCE_HIGH_WATER_READ_2','FORWARD_DELTA_APPLYING','FORWARD_DELTA_APPLIED')) {
        if (-not (Test-Path -LiteralPath $classification.ObservedRestoreSql -PathType Leaf)) { throw 'OBSERVED_ACL_RESTORE_MISSING' }
        $recovery = Invoke-ExactAclRecovery $legacyDatabaseUrl $privateInput $classification.AclObservationSql $primaryAclPreobserve $classification.ObservedRestoreSql $privateRoot 'catch-primary' -WriterCaptureSql $classification.WriterCaptureSql -PhasePrefix 'LEGACY' -State $state -ResolvedStatePath $resolvedState -DrainBeforeRestore:([string]$state.phase -ceq 'LEGACY_WRITERS_FENCING')
        $databaseTransactions += [int]$recovery.DatabaseTransactions
        $aclRestoreVerifications += [int]$recovery.RestoreVerifications
        $writerCaptureReads += [int]$recovery.CaptureReads
        $writerDrainReads += [int]$recovery.DrainReads
        $writerLockBarriers += [int]$recovery.LockBarriers
        $restored = Invoke-AuthConfig $managementToken $LegacyProjectRef @{ disable_signup = [bool]$state.legacy_disable_signup_preimage }
        $providerWrites += 1
        if ([bool]$restored.disable_signup -ne [bool]$state.legacy_disable_signup_preimage) { throw 'LEGACY_PREIMAGE_RESTORE_FAILED' }
        $rollbackActions += 1
        $effect = if ([string]$state.phase -in @('FORWARD_DELTA_APPLYING','FORWARD_DELTA_APPLIED')) { 'TARGET_DELTA_QUARANTINED_LEGACY_PREIMAGE_RESTORED' } else { 'EXACT_PREIMAGE_RESTORED' }
        Set-StatePhase $state 'ROLLED_BACK' $resolvedState
      }
      elseif ([string]$state.direction -ceq 'reverse' -and [string]$state.phase -in @('MASTER_WRITERS_FENCING','MASTER_WRITERS_FENCED','SOURCE_HIGH_WATER_READ_1','SOURCE_HIGH_WATER_READ_2','REVERSE_DELTA_APPLYING','REVERSE_DELTA_APPLIED')) {
        if (-not (Test-Path -LiteralPath $classification.ObservedRestoreSql -PathType Leaf)) { throw 'OBSERVED_ACL_RESTORE_MISSING' }
        $recovery = Invoke-ExactAclRecovery $masterDatabaseUrl $privateInput $classification.AclObservationSql $primaryAclPreobserve $classification.ObservedRestoreSql $privateRoot 'catch-primary' -WriterCaptureSql $classification.WriterCaptureSql -PhasePrefix 'MASTER' -State $state -ResolvedStatePath $resolvedState -DrainBeforeRestore:([string]$state.phase -ceq 'MASTER_WRITERS_FENCING')
        $databaseTransactions += [int]$recovery.DatabaseTransactions
        $aclRestoreVerifications += [int]$recovery.RestoreVerifications
        $writerCaptureReads += [int]$recovery.CaptureReads
        $writerDrainReads += [int]$recovery.DrainReads
        $writerLockBarriers += [int]$recovery.LockBarriers
        $restored = Invoke-AuthConfig $managementToken $MasterProjectRef @{ hook_before_user_created_enabled = [bool]$state.master_hook_enabled_preimage }
        $providerWrites += 1
        if ([bool]$restored.hook_before_user_created_enabled -ne [bool]$state.master_hook_enabled_preimage) { throw 'MASTER_PREIMAGE_RESTORE_FAILED' }
        $signupRestoreProof = Join-Path $privateRoot 'catch-master-signup-admission-restored.json'
        Invoke-PsqlJsonPrivate $masterDatabaseUrl $classification.SignupAdmissionRestoreSql $signupRestoreProof 'MASTER_SIGNUP_ADMISSION_RESTORE_FAILED'
        $null = Assert-SignupAdmissionReceipt $signupRestoreProof 'PASS_SIGNUP_ADMISSION_PREIMAGE_RESTORED'
        $databaseTransactions += 1
        $signupAdmissionRestores += 1
        $rollbackActions += 1
        $effect = if ([string]$state.phase -in @('REVERSE_DELTA_APPLYING','REVERSE_DELTA_APPLIED')) { 'LEGACY_DELTA_QUARANTINED_MASTER_PREIMAGE_RESTORED' } else { 'EXACT_PREIMAGE_RESTORED' }
        Set-StatePhase $state 'ROLLED_BACK' $resolvedState
      }
    }
  }
  catch {
    $effect = 'AMBIGUOUS_HOLD'
    try { if ($null -ne $state) { Set-StatePhase $state 'AMBIGUOUS_HOLD' $resolvedState } } catch {}
  }
  Write-SafeResult 'HOLD_MAZER_MASTER_CUTOVER_DATA_FENCE' ([ordered]@{
    category = $category
    effect_status = $effect
    provider_reads = $providerReads
    provider_writes = $providerWrites
    database_transactions = $databaseTransactions
    rollback_actions = $rollbackActions
    acl_restore_verifications = $aclRestoreVerifications
    writer_capture_reads = $writerCaptureReads
    writer_drain_reads = $writerDrainReads
    writer_lock_barriers = $writerLockBarriers
    signup_admission_reads = $signupAdmissionReads
    signup_admission_barriers = $signupAdmissionBarriers
    signup_admission_restores = $signupAdmissionRestores
    deployments = 0
    production_changes = 0
  })
  exit 2
}
finally {
  $managementToken = $null
  $legacyDatabaseUrl = $null
  $masterDatabaseUrl = $null
  if ($null -ne $privateRoot -and (Test-Path -LiteralPath $privateRoot -PathType Container)) {
    $resolvedPrivate = Assert-PathUnder $privateRoot @($SecretPacketRoot)
    Remove-Item -LiteralPath $resolvedPrivate -Recurse -Force
  }
}
