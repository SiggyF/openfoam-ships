#!/bin/bash
# Dedicated benchmark for rigidBodyHull (ESI) which has a complex folder structure

ESI_IMAGE="opencfd/openfoam-default:2406"
CASE_DIR="tutorials/esi/rigidBodyHull"
HOST_PATH="$PWD/$CASE_DIR"
LOG_FILE="$HOST_PATH/benchmark_fixed.log"

echo "Starting Manual Benchmark for rigidBodyHull (ESI)..."
echo "Log: $LOG_FILE"

# Prepare controlDict (manual injection since script failed)
# We already did this manually via editor, but let's confirm/ensure
# The controlDict is in background/system/controlDict

CONTROL_DICT="tutorials/esi/rigidBodyHull/background/system/controlDict"
if grep -q "maxClockTime" "$CONTROL_DICT"; then
    echo "maxClockTime found in $CONTROL_DICT"
else
    echo "Injecting maxClockTime..."
    sed -i '' '/^application/a maxClockTime 120;' "$CONTROL_DICT"
fi

# We also need to set endTime to 5 if not already
sed -i '' 's/^endTime.*/endTime 5;/' "$CONTROL_DICT"

# Run Docker
# We mount the whole repo to /repo
docker run --rm \
    -v "$PWD:/repo" \
    -w "/repo" \
    -e OMPI_ALLOW_RUN_AS_ROOT=1 \
    -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \
    "$ESI_IMAGE" \
    bash -c "cd /repo/tutorials/esi/rigidBodyHull && ./Allclean && ./Allrun" > "$LOG_FILE" 2>&1

echo "rigidBodyHull Benchmark Finished."
