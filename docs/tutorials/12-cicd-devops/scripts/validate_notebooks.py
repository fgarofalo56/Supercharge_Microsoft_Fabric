#!/usr/bin/env python3
"""
Validate Fabric notebook syntax and structure.

This script validates Microsoft Fabric notebooks before deployment:
- Checks Python syntax in notebook cells
- Verifies required metadata files exist
- Validates notebook structure

Usage:
    python validate_notebooks.py --path fabric/dev

Author: Fabric POC Team
Version: 1.0.0
"""

import os
import sys
import json
import argparse
import ast
from pathlib import Path
from typing import List, Tuple, Optional


def validate_python_syntax(code: str, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Python syntax in notebook cells.

    Args:
        code: Python code to validate
        filename: Source filename for error reporting

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"{filename}: Syntax error at line {e.lineno}: {e.msg}"


def preprocess_notebook_code(code: str) -> str:
    """
    Preprocess notebook code to handle magic commands and shell commands.

    Magic commands (%) and shell commands (!) are not valid Python
    and need to be removed or commented for syntax validation.

    Args:
        code: Raw notebook code

    Returns:
        Preprocessed code safe for ast.parse
    """
    lines = []
    for line in code.split('\n'):
        stripped = line.strip()
        # Skip magic commands and shell commands
        if stripped.startswith('%') or stripped.startswith('!'):
            # Replace with empty line to preserve line numbers
            lines.append('')
        # Skip Spark SQL magic blocks
        elif stripped.startswith('%%'):
            lines.append('')
        else:
            lines.append(line)
    return '\n'.join(lines)


def validate_notebook(notebook_path: Path) -> List[str]:
    """
    Validate a Fabric notebook.

    Args:
        notebook_path: Path to notebook directory

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    notebook_name = notebook_path.name

    # Check for notebook content file
    content_file = notebook_path / "notebook-content.py"
    if not content_file.exists():
        # Try JSON format
        content_file = notebook_path / "notebook-content.json"
        if not content_file.exists():
            # Try ipynb format
            content_file = notebook_path / "content.ipynb"

    if not content_file.exists():
        errors.append(f"{notebook_name}: Missing notebook content file")
        return errors

    # Validate based on file type
    if content_file.suffix == ".py":
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            errors.append(f"{notebook_name}: Unable to read file (encoding issue)")
            return errors

        # Preprocess to handle magic commands
        processed_code = preprocess_notebook_code(code)

        # Validate syntax
        valid, error = validate_python_syntax(processed_code, str(content_file))
        if not valid:
            errors.append(error)

    elif content_file.suffix == ".json" or content_file.suffix == ".ipynb":
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                notebook_json = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{notebook_name}: Invalid JSON - {e}")
            return errors
        except UnicodeDecodeError:
            errors.append(f"{notebook_name}: Unable to read file (encoding issue)")
            return errors

        # If it's a Jupyter notebook format, validate code cells
        if "cells" in notebook_json:
            for i, cell in enumerate(notebook_json.get("cells", [])):
                if cell.get("cell_type") == "code":
                    source = cell.get("source", [])
                    if isinstance(source, list):
                        code = ''.join(source)
                    else:
                        code = source

                    processed_code = preprocess_notebook_code(code)
                    valid, error = validate_python_syntax(
                        processed_code,
                        f"{notebook_name} cell {i+1}"
                    )
                    if not valid:
                        errors.append(error)

    # Check for .platform metadata file
    platform_file = notebook_path / ".platform"
    if not platform_file.exists():
        errors.append(f"{notebook_name}: Missing .platform metadata file")

    return errors


def validate_pipeline(pipeline_path: Path) -> List[str]:
    """
    Validate a Fabric Data Pipeline.

    Args:
        pipeline_path: Path to pipeline directory

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    pipeline_name = pipeline_path.name

    # Check for pipeline content file
    content_file = pipeline_path / "pipeline-content.json"
    if not content_file.exists():
        content_file = pipeline_path / "definition.json"

    if not content_file.exists():
        errors.append(f"{pipeline_name}: Missing pipeline definition file")
        return errors

    # Validate JSON structure
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            pipeline_json = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{pipeline_name}: Invalid JSON - {e}")
        return errors

    # Check for required fields
    if "name" not in pipeline_json and "properties" not in pipeline_json:
        errors.append(f"{pipeline_name}: Missing required pipeline properties")

    # Check for .platform file
    platform_file = pipeline_path / ".platform"
    if not platform_file.exists():
        errors.append(f"{pipeline_name}: Missing .platform metadata file")

    return errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Fabric notebooks and pipelines'
    )
    parser.add_argument(
        '--path',
        required=True,
        help='Path to fabric items directory'
    )
    parser.add_argument(
        '--type',
        choices=['all', 'notebooks', 'pipelines'],
        default='all',
        help='Type of items to validate'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    args = parser.parse_args()

    root_path = Path(args.path)
    if not root_path.exists():
        print(f"Error: Path does not exist: {root_path}")
        sys.exit(1)

    all_errors = []
    validated_count = 0

    # Find and validate notebooks
    if args.type in ['all', 'notebooks']:
        for item in root_path.iterdir():
            if item.is_dir() and item.name.endswith('.Notebook'):
                if args.verbose:
                    print(f"Validating notebook: {item.name}")
                errors = validate_notebook(item)
                all_errors.extend(errors)
                validated_count += 1

    # Find and validate pipelines
    if args.type in ['all', 'pipelines']:
        for item in root_path.iterdir():
            if item.is_dir() and item.name.endswith('.DataPipeline'):
                if args.verbose:
                    print(f"Validating pipeline: {item.name}")
                errors = validate_pipeline(item)
                all_errors.extend(errors)
                validated_count += 1

    # Report results
    print("")
    print("=" * 50)
    print("VALIDATION RESULTS")
    print("=" * 50)
    print(f"Items validated: {validated_count}")
    print(f"Errors found: {len(all_errors)}")
    print("")

    if all_errors:
        print("VALIDATION FAILED:")
        print("")
        for error in all_errors:
            print(f"  ❌ {error}")
        print("")
        sys.exit(1)
    else:
        print("✅ All items validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
