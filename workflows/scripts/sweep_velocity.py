import shutil
import subprocess
import copy
import pandas as pd
import numpy as np
from pathlib import Path
import toml
import logging
from typing import List, Dict

# Configuration
CASES_DIR = Path("cases")
BUILD_DIR = Path("build")
RESULTS_DIR = Path("results")
BASE_CASE = "dtc_esi" 
MESH_BASE_CASE = "dtc_esi_mesh_base"
GEOMETRY_SOURCE = Path("config/geometry/dtc_hull_esi.stl.gz")
GRAVITY = 9.81
LENGTH_DTC = 3.0  # Model scale length in meters
FROUDE_POINTS = [0.10, 0.15, 0.18, 0.20, 0.22, 0.25]

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_velocity(froude, length=LENGTH_DTC, g=GRAVITY):
    """Calculate velocity from Froude number: V = Fr * sqrt(g * L)"""
    return froude * np.sqrt(g * length)

def run_command(command, cwd=None):
    """Run a shell command."""
    logging.info(f"Running: {command}")
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        raise

def prepare_base_mesh(dry_run=False):
    """Generate and run a base case solely for mesh generation."""
    mesh_case_name = f"{BASE_CASE}_mesh_base"
    mesh_case_path = CASES_DIR / mesh_case_name
    
    # Check if we already have a valid mesh source from a previous run
    # If using results structure:
    mesh_source_path = RESULTS_DIR / mesh_case_name / "constant" / "polyMesh"
    if mesh_source_path.exists() and (mesh_source_path / "points").exists():
        logging.info(f"Using existing base mesh from {mesh_source_path}")
        return mesh_source_path

    logging.info(f"Preparing base mesh case: {mesh_case_name}")
    
    if not dry_run:
        if mesh_case_path.exists():
            shutil.rmtree(mesh_case_path)
        mesh_case_path.mkdir(parents=True)
        
        # Clean build
        if (BUILD_DIR / mesh_case_name).exists():
           shutil.rmtree(BUILD_DIR / mesh_case_name)

        # Load base config
        base_case_path = CASES_DIR / BASE_CASE
        base_config_path = base_case_path / "case.toml"
        
        if not base_config_path.exists():
            raise FileNotFoundError(f"Base case {BASE_CASE} not found at {base_config_path}")
            
        base_config = toml.load(base_config_path)
            
        # Create mesh base dir
        mesh_case_path.mkdir(parents=True, exist_ok=True)
        
        # Write temporary mesh base TOML 
        # We can just copy the file or render a slightly modified one
        # For simplicity, we just copy it but might assume defaults are fine for meshing
        shutil.copy(base_config_path, mesh_case_path / "case.toml")
        
        # Copy system directory to ensure overrides (like optimized snappyHexMeshDict) are used
        if (base_case_path / "system").exists():
            shutil.copytree(base_case_path / "system", mesh_case_path / "system", dirs_exist_ok=True)
        
        # Ensure system directory exists for overrides?
        # Actually prepare_case handles this if we just point to it.
        # But we might need specific mesh modifications? 
        # For now, assuming base case mesh settings are what we want.

    # Run prepare_case for the mesh base
    # We use Snakemake to run just the 'run_case' rule (which triggers prepare)
    # BUT we need to stop BEFORE running solver if possible?
    # Our current Allrun runs everything. 
    # Optimization: We let it run. The "mesh base" case will run a full simulation,
    # but that's a one-time cost. 
    # BETTER: just let it run. 
    
    log_path = RESULTS_DIR / MESH_BASE_CASE / "log.foamRun"
    
    if (RESULTS_DIR / MESH_BASE_CASE / "constant" / "polyMesh" / "points").exists():
         logging.info(f"Using existing base mesh from {RESULTS_DIR / MESH_BASE_CASE / 'constant' / 'polyMesh'}")
         return RESULTS_DIR / MESH_BASE_CASE / "constant" / "polyMesh"

    logging.info(f"Preparing base mesh case: {MESH_BASE_CASE}")
    
    cmd = [
        "snakemake",
        "-j", "1",
        str(log_path)
    ]
    
    if dry_run:
        logging.info(f"Dry run: Would execute {' '.join(cmd)}")
        return RESULTS_DIR / MESH_BASE_CASE / "constant" / "polyMesh"  # Fake path
    
    subprocess.run(cmd, check=True)
    
    return RESULTS_DIR / MESH_BASE_CASE / "constant" / "polyMesh"

