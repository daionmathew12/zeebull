#!/usr/bin/env python3
"""
Lists all actual tables in zeebulldb directly via psycopg2.
"""
import subprocess
result = subprocess.run(
    ['psql', '-U', 'orchid_user', '-d', 'zeebulldb', '-c', r'\dt'],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)
