# Python Development Guidelines

This document outlines the coding standards and best practices for Python scripts in the `openfoam-ships` repository.

## Core Principles

### 1. Exception Handling
**Rule:** Never swallow exceptions. Fail early and loudly at the source of the error.
- **Do not** use broad `try...except` blocks that pass or print a generic message without re-raising.
- **Do not** catch specific exceptions just to re-raise them as a generic `RuntimeError` or `Exception` (this obscures the original error type and stack trace).
- **Do** allow exceptions (like `FileNotFoundError`, `jinja2.TemplateError`) to propagate naturally so the workflow (e.g., Snakemake) detects the failure immediately with full context.
- **Rationale**: Debugging silent failures or generic error messages in complex simulation workflows is painful. We prefer a crash with a specific stack trace.

### 2. Path Management
**Rule:** Always use `pathlib.Path` for file system operations.
- **Do not** use `os.path.join`, `os.path.exists`, `glob.glob` (string-based steps).
- **Do** use `Path(path).clean()`, `/` operator for joining, `Path.exists()`, `Path.glob()`.
- **Rationale**: `pathlib` offers an object-oriented interface that is less error-prone and cross-platform compatible.

### 3. Templating
**Rule:** Use `jinja2` for generating all configuration files.
- **Do not** use Python string formatting (`f-strings` or `.format()`) for complex file generation.
- **Do** separate logic from data by creating `.j2` templates and rendering them with a context dictionary.
- **Rationale**: OpenFOAM configuration files are complex; separating them keeps Python code clean and allows logic (loops, conditionals) within the config file structure itself.

### 4. Command Line Interfaces
**Rule:** Use `click` for parsing command line arguments.
- **Do not** use `sys.argv` or `argparse`.
- **Do** use `@click.command()` and `@click.argument/option` decorators.
- **Rationale**: `click` provides a composable, declarative interface that handles help messages and type conversion automatically.

### 6. Logging
**Rule:** Use the `logging` module instead of `print`.
- **Do not** use `print()` for status updates or debugging.
- **Do** configure `logging.basicConfig(level=logging.INFO)` and use `logging.info()`, `logging.warning()`, etc.
- **Rationale**: Logging provides timestamps, log levels (INFO, DEBUG, ERROR), and can be easily redirected to files or suppressed without changing code.

## Example

```python
import click
from pathlib import Path
from jinja2 import Template

@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output_path", type=click.Path(path_type=Path))
def process_file(input_path: Path, output_path: Path):
    """Process an input file and generate an output."""
    # Fail early if validation fails (Click handles path existence above for input)
    if not input_path.suffix == ".toml":
        raise ValueError(f"Input file must be .toml, got {input_path.suffix}")

    # ... logic ...

if __name__ == "__main__":
    process_file()
```
