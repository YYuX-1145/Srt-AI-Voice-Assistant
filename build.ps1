param(
    [string]$PyInstallerPath = "pyinstaller",
    [switch]$DryRun,
    [switch]$SkipManualSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSCommandPath
Set-Location $repoRoot
$manualSyncScript = Join-Path $repoRoot "sync_built-in_manual.ps1"

function Resolve-PyInstallerCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandOrPath
    )

    if (Test-Path -LiteralPath $CommandOrPath) {
        return (Resolve-Path -LiteralPath $CommandOrPath).Path
    }

    $command = Get-Command $CommandOrPath -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    return $CommandOrPath
}

function Get-PythonModuleNames {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativeRoot
    )

    $searchRoot = Join-Path $repoRoot $RelativeRoot
    if (-not (Test-Path -LiteralPath $searchRoot)) {
        return @()
    }

    return Get-ChildItem -LiteralPath $searchRoot -Recurse -File -Filter "*.py" |
        Sort-Object FullName |
        ForEach-Object {
            if ($_.BaseName -eq "__init__") {
                return
            }

            $relativePath = $_.FullName.Substring($repoRoot.Length).TrimStart("\", "/")
            ($relativePath -replace "\.py$", "") -replace "[\\/]", "."
        }
}

$pyInstallerExe = Resolve-PyInstallerCommand -CommandOrPath $PyInstallerPath
$commandParts = [System.Collections.Generic.List[string]]::new()

$hiddenImports = @(
    Get-PythonModuleNames -RelativeRoot "Sava_Utils\man"
    Get-PythonModuleNames -RelativeRoot "Sava_Utils\i18nAuto\translations"
) | Sort-Object -Unique

$commandParts.Add("--noconfirm")

foreach ($moduleName in $hiddenImports) {
    $commandParts.Add("--hidden-import=$moduleName")
}

foreach ($packageName in @("gradio", "gradio_client", "safehttpx", "groovy")) {
    $commandParts.Add("--collect-data=$packageName")
}

$commandParts.Add("--additional-hooks-dir=hooks")
$commandParts.Add("-F")
$commandParts.Add("Srt-AI-Voice-Assistant.py")

$displayCommand = @('"' + $pyInstallerExe + '"') + $commandParts
Write-Host ($displayCommand -join " ")

if (-not $DryRun) {
    if (-not $SkipManualSync) {
        if (-not (Test-Path -LiteralPath $manualSyncScript)) {
            throw "Manual sync script not found: $manualSyncScript"
        }

        & $manualSyncScript
        if ($LASTEXITCODE -ne 0) {
            throw "Manual sync failed with exit code $LASTEXITCODE"
        }
    }

    & $pyInstallerExe $commandParts
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
}
