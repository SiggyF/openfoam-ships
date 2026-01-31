# Running on Delft Blue

Delft Blue is the supercomputer of TU Delft.

## Prerequisites
- Access to Delft Blue via SSH (`tudelft.net` account).
- Container image setup (Apptainer/Singularity).

## Configuration
Typical SLURM configuration for OpenFOAM jobs:
```bash
#!/bin/bash
#SBATCH --job-name=of_ship
#SBATCH --output=log.slurm.%j.out
#SBATCH --error=log.slurm.%j.err
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --partition=compute
#SBATCH --account=innovation  # Replace with your account
```

## Workflow
1. Transfer files to scratch storage (`/scratch/{netid}/`).
2. Build/Pull Apptainer image.
3. Submit using `sbatch scripts/submit_delft_blue.sh`.
