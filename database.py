"""
database.py
Database operations for user authentication and label persistence.
Uses SQLite for local development and Hugging Face Spaces deployment.

New Schema:
- users: User accounts with authentication
- properties: Property metadata (name, domain, range, IRIs)
- sentences: All sentences from the corpus
- labels: User label assignments
"""

import sqlite3
import os
import bcrypt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Determine database path based on environment
# HF Spaces: /data directory (persistent storage)
# Local: current directory
DB_PATH = Path("/data/labeling_data.db") if os.path.exists("/data") else Path("labeling_data.db")

def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hash string
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: Plain text password
        hashed: Stored bcrypt hash
        
    Returns:
        True if password matches
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_database():
    """Initialize database schema if tables don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # ==========================================
    # USERS TABLE
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            sentences_labeled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # ==========================================
    # PROPERTIES TABLE
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name TEXT UNIQUE NOT NULL,
            property_domain TEXT,
            property_range TEXT,
            property_iri TEXT,
            domain_iri TEXT,
            range_iri TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ==========================================
    # SENTENCES TABLE
    # ==========================================
    # SQLite TEXT can store up to ~1 billion characters, so no problem with long sentences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence TEXT NOT NULL,
            property_id INTEGER NOT NULL,
            label_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id),
            UNIQUE(sentence, property_id)
        )
    """)
    
    # ==========================================
    # LABELS TABLE (Updated schema)
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sentence_id INTEGER NOT NULL,
            label_code TEXT NOT NULL,
            subject_words TEXT,
            object_words TEXT,
            is_complete BOOLEAN DEFAULT 0,
            labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (sentence_id) REFERENCES sentences(id),
            UNIQUE(user_id, sentence_id)
        )
    """)
    
    # ==========================================
    # INDEXES for performance
    # ==========================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_labels_user 
        ON labels(user_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_labels_sentence 
        ON labels(sentence_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sentences_property 
        ON sentences(property_id)
    """)
    
    conn.commit()
    conn.close()

# ==========================================
# USER OPERATIONS
# ==========================================

