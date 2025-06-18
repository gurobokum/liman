#!/usr/bin/env bash

set -euo pipefail

echo "Listing files in sandbox:"
echo $(find . -type f)

echo "Running golangci-lint fmt..."
if ! golangci-lint fmt --diff-colored; then
    echo "❌ Formatting check failed"
    exit 1
fi

echo "Running golangci-lint run..."
if ! golangci-lint run; then
    echo "❌ Linting failed"
    exit 1
fi

echo "✅ All checks passed"
