[CmdletBinding(DefaultParameterSetName = 'Source')]
param(
  [Parameter(Mandatory = $true, ParameterSetName = 'Source')][switch]$SourceOnlyValidate,
  [Parameter(Mandatory = $true, ParameterSetName = 'Probe')][switch]$LocalSentinelProbe,
  [Parameter(Mandatory = $true, ParameterSetName = 'Adversary')][ValidateSet('timeout','stderr','malformed','empty_object','wrong_schema','wrong_result','missing_fields','duplicate_key','escaped_key','array','scalar')][string]$LocalTransportAdversary,
  [Parameter(Mandatory = $true, ParameterSetName = 'Validate')][switch]$ValidateInvocationOnly,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][Parameter(Mandatory = $true, ParameterSetName = 'Validate')][string]$InvocationPath,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][Parameter(Mandatory = $true, ParameterSetName = 'Validate')][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedInvocationSha256,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][switch]$ExecuteProtected
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Root = [IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot, '..', '..'))
$Runtime = Join-Path $Root 'runtime\atlas'
$Secrets = Join-Path $Root 'secrets'
$PacketRoot = Join-Path $Secrets 'packet\mazer-master-preparation-r017'
$HostScript = Join-Path $PSScriptRoot 'invoke_supabase_mazer_master_preparation_r017.ps1'
$Packet = 'FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001'
$SourceRelative = 'private-source-auth-action-preimage-v3-20260826.json'
$SourceSha = '9326145071e2e067286e6460d06187d89d3bdc6b82c202b2cbea2f313f0b35ae'
$ManifestRelative = 'materialized-auth-action-preimage-v3-20260826\manifest.json'
$ManifestSha = 'b60539e13e7b838a0f36adc8333cfdccfc0ac55cccc57330240cacede2335879'
$HostSha = 'd3ec9c210e031ebd887e5f643939ebd584efe218e0db2b346586392bc280453d'
$PredecessorCorrelation = 'a7db1fd5-a165-43e6-a9a8-c267233005b2'
$PredecessorStateName = 'mazer-master-r017-execution-a7db1fd5-a165-43e6-a9a8-c267233005b2.json'
$PredecessorStateSha = '5e01271273a910d861c1fb0712ac7d48a8b565a971f6a270cf6fe8409138a0d9'
$OriginatingTaskId = '019fa791-8d17-7c83-9c61-3e3c687e9dd7'
$EffectClass = 'supabase_protected_master_preparation'
$EffectTarget = 'supabase:geknvnrmktchljnyddwp/public+bxtcuhkotumitoqtrcej/mazer'
$MaxEffectCount = 20
$LegacyRef = 'geknvnrmktchljnyddwp'
$MasterRef = 'bxtcuhkotumitoqtrcej'
$CredentialTarget = 'Supabase CLI:supabase'
$NodeShimSha = '4053ed27750a4e4593959a7caa7ea2562ebd56912852454547f12889a9b8d3c9'
$PsqlShimSha = '9aaf469a1d7f2f7e3d13d8f32609f623ce227e8d015439ed6e5bd22c0f2e3b19'
$script:ProtectedChildStarted = $false
$script:SafeExecutionCorrelation = $null

function Get-Sha256([string]$Path) {
  $stream = [IO.File]::OpenRead($Path)
  try { $hasher = [Security.Cryptography.SHA256]::Create(); try { return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() } finally { $hasher.Dispose() } }
  finally { $stream.Dispose() }
}

