#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/migrate_to_repo.sh https://github.com/haohao202603/your-new-repo.git

TARGET_REPO_URL=${1:-}
if [[ -z "$TARGET_REPO_URL" ]]; then
  echo "Usage: bash scripts/migrate_to_repo.sh <target_repo_url>"
  exit 1
fi

WORKDIR=$(mktemp -d)
echo "Using temp dir: $WORKDIR"

git clone "$TARGET_REPO_URL" "$WORKDIR/new_repo"

rsync -av --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  ./ "$WORKDIR/new_repo/"

cd "$WORKDIR/new_repo"

git add .
if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "chore: migrate Patent Insight Tracker files"
git push origin HEAD

echo "Migration completed: $TARGET_REPO_URL"
