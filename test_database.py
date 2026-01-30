"""
test_database.py
Script to inspect the database and display all entries.
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path("labeling_data.db")

def display_database():
    """Display all entries in the database."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Display users
    print("\n" + "="*80)
    print("USERS TABLE")
    print("="*80)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    if users:
        for user in users:
            print(f"\nUser ID: {user['user_id']}")
            print(f"  Username: {user['username']}")
            print(f"  Created: {user['created_at']}")
    else:
        print("No users found.")
    
    # Display labels
    print("\n" + "="*80)
    print("LABELS TABLE")
    print("="*80)
    cursor.execute("SELECT * FROM labels ORDER BY user_id, property, labeled_at")
    labels = cursor.fetchall()
    
    if labels:
        for label in labels:
            print(f"\nLabel ID: {label['label_id']}")
            print(f"  User ID: {label['user_id']}")
            print(f"  Property: {label['property']}")
            print(f"  Sentence: {label['sentence'][:80]}...")  # First 80 chars
            print(f"  Label Code: {label['label_code']}")
            print(f"  Subject Words: {label['subject_words']}")
            print(f"  Property Words: {label['property_words']}")
            print(f"  Object Words: {label['object_words']}")
            print(f"  Labeled At: {label['labeled_at']}")
    else:
        print("No labels found.")
    
    # Statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    cursor.execute("SELECT COUNT(*) as count FROM labels")
    total_labels = cursor.fetchone()['count']
    print(f"Total labels: {total_labels}")
    
    cursor.execute("SELECT COUNT(*) as count FROM labels WHERE subject_words IS NOT NULL")
    with_subject = cursor.fetchone()['count']
    print(f"Labels with subject words: {with_subject}")
    
    cursor.execute("SELECT COUNT(*) as count FROM labels WHERE property_words IS NOT NULL")
    with_property = cursor.fetchone()['count']
    print(f"Labels with property words: {with_property}")
    
    cursor.execute("SELECT COUNT(*) as count FROM labels WHERE object_words IS NOT NULL")
    with_object = cursor.fetchone()['count']
    print(f"Labels with object words: {with_object}")
    
    conn.close()
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    display_database()
