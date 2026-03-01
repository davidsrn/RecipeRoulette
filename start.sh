#!/bin/sh
set -e

echo "=== RecipeRoulette startup ==="
echo "DB_PATH: ${DB_PATH:-/data/recipes.db}"
echo "PORT:    ${PORT:-8000}"

# If the DB doesn't exist yet, initialise it and import the CSV
DB_FILE="${DB_PATH:-/data/recipes.db}"
echo "Checking for DB at: $DB_FILE"
ls -lah "$(dirname $DB_FILE)" 2>/dev/null || echo "(data dir missing)"
if [ ! -f "$DB_FILE" ]; then
    echo "First run — initialising database and importing CSV..."
    python import_csv.py
else
    SIZE=$(stat -c%s "$DB_FILE" 2>/dev/null || stat -f%z "$DB_FILE" 2>/dev/null || echo "unknown")
    echo "DB exists, size=${SIZE} bytes — skipping import"
fi

# Start the Telegram bot in the background
echo "Starting Telegram bot..."
python bot.py &
BOT_PID=$!

# Start the web server in the foreground (Railway health-checks need this)
echo "Starting web server on port ${PORT:-8000}..."
exec uvicorn app:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --log-level info
