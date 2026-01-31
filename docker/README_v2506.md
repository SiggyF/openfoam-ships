# OpenFOAM v2506 Container Analysis

**Base Image**: `opencfd/openfoam-default:latest` (resolves to v2506 as of Dec 2025)

## Users
- `root` (id=0)
- `ubuntu` (id=1000): Default non-root user.
- `sudofoam` (id=1001): Created by `post-install.sh` as a sudo-enabled user.
- **Note**: The user `openfoam` does **NOT** exist. The build script `post-install.sh` creates `sudofoam` instead. `/home/openfoam` is created as a directory but not assigned to a user named `openfoam`.

## OpenFOAM Usage
- **Installation Directory**: `/usr/lib/openfoam/openfoam2506`
- **Environment Script**: `/usr/lib/openfoam/openfoam2506/etc/bashrc`
- **Tutorials Directory**: `/usr/lib/openfoam/openfoam2506/tutorials`

## Recommended Execution
To run OpenFOAM commands, you must source the environment script inside the shell.

**Example (Interactive)**:
```bash
docker run -it --rm -u 1000 opencfd/openfoam-default:latest /bin/bash
source /usr/lib/openfoam/openfoam2506/etc/bashrc
simpleFoam -help
```

**Example (Non-Interactive)**:
```bash
# Run as root or ubuntu (with careful volume permissions)
docker run --rm -u 0 -v $(pwd):/job -w /job opencfd/openfoam-default:latest \
    /bin/bash -c "source /usr/lib/openfoam/openfoam2506/etc/bashrc && ./Allrun"
```

## Troubleshooting
- **Exit Code 127**: Usually means a command is not found. Ensure the environment is sourced correctly.
- **Permission Denied**: If running as `ubuntu` with host mounts, ensure UIDs match or use `root` (`-u 0`).
