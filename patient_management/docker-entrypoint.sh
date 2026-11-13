#!/bin/sh
set -eu

# The repository currently contains an old, duplicate Alembic root revision.
# c3c75256aed0 is the migration chain used by this application
# (65a376b2b8b0 -> c3c75256aed0), so target it explicitly until the obsolete
# revision is removed in a dedicated migration cleanup.
alembic upgrade c3c75256aed0

exec uvicorn main:app --host 0.0.0.0 --port 8000
