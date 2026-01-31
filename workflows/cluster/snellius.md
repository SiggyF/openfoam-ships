# Running on SURF Snellius

Snellius is the Dutch national supercomputer managed by SURF.

## Prerequisites
- Access to Snellius via SSH.
- Budget/Project code (e.g., `vuw01`).

## Configuration
Typical SLURM configuration for OpenFOAM jobs:
```bash
#!/bin/bash
#SBATCH --job-name=of_ship
#SBATCH --output=log.slurm.%j.out
#SBATCH --error=log.slurm.%j.err
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=128
#SBATCH --partition=genoa
```

## Workflow
1. Transfer files to project space.
2. Build/Pull Apptainer image.
3. Submit using `sbatch scripts/submit_snellius.sh`.
