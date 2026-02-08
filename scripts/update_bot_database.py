#!/usr/bin/env python3
"""
Update bot database with new UUID mappings after panel migration.

Usage:
    python3 update_bot_database.py uuid_mapping.json [path/to/bot_data.db]
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def update_database(mapping_file: str, db_path: str):
    """Update bot database with new UUIDs."""
    
    # Load UUID mapping
    with open(mapping_file, 'r', encoding='utf-8') as f:
        uuid_mapping = json.load(f)
    
    if not uuid_mapping:
        print("❌ Empty UUID mapping file")
        sys.exit(1)
    
    print(f"📦 Loaded {len(uuid_mapping)} UUID mappings")
    
    # Check if database exists
    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    # Create backup
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"💾 Creating backup: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    
    # Connect to database
    print(f"🔗 Connecting to: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get current users with UUID
    cursor.execute("SELECT telegram_id, username, remnawave_user_uuid FROM bot_users WHERE remnawave_user_uuid IS NOT NULL")
    users = cursor.fetchall()
    
    print(f"👥 Found {len(users)} users in bot database with UUID")
    print()
    
    updated = 0
    not_found = 0
    
    for user in users:
        telegram_id = user['telegram_id']
        username = user['username'] or f"user_{telegram_id}"
        old_uuid = user['remnawave_user_uuid']
        
        if old_uuid in uuid_mapping:
            new_uuid = uuid_mapping[old_uuid]
            
            cursor.execute(
                "UPDATE bot_users SET remnawave_user_uuid = ? WHERE telegram_id = ?",
                (new_uuid, telegram_id)
            )
            
            updated += 1
            print(f"✅ Updated {username}: {old_uuid[:8]}... → {new_uuid[:8]}...")
        else:
            not_found += 1
            print(f"⚠️  Not in mapping: {username} ({old_uuid[:8]}...)")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print(f"✅ Database update complete!")
    print(f"   Updated: {updated}")
    print(f"   Not found in mapping: {not_found}")
    print(f"   Total users: {len(users)}")
    print(f"💾 Backup saved to: {backup_path}")
    print("=" * 60)
    
    if not_found > 0:
        print()
        print("⚠️  Warning: Some users were not found in the UUID mapping.")
        print("   These users will need to re-purchase or receive a free trial.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 update_bot_database.py <uuid_mapping.json> [path/to/bot_data.db]")
        print()
        print("Default database path: data/bot_data.db")
        sys.exit(1)
    
    mapping_file = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "data/bot_data.db"
    
    if not Path(mapping_file).exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        sys.exit(1)
    
    # Confirm
    print("⚠️  This will modify your bot database!")
    print(f"   Database: {db_path}")
    print(f"   Mapping: {mapping_file}")
    print()
    response = input("Continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        sys.exit(0)
    
    update_database(mapping_file, db_path)
    
    print()
    print("Next steps:")
    print("1. Update .env with new API_BASE_URL and API_TOKEN")
    print("2. Restart the bot: docker compose down && docker compose up -d")
    print("3. Test with a user: /start → Мой доступ")
    print("4. Send migration notification: /migrate_notify")

