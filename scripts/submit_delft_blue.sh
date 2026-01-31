#!/bin/bash
#SBATCH --job-name=dtc_sweep
#SBATCH --output=logs/slurm_%j.out
#SBATCH --error=logs/slurm_%j.err
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=compute
#SBATCH --account=innovation  # CHANGE THIS

# Load modules
module load 2024r1
module load openfoam

# Variables
CASE_DIR=$1

if [ -z "$CASE_DIR" ]; then
    echo "Usage: sbatch submit_delft_blue.sh <case_dir>"
    exit 1
fi

echo "Running case $CASE_DIR on Delft Blue"
# Command placeholder - adapt to actual Apptainer/Module usage
# apptainer run ...
