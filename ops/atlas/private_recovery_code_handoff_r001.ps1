# Uninstalled source integration candidate. Functions are not an authority boundary.
# A separately reviewed action wrapper must admit live use and pin these bytes.
Set-StrictMode -Version Latest

function ConvertFrom-OfflineRecoveryCode {
  param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
  $compact = $Text.Replace(' ', '').Replace('-', '')
  if ($compact -cnotmatch '^[0-9A-Fa-f]{64}$') {
    throw 'RECOVERY_CODE_FORMAT_REJECTED'
  }
  return ,([Convert]::FromHexString($compact))
}

function Test-OfflineRecoveryCodeEntry {
  param(
    [Parameter(Mandatory = $true)][byte[]]$Expected,
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Entry
  )
  if ($Expected.Length -ne 32) { throw 'EXPECTED_CODE_SHAPE_REJECTED' }
  [byte[]]$entered = $null
  try {
    $entered = ConvertFrom-OfflineRecoveryCode -Text $Entry
    return [System.Security.Cryptography.CryptographicOperations]::FixedTimeEquals(
      $Expected, $entered)
  } catch {
    if ($_.Exception.Message -eq 'RECOVERY_CODE_FORMAT_REJECTED') { return $false }
    throw
  } finally {
    if ($null -ne $entered) { [System.Array]::Clear($entered, 0, $entered.Length) }
  }
}

function Test-PrivateHandoffHostVersion {
  param([int]$Major, [int]$Build)
  return ($Major -gt 10 -or ($Major -eq 10 -and $Build -ge 19041))
}

