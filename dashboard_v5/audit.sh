#!/usr/bin/env bash
set -euo pipefail

API_C=mcmv-v5-api
FE_C=mcmv-v5-frontend
OUT=./_container_audit
rm -rf "$OUT" && mkdir -p "$OUT"/{api,frontend,nginx,envs,logs,diffs}

echo "==> Inspect mounts"
docker inspect "$API_C" --format '{{json .Mounts}}' | jq '.' > "$OUT/api_mounts.json" 2>/dev/null || docker inspect "$API_C" --format '{{json .Mounts}}' > "$OUT/api_mounts.json"
docker inspect "$FE_C"  --format '{{json .Mounts}}' | jq '.' > "$OUT/frontend_mounts.json" 2>/dev/null || docker inspect "$FE_C" --format '{{json .Mounts}}' > "$OUT/frontend_mounts.json"

echo "==> Snapshot API filesystem"
# Adjust if app path differs
docker cp "$API_C":/app "$OUT/api/app"
# Common env locations
docker exec "$API_C" printenv | sort > "$OUT/envs/api.env.dump"
docker exec "$API_C" bash -lc 'ls -la /app || true; find /app -maxdepth 3 -type f | wc -l' > "$OUT/api_tree.txt"

echo "==> Snapshot Frontend filesystem"
# Nginx default static root for multi-stage builds
docker cp "$FE_C":/usr/share/nginx/html "$OUT/frontend/html"
# nginx conf (site + main)
docker cp "$FE_C":/etc/nginx/nginx.conf "$OUT/nginx/nginx.conf" || true
docker cp "$FE_C":/etc/nginx/conf.d "$OUT/nginx/conf.d" || true
docker exec "$FE_C" printenv | sort > "$OUT/envs/frontend.env.dump"
docker exec "$FE_C" sh -lc 'ls -la /usr/share/nginx/html | sed -n "1,120p"' > "$OUT/frontend_tree.txt"

echo "==> Capture live dependency locks"
docker exec "$API_C" python -V            > "$OUT/api/python_version.txt" || true
docker exec "$API_C" pip freeze --disable-pip-version-check > "$OUT/api/pip_freeze.txt" || true
docker exec "$FE_C"  sh -lc 'node -v && npm -v' > "$OUT/frontend/node_npm_versions.txt" || true
# "npm ls --prod" can be verbose; include anyway
docker exec "$FE_C"  sh -lc 'cd /usr/share/nginx/html >/dev/null 2>&1 || true; true' # placeholder
# If the FE container still has /app before build stage, capture package.json/lock:
docker exec "$FE_C"  sh -lc 'test -d /app && (cd /app && [ -f package.json ] && cat package.json) || true' > "$OUT/frontend/package.json.in-image" 
docker exec "$FE_C"  sh -lc 'test -d /app && (cd /app && [ -f package-lock.json ] && cat package-lock.json) || true' > "$OUT/frontend/package-lock.json.in-image"

echo "==> Generate diffs (local → container)"
# Adjust these local paths to your repo layout:
LOC_API=./backend
LOC_FE_BUILD=./frontend/dist
LOC_NGX=./nginx

mkdir -p "$OUT/diffs"
diff -ruN "$LOC_API"      "$OUT/api/app"                 > "$OUT/diffs/backend.diff"  || true
diff -ruN "$LOC_FE_BUILD" "$OUT/frontend/html"           > "$OUT/diffs/frontend.diff" || true
diff -ruN "$LOC_NGX"      "$OUT/nginx"                   > "$OUT/diffs/nginx.diff"    || true

echo "==> Summary"
{
    echo "API mounts:"; jq -r '.[].Destination + " <= " + .[].Source?' "$OUT/api_mounts.json" 2>/dev/null || cat "$OUT/api_mounts.json" | grep -o '"Destination":"[^"]*"' | cut -d'"' -f4 || true
    echo
    echo "FRONTEND mounts:"; jq -r '.[].Destination + " <= " + .[].Source?' "$OUT/frontend_mounts.json" 2>/dev/null || cat "$OUT/frontend_mounts.json" | grep -o '"Destination":"[^"]*"' | cut -d'"' -f4 || true
    echo
    echo "Backend diff:   $OUT/diffs/backend.diff"
    echo "Frontend diff:  $OUT/diffs/frontend.diff"
    echo "Nginx diff:     $OUT/diffs/nginx.diff"
    echo
    echo "If diffs are non-empty, copy missing files back into the repo paths above."
} | tee "$OUT/summary.txt"

echo "Done. See $OUT/"