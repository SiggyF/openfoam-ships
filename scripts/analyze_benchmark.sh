#!/bin/bash

# Usage: ./analyze_benchmark.sh <path_to_log_foamRun>

LOG_FILE=$1

if [ ! -f "$LOG_FILE" ]; then
    echo "Log file not found: $LOG_FILE"
    exit 1
fi

echo "Analyzing $LOG_FILE..."

# Parse log using awk to get the last valid (Time, ClockTime) pair
# Output format: "Time=... Clock=..."
RESULT=$(awk '
/^Time = / { 
    ct = $3 
}
/ClockTime =/ { 
    lastT = ct
    lastC = $7 
}
END { 
    if (lastT != "" && lastC != "") {
        print lastT " " lastC
    }
}' "$LOG_FILE")

if [ -z "$RESULT" ]; then
    echo "Could not find valid completed time steps in log."
    exit 1
fi

LAST_TIME=$(echo "$RESULT" | awk '{print $1}' | tr -d 's')
CLOCK_TIME=$(echo "$RESULT" | awk '{print $2}')

echo "Last Completed Simulation Time: $LAST_TIME s"
echo "Wall Clock Time: $CLOCK_TIME s"

# Extrapolate to 5s
TARGET_TIME=5.0
ESTIMATED_TIME=$(awk -v t="$LAST_TIME" -v c="$CLOCK_TIME" -v target="$TARGET_TIME" 'BEGIN { printf "%.2f", (c / t) * target }')

echo "Estimated Runtime for 5s: $ESTIMATED_TIME s"
echo "--------------------------------"
