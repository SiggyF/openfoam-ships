# Based on OpenFOAM Foundation image
FROM openfoam/openfoam13-graphical:latest

# Switch to root to install dependencies if needed (optional)
USER root

# Install any potential missing tools (e.g. for post-processing)
# RUN apt-get update && apt-get install -y python3-pip

# Switch back to user
USER openfoam

# Set working directory
WORKDIR /home/openfoam
