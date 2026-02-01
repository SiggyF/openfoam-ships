# OpenFOAM Ships Test Repository

This repository contains validation test cases for OpenFOAM ship hydrodynamics, running in **Docker** containers on local machines or HPC clusters.

**Standard Version**: OpenFOAM ESI (v2506)

## Architecture

- **Dependency Management**: `uv` handles Python dependencies.
- **Configuration**: Test cases are defined in `cases/**/*.toml`.
- **Execution**: Simulations run in Docker containers (converted to Apptainer on HPC).
    - **Solver**: `siggyf/openfoam-ships-solver:latest` (OpenFOAM v2506)
    - **Extraction**: `siggyf/openfoam-ships-extract:latest` (Python 3.13)

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) (Local)
- [uv](https://github.com/astral-sh/uv)

### Running Locally

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Run Test Cases**:
   ```bash
   uv run snakemake --cores all
   ```

## HPC Execution

We rely on **Apptainer** (formerly Singularity) to run Docker images on HPC systems.

### 1. Configuration
Copy the template and configure your cluster details (username, partition, etc.):
```bash
cp cluster.env.template .cluster.env
# Edit .cluster.env with your credentials
```

### 2. Workflow
The workflow consists of four steps:

**Step A: Sync Project**
Upload code and configuration to the cluster scratch directory.
```bash
./scripts/sync_to_hpc.sh
```

**Step B: Pull Containers**
Pull Docker images and convert them to `.sif` files on the cluster.
```bash
./scripts/pull_containers.sh
```

**Step C: Run Job**
Submit a simulation job. The wrapper script ensures correct partitions and accounts are used.
```bash
./scripts/run_job.sh cases/dtc_test
```

**Step D: Download Results**
Download only the analysis results (CSV, PNG, logs) back to your local machine.
```bash
./scripts/download_results.sh
```

## Available Test Cases

| Case | Description | Features | Geometry Source |
| :--- | :--- | :--- | :--- |
| **`stokes_wave`** | ESI tutorial-based wave test. | `interFoam`, `waves` | Box |
| **`wigley`** | Wigley hull (L=1m). | `sixDoF`, `snappyHexMesh` | Generated |
| **`dtc`** | Duisburg Test Case (L=3.0m). | `sixDoF`, `probes` | `tanker.stl` |
| **`kcs`** | KRISO Container Ship (L=7.3m). | `forces`, `probes` | `tanker_kvlcc2.stl` |

## Folder Structure

- `cases/`: TOML definitions.
- `docker/`: Dockerfiles for Solver and Extractor.
- `scripts/`: HPC utility scripts (`sync`, `pull`, `run`, `download`).
- `config/`: Base OpenFOAM templates.
- `workflows/`: Snakemake rules.
