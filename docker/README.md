# OpenFOAM Docker Images

This directory contains Dockerfiles and documentation for the OpenFOAM images used in this project.

## Images

### 1. Foundation (v13)
*   **Dockerfile**: `openfoam13.Dockerfile`
*   **Base Image**: `openfoam/openfoam13-graphical:latest`
*   **Description**: Targeted for OpenFOAM Foundation version 13.
*   **Usage**: Used for standard tutorials and main development.
*   **User**: Runs as `openfoam` (uid=1000) by default. Environment is auto-loaded.

### 2. ESI (v2406)
*   **Dockerfile**: `openfoam2406.Dockerfile`
*   **Base Image**: `opencfd/openfoam-default:2406`
*   **Description**: Targeted for OpenFOAM ESI version v2406.
*   **Usage**: Used for ESI-specific tutorials and benchmarks.
*   **Particularities**:
    *   **Default User**: Runs as `root` (uid=0) by default.
    *   **Environment**: You must explicitly source the bashrc file: `source /usr/lib/openfoam/openfoam2406/etc/bashrc`.
    *   **Non-Root Execution**: Can run as `ubuntu` (uid=1000) but requires permission management for mounted volumes.

## Geometry Storage Policy

To minimize repository size, we follow these guidelines for geometry files:
1.  **Compression**: Always compress STL files using `gzip` (e.g., `hull.stl.gz`).
2.  **Location**: specific geometry files should be stored in `constant/geometry` within the tutorial directory.
3.  **Runtime**: The `Allrun` script (or `Allmesh`) must handle copying or uncompressing these files to `constant/triSurface` as needed by `snappyHexMesh`.
4.  **Exclusion**: Do not commit uncompressed STLs or generated mesh files (`polyMesh`, `extendedFeatureEdgeMesh`, etc.) to the repository.

## Performance Benchmarks

The following table summarizes the runtime performance of standard tutorials on a reference machine (e.g., Apple M1/M2/M3). Simulations were run for **5 seconds** of simulation time.

| Tutorial Name | OpenFOAM Version | Simulation Time | Wall Clock Time | Cores | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DTCHull** | ESI (v2406) | 5s | *Pending* | 1 | |
| **DTCHull** | Foundation (v13) | 5s | ~755s | 8 | |
| **DTCHullMoving** | ESI (v2406) | 5s | *Stopped* | 1 | |
| **DTCHullMoving** | Foundation (v13) | 5s | *Incomplete* | 8 | Slow |
| **rigidBodyHull** | ESI (v2406) | 5s | *Pending* | 1 | |
| **DTCHullWave** | Foundation (v13) | 5s | *Pending* | 8 | |

## Running Containers

### ESI (v2406)
```bash
docker run --rm \
  -v $(pwd)/tutorials/esi/DTCHull:/data \
  -w /data \
  opencfd/openfoam-default:2406 \
  bash -c 'source /usr/lib/openfoam/openfoam2406/etc/bashrc && ./Allrun'
```

### Foundation (v13)
```bash
docker run --rm \
  -v $(pwd)/tutorials/of13/DTCHull:/home/openfoam/run/case \
  -w /home/openfoam/run/case \
  openfoam/openfoam13-graphical:latest \
  ./Allrun
```
