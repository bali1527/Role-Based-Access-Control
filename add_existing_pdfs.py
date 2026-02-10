"""
Script to add existing PDF files to the database.
Use this if you have PDF files in uploads/pdfs/ but no database records.
"""

import os
import sqlite3
from pathlib import Path

# Database path
DB_PATH = r'c:\Users\User\Desktop\RBAC\rbac.db'
UPLOADS_DIR = r'c:\Users\User\Desktop\RBAC\uploads\pdfs'

# Connect to database
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Get all PDF files in uploads/pdfs/
pdf_files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf')]

print(f"Found {len(pdf_files)} PDF files in {UPLOADS_DIR}")

# Get a user (super_admin user should exist from /init)
cursor.execute("SELECT id FROM users WHERE username = 'superadmin1'")
user_result = cursor.fetchone()

if not user_result:
    print("ERROR: No user found. Please run /init endpoint first.")
    db.close()
    exit(1)

uploader_id = user_result[0]
print(f"Using uploader_id: {uploader_id}")

# Add each PDF to database
for filename in pdf_files:
    # Extract title from filename (remove UUID prefix)
    title = filename.split('_', 1)[1] if '_' in filename else filename
    title = title.replace('.pdf', '')
    
    # Check if already exists
    cursor.execute("SELECT id FROM pdfs WHERE filename = ?", (filename,))
    if cursor.fetchone():
        print(f"  ⚠️  {filename} already in database, skipping...")
        continue
    
    # Insert into database
    cursor.execute(
        "INSERT INTO pdfs (title, filename, uploaded_by) VALUES (?, ?, ?)",
        (title, filename, uploader_id)
    )
    print(f"  ✓ Added: {filename} -> {title}")

db.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM pdfs")
count = cursor.fetchone()[0]
print(f"\nTotal PDFs in database: {count}")

db.close()
print("Done!")
