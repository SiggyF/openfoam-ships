#!/bin/bash
# Dedicated benchmark for DTCHullWave (OF13) with proper mounting
# and 120s timeout enforced by controlDict (already patched)

IMAGE_NAME="openfoam-ships:latest"
# Mount the parent directory of the tutorial so it can see sibling cases (DTCHull, DTCHullMoving)
# We mount 'tutorials/of13' on host to '/tutorials' in container.
# Then we work in '/tutorials/DTCHullWave'.

# Absolute path to tutorials/of13
TUTORIALS_DIR="$PWD/tutorials/of13"
LOG_FILE="$PWD/tutorials/of13/DTCHullWave/benchmark_fixed.log"

echo "Starting Fixed Benchmark for DTCHullWave (OF13)..."
echo "Log: $LOG_FILE"
echo "Mounting: $TUTORIALS_DIR -> /tutorials"

# Ensure we have the latest image
# (Assuming it's built locally as openfoam-ships:latest)

docker run --rm \
    -v "$TUTORIALS_DIR:/tutorials" \
    -w "/tutorials/DTCHullWave" \
    "$IMAGE_NAME" \
    bash -c "source /opt/openfoam13/etc/bashrc && ./Allclean && ./Allrun" > "$LOG_FILE" 2>&1

echo "DTCHullWave Benchmark Finished."
