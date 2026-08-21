#!/bin/sh
# Entrypoint: fix ownership of the bind-mounted data volume, then drop to the
# non-root app user.
#
# The image's Dockerfile chowns /app/data to appuser at build time, but
# docker-compose.yml bind-mounts a host directory over that same path
# (`${BACKEND_DATA_DIR:-./backend/data}:/app/data`) — a bind mount replaces
# whatever the image had there, ownership included. If the host directory was
# created by root (the common case: `docker compose up` run via sudo, or the
# directory auto-created by the Docker daemon on first run), appuser has no
# write permission on it at all, and every node that needs to create a
# campaign subdirectory under DATA_DIR fails with
# PermissionError: [Errno 13] Permission denied — exactly the crash this
# script exists to prevent.
#
# Running as root only long enough to chown, then re-executing as appuser via
# `su-exec`/`gosu`-style `su`, is the standard fix for this class of bug
# without requiring every operator to remember to `chown` the host directory
# by hand before every deploy.
set -e

if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/data
    chown -R appuser:appuser /app/data
    exec su -s /bin/sh appuser -c "exec $*"
fi

exec "$@"
