$ErrorActionPreference = "Stop"

$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scripts
$icon = Join-Path $root "assets\generala_plus_icon.ico"
$entry = Join-Path $root "ejercicio-9.py"

Set-Location $root

python -m pip install -r requirements.txt
python -m pip install pyinstaller

$args = @(
    "--noconfirm",
    "--windowed",
    "--name", "Generala Plus",
    "--add-data", "assets;assets",
    "--add-data", "docs;docs"
)

if (Test-Path $icon) {
    $args += @("--icon", $icon)
}

$args += $entry

python -m PyInstaller @args

Write-Host "EXE listo en dist\Generala Plus\Generala Plus.exe"
