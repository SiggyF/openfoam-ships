#!/bin/bash

# Find container ID for openfoam-ships
CONTAINER_ID=$(docker ps -q --filter ancestor=openfoam-ships:latest)

if [ -z "$CONTAINER_ID" ]; then
    echo "No running openfoam-ships container found."
    exit 0
fi

echo "Found container: $CONTAINER_ID"
echo "Sending SIGINT to interFoam for graceful shutdown (writing latest time step)..."

docker exec $CONTAINER_ID killall -INT interFoam

if [ $? -eq 0 ]; then
    echo "Signal sent. Monitor the log to ensure it stops."
else
    echo "Failed to send signal. Trying 'docker stop' (might not write data)..."
    docker stop $CONTAINER_ID
fi