def create_user(username: str, password: str) -> int:
    """
    Create a new user with hashed password.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        user_id: ID of the created user
        
    Raises:
        ValueError: If username already exists
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (name, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Username '{username}' already exists")
    
    conn.close()
    return user_id

def create_oauth_user(email: str) -> int:
    """
    Create a new user from OAuth login (Google, etc.) or return existing user ID.
    Uses a placeholder password since OAuth users don't need password authentication.
    
    Args:
        email: User's email from OAuth provider
        
    Returns:
        user_id: ID of the created or existing user
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE name = ?", (email,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return existing["id"]
    
    # Create new user with OAuth placeholder password
    # Use a secure random string that can't be guessed
    oauth_placeholder = f"OAUTH_USER_{hash_password(email + str(datetime.now()))}"
    
    try:
        cursor.execute(
            "INSERT INTO users (name, password) VALUES (?, ?)",
            (email, oauth_placeholder)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Race condition - user was created between check and insert
        cursor.execute("SELECT id FROM users WHERE name = ?", (email,))
        user_id = cursor.fetchone()["id"]
    
    conn.close()
    return user_id

def authenticate_user(username: str, password: str) -> Optional[int]:
    """
    Authenticate a user and return their ID.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        user_id if authentication successful, None otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, password FROM users WHERE name = ?", (username,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row and verify_password(password, row["password"]):
        # Update last login
        update_last_login(row["id"])
        return row["id"]
    return None

def update_last_login(user_id: int):
    """Update user's last login timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()

def get_user(username: str) -> Optional[Dict]:
    """
    Get user information by username.
    
    Args:
        username: Username to look up
        
    Returns:
        User dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, sentences_labeled, created_at, last_login FROM users WHERE name = ?", (username,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user information by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, sentences_labeled, created_at, last_login FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def increment_user_sentences_labeled(user_id: int):
    """Increment the sentences_labeled count for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET sentences_labeled = sentences_labeled + 1 WHERE id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()

# ==========================================
# PROPERTY OPERATIONS
# ==========================================

def create_property(property_name: str, domain: str, range_val: str,
                   property_iri: str = None, domain_iri: str = None, range_iri: str = None) -> int:
    """
    Create a new property entry.
    
    Args:
        property_name: Name of the property
        domain: Domain class
        range_val: Range class
        property_iri: IRI/URL for the property
        domain_iri: IRI/URL for the domain class
        range_iri: IRI/URL for the range class
        
    Returns:
        property_id: ID of the created property
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO properties (property_name, property_domain, property_range, 
                                   property_iri, domain_iri, range_iri)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (property_name, domain, range_val, property_iri, domain_iri, range_iri))
        conn.commit()
        property_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Property already exists, get its ID
        cursor.execute("SELECT id FROM properties WHERE property_name = ?", (property_name,))
        property_id = cursor.fetchone()["id"]
    
    conn.close()
    return property_id

def get_property_by_name(property_name: str) -> Optional[Dict]:
    """Get property information by name."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM properties WHERE property_name = ?", (property_name,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_properties() -> List[Dict]:
    """Get all properties."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM properties ORDER BY property_name")
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]

# ==========================================
# SENTENCE OPERATIONS
# ==========================================

def create_sentence(sentence: str, property_id: int) -> int:
    """
    Create a new sentence entry.
    
    Args:
        sentence: The sentence text
        property_id: ID of the associated property
        
    Returns:
        sentence_id: ID of the created sentence
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO sentences (sentence, property_id)
            VALUES (?, ?)
        """, (sentence, property_id))
        conn.commit()
        sentence_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Sentence already exists for this property, get its ID
        cursor.execute(
            "SELECT id FROM sentences WHERE sentence = ? AND property_id = ?",
            (sentence, property_id)
        )
        sentence_id = cursor.fetchone()["id"]
    
    conn.close()
    return sentence_id

def get_sentences_by_property(property_id: int) -> List[Dict]:
    """Get all sentences for a property."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sentences 
        WHERE property_id = ?
        ORDER BY id
    """, (property_id,))
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]

def get_sentence_by_text(sentence_text: str, property_name: str) -> Optional[Dict]:
    """
    Get sentence information by text and property name.
    
    Args:
        sentence_text: The sentence text to look up
        property_name: Name of the property
        
    Returns:
        Sentence dict with id, sentence, property_id, etc. or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.* FROM sentences s
        JOIN properties p ON s.property_id = p.id
        WHERE s.sentence = ? AND p.property_name = ?
    """, (sentence_text, property_name))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def increment_sentence_label_count(sentence_id: int):
    """Increment the label_count for a sentence."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE sentences SET label_count = label_count + 1 WHERE id = ?",
        (sentence_id,)
    )
    
    conn.commit()
    conn.close()

# ==========================================
# LABEL OPERATIONS
# ==========================================

def save_label(user_id: int, sentence_id: int, label_code: str,
               subject_words: str = None, object_words: str = None, 
               is_complete: bool = False):
    """
    Save or update a label for a specific user and sentence.
    
    Args:
        user_id: ID of the user
        sentence_id: ID of the sentence
        label_code: Label code (pdr, pd, pr, p, n)
        subject_words: Comma-separated word indices for subject
        object_words: Comma-separated word indices for object
        is_complete: Whether this is a complete label assignment
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if label already exists
        cursor.execute(
            "SELECT id, is_complete FROM labels WHERE user_id = ? AND sentence_id = ?",
            (user_id, sentence_id)
        )
        existing = cursor.fetchone()
        
        was_complete = existing["is_complete"] if existing else False
        
        # Use INSERT OR REPLACE to handle updates
        cursor.execute("""
            INSERT OR REPLACE INTO labels 
            (user_id, sentence_id, label_code, subject_words, 
             object_words, is_complete, labeled_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT labeled_at FROM labels WHERE user_id = ? AND sentence_id = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP)
        """, (user_id, sentence_id, label_code, subject_words, 
              object_words, is_complete, user_id, sentence_id))
        
        # If this is a newly completed label, update counters in same transaction
        if is_complete and not was_complete:
            # Increment sentence label count
            cursor.execute(
                "UPDATE sentences SET label_count = label_count + 1 WHERE id = ?",
                (sentence_id,)
            )
            
            # Increment user sentences labeled
            cursor.execute(
                "UPDATE users SET sentences_labeled = sentences_labeled + 1 WHERE id = ?",
                (user_id,)
            )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_sentence_ids_labeled_by_anyone() -> set:
    """
    Return the set of sentence IDs that have at least one label from any user.
    Used for "unlabeled only" mode to show only sentences not yet labeled by anybody.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT sentence_id FROM labels")
    ids = {row["sentence_id"] for row in cursor.fetchall()}
    conn.close()
    return ids


def get_labeled_sentence_stats() -> Tuple[int, int]:
    """
    Return (total_sentences, labeled_by_anyone_count).
    labeled_by_anyone_count = number of distinct sentences that have at least one label from any user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM sentences")
    total = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(DISTINCT sentence_id) as c FROM labels")
    labeled = cursor.fetchone()["c"]
    conn.close()
    return total, labeled

def get_user_labels(user_id: int, property_name: Optional[str] = None) -> Dict[str, Dict[str, Dict]]:
    """
    Get all labels for a user, optionally filtered by property.
    
    Args:
        user_id: ID of the user
        property_name: Optional property name to filter by
        
    Returns:
        Dictionary structured as {property: {sentence: {label_code, subject_words, object_words, ...}}}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if property_name:
        cursor.execute("""
            SELECT p.property_name, s.sentence, l.label_code, l.subject_words, 
                   l.object_words, l.is_complete, l.labeled_at, l.updated_at
            FROM labels l
            JOIN sentences s ON l.sentence_id = s.id
            JOIN properties p ON s.property_id = p.id
            WHERE l.user_id = ? AND p.property_name = ?
        """, (user_id, property_name))
    else:
        cursor.execute("""
            SELECT p.property_name, s.sentence, l.label_code, l.subject_words, 
                   l.object_words, l.is_complete, l.labeled_at, l.updated_at
            FROM labels l
            JOIN sentences s ON l.sentence_id = s.id
            JOIN properties p ON s.property_id = p.id
            WHERE l.user_id = ?
        """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Organize into nested dictionary
    labels = {}
    for row in rows:
        prop = row["property_name"]
        sentence = row["sentence"]
        
        if prop not in labels:
            labels[prop] = {}
        labels[prop][sentence] = {
            "label_code": row["label_code"],
            "subject_words": row["subject_words"],
            "object_words": row["object_words"],
            "is_complete": bool(row["is_complete"]),
            "labeled_at": row["labeled_at"],
            "updated_at": row["updated_at"],
        }
    
    return labels

def get_user_stats(user_id: int) -> Dict[str, int]:
    """
    Get labeling statistics for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with complete_labels count
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get user info
    user = get_user_by_id(user_id)
    
    # Complete labels (only count is_complete = 1)
    cursor.execute("SELECT COUNT(*) as count FROM labels WHERE user_id = ? AND is_complete = 1", (user_id,))
    complete_labels = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "complete_labels": complete_labels,
        "sentences_labeled": user["sentences_labeled"] if user else 0
    }

def get_all_users() -> List[Dict]:
    """
    Get all users in the system.
    
    Returns:
        List of user dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, sentences_labeled, created_at, last_login FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]

def delete_label(user_id: int, sentence_id: int):
    """
    Delete a specific label.
    
    Args:
        user_id: ID of the user
        sentence_id: ID of the sentence
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if it was complete before deleting
    cursor.execute(
        "SELECT is_complete FROM labels WHERE user_id = ? AND sentence_id = ?",
        (user_id, sentence_id)
    )
    row = cursor.fetchone()
    was_complete = row["is_complete"] if row else False
    
    cursor.execute("""
        DELETE FROM labels 
        WHERE user_id = ? AND sentence_id = ?
    """, (user_id, sentence_id))
    
    # If it was complete, decrement counters
    if was_complete:
        cursor.execute(
            "UPDATE sentences SET label_count = label_count - 1 WHERE id = ?",
            (sentence_id,)
        )
        cursor.execute(
            "UPDATE users SET sentences_labeled = sentences_labeled - 1 WHERE id = ?",
            (user_id,)
        )
    
    conn.commit()
    conn.close()

# ==========================================
# DATA MIGRATION / POPULATION
# ==========================================

def populate_from_json(json_file_path: str):
    """
    Populate properties and sentences tables from the JSON corpus file.
    
    Args:
        json_file_path: Path to property_text_corpus_full_resolved.json
    """
    import json
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for property_name, property_data in data.items():
        domain = property_data.get("domain", "")
        range_val = property_data.get("range", "")
        texts = property_data.get("texts", [])
        
        # Get IRIs if available
        property_iri = property_data.get("property_iri")
        domain_iri = property_data.get("domain_iri")
        range_iri = property_data.get("range_iri")
        
        # Create property (or get existing)
        property_id = create_property(property_name, domain, range_val, 
                                      property_iri, domain_iri, range_iri)
        
        # Create sentences
        for sentence in texts:
            create_sentence(sentence, property_id)
    
    conn.close()
    print(f"✅ Populated database with {len(data)} properties")


def auto_populate_database():
    """
    Automatically populate database from JSON file if database is empty.
    This runs on application startup to ensure data is available.
    """
    import os
    from pathlib import Path
    
    # Check if database has any properties
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM properties")
    count = cursor.fetchone()["count"]
    conn.close()
    
    # If database is empty, try to populate from JSON
    if count == 0:
        json_file = Path("property_text_corpus_full_resolved.json")
        
        if json_file.exists():
            print("📊 Database is empty. Auto-populating from JSON file...")
            try:
                populate_from_json(str(json_file))
                print("✅ Database auto-population complete!")
            except Exception as e:
                print(f"⚠️ Failed to auto-populate database: {e}")
                print("   Please run: python migrate_database.py")
        else:
            print("⚠️ Database is empty and JSON file not found.")
            print("   Please ensure property_text_corpus_full_resolved.json exists")
            print("   or run: python migrate_database.py")


# Initialize database on module import
init_database()

# Auto-populate database if empty (first run)
auto_populate_database()
