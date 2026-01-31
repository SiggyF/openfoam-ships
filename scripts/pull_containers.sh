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

echo "Pulling containers on ${HPC_HOST:-delftblue}..."

# We use ssh to run the pull commands on the cluster
# This requires apptainer to be in path (verified in profile)
ssh "${HPC_HOST:?HPC_HOST not set}" "cd ${HPC_REMOTE_DIR} && \
    module load apptainer || true && \
    echo 'Pulling Solver...' && \
    apptainer pull --force solver.sif ${HPC_SOLVER_IMAGE} && \
    echo 'Pulling Extractor...' && \
    apptainer pull --force extract.sif ${HPC_EXTRACT_IMAGE}"

echo "Containers pulled successfully to ${HPC_REMOTE_DIR}/solver.sif and extract.sif"
