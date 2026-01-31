#!/bin/bash
set -euo pipefail

# Wrapper to download results from the cluster
# USAGE: ./scripts/download_results.sh

# Load Configuration
if [ -f ".cluster.env" ]; then
    source .cluster.env
else
    echo "Error: .cluster.env not found."
    exit 1
fi

echo "Downloading results from ${HPC_HOST:-delftblue}..."

# Download only CSV and PNG files from the remote directory
# We exclude everything else to save bandwidth
rsync -avz --include='OPTIONS' --include='*/' --include='*.csv' --include='*.png' --exclude='*' \
    "${HPC_HOST:?HPC_HOST not set}:${HPC_REMOTE_DIR}/" \
    results/

echo "Results downloaded to local results/ directory."
