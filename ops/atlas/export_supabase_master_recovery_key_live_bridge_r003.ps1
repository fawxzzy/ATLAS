[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('SealSynthetic', 'VerifySynthetic', 'VerifyHostCoreSynthetic',
    'VerifyHostPersistenceSynthetic', 'VerifyFileAclSynthetic',
    'VerifyPathIdentitySynthetic', 'SealLive')]
  [string]$Action,

  [Parameter(Mandatory = $true)]
  [string]$FixtureRoot,

  [Parameter(Mandatory = $true)]
  [string]$AttemptId,

  [Parameter(Mandatory = $true)]
  [string]$ProjectRef,

  [Parameter(Mandatory = $true)]
  [string]$DescriptorSha256,

  [Parameter(Mandatory = $true)]
  [string]$ArchiveSha256,

  [switch]$WrongCode,

  [switch]$WrongKey,

  [switch]$TamperCoreContext
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# This source packet cannot execute a live action. The live key-binding and
# sealing primitives below are source for later ACTION review. SealLive refuses
# before marker or vault access; source integration does not admit a live action.
# Synthetic actions use fixed public vectors; no file supplies key or code.
$domain = 'ATLAS|Supabase|MasterArchiveKeyCapsule|v1'
$capsuleSchema = 'atlas.supabase.master-archive-key-capsule.v1'
$dpapiEntropy = [System.Text.Encoding]::UTF8.GetBytes('ATLAS|Supabase|OffsiteArchiveRecovery|v1')

function Get-Sha256Hex {
  param([byte[]]$Bytes)
  return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Assert-NoReparsePoint {
  param([string]$Path)
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Synthetic fixture path contains a reparse point.'
  }
}