function Get-BytesSha256([byte[]]$Bytes) {
  $hasher = [Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
  finally { $hasher.Dispose() }
}

function Read-JsonSnapshot([string]$Path, [string]$Boundary, [string]$ExpectedSha) {
  $resolved = Assert-Under $Path $Boundary
  if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { throw 'APPROVAL_FILE_MISSING' }
  Assert-NoReparse $resolved $Boundary
  $stream = New-Object IO.FileStream($resolved, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
  $bytes = $null
  try {
    if ($stream.Length -lt 2 -or $stream.Length -gt 262144) { throw 'APPROVAL_FILE_SIZE' }
    $bytes = New-Object byte[] ([int]$stream.Length); $offset = 0
    while ($offset -lt $bytes.Length) { $read = $stream.Read($bytes,$offset,$bytes.Length-$offset); if ($read -le 0) { throw 'APPROVAL_FILE_TRUNCATED' }; $offset += $read }
    $sha = Get-BytesSha256 $bytes
    if ($sha -cne $ExpectedSha) { throw 'APPROVAL_FILE_DIGEST' }
    $text = (New-Object Text.UTF8Encoding($false,$true)).GetString($bytes)
  }
  finally { $stream.Dispose(); if ($null -ne $bytes) { [Array]::Clear($bytes,0,$bytes.Length) } }
  if ($text -match '[^\x00-\x7f]' -or $text -match '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]') { throw 'APPROVAL_FILE_ASCII' }
  try { $value = $text | ConvertFrom-Json } catch { throw 'APPROVAL_FILE_JSON' }
  if ($null -eq $value -or $value -is [Array] -or $value -isnot [pscustomobject]) { throw 'APPROVAL_FILE_ROOT' }
  return [pscustomobject]@{ Path=$resolved; Sha256=$sha; Value=$value; Text=$text }
}

function Parse-Rfc3339([string]$Value, [string]$Code) {
  if ($Value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?Z$') { throw $Code }
  try { return [DateTimeOffset]::Parse($Value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind) } catch { throw $Code }
}

function Get-RawJsonString([string]$Text, [string]$Key, [string]$Code) {
  $match=[regex]::Match($Text,'"'+[regex]::Escape($Key)+'"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"')
  if(-not$match.Success){throw $Code}
  if($match.Groups[1].Value.Contains('\')){throw $Code}
  return [string]$match.Groups[1].Value
}

function Get-CanonicalAliasPath([string]$DecisionPath) {
  $stem=[IO.Path]::GetFileNameWithoutExtension($DecisionPath)
  foreach($suffix in @('-operator-decision-request','-decision-request')){if($stem.EndsWith($suffix,[StringComparison]::Ordinal)){$stem=$stem.Substring(0,$stem.Length-$suffix.Length);break}}
  return [IO.Path]::GetFullPath((Join-Path ([IO.Path]::GetDirectoryName($DecisionPath)) ($stem+'-scoped-approval-alias.json')))
}
function Get-CanonicalAuthorizationPath([string]$AliasPath) { return [IO.Path]::GetFullPath((Join-Path ([IO.Path]::GetDirectoryName($AliasPath)) ([IO.Path]::GetFileNameWithoutExtension($AliasPath)+'-authorization.json'))) }
function Get-CanonicalConsumptionPath([string]$AliasPath) { return [IO.Path]::GetFullPath((Join-Path ([IO.Path]::GetDirectoryName($AliasPath)) ([IO.Path]::GetFileNameWithoutExtension($AliasPath)+'-consumption.json'))) }

function Assert-Under([string]$Path, [string]$Boundary) {
  $candidate = [IO.Path]::GetFullPath($Path)
  $root = [IO.Path]::GetFullPath($Boundary).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
  if (-not $candidate.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'PATH_SCOPE' }
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

function Read-Invocation([string]$Path, [string]$ExpectedSha) {
  $resolved = Assert-Under $Path $PacketRoot
  if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { throw 'INVOCATION_MISSING' }
  Assert-NoReparse $resolved $PacketRoot
  $stream = New-Object IO.FileStream($resolved, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
  $bytes = $null
  try {
    if ($stream.Length -lt 2 -or $stream.Length -gt 32768) { throw 'INVOCATION_SIZE' }
    $bytes = New-Object byte[] ([int]$stream.Length); $offset = 0
    while ($offset -lt $bytes.Length) { $read = $stream.Read($bytes, $offset, $bytes.Length - $offset); if ($read -le 0) { throw 'INVOCATION_TRUNCATED' }; $offset += $read }
  }
  finally { $stream.Dispose() }
  try {
    if ((Get-BytesSha256 $bytes) -cne $ExpectedSha) { throw 'INVOCATION_DIGEST_DRIFT' }
    $text = (New-Object Text.UTF8Encoding($false, $true)).GetString($bytes)
  }
  finally { if ($null -ne $bytes) { [Array]::Clear($bytes, 0, $bytes.Length) } }
  if ($text -match '[^\x00-\x7f]' -or $text -match '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]') { throw 'INVOCATION_ASCII' }
  $trimmed = $text.Trim()
  if (-not $trimmed.StartsWith('{') -or -not $trimmed.EndsWith('}')) { throw 'INVOCATION_ROOT_OBJECT' }
  $expectedKeys = @('schema','packet','decision_request_path','decision_request_sha256','approval_alias_path','approval_alias_sha256','approval_authorization_path','approval_authorization_sha256','approval_consumption_path','approval_consumption_sha256','approval_expires_at','predecessor_correlation_id','predecessor_state_path','predecessor_state_sha256','execution_correlation_id','private_source_path','private_source_sha256','private_manifest_path','private_manifest_sha256','successor_state_path','host_path','host_sha256','launcher_path','launcher_sha256','not_before','issued_at','expires_at')
  $keys = @([regex]::Matches($text, '"((?:\\["\\/bfnrt]|\\u[0-9A-Fa-f]{4}|[^"\\\x00-\x1f])*)"\s*:') | ForEach-Object { try { [string](('"' + $_.Groups[1].Value + '"') | ConvertFrom-Json) } catch { throw 'INVOCATION_KEY_ENCODING' } })
  if ($keys.Count -ne $expectedKeys.Count -or (@($keys | Sort-Object -Unique).Count -ne $keys.Count) -or (($keys | Sort-Object) -join "`n") -cne (($expectedKeys | Sort-Object) -join "`n")) { throw 'INVOCATION_KEYS' }
  try { $value = $text | ConvertFrom-Json } catch { throw 'INVOCATION_JSON' }
  if ($null -eq $value -or $value -is [Array] -or $value -isnot [pscustomobject]) { throw 'INVOCATION_ROOT_OBJECT' }
  foreach ($key in @($expectedKeys | Where-Object { $_ -notin @('approval_expires_at','not_before','issued_at','expires_at') })) { if ($value.$key -isnot [string]) { throw 'INVOCATION_VALUE_TYPES' } }
  if ([string]$value.schema -cne 'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v2' -or [string]$value.packet -cne $Packet) { throw 'INVOCATION_SCHEMA' }
  if ([string]$value.predecessor_correlation_id -cne $PredecessorCorrelation -or [string]$value.predecessor_state_sha256 -cne $PredecessorStateSha) { throw 'PREDECESSOR_BINDING' }
  if ([string]$value.private_source_sha256 -cne $SourceSha -or [string]$value.private_manifest_sha256 -cne $ManifestSha -or [string]$value.host_sha256 -cne $HostSha) { throw 'SEALED_HASH_BINDING' }
  if ([string]$value.execution_correlation_id -cnotmatch '^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$') { throw 'EXECUTION_CORRELATION' }
  $source = Assert-Under ([string]$value.private_source_path) $PacketRoot
  $manifest = Assert-Under ([string]$value.private_manifest_path) $PacketRoot
  $predecessor = Assert-Under ([string]$value.predecessor_state_path) $Runtime
  $successor = Assert-Under ([string]$value.successor_state_path) $Runtime
  $hostPath = Assert-Under ([string]$value.host_path) $PSScriptRoot
  $launcherPath = Assert-Under ([string]$value.launcher_path) $PSScriptRoot
  $decisionPath = Assert-Under ([string]$value.decision_request_path) $Runtime
  $aliasPath = Assert-Under ([string]$value.approval_alias_path) $Runtime
  $authorizationPath = Assert-Under ([string]$value.approval_authorization_path) $Runtime
  $consumptionPath = Assert-Under ([string]$value.approval_consumption_path) $Runtime
  if ($aliasPath-cne(Get-CanonicalAliasPath $decisionPath)-or$authorizationPath-cne(Get-CanonicalAuthorizationPath $aliasPath)-or$consumptionPath-cne(Get-CanonicalConsumptionPath $aliasPath)) { throw 'APPROVAL_PATH_BINDING' }
  if ($source -cne [IO.Path]::GetFullPath((Join-Path $PacketRoot $SourceRelative)) -or $manifest -cne [IO.Path]::GetFullPath((Join-Path $PacketRoot $ManifestRelative))) { throw 'SEALED_PATH_BINDING' }
  if ($predecessor -cne [IO.Path]::GetFullPath((Join-Path $Runtime $PredecessorStateName))) { throw 'PREDECESSOR_PATH_BINDING' }
  $expectedSuccessor = [IO.Path]::GetFullPath((Join-Path $Runtime ('mazer-master-r017-execution-' + [string]$value.execution_correlation_id + '.json')))
  if ($successor -cne $expectedSuccessor -or (Test-Path -LiteralPath $successor)) { throw 'SUCCESSOR_STATE_BINDING' }
  if ($hostPath -cne [IO.Path]::GetFullPath($HostScript) -or $launcherPath -cne [IO.Path]::GetFullPath($PSCommandPath)) { throw 'HOST_PATH_BINDING' }
  foreach ($file in @($source,$manifest,$predecessor,$hostPath,$launcherPath)) { if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw 'SEALED_FILE_MISSING' } }
  Assert-NoReparse $source $PacketRoot; Assert-NoReparse $manifest $PacketRoot; Assert-NoReparse $predecessor $Runtime; Assert-NoReparse $hostPath $PSScriptRoot; Assert-NoReparse $launcherPath $PSScriptRoot
  if ((Get-Sha256 $source) -cne $SourceSha -or (Get-Sha256 $manifest) -cne $ManifestSha -or (Get-Sha256 $predecessor) -cne $PredecessorStateSha -or (Get-Sha256 $hostPath) -cne $HostSha -or (Get-Sha256 $launcherPath) -cne [string]$value.launcher_sha256) { throw 'SEALED_FILE_DIGEST_DRIFT' }
  try { $prior = Get-Content -LiteralPath $predecessor -Raw | ConvertFrom-Json } catch { throw 'PREDECESSOR_STATE_JSON' }
  if ([string]$prior.phase -cne 'AMBIGUOUS_HOLD' -or [string]$prior.previous_phase -cne 'PREFLIGHT' -or $null -ne $prior.watchdog_pid -or $null -ne $prior.fence_started_at -or $null -ne $prior.rollback_deadline_at -or (Test-Path -LiteralPath ($predecessor + '.fence.json'))) { throw 'PREDECESSOR_EFFECT_STATE' }
  $decision = Read-JsonSnapshot $decisionPath $Runtime ([string]$value.decision_request_sha256)
  $alias = Read-JsonSnapshot $aliasPath $Runtime ([string]$value.approval_alias_sha256)
  $authorization = Read-JsonSnapshot $authorizationPath $Runtime ([string]$value.approval_authorization_sha256)
  $consumption = Read-JsonSnapshot $consumptionPath $Runtime ([string]$value.approval_consumption_sha256)
  $d=$decision.Value;$a=$alias.Value;$z=$authorization.Value;$c=$consumption.Value
  $envelopeApprovalExpires=Get-RawJsonString $text 'approval_expires_at' 'INVOCATION_TIMESTAMP';$envelopeNotBefore=Get-RawJsonString $text 'not_before' 'INVOCATION_TIMESTAMP';$envelopeIssued=Get-RawJsonString $text 'issued_at' 'INVOCATION_TIMESTAMP';$envelopeExpires=Get-RawJsonString $text 'expires_at' 'INVOCATION_TIMESTAMP'
  $decisionExpires=Get-RawJsonString $decision.Text 'expires_at' 'APPROVAL_TIMESTAMP';$aliasExpires=Get-RawJsonString $alias.Text 'expires_at' 'APPROVAL_TIMESTAMP';$aliasIssuedRaw=Get-RawJsonString $alias.Text 'issued_at' 'APPROVAL_TIMESTAMP';$authorizedRaw=Get-RawJsonString $authorization.Text 'authorized_at' 'APPROVAL_TIMESTAMP';$consumedRaw=Get-RawJsonString $consumption.Text 'consumed_at' 'APPROVAL_TIMESTAMP'
  if ([string]$d.schema-cne'atlas.operator-decision-request.v1'-or[string]$d.packet-cne$Packet-or[string]$d.status-cne'AWAITING_OPERATOR_DECISION'-or[bool]$d.execution_authority) { throw 'DECISION_CONTRACT' }
  if ([string]$a.schema-cne'atlas.scoped-approval-alias.v1'-or[string]$a.packet-cne$Packet-or[string]$a.status-cne'OPEN'-or-not[bool]$a.single_use-or[bool]$a.execution_authority-or[string]$a.originating_task_id-cne$OriginatingTaskId-or[string]$a.expected_operator_response-cne('APPROVE '+[string]$a.approval_code)) { throw 'ALIAS_CONTRACT' }
  $decisionRelative=[IO.Path]::GetFullPath((Join-Path $Root ([string]$a.decision_request.path)));$authorizationDecisionRelative=[IO.Path]::GetFullPath((Join-Path $Root ([string]$z.decision_request.path)));$authorizationAliasRelative=[IO.Path]::GetFullPath((Join-Path $Root ([string]$z.alias.path)))
  $phraseSha=Get-BytesSha256 ([Text.Encoding]::UTF8.GetBytes([string]$d.exact_authorization_phrase))
  if ([string]$a.allowed_effect.effect_class-cne$EffectClass-or[string]$a.allowed_effect.target-cne$EffectTarget-or[int]$a.allowed_effect.max_effect_count-ne$MaxEffectCount-or[string]$a.decision_request.sha256-cne$decision.Sha256-or$decisionRelative-cne$decisionPath-or[string]$a.decision_request.exact_authorization_phrase_sha256-cne$phraseSha) { throw 'ALIAS_BINDING' }
  if ([string]$z.schema-cne'atlas.scoped-approval-authorization.v1'-or[string]$z.packet-cne$Packet-or[string]$z.status-cne'AUTHORIZED_SINGLE_USE'-or-not[bool]$z.single_use-or-not[bool]$z.execution_authority-or[string]$z.originating_task_id-cne$OriginatingTaskId-or[string]$z.approval_code-cne[string]$a.approval_code-or[string]$z.alias.sha256-cne$alias.Sha256-or$authorizationAliasRelative-cne$aliasPath-or[string]$z.decision_request.sha256-cne$decision.Sha256-or$authorizationDecisionRelative-cne$decisionPath-or[string]$z.decision_request.exact_authorization_phrase_sha256-cne$phraseSha-or[string]$z.allowed_effect.effect_class-cne$EffectClass-or[string]$z.allowed_effect.target-cne$EffectTarget-or[int]$z.allowed_effect.max_effect_count-ne$MaxEffectCount-or[string]$z.intent_digest-cne[string]$a.intent_digest) { throw 'AUTHORIZATION_BINDING' }
  if ([string]$c.schema-cne'atlas.scoped-approval-consumption.v1'-or[string]$c.packet-cne$Packet-or[string]$c.status-cne'CONSUMED'-or[bool]$c.reusable-or[string]$c.approval_code-cne[string]$a.approval_code-or[int]$c.max_effect_count-ne$MaxEffectCount-or[string]$c.authorization_sha256-cne$authorization.Sha256-or[string]$c.intent_digest-cne[string]$a.intent_digest-or[string]$c.execution_correlation_id-cne[string]$value.execution_correlation_id) { throw 'CONSUMPTION_BINDING' }
  if ([string]$d.sealed_inputs.execution_correlation_id-cne[string]$value.execution_correlation_id-or[string]$d.sealed_inputs.private_source_sha256-cne$SourceSha-or[string]$d.sealed_inputs.manifest_sha256-cne$ManifestSha-or[string]$d.sealed_inputs.host_sha256-cne$HostSha-or[string]$d.sealed_inputs.credential_safe_launcher_sha256-cne[string]$value.launcher_sha256) { throw 'DECISION_EXECUTION_BINDING' }
  if ($envelopeApprovalExpires-cne$aliasExpires-or$envelopeExpires-cne$aliasExpires-or$decisionExpires-cne$aliasExpires-or$envelopeNotBefore-cne$consumedRaw) { throw 'INVOCATION_APPROVAL_TIME_BINDING' }
  $issued=Parse-Rfc3339 $envelopeIssued 'INVOCATION_TIMESTAMP';$notBefore=Parse-Rfc3339 $envelopeNotBefore 'INVOCATION_TIMESTAMP';$expires=Parse-Rfc3339 $envelopeExpires 'INVOCATION_TIMESTAMP';$aliasIssued=Parse-Rfc3339 $aliasIssuedRaw 'APPROVAL_TIMESTAMP';$authorized=Parse-Rfc3339 $authorizedRaw 'APPROVAL_TIMESTAMP';$consumed=Parse-Rfc3339 $consumedRaw 'APPROVAL_TIMESTAMP'
  $now=[DateTimeOffset]::UtcNow
  if ($aliasIssued -gt $authorized -or $authorized -gt $consumed -or $consumed -gt $issued -or $issued -gt $now.AddSeconds(5) -or $notBefore -gt $now.AddSeconds(5)) { throw 'INVOCATION_NOT_YET_VALID' }
  if ($expires -le $now -or $issued -ge $expires -or $expires -gt $aliasIssued.AddHours(24)) { throw 'INVOCATION_EXPIRED' }
  return [pscustomobject]@{ Source=$source; SourceSha=$SourceSha; State=$successor; Correlation=[string]$value.execution_correlation_id }
}

function Find-HostRoot {
  $candidate = [IO.DirectoryInfo]$Root
  while ($null -ne $candidate) {
    if (Test-Path -LiteralPath (Join-Path $candidate.FullName 'secrets\local\supabase-project-database-passwords\mazer-password.dpapi')) { return $candidate.FullName }
    $candidate = $candidate.Parent
  }
  throw 'HOST_ROOT_MISSING'
}

function Read-ProjectPassword([string]$Path, [string]$ProjectRef) {
  $protected=[IO.File]::ReadAllBytes($Path);$entropy=[Text.Encoding]::UTF8.GetBytes("ATLAS|Supabase|ProjectDatabasePassword|v1|$ProjectRef")
  try { $plain=[Security.Cryptography.ProtectedData]::Unprotect($protected,$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser);if($plain.Length-ne40){[Array]::Clear($plain,0,$plain.Length);throw 'PASSWORD_SHAPE'};return $plain }
  finally { [Array]::Clear($protected,0,$protected.Length);[Array]::Clear($entropy,0,$entropy.Length) }
}

function Initialize-CredentialInterop {
  if ('AtlasR017TupleCredentialNative' -as [type]) { return }
  Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct AtlasR017TupleCredential { public UInt32 Flags; public UInt32 Type; public string TargetName; public string Comment; public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten; public UInt32 CredentialBlobSize; public IntPtr CredentialBlob; public UInt32 Persist; public UInt32 AttributeCount; public IntPtr Attributes; public string TargetAlias; public string UserName; }
public static class AtlasR017TupleCredentialNative { [DllImport("advapi32.dll",EntryPoint="CredReadW",CharSet=CharSet.Unicode,SetLastError=true)] public static extern bool CredRead(string target,UInt32 type,UInt32 flags,out IntPtr credential); [DllImport("advapi32.dll",SetLastError=true)] public static extern void CredFree(IntPtr credential); }
'@
}

function Read-ManagementToken {
  Initialize-CredentialInterop;$pointer=[IntPtr]::Zero
  try { if(-not[AtlasR017TupleCredentialNative]::CredRead($CredentialTarget,1,0,[ref]$pointer)-or$pointer-eq[IntPtr]::Zero){throw 'MANAGEMENT_CREDENTIAL_MISSING'};$credential=[Runtime.InteropServices.Marshal]::PtrToStructure($pointer,[type][AtlasR017TupleCredential]);if($credential.CredentialBlobSize-lt16-or$credential.CredentialBlobSize-gt8192){throw 'MANAGEMENT_CREDENTIAL_SHAPE'};$bytes=New-Object byte[] $credential.CredentialBlobSize;[Runtime.InteropServices.Marshal]::Copy($credential.CredentialBlob,$bytes,0,$bytes.Length);try{$unicode=($bytes.Length%2-eq0);if($unicode){for($i=1;$i-lt$bytes.Length;$i+=2){if($bytes[$i]-ne0){$unicode=$false;break}}};$token=if($unicode){[Text.Encoding]::Unicode.GetString($bytes).TrimEnd([char]0)}else{(New-Object Text.UTF8Encoding($false,$true)).GetString($bytes).TrimEnd([char]0)};if($token.Length-lt16-or$token.Length-gt4096-or$token-match'[\x00-\x20\x7f]'){throw 'MANAGEMENT_CREDENTIAL_FORMAT'};return $token}finally{[Array]::Clear($bytes,0,$bytes.Length)} }
  finally { if($pointer-ne[IntPtr]::Zero){[AtlasR017TupleCredentialNative]::CredFree($pointer)} }
}

function ConvertTo-ProcessArgument([string]$Argument) {
  if ([string]::IsNullOrEmpty($Argument)) { return '""' }
  if ($Argument -notmatch '[\s"]') { return $Argument }
  return '"' + ($Argument -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Invoke-Child([string]$File,[string[]]$Arguments,[Collections.IDictionary]$Environment,[int]$TimeoutMs,[switch]$TrackProtectedStart) {
  $start=New-Object Diagnostics.ProcessStartInfo;$start.FileName=$File;$start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
  if($null-ne$start.PSObject.Properties['ArgumentList']){foreach($arg in $Arguments){[void]$start.ArgumentList.Add([string]$arg)}}else{$start.Arguments=(($Arguments|ForEach-Object{ConvertTo-ProcessArgument([string]$_)})-join' ')};foreach($key in $Environment.Keys){$start.EnvironmentVariables[[string]$key]=[string]$Environment[$key]}
  $process=New-Object Diagnostics.Process;$process.StartInfo=$start
  try{if(-not$process.Start()){throw 'CHILD_START'};if($TrackProtectedStart){$script:ProtectedChildStarted=$true};$stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync();if(-not$process.WaitForExit($TimeoutMs)){try{$process.Kill()}catch{};throw 'CHILD_TIMEOUT'};$stdoutText=$stdout.GetAwaiter().GetResult();$stderrText=$stderr.GetAwaiter().GetResult();return [pscustomobject]@{ExitCode=$process.ExitCode;Stdout=$stdoutText;Stderr=$stderrText}}
  finally{$process.Dispose()}
}

function Convert-ProtectedChildReceipt([object]$Child) {
  if(-not[string]::IsNullOrEmpty([string]$Child.Stderr)){throw 'CHILD_STDERR'}
  $text=[string]$Child.Stdout.Trim();if($text.Length-lt2-or$text.Length-gt32768){throw 'CHILD_RECEIPT_SHAPE'}
  if($text-match'[^\x00-\x7f]'-or$text-match'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'){throw 'CHILD_RECEIPT_SHAPE'}
  if(-not$text.StartsWith('{')-or-not$text.EndsWith('}')){throw 'CHILD_RECEIPT_SHAPE'}
  $keys=@([regex]::Matches($text,'"((?:\\["\\/bfnrt]|\\u[0-9A-Fa-f]{4}|[^"\\\x00-\x1f])*)"\s*:')|ForEach-Object{try{[string](('"'+$_.Groups[1].Value+'"')|ConvertFrom-Json)}catch{throw 'CHILD_RECEIPT_KEYS'}})
  if(@($keys|Sort-Object -Unique).Count-ne$keys.Count){throw 'CHILD_RECEIPT_KEYS'}
  try{$receipt=$text|ConvertFrom-Json}catch{throw 'CHILD_RECEIPT_JSON'}
  if($null-eq$receipt-or$receipt-is[Array]-or$receipt-isnot[pscustomobject]){throw 'CHILD_RECEIPT_SHAPE'}
  $baseKeys=@('schema','result','legacy_project_ref','master_project_ref','raw_records_emitted','pii_emitted','secrets_emitted','environment_changes','deployments','production_changes')
  $successKeys=@('phase','master_hook_enabled','legacy_signup_and_acl_restored','fresh_dual_refence_and_catchup_required_for_cutover','fence_lease_seconds','rollback_initiation_deadline_seconds','provider_writes','database_transactions','final_identity_edges','profiles','player','ai','receipts')
  $holdKeys=@('category','rollback_disposition','provider_writes','database_transactions')
  if(@($baseKeys|Where-Object{$_-notin$keys}).Count-ne0){throw 'CHILD_RECEIPT_KEYS'}
  if($receipt.result-ceq'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER'){$expected=@($baseKeys+$successKeys)}elseif($receipt.result-ceq'HOLD_MAZER_MASTER_PREPARATION_R017'){$expected=@($baseKeys+$holdKeys)}else{throw 'CHILD_RECEIPT_RESULT'}
  if($keys.Count-ne$expected.Count-or(($keys|Sort-Object)-join"`n")-cne(($expected|Sort-Object)-join"`n")){throw 'CHILD_RECEIPT_KEYS'}
  if($receipt.schema-isnot[string]-or$receipt.result-isnot[string]-or$receipt.legacy_project_ref-isnot[string]-or$receipt.master_project_ref-isnot[string]-or$receipt.raw_records_emitted-isnot[bool]-or$receipt.pii_emitted-isnot[bool]-or$receipt.secrets_emitted-isnot[bool]){throw 'CHILD_RECEIPT_TYPES'}
  foreach($key in @('environment_changes','deployments','production_changes','provider_writes','database_transactions')){if($receipt.$key-isnot[int]-and$receipt.$key-isnot[long]){throw 'CHILD_RECEIPT_TYPES'}}
  if($receipt.schema-cne'atlas.supabase.mazer-master-preparation-host-result.r017.v1'-or$receipt.legacy_project_ref-cne$LegacyRef-or$receipt.master_project_ref-cne$MasterRef-or[bool]$receipt.raw_records_emitted-or[bool]$receipt.pii_emitted-or[bool]$receipt.secrets_emitted-or[int]$receipt.environment_changes-ne0-or[int]$receipt.deployments-ne0-or[int]$receipt.production_changes-ne0){throw 'CHILD_RECEIPT_VALUES'}
  if($receipt.result-ceq'MASTER_PREPARED_LEGACY_RESTORED_NOT_CUTOVER'){
    foreach($key in @('master_hook_enabled','legacy_signup_and_acl_restored','fresh_dual_refence_and_catchup_required_for_cutover')){if($receipt.$key-isnot[bool]){throw 'CHILD_RECEIPT_TYPES'}}
    foreach($key in @('fence_lease_seconds','rollback_initiation_deadline_seconds','final_identity_edges','profiles','player','ai','receipts')){if($receipt.$key-isnot[int]-and$receipt.$key-isnot[long]){throw 'CHILD_RECEIPT_TYPES'}}
    if($receipt.phase-cne'PREPARATION_COMPLETE'-or-not[bool]$receipt.master_hook_enabled-or-not[bool]$receipt.legacy_signup_and_acl_restored-or-not[bool]$receipt.fresh_dual_refence_and_catchup_required_for_cutover-or[int]$receipt.final_identity_edges-ne19-or[int]$receipt.profiles-ne13-or[int]$receipt.player-ne16-or[int]$receipt.ai-ne16-or[int]$receipt.receipts-ne1887){throw 'CHILD_RECEIPT_VALUES'}
  }else{
    if($receipt.category-isnot[string]-or$receipt.rollback_disposition-isnot[string]){throw 'CHILD_RECEIPT_TYPES'}
    if($receipt.category-cnotmatch'^[A-Z0-9_]{1,96}$'-or$receipt.rollback_disposition-notin@('NO_EFFECT_CONFIRMED','EXACT_ROLLBACK_COMPLETED','ROLLBACK_FAILED')){throw 'CHILD_RECEIPT_VALUES'}
  }
  return $receipt
}

function Write-LauncherHold([string]$Category) {
  $allowed=@('CHILD_TIMEOUT','CHILD_STDERR','CHILD_RECEIPT_JSON','CHILD_RECEIPT_SHAPE','CHILD_RECEIPT_KEYS','CHILD_RECEIPT_SCHEMA','CHILD_RECEIPT_RESULT','CHILD_RECEIPT_TYPES','CHILD_RECEIPT_VALUES','CHILD_DISCLOSURE')
  $candidate=($Category-replace'[^A-Za-z0-9_]','').ToUpperInvariant();$safe=if($candidate-in$allowed){$candidate}elseif($script:ProtectedChildStarted){'POSTSTART_EXECUTION_HOLD'}else{'PRESTART_VALIDATION_HOLD'}
  $value=[ordered]@{schema='atlas.supabase.mazer-master-preparation-credential-safe-launcher-result.r017.v1';result='HOLD_R017_CREDENTIAL_SAFE_LAUNCHER';category=$safe;external_effects_unknown=[bool]$script:ProtectedChildStarted;execution_correlation_id=$script:SafeExecutionCorrelation;raw_records_emitted=$false;pii_emitted=$false;secrets_emitted=$false}
  [Console]::Out.WriteLine(($value|ConvertTo-Json -Compress))
}

function Invoke-SentinelProbe {
  $shell=(Get-Command pwsh -ErrorAction SilentlyContinue);if($null-eq$shell){$shell=Get-Command powershell -ErrorAction Stop}
  $script='$ok=($env:SUPABASE_ACCESS_TOKEN -ceq "sentinel-token-0123456789")-and($env:ATLAS_MAZER_LEGACY_DATABASE_URL -ceq "sentinel-legacy")-and($env:ATLAS_MAZER_MASTER_DATABASE_URL -ceq "sentinel-master"); if($ok){[Console]::Out.WriteLine("{`"result`":`"PASS_R017_CREDENTIAL_SAFE_ENV_SENTINEL`",`"external_calls`":0}");exit 0};exit 7'
  return Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-Command',$script) @{SUPABASE_ACCESS_TOKEN='sentinel-token-0123456789';ATLAS_MAZER_LEGACY_DATABASE_URL='sentinel-legacy';ATLAS_MAZER_MASTER_DATABASE_URL='sentinel-master'} 30000
}

if($PSCmdlet.ParameterSetName-ceq'Source'){$tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$tokens,[ref]$errors);if($errors.Count-ne0){throw 'POWERSHELL_PARSE'};$probe=Invoke-SentinelProbe;if($probe.ExitCode-ne0-or-not[string]::IsNullOrEmpty($probe.Stderr)-or$probe.Stdout-notmatch'PASS_R017_CREDENTIAL_SAFE_ENV_SENTINEL'){throw 'SENTINEL_PROBE'};[Console]::Out.WriteLine('{"result":"PASS_R017_CREDENTIAL_SAFE_LAUNCHER_SOURCE","external_calls":0,"credential_reads":0,"secret_reads":0}');exit 0}
if($PSCmdlet.ParameterSetName-ceq'Probe'){$probe=Invoke-SentinelProbe;[Console]::Out.Write($probe.Stdout);exit $probe.ExitCode}
if($PSCmdlet.ParameterSetName-ceq'Adversary'){
  $shell=(Get-Command pwsh -ErrorAction SilentlyContinue);if($null-eq$shell){$shell=Get-Command powershell -ErrorAction Stop}
  try {
    $script:SafeExecutionCorrelation='00000000-0000-4000-8000-000000000000'
    $valid='{"schema":"atlas.supabase.mazer-master-preparation-host-result.r017.v1","result":"HOLD_MAZER_MASTER_PREPARATION_R017","legacy_project_ref":"geknvnrmktchljnyddwp","master_project_ref":"bxtcuhkotumitoqtrcej","raw_records_emitted":false,"pii_emitted":false,"secrets_emitted":false,"environment_changes":0,"deployments":0,"production_changes":0,"category":"SENTINEL_HOLD","rollback_disposition":"NO_EFFECT_CONFIRMED","provider_writes":0,"database_transactions":0}'
    if($LocalTransportAdversary-ceq'timeout'){$child=Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-Command','Start-Sleep -Milliseconds 500') @{} 100 -TrackProtectedStart}
    elseif($LocalTransportAdversary-ceq'stderr'){$child=Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-Command','[Console]::Error.Write("sentinel");[Console]::Out.Write($env:ATLAS_SENTINEL_RECEIPT)') @{ATLAS_SENTINEL_RECEIPT=$valid} 30000 -TrackProtectedStart}
    else{
      $payload=switch($LocalTransportAdversary){'malformed'{'not-json'}'empty_object'{'{}'}'wrong_schema'{$valid.Replace('atlas.supabase.mazer-master-preparation-host-result.r017.v1','wrong.schema')}'wrong_result'{$valid.Replace('HOLD_MAZER_MASTER_PREPARATION_R017','UNKNOWN_RESULT')}'missing_fields'{$valid.Replace(',"category":"SENTINEL_HOLD"','')}'duplicate_key'{$valid.Substring(0,$valid.Length-1)+',"result":"HOLD_MAZER_MASTER_PREPARATION_R017"}'}'escaped_key'{$valid.Substring(0,$valid.Length-1)+',"\u0072esult":"HOLD_MAZER_MASTER_PREPARATION_R017"}'}'array'{'['+$valid+']'}'scalar'{'42'}default{throw 'ADVERSARY_KIND'}}
      $child=Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-Command','[Console]::Out.Write($env:ATLAS_SENTINEL_RECEIPT)') @{ATLAS_SENTINEL_RECEIPT=$payload} 30000 -TrackProtectedStart
    }
    [void](Convert-ProtectedChildReceipt $child);throw 'ADVERSARY_DID_NOT_HOLD'
  } catch { Write-LauncherHold ([string]$_.Exception.Message); exit 2 }
}
if($PSCmdlet.ParameterSetName-ceq'Validate'){try{$bound=Read-Invocation $InvocationPath $ExpectedInvocationSha256;[Console]::Out.WriteLine(('{"result":"PASS_R017_LAUNCHER_INVOCATION_BOUND","execution_correlation_id":"'+$bound.Correlation+'","external_calls":0,"credential_reads":0,"secret_reads":0}'));exit 0}catch{$category=([string]$_.Exception.Message-replace'[^A-Za-z0-9_]','').ToUpperInvariant();if($category.Length-gt64){$category=$category.Substring(0,64)};[Console]::Out.WriteLine(('{"result":"HOLD_R017_LAUNCHER_INVOCATION","category":"'+$category+'","external_calls":0,"credential_reads":0,"secret_reads":0}'));exit 2}}
if(-not$ExecuteProtected){throw 'PROTECTED_EXECUTION_SWITCH_REQUIRED'}

$legacyPassword=$null;$masterPassword=$null;$token=$null
try {
  $bound=Read-Invocation $InvocationPath $ExpectedInvocationSha256
  $script:SafeExecutionCorrelation=$bound.Correlation
  $hostRoot=Find-HostRoot;Add-Type -AssemblyName System.Security
  $legacyBlob=Join-Path $hostRoot 'secrets\local\supabase-project-database-passwords\mazer-password.dpapi';$masterBlob=Join-Path $hostRoot 'secrets\local\supabase-project-database-passwords\website-password.dpapi'
  $nodeShim=Join-Path $hostRoot 'tmp\r017-node-shim-reviewed2';$psqlShim=Join-Path $hostRoot 'tmp\r017-psql-shim-reviewed2';$psqlBin='C:\Program Files\PostgreSQL\17\bin'
  if((Get-Sha256 (Join-Path $nodeShim 'node.exe'))-cne$NodeShimSha-or(Get-Sha256 (Join-Path $psqlShim 'psql.exe'))-cne$PsqlShimSha){throw 'SHIM_DIGEST_DRIFT'}
  $legacyPassword=Read-ProjectPassword $legacyBlob $LegacyRef;$masterPassword=Read-ProjectPassword $masterBlob $MasterRef;$token=Read-ManagementToken
  $legacyText=[Text.Encoding]::UTF8.GetString($legacyPassword);$masterText=[Text.Encoding]::UTF8.GetString($masterPassword)
  $environment=@{SUPABASE_ACCESS_TOKEN=$token;ATLAS_MAZER_LEGACY_DATABASE_URL="postgresql://postgres:$([Uri]::EscapeDataString($legacyText))@db.${LegacyRef}.supabase.co:5432/postgres?sslmode=require";ATLAS_MAZER_MASTER_DATABASE_URL="postgresql://postgres.${MasterRef}:$([Uri]::EscapeDataString($masterText))@aws-0-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require";PATH=$nodeShim+[IO.Path]::PathSeparator+$psqlShim+[IO.Path]::PathSeparator+$psqlBin+[IO.Path]::PathSeparator+$env:PATH}
  $shell=Get-Command pwsh -ErrorAction SilentlyContinue;if($null-eq$shell){$shell=Get-Command powershell -ErrorAction Stop}
  $child=Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-File',$HostScript,'-Mode','Prepare','-PrivateSourcePath',$bound.Source,'-ExpectedPrivateSourceSha256',$bound.SourceSha,'-StatePath',$bound.State,'-ExecuteProtected') $environment 1200000 -TrackProtectedStart
  $receipt=Convert-ProtectedChildReceipt $child
  [Console]::Out.WriteLine(($receipt|ConvertTo-Json -Compress -Depth 10));exit $child.ExitCode
}
catch{Write-LauncherHold ([string]$_.Exception.Message);exit 90}
finally{if($null-ne$legacyPassword){[Array]::Clear($legacyPassword,0,$legacyPassword.Length)};if($null-ne$masterPassword){[Array]::Clear($masterPassword,0,$masterPassword.Length)};$token=$null}
