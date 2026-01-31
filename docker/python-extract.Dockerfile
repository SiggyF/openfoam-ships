FROM python:3.13-slim

# Install system dependencies (if needed for pyvista/vtk headless)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libxrender1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    pyvista \
    matplotlib \
    scipy

# Create working directory
WORKDIR /app

# Entrypoint
CMD ["python3", "extract_data.py"]
