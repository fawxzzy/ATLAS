[CmdletBinding()]
param(
    [ValidateRange(1, 50)]
    [int]$Top = 10,

    [switch]$WorkflowOnly,

    [switch]$IncludePath,

    [switch]$JsonSummary
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

function Get-SafeCpuSeconds {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process
    )

    try {
        if ($null -eq $Process.CPU) {
            return 0.0
        }

        return [double]$Process.CPU
    } catch {
        return 0.0
    }
}

function Get-SafeWorkingSetBytes {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process
    )

    try {
        if ($null -eq $Process.WorkingSet64) {
            return 0.0
        }

        return [double]$Process.WorkingSet64
    } catch {
        return 0.0
    }
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
            @{ Name = "CPUSeconds"; Expression = { Format-CpuSeconds -Cpu (Get-SafeCpuSeconds -Process $_) } }, `
            @{ Name = "WorkingSetMB"; Expression = { Format-Megabytes -Bytes (Get-SafeWorkingSetBytes -Process $_) } }, `
            @{ Name = "Path"; Expression = { Get-SafePath -Process $_ } }
    }

    return $Processes | Select-Object `
        Name, `
        Id, `
        @{ Name = "CPUSeconds"; Expression = { Format-CpuSeconds -Cpu (Get-SafeCpuSeconds -Process $_) } }, `
        @{ Name = "WorkingSetMB"; Expression = { Format-Megabytes -Bytes (Get-SafeWorkingSetBytes -Process $_) } }
}

function Get-ProcessRecord {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process
    )

    $record = [ordered]@{
        name = [string]$Process.ProcessName
        id = [int]$Process.Id
        cpu_seconds = Format-CpuSeconds -Cpu (Get-SafeCpuSeconds -Process $Process)
        working_set_mb = Format-Megabytes -Bytes (Get-SafeWorkingSetBytes -Process $Process)
    }

    if ($IncludePath) {
        $record.path = Get-SafePath -Process $Process
    }

    return [pscustomobject]$record
}

function Get-WorkflowSummaryRecord {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process[]]$Processes
    )

    if (-not $Processes -or $Processes.Count -eq 0) {
        return [pscustomobject]([ordered]@{
            workflow_process_count = 0
            distinct_workflow_names = 0
            workflow_working_set_mb = 0.0
            workflow_names = @()
        })
    }

    $totalWorkingSetBytes = ($Processes | Measure-Object -Property WorkingSet64 -Sum).Sum
    if ($null -eq $totalWorkingSetBytes) {
        $totalWorkingSetBytes = 0
    }

    $groupedNames = $Processes |
        Group-Object { $_.ProcessName.ToLowerInvariant() } |
        Sort-Object -Property @{ Expression = "Count"; Descending = $true }, @{ Expression = "Name"; Descending = $false } |
        ForEach-Object {
            [pscustomobject]([ordered]@{
                name = [string]$_.Name
                count = [int]$_.Count
            })
        }

    return [pscustomobject]([ordered]@{
        workflow_process_count = [int]$Processes.Count
        distinct_workflow_names = [int](($Processes | Group-Object { $_.ProcessName.ToLowerInvariant() }).Count)
        workflow_working_set_mb = Format-Megabytes -Bytes $totalWorkingSetBytes
        workflow_names = @($groupedNames)
    })
}

