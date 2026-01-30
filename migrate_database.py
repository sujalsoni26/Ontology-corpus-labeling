"""
migrate_database.py
Script to migrate data from the old database schema to the new one,
and populate properties and sentences from the JSON corpus.
"""

import os
import sqlite3
from pathlib import Path
from database import (
    init_database,
    populate_from_json,
    DB_PATH
)

def backup_old_database():
    """Backup the old database if it exists."""
    if DB_PATH.exists():
        backup_path = DB_PATH.with_suffix('.db.backup')
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backed up old database to {backup_path}")
        return True
    return False

def migrate_database():
    """Main migration function."""
    print("=" * 60)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    
    # Step 1: Backup old database
    print("\n[1/4] Backing up old database...")
    if backup_old_database():
        print("     Old database backed up successfully")
    else:
        print("     No existing database found")
    
    # Step 2: Remove old database and create new schema
    print("\n[2/4] Creating new database schema...")
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print("     Removed old database")
    
    init_database()
    print("     ✅ New schema created with tables:")
    print("        - users (id, name, password, sentences_labeled)")
    print("        - properties (id, property_name, domain, range, IRIs)")
    print("        - sentences (id, sentence, property_id, label_count)")
    print("        - labels (id, user_id, sentence_id, label_code, word selections)")
    
    # Step 3: Populate properties and sentences from JSON
    print("\n[3/4] Populating properties and sentences from JSON...")
    json_file = Path("property_text_corpus_full_resolved.json")
    
    if json_file.exists():
        populate_from_json(str(json_file))
        
        # Show statistics
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM properties")
        prop_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sentences")
        sent_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"     ✅ Populated {prop_count} properties")
        print(f"     ✅ Populated {sent_count} sentences")
    else:
        print(f"     ❌ JSON file not found: {json_file}")
        print("     Please ensure property_text_corpus_full_resolved.json is in the current directory")
    
    # Step 4: Migration complete
    print("\n[4/4] Migration complete!")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Update your application code to use the new database schema")
    print("2. Users will need to create new accounts with passwords")
    print("3. Old labels can be migrated if needed (contact admin)")
    print("\nNOTE: The old database is backed up as 'labeling_data.db.backup'")
    print("=" * 60)

if __name__ == "__main__":
    migrate_database()
