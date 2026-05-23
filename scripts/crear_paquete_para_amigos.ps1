$ErrorActionPreference = "Stop"

$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scripts
$distRoot = Join-Path $root "dist"
$package = Join-Path $distRoot "Generala Plus"
$resolvedRoot = (Resolve-Path -LiteralPath $root).Path

if (Test-Path $package) {
    $resolvedPackage = (Resolve-Path -LiteralPath $package).Path
    if (-not $resolvedPackage.StartsWith($resolvedRoot)) {
        throw "Ruta de paquete fuera del proyecto: $resolvedPackage"
    }
    Remove-Item -LiteralPath $package -Recurse -Force
}

New-Item -ItemType Directory -Path $package | Out-Null

$items = @(
    "generala_plus",
    "assets",
    "docs",
    "scripts",
    "requirements.txt",
    "README.md",
    "ejercicio-9.py",
    "Jugar Generala Plus.bat",
    "Host Online Generala Plus.bat",
    "Unirse Online Generala Plus.bat"
)

foreach ($item in $items) {
    $source = Join-Path $root $item
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination $package -Recurse -Force
    }
}

Get-ChildItem -LiteralPath $package -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $package -Recurse -File |
    Where-Object { $_.Extension -in @(".pyc", ".pyo") } |
    Remove-Item -Force

Write-Host "Paquete listo:" $package
Write-Host "Comparte esa carpeta completa. Para jugar, abrir 'Jugar Generala Plus.bat'."
