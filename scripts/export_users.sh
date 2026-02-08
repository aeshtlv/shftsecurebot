#!/bin/bash
# Export users from old Remnawave panel

set -e

# Configuration
OLD_PANEL="${OLD_PANEL_URL:-https://panel.old-domain.com}"
API_TOKEN="${OLD_API_TOKEN}"

if [ -z "$API_TOKEN" ]; then
    echo "❌ Error: OLD_API_TOKEN environment variable is not set"
    echo "Usage: OLD_API_TOKEN=your_token OLD_PANEL_URL=https://... ./export_users.sh"
    exit 1
fi

echo "📦 Exporting users from: $OLD_PANEL"

# Export users (max 1000, adjust if needed)
curl -X GET "$OLD_PANEL/api/users?start=0&size=1000" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Accept: application/json" \
  -o users_export.json

if [ $? -eq 0 ]; then
    USER_COUNT=$(jq '.response.items | length' users_export.json 2>/dev/null || echo "0")
    echo "✅ Exported $USER_COUNT users to users_export.json"
    
    # Show summary
    echo ""
    echo "📊 Summary:"
    jq -r '.response.items[] | "\(.username) - Expires: \(.expireAt)"' users_export.json 2>/dev/null | head -10
    
    if [ "$USER_COUNT" -ge 1000 ]; then
        echo ""
        echo "⚠️ Warning: Reached export limit (1000 users). You may need to export in batches."
    fi
else
    echo "❌ Failed to export users"
    exit 1
fi

