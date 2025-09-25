#!/usr/bin/env python3
"""Migration script to add missing columns to boundaries table."""

import sqlite3
import os

def migrate_boundaries_table():
    """Add missing columns to the boundaries table."""
    db_path = os.path.join(os.path.dirname(__file__), "data", "nisto.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Migrating database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if boundaries table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boundaries'")
    if not cursor.fetchone():
        print("Boundaries table doesn't exist. Creating it...")
        # Create the table with all columns
        cursor.execute("""
            CREATE TABLE boundaries (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                label TEXT NOT NULL,
                points TEXT NOT NULL,
                closed INTEGER DEFAULT 1,
                style TEXT NOT NULL,
                created TEXT NOT NULL,
                x REAL,
                y REAL,
                width REAL,
                height REAL,
                config TEXT DEFAULT '{}'
            )
        """)
        conn.commit()
        print("✓ Created boundaries table with all columns")
    else:
        # Check which columns exist
        cursor.execute("PRAGMA table_info(boundaries)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        new_columns = {
            'x': 'REAL',
            'y': 'REAL', 
            'width': 'REAL',
            'height': 'REAL',
            'config': "TEXT DEFAULT '{}'"
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE boundaries ADD COLUMN {column_name} {column_type}")
                    print(f"✓ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"✗ Failed to add column {column_name}: {e}")
        
        conn.commit()
    
    # Verify the final schema
    cursor.execute("PRAGMA table_info(boundaries)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"Final columns: {final_columns}")
    
    conn.close()
    print("✓ Database migration completed")

if __name__ == "__main__":
    migrate_boundaries_table()
