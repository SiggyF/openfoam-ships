#!/bin/bash
set -euo pipefail

# Wrapper to pull containers on the cluster
# USAGE: ./scripts/pull_containers.sh

# Load Configuration
if [ -f ".cluster.env" ]; then
    source .cluster.env
else
    echo "Error: .cluster.env not found."
    exit 1
fi

echo "Pulling containers on ${HPC_HOST:-your_cluster}..."

# We use ssh to run the pull commands on the cluster
# We use single long command string with double quotes for local expansion
# Added robust quoting and removed module load
REMOTE_CMD="cd ${HPC_REMOTE_DIR} && \
echo 'Pulling Solver...' && \
apptainer pull --force solver.sif ${HPC_SOLVER_IMAGE} && \
echo 'Pulling Extractor...' && \
apptainer pull --force extract.sif ${HPC_EXTRACT_IMAGE}"

ssh "${HPC_HOST:?HPC_HOST not set}" "$REMOTE_CMD"

echo "Containers pulled successfully to ${HPC_REMOTE_DIR}/solver.sif and extract.sif"
