$ErrorActionPreference = "Stop"

$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scripts
$packageScript = Join-Path $scripts "crear_paquete_para_amigos.ps1"
$releaseDir = Join-Path $root "release"
$versionLine = Select-String -Path (Join-Path $root "generala_plus\version.py") -Pattern 'VERSION\s*=\s*"([^"]+)"' | Select-Object -First 1
$version = $versionLine.Matches[0].Groups[1].Value
$packageDir = Join-Path $root "dist\Generala Plus v$version"
$zipPath = Join-Path $releaseDir "Generala-Plus-v$version-windows.zip"

& $packageScript

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath -Force

Write-Host "Release ZIP listo:" $zipPath
