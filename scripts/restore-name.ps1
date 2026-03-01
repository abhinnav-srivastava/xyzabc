# Restore app name after download. Run from project root.
# Usage: .\scripts\restore-name.ps1 -Name "YourApp"
# Or use setup-dev: .\scripts\setup-dev.ps1 -Name "YourApp"

param(
    [Parameter(Mandatory=$true)]
    [string]$Name
)

$Id = ($Name -replace '\s', '').ToLower()
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Restoring app name to: $Name (id: $Id)" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

$files = Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.py,*.js,*.json,*.html,*.md,*.yml,*.sh,*.ps1,*.bat |
    Where-Object { $_.FullName -notmatch '\\node_modules\\|\\\.git\\|\\dist|\\build' }

$count = 0
foreach ($f in $files) {
    $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    $orig = $content
    $content = $content -replace 'CodeReview', $Name
    $content = $content -replace 'codereview', $Id
    if ($content -ne $orig) {
        Set-Content $f.FullName -Value $content -NoNewline
        $count++
        Write-Host "  $($f.FullName.Replace($ProjectRoot, '.'))"
    }
}

Write-Host ""
Write-Host "Done. Updated $count files." -ForegroundColor Green
