# Docker Makefile for OpenFOAM Ships

# Configuration
REPO_USER ?= siggyf
PLATFORM ?= linux/amd64,linux/arm64

# Image Names
SOLVER_IMAGE = $(REPO_USER)/openfoam-ships-solver:latest
EXTRACT_IMAGE = $(REPO_USER)/openfoam-ships-extract:latest

# Defaults
.PHONY: all build push build-solver build-extract push-solver push-extract builder-init

all: build
build: build-solver build-extract
push: push-solver push-extract

# Setup buildx (run once)
builder-init:
	docker buildx create --use --name multiarch-builder || true

# Solver
build-solver:
	docker buildx build --platform $(PLATFORM) -t $(SOLVER_IMAGE) -f openfoam2506.Dockerfile ..

push-solver:
	docker buildx build --platform $(PLATFORM) -t $(SOLVER_IMAGE) -f openfoam2506.Dockerfile --push ..

# Extractor
build-extract:
	docker buildx build --platform $(PLATFORM) -t $(EXTRACT_IMAGE) -f python-extract.Dockerfile ..

push-extract:
	docker buildx build --platform $(PLATFORM) -t $(EXTRACT_IMAGE) -f python-extract.Dockerfile --push ..
