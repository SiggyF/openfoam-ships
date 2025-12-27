# OpenFOAM ESI (v2406) Tutorials

This directory contains standard tutorials extracted from the OpenFOAM ESI Docker image (`opencfd/openfoam-default:2406`).

## Docker Image Particularities

Unlike the Foundation (v13) images, the ESI image (`opencfd/openfoam-default:2406`) has the following characteristics:

1.  **Default User**: Runs as `root` (uid=0) by default. It does not have a pre-configured `openfoam` user (uid=1000) accessible in the same way.
2.  **Environment**: The OpenFOAM environment variables are **not** automatically loaded for non-interactive shells (`bash -c ...`). You must explicitly source the bashrc file.
3.  **Path**: The bashrc file is located at `/usr/lib/openfoam/openfoam2406/etc/bashrc`.

## Running Tutorials

To successfully run these tutorials using the ESI image, use the following pattern:

```bash
docker run --rm \
  -v $(pwd)/tutorials/esi/DTCHull:/data \
  -w /data \
  opencfd/openfoam-default:2406 \
  bash -c 'source /usr/lib/openfoam/openfoam2406/etc/bashrc && ./Allrun'
```

### Notes
- **Volume Mounting**: Mount the case directory to a path like `/data`.
- **Sourcing**: Always chain `source /usr/lib/openfoam/openfoam2406/etc/bashrc` before your commands.
- **Permissions**: Since the container runs as root, output files will be owned by root. You may need to `chown` them back to your user on the host.

## Non-Root Execution

The image contains a user named `ubuntu` (UID 1000). You can use this user to run simulations, which is safer but requires managing volume permissions (ensure the mounted directory is writable by UID 1000).

```bash
docker run --rm \
  -u ubuntu \
  -v $(pwd)/tutorials/esi/DTCHull:/data \
  -w /data \
  opencfd/openfoam-default:2406 \
  bash -c 'source /usr/lib/openfoam/openfoam2406/etc/bashrc && ./Allrun'
```
