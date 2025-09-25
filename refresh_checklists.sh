#!/bin/bash
echo "🔄 Refreshing checklists..."
python scripts/auto_update_checklists.py
if [ $? -eq 0 ]; then
    echo "✅ Checklists refreshed successfully!"
else
    echo "❌ Failed to refresh checklists."
fi
