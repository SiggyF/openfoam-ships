#!/bin/bash
set -euo pipefail

# Syncs the current directory to Delft Blue scratch space

# Load Configuration
if [ -f ".cluster.env" ]; then
    source .cluster.env
else
    echo "Error: .cluster.env not found. Copy cluster.env.template and configure it."
    exit 1
fi

# Use variables from env
REMOTE_HOST="${HPC_HOST:?HPC_HOST not set in .cluster.env}"
REMOTE_DIR="${HPC_REMOTE_DIR:?HPC_REMOTE_DIR not set in .cluster.env}"

# Ensure we are in the project root (simple check)
if [ ! -f "scripts/sync_to_hpc.sh" ]; then
    echo "Error: Please run this script from the project root."
    exit 1
fi

echo "Syncing to ${REMOTE_HOST}:${REMOTE_DIR}..."

# Sync current directory to remote
# Excludes: .git, logs, processor (folders), .venv
rsync -avz \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='processor*' \
    --exclude='.venv' \
    --exclude='.vscode' \
    --exclude='.snakemake' \
    --exclude='__pycache__' \
    --exclude='results' \
    "$@" \
    . \
    "${REMOTE_HOST}:${REMOTE_DIR}"

echo "Sync complete."