def ensure_dir(path):
    if not path.exists():
        path.mkdir(parents=True)

def setup_sweep_cases(froude_numbers: List[float], mesh_source_path: Path = None, dry_run: bool = False) -> Dict[str, float]:
    """
    Creates case variants for each Froude number.
    Returns a dictionary mapping case_name -> velocity.
    """
    base_case_path = CASES_DIR / BASE_CASE
    base_config_path = base_case_path / "case.toml"
    if not base_config_path.exists():
        raise FileNotFoundError(f"Base case {BASE_CASE} configuration not found.")

    base_config = toml.load(base_config_path)
    length = base_config["parameters"].get("length", 3.0) # Default to 3.0 for DTC
    g = 9.81
    
    case_map = {}
    
    for fr in froude_numbers:
        vel = fr * (g * length) ** 0.5
        variant_name = f"dtc_fr{int(fr*1000):04d}"
        
        variant_path = CASES_DIR / variant_name
        
        logging.info(f"Preparing case: {variant_name} (Fr={fr:.3f}, V={vel:.3f} m/s)")
        
        if not dry_run:
            # Create variant directory
            if variant_path.exists():
                shutil.rmtree(variant_path)
            variant_path.mkdir(parents=True)
            
            # Clean build directory
            if (BUILD_DIR / variant_name).exists():
                shutil.rmtree(BUILD_DIR / variant_name)
            
            # Clean results directory to force rerun
            if (RESULTS_DIR / variant_name).exists():
                shutil.rmtree(RESULTS_DIR / variant_name)

            # Update configuration
            variant_config = copy.deepcopy(base_config)
            variant_config['meta']['name'] = variant_name
            variant_config['parameters']['velocity'] = float(f"{vel:.4f}")
            variant_config['parameters']['froude'] = float(f"{fr:.4f}") 
            
            with open(variant_path / "case.toml", "w") as f:
                toml.dump(variant_config, f)
            
            # Copy System Directory
            if (base_case_path / "system").exists():
                shutil.copytree(base_case_path / "system", variant_path / "system")
                
                # We still patch snappyHexMeshDict even if reusing mesh (consistency)
                snappy_path = variant_path / "system" / "snappyHexMeshDict"
                if snappy_path.exists():
                     with open(snappy_path, 'r') as f:
                         content = f.read()
                     content = content.replace(f"{base_name}_hull", f"{variant_name}")
                     content = content.replace(f"{base_name}.stl", f"{variant_name}.stl")
                     content = content.replace(f"{base_name}.eMesh", f"{variant_name}.eMesh")
                     content = content.replace(f"{base_name}", f"{variant_name}")
                     with open(snappy_path, 'w') as f:
                         f.write(content)

            # Copy Geometry
            if GEOMETRY_SOURCE.exists():
                 target_geo = variant_path / f"{variant_name}.stl.gz"
                 shutil.copy(GEOMETRY_SOURCE, target_geo)

            # Copy Pre-generated Mesh if available
            # NOTE: run_case rule copies BUILD_DIR to RESULTS_DIR.
            # prepare_case.py populates BUILD_DIR from CASES_DIR.
            # So we must put the mesh in CASES_DIR for prepare_case to see it?
            # prepare_case logic: "Overrides from case directory: Copy system/ and constant/"
            # So if we put polyMesh in cases/{variant}/constant/polyMesh, prepare_case will copy it to build.
            
            if mesh_source_path and mesh_source_path.exists():
                target_mesh_dir = variant_path / "constant" / "polyMesh"
                if target_mesh_dir.exists():
                    shutil.rmtree(target_mesh_dir)
                shutil.copytree(mesh_source_path, target_mesh_dir)
                logging.info(f"Copied mesh from base to {variant_name}")
            
        case_map[variant_name] = {
            "path": variant_path,
            "velocity": vel,
            "froude": fr
        }
        
    return case_map

