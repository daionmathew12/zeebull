#!/bin/bash
# Extract DATABASE_URL properly
# Note: output of read_url.py is "URL: DATABASE_URL=value"

# 1. Run read_url.py and capture output
OUTPUT=$(python3 read_url.py)
echo "Raw output: $OUTPUT"

# 2. Grep the line
LINE=$(echo "$OUTPUT" | grep "URL: DATABASE_URL=")
echo "Grep line: $LINE"

# 3. Cut value (after first =)
VAL=$(echo "$LINE" | cut -d'=' -f2-)
echo "Extracted URL: $VAL"

# 4. Export and run
export DATABASE_URL="$VAL"
echo "Running migration..."
python3 create_salary_payments.py
