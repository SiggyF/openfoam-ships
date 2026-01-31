#!/bin/bash
#SBATCH --job-name=of_ship
#SBATCH --output=logs/slurm-%j.out
#SBATCH --error=logs/slurm-%j.err
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --partition=generic # Overridden by run_job.sh
#SBATCH --account=generic   # Overridden by run_job.sh

# Note: Partition and Account are hardcoded above for SBATCH parsing.
# To make them dynamic, use a submission wrapper or `sbatch --partition=$HPC_PARTITION ...`

# Load Apptainer (Singularity)
# Available in /usr/bin/apptainer, no module load required

# Variables
CASE_DIR=$1
# Default images (Can be overridden by exporting variables before sbatch, 
# but easier to change here or via sed if needed. For now, removing hardcoded user).
# Ideally, these should be passed in or set in a config file derived container setup.
# Reverting to placeholders that MUST be updated or injected.
SOLVER_IMAGE="${HPC_SOLVER_IMAGE:-docker://username/openfoam-ships-solver:latest}"
EXTRACT_IMAGE="${HPC_EXTRACT_IMAGE:-docker://username/openfoam-ships-extract:latest}"

if [ -z "$CASE_DIR" ]; then
    echo "Usage: sbatch submit_job.sh <case_dir>"
    exit 1
fi

echo "Running case $CASE_DIR on $(hostname)"

# Ensure log directory exists
mkdir -p logs

# Run OpenFOAM Solver
echo "Starting Solver..."
apptainer exec --bind /scratch:/scratch "$SOLVER_IMAGE" /bin/bash -c "source /opt/openfoam2312/etc/bashrc && cd $CASE_DIR && ./Allrun"

# Run Data Extraction
# We use the python-extract image to generate CSVs
echo "Starting Data Extraction..."
# We assume the project root contains scripts/extract_results.py
# Since we cd into $CASE_DIR (e.g. cases/dtc), the script is at ../../scripts/extract_results.py
apptainer exec --bind /scratch:/scratch "$EXTRACT_IMAGE" /bin/bash -c "cd $CASE_DIR && python3 ../../scripts/extract_results.py ."

echo "Job Complete."
