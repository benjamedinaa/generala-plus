$ErrorActionPreference = "Stop"

$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scripts
$packageScript = Join-Path $scripts "crear_paquete_para_amigos.ps1"
$releaseDir = Join-Path $root "release"
$packageDir = Join-Path $root "dist\Generala Plus"
$zipPath = Join-Path $releaseDir "Generala-Plus-windows.zip"

& $packageScript

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath -Force

Write-Host "Release ZIP listo:" $zipPath
