#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    attempts="${MIGRATION_RETRIES:-30}"
    delay="${MIGRATION_RETRY_DELAY:-2}"
    current=1

    while ! python -m flask --app app:create_app db upgrade; do
        if [ "$current" -ge "$attempts" ]; then
            echo "Database migration failed after $attempts attempts." >&2
            exit 1
        fi

        echo "Database is not ready yet. Retrying migration ($current/$attempts)..." >&2
        current=$((current + 1))
        sleep "$delay"
    done
fi

exec "$@"
