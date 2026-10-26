#!/usr/bin/env bash
# Fetch the paper's public data (40 projects, choice judge, test check) at a pinned commit.
# The upstream repository carries no licence, so it is cloned at run time instead of vendored.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HERE/paper-data"
REPO="https://github.com/WenJing95/stale-docs-data.git"
PIN="fa3c8b8"
if [ -d "$DEST/.git" ]; then
  echo "already present: $DEST ($(git -C "$DEST" rev-parse --short HEAD))"
else
  git clone -q "$REPO" "$DEST"
fi
git -C "$DEST" checkout -q "$PIN"
echo "paper data at $DEST ($(git -C "$DEST" rev-parse --short HEAD)); $(ls "$DEST/tasks" | wc -l) tasks"
