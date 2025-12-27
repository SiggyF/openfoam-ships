#!/bin/bash
# Debug script to compare local rigidBodyHull files with original container files

ESI_IMAGE="opencfd/openfoam-default:2406"
LOCAL_DIR="$PWD/tutorials/esi/rigidBodyHull"

echo "Comparing rigidBodyHull files..."

docker run --rm \
    -v "$LOCAL_DIR:/local_repo" \
    "$ESI_IMAGE" \
    bash -c '
        # Find the tutorial in the container
        # Typically in $FOAM_TUTORIALS (which is set in env)
        source /usr/lib/openfoam/openfoam2406/etc/bashrc
        ORIG_DIR=$(find $FOAM_TUTORIALS -name rigidBodyHull | head -n 1)
        
        if [ -z "$ORIG_DIR" ]; then
            echo "Could not find rigidBodyHull in container tutorials!"
            exit 1
        fi
        
        echo "Found original tutorial at: $ORIG_DIR"
        
        echo "---------------------------------------------------"
        echo "Comparing background/system/exclude_from_diff (if relevant)..."
        
        # Check specific files associated with the error
        # "Number of searchBoxDivisions 3 should equal the number of zones 2"
        # This usually relates to decomposeParDict or snappyHexMeshDict setup in overset cases.
        
        echo "Diffing background/system/decomposeParDict:"
        diff $ORIG_DIR/background/system/decomposeParDict /local_repo/background/system/decomposeParDict
        
        echo "Diffing overset-1/system/decomposeParDict (if exists):"
         [ -f /local_repo/overset-1/system/decomposeParDict ] && diff $ORIG_DIR/overset-1/system/decomposeParDict /local_repo/overset-1/system/decomposeParDict

        echo "Diffing Allrun:"
        diff $ORIG_DIR/Allrun /local_repo/Allrun
        
        echo "---------------------------------------------------"
        echo "Checking for missing files in /local_repo:"
        # List files in orig but not in local
        cd $ORIG_DIR
        find . -type f | while read f; do
            if [ ! -f "/local_repo/$f" ]; then
                echo "MISSING: $f"
            fi
        done
    '
