# Sweep orphaned Claude Code MCP node.exe processes.
# Kills a node.exe ONLY when BOTH are true:
#   1) it is an npx-launched MCP-style process (command line contains _npx or npx-cli.js)
#   2) walking up its parent chain never reaches a still-running claude session
# Project dev servers (node from a project's node_modules, e.g. npm run dev) are NOT touched.
$ErrorActionPreference = 'SilentlyContinue'

$all  = Get-CimInstance Win32_Process
$byId = @{}
foreach ($p in $all) { $byId[[int]$p.ProcessId] = $p }

function Reaches-LiveClaude($n) {
    $cur  = $n
    $seen = @{}
    while ($true) {
        $ppid = [int]$cur.ParentProcessId
        if ($seen.ContainsKey($ppid)) { return $false }        # cycle guard
        $seen[$ppid] = $true
        $parent = $byId[$ppid]
        if (-not $parent) { return $false }                    # dead ancestor -> orphan
        if ($parent.CreationDate -gt $cur.CreationDate) { return $false }  # PID recycled
        if ($parent.Name -like 'claude*') { return $true }     # reached a live session
        $cur = $parent
    }
}

$killed = @()
foreach ($n in ($all | Where-Object { $_.Name -eq 'node.exe' })) {
    $cmd = [string]$n.CommandLine
    if ($cmd -notmatch '_npx' -and $cmd -notmatch 'npx-cli\.js') { continue }  # only npx MCP-style
    if (Reaches-LiveClaude $n) { continue }                                     # live session -> keep
    try {
        $ws = [math]::Round($n.WorkingSetSize / 1MB, 0)
        Stop-Process -Id $n.ProcessId -Force -ErrorAction Stop
        $killed += ("PID={0}({1}MB)" -f $n.ProcessId, $ws)
    } catch { }
}

if ($killed.Count -gt 0) {
    $ts   = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] swept $($killed.Count) orphan MCP node -> " + ($killed -join ', ')
    Add-Content -Path "$env:USERPROFILE\.claude\orphan-sweep.log" -Value $line
}
