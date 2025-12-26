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
        log = RESULTS_DIR / "{case_name}" / "log.interFoam",
        dummy_time = directory(RESULTS_DIR / "{case_name}" / "0.1")
    params:
        image = "openfoam/openfoam13-graphical" 
    shell:
        """
        # Placeholder for Docker execution
        # We simulate a run by creating a log and a dummy time directory
        mkdir -p $(dirname {output.log})
        echo "Starting simulation for {wildcards.case_name}" > {output.log}
        echo "Using image {params.image}" >> {output.log}
        
        # Create dummy time dir for visualization sensing
        mkdir -p {output.dummy_time}
        """

rule visualize:
    input:
        log = RESULTS_DIR / "{case_name}" / "log.interFoam",
        dummy_time = RESULTS_DIR / "{case_name}" / "0.1",
        script = "workflows/scripts/visualize.py"
    output:
        png = RESULTS_DIR / "{case_name}" / "visualization.png"
    params:
        case_dir = lambda wc: str(RESULTS_DIR / wc.case_name)
    shell:
        """
        uv run python {input.script} {params.case_dir} $(dirname {output.png})
        """
