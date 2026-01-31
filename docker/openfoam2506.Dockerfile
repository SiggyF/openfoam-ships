# Based on OpenFOAM ESI image
FROM opencfd/openfoam-default:latest

# Switch to root to install dependencies if needed
USER root

# Switch back to user
# Switch back to user
USER ubuntu

# Set working directory
WORKDIR /home/ubuntu
