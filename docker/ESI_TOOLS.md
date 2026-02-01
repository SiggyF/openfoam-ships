# OpenFOAM ESI Tools & Compatibility

This project uses the OpenFOAM ESI version (e.g., v2406, v2506), which differs from the OpenFOAM Foundation (org) version.

## Key Differences

### Solver Executables
*   **Foundation (org)**: Often uses `foamRun` as a generic solver wrapper in newer versions.
*   **ESI (com)**: Relies on specific application solvers:
    *   `interFoam`: Multiphase flow (VOF).
    *   `simpleFoam`: Steady-state incompressible.
    *   `pimpleFoam`: Transient incompressible.
    *   `overInterDyMFoam`: Overset mesh + VOF (moved to `overInterDyMFoam` or consolidated).

### Utilities
*   **Feature Extraction**:
    *   **Foundation**: `surfaceFeatures`
    *   **ESI**: `surfaceFeatureExtract` (reads from `system/surfaceFeatureExtractDict`)

### Environment
*   **Bashrc Path**:
    *   Foundation: `/opt/openfoam<VER>/etc/bashrc`
    *   ESI (Docker): `/usr/lib/openfoam/openfoam<VER>/etc/bashrc`

## Container Tools Check
To verify available tools in the container:
```bash
apptainer exec solver.sif which interFoam
apptainer exec solver.sif which surfaceFeatureExtract
```
