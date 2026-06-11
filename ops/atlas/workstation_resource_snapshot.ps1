[CmdletBinding()]
param(
    [ValidateRange(1, 50)]
    [int]$Top = 10,

    [switch]$WorkflowOnly,

    [switch]$IncludePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$workflowNames = @(
    "node",
    "python",
    "pwsh",
    "powershell",
    "Code",
    "codex",
    "chrome",
    "msedge",
    "chromium",
    "playwright",
    "npm",
    "vite",
    "next"
)

function Format-CpuSeconds {
    param(
        [Parameter(Mandatory = $true)]
        [double]$Cpu
    )

    return [math]::Round($Cpu, 2)
}

function Format-Megabytes {
    param(
        [Parameter(Mandatory = $true)]
        [double]$Bytes
    )

    return [math]::Round($Bytes / 1MB, 1)
}

function Get-SafePath {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process
    )

    try {
        return [string]$Process.Path
    } catch {
        return ""
    }
}

function Select-ProcessView {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process[]]$Processes
    )

    if ($IncludePath) {
        return $Processes | Select-Object `
            Name, `
            Id, `
            @{ Name = "CPUSeconds"; Expression = { Format-CpuSeconds -Cpu $_.CPU } }, `
            @{ Name = "WorkingSetMB"; Expression = { Format-Megabytes -Bytes $_.WorkingSet64 } }, `
            @{ Name = "Path"; Expression = { Get-SafePath -Process $_ } }
    }

    return $Processes | Select-Object `
        Name, `
        Id, `
        @{ Name = "CPUSeconds"; Expression = { Format-CpuSeconds -Cpu $_.CPU } }, `
        @{ Name = "WorkingSetMB"; Expression = { Format-Megabytes -Bytes $_.WorkingSet64 } }
}

function Write-Section {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,

        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process[]]$Processes
    )

    Write-Output ""
    Write-Output "== $Title =="

    if (-not $Processes -or $Processes.Count -eq 0) {
        Write-Output "(none)"
        return
    }

    Select-ProcessView -Processes $Processes | Format-Table -AutoSize | Out-String -Width 220 | Write-Output
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
Write-Output "ATLAS workstation resource snapshot"
Write-Output "Generated: $timestamp"
Write-Output "Read-only helper. It does not stop processes, mutate services, inspect secrets, or write logs."
Write-Output "Privacy warning: process paths and window-title-adjacent context can be sensitive. Do not commit raw machine-private output."

$allProcesses = Get-Process
$workflowProcesses = $allProcesses | Where-Object { $workflowNames -contains $_.ProcessName } | Sort-Object -Property `
    @{ Expression = "CPU"; Descending = $true }, `
    @{ Expression = "WorkingSet64"; Descending = $true } | Select-Object -First $Top

if (-not $WorkflowOnly) {
    $topCpu = $allProcesses | Sort-Object CPU -Descending | Select-Object -First $Top
    $topMemory = $allProcesses | Sort-Object WorkingSet64 -Descending | Select-Object -First $Top

    Write-Section -Title "Top CPU processes" -Processes $topCpu
    Write-Section -Title "Top memory processes" -Processes $topMemory
}

Write-Section -Title "Common workflow processes" -Processes $workflowProcesses

Write-Output ""
Write-Output "Review guidance:"
Write-Output "- Only one Codex chat should be hot at a time."
Write-Output "- Hot means commands, browser automation, tests, dev servers, screenshots, or validation are actively running."
Write-Output "- If another chat stays open, keep it idle and explicitly report what remains running before handoff or archive."
