import click
import pyvista as pv
import numpy as np
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

@click.command()
@click.argument("case_dir", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
def visualize(case_dir: Path, output_dir: Path):
    """
    Generate visualizations for an OpenFOAM case.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Locate the latest time directory (simple heuristic)
    # OpenFOAM time directories are numbers.
    time_dirs = []
    for item in case_dir.iterdir():
        if item.is_dir():
            try:
                float(item.name)
                time_dirs.append(item)
            except ValueError:
                pass
    
    if not time_dirs:
        logging.warning(f"No time directories found in {case_dir}. Skipping visualization.")
        return

    latest_proctime = max(time_dirs, key=lambda p: float(p.name))
    logging.info(f"Visualizing results from time: {latest_proctime.name}")

    try:
        # Create a dummy .foam file for Reader if it doesn't exist
        foam_file = case_dir / "case.foam"
        if not foam_file.exists():
            foam_file.touch()
            
        reader = pv.POpenFOAMReader(str(foam_file))
        reader.set_active_time_value(float(latest_proctime.name))
        
        pv.global_theme.allow_empty_mesh = True
        
        mesh = reader.read()
        logging.info(f"Reader returned: {type(mesh)}")
        if isinstance(mesh, pv.MultiBlock):
            logging.info(f"MultiBlock keys: {mesh.keys()}")
            # Prefer internalMesh
            if 'internalMesh' in mesh:
                mesh = mesh['internalMesh']
                logging.info(f"Selected internalMesh. n_points={mesh.n_points}, n_cells={mesh.n_cells}")
            elif len(mesh) > 0:
                mesh = mesh[0]
                logging.info(f"Selected index 0. n_points={mesh.n_points}, n_cells={mesh.n_cells}")
            else:
                raise ValueError("OpenFOAM reader returned empty MultiBlock dataset.")
        
        p = pv.Plotter(off_screen=True)
        if mesh.n_points > 0:
            p.add_mesh(mesh, show_edges=True, color="white", opacity=0.5, label="Mesh")
        else:
            logging.warning("Mesh has 0 points. Attempting to plot anyway (allow_empty_mesh=True).")
        
        # Try to show alpha.water if available
        # alpha.water might be in cell_data
        if "alpha.water" in mesh.point_data:
             water = mesh.contour(isosurfaces=[0.5], scalars="alpha.water")
             p.add_mesh(water, color="blue", opacity=0.8, label="Water Surface")
        elif "alpha.water" in mesh.cell_data:
             # Cell data contouring needs cell_to_point often, but recent pv handles it or we use ctp()
             water = mesh.ctp().contour(isosurfaces=[0.5], scalars="alpha.water")
             p.add_mesh(water, color="blue", opacity=0.8, label="Water Surface")
        else:
             logging.info("alpha.water not found in mesh data.")
        
        p.add_title(f"Simulation: {case_dir.name} at t={latest_proctime.name}")
        p.add_legend()
        
        screenshot_path = output_dir / "visualization.png"
        p.screenshot(screenshot_path)
        logging.info(f"Saved visualization to {screenshot_path}")
        
    except Exception as e:
        logging.error(f"Failed to read/visualize OpenFOAM case: {e}")
        # Fallback to mock if real read fails (e.g. strict reader issues)
        logging.info("Falling back to mock visualization.")
        p = pv.Plotter(off_screen=True)
        p.add_mesh(pv.Sphere(), color="red", label="Active Fallback")
        p.add_title(f"Simulation: {case_dir.name} (Visualization Failed)")
        screenshot_path = output_dir / "visualization.png"
        p.screenshot(screenshot_path)
        logging.info(f"Saved fallback visualization to {screenshot_path}")

if __name__ == "__main__":
    visualize()
