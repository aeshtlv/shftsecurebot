#!/usr/bin/env python3
"""
Import users from old Remnawave panel to new panel.

Usage:
    export NEW_PANEL_URL=https://panel.new-domain.com
    export NEW_API_TOKEN=your_new_token
    export EXTERNAL_SQUAD_UUID=your-squad-uuid
    export INTERNAL_SQUAD_UUIDS=uuid1,uuid2
    python3 import_users.py users_export.json
"""

import json
import sys
import os
from typing import Dict, List
import httpx
from datetime import datetime

def load_config():
    """Load configuration from environment variables."""
    config = {
        'new_panel': os.getenv('NEW_PANEL_URL', 'https://panel.new-domain.com').rstrip('/'),
        'api_token': os.getenv('NEW_API_TOKEN'),
        'external_squad': os.getenv('EXTERNAL_SQUAD_UUID'),
        'internal_squads': os.getenv('INTERNAL_SQUAD_UUIDS', '').split(',') if os.getenv('INTERNAL_SQUAD_UUIDS') else []
    }
    
    if not config['api_token']:
        print("❌ Error: NEW_API_TOKEN environment variable is not set")
        sys.exit(1)
    
    return config

def import_users(export_file: str, config: Dict) -> Dict[str, str]:
    """Import users and return UUID mapping."""
    
    # Load exported users
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        users = data.get('response', {}).get('items', [])
    
    if not users:
        print("❌ No users found in export file")
        sys.exit(1)
    
    print(f"📦 Found {len(users)} users to migrate")
    print(f"🎯 Target panel: {config['new_panel']}")
    print(f"🔑 External squad: {config['external_squad']}")
    print(f"🔑 Internal squads: {', '.join(config['internal_squads']) if config['internal_squads'] else 'None'}")
    print()
    
    # Confirm
    response = input("Continue with migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Migration cancelled")
        sys.exit(0)
    
    uuid_mapping = {}
    
    client = httpx.Client(
        base_url=config['new_panel'],
        headers={
            "Authorization": f"Bearer {config['api_token']}",
            "Content-Type": "application/json"
        },
        timeout=30.0
    )
    
    success = 0
    failed = 0
    
    for i, user in enumerate(users, 1):
        old_uuid = user['uuid']
        username = user['username']
        telegram_id = user.get('telegramId')
        expire_at = user['expireAt']
        traffic_limit = user.get('trafficLimitBytes', 0)
        description = user.get('description', '')
        
        print(f"[{i}/{len(users)}] Migrating: {username} ({old_uuid})", end=' ')
        
        try:
            payload = {
                "username": username,
                "expireAt": expire_at,
                "trafficLimitBytes": traffic_limit,
                "trafficLimitStrategy": "MONTH",
                "description": description or f"Migrated from old panel",
            }
            
            if telegram_id:
                payload["telegramId"] = telegram_id
            
            if config['external_squad']:
                payload["externalSquadUuid"] = config['external_squad']
            
            if config['internal_squads']:
                payload["activeInternalSquads"] = [s for s in config['internal_squads'] if s]
            
            response = client.post("/api/users", json=payload)
            response.raise_for_status()
            
            new_user = response.json().get("response", response.json())
            new_uuid = new_user.get("uuid")
            
            if new_uuid:
                uuid_mapping[old_uuid] = new_uuid
                success += 1
                print(f"✅ → {new_uuid}")
            else:
                failed += 1
                print(f"❌ No UUID returned")
            
        except httpx.HTTPStatusError as e:
            failed += 1
            error_detail = e.response.text[:100] if e.response else str(e)
            print(f"❌ HTTP {e.response.status_code if e.response else '?'}: {error_detail}")
        
        except Exception as e:
            failed += 1
            print(f"❌ {str(e)[:100]}")
    
    client.close()
    
    # Save UUID mapping
    mapping_file = "uuid_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(uuid_mapping, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ Migration complete!")
    print(f"   Success: {success}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(users)}")
    print(f"📄 UUID mapping saved to: {mapping_file}")
    print("=" * 60)
    
    return uuid_mapping

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 import_users.py <users_export.json>")
        print()
        print("Environment variables:")
        print("  NEW_PANEL_URL       - URL of new panel (required)")
        print("  NEW_API_TOKEN       - API token for new panel (required)")
        print("  EXTERNAL_SQUAD_UUID - External squad UUID (optional)")
        print("  INTERNAL_SQUAD_UUIDS - Comma-separated internal squad UUIDs (optional)")
        sys.exit(1)
    
    config = load_config()
    uuid_mapping = import_users(sys.argv[1], config)
    
    print()
    print("Next steps:")
    print("1. Copy uuid_mapping.json to your bot server")
    print("2. Run update_bot_database.py to update UUID mappings")
    print("3. Update .env with new API_BASE_URL and API_TOKEN")
    print("4. Restart the bot")

