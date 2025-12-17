#!/usr/bin/env python3
"""
Format MODELS_CONFIG between multi-line (readable) and single-line (Docker-compatible) formats.

Usage:
    # Convert multi-line to single-line
    python format_models_config.py --to-single-line models.json

    # Convert single-line to multi-line
    python format_models_config.py --to-multi-line models.json

    # Validate JSON format
    python format_models_config.py --validate models.json
"""
import argparse
import json
import sys
from pathlib import Path


def load_json(file_path: Path) -> list[dict]:
    """Load and parse JSON from file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Try to parse as JSON directly
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)


def to_single_line(models: list[dict]) -> str:
    """Convert models to single-line JSON format (Docker-compatible)."""
    return json.dumps(models, separators=(',', ':'), ensure_ascii=False)


def to_multi_line(models: list[dict]) -> str:
    """Convert models to multi-line JSON format (readable)."""
    return json.dumps(models, indent=2, ensure_ascii=False)


def validate_models(models: list[dict]) -> bool:
    """Validate models configuration."""
    required_fields = ['id', 'name', 'model', 'category', 'description']
    valid_providers = ['huggingface', 'replicate']

    errors = []

    if not isinstance(models, list):
        errors.append("Root element must be a JSON array")
        return False

    for i, model in enumerate(models):
        if not isinstance(model, dict):
            errors.append(f"Model {i}: Must be a JSON object")
            continue

        # Check required fields
        for field in required_fields:
            if field not in model:
                errors.append(f"Model {i} ({model.get('id', 'unknown')}): Missing required field '{field}'")

        # Validate provider
        if 'provider' in model:
            provider = model['provider']
            if provider not in valid_providers:
                errors.append(
                    f"Model {i} ({model.get('id', 'unknown')}): "
                    f"Invalid provider '{provider}'. Must be one of: {', '.join(valid_providers)}"
                )

    if errors:
        print("Validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return False

    print(f"✓ Validation passed: {len(models)} model(s) are valid")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Format MODELS_CONFIG between multi-line and single-line formats'
    )
    parser.add_argument(
        'file',
        type=Path,
        help='JSON file containing models configuration'
    )
    parser.add_argument(
        '--to-single-line',
        action='store_true',
        help='Convert to single-line format (Docker-compatible)'
    )
    parser.add_argument(
        '--to-multi-line',
        action='store_true',
        help='Convert to multi-line format (readable)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate models configuration'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        help='Output file (default: stdout)'
    )

    args = parser.parse_args()

    # Load models
    models = load_json(args.file)

    # Validate if requested
    if args.validate:
        if not validate_models(models):
            sys.exit(1)
        if not args.to_single_line and not args.to_multi_line:
            return

    # Convert format
    if args.to_single_line:
        output = to_single_line(models)
        format_name = "single-line"
    elif args.to_multi_line:
        output = to_multi_line(models)
        format_name = "multi-line"
    else:
        print("Error: Must specify --to-single-line, --to-multi-line, or --validate", file=sys.stderr)
        sys.exit(1)

    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✓ Converted to {format_name} format: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
