[CmdletBinding(DefaultParameterSetName = 'Source')]
param(
  [Parameter(Mandatory = $true, ParameterSetName = 'Source')][switch]$SourceOnlyValidate,
  [Parameter(Mandatory = $true, ParameterSetName = 'Probe')][switch]$LocalSentinelProbe,
  [Parameter(Mandatory = $true, ParameterSetName = 'ProductionProbe')][switch]$LocalProductionShapeProbe,
  [Parameter(Mandatory = $true, ParameterSetName = 'HostRace')][switch]$LocalHostReplacementAdversary,
  [Parameter(Mandatory = $true, ParameterSetName = 'Adversary')][ValidateSet('timeout','stderr','malformed','empty_object','wrong_schema','wrong_result','missing_fields','duplicate_key','escaped_key','array','scalar')][string]$LocalTransportAdversary,
  [Parameter(Mandatory = $true, ParameterSetName = 'Validate')][switch]$ValidateInvocationOnly,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][Parameter(Mandatory = $true, ParameterSetName = 'Validate')][Parameter(Mandatory = $true, ParameterSetName = 'ProductionProbe')][string]$InvocationPath,
  [Parameter(Mandatory = $true, ParameterSetName = 'Execute')][Parameter(Mandatory = $true, ParameterSetName = 'Validate')][Parameter(Mandatory = $true, ParameterSetName = 'ProductionProbe')][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedInvocationSha256,
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

function Resolve-DecisionRelative([string]$Value,[string]$Code) {
  if([string]::IsNullOrWhiteSpace($Value)-or[IO.Path]::IsPathRooted($Value)-or$Value.Contains('\')-or@($Value.Split('/')|Where-Object{$_-ceq'..'}).Count-ne0){throw $Code}
  return [IO.Path]::GetFullPath((Join-Path $Root $Value))
}

function Get-CanonicalApprovalInstant([string]$Value,[string]$Code) {
  $parsed=Parse-Rfc3339 $Value $Code
  return $parsed.UtcDateTime.Ticks-($parsed.UtcDateTime.Ticks%10)
}

function Read-SealedJsonSnapshot([string]$Path,[string]$Boundary,[string]$ExpectedSha,[int]$MaxBytes) {
  $resolved=Assert-Under $Path $Boundary;Assert-NoReparse $resolved $Boundary
  $stream=New-Object IO.FileStream($resolved,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$bytes=$null
  try{if($stream.Length-lt2-or$stream.Length-gt$MaxBytes){throw 'SEALED_JSON_SIZE'};$bytes=New-Object byte[] ([int]$stream.Length);$offset=0;while($offset-lt$bytes.Length){$read=$stream.Read($bytes,$offset,$bytes.Length-$offset);if($read-le0){throw 'SEALED_JSON_TRUNCATED'};$offset+=$read};if((Get-BytesSha256 $bytes)-cne$ExpectedSha){throw 'SEALED_JSON_DIGEST'};$text=(New-Object Text.UTF8Encoding($false,$true)).GetString($bytes)}finally{$stream.Dispose();if($null-ne$bytes){[Array]::Clear($bytes,0,$bytes.Length)}}
  try{$value=$text|ConvertFrom-Json}catch{throw 'SEALED_JSON_PARSE'};if($null-eq$value-or$value-is[Array]-or$value-isnot[pscustomobject]){throw 'SEALED_JSON_ROOT'};return $value
}

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
  $expectedKeys = @('schema','packet','decision_request_path','decision_request_sha256','approval_alias_path','approval_alias_sha256','approval_authorization_path','approval_authorization_sha256','approval_consumption_path','approval_consumption_sha256','approval_expires_at','predecessor_state_path','predecessor_state_sha256','execution_correlation_id','private_source_path','private_source_sha256','private_manifest_path','private_manifest_sha256','successor_state_path','host_path','host_sha256','launcher_path','launcher_sha256','terminal_final_identity_edges','terminal_profiles','terminal_player','terminal_ai','terminal_receipts','not_before','issued_at','expires_at')
  $keys = @([regex]::Matches($text, '"((?:\\["\\/bfnrt]|\\u[0-9A-Fa-f]{4}|[^"\\\x00-\x1f])*)"\s*:') | ForEach-Object { try { [string](('"' + $_.Groups[1].Value + '"') | ConvertFrom-Json) } catch { throw 'INVOCATION_KEY_ENCODING' } })
  if ($keys.Count -ne $expectedKeys.Count -or (@($keys | Sort-Object -Unique).Count -ne $keys.Count) -or (($keys | Sort-Object) -join "`n") -cne (($expectedKeys | Sort-Object) -join "`n")) { throw 'INVOCATION_KEYS' }
  try { $value = $text | ConvertFrom-Json } catch { throw 'INVOCATION_JSON' }
  if ($null -eq $value -or $value -is [Array] -or $value -isnot [pscustomobject]) { throw 'INVOCATION_ROOT_OBJECT' }
  $countKeys=@('terminal_final_identity_edges','terminal_profiles','terminal_player','terminal_ai','terminal_receipts')
  foreach ($key in @($expectedKeys | Where-Object { $_ -notin @('approval_expires_at','not_before','issued_at','expires_at') -and $_ -notin $countKeys })) { if ($value.$key -isnot [string]) { throw 'INVOCATION_VALUE_TYPES' } }
  foreach($key in $countKeys){if(($value.$key-isnot[int]-and$value.$key-isnot[long])-or[int64]$value.$key-le0){throw 'INVOCATION_VALUE_TYPES'}}
  if ([string]$value.schema -cne 'atlas.supabase.mazer-master-preparation-launcher-invocation.r017.v3' -or [string]$value.packet -cne $Packet) { throw 'INVOCATION_SCHEMA' }
  foreach($key in @('decision_request_sha256','approval_alias_sha256','approval_authorization_sha256','approval_consumption_sha256','predecessor_state_sha256','private_source_sha256','private_manifest_sha256','host_sha256','launcher_sha256')){if([string]$value.$key-cnotmatch'^[a-f0-9]{64}$'){throw 'SEALED_HASH_BINDING'}}
  if([int]$value.terminal_final_identity_edges-gt$MaxEffectCount){throw 'TERMINAL_DENOMINATORS'}
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
  if ((Split-Path -Parent $source) -cne [IO.Path]::GetFullPath($PacketRoot) -or [IO.Path]::GetFileName($source) -cnotmatch '^private-source(?:-[a-z0-9-]+)?\.json$') { throw 'SEALED_PATH_BINDING' }
  if ([IO.Path]::GetFileName($manifest) -cne 'manifest.json' -or [IO.Path]::GetFileName((Split-Path -Parent $manifest)) -cnotmatch '^materialized-[a-z0-9-]+$') { throw 'SEALED_PATH_BINDING' }
  if ([IO.Path]::GetFileName($predecessor) -cnotmatch '^mazer-master-r017-terminal-rollback-[a-z0-9-]+\.json$') { throw 'PREDECESSOR_PATH_BINDING' }
  $expectedSuccessor = [IO.Path]::GetFullPath((Join-Path $Runtime ('mazer-master-r017-execution-' + [string]$value.execution_correlation_id + '.json')))
  if ($successor -cne $expectedSuccessor -or (Test-Path -LiteralPath $successor)) { throw 'SUCCESSOR_STATE_BINDING' }
  if ($hostPath -cne [IO.Path]::GetFullPath($HostScript) -or $launcherPath -cne [IO.Path]::GetFullPath($PSCommandPath)) { throw 'HOST_PATH_BINDING' }
  foreach ($file in @($source,$manifest,$predecessor,$hostPath,$launcherPath)) { if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw 'SEALED_FILE_MISSING' } }
  Assert-NoReparse $source $PacketRoot; Assert-NoReparse $manifest $PacketRoot; Assert-NoReparse $predecessor $Runtime; Assert-NoReparse $hostPath $PSScriptRoot; Assert-NoReparse $launcherPath $PSScriptRoot
  if ((Get-Sha256 $source) -cne [string]$value.private_source_sha256 -or (Get-Sha256 $manifest) -cne [string]$value.private_manifest_sha256 -or (Get-Sha256 $predecessor) -cne [string]$value.predecessor_state_sha256 -or (Get-Sha256 $hostPath) -cne [string]$value.host_sha256 -or (Get-Sha256 $launcherPath) -cne [string]$value.launcher_sha256) { throw 'SEALED_FILE_DIGEST_DRIFT' }
  try { $prior = Get-Content -LiteralPath $predecessor -Raw | ConvertFrom-Json } catch { throw 'PREDECESSOR_STATE_JSON' }
  if ([string]$prior.schema -cne 'atlas.supabase.mazer-master-preparation-terminal-receipt.r017.v1' -or [string]$prior.packet -cne $Packet -or [string]$prior.result -cne 'HOLD_MAZER_MASTER_PREPARATION_R017' -or [string]$prior.rollback_disposition -cne 'EXACT_ROLLBACK_COMPLETED' -or [string]$prior.execution_correlation_id -cnotmatch '^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$' -or [string]$prior.host_phase -cne 'ROLLED_BACK' -or [string]$prior.fence_phase -cne 'ROLLED_BACK' -or [bool]$prior.watchdog_running -or [int]$prior.provider_writes -ne 0 -or [int]$prior.environment_changes -ne 0 -or [int]$prior.deployments -ne 0 -or [int]$prior.production_changes -ne 0 -or [bool]$prior.raw_records_emitted -or [bool]$prior.pii_emitted -or [bool]$prior.secrets_emitted -or [string]$prior.replay_disposition -cne 'CONSUMED_NON_REPLAYABLE') { throw 'PREDECESSOR_EFFECT_STATE' }
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
  $sealedKeys=@('execution_correlation_id','private_source_path','private_source_sha256','manifest_path','manifest_sha256','auth_apply_sha256','postverify_sha256','host_path','host_sha256','credential_safe_launcher_path','credential_safe_launcher_sha256','packet_merge_commit','jit_invocation_merge_commit','independent_review_checkpoint','prior_rollback_state_path','prior_rollback_receipt_sha256')
  $actualSealedKeys=@($d.sealed_inputs.PSObject.Properties.Name);if($actualSealedKeys.Count-ne$sealedKeys.Count-or(($actualSealedKeys|Sort-Object)-join"`n")-cne(($sealedKeys|Sort-Object)-join"`n")){throw 'DECISION_TUPLE_KEYS'}
  foreach($key in @('private_source_sha256','manifest_sha256','auth_apply_sha256','postverify_sha256','host_sha256','credential_safe_launcher_sha256','prior_rollback_receipt_sha256')){if([string]$d.sealed_inputs.$key-cnotmatch'^[a-f0-9]{64}$'){throw 'DECISION_TUPLE_DIGEST'}}
  if([string]$d.sealed_inputs.packet_merge_commit-cnotmatch'^[a-f0-9]{40}$'-or[string]$d.sealed_inputs.jit_invocation_merge_commit-cnotmatch'^[a-f0-9]{40}$'-or[string]$d.sealed_inputs.independent_review_checkpoint-cnotmatch'^threadctx_[a-f0-9]{64}$'){throw 'DECISION_TUPLE_PROVENANCE'}
  $effectKeys=@('execution_clusters','legacy_writer_fence_and_restore','master_migrations','auth_identity_edges','auth_user_imports','auth_existing_user_binds','auth_same_uuid_retained','profiles','player_rows','ai_rows','receipts','username_backfill_and_origin_contract','vault_key_create_and_rollback_delete','before_user_created_hook_activation','bounded_qa_and_cleanup','rollback_on_any_failed_gate','cutover','vercel_or_app_deployment','production_alias_change');$actualEffectKeys=@($d.effect_ceiling.PSObject.Properties.Name);if($actualEffectKeys.Count-ne$effectKeys.Count-or(($actualEffectKeys|Sort-Object)-join"`n")-cne(($effectKeys|Sort-Object)-join"`n")){throw 'DECISION_EFFECT_KEYS'}
  if([int]$d.effect_ceiling.execution_clusters-ne1-or-not[bool]$d.effect_ceiling.legacy_writer_fence_and_restore-or(@($d.effect_ceiling.master_migrations)-join',')-cne'M1,M2,M3,M4'-or-not[bool]$d.effect_ceiling.username_backfill_and_origin_contract-or-not[bool]$d.effect_ceiling.vault_key_create_and_rollback_delete-or-not[bool]$d.effect_ceiling.before_user_created_hook_activation-or-not[bool]$d.effect_ceiling.bounded_qa_and_cleanup-or-not[bool]$d.effect_ceiling.rollback_on_any_failed_gate-or[bool]$d.effect_ceiling.cutover-or[bool]$d.effect_ceiling.vercel_or_app_deployment-or[bool]$d.effect_ceiling.production_alias_change){throw 'DECISION_EFFECT_CONTRACT'}
  if ([string]$d.sealed_inputs.execution_correlation_id-cne[string]$value.execution_correlation_id-or(Resolve-DecisionRelative ([string]$d.sealed_inputs.private_source_path) 'DECISION_SOURCE_PATH')-cne$source-or[string]$d.sealed_inputs.private_source_sha256-cne[string]$value.private_source_sha256-or(Resolve-DecisionRelative ([string]$d.sealed_inputs.manifest_path) 'DECISION_MANIFEST_PATH')-cne$manifest-or[string]$d.sealed_inputs.manifest_sha256-cne[string]$value.private_manifest_sha256-or(Resolve-DecisionRelative ([string]$d.sealed_inputs.host_path) 'DECISION_HOST_PATH')-cne$hostPath-or[string]$d.sealed_inputs.host_sha256-cne[string]$value.host_sha256-or(Resolve-DecisionRelative ([string]$d.sealed_inputs.credential_safe_launcher_path) 'DECISION_LAUNCHER_PATH')-cne$launcherPath-or[string]$d.sealed_inputs.credential_safe_launcher_sha256-cne[string]$value.launcher_sha256-or(Resolve-DecisionRelative ([string]$d.sealed_inputs.prior_rollback_state_path) 'DECISION_PREDECESSOR_PATH')-cne$predecessor-or[string]$d.sealed_inputs.prior_rollback_receipt_sha256-cne[string]$value.predecessor_state_sha256) { throw 'DECISION_EXECUTION_BINDING' }
  if([int]$d.effect_ceiling.auth_identity_edges-ne[int]$value.terminal_final_identity_edges-or[int]$d.effect_ceiling.profiles-ne[int]$value.terminal_profiles-or[int]$d.effect_ceiling.player_rows-ne[int]$value.terminal_player-or[int]$d.effect_ceiling.ai_rows-ne[int]$value.terminal_ai-or[int]$d.effect_ceiling.receipts-ne[int]$value.terminal_receipts-or[int]$d.effect_ceiling.auth_identity_edges-ne([int]$d.effect_ceiling.auth_user_imports+[int]$d.effect_ceiling.auth_existing_user_binds+[int]$d.effect_ceiling.auth_same_uuid_retained)){throw 'TERMINAL_DENOMINATORS'}
  $aliasExpiryInstant=Get-CanonicalApprovalInstant $aliasExpires 'APPROVAL_TIMESTAMP'
  if ((Get-CanonicalApprovalInstant $envelopeApprovalExpires 'INVOCATION_TIMESTAMP')-ne$aliasExpiryInstant-or(Get-CanonicalApprovalInstant $envelopeExpires 'INVOCATION_TIMESTAMP')-ne$aliasExpiryInstant-or(Get-CanonicalApprovalInstant $decisionExpires 'APPROVAL_TIMESTAMP')-ne$aliasExpiryInstant-or$envelopeNotBefore-cne$consumedRaw) { throw 'INVOCATION_APPROVAL_TIME_BINDING' }
  $issued=Parse-Rfc3339 $envelopeIssued 'INVOCATION_TIMESTAMP';$notBefore=Parse-Rfc3339 $envelopeNotBefore 'INVOCATION_TIMESTAMP';$expires=Parse-Rfc3339 $envelopeExpires 'INVOCATION_TIMESTAMP';$aliasIssued=Parse-Rfc3339 $aliasIssuedRaw 'APPROVAL_TIMESTAMP';$authorized=Parse-Rfc3339 $authorizedRaw 'APPROVAL_TIMESTAMP';$consumed=Parse-Rfc3339 $consumedRaw 'APPROVAL_TIMESTAMP'
  $now=[DateTimeOffset]::UtcNow
  if ($aliasIssued -gt $authorized -or $authorized -gt $consumed -or $consumed -gt $issued -or $issued -gt $now.AddSeconds(5) -or $notBefore -gt $now.AddSeconds(5)) { throw 'INVOCATION_NOT_YET_VALID' }
  if ($expires -le $now -or $issued -ge $expires -or $expires -gt $aliasIssued.AddHours(24)) { throw 'INVOCATION_EXPIRED' }
  $sourceContract=Read-SealedJsonSnapshot $source $PacketRoot ([string]$value.private_source_sha256) 32000000;$manifestContract=Read-SealedJsonSnapshot $manifest $PacketRoot ([string]$value.private_manifest_sha256) 262144
  if([string]$sourceContract.schema-cne'atlas.supabase.mazer-master-preparation-private-source.r017.v1'-or[string]$sourceContract.packet-cne$Packet-or[string]$sourceContract.sql_sha256.'auth-apply.sql'-cne[string]$d.sealed_inputs.auth_apply_sha256-or[string]$sourceContract.sql_sha256.'postverify.sql'-cne[string]$d.sealed_inputs.postverify_sha256){throw 'SOURCE_CONTRACT'}
  if([string]$manifestContract.schema-cne'atlas.supabase.mazer-master-preparation-private-manifest.r017.v1'-or[string]$manifestContract.packet-cne$Packet-or[int]$manifestContract.auth_counts.final_edges-ne[int]$value.terminal_final_identity_edges-or[int]$manifestContract.auth_counts.imports-ne[int]$d.effect_ceiling.auth_user_imports-or[int]$manifestContract.auth_counts.binds-ne[int]$d.effect_ceiling.auth_existing_user_binds-or[int]$manifestContract.auth_counts.retained_edges-ne[int]$d.effect_ceiling.auth_same_uuid_retained-or[int]$manifestContract.app_counts.profiles-ne[int]$value.terminal_profiles-or[int]$manifestContract.app_counts.player-ne[int]$value.terminal_player-or[int]$manifestContract.app_counts.ai-ne[int]$value.terminal_ai-or[int]$manifestContract.app_counts.receipts-ne[int]$value.terminal_receipts-or[int]$manifestContract.receipt_conservation.final-ne[int]$value.terminal_receipts){throw 'MANIFEST_CONTRACT'}
  return [pscustomobject]@{ Source=$source; SourceSha=[string]$value.private_source_sha256; HostSha=[string]$value.host_sha256; State=$successor; Correlation=[string]$value.execution_correlation_id; Counts=[pscustomobject]@{final_identity_edges=[int]$value.terminal_final_identity_edges;profiles=[int]$value.terminal_profiles;player=[int]$value.terminal_player;ai=[int]$value.terminal_ai;receipts=[int]$value.terminal_receipts} }
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

function Get-VerifiedHostBootstrapEncoded {
  $bootstrap=@'
$ErrorActionPreference='Stop';$p=[IO.Path]::GetFullPath($env:ATLAS_R017_VERIFIED_HOST_PATH);$s=New-Object IO.FileStream($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$b=$null
try{if($s.Length-lt2-or$s.Length-gt2097152){exit 81};$b=New-Object byte[] ([int]$s.Length);$o=0;while($o-lt$b.Length){$r=$s.Read($b,$o,$b.Length-$o);if($r-le0){exit 82};$o+=$r};$h=[Security.Cryptography.SHA256]::Create();try{$a=([BitConverter]::ToString($h.ComputeHash($b))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()};if($a-cne$env:ATLAS_R017_VERIFIED_HOST_SHA256){exit 83};$t=(New-Object Text.UTF8Encoding($false,$true)).GetString($b)}finally{$s.Dispose();if($null-ne$b){[Array]::Clear($b,0,$b.Length)}}
$global:ATLAS_R017_VERIFIED_HOST_SOURCE_TEXT=$t;if($env:ATLAS_R017_VERIFIED_MODE-ceq'Synthetic'-and-not[string]::IsNullOrWhiteSpace($env:ATLAS_R017_VERIFIED_TEST_REPLACEMENT_PATH)){[IO.File]::Copy($env:ATLAS_R017_VERIFIED_TEST_REPLACEMENT_PATH,$p,$true)};$sb=[ScriptBlock]::Create($t)
if($env:ATLAS_R017_VERIFIED_MODE-ceq'Source'){. $sb -SourceOnlyValidate}elseif($env:ATLAS_R017_VERIFIED_MODE-ceq'Execute'){. $sb -Mode $env:ATLAS_R017_CHILD_MODE -PrivateSourcePath $env:ATLAS_R017_CHILD_SOURCE -ExpectedPrivateSourceSha256 $env:ATLAS_R017_CHILD_SOURCE_SHA -StatePath $env:ATLAS_R017_CHILD_STATE -ExecuteProtected}else{. $sb};exit $LASTEXITCODE
'@
  return [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($bootstrap))
}

function Invoke-VerifiedHostChild([string]$SourcePath,[string]$ExpectedSha,[string]$VerifiedMode,[string]$ChildMode,[string]$ChildSource,[string]$ChildSourceSha,[string]$ChildState,[Collections.IDictionary]$Environment,[int]$TimeoutMs,[switch]$TrackProtectedStart,[string]$TestReplacementPath) {
  $shell=Get-Command pwsh -ErrorAction SilentlyContinue;if($null-eq$shell){$shell=Get-Command powershell -ErrorAction Stop};$childEnvironment=@{};foreach($key in $Environment.Keys){$childEnvironment[[string]$key]=[string]$Environment[$key]}
  $childEnvironment.ATLAS_R017_VERIFIED_HOST_PATH=[IO.Path]::GetFullPath($SourcePath);$childEnvironment.ATLAS_R017_VERIFIED_HOST_SHA256=$ExpectedSha;$childEnvironment.ATLAS_R017_VERIFIED_HOST_DIR=[IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($SourcePath));$childEnvironment.ATLAS_R017_VERIFIED_MODE=$VerifiedMode;$childEnvironment.ATLAS_R017_CHILD_MODE=$ChildMode;$childEnvironment.ATLAS_R017_CHILD_SOURCE=$ChildSource;$childEnvironment.ATLAS_R017_CHILD_SOURCE_SHA=$ChildSourceSha;$childEnvironment.ATLAS_R017_CHILD_STATE=$ChildState;$childEnvironment.ATLAS_R017_VERIFIED_TEST_REPLACEMENT_PATH=if($VerifiedMode-ceq'Synthetic'){$TestReplacementPath}else{''}
  return Invoke-Child $shell.Source @('-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',(Get-VerifiedHostBootstrapEncoded)) $childEnvironment $TimeoutMs -TrackProtectedStart:$TrackProtectedStart
}

function Convert-ProtectedChildReceipt([object]$Child,[object]$ExpectedCounts) {
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
    if($null-eq$ExpectedCounts-or$receipt.phase-cne'PREPARATION_COMPLETE'-or-not[bool]$receipt.master_hook_enabled-or-not[bool]$receipt.legacy_signup_and_acl_restored-or-not[bool]$receipt.fresh_dual_refence_and_catchup_required_for_cutover-or[int]$receipt.final_identity_edges-ne[int]$ExpectedCounts.final_identity_edges-or[int]$receipt.profiles-ne[int]$ExpectedCounts.profiles-or[int]$receipt.player-ne[int]$ExpectedCounts.player-or[int]$receipt.ai-ne[int]$ExpectedCounts.ai-or[int]$receipt.receipts-ne[int]$ExpectedCounts.receipts){throw 'CHILD_RECEIPT_VALUES'}
  }else{
    if($receipt.category-isnot[string]-or$receipt.rollback_disposition-isnot[string]){throw 'CHILD_RECEIPT_TYPES'}
    if($receipt.category-cnotmatch'^[A-Z0-9_]{1,96}$'-or$receipt.rollback_disposition-notin@('NO_EFFECT_CONFIRMED','EXACT_ROLLBACK_COMPLETED','ROLLBACK_FAILED')){throw 'CHILD_RECEIPT_VALUES'}
  }
  return $receipt
}

function Write-LauncherHold([string]$Category) {
  $allowed=@('CHILD_TIMEOUT','CHILD_STDERR','CHILD_RECEIPT_JSON','CHILD_RECEIPT_SHAPE','CHILD_RECEIPT_KEYS','CHILD_RECEIPT_SCHEMA','CHILD_RECEIPT_RESULT','CHILD_RECEIPT_TYPES','CHILD_RECEIPT_VALUES','CHILD_DISCLOSURE','HOST_VERIFIED_BOOTSTRAP_SIZE','HOST_VERIFIED_BOOTSTRAP_TRUNCATED','HOST_VERIFIED_BOOTSTRAP_DIGEST','HOST_VERIFIED_SOURCE_EXIT','HOST_VERIFIED_SOURCE_STDERR','HOST_VERIFIED_SOURCE_OUTPUT')
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
if($PSCmdlet.ParameterSetName-ceq'ProductionProbe'){try{$bound=Read-Invocation $InvocationPath $ExpectedInvocationSha256;$script:SafeExecutionCorrelation=$bound.Correlation;$hostProbe=Invoke-VerifiedHostChild $HostScript (Get-Sha256 $HostScript) 'Source' '' '' '' '' @{} 120000;if(-not[string]::IsNullOrEmpty($hostProbe.Stderr)){throw 'HOST_VERIFIED_SOURCE_STDERR'};if($hostProbe.ExitCode-ne0){$exitCategory=switch([int]$hostProbe.ExitCode){81{'HOST_VERIFIED_BOOTSTRAP_SIZE'}82{'HOST_VERIFIED_BOOTSTRAP_TRUNCATED'}83{'HOST_VERIFIED_BOOTSTRAP_DIGEST'}default{'HOST_VERIFIED_SOURCE_EXIT'}};throw $exitCategory};if($hostProbe.Stdout-notmatch'PASS_MAZER_MASTER_PREPARATION_R017_SOURCE'){throw 'HOST_VERIFIED_SOURCE_OUTPUT'};$probe=Invoke-SentinelProbe;if($probe.ExitCode-ne0-or-not[string]::IsNullOrEmpty($probe.Stderr)-or$probe.Stdout-notmatch'PASS_R017_CREDENTIAL_SAFE_ENV_SENTINEL'){throw 'SENTINEL_PROBE'};[Console]::Out.WriteLine(('{"result":"PASS_R017_CREDENTIAL_SAFE_PRODUCTION_SHAPE_SENTINEL","execution_correlation_id":"'+$bound.Correlation+'","external_calls":0,"credential_reads":0,"secret_reads":0}'));exit 0}catch{Write-LauncherHold ([string]$_.Exception.Message);exit 2}}
if($PSCmdlet.ParameterSetName-ceq'HostRace'){$id=[guid]::NewGuid().ToString().ToLowerInvariant();$synthetic=Join-Path $PacketRoot ('host-race-source-'+$id+'.ps1');$replacement=Join-Path $PacketRoot ('host-race-replacement-'+$id+'.ps1');try{[IO.File]::WriteAllText($synthetic,'[Console]::Out.Write("R017_ORIGINAL_HOST_BYTES")',(New-Object Text.UTF8Encoding($false)));[IO.File]::WriteAllText($replacement,'[Console]::Out.Write("R017_REPLACEMENT_MUST_NOT_RUN")',(New-Object Text.UTF8Encoding($false)));$probe=Invoke-VerifiedHostChild $synthetic (Get-Sha256 $synthetic) 'Synthetic' '' '' '' '' @{} 30000 -TestReplacementPath $replacement;if($probe.ExitCode-ne0-or-not[string]::IsNullOrEmpty($probe.Stderr)-or[string]$probe.Stdout.Trim()-cne'R017_ORIGINAL_HOST_BYTES'-or(Get-Content -Raw -LiteralPath $synthetic)-notmatch'REPLACEMENT_MUST_NOT_RUN'){throw 'HOST_REPLACEMENT_RACE'};[Console]::Out.WriteLine('{"result":"PASS_R017_SAME_BUFFER_HOST_REPLACEMENT_ADVERSARY","replacement_executed":false,"credential_reads":0,"external_calls":0}');exit 0}catch{Write-LauncherHold ([string]$_.Exception.Message);exit 2}finally{foreach($file in @($synthetic,$replacement)){if(Test-Path -LiteralPath $file){Remove-Item -LiteralPath $file -Force}}}}
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
    [void](Convert-ProtectedChildReceipt $child ([pscustomobject]@{final_identity_edges=20;profiles=13;player=17;ai=17;receipts=1887}));throw 'ADVERSARY_DID_NOT_HOLD'
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
  $child=Invoke-VerifiedHostChild $HostScript ([string]$bound.HostSha) 'Execute' 'Prepare' $bound.Source $bound.SourceSha $bound.State $environment 1200000 -TrackProtectedStart
  $receipt=Convert-ProtectedChildReceipt $child $bound.Counts
  [Console]::Out.WriteLine(($receipt|ConvertTo-Json -Compress -Depth 10));exit $child.ExitCode
}
catch{Write-LauncherHold ([string]$_.Exception.Message);exit 90}
finally{if($null-ne$legacyPassword){[Array]::Clear($legacyPassword,0,$legacyPassword.Length)};if($null-ne$masterPassword){[Array]::Clear($masterPassword,0,$masterPassword.Length)};$token=$null}
