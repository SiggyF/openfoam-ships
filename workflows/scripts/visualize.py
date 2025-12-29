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
@click.option("--view", default="default", help="Camera view: default, xz (side), xy (top)")
@click.option("--focus-interface", is_flag=True, help="Zoom camera to fit the water interface")
@click.option("--z-scale", default=1.0, help="Scale factor for Z-axis (amplify details)")
def visualize(case_dir: Path, output_dir: Path, view: str, focus_interface: bool, z_scale: float):
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
        
        # Apply z-scaling if requested
        if z_scale != 1.0:
            mesh.points[:, 2] *= z_scale
            logging.info(f"Applied Z-scaling factor: {z_scale}")

        p = pv.Plotter(off_screen=True)
        p.set_background("white") # Clean background

        if mesh.n_points > 0:
            # Show domain outline for context
            p.add_mesh(mesh.outline(), color="black", label="Domain")
        else:
            logging.warning("Mesh has 0 points.")
        
        # Try to show alpha.water if available
        if "alpha.water" in mesh.point_data or "alpha.water" in mesh.cell_data:
             if "alpha.water" in mesh.cell_data:
                 mesh = mesh.ctp()
             
             # Show the full water volume (alpha > 0.5) for better context
             water_vol = mesh.threshold(value=0.5, scalars="alpha.water", invert=False)
             p.add_mesh(water_vol, color="blue", opacity=0.7, show_edges=False, label="Water Volume")
             
             # Also add a darker line for the actual interface
             water_surf = mesh.contour(isosurfaces=[0.5], scalars="alpha.water")
             p.add_mesh(water_surf, color="darkblue", line_width=2, label="Interface")
        else:
             logging.info("alpha.water not found in mesh data.")
        
        p.add_title(f"Simulation: {case_dir.name} at t={latest_proctime.name}", color="black")
        p.add_legend() # Default color
        p.show_axes()
        p.show_grid(color="gray")

        if view == "xz":
            p.view_xz()
        elif view == "xy":
            p.view_xy()

        if focus_interface and 'water' in locals():
            # Zoom to the water bounds
            # p.camera.tight_view = True # Invalid attribute
            # We can explicitly set the view range or just let pyvista reset camera to the visible actor
            # Simple approach: Get bounds of water, set camera focal point and distance?
            # Easier: p.reset_camera(bounds=water.bounds)
            p.reset_camera(water.bounds)
            p.camera.zoom(4.0) # Zoom in significantly (4x) to show wave details separate from domain length
        
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
