
import logging
from pathlib import Path
import re
import pandas as pd
import toml
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

CASES_DIR = Path("cases")
RESULTS_DIR = Path("results")
OUTPUT_FILE = RESULTS_DIR / "dtc_sweep.csv"

def parse_forces(log_path):
    """
    Parse forces from log.foamRun.
    Expects lines like:
    sum of forces:
        pressure : (Fx Fy Fz)
        viscous  : (Fx Fy Fz)
    """
    data = []
    
    current_time = 0.0
    pressure_force = None
    viscous_force = None
    
    # Regex for capturing vector components: (val1 val2 val3)
    vector_pattern = re.compile(r'\(([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?) ([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?) ([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\)')
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if "Time =" in line and "ExecutionTime" not in line:
            try:
                current_time = float(line.split()[2].replace('s', ''))
            except ValueError:
                pass
                
        if "sum of forces:" in line:
            # Next line usually pressure
            # Next next line usually viscous
            if i+2 < len(lines):
                p_line = lines[i+1]
                v_line = lines[i+2]
                
                if "pressure :" in p_line and "viscous  :" in v_line:
                    p_match = vector_pattern.search(p_line)
                    v_match = vector_pattern.search(v_line)
                    
                    if p_match and v_match:
                        fp_x = float(p_match.group(1))
                        fv_x = float(v_match.group(1))
                        
                        data.append({
                            'time': current_time,
                            'force_p': fp_x,
                            'force_v': fv_x,
                            'force_total': fp_x + fv_x
                        })
                        
    return pd.DataFrame(data)

def extract_resistance():
    """Iterate over successful cases and extract mean resistance."""
    results = []
    
    # Identify DTC sweep cases
    for case_dir in CASES_DIR.glob("dtc_fr*"):
        case_name = case_dir.name
        log_path = RESULTS_DIR / case_name / "log.foamRun"
        config_path = case_dir / "case.toml"
        
        if not log_path.exists():
            logging.warning(f"Log not found for {case_name}, skipping.")
            continue
            
        if not config_path.exists():
            logging.warning(f"Config not found for {case_name}, skipping.")
            continue
            
        # Helper configuration
        config = toml.load(config_path)
        velocity = config['parameters'].get('velocity')
        froude = config['parameters'].get('froude')
        
        logging.info(f"Processing {case_name} (V={velocity}, Fr={froude})...")
        
        df = parse_forces(log_path)
        
        if df.empty:
            logging.warning(f"No valid force data found for {case_name}.")
            continue
            
        # Calculate mean over stable region (last 20%)
        # Ensure we have enough data
        if df['time'].max() > 0:
            t_end = df['time'].max()
            t_start = t_end * 0.8
            
            stable_df = df[df['time'] >= t_start]
            mean_force = stable_df['force_total'].mean()
            std_force = stable_df['force_total'].std()
            
            results.append({
                'case': case_name,
                'velocity': velocity,
                'froude': froude,
                'force_x': mean_force,
                'force_std': std_force,
                't_start': t_start,
                't_end': t_end
            })
            logging.info(f"  Mean Force: {mean_force:.2f} N (std: {std_force:.2f})")
        else:
             logging.warning(f"  Time series too short for {case_name}.")

    # Save to CSV
    if results:
        out_df = pd.DataFrame(results)
        out_df = out_df.sort_values('velocity')
        out_df.to_csv(OUTPUT_FILE, index=False)
        logging.info(f"Results saved to {OUTPUT_FILE}")
        print(out_df)
    else:
        logging.warning("No results extracted.")

if __name__ == "__main__":
    extract_resistance()
