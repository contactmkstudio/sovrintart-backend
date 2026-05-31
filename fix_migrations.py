#!/usr/bin/env python
"""
One-time script to fix the Django migration inconsistency.
Run this once: python fix_migrations.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

# Delete the problematic admin.0001_initial record
with connection.cursor() as cursor:
    cursor.execute(
        "DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';"
    )
    print("✓ Deleted admin.0001_initial from django_migrations table")
    print("✓ Database is now ready for fresh migrations")

