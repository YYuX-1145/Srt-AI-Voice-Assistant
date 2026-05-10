Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSCommandPath
Set-Location $repoRoot

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$rootReadmePath = Join-Path $repoRoot "README.md"
$englishReadmePath = Join-Path $repoRoot "docs\en_US\README.md"

$readmeLines = [System.IO.File]::ReadAllLines($rootReadmePath, $utf8NoBom)
if ($readmeLines.Length -gt 0) {
    $readmeLines[0] = $readmeLines[0].TrimStart([char]0xFEFF)
}
if ($readmeLines.Length -ge 2) {
    $readmeLines = @($readmeLines[0]) + $readmeLines[2..($readmeLines.Length - 1)]
}
[System.IO.File]::WriteAllLines($englishReadmePath, $readmeLines, $utf8NoBom)

Get-ChildItem -LiteralPath (Join-Path $repoRoot "docs") -Recurse -File -Filter "*.md" |
    Sort-Object FullName |
    ForEach-Object {
        $language = Split-Path -Path $_.DirectoryName -Leaf
        $name = $_.BaseName
        $targetDir = Join-Path $repoRoot "Sava_Utils\man\$language"
        $targetPath = Join-Path $targetDir "$name.py"

        if (-not (Test-Path -LiteralPath $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir | Out-Null
        }

        $markdown = [System.IO.File]::ReadAllText($_.FullName, $utf8NoBom).TrimStart([char]0xFEFF)
        $pythonContent = $name + " = r`"`"`"`n" + $markdown
        if (-not $pythonContent.EndsWith("`n")) {
            $pythonContent += "`n"
        }
        $pythonContent += "`"`"`"`n"

        [System.IO.File]::WriteAllText($targetPath, $pythonContent, $utf8NoBom)
    }
