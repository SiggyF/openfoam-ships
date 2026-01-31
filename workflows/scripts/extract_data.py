
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

def parse_forces_log(log_path):
    """
    Parse forces from log.foamRun.
    Expects lines like:
    sum of forces:
        pressure : (Fx Fy Fz)
        viscous  : (Fx Fy Fz)
    """
    data = []
    
    current_time = 0.0
    
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

def parse_forces_dat(dat_path):
    """
    Parse forces from force.dat (ESI format).
    Expects standard OF function object output:
    # Time       total_x total_y total_z pressure_x ... viscous_x ...
    0.01         ...     ...     ...     ...            ...
    """
    data = []
    
    try:
        # force.dat usually has columns:
        # Time(0) TotalX(1) TotalY(2) TotalZ(3) PressureX(4) ... ViscousX(7) ...
        # But let's check the header or assume standard structure based on previous inspection
        # Previous view showed:
        # Time total_x total_y total_z pressure_x pressure_y pressure_z viscous_x viscous_y viscous_z
        # So: Time=0, TotalX=1, PressureX=4, ViscousX=7
        
        # Using pandas is easiest for whitespace separated data
        # Skip rows starting with # (comments), but headers might be commented
        
        # Manual parsing often more robust against weird header variations
        with open(dat_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.replace('(', '').replace(')', '').split()
            
            # Ensure we have enough columns. We saw about 10 columns.
            if len(parts) >= 8:
                try:
                    time = float(parts[0])
                    # Ensure we handle scientific notation
                    total_x = float(parts[1])
                    pressure_x = float(parts[4])
                    viscous_x = float(parts[7])
                    
                    data.append({
                        'time': time,
                        'force_p': pressure_x,
                        'force_v': viscous_x,
                        'force_total': total_x
                    })
                except ValueError:
                    continue
                    
        return pd.DataFrame(data)
        
    except Exception as e:
        logging.error(f"Error parsing {dat_path}: {e}")
        return pd.DataFrame()

def extract_resistance():
    """Iterate over successful cases and extract mean resistance."""
    results = []
    
    # 1. Process Standard/Benchmark Cases (Managed by Snakemake/case.toml)
    for case_dir in CASES_DIR.glob("dtc_fr*"):
        case_name = case_dir.name
        log_path = RESULTS_DIR / case_name / "log.foamRun"
        config_path = case_dir / "case.toml"
        
        if not log_path.exists() or not config_path.exists():
            continue
            
        config = toml.load(config_path)
        velocity = config['parameters'].get('velocity')
        froude = config['parameters'].get('froude')
        
        logging.info(f"Processing {case_name} (Standard, Fr={froude})...")
        df = parse_forces_log(log_path)
        process_df(df, case_name, velocity, froude, results)

    # 2. Process ESI Sweep Cases (Managed by scripts/sweep_velocity_esi.py)
    # Pattern: dtc_esi_frXXX where XXX is Fr * 1000
    LPP = 5.976
    match_velocity_baseline = 1.668 # Hardcoded reference if needed
    g = 9.81

    for case_dir in CASES_DIR.glob("dtc_esi_fr*"):
        case_name = case_dir.name
        
        # Locate force data
        # ESI Tutorial typically puts it in postProcessing/forces/0/force.dat
        # But sometimes it might be just 'forces/0/force.dat' depending on OF version/func object
        dat_path = case_dir / "postProcessing/forces/0/force.dat"
        if not dat_path.exists():
             # Try alternate path?
             dat_path = case_dir / "postProcessing/forces/0/forces.dat"
        
        if not dat_path.exists():
            logging.warning(f"Data not found for {case_name}, skipping.")
            continue
            
        # Parse Fr from name
        try:
            fr_str = case_name.replace("dtc_esi_fr", "")
            froude = float(fr_str) / 1000.0
            velocity = froude * np.sqrt(g * LPP)
        except ValueError:
            logging.warning(f"Could not parse Fr from {case_name}")
            continue

        logging.info(f"Processing {case_name} (ESI, Fr={froude:.3f}, V={velocity:.3f})...")
        df = parse_forces_dat(dat_path)
        process_df(df, case_name, velocity, froude, results)

    # Save to CSV
    if results:
        out_df = pd.DataFrame(results)
        out_df = out_df.sort_values('velocity')
        out_df.to_csv(OUTPUT_FILE, index=False)
        logging.info(f"Results saved to {OUTPUT_FILE}")
        print(out_df)
    else:
        logging.warning("No results extracted.")

def process_df(df, case_name, velocity, froude, results_list):
    """Helper to average data and append to results."""
    if df.empty:
        logging.warning(f"No valid force data found for {case_name}.")
        return

    # Calculate mean over stable region (last 20%)
    if df['time'].max() > 0:
        t_end = df['time'].max()
        # Ensure we take a reasonable window, e.g., last 20% or last 5 seconds
        t_start = t_end * 0.8
        
        stable_df = df[df['time'] >= t_start]
        if stable_df.empty:
             logging.warning(f"Stable region empty for {case_name}")
             return

        mean_force = stable_df['force_total'].mean()
        std_force = stable_df['force_total'].std()
        
        results_list.append({
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

if __name__ == "__main__":
    extract_resistance()
