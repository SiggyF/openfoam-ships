# OpenFOAM Docker Images

We use **OpenFOAM ESI (v2506)** as the standard for this project.

## Available Images

### 1. Solver (ESI v2506)
*   **Image Name**: `siggyf/openfoam-ships-solver:latest`
*   **Dockerfile**: `docker/openfoam2506.Dockerfile`
*   **Base**: `opencfd/openfoam-default:2506`
*   **Usage**: Runs the OpenFOAM solver (mesh, solve).
*   **Execution**:
    ```bash
    apptainer exec docker://siggyf/openfoam-ships-solver:latest ./Allrun
    ```

### 2. Extractor (Python)
*   **Image Name**: `siggyf/openfoam-ships-extract:latest`
*   **Dockerfile**: `docker/python-extract.Dockerfile`
*   **Base**: `python:3.11-slim`
*   **Usage**: Runs post-processing and data extraction (Python/PyVista).
*   **Execution**:
    ```bash
    apptainer exec docker://siggyf/openfoam-ships-extract:latest python3 extract_data.py
    ```

## Building Images
To build and push the images (requires Docker login):
```bash
# Solver
docker build -t siggyf/openfoam-ships-solver:latest -f docker/openfoam2506.Dockerfile .
docker push siggyf/openfoam-ships-solver:latest

# Extractor
docker build -t siggyf/openfoam-ships-extract:latest -f docker/python-extract.Dockerfile .
docker push siggyf/openfoam-ships-extract:latest
```

## Geometry Storage
*   **Compression**: Always compress STL files (`gzip hull.stl`).
*   **Location**: Store in `constant/geometry`.
