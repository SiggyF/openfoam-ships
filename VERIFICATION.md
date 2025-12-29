# Simulation Walkthrough: Issue #2 Verification

## `empty_tank` Baseline
The 'empty_tank' simulation serves as a baseline to verify the numerical domain and solver stability without any floating bodies.
The simulation was run up to t=2.5s (50% complete) and reconstructed.

### Visualization (t=2.5s)
The following image shows the distribution of `alpha.water` (blue isosurface) in the tank. The surface is essentially flat as expected for a calm tank, verifying the initialization and boundary conditions are stable.

![empty_tank visualization](/Users/baart_f/.gemini/antigravity/brain/bebb22d9-3c33-4d5e-99f5-f024442ad1d3/empty_tank_vis.png)

## Stokes Wave Verification (OF13 Foundation)
**Status**: Success
**Configuration**:
- **Mesh**: 2D tutorial mesh (copied via overrides).
- **Physics**: Laminar, `Stokes2` wave model (Amp: 0.025m, Period: 3.0s).
- **Visualization**: Side View (XZ), Amplified 10x Z-scale, Domain Outline, Water Volume (Blue).
- **Fixes Applied**: OF13 syntax for `waveProperties` and `setFieldsDict`, added `libwaves.so`.

![Stokes Wave Result at t=1.35s (Amplified 10x)](/Users/baart_f/.gemini/antigravity/brain/bebb22d9-3c33-4d5e-99f5-f024442ad1d3/stokes_wave_vis.png)

## Wigley Hull Verification
**Status**: Success
**Configuration**:
- **Mesh**: Optimized `snappyHexMesh` (~100k cells) for rapid verification.
- **Solver**: `interFoam` (Parallel).
- **Result**: Wave pattern successfully developing around the hull.

![Wigley Wave Pattern at t=3.6s](/Users/baart_f/.gemini/antigravity/brain/bebb22d9-3c33-4d5e-99f5-f024442ad1d3/wigley_vis.png)

## DTC Hull (6DoF) Verification
**Status**: Success (Optimized)
**Configuration**:
- **Mesh**: Optimized `snappyHexMesh` with **Level 2** refinement (down from Level 6/Tutorial settings).
- **Count**: **189,126 cells** (vs 2.3M original).
- **Performance**: Simulation reached t=2.0s rapidly (< 5 mins).
- **Result**: 6DoF motion active, wave formation visible.

![DTC Wave Interaction at t=2.0s](/Users/baart_f/.gemini/antigravity/brain/bebb22d9-3c33-4d5e-99f5-f024442ad1d3/dtc_vis.png)

## Summary of Findings
- **OpenFOAM 13 Compatibility**: Confirmed for `waveProperties`, `momentumTransport`, and parallel execution.
- **Mesh Sensitivity**: Heavy meshes (Lev 5-6) cause massive slowdowns locally; Level 2 is sufficient for functional verification.
- **Visuals**: Z-scaling (5x-10x) is essential for validating wave physics in these scenarios.
