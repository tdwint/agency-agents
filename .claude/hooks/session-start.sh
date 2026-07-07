#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Ensure scripts are executable
chmod +x "$CLAUDE_PROJECT_DIR"/scripts/*.sh
