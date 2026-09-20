#!/bin/sh
# Builds /etc/nginx/.htpasswd from env vars at container start, so the
# actual username/password never has to be committed to git — they live
# only in the .env file on the NAS (which is gitignored).
set -e

: "${BASIC_AUTH_USER:?Set BASIC_AUTH_USER in your .env file}"
: "${BASIC_AUTH_PASSWORD:?Set BASIC_AUTH_PASSWORD in your .env file}"

htpasswd -bc /etc/nginx/.htpasswd "$BASIC_AUTH_USER" "$BASIC_AUTH_PASSWORD"

exec nginx -g "daemon off;"
