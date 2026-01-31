#!/usr/bin/env python3
import subprocess
import os
import re

cases = ["cases/dtc_esi_fr180", "cases/dtc_esi_fr200", "cases/dtc_esi_fr220"]
cmd = "docker run --rm -u 1000 -v /Users/baart_f/src/openfoam-ships:/data -w /data openfoam-ships:2506 /bin/bash -c 'source /usr/lib/openfoam/openfoam2506/etc/bashrc && cd /data/{case} && postProcess -time 35'"

# Function to patch controlDict
def patch_controldict(case_path):
    cd_path = os.path.join(case_path, "system", "controlDict")
    try:
        with open(cd_path, "r") as f:
            content = f.read()
        
        # Check if pName already exists
        if "pName" in content:
            print(f"Skipping patch for {case_path} (pName present)")
            return

        # Insert pName and UName into the forces block
        # Look for 'rhoInf' which is unique to forces usually
        new_content = content.replace("rhoInf", "pName p_rgh;\n        UName U;\n        rhoInf")
        
        with open(cd_path, "w") as f:
            f.write(new_content)
        print(f"Patched {cd_path}")
    except Exception as e:
        print(f"Error patching {cd_path}: {e}")

for case in cases:
    print(f"Processing {case}...")
    patch_controldict(case)
    
    # Remove system/forces if I created it earlier
    sf = os.path.join(case, "system", "forces")
    if os.path.exists(sf):
        os.remove(sf)

    full_cmd = cmd.format(case=case)
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        print(f"Error: {e}")