def run_sweep(case_map, dry_run=False):
    """Run simulations for all prepared cases using Snakemake."""
    
    targets = [f"results/{name}/log.foamRun" for name in case_map.keys()]
    
    # Run sequentially (-j 1) or parallel (-j N)
    # Since we are reusing mesh, memory overhead is lower, but solver is still heavy.
    # Keep -j 1 for safety unless requested otherwise.
    cmd = f"snakemake -j 1 {' '.join(targets)}"
    
    if dry_run:
        logging.info(f"[DRY-RUN] Would execute: {cmd}")
    else:
        run_command(cmd)

def parse_execution_time(log_path):
    """Parse log file to calculate average execution time per simulated second."""
    # This is a simplified parser. For accurate results, we'd need to parse the time loop.
    # Assuming 'ExecutionTime = X s' lines exist.
    times = []
    sim_times = []
    
    with open(log_path, 'r') as f:
        for line in f:
            if "ExecutionTime =" in line:
                parts = line.split()
                try:
                    # "ExecutionTime = 123.45 s"
                    idx = parts.index("ExecutionTime")
                    times.append(float(parts[idx + 2]))
                except (ValueError, IndexError):
                    pass
            if "Time =" in line and "ExecutionTime" not in line:
                 parts = line.split()
                 try:
                     sim_times.append(float(parts[2]))
                 except (ValueError, IndexError):
                     pass
                     
    if len(times) < 2 or len(sim_times) < 2:
        return None

    # Calculate speed: Wall seconds per Simulated second
    # Use last 50% of data to avoid startup transients
    n = len(times)
    start_idx = int(n/2)
    
    delta_wall = times[-1] - times[start_idx]
    delta_sim = sim_times[-1] - sim_times[start_idx]
    
    if delta_sim <= 0:
        return None
        
    return delta_wall / delta_sim

