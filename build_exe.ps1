$ErrorActionPreference = "Stop"

$pyiArgs = @()

Get-ChildItem -Path "./Sava_Utils/man" -Recurse -Filter "*.py" | ForEach-Object {
    $name = $_.BaseName
    if ($name -ne "__init__") {
        $lang = $_.Directory.Name
        $pyiArgs += "--hidden-import=Sava_Utils.man.$lang.$name"
    }
}

Get-ChildItem -Path "./Sava_Utils/i18nAuto/translations" -Filter "*.py" | ForEach-Object {
    $name = $_.BaseName
    if ($name -ne "__init__") {
        $pyiArgs += "--hidden-import=Sava_Utils.i18nAuto.translations.$name"
    }
}

$pyiArgs += "--collect-data=gradio"
$pyiArgs += "--collect-data=gradio_client"
$pyiArgs += "--collect-data=safehttpx"
$pyiArgs += "--collect-data=groovy"

# Step 1: Generate spec file
$specCmd = @("pyi-makespec") + $pyiArgs + @("-F", "Srt-AI-Voice-Assistant.py")
Write-Host "Generating spec file..." -ForegroundColor Cyan
Write-Host "$($specCmd -join ' ')" -ForegroundColor DarkGray
& $specCmd[0] $specCmd[1..($specCmd.Length - 1)]

# Step 2: Patch spec file — gradio requires source .py files, not byte-compiled .pyc in PYZ
$specFile = "Srt-AI-Voice-Assistant.spec"
$specContent = Get-Content $specFile -Raw
$specContent = $specContent -replace "(a\s*=\s*Analysis\(\s*\[)", "`$1"
$specContent = $specContent -replace "(\bhiddenimports=)", "module_collection_mode={'gradio': 'py'},`n             `$1"
Set-Content $specFile $specContent
Write-Host "Patched spec file with module_collection_mode for gradio." -ForegroundColor Green

# Step 3: Build from spec file
Write-Host "Building exe..." -ForegroundColor Cyan
pyinstaller $specFile
