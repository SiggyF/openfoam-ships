import toml
import shutil
import os
import click
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

@click.command()
@click.argument("toml_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
def prepare_case(toml_path: Path, output_dir: Path):
    """
    Prepare an OpenFOAM case directory based on a TOML configuration.
    """
    # Fail early is implicit with click.Path(exists=True) for toml_path,
    # but let's be explicit about loading valid TOML
    try:
        config = toml.load(toml_path)
    except Exception as e:
        # We catch here only to provide context, but re-raise is cleaner for python guideline compliance?
        # The guideline says "Fail early... allow exceptions to propagate".
        # But for CLI entry points, it is sometimes nicer to crash with a message.
        # However, complying with "Fail early... allow propagation", we might want to just let it crash.
        # But `toml.load` failing is a data error, so maybe just let it bubble.
        # Let's let it bubble to be strictly compliant, OR just re-raise.
        # But this block was already here. I will leave the try/except but ensure it uses logging if we were printing.
        # The current code raises RuntimeError. That's fine.
        raise RuntimeError(f"Failed to parse TOML file at {toml_path}: {e}")

    meta = config.get("meta", {})
    version = meta.get("version", "of13")
    flags = config.get("flags", {})
    parameters = config.get("parameters", {})
    
    logging.info(f"Preparing case '{meta.get('name', 'unnamed')}' for OpenFOAM {version}")
    
    # Define source paths
    repo_root = Path(__file__).resolve().parent.parent.parent
    base_config_root = repo_root / "config" / "base" / version
    
    if not base_config_root.exists():
        raise FileNotFoundError(f"Base configuration for version '{version}' not found at {base_config_root}")
        
    # Clean output directory if exists
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy structure from Base
    for folder in ["system", "constant", "0"]:
        src = base_config_root / folder
        dst = output_dir / folder
        if src.exists():
            shutil.copytree(src, dst)
            
    # Template Processing
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if not file.endswith(".j2"):
                continue

            file_path = Path(root) / file
            target_path = file_path.with_suffix("") 
            
            # Setup Jinja environment for this file's folder (to allow includes relative to it)
            # But mostly we just want to pass our flags
            env = Environment(loader=FileSystemLoader(root))
            # Add a strict undefined handler if we wanted to enforce all vars are present
            # env.undefined = jinja2.StrictUndefined 
            
            template = env.get_template(file)
            rendered_content = template.render(
                flags=flags, 
                parameters=parameters,
                meta=meta
            )
            
            with open(target_path, "w") as f:
                f.write(rendered_content)
            
            # Remove the template file
            file_path.unlink()
            logging.info(f"Rendered template: {target_path.name}")
    
    # Copy Geometry if applicable
    case_name = meta.get("name")
    if case_name:
        geometry_file = repo_root / "config" / "geometry" / f"{case_name}.stl"
        if geometry_file.exists():
            tri_surface_dir = output_dir / "constant" / "triSurface"
            tri_surface_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(geometry_file, tri_surface_dir)
            logging.info(f"Copied geometry file: {geometry_file.name}")

    # Generate Allrun script
    allrun_path = output_dir / "Allrun"
    with open(allrun_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Source OpenFOAM environment if needed (handled by container usually)\n")
        f.write("set -e\n") # Fail fast
        
        # Geometry Scaling
        scale = parameters.get("scale")
        if scale and case_name:
             f.write(f"echo 'Scaling geometry by factor {scale}...'\n")
             # New syntax: surfaceTransformPoints "scale=(x y z)" input output
             # Note: quotes around the transformation string are important.
             f.write(f"surfaceTransformPoints \"scale=({scale} {scale} {scale})\" constant/triSurface/{case_name}.stl constant/triSurface/{case_name}_scaled.stl > log.surfaceTransformPoints 2>&1\n")
             f.write(f"mv constant/triSurface/{case_name}_scaled.stl constant/triSurface/{case_name}.stl\n")

        f.write("echo 'Running blockMesh...'\n")
        f.write("blockMesh > log.blockMesh 2>&1\n")
        
        # Check if snappyHexMeshDict exists
        if (output_dir / "system" / "snappyHexMeshDict").exists():
             if (output_dir / "system" / "surfaceFeaturesDict").exists():
                 f.write("echo 'Running surfaceFeatures...'\n")
                 f.write(f"surfaceFeatures > log.surfaceFeatures 2>&1\n")
             elif (output_dir / "system" / "surfaceFeatureExtractDict").exists():
                 # Legacy fallback
                 f.write("echo 'Running surfaceFeatureExtract...'\n")
                 f.write(f"surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1\n")
             
             f.write("echo 'Running snappyHexMesh...'\n")
             f.write(f"snappyHexMesh -overwrite > log.snappyHexMesh 2>&1\n")

        # Placeholder for topoSet/snappyHexMesh if needed
        # f.write("setFields > log.setFields 2>&1\n") # Need setup for setFields
        f.write("echo 'Running interFoam...'\n")
        f.write(f"interFoam > log.interFoam 2>&1\n")
    
    # Make executable
    allrun_path.chmod(0o755)
    logging.info(f"Created Allrun script at {allrun_path}")

    logging.info(f"Case preparation complete: {output_dir}")

if __name__ == "__main__":
    prepare_case()
