"""
database.py
Database operations for user authentication and label persistence.
Uses SQLite for local development and Hugging Face Spaces deployment.
"""

import sqlite3
import os
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

def init_database():
    """Initialize database schema if tables don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create labels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            label_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property TEXT NOT NULL,
            sentence TEXT NOT NULL,
            label_code TEXT NOT NULL,
            subject_words TEXT,
            property_words TEXT,
            object_words TEXT,
            labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, property, sentence)
        )
    """)
    
    # Add new columns to existing tables if they don't exist (migration)
    try:
        cursor.execute("ALTER TABLE labels ADD COLUMN subject_words TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE labels ADD COLUMN property_words TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE labels ADD COLUMN object_words TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_labels_user_property 
        ON labels(user_id, property)
    """)
    
    conn.commit()
    conn.close()

def create_user(username: str) -> int:
    """
    Create a new user or return existing user ID.
    
    Args:
        username: Username to create/retrieve
        
    Returns:
        user_id: ID of the created or existing user
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # User already exists, get their ID
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()["user_id"]
    
    conn.close()
    return user_id

def get_user(username: str) -> Optional[Dict]:
    """
    Get user information by username.
    
    Args:
        username: Username to look up
        
    Returns:
        User dict with user_id, username, created_at or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def save_label(user_id: int, property_name: str, sentence: str, label_code: str,
               subject_words: str = None, property_words: str = None, object_words: str = None):
    """
    Save or update a label for a specific user, property, and sentence.
    
    Args:
        user_id: ID of the user
        property_name: Property name
        sentence: Sentence text
        label_code: Label code (pdr, pd, pr, p, n)
        subject_words: Comma-separated word indices for subject (e.g., "0,1,2")
        property_words: Comma-separated word indices for property
        object_words: Comma-separated word indices for object
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use INSERT OR REPLACE to handle updates
    cursor.execute("""
        INSERT OR REPLACE INTO labels 
        (user_id, property, sentence, label_code, subject_words, property_words, object_words, labeled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, property_name, sentence, label_code, subject_words, property_words, object_words))
    
    conn.commit()
    conn.close()

def get_user_labels(user_id: int, property_name: Optional[str] = None) -> Dict[str, Dict[str, Dict]]:
    """
    Get all labels for a user, optionally filtered by property.
    
    Args:
        user_id: ID of the user
        property_name: Optional property name to filter by
        
    Returns:
        Dictionary structured as {property: {sentence: {label_code, subject_words, property_words, object_words}}}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if property_name:
        cursor.execute("""
            SELECT property, sentence, label_code, subject_words, property_words, object_words
            FROM labels 
            WHERE user_id = ? AND property = ?
        """, (user_id, property_name))
    else:
        cursor.execute("""
            SELECT property, sentence, label_code, subject_words, property_words, object_words
            FROM labels 
            WHERE user_id = ?
        """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Organize into nested dictionary
    labels = {}
    for row in rows:
        prop = row["property"]
        sentence = row["sentence"]
        
        if prop not in labels:
            labels[prop] = {}
        labels[prop][sentence] = {
            "label_code": row["label_code"],
            "subject_words": row["subject_words"],
            "property_words": row["property_words"],
            "object_words": row["object_words"]
        }
    
    return labels

def get_user_stats(user_id: int) -> Dict[str, int]:
    """
    Get labeling statistics for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with total_labels, properties_count, etc.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total labels
    cursor.execute("SELECT COUNT(*) as count FROM labels WHERE user_id = ?", (user_id,))
    total_labels = cursor.fetchone()["count"]
    
    # Number of unique properties labeled
    cursor.execute("""
        SELECT COUNT(DISTINCT property) as count 
        FROM labels 
        WHERE user_id = ?
    """, (user_id,))
    properties_count = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_labels": total_labels,
        "properties_count": properties_count
    }

def get_all_users() -> List[Dict]:
    """
    Get all users in the system.
    
    Returns:
        List of user dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]

def delete_label(user_id: int, property_name: str, sentence: str):
    """
    Delete a specific label.
    
    Args:
        user_id: ID of the user
        property_name: Property name
        sentence: Sentence text
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM labels 
        WHERE user_id = ? AND property = ? AND sentence = ?
    """, (user_id, property_name, sentence))
    
    conn.commit()
    conn.close()

# Initialize database on module import
init_database()