function Initialize-PrivateHandoffDisplay {
  $version = [Environment]::OSVersion.Version
  if (-not $IsWindows -or -not [Environment]::UserInteractive -or
      -not (Test-PrivateHandoffHostVersion -Major $version.Major -Build $version.Build)) {
    throw 'TRUSTED_INTERACTIVE_WINDOWS_SESSION_REQUIRED'
  }
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
  if (-not ('AtlasPrivateHandoffCaptureGuardR001' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class AtlasPrivateHandoffCaptureGuardR001 {
  [DllImport("user32.dll", SetLastError = true)]
  private static extern bool SetWindowDisplayAffinity(IntPtr window, uint affinity);
  [DllImport("user32.dll", SetLastError = true)]
  private static extern bool GetWindowDisplayAffinity(IntPtr window, out uint affinity);
  public static bool Exclude(IntPtr window) {
    if (!SetWindowDisplayAffinity(window, 0x11)) return false;
    uint observed = 0;
    return GetWindowDisplayAffinity(window, out observed) && observed == 0x11;
  }
}
'@
  }
}

function Show-PrivateRecoveryCodeDialog {
  param([Parameter(Mandatory = $true)][byte[]]$Code, [switch]$Interactive)
  if (-not $Interactive) { throw 'PRIVATE_HANDOFF_INTERACTIVE_OPT_IN_REQUIRED' }
  if ($Code.Length -ne 32) { throw 'RECOVERY_CODE_SHAPE_REJECTED' }
  Initialize-PrivateHandoffDisplay
  $codeText = [Convert]::ToHexString($Code)
  $display = [System.Windows.Forms.Form]::new()
  $display.Text = 'ATLAS private recovery code'
  $display.Width = 620
  $display.Height = 190
  $display.StartPosition = 'CenterScreen'
  $display.TopMost = $true
  $label = [System.Windows.Forms.Label]::new()
  $label.Left = 18; $label.Top = 24; $label.Width = 580; $label.Height = 44
  $label.Text = 'Preparing protected display...'
  $display.Controls.Add($label)
  $saved = [System.Windows.Forms.Button]::new()
  $saved.Left = 18; $saved.Top = 92; $saved.Width = 170
  $saved.Text = 'I saved this code'
  $saved.Enabled = $false
  $saved.Add_Click({ $display.DialogResult = [System.Windows.Forms.DialogResult]::OK; $display.Close() }.GetNewClosure())
  $display.Controls.Add($saved)
  $display.Add_Shown({
    if (-not [AtlasPrivateHandoffCaptureGuardR001]::Exclude($display.Handle)) {
      $display.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
      $display.Close()
      return
    }
    $label.Text = $codeText
    $saved.Enabled = $true
  }.GetNewClosure())
  try { $shown = $display.ShowDialog() }
  finally { $label.Text = ''; $display.Dispose(); $codeText = $null }
  if ($shown -ne [System.Windows.Forms.DialogResult]::OK) { return $false }

  $entryForm = [System.Windows.Forms.Form]::new()
  $entryForm.Text = 'Re-enter private recovery code'
  $entryForm.Width = 620
  $entryForm.Height = 175
  $entryForm.StartPosition = 'CenterScreen'
  $entryForm.TopMost = $true
  $entry = [System.Windows.Forms.TextBox]::new()
  $entry.Left = 18; $entry.Top = 25; $entry.Width = 565
  $entry.UseSystemPasswordChar = $true
  $entry.MaxLength = 95
  $entry.Enabled = $false
  $entryForm.Controls.Add($entry)
  $confirm = [System.Windows.Forms.Button]::new()
  $confirm.Left = 18; $confirm.Top = 75; $confirm.Width = 145
  $confirm.Text = 'Confirm'
  $confirm.Enabled = $false
  $confirm.Add_Click({ $entryForm.DialogResult = [System.Windows.Forms.DialogResult]::OK; $entryForm.Close() }.GetNewClosure())
  $entryForm.Controls.Add($confirm)
  $entryForm.Add_Shown({
    if (-not [AtlasPrivateHandoffCaptureGuardR001]::Exclude($entryForm.Handle)) {
      $entryForm.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
      $entryForm.Close()
      return
    }
    $entry.Enabled = $true
    $confirm.Enabled = $true
    $entry.Focus()
  }.GetNewClosure())
  try {
    $accepted = $entryForm.ShowDialog()
    if ($accepted -ne [System.Windows.Forms.DialogResult]::OK) { return $false }
    return Test-OfflineRecoveryCodeEntry -Expected $Code -Entry $entry.Text
  } finally {
    $entry.Clear()
    $entryForm.Dispose()
  }
}

function Show-SyntheticPrivateRecoveryCodeDialog {
  param([Parameter(Mandatory = $true)][byte[]]$SyntheticCode, [switch]$Interactive)
  if ($SyntheticCode.Length -ne 32) { throw 'SYNTHETIC_CODE_SHAPE_REJECTED' }
  [byte[]]$onlyPublicFixture = 0..31
  try {
    if (-not [System.Security.Cryptography.CryptographicOperations]::FixedTimeEquals(
      $onlyPublicFixture, $SyntheticCode)) {
      throw 'NON_PUBLIC_SYNTHETIC_VECTOR_REJECTED'
    }
  } finally { [System.Array]::Clear($onlyPublicFixture, 0, $onlyPublicFixture.Length) }
  if (-not $Interactive) { throw 'SYNTHETIC_INTERACTION_EXPLICIT_OPT_IN_REQUIRED' }
  return Show-PrivateRecoveryCodeDialog -Code $SyntheticCode -Interactive
}

function Invoke-SyntheticPrivateRecoveryCodeHandoff {
  param([switch]$Interactive)
  if (-not $Interactive) { throw 'SYNTHETIC_INTERACTION_EXPLICIT_OPT_IN_REQUIRED' }
  [byte[]]$publicFixture = 0..31
  try {
    if (Show-SyntheticPrivateRecoveryCodeDialog -SyntheticCode $publicFixture -Interactive) {
      return 'SYNTHETIC_LOCAL_REENTRY_CONFIRMED_NOT_CUSTODY_PROOF'
    }
    return 'SYNTHETIC_LOCAL_REENTRY_REJECTED'
  } finally { [System.Array]::Clear($publicFixture, 0, $publicFixture.Length) }
}

function Invoke-PrivateRecoveryCodeHandoff {
  param([AllowNull()][byte[]]$RecoveryCode, [switch]$Interactive)
  # Explicit interaction is necessary, but is not live-action authorization.
  if (-not $Interactive) { throw 'PRIVATE_HANDOFF_INTERACTIVE_OPT_IN_REQUIRED' }
  if ($null -eq $RecoveryCode -or $RecoveryCode.Length -ne 32) {
    throw 'RECOVERY_CODE_SHAPE_REJECTED'
  }
  [byte[]]$ownedCode = $RecoveryCode.Clone()
  try {
    return Show-PrivateRecoveryCodeDialog -Code $ownedCode -Interactive
  } finally {
    [System.Array]::Clear($ownedCode, 0, $ownedCode.Length)
  }
}
