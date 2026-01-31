#!/bin/bash
#SBATCH --job-name=dtc_sweep
#SBATCH --output=logs/slurm_%j.out
#SBATCH --error=logs/slurm_%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --partition=genoa
#SBATCH --account=project_code  # CHANGE THIS

# Load modules
module load 2023
module load OpenFOAM/v2312-foss-2023a

# Variables
CASE_DIR=$1

if [ -z "$CASE_DIR" ]; then
    echo "Usage: sbatch submit_snellius.sh <case_dir>"
    exit 1
fi

echo "Running case $CASE_DIR on Snellius"
# Command placeholder
# mpirun -np $SLURM_NTASKS ...
