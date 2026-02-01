#!/bin/sh
set -e

proxy_headers_value=$(printf '%s' "${PROXY_HEADERS:-true}" | tr '[:upper:]' '[:lower:]')

set -- uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-1235}"

case "${proxy_headers_value}" in
  false|0|no|off)
    ;;
  *)
    set -- "$@" --proxy-headers --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}"
    ;;
esac

exec "$@"
