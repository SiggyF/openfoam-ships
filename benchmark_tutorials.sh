#!/bin/bash

# Define images
ESI_IMAGE="opencfd/openfoam-default:2406"
OF13_IMAGE="openfoam-ships:latest"

# Define tutorials
ESI_TUTORIALS=("DTCHull" "DTCHullMoving" "rigidBodyHull")
OF13_TUTORIALS=("DTCHull" "DTCHullMoving" "DTCHullWave")

PWD=$(pwd)

echo "Starting Benchmarks..."
echo "======================"

# Function to run benchmark
run_benchmark() {
    local type=$1
    local image=$2
    local case=$3
    local mount_point=$4
    local cmd=$5

    echo "Benchmarking $type - $case"
    local case_path="$PWD/tutorials/$type/$case"
    echo "Host path: $case_path"
    local log_file="$case_path/benchmark.log"
    
    echo "Running container..."
    start_time=$(date +%s)
    
    cleanup_cmd="if [ -f ./Allclean ]; then ./Allclean; fi"
    log_capture="echo '--- log.foamRun ---'; if [ -f log.foamRun ]; then cat log.foamRun; else echo 'log.foamRun not found'; tail -n 20 log.*; fi"

    # Prepare controlDict
    # Set endTime to 5
    # Set maxClockTime to 120 (for constrained benchmarking)
    # Note: We use a python one-liner or sed to robustly edit controlDict if possible, 
    # but simple sed is risky with foam syntax. However, standard controlDict usually has "endTime ...;" on one line.
    
    # We will invoke a pre-run command in the container to modify controlDict
    setup_cmd="sed -i 's/^endTime.*/endTime 5;/' system/controlDict && \
               sed -i 's/^stopAt.*/stopAt endTime;/' system/controlDict && \
               if grep -q maxClockTime system/controlDict; then \
                 sed -i 's/^maxClockTime.*/maxClockTime 120;/' system/controlDict; \
               else \
                 sed -i '/^application/a maxClockTime 120;' system/controlDict; \
               fi"
               
    # ESI Command
     if [ "$type" == "esi" ]; then
         docker run --rm \
            -v "$PWD:/repo" \
            -w "/repo" \
            -e OMPI_ALLOW_RUN_AS_ROOT=1 \
            -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \
            $image \
            bash -c "cd /repo/tutorials/$type/$case && source /usr/lib/openfoam/openfoam2406/etc/bashrc && $cleanup_cmd && $setup_cmd && ./Allrun && $log_capture" > "$log_file" 2>&1
    else
        # OF13 Command
         docker run --rm \
            -v "$case_path:/home/openfoam/run/case" \
            -w /home/openfoam/run/case \
            $image \
            /bin/bash -c "ls -la && $cleanup_cmd && $setup_cmd && ./Allrun; $log_capture" > "$log_file" 2>&1
    fi
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo "Completed $type - $case in ${duration}s"
    echo "Log: $log_file"
    echo "--------------------------------"
}

# Run ESI (Sequential)
for case in "${ESI_TUTORIALS[@]}"; do
    run_benchmark "esi" "$ESI_IMAGE" "$case" "/data"
done

# Run OF13 (Sequential)
for case in "${OF13_TUTORIALS[@]}"; do
    run_benchmark "of13" "$OF13_IMAGE" "$case" "/home/openfoam/run/case"
done

echo "Benchmarks Complete."
