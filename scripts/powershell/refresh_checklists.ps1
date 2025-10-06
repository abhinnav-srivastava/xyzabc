Write-Host "🔄 Refreshing checklists..." -ForegroundColor Blue
python scripts\py\auto_update_checklists.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Checklists refreshed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to refresh checklists." -ForegroundColor Red
}
Read-Host "Press Enter to continue"
