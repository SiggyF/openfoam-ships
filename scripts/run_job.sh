#!/bin/bash
set -euo pipefail

# Wrapper to submit jobs with configuration from .cluster.env

# Load Configuration
if [ -f ".cluster.env" ]; then
    source .cluster.env
else
    echo "Error: .cluster.env not found."
    exit 1
fi

# Variables
CASE_DIR="${1:-}"

if [ -z "$CASE_DIR" ]; then
    echo "Usage: ./scripts/run_job.sh <case_dir>"
    exit 1
fi

echo "Submitting job for $CASE_DIR..."
echo "  Partition: ${HPC_PARTITION}"
echo "  Account:   ${HPC_ACCOUNT}"

# Submit using sbatch, overriding script defaults with config values
# Note: Command line arguments override #SBATCH directives in the script
ssh "${HPC_HOST:?HPC_HOST not set in .cluster.env}" "cd ${HPC_REMOTE_DIR} && sbatch --partition=${HPC_PARTITION} --account=${HPC_ACCOUNT} scripts/submit_job.sh ${CASE_DIR}"
