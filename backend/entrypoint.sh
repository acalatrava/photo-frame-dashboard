#!/bin/sh
# Makes the bind-mounted /data writable for the unprivileged service user, then drops root.
set -e
if [ "$(id -u)" = "0" ]; then
    if [ "$(stat -c %u /data)" != "10001" ]; then
        chown -R 10001:10001 /data
    fi
    exec setpriv --reuid=10001 --regid=10001 --clear-groups "$@"
fi
exec "$@"
