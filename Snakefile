import glob
from pathlib import Path

# --- Configuration ---
CASES_DIR = Path("cases")
BUILD_DIR = Path("build")
RESULTS_DIR = Path("results")

# Discover all case.toml files
# Format: cases/{case_name}/case.toml
CASE_FILES = glob.glob(str(CASES_DIR / "**" / "case.toml"), recursive=True)
CASE_NAMES = [Path(f).parent.name for f in CASE_FILES]

# --- Rules ---

rule all:
    input:
        expand(RESULTS_DIR / "{case_name}" / "visualization.png", case_name=CASE_NAMES)

rule prepare_case:
    input:
        config = CASES_DIR / "{case_name}" / "case.toml",
        script = "workflows/scripts/prepare_case.py"
    output:
        directory(BUILD_DIR / "{case_name}")
    shell:
        """
        uv run python {input.script} {input.config} {output}
        """

rule run_case:
    input:
        case_dir = BUILD_DIR / "{case_name}"
    output:
        log = RESULTS_DIR / "{case_name}" / "log.foamRun"
    params:
        image = "openfoam-ships:latest",
        results_root = lambda wc: str(RESULTS_DIR / wc.case_name)
    shell:
        """
        # 1. Setup Results Directory
        rm -rf {params.results_root}
        mkdir -p {params.results_root}
        # Copy build files to results
        cp -r {input.case_dir}/* {params.results_root}/
        
        # 2. Permission fix (ensure Docker can write)
        chmod -R 777 {params.results_root}
        
        # 3. Run Docker
        # echo "Starting Docker simulation for {wildcards.case_name}..." > {output.log} # CAUSES SKIP
        
        # We use absolute paths for Docker volume
        # Actually, simpler to just use $(pwd)/{params.results_root}
        docker run --rm \
            -v "$(pwd)/{params.results_root}:/home/openfoam/run/case" \
            -w /home/openfoam/run/case \
            {params.image} \
            /bin/bash -c "ls -la && ./Allrun" > {params.results_root}/wrapper.log 2>&1 || true
        """

rule visualize:
    input:
        log = RESULTS_DIR / "{case_name}" / "log.foamRun",
        script = "workflows/scripts/visualize.py"
    output:
        png = RESULTS_DIR / "{case_name}" / "visualization.png"
    params:
        case_dir = lambda wc: str(RESULTS_DIR / wc.case_name)
    shell:
        """
        uv run python {input.script} {params.case_dir} $(dirname {output.png})
        """
