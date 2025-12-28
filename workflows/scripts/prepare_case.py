import toml
import shutil
import os
import click
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

@click.command()
@click.argument("toml_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
def prepare_case(toml_path: Path, output_dir: Path):
    """
    Prepare an OpenFOAM case directory based on a TOML configuration.
    """
    try:
        config = toml.load(toml_path)
    except Exception as e:
        raise RuntimeError(f"Failed to parse TOML file at {toml_path}: {e}")

    meta = config.get("meta", {})
    version = meta.get("version", "of13")
    flags = config.get("flags", {})
    parameters = config.get("parameters", {})
    
    case_name = meta.get("name")
    
    logging.info(f"Preparing case '{meta.get('name', 'unnamed')}' for OpenFOAM {version}")
    
    # Define source paths
    repo_root = Path(__file__).resolve().parent.parent.parent
    templates_root = repo_root / "templates"
    
    # Clean output directory if exists
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    # 1. Apply Base Template
    base_template = templates_root / "base"
    if not base_template.exists():
         raise FileNotFoundError(f"Base template not found at {base_template}")
    
    logging.info(f"Applying base template from {base_template}")
    
    # Ignore build artifacts
    ignore_func = shutil.ignore_patterns("log.*", "processor*", "postProcessing", "*.foam", "dynamicCode")
    shutil.copytree(base_template, output_dir, ignore=ignore_func)
    
    # 2. Apply Features
    features = flags.get("features", {})
    
    # Feature: Six DoF
    if features.get("six_dof"):
        feature_path = templates_root / "features" / "six_dof"
        if feature_path.exists():
            logging.info("Applying feature: six_dof")
            shutil.copytree(feature_path, output_dir, dirs_exist_ok=True)
        else:
            logging.warning(f"Feature six_dof requested but template not found at {feature_path}")

    # --- Patching Logic (Applied to the composed case) ---
    
    # Patching Logic (Applied to the composed case)
    # Most dicts are now handled via Jinja2 templates (see .j2 files in templates/)
    # - snappyHexMeshDict.j2
    # - fvSolution.j2
    # - fvSchemes.j2
    # - decomposeParDict.j2
    # - U.j2
    
    # Generate surfaceFeaturesDict (OF13 compatibility)
    surf_feat_template_path = templates_root / "scripts" / "surfaceFeaturesDict.template"
    if surf_feat_template_path.exists() and case_name and features.get("meshing", True):
        with open(surf_feat_template_path, "r") as f:
            template_content = f.read()
        
        rendered = template_content.replace("{stl_filename}", f"{case_name}.stl")
        
        surf_feat_dict = output_dir / "system" / "surfaceFeaturesDict"
        with open(surf_feat_dict, "w") as f:
            f.write(rendered)
        logging.info(f"Generated surfaceFeaturesDict from template")

    # Remove legacy dict
    legacy_dict = output_dir / "system" / "surfaceFeatureExtractDict"
    if legacy_dict.exists():
        legacy_dict.unlink()

    # Patch controlDict (Handling moved to templates/base/system/controlDict.j2)
    pass

    # Patch dynamicMeshDict
    dyn_mesh_dict = output_dir / "constant" / "dynamicMeshDict"
    # Placeholder for mass property injection if we implement it dynamically
    # For now, we rely on the template or manual edits, but could inject mass/CoM here.
    
    # Patch fvSolution (Moved to template)
    pass

    # Patch fvSchemes (Moved to template)
    pass

    # Patch turbulenceProperties -> momentumTransport
    turb_props = output_dir / "constant" / "turbulenceProperties"
    mom_transport = output_dir / "constant" / "momentumTransport"
    if turb_props.exists() and not mom_transport.exists():
        turb_props.rename(mom_transport)
        logging.info("Renamed turbulenceProperties -> momentumTransport for OF13 compatibility")

    # Patch decomposeParDict (Moved to template)
    pass

    # Patch 0/U (Moved to template)
    pass

    # Patch Allrun (Legacy patching removed - Logic handled by Allrun.j2 template)
    pass

    # Clean numbered directories
    for item in output_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
             if item.name == "0": continue
             shutil.rmtree(item)

    # Template Processing
    for file_path in output_dir.rglob("*.j2"):
        if file_path.name == "header.j2":
            file_path.unlink()
            continue

        target_path = file_path.with_suffix("") 
        
        # Jinja2 requires a str path for loader
        # We add the file's parent AND templates/base to allow including common templates like header.j2
        search_paths = [str(file_path.parent), str(templates_root / "base")]
        env = Environment(loader=FileSystemLoader(search_paths))
        if file_path.name == "snappyHexMeshDict.j2" and not features.get("meshing", True):
             file_path.unlink()
             continue

        template = env.get_template(file_path.name)
        rendered_content = template.render(
            flags=flags, 
            parameters=parameters, 
            meta=meta, 
            case_name=case_name,
            version=version
        )
        
        with open(target_path, "w") as f:
            f.write(rendered_content)
        
        file_path.unlink()
        logging.info(f"Rendered template: {target_path.name}")
    
    # Geometry Handling
    geometry_dir = output_dir / "constant" / "triSurface"
    geometry_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for compressed or uncompressed source
    source_stl = toml_path.parent / f"{case_name}.stl"
    source_stl_gz = toml_path.parent / f"{case_name}.stl.gz"
    
    # Fallback to config/geometry if not in case dir
    if not source_stl.exists() and not source_stl_gz.exists():
         source_stl = repo_root / "config" / "geometry" / f"{case_name}.stl"
         source_stl_gz = repo_root / "config" / "geometry" / f"{case_name}.stl.gz"

    target_stl = geometry_dir / f"{case_name}.stl"

    if source_stl.exists():
        shutil.copy(source_stl, target_stl)
        logging.info(f"Copied geometry file: {source_stl.name}")
    elif source_stl_gz.exists():
        import gzip
        with gzip.open(source_stl_gz, 'rb') as f_in:
            with open(target_stl, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        logging.info(f"Copied and decompressed geometry file: {source_stl_gz.name}")
    else:
        logging.warning(f"Geometry file for {case_name} not found in case dir or config/geometry.")
    
    # Generate Allrun script (Jinja2 template based)
    allrun_path = output_dir / "Allrun"
    allrun_template_path = templates_root / "scripts" / "Allrun.j2"
    
    if not allrun_path.exists() and allrun_template_path.exists():
        with open(allrun_template_path, "r") as f:
            template_content = f.read()
            
        template = Environment(loader=FileSystemLoader(allrun_template_path.parent)).from_string(template_content)

        # Prepare Context
        context = {
            "case_name": case_name,
            "scale": parameters.get("scale"),
            "has_0_orig": (output_dir / "0.orig").exists(),
            "has_block_mesh": (output_dir / "system" / "blockMeshDict").exists(),
            "has_snappy": (output_dir / "system" / "snappyHexMeshDict").exists(),
            "has_surface_features": (output_dir / "system" / "surfaceFeaturesDict").exists(),
            "has_surface_feature_extract": (output_dir / "system" / "surfaceFeatureExtractDict").exists(),
            "has_set_fields": (output_dir / "system" / "setFieldsDict").exists(),
            "has_decompose": (output_dir / "system" / "decomposeParDict").exists()
        }

        rendered_allrun = template.render(context)

        with open(allrun_path, "w") as f:
            f.write(rendered_allrun)
        allrun_path.chmod(0o755)
        logging.info(f"Created Allrun script from template at {allrun_path}")

    logging.info(f"Case preparation complete: {output_dir}")

if __name__ == "__main__":
    prepare_case()
