import argparse
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_forces_dat(dat_path):
    """
    Parse forces from force.dat (ESI format).
    """
    data = []
    try:
        with open(dat_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.replace('(', '').replace(')', '').split()
            
            # Basic expectation: Time + Forces + Moments
            if len(parts) >= 4:
                try:
                    time = float(parts[0])
                    # Total X force usually index 1
                    total_x = float(parts[1])
                    
                    # ESI force.dat columns can vary, but standard is:
                    # Time, TotalX, TotalY, TotalZ, PressureX...
                    
                    data.append({
                        'time': time,
                        'force_x': total_x
                    })
                except ValueError:
                    continue
                    
        return pd.DataFrame(data)
        
    except Exception as e:
        logging.error(f"Error parsing {dat_path}: {e}")
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description="Extract results from OpenFOAM case.")
    parser.add_argument("case_dir", type=Path, help="Path to case directory")
    args = parser.parse_args()
    
    case_dir = args.case_dir.resolve()
    logging.info(f"Processing case: {case_dir}")
    
    # Locate data
    # Standard ESI location
    force_file = case_dir / "postProcessing" / "forces" / "0" / "force.dat"
    # Fallback
    if not force_file.exists():
        force_file = case_dir / "postProcessing" / "forces" / "0" / "forces.dat"
        
    if not force_file.exists():
        logging.warning(f"No force data found in {case_dir}")
        return

    df = parse_forces_dat(force_file)
    
    if not df.empty:
        output_csv = case_dir / "results.csv"
        df.to_csv(output_csv, index=False)
        logging.info(f"Saved results to {output_csv}")
        
        # Simple summary
        mean_force = df['force_x'].tail(50).mean() # Last 50 steps
        logging.info(f"Mean Force (Last 50): {mean_force}")
    else:
        logging.warning("Empty data extracted.")

if __name__ == "__main__":
    main()