def run_benchmark():
    """Run a single short benchmark case to estimate runtime."""
    logging.info("Running benchmark...")
    
    # 1. Setup a single case with short duration
    fr = 0.26 # Design speed
    vel = calculate_velocity(fr)
    variant_name = f"{BASE_CASE}_benchmark"
    variant_path = CASES_DIR / variant_name
    
    if variant_path.exists():
        shutil.rmtree(variant_path)
    variant_path.mkdir(parents=True)
    
    # Clean build directory
    if (BUILD_DIR / variant_name).exists():
        shutil.rmtree(BUILD_DIR / variant_name)
    
    base_case_path = CASES_DIR / BASE_CASE
    base_config_path = base_case_path / "case.toml"
    base_config = toml.load(base_config_path)
    base_name = base_config['meta']['name'] # Capture original name
    
    # Override for benchmark
    # Use deep copy or manual dict creation to avoid mutating base_config if reused,
    # though here it's single use. But for clarity:
    import copy
    variant_config = copy.deepcopy(base_config)
    variant_config['meta']['name'] = variant_name
    variant_config['parameters']['velocity'] = float(f"{vel:.4f}")
    variant_config['parameters']['endTime'] = 2.0 
    variant_config['parameters']['writeInterval'] = 1.0
    
    with open(variant_path / "case.toml", "w") as f:
        toml.dump(variant_config, f)

    # Copy System Directory (to preserve optimized mesh settings)
    if (base_case_path / "system").exists():
        if (variant_path / "system").exists():
            shutil.rmtree(variant_path / "system")
        shutil.copytree(base_case_path / "system", variant_path / "system")
        
        # Patch snappyHexMeshDict to match new case name
        snappy_path = variant_path / "system" / "snappyHexMeshDict"
        if snappy_path.exists():
                with open(snappy_path, 'r') as f:
                    content = f.read()
                
                # Patch "kcs_hull" -> "kcs_benchmark" (most specific)
                content = content.replace(f"{base_name}_hull", f"{variant_name}")
                # Patch "kcs_hull.stl" -> "kcs_benchmark.stl"
                content = content.replace(f"{base_name}.stl", f"{variant_name}.stl")
                content = content.replace(f"{base_name}.eMesh", f"{variant_name}.eMesh")
                content = content.replace(f"{base_name}", f"{variant_name}") # Catch-all
                
                with open(snappy_path, 'w') as f:
                    f.write(content)

    # Copy Geometry
    if GEOMETRY_SOURCE.exists():
            target_geo = variant_path / f"{variant_name}.stl.gz"
            shutil.copy(GEOMETRY_SOURCE, target_geo)
    else:
            logging.warning(f"Geometry source not found at {GEOMETRY_SOURCE}")
        
    # 2. Run simulation
    logging.info(f"Executing benchmark simulation: {variant_name}")
    log_path = RESULTS_DIR / variant_name / "log.foamRun"
    
    # Ensure results dir exists
    (RESULTS_DIR / variant_name).mkdir(parents=True, exist_ok=True)
    
    # We use the Snakefile to run just this case
    # Need to be careful: the Snakefile expects case directories to exist in cases/
    # We just created cases/kcs_benchmark
    
    cmd = f"snakemake -j 1 results/{variant_name}/log.foamRun"
    run_command(cmd)
    
    # 3. Analyze performance
    if not log_path.exists():
        logging.error("Benchmark failed: log file not found.")
        return

    wall_per_sim = parse_execution_time(log_path)
    
    if wall_per_sim:
        logging.info(f"Benchmark Result: {wall_per_sim:.2f} wall-seconds per simulated-second")
        
        # Estimate full sweep
        # 6 cases * 20s simulated time each = 120s simulated
        # But wait, cases have different endTimes? KCS base says 20.0
        total_sim_time = 6 * 20.0 
        estimated_wall_seconds = wall_per_sim * total_sim_time
        
        hours = estimated_wall_seconds / 3600
        logging.info(f"Estimated Total Sweep Time (6 cases, 20s each): {hours:.2f} hours")
    else:
        logging.warning("Could not calculate execution speed from logs.")

import click

@click.group()
def cli():
    """Velocity sweep and benchmarking tool for KCS hull."""
    pass

@cli.command()
def benchmark():
    """Run a single short benchmark case to estimate runtime."""
    run_benchmark()

@cli.command()
@click.option("--froude", "-f", multiple=True, type=float, help="Froude numbers to run (default: defined in FROUDE_POINTS)")
@click.option("--dry-run", is_flag=True, help="Generate cases but do not run simulations")
def sweep(froude, dry_run):
    """
    Run a velocity sweep for the base case.
    """
    froude_points = list(froude) if froude else FROUDE_POINTS
    
    logging.info(f"Starting sweep for Froude numbers: {froude_points}")
    
    try:
        # 1. Prepare/Get Base Mesh
        logging.info("Step 1: Preparing Base Mesh...")
        mesh_source_path = prepare_base_mesh(dry_run=dry_run)
        
        # 2. Setup Cases (copying the base mesh)
        logging.info("Step 2: Setting up Sweep Cases...")
        case_map = setup_sweep_cases(froude_points, mesh_source_path=mesh_source_path, dry_run=dry_run)
        
        # 3. Run Sweep
        logging.info("Step 3: Running Sweep...")
        run_sweep(case_map, dry_run=dry_run)
        logging.info("Sweep completed successfully.")
        
    except Exception as e:
        logging.error(f"Sweep failed: {e}")
        exit(1)

if __name__ == "__main__":
    cli()
