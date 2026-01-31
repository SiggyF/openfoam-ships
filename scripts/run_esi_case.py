#!/usr/bin/env python3
import subprocess
import argparse
import os
import sys

def run_command(cmd, dry_run=False):
    print(f"Running: {cmd}")
    if not dry_run:
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Error executing command: {cmd}")
            sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="Run OpenFOAM ESI Case with 6-step refinement loop.")
    parser.add_argument("--case-dir", default="cases/dtc_esi_baseline", help="Path to the case directory")
    parser.add_argument("--image", default="openfoam-ships:2506", help="Docker image to use")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()

    abs_case_dir = os.path.abspath(args.case_dir)
    container_mount = "/mnt/case"
    
    # OpenFOAM environment setup
    foam_bashrc = "/usr/lib/openfoam/openfoam2506/etc/bashrc"
    
    # Construct the chain of OpenFOAM commands
    # 1. Setup
    cmds = [f"source {foam_bashrc}", f"cd {container_mount}"]
    
    # 2. Cleanup (optional, maybe safe to skip or make explicitly requested? Let's assume clean start or overwrite)
    # cmds.append("rm -rf constant/polyMesh 0") 
    # For now, we assume user cleans if needed, or we add a --clean flag. 
    # But Allrun.esi_template implies overwrite.
    
    # 3. Pre-processing
    cmds.append("surfaceFeatureExtract")
    cmds.append("blockMesh")
    
    # 4. Refinement Loop (1 to 6)
    for i in range(1, 7):
        cmds.append(f"topoSet -dict system/topoSetDict.{i}")
        cmds.append("refineMesh -dict system/refineMeshDict -overwrite")
        
    # 5. Snappy
    cmds.append("snappyHexMesh -overwrite")
    
    # 6. Solver Setup
    cmds.append("rm -rf 0") # dynamicMeshDict might be in constant, ensuring clean 0 start
    cmds.append("cp -r 0.orig 0") # Standard restore0Dir equivalent
    cmds.append("setFields")
    cmds.append("rm -rf processor*") # Clean up old processor directories
    cmds.append("decomposePar")
    cmds.append("renumberMesh -overwrite")
    
    # 7. Solver
    cmds.append("mpirun -np 8 interFoam -parallel")
    
    # 8. Reconstruct
    cmds.append("reconstructPar")

    # Combine into single bash command string
    full_cmd_str = " && ".join(cmds)
    
    # Docker Run Command
    docker_cmd = f"docker run --rm -u 1000 -v {abs_case_dir}:{container_mount} -w {container_mount} {args.image} /bin/bash -c \"{full_cmd_str}\""
    
    run_command(docker_cmd, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