function Get-ReviewGuidance {
    return @(
        "Only one Codex chat should be hot at a time.",
        "Hot means commands, browser automation, tests, dev servers, screenshots, or validation are actively running.",
        "If another chat stays open, keep it idle and explicitly report what remains running before handoff or archive."
    )
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

function Write-WorkflowSummary {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process[]]$Processes
    )

    Write-Output ""
    Write-Output "== Workflow summary =="

    if (-not $Processes -or $Processes.Count -eq 0) {
        Write-Output "(none)"
        return
    }

    $totalWorkingSetBytes = ($Processes | Measure-Object -Property WorkingSet64 -Sum).Sum
    if ($null -eq $totalWorkingSetBytes) {
        $totalWorkingSetBytes = 0
    }

    $groupedNames = $Processes |
        Group-Object { $_.ProcessName.ToLowerInvariant() } |
        Sort-Object -Property @{ Expression = "Count"; Descending = $true }, @{ Expression = "Name"; Descending = $false } |
        ForEach-Object { "{0}({1})" -f $_.Name, $_.Count }

    Write-Output ("Workflow process count: {0}" -f $Processes.Count)
    Write-Output ("Distinct workflow names: {0}" -f (($Processes | Group-Object { $_.ProcessName.ToLowerInvariant() }).Count))
    Write-Output ("Workflow working set (MB): {0}" -f (Format-Megabytes -Bytes $totalWorkingSetBytes))
    Write-Output ("Workflow names: {0}" -f ($groupedNames -join ", "))
}

if ($JsonSummary -and $IncludePath) {
    throw "-JsonSummary cannot be combined with -IncludePath because JSON output must stay privacy-bounded."
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$allProcesses = Get-Process
$workflowProcesses = $allProcesses | Where-Object { $workflowNames -contains $_.ProcessName } | Sort-Object -Property `
    @{ Expression = { Get-SafeCpuSeconds -Process $_ }; Descending = $true }, `
    @{ Expression = { Get-SafeWorkingSetBytes -Process $_ }; Descending = $true } | Select-Object -First $Top

if ($JsonSummary) {
    $payload = [ordered]@{
        contract_version = "atlas.workstation_resource_snapshot.summary.v1"
        generated_at = [DateTimeOffset]::Now.ToString("o")
        workflow_only = [bool]$WorkflowOnly
        include_path = $false
        top = [int]$Top
        workflow_summary = Get-WorkflowSummaryRecord -Processes $workflowProcesses
        workflow_processes = @($workflowProcesses | ForEach-Object { Get-ProcessRecord -Process $_ })
        review_guidance = @(Get-ReviewGuidance)
    }

    if (-not $WorkflowOnly) {
        $topCpu = $allProcesses | Sort-Object -Property @{ Expression = { Get-SafeCpuSeconds -Process $_ }; Descending = $true } | Select-Object -First $Top
        $topMemory = $allProcesses | Sort-Object -Property @{ Expression = { Get-SafeWorkingSetBytes -Process $_ }; Descending = $true } | Select-Object -First $Top
        $payload.top_cpu_processes = @($topCpu | ForEach-Object { Get-ProcessRecord -Process $_ })
        $payload.top_memory_processes = @($topMemory | ForEach-Object { Get-ProcessRecord -Process $_ })
    }

    $payload | ConvertTo-Json -Depth 6
    return
}

Write-Output "ATLAS workstation resource snapshot"
Write-Output "Generated: $timestamp"
Write-Output "Read-only helper. It does not stop processes, mutate services, inspect secrets, or write logs."
Write-Output "Privacy warning: process paths and window-title-adjacent context can be sensitive. Do not commit raw machine-private output."

Write-WorkflowSummary -Processes $workflowProcesses

if (-not $WorkflowOnly) {
    $topCpu = $allProcesses | Sort-Object -Property @{ Expression = { Get-SafeCpuSeconds -Process $_ }; Descending = $true } | Select-Object -First $Top
    $topMemory = $allProcesses | Sort-Object -Property @{ Expression = { Get-SafeWorkingSetBytes -Process $_ }; Descending = $true } | Select-Object -First $Top

    Write-Section -Title "Top CPU processes" -Processes $topCpu
    Write-Section -Title "Top memory processes" -Processes $topMemory
}

Write-Section -Title "Common workflow processes" -Processes $workflowProcesses

Write-Output ""
Write-Output "Review guidance:"
Get-ReviewGuidance | ForEach-Object { Write-Output ("- {0}" -f $_) }
