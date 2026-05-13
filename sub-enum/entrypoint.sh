#!/bin/sh
# Entrypoint to safely load Docker secrets and run sub-enum from /app/scans
set -eu

# Load secrets placed in /run/secrets by Docker (if any)
if [ -d /run/secrets ]; then
  for secret in /run/secrets/*; do
    [ -f "$secret" ] || continue
    case "$(basename "$secret")" in
      chaos_key)
        export CHAOS_KEY="$(cat "$secret")"
        ;;
      chaos_api_key)
        export CHAOS_API_KEY="$(cat "$secret")"
        ;;
      subfinder_api_key)
        export SUBFINDER_API_KEY="$(cat "$secret")"
        ;;
      *)
        # ignore unknown secret files
        ;;
    esac
  done
fi

# Ensure scans dir exists and is writable
mkdir -p /app/scans
chown -R $(id -u):$(id -g) /app/scans || true

# Execute the main tool. Use exec so signals are forwarded.
exec sub-enum -L /app/targets.txt --workers 4 --yes
