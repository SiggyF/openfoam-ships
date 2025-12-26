# Based on OpenFOAM ESI image
FROM opencfd/openfoam-default:2406

# Switch to root to install dependencies if needed
USER root

# Switch back to user
USER openfoam

# Set working directory
WORKDIR /home/openfoam
