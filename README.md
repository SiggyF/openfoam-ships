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

| Case | Description | Features | Geometry Source | Reference |
| :--- | :--- | :--- | :--- | :--- |
| **`empty_tank`** | Basic domain validation. | `interFoam`, `blockMesh` | None (Box) | N/A |
| **`wigley`** | Wigley hull (L=1m). | `sixDoF`, `snappyHexMesh` | Generated (Math) | [Wigley (1942)](https://doi.org/10.5957/attc-1942-016) |
| **`dtc`** | Duisburg Test Case (L=3.0m). | `sixDoF`, `probes` | `tanker.stl` (Proxy*) | [el Moctar et al. (2012)](https://doi.org/10.1080/09377255.2012.701315) |
| **`kcs`** | KRISO Container Ship (L=7.3m). | `forces`, `probes` | `tanker_kvlcc2.stl` (Proxy*) | [SIMMAN 2008](http://www.simman2008.dk/KCS/kcs_geometry.htm) |
| **`series60`** | Series 60 Hull (L=2.4m). | `forces` | `barge.stl` (Proxy*) | [Todd (1963)](https://apps.dtic.mil/sti/citations/AD0430632) |
| **`DTCHullWave`** | Unmodified tutorial case. | `interFoam`, `wave` | `DTCHull.stl` | OpenFOAM Tutorial |

*> **Note on Geometry Proxies**: Due to licensing/distribution limits, some cases currently use placeholder geometries from `jax-vessels` that approximate the hull form for workflow validation.*

### Standard Tutorials (Benchmarks)
We benchmark standard OpenFOAM tutorials for both Foundation (v11/v13) and ESI (v2406) versions to evaluate runtime performance.

For detailed performance results and container usage, see [docker/README.md](docker/README.md).

**Key Benchmarks:**
*   **Foundation (v13)**: `DTCHull`, `DTCHullMoving`, `DTCHullWave`
*   **ESI (v2406)**: `DTCHull`, `DTCHullMoving`, `rigidBodyHull`


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
