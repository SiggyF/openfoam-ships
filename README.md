# OpenFOAM Ships Test Repository

This repository contains validation test cases for OpenFOAM ship hydrodynamics, orchestrated by **Snakemake** and running in **Docker** containers.

## Architecture

- **Dependency Management**: `uv` handles Python dependencies (`snakemake`, `pyvista`, etc.).
- **Configuration**: Test cases are defined in `cases/**/*.toml`.
- **Case Generation**: A Jinja2-based templating system (`prepare_case.py`) generates OpenFOAM `system/` and `constant/` files from base configurations and feature flags (e.g., `six_dof`, `waves`).
- **Execution**: Simulations run in Docker containers (`openfoam/openfoam13-graphical` or `opencfd/openfoam-default:2406`).

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [uv](https://github.com/astral-sh/uv)

### Running the Workflow

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Run All Test Cases**:
   ```bash
   uv run snakemake --cores all
   ```

## Available Test Cases

| Case | Description | Features | Geometry |
| :--- | :--- | :--- | :--- |
| **`empty_tank`** | Basic domain validation. | `interFoam`, `blockMesh` | None (Box) |
| **`wigley`** | Wigley hull (L=1m) benchmark. | `sixDoF`, `snappyHexMesh` | Generated STL |
| **`dtc`** | Duisburg Test Case (L=3.0m). | `sixDoF`, `probes` | `tanker.stl` (proxy) |
| **`kcs`** | KRISO Container Ship (L=7.3m). | `forces`, `probes` | `tanker_kvlcc2.stl` |
| **`series60`** | Series 60 Hull (L=2.4m). | `forces` | `barge.stl` (proxy) |

## Adding a New Case

1. Create a new directory in `cases/`.
2. Add a `case.toml` file:
   ```toml
   [meta]
   name = "my_new_case"
   version = "of13"

   [flags]
   [flags.features]
   six_dof = true
   
   [parameters]
   maxCo = 0.5
   ```
3. Run `snakemake` again.

## Folder Structure

- `cases/`: TOML definitions.
- `config/`: Base OpenFOAM templates (OF13, OF2406) and feature includes.
- `docker/`: Dockerfiles.
- `workflows/`: Snakemake rules and scripts.
