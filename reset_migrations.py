"""
Script to reset migration history by deleting the database and clearing migration records.
Run this script before running migrations.
"""
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection

# Delete the database file
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted database file: {db_path}")
else:
    print(f"Database file not found: {db_path}")

print("Database reset complete. Now run: python manage.py migrate")

