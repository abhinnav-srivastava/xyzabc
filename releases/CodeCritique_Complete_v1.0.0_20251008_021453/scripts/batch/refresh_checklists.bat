@echo off
echo 🔄 Refreshing checklists...
python scripts\py\auto_update_checklists.py
if %errorlevel% equ 0 (
    echo ✅ Checklists refreshed successfully!
) else (
    echo ❌ Failed to refresh checklists.
)
pause
