#!/bin/bash
#SBATCH --job-name=of_ship
#SBATCH --output=logs/slurm-%j.out
#SBATCH --error=logs/slurm-%j.err
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem-per-cpu=2G
#SBATCH --partition=generic # Overridden by run_job.sh
#SBATCH --account=generic   # Overridden by run_job.sh

# Note: Partition and Account are hardcoded above for SBATCH parsing.
# To make them dynamic, use a submission wrapper or `sbatch --partition=$HPC_PARTITION ...`

# Load Apptainer (Singularity)
# Available in /usr/bin/apptainer, no module load required

# Variables
CASE_DIR=$1
# Default images (Expecting SIF files in project root, or passed via env)
# We default to local SIF files because compute nodes cannot pull from Docker Hub
SOLVER_IMAGE="${HPC_SOLVER_IMAGE:-solver.sif}"
EXTRACT_IMAGE="${HPC_EXTRACT_IMAGE:-extract.sif}"

if [ -z "$CASE_DIR" ]; then
    echo "Usage: sbatch submit_job.sh <case_dir>"
    exit 1
fi

echo "Running case $CASE_DIR on $(hostname)"

# Ensure log directory exists
mkdir -p logs

# Run OpenFOAM Solver
echo "Starting Solver..."
apptainer exec --bind /scratch:/scratch "$SOLVER_IMAGE" /bin/bash -c "source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd $CASE_DIR && ./Allrun"

# Run Data Extraction
# We use the python-extract image to generate CSVs
echo "Starting Data Extraction..."
# We assume the project root contains scripts/extract_results.py
# Since we cd into $CASE_DIR (e.g. cases/dtc), the script is at ../../scripts/extract_results.py
apptainer exec --bind /scratch:/scratch "$EXTRACT_IMAGE" /bin/bash -c "cd $CASE_DIR && python3 ../../scripts/extract_results.py ."

echo "Job Complete."
