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

    logging.info(f"Case preparation complete: {output_dir}")

if __name__ == "__main__":
    prepare_case()
