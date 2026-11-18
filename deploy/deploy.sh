#!/usr/bin/env bash
# Runs on the VM (called by .github/workflows/deploy.yml, or by hand):
#   LEAFPDF_IMAGE=ghcr.io/jagritvats/leafpdf-website:<sha> bash deploy/deploy.sh
# Pulls the image, restarts the service, waits for /healthz and checks the home page, then removes older
# images of this site.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

IMAGE="${LEAFPDF_IMAGE:-ghcr.io/jagritvats/leafpdf-website:main}"
PORT="${LEAFPDF_LOCAL_PORT:-8120}"

docker network inspect "${TRAEFIK_NETWORK:-synapse-edge}" >/dev/null

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u "${GHCR_USER:?GHCR_USER is required with GHCR_TOKEN}" --password-stdin
fi

{
  echo "LEAFPDF_IMAGE=$IMAGE"
  echo "LEAFPDF_LOCAL_PORT=$PORT"
  [[ -n "${LEAFPDF_HOST_RULE:-}" ]] && echo "LEAFPDF_HOST_RULE=$LEAFPDF_HOST_RULE"
  [[ -n "${LEAFPDF_MEM_LIMIT:-}" ]] && echo "LEAFPDF_MEM_LIMIT=$LEAFPDF_MEM_LIMIT"
  true
} > .env

# No --remove-orphans: the VM is shared, and this stack owns exactly one service.
docker compose pull
docker compose up -d

echo "Waiting for /healthz ..."
ok=""
for _ in $(seq 1 30); do
  if curl -fsS --max-time 3 "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done
if [[ -z "$ok" ]]; then
  echo "leafpdf.org did not answer /healthz in 60 seconds." >&2
  docker compose ps >&2
  docker compose logs --tail 80 >&2
  exit 1
fi
if ! curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/" | grep -q "Edit PDFs"; then
  echo "/healthz answers but the home page does not look right." >&2
  exit 1
fi
echo "leafpdf.org is up on 127.0.0.1:${PORT}."

# Keep the running image and :main; drop older tags of this image so the disk does not fill up.
# Only this site's images: no VM-wide prune -a.
repo="${IMAGE%:*}"
docker images "$repo" --format '{{.Repository}}:{{.Tag}}' \
  | grep -v -x -e "$IMAGE" -e "$repo:main" \
  | xargs -r docker rmi >/dev/null 2>&1 || true
docker image prune -f >/dev/null || true

docker compose ps
