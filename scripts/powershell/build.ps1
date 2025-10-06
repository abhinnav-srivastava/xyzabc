param(
  [string]$Entry = "app.py",
  [string]$Name = "CodeCritique"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  py -3 -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install pyinstaller

$datas = @(
  "templates;templates",
  "static;static",
  "config;config",
  "checklists;checklists"
) -join " "

pyinstaller --noconfirm --clean --name $Name --onefile --add-data $datas $Entry

Write-Host "Built dist\$Name.exe"
