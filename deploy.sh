#!/bin/bash

set -e

echo "Checking git status..."
git status

echo "Adding changes..."
git add .

if git diff --cached --quiet; then
  echo "No changes to commit."
else
  echo "Committing changes..."
  git commit -m "${1:-Update project files}"
fi

echo "Pushing to remote..."
git push origin main

echo "Deploy complete."