function New-PrivatePathGuard {
  param([string]$Directory)
  if (-not ('AtlasMasterKeyPathGuardR003' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
public sealed class AtlasMasterKeyPathGuardR003 : IDisposable {
  [StructLayout(LayoutKind.Sequential)] struct ByHandleInfo {
    public uint Attributes;
    public System.Runtime.InteropServices.ComTypes.FILETIME Created, Accessed, Written;
    public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
  }
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern SafeFileHandle CreateFileW(string path, uint access, uint share,
    IntPtr security, uint creation, uint flags, IntPtr template);
  [DllImport("kernel32.dll", SetLastError=true)]
  static extern bool GetFileInformationByHandle(SafeFileHandle handle, out ByHandleInfo info);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern uint GetFinalPathNameByHandleW(SafeFileHandle handle,
    StringBuilder path, uint length, uint flags);
  readonly List<Tuple<SafeFileHandle,string>> parents = new List<Tuple<SafeFileHandle,string>>();
  readonly List<Tuple<FileStream,string>> pinnedFiles = new List<Tuple<FileStream,string>>();
  const uint ReadAttributes = 0x80, ReadControl = 0x20000, GenericRead = 0x80000000;
  const uint ShareRead = 1, OpenExisting = 3, BackupSemantics = 0x02000000;
  const uint OpenReparsePoint = 0x00200000;
  static string Identity(SafeFileHandle handle, string expected, bool directory) {
    if (handle == null || handle.IsInvalid ||
        !GetFileInformationByHandle(handle, out ByHandleInfo info) ||
        (info.Attributes & 0x400) != 0 ||
        ((info.Attributes & 0x10) != 0) != directory ||
        (!directory && info.Links != 1))
      throw new IOException("PRIVATE_PATH_IDENTITY_UNPROVEN");
    StringBuilder path = new StringBuilder(32768);
    uint length = GetFinalPathNameByHandleW(handle, path, (uint)path.Capacity, 0);
    if (length == 0 || length >= path.Capacity)
      throw new IOException("PRIVATE_PATH_IDENTITY_UNPROVEN");
    string actual = path.ToString();
    if (actual.StartsWith(@"\\?\", StringComparison.Ordinal)) actual = actual.Substring(4);
    if (!String.Equals(actual.TrimEnd('\\'), expected.TrimEnd('\\'),
                       StringComparison.OrdinalIgnoreCase))
      throw new IOException("PRIVATE_PATH_IDENTITY_DRIFT");
    return info.Volume.ToString("X8") + ":" + info.IndexHigh.ToString("X8") +
      ":" + info.IndexLow.ToString("X8");
  }
  void BindParent(string path) {
    SafeFileHandle handle = CreateFileW(path, ReadAttributes, ShareRead,
      IntPtr.Zero, OpenExisting, BackupSemantics | OpenReparsePoint, IntPtr.Zero);
    try {
      Identity(handle, path, true);
      parents.Add(Tuple.Create(handle, path));
    } catch { handle.Dispose(); throw; }
  }
  public static AtlasMasterKeyPathGuardR003 Open(string directory) {
    string full = Path.GetFullPath(directory).TrimEnd('\\');
    string root = Path.GetPathRoot(full);
    if (root == null || root.Length != 3 || root[1] != ':' ||
        !String.Equals(full, directory.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
      throw new IOException("PRIVATE_PATH_SCOPE_INVALID");
    AtlasMasterKeyPathGuardR003 guard = new AtlasMasterKeyPathGuardR003();
    try {
      guard.BindParent(root);
      string current = root;
      foreach (string part in full.Substring(root.Length).Split('\\')) {
        if (part.Length == 0 || part.EndsWith(".", StringComparison.Ordinal) ||
            part.EndsWith(" ", StringComparison.Ordinal) || part.IndexOf(':') >= 0)
          throw new IOException("PRIVATE_PATH_SCOPE_INVALID");
        current = Path.Combine(current, part);
        guard.BindParent(current);
      }
      return guard;
    } catch { guard.Dispose(); throw; }
  }
  public void AssertParents() {
    foreach (Tuple<SafeFileHandle,string> parent in parents)
      Identity(parent.Item1, parent.Item2, true);
  }
  public void AssertPinnedFiles() {
    AssertParents();
    foreach (Tuple<FileStream,string> file in pinnedFiles)
      Identity(file.Item1.SafeFileHandle, file.Item2, false);
  }
  public string CaptureOpenFile(SafeFileHandle handle, string expected) {
    AssertParents();
    return Identity(handle, expected, false);
  }
  public FileStream PinClosedFile(string path, string expectedIdentity) {
    AssertParents();
    // Exclusive reopen rejects an existing writer and prevents later writes,
    // replacement or deletion until the exact postimage has been checked.
    SafeFileHandle handle = CreateFileW(path, GenericRead | ReadControl | ReadAttributes,
      0, IntPtr.Zero, OpenExisting, OpenReparsePoint, IntPtr.Zero);
    try {
      string actualIdentity = Identity(handle, path, false);
      if (!String.Equals(actualIdentity, expectedIdentity, StringComparison.Ordinal))
        throw new IOException("PRIVATE_PATH_FILE_REPLACED");
      FileStream stream = new FileStream(handle, FileAccess.Read);
      pinnedFiles.Add(Tuple.Create(stream, path));
      return stream;
    } catch { handle.Dispose(); throw; }
  }
  public void Dispose() {
    for (int i = pinnedFiles.Count - 1; i >= 0; i--) pinnedFiles[i].Item1.Dispose();
    for (int i = parents.Count - 1; i >= 0; i--) parents[i].Item1.Dispose();
  }
}
'@
  }
  return [AtlasMasterKeyPathGuardR003]::Open($Directory)
}

function Assert-HexDigest {
  param([string]$Value)
  if ($Value -cnotmatch '^[0-9a-f]{64}$') {
    throw 'Expected a lowercase SHA-256 digest.'
  }
}

function Assert-ExactKeys {
  param([System.Collections.IDictionary]$Value, [string[]]$Expected)
  $actual = @($Value.Keys | Sort-Object)
  if (Compare-Object -ReferenceObject @($Expected | Sort-Object) -DifferenceObject $actual) {
    throw 'Capsule shape drift.'
  }
}

function Confirm-OfflineCodeHandoff {
  param([byte[]]$Code, [switch]$Interactive)
  if (-not $Interactive) { throw 'PRIVATE_HANDOFF_INTERACTIVE_OPT_IN_REQUIRED' }
  if ($null -eq $Code -or $Code.Length -ne 32) { throw 'RECOVERY_CODE_SHAPE_REJECTED' }
  # This source-library call is not an ACTION authority boundary. The future
  # installed wrapper must admit the action and pin both complete source files.
  $handoffPath = Join-Path $PSScriptRoot 'private_recovery_code_handoff_r001.ps1'
  Assert-NoReparsePoint $handoffPath
  if (-not [System.IO.File]::Exists($handoffPath)) { throw 'PRIVATE_HANDOFF_SOURCE_REQUIRED' }
  $handoffStream = [System.IO.File]::Open($handoffPath,
    [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::Read)
  try {
    if ($handoffStream.Length -le 0 -or $handoffStream.Length -gt 65536) {
      throw 'PRIVATE_HANDOFF_SOURCE_IDENTITY_REJECTED'
    }
    [byte[]]$handoffBytes = [byte[]]::new([int]$handoffStream.Length)
    $offset = 0
    while ($offset -lt $handoffBytes.Length) {
      $count = $handoffStream.Read($handoffBytes, $offset, $handoffBytes.Length - $offset)
      if ($count -le 0) { throw 'PRIVATE_HANDOFF_SOURCE_IDENTITY_REJECTED' }
      $offset += $count
    }
    if ($handoffStream.ReadByte() -ne -1) { throw 'PRIVATE_HANDOFF_SOURCE_IDENTITY_REJECTED' }
  } finally { $handoffStream.Dispose() }
  if ((Get-Sha256Hex $handoffBytes) -cne '42fb3478f11d5b805e662b760ad0a9c869abd0307e9b96fbbce073d17286fd38') {
    throw 'PRIVATE_HANDOFF_SOURCE_IDENTITY_REJECTED'
  }
  # Hash and execute the same public source bytes; do not reopen the path.
  . ([scriptblock]::Create([System.Text.Encoding]::UTF8.GetString($handoffBytes)))
  $confirmed = @(Invoke-PrivateRecoveryCodeHandoff -RecoveryCode $Code -Interactive)
  if ($confirmed.Count -ne 1 -or $confirmed[0] -isnot [bool] -or -not $confirmed[0]) {
    throw 'PRIVATE_USER_ONLY_HANDOFF_NOT_CONFIRMED'
  }
}

function Seal-HostBoundKey {
  param([byte[]]$ArchiveKey, [byte[]]$RecoveryCode,
        [System.Collections.IDictionary]$Context)
  if ($ArchiveKey.Length -ne 32 -or $RecoveryCode.Length -ne 32) {
    throw 'Live key or recovery code shape drift.'
  }
  Assert-ExactKeys $Context @('domain', 'attempt_id', 'project_ref',
    'descriptor_sha256', 'archive_sha256')
  if ($Context.domain -cne $domain) { throw 'Live capsule domain drift.' }
  if ($Context.attempt_id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]{3,79}$' -or
      $Context.project_ref -cnotmatch '^[a-z0-9]{8,32}$') {
    throw 'Live capsule identity drift.'
  }
  Assert-HexDigest $Context.descriptor_sha256
  Assert-HexDigest $Context.archive_sha256
  $contextSnapshot = [ordered]@{
    domain = [string]$Context.domain
    attempt_id = [string]$Context.attempt_id
    project_ref = [string]$Context.project_ref
    descriptor_sha256 = [string]$Context.descriptor_sha256
    archive_sha256 = [string]$Context.archive_sha256
  }
  $associatedData = [System.Text.Encoding]::UTF8.GetBytes(
    ($contextSnapshot | ConvertTo-Json -Compress -Depth 4))
  $nonceBytes = [byte[]]::new(12)
  $tagBytes = [byte[]]::new(16)
  $wrappedBytes = [byte[]]::new(32)
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($nonceBytes)
  $aes = [System.Security.Cryptography.AesGcm]::new($RecoveryCode, 16)
  try {
    $aes.Encrypt($nonceBytes, $ArchiveKey, $wrappedBytes, $tagBytes,
      $associatedData)
    $capsule = [ordered]@{
      schema = $capsuleSchema
      algorithm = 'AES-256-GCM'
      context = $contextSnapshot
      nonce_b64 = [Convert]::ToBase64String($nonceBytes)
      tag_b64 = [Convert]::ToBase64String($tagBytes)
      wrapped_key_b64 = [Convert]::ToBase64String($wrappedBytes)
    }
    return ($capsule | ConvertTo-Json -Compress -Depth 6)
  } finally {
    $aes.Dispose()
    [System.Array]::Clear($associatedData, 0, $associatedData.Length)
    [System.Array]::Clear($wrappedBytes, 0, $wrappedBytes.Length)
  }
}

function Assert-PrivateCapsuleDirectory {
  # A later ACTION wrapper must first prove the installed source path and
  # current writer grant. This check is a local defense, not that authority.
  $atlasRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
  $vault = Join-Path $atlasRoot 'secrets\local\supabase-offsite-recovery'
  $capsules = Join-Path $vault 'capsules'
  foreach ($path in @($atlasRoot, (Join-Path $atlasRoot 'secrets'),
      (Join-Path $atlasRoot 'secrets\local'), $vault, $capsules)) {
    Assert-NoReparsePoint $path
  }
  if (-not (Test-Path -LiteralPath $capsules -PathType Container)) {
    throw 'Private capsule directory is missing.'
  }
  $acl = Get-Acl -LiteralPath $capsules
  if (-not $acl.AreAccessRulesProtected) {
    throw 'Private capsule ACL inheritance is enabled.'
  }
  $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate(
      [System.Security.Principal.SecurityIdentifier]).Value
    if ($rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
        $sid -notin @($currentSid, 'S-1-5-18')) {
      throw 'Private capsule ACL contains an unexpected principal or rule.'
    }
  }
  return $capsules
}

function Assert-PrivateFileAcl {
  param([string]$Path, [System.IO.FileStream]$Stream = $null)
  Assert-NoReparsePoint $Path
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw 'Private capsule file is missing.'
  }
  $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  if ($null -ne $Stream) {
    # Bind the creation/write check to the opened file, not a second path open.
    $acl = [System.IO.FileSystemAclExtensions]::GetAccessControl($Stream)
  } else {
    $acl = Get-Acl -LiteralPath $Path
  }
  $ownerSid = $acl.GetOwner(
    [System.Security.Principal.SecurityIdentifier]).Value
  if ($ownerSid -cne $currentSid -or -not $acl.AreAccessRulesProtected) {
    throw 'Private capsule file owner or DACL protection drift.'
  }
  $rules = @($acl.GetAccessRules($true, $true,
    [System.Security.Principal.SecurityIdentifier]))
  $currentFullControl = $false
  if ($rules.Count -eq 0) { throw 'Private capsule file has no access rules.' }
  foreach ($rule in $rules) {
    $sid = $rule.IdentityReference.Value
    if ($rule.IsInherited -or
        $rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
        $sid -notin @($currentSid, 'S-1-5-18') -or
        $rule.InheritanceFlags -ne [System.Security.AccessControl.InheritanceFlags]::None -or
        $rule.PropagationFlags -ne [System.Security.AccessControl.PropagationFlags]::None) {
      throw 'Private capsule file ACL contains an unexpected rule.'
    }
    if ($sid -ceq $currentSid -and
        ($rule.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -eq
          [System.Security.AccessControl.FileSystemRights]::FullControl) {
      $currentFullControl = $true
    }
  }
  if (-not $currentFullControl) {
    throw 'Private capsule file owner lacks full control.'
  }
}

function Assert-PinnedFileContent {
  param([System.IO.FileStream]$Stream, [string]$ExpectedSha256,
        [int]$ExpectedLength)
  Assert-HexDigest $ExpectedSha256
  if ($ExpectedLength -lt 1 -or $ExpectedLength -gt 1048576 -or
      $Stream.Length -ne $ExpectedLength) {
    throw 'Private file length drift.'
  }
  $Stream.Position = 0
  $actual = [Convert]::ToHexString(
    [System.Security.Cryptography.SHA256]::HashData($Stream)).ToLowerInvariant()
  $Stream.Position = 0
  if ($actual -cne $ExpectedSha256) {
    throw 'Private file content drift.'
  }
}

function New-PrivateFileStream {
  param([string]$Path, [object]$Guard)
  # FileSystemAclExtensions.Create applies the protected DACL at CreateNew;
  # applying Set-Acl after File.Open would leave an inherited-permission window.
  $parent = [System.IO.Path]::GetDirectoryName(
    [System.IO.Path]::GetFullPath($Path))
  $Guard.AssertParents()
  Assert-NoReparsePoint $parent
  if (Test-Path -LiteralPath $Path) {
    throw 'Private capsule file already exists; no retry.'
  }
  $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
  $systemSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
  $security = [System.Security.AccessControl.FileSecurity]::new()
  $security.SetAccessRuleProtection($true, $false)
  $security.SetOwner($currentSid)
  foreach ($sid in @($currentSid, $systemSid)) {
    $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
      $sid, [System.Security.AccessControl.FileSystemRights]::FullControl,
      [System.Security.AccessControl.AccessControlType]::Allow)
    $security.AddAccessRule($rule)
  }
  $file = [System.IO.FileInfo]::new($Path)
  $stream = [System.IO.FileSystemAclExtensions]::Create(
    $file, [System.IO.FileMode]::CreateNew,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    [System.IO.FileShare]::None, 4096,
    [System.IO.FileOptions]::WriteThrough, $security)
  try {
    Assert-PrivateFileAcl -Path $Path -Stream $stream
    $identity = $Guard.CaptureOpenFile($stream.SafeFileHandle, $Path)
    return @{ stream = $stream; identity = $identity }
  } catch {
    $stream.Dispose()
    # Preserve the one-use path after an uncertain ACL result; no retry or
    # cleanup can silently replace a file that may have been visible.
    throw
  }
}

function New-OneUseLiveMarker {
  param([string]$CapsuleDirectory, [System.Collections.IDictionary]$Context,
        [object]$Guard)
  Assert-ExactKeys $Context @('domain', 'attempt_id', 'project_ref',
    'descriptor_sha256', 'archive_sha256')
  if ($Context.attempt_id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]{3,79}$') {
    throw 'Live attempt identity drift.'
  }
  $markerPath = Join-Path $CapsuleDirectory ($Context.attempt_id + '.attempt.json')
  $capsulePath = Join-Path $CapsuleDirectory ($Context.attempt_id + '.capsule.json')
  if ((Test-Path -LiteralPath $markerPath) -or
      (Test-Path -LiteralPath $capsulePath)) {
    throw 'Live attempt already exists; no retry.'
  }
  $marker = [ordered]@{
    schema = 'atlas.supabase.master-archive-key-live-attempt.v1'
    state = 'IN_PROGRESS_NO_RETRY'
    context = $Context
  }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes(
    ($marker | ConvertTo-Json -Compress -Depth 6) + "`n")
  $markerDigest = Get-Sha256Hex $bytes
  $markerLength = $bytes.Length
  $stream = $null
  $identity = $null
  try {
    $opened = New-PrivateFileStream -Path $markerPath -Guard $Guard
    $stream = $opened.stream
    $identity = $opened.identity
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush($true)
    $Guard.AssertPinnedFiles()
    Assert-PrivateFileAcl -Path $markerPath -Stream $stream
  } finally {
    if ($null -ne $stream) { $stream.Dispose() }
    [System.Array]::Clear($bytes, 0, $bytes.Length)
  }
  # Reopen the exact created file and pin it without delete sharing. A path
  # replacement between close and reopen is detected by volume/file index.
  $readback = $Guard.PinClosedFile($markerPath, $identity)
  $Guard.AssertPinnedFiles()
  Assert-PrivateFileAcl -Path $markerPath -Stream $readback
  Assert-PinnedFileContent -Stream $readback -ExpectedSha256 $markerDigest `
    -ExpectedLength $markerLength
  return @{ marker_path = $markerPath; capsule_path = $capsulePath;
    marker_readback = $readback; marker_sha256 = $markerDigest }
}

function Write-NewLiveCapsule {
  param([string]$CapsulePath, [string]$SerializedCapsule,
        [object]$Guard)
  # CreateNew and the preserved attempt marker prevent implicit overwrite or
  # retry. The ACTION wrapper must reconcile a failed or uncertain write.
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($SerializedCapsule + "`n")
  $capsuleDigest = Get-Sha256Hex $bytes
  $capsuleLength = $bytes.Length
  $stream = $null
  $identity = $null
  try {
    $opened = New-PrivateFileStream -Path $CapsulePath -Guard $Guard
    $stream = $opened.stream
    $identity = $opened.identity
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush($true)
    $Guard.AssertPinnedFiles()
    Assert-PrivateFileAcl -Path $CapsulePath -Stream $stream
  } finally {
    if ($null -ne $stream) { $stream.Dispose() }
    [System.Array]::Clear($bytes, 0, $bytes.Length)
  }
  $readback = $Guard.PinClosedFile($CapsulePath, $identity)
  $Guard.AssertPinnedFiles()
  Assert-PrivateFileAcl -Path $CapsulePath -Stream $readback
  Assert-PinnedFileContent -Stream $readback -ExpectedSha256 $capsuleDigest `
    -ExpectedLength $capsuleLength
  return @{ capsule_sha256 = $capsuleDigest; capsule_bytes = $capsuleLength;
    capsule_readback = $readback }
}

function Invoke-HostBoundLiveBridge {
  param([string]$Attempt, [string]$Project, [string]$DescriptorDigest,
        [string]$ArchiveDigest)
  # This routine is dormant in the source packet. Dot-sourcing the script can
  # expose functions; it is not an authority boundary. A separately reviewed
  # installed wrapper must prove exact ACTION grant and source identity first.
  Assert-HexDigest $DescriptorDigest
  Assert-HexDigest $ArchiveDigest
  if ($Project -cnotmatch '^[a-z0-9]{8,32}$') { throw 'Project identity drift.' }
  $context = [ordered]@{
    domain = $domain
    attempt_id = $Attempt
    project_ref = $Project
    descriptor_sha256 = $DescriptorDigest
    archive_sha256 = $ArchiveDigest
  }
  $atlasRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
  $expectedDirectory = Join-Path $atlasRoot 'secrets\local\supabase-offsite-recovery\capsules'
  $guard = New-PrivatePathGuard $expectedDirectory
  $codeBytes = $null
  $keyBytes = $null
  $descriptorRaw = $null
  $protectedBytes = $null
  try {
    $directory = Assert-PrivateCapsuleDirectory
    if ($directory -cne $expectedDirectory) {
      throw 'Private capsule directory identity drift.'
    }
    $paths = New-OneUseLiveMarker -CapsuleDirectory $directory -Context $context -Guard $guard
    $codeBytes = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($codeBytes)
    Confirm-OfflineCodeHandoff -Code $codeBytes -Interactive
    $vault = Join-Path $atlasRoot 'secrets\local\supabase-offsite-recovery'
    $blobPath = Join-Path $vault 'archive-master-key.dpapi'
    $descriptorPath = Join-Path $vault 'archive-master-key.descriptor.json'
    foreach ($path in @($atlasRoot, (Join-Path $atlasRoot 'secrets'),
        (Join-Path $atlasRoot 'secrets\local'), $vault, $blobPath,
        $descriptorPath)) {
      Assert-NoReparsePoint $path
    }
    $descriptorRaw = [System.IO.File]::ReadAllBytes($descriptorPath)
    if ((Get-Sha256Hex $descriptorRaw) -cne $DescriptorDigest) {
      throw 'Protected descriptor preimage drift.'
    }
    $descriptor = [System.Text.Encoding]::UTF8.GetString($descriptorRaw) |
      ConvertFrom-Json -AsHashtable
    Assert-ExactKeys $descriptor @('schema', 'key_id', 'purpose', 'algorithm',
      'protection', 'scope', 'protected_blob_sha256', 'created_at',
      'secret_value_in_descriptor', 'archive_destination', 'disaster_recovery_class')
    if ($descriptor.schema -cne 'atlas.supabase.offsite-recovery-key.descriptor.v1' -or
        $descriptor.purpose -cne 'SUPABASE_CROSS_PROJECT_OFFSITE_ARCHIVE_ENCRYPTION' -or
        $descriptor.algorithm -cne 'AES-256-GCM' -or
        $descriptor.protection -cne 'WINDOWS_DPAPI_CURRENT_USER' -or
        $descriptor.scope -cne 'ATLAS_LOCAL_PROTECTED_SECRET_BOUNDARY' -or
        $descriptor.secret_value_in_descriptor -ne $false) {
      throw 'Protected descriptor contract drift.'
    }
    Assert-HexDigest $descriptor.protected_blob_sha256
    $protectedBytes = [System.IO.File]::ReadAllBytes($blobPath)
    if ($protectedBytes.Length -lt 48 -or
        (Get-Sha256Hex $protectedBytes) -cne $descriptor.protected_blob_sha256) {
      throw 'Protected blob preimage drift.'
    }
    Add-Type -AssemblyName System.Security
    $keyBytes = [System.Security.Cryptography.ProtectedData]::Unprotect(
      $protectedBytes, $dpapiEntropy,
      [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
    if ($keyBytes.Length -ne 32) { throw 'Archive key shape drift.' }
    $serialized = Seal-HostBoundKey -ArchiveKey $keyBytes `
      -RecoveryCode $codeBytes -Context $context
    $result = Write-NewLiveCapsule -CapsulePath $paths.capsule_path `
      -SerializedCapsule $serialized -Guard $guard
    $guard.AssertPinnedFiles()
    return @{ result = 'LOCAL_ENCRYPTED_CAPSULE_CREATED';
      capsule_sha256 = $result.capsule_sha256;
      capsule_bytes = $result.capsule_bytes;
      live_effect = $true }
  } finally {
    $guard.Dispose()
    if ($null -ne $keyBytes) {
      [System.Array]::Clear($keyBytes, 0, $keyBytes.Length)
    }
    if ($null -ne $codeBytes) {
      [System.Array]::Clear($codeBytes, 0, $codeBytes.Length)
    }
    if ($null -ne $protectedBytes) {
      [System.Array]::Clear($protectedBytes, 0, $protectedBytes.Length)
    }
    if ($null -ne $descriptorRaw) {
      [System.Array]::Clear($descriptorRaw, 0, $descriptorRaw.Length)
    }
  }
}

if ($Action -eq 'SealLive') {
  throw 'LIVE_ACTION_NOT_ADMITTED_PRIVATE_HANDOFF_NOT_INSTALLED'
}

if ($AttemptId -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]{3,79}$') {
  throw 'Unsafe synthetic attempt ID.'
}
if ($ProjectRef -cnotmatch '^[a-z0-9]{8,32}$') {
  throw 'Invalid project reference.'
}
if (($WrongCode -and $Action -ne 'VerifySynthetic') -or
    ($WrongKey -and $Action -ne 'SealSynthetic') -or
    ($TamperCoreContext -and $Action -ne 'VerifyHostCoreSynthetic')) {
  throw 'Synthetic fault switch does not match the action.'
}
Assert-HexDigest $DescriptorSha256
Assert-HexDigest $ArchiveSha256

if ($Action -eq 'VerifyHostCoreSynthetic') {
  $publicKey = [byte[]](0..31)
  $publicCode = [byte[]](32..63)
  $recovered = [byte[]]::new(32)
  $publicContext = [ordered]@{
    domain = $domain
    attempt_id = $AttemptId
    project_ref = $ProjectRef
    descriptor_sha256 = $DescriptorSha256
    archive_sha256 = $ArchiveSha256
  }
  try {
    $sealedJson = Seal-HostBoundKey -ArchiveKey $publicKey -RecoveryCode $publicCode `
      -Context $publicContext
    $publicContext.archive_sha256 = 'f' * 64
    $sealed = $sealedJson | ConvertFrom-Json -AsHashtable
    if ($sealed.context.archive_sha256 -cne $ArchiveSha256) {
      throw 'Synthetic host context snapshot drift.'
    }
    if ($TamperCoreContext) { $sealed.context.archive_sha256 = '0' * 64 }
    $nonceBytes = [Convert]::FromBase64String($sealed.nonce_b64)
    $tagBytes = [Convert]::FromBase64String($sealed.tag_b64)
    $wrappedBytes = [Convert]::FromBase64String($sealed.wrapped_key_b64)
    $aadBytes = [System.Text.Encoding]::UTF8.GetBytes(
      ($sealed.context | ConvertTo-Json -Compress -Depth 4))
    $aes = [System.Security.Cryptography.AesGcm]::new($publicCode, 16)
    try {
      $aes.Decrypt($nonceBytes, $wrappedBytes, $tagBytes, $recovered, $aadBytes)
    } finally {
      $aes.Dispose()
      [System.Array]::Clear($aadBytes, 0, $aadBytes.Length)
      [System.Array]::Clear($wrappedBytes, 0, $wrappedBytes.Length)
    }
    if (-not [System.Security.Cryptography.CryptographicOperations]::FixedTimeEquals(
        $publicKey, $recovered)) { throw 'Synthetic host core mismatch.' }
    [ordered]@{
      result = 'SYNTHETIC_HOST_CORE_VERIFIED'
      secret_emitted = $false
      live_effect = $false
    } | ConvertTo-Json -Compress
  } finally {
    [System.Array]::Clear($publicKey, 0, $publicKey.Length)
    [System.Array]::Clear($publicCode, 0, $publicCode.Length)
    [System.Array]::Clear($recovered, 0, $recovered.Length)
  }
  return
}

$resolvedFixtureRoot = [System.IO.Path]::GetFullPath($FixtureRoot).TrimEnd('\', '/')
$resolvedTempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\', '/')
$tempPrefix = $resolvedTempRoot + [System.IO.Path]::DirectorySeparatorChar
if (-not $resolvedFixtureRoot.StartsWith($tempPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'Synthetic fixture root must be beneath the system temp directory.'
}
if (-not (Test-Path -LiteralPath $resolvedFixtureRoot -PathType Container)) {
  throw 'Synthetic fixture root is missing.'
}
Assert-NoReparsePoint $resolvedTempRoot
$fixtureRelativePath = $resolvedFixtureRoot.Substring($tempPrefix.Length)
$fixtureCursor = $resolvedTempRoot
foreach ($segment in $fixtureRelativePath.Split([System.IO.Path]::DirectorySeparatorChar,
  [System.StringSplitOptions]::RemoveEmptyEntries)) {
  $fixtureCursor = Join-Path $fixtureCursor $segment
  Assert-NoReparsePoint $fixtureCursor
}

$markerPath = Join-Path $resolvedFixtureRoot 'synthetic-fixture.marker.json'
$capsuleRoot = Join-Path $resolvedFixtureRoot 'capsules'
$capsulePath = Join-Path $capsuleRoot ($AttemptId + '.capsule.json')
if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
  throw 'Synthetic fixture is incomplete.'
}
Assert-NoReparsePoint $markerPath
$marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json -AsHashtable
Assert-ExactKeys $marker @('schema', 'synthetic_only')
if ($marker.schema -cne 'atlas.synthetic-key-capsule-fixture.v1' -or $marker.synthetic_only -ne $true) {
  throw 'Synthetic fixture marker is invalid.'
}

$context = [ordered]@{
  domain = $domain
  attempt_id = $AttemptId
  project_ref = $ProjectRef
  descriptor_sha256 = $DescriptorSha256
  archive_sha256 = $ArchiveSha256
}
if ($Action -eq 'VerifyFileAclSynthetic') {
  Assert-NoReparsePoint $capsuleRoot
  Assert-PrivateFileAcl (Join-Path $capsuleRoot ($AttemptId + '.attempt.json'))
  Assert-PrivateFileAcl $capsulePath
  [ordered]@{
    result = 'SYNTHETIC_FILE_ACL_VERIFIED'
    secret_emitted = $false
    live_effect = $false
  } | ConvertTo-Json -Compress
  return
}
if ($Action -eq 'VerifyPathIdentitySynthetic') {
  # Public sentinel bytes only. This exercises the same guard, secure CreateNew,
  # close/reopen identity check and pinning used by marker/capsule creation.
  if (-not (Test-Path -LiteralPath $capsuleRoot)) {
    $null = New-Item -ItemType Directory -Path $capsuleRoot -ErrorAction Stop
  }
  $guard = New-PrivatePathGuard $capsuleRoot
  try {
    $probe = Join-Path $capsuleRoot 'identity-probe.txt'
    $opened = New-PrivateFileStream -Path $probe -Guard $guard
    $bytes = [System.Text.Encoding]::ASCII.GetBytes('synthetic identity probe')
    try {
      $opened.stream.Write($bytes, 0, $bytes.Length)
      $opened.stream.Flush($true)
    } finally {
      $opened.stream.Dispose()
      [System.Array]::Clear($bytes, 0, $bytes.Length)
    }
    $renamed = $false
    $directoryDriftDetected = $false
    try {
      [System.IO.Directory]::Move($capsuleRoot, ($capsuleRoot + '.moved'))
      $renamed = $true
    } catch [System.IO.IOException], [System.UnauthorizedAccessException] { }
    if ($renamed) {
      try {
        $null = [System.IO.Directory]::CreateDirectory($capsuleRoot)
        try {
          $guard.AssertParents()
        } catch [System.IO.IOException] {
          if ($_.Exception.Message -notin @('PRIVATE_PATH_IDENTITY_DRIFT',
              'PRIVATE_PATH_IDENTITY_UNPROVEN')) { throw }
          $directoryDriftDetected = $true
        }
      } finally {
        [System.IO.Directory]::Delete($capsuleRoot)
        [System.IO.Directory]::Move(($capsuleRoot + '.moved'), $capsuleRoot)
      }
      if (-not $directoryDriftDetected) { throw 'PRIVATE_PARENT_SWAP_NOT_DETECTED' }
    }
    [System.IO.File]::Move($probe, ($probe + '.moved'))
    [System.IO.File]::Copy(($probe + '.moved'), $probe)
    $replacementRejected = $false
    try {
      $null = $guard.PinClosedFile($probe, $opened.identity)
    } catch [System.IO.IOException] {
      if ($_.Exception.Message -ne 'PRIVATE_PATH_FILE_REPLACED') { throw }
      $replacementRejected = $true
    }
    if (-not $replacementRejected) { throw 'PRIVATE_FILE_REPLACEMENT_NOT_REJECTED' }
    $tamperProbe = Join-Path $capsuleRoot 'same-file-probe.txt'
    $originalBytes = [System.Text.Encoding]::ASCII.GetBytes('synthetic original bytes')
    $changedBytes = [System.Text.Encoding]::ASCII.GetBytes('synthetic changed! bytes')
    $expectedDigest = Get-Sha256Hex $originalBytes
    $openedTamper = New-PrivateFileStream -Path $tamperProbe -Guard $guard
    try {
      $openedTamper.stream.Write($originalBytes, 0, $originalBytes.Length)
      $openedTamper.stream.Flush($true)
    } finally {
      $openedTamper.stream.Dispose()
    }
    [System.IO.File]::WriteAllBytes($tamperProbe, $changedBytes)
    $readbackTamper = $guard.PinClosedFile($tamperProbe, $openedTamper.identity)
    $sameFileTamperRejected = $false
    try {
      Assert-PinnedFileContent -Stream $readbackTamper `
        -ExpectedSha256 $expectedDigest -ExpectedLength $originalBytes.Length
    } catch {
      if ($_.Exception.Message -ne 'Private file content drift.') { throw }
      $sameFileTamperRejected = $true
    } finally {
      [System.Array]::Clear($originalBytes, 0, $originalBytes.Length)
      [System.Array]::Clear($changedBytes, 0, $changedBytes.Length)
    }
    if (-not $sameFileTamperRejected) { throw 'PRIVATE_SAME_FILE_TAMPER_NOT_REJECTED' }
    $pinned = Join-Path $capsuleRoot 'pinned-probe.txt'
    $openedPinned = New-PrivateFileStream -Path $pinned -Guard $guard
    $openedPinned.stream.Dispose()
    $readback = $guard.PinClosedFile($pinned, $openedPinned.identity)
    Assert-PrivateFileAcl -Path $pinned -Stream $readback
    $leafRenamed = $false
    $pinnedDriftDetected = $false
    try {
      [System.IO.File]::Move($pinned, ($pinned + '.moved'))
      $leafRenamed = $true
    } catch [System.IO.IOException], [System.UnauthorizedAccessException] { }
    if ($leafRenamed) {
      try {
        $guard.AssertPinnedFiles()
      } catch [System.IO.IOException] {
        if ($_.Exception.Message -notin @('PRIVATE_PATH_IDENTITY_DRIFT',
            'PRIVATE_PATH_IDENTITY_UNPROVEN')) { throw }
        $pinnedDriftDetected = $true
      }
      if (-not $pinnedDriftDetected) { throw 'PRIVATE_PINNED_FILE_SWAP_NOT_DETECTED' }
    }
    [ordered]@{
      result = 'SYNTHETIC_PATH_IDENTITY_VERIFIED'
      directory_swap_blocked_or_detected = $true
      directory_swap_detected = $directoryDriftDetected
      closed_file_replacement_rejected = $true
      same_file_tamper_rejected = $true
      pinned_file_swap_blocked_or_detected = $true
      pinned_file_swap_detected = $pinnedDriftDetected
      secret_emitted = $false
      live_effect = $false
    } | ConvertTo-Json -Compress
  } finally {
    $guard.Dispose()
  }
  return
}
if ($Action -eq 'VerifyHostPersistenceSynthetic') {
  $publicKey = [byte[]](0..31)
  $publicCode = [byte[]](32..63)
  $guard = $null
  try {
    if (-not (Test-Path -LiteralPath $capsuleRoot)) {
      $null = New-Item -ItemType Directory -Path $capsuleRoot -ErrorAction Stop
    }
    Assert-NoReparsePoint $capsuleRoot
    $guard = New-PrivatePathGuard $capsuleRoot
    $sealedJson = Seal-HostBoundKey -ArchiveKey $publicKey `
      -RecoveryCode $publicCode -Context $context
    $paths = New-OneUseLiveMarker -CapsuleDirectory $capsuleRoot -Context $context -Guard $guard
    $written = Write-NewLiveCapsule -CapsulePath $paths.capsule_path `
      -SerializedCapsule $sealedJson -Guard $guard
    $guard.AssertPinnedFiles()
    Assert-PrivateFileAcl -Path $paths.marker_path -Stream $paths.marker_readback
    Assert-PrivateFileAcl -Path $paths.capsule_path -Stream $written.capsule_readback
    [ordered]@{
      result = 'SYNTHETIC_HOST_PERSISTENCE_VERIFIED'
      marker_sha256 = $paths.marker_sha256
      capsule_sha256 = $written.capsule_sha256
      capsule_bytes = $written.capsule_bytes
      marker_file_acl_verified = $true
      capsule_file_acl_verified = $true
      secret_emitted = $false
      live_effect = $false
    } | ConvertTo-Json -Compress
  } finally {
    if ($null -ne $guard) { $guard.Dispose() }
    [System.Array]::Clear($publicKey, 0, $publicKey.Length)
    [System.Array]::Clear($publicCode, 0, $publicCode.Length)
  }
  return
}
$aad = [System.Text.Encoding]::UTF8.GetBytes(($context | ConvertTo-Json -Compress -Depth 4))
$key = $null
$code = $null
$wrapped = $null
$created = $false
try {
  if ($WrongCode) { $code = [byte[]](64..95) }
  else { $code = [byte[]](32..63) }

  if ($Action -eq 'SealSynthetic') {
    if ($WrongKey) { $key = [byte[]](96..127) }
    else { $key = [byte[]](0..31) }
    if (Test-Path -LiteralPath $capsulePath) { throw 'Duplicate synthetic attempt.' }
    if (-not (Test-Path -LiteralPath $capsuleRoot)) {
      $null = New-Item -ItemType Directory -Path $capsuleRoot -ErrorAction Stop
    }
    Assert-NoReparsePoint $capsuleRoot

    $nonce = [byte[]]::new(12)
    $tag = [byte[]]::new(16)
    $wrapped = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($nonce)
    $aes = [System.Security.Cryptography.AesGcm]::new($code, 16)
    try {
      $aes.Encrypt($nonce, $key, $wrapped, $tag, $aad)
    } finally {
      $aes.Dispose()
    }
    $capsule = [ordered]@{
      schema = $capsuleSchema
      algorithm = 'AES-256-GCM'
      context = $context
      nonce_b64 = [Convert]::ToBase64String($nonce)
      tag_b64 = [Convert]::ToBase64String($tag)
      wrapped_key_b64 = [Convert]::ToBase64String($wrapped)
    }
    $serialized = [System.Text.Encoding]::UTF8.GetBytes(($capsule | ConvertTo-Json -Compress -Depth 6) + "`n")
    $stream = [System.IO.File]::Open($capsulePath, [System.IO.FileMode]::CreateNew,
      [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    $created = $true
    try {
      $stream.Write($serialized, 0, $serialized.Length)
      $stream.Flush($true)
    } finally {
      $stream.Dispose()
    }
    [ordered]@{
      result = 'SYNTHETIC_CAPSULE_SEALED'
      capsule_sha256 = Get-Sha256Hex $serialized
      capsule_bytes = $serialized.Length
      secret_emitted = $false
      live_effect = $false
    } | ConvertTo-Json -Compress
  } else {
    if (-not (Test-Path -LiteralPath $capsulePath -PathType Leaf)) {
      throw 'Synthetic capsule is missing.'
    }
    Assert-NoReparsePoint $capsuleRoot
    Assert-NoReparsePoint $capsulePath
    $serialized = [System.IO.File]::ReadAllBytes($capsulePath)
    $capsule = [System.Text.Encoding]::UTF8.GetString($serialized) | ConvertFrom-Json -AsHashtable
    Assert-ExactKeys $capsule @('schema', 'algorithm', 'context', 'nonce_b64', 'tag_b64', 'wrapped_key_b64')
    Assert-ExactKeys $capsule.context @('domain', 'attempt_id', 'project_ref', 'descriptor_sha256', 'archive_sha256')
    if ($capsule.schema -cne $capsuleSchema -or $capsule.algorithm -cne 'AES-256-GCM') {
      throw 'Capsule version or algorithm drift.'
    }
    foreach ($field in $context.Keys) {
      if ($capsule.context[$field] -cne $context[$field]) { throw 'Capsule context mismatch.' }
    }
    try {
      $nonce = [Convert]::FromBase64String($capsule.nonce_b64)
      $tag = [Convert]::FromBase64String($capsule.tag_b64)
      $wrapped = [Convert]::FromBase64String($capsule.wrapped_key_b64)
    } catch {
      throw 'Capsule encoding is invalid.'
    }
    if ($nonce.Length -ne 12 -or $tag.Length -ne 16 -or $wrapped.Length -ne 32) {
      throw 'Capsule field length drift.'
    }
    $key = [byte[]]::new(32)
    $aes = [System.Security.Cryptography.AesGcm]::new($code, 16)
    try {
      try {
        $aes.Decrypt($nonce, $wrapped, $tag, $key, $aad)
      } catch {
        throw 'Capsule authentication failed.'
      }
    } finally {
      $aes.Dispose()
    }
    if ([Convert]::ToHexString($key) -cne
      '000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F') {
      throw 'Synthetic key mismatch.'
    }
    [ordered]@{
      result = 'SYNTHETIC_CAPSULE_VERIFIED'
      capsule_sha256 = Get-Sha256Hex $serialized
      secret_emitted = $false
      live_effect = $false
    } | ConvertTo-Json -Compress
  }
} catch {
  if ($created -and (Test-Path -LiteralPath $capsulePath)) {
    [System.IO.File]::Delete($capsulePath)
  }
  throw
} finally {
  if ($null -ne $key) { [System.Array]::Clear($key, 0, $key.Length) }
  if ($null -ne $code) { [System.Array]::Clear($code, 0, $code.Length) }
  if ($null -ne $wrapped) { [System.Array]::Clear($wrapped, 0, $wrapped.Length) }
}
