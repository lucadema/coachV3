#!/bin/bash

set -euo pipefail

echo "Checking git status..."
git status

echo "Adding changes..."
git add -A

if git diff --cached --quiet; then
  echo "No changes to commit."
else
  echo "Committing changes..."
  git commit -m "${1:-Update project files}"
fi

echo "Fetching remote..."
git fetch origin

echo "Rebasing onto origin/main..."
git rebase origin/main

if [ -z "$(git rev-list origin/main..HEAD)" ]; then
  echo "Nothing to deploy."
  exit 0
fi

echo "Pushing to remote..."
git push origin main

echo "Deploy complete."
