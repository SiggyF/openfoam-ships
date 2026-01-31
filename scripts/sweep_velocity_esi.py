#!/usr/bin/env python3
import os
import shutil
import math
import subprocess
import argparse
import sys

def calculate_velocity(fr, Lpp=5.976, g=9.81):
    """Calculate velocity U from Froude number."""
    return fr * math.sqrt(g * Lpp)

def sed_replace(file_path, search_str, replace_str):
    """Replace string in file using sed-like logic (reading whole file)."""
    with open(file_path, 'r') as f:
        content = f.read()
    new_content = content.replace(search_str, replace_str)
    with open(file_path, 'w') as f:
        f.write(new_content)

def main():
    parser = argparse.ArgumentParser(description="Run Velocity Sweep for DTC ESI")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only")
    parser.add_argument("--base-case", default="cases/dtc_esi_baseline", help="Source baseline case")
    parser.add_argument("--froude", nargs="+", type=float, default=[0.18, 0.20, 0.22], help="List of Fr to run")
    args = parser.parse_args()

    # Constants
    LPP = 5.976
    match_velocity = 1.668 # Context: The value found in 0.orig/U of the baseline
    
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    runner_script = os.path.join(scripts_dir, "run_esi_case.py")

    for fr in args.froude:
        target_u = calculate_velocity(fr, LPP)
        case_name = f"dtc_esi_fr{int(fr*1000)}"
        case_dir = f"cases/{case_name}"
        
        print(f"\n--- Preparing Case: {case_name} (Fr={fr:.3f}, U={target_u:.4f} m/s) ---")
        
        if not args.dry_run:
            if os.path.exists(case_dir):
                print(f"Directory {case_dir} exists. Skipping/Overwriting? (Assumed safe or manual clean needed)")
                # Ideally check or clean. For now, we assume user manages repeated runs or we overwrite.
            else:
                print(f"Cloning {args.base_case} to {case_dir}...")
                shutil.copytree(args.base_case, case_dir)
            
            # Update U
            u_file = os.path.join(case_dir, "0.orig/U")
            # The baseline has "Umean 1.668;"
            # We replace "1.668" with new value
            sed_replace(u_file, "1.668", f"{target_u:.5f}")
            sed_replace(u_file, "-1.668", f"{-target_u:.5f}") # mUmean
            
            # NOTE: dynamicMeshDict damping might need adjustment? 
            # For now keeping it constant as part of the "baseline methodology".
            
            # Execution
            cmd = f"python3 {runner_script} --case-dir {case_dir}"
            print(f"executing: {cmd}")
            ret = subprocess.call(cmd, shell=True)
            if ret != 0:
                print(f"Error running {case_name}")
        else:
            print(f"[Dry Run] Would clone {args.base_case} -> {case_dir}")
            print(f"[Dry Run] Would update U: 1.668 -> {target_u:.5f}")
            print(f"[Dry Run] Would exec: python3 {runner_script} --case-dir {case_dir}")

if __name__ == "__main__":
    main()
