#!/usr/bin/env python3
"""
Fetch Replicate model schema from API.

This utility fetches a model's input/output schema from Replicate's API
and outputs it in the format expected by our configuration files.

Usage:
    python scripts/fetch_replicate_schema.py flux-kontext-apps/restore-image
    python scripts/fetch_replicate_schema.py google/upscaler
"""
import argparse
import json
import sys
from typing import Any

import requests


def fetch_model_schema(model_path: str, api_token: str | None = None) -> dict[str, Any]:
    """
    Fetch model schema from Replicate API.

    Args:
        model_path: Model path in format "owner/model-name"
        api_token: Optional Replicate API token for authenticated requests

    Returns:
        Model schema dictionary

    Raises:
        ValueError: If model path is invalid
        requests.HTTPError: If API request fails
    """
    if "/" not in model_path:
        raise ValueError("Model path must be in format 'owner/model-name'")

    owner, model_name = model_path.split("/", 1)

    # Fetch model info from Replicate API
    url = f"https://api.replicate.com/v1/models/{owner}/{model_name}"

    headers = {}
    if api_token:
        headers["Authorization"] = f"Token {api_token}"

    print(f"Fetching model info from: {url}", file=sys.stderr)
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    model_data = response.json()

    # Get latest version schema
    latest_version = model_data.get("latest_version")
    if not latest_version:
        raise ValueError("Model has no latest_version")

    openapi_schema = latest_version.get("openapi_schema")
    if not openapi_schema:
        raise ValueError("Model has no openapi_schema")

    # Extract input schema
    input_schema_ref = openapi_schema.get("components", {}).get("schemas", {}).get("Input")
    if not input_schema_ref:
        raise ValueError("Model has no Input schema")

    # Parse input properties
    properties = input_schema_ref.get("properties", {})
    required = input_schema_ref.get("required", [])

    # Try to identify the image input parameter
    image_param_name = None
    for prop_name, prop_schema in properties.items():
        # Look for properties with format: uri or type: string with image-like names
        if prop_schema.get("format") == "uri" or "image" in prop_name.lower():
            image_param_name = prop_name
            break

    if not image_param_name:
        # Default to first parameter if can't detect
        image_param_name = list(properties.keys())[0] if properties else "image"
        print(f"Warning: Could not detect image parameter, using '{image_param_name}'", file=sys.stderr)

    # Build parameter list (exclude image parameter)
    parameters = []
    for prop_name, prop_schema in properties.items():
        if prop_name == image_param_name:
            continue

        param = {
            "name": prop_name,
            "type": map_json_type_to_schema_type(prop_schema),
            "required": prop_name in required,
            "description": prop_schema.get("description", ""),
        }

        # Add type-specific fields
        if "default" in prop_schema:
            param["default"] = prop_schema["default"]

        if "enum" in prop_schema:
            param["values"] = prop_schema["enum"]

        if "minimum" in prop_schema:
            param["min"] = prop_schema["minimum"]

        if "maximum" in prop_schema:
            param["max"] = prop_schema["maximum"]

        # UI hints (you'll need to configure these manually)
        param["ui_hidden"] = False
        param["ui_group"] = None

        parameters.append(param)

    # Build replicate_schema
    replicate_schema = {
        "input": {
            "image": {
                "param_name": image_param_name,
                "type": "uri",
                "format": "image",
                "required": True,
                "description": properties.get(image_param_name, {}).get("description", "Input image"),
            },
            "parameters": parameters,
        },
        "output": {
            "type": "uri",  # Most image models output URIs
            "format": "image",
        },
        "custom": {
            "max_file_size_mb": 10,
            "supported_formats": ["jpg", "jpeg", "png"],
            "estimated_time_seconds": None,
        }
    }

    return replicate_schema


def map_json_type_to_schema_type(prop_schema: dict[str, Any]) -> str:
    """
    Map JSON schema type to our parameter type.

    Args:
        prop_schema: Property schema from OpenAPI

    Returns:
        Parameter type string
    """
    json_type = prop_schema.get("type", "string")

    if "enum" in prop_schema:
        return "enum"

    type_map = {
        "integer": "integer",
        "number": "float",
        "boolean": "boolean",
        "string": "string",
    }

    return type_map.get(json_type, "string")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch Replicate model schema and output configuration JSON"
    )
    parser.add_argument(
        "model_path",
        help="Replicate model path (e.g., 'flux-kontext-apps/restore-image')"
    )
    parser.add_argument(
        "--token",
        help="Replicate API token (optional, uses REPLICATE_API_TOKEN env var if not provided)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Get API token
    api_token = args.token
    if not api_token:
        import os
        api_token = os.getenv("REPLICATE_API_TOKEN")

    try:
        # Fetch schema
        schema = fetch_model_schema(args.model_path, api_token)

        # Format output
        output_json = json.dumps({"replicate_schema": schema}, indent=2)

        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
            print(f"Schema written to {args.output}", file=sys.stderr)
        else:
            print(output_json)

        print("\nNote: Please review and adjust the following manually:", file=sys.stderr)
        print("  - ui_hidden flags for parameters", file=sys.stderr)
        print("  - ui_group assignments", file=sys.stderr)
        print("  - custom.max_file_size_mb", file=sys.stderr)
        print("  - custom.supported_formats", file=sys.stderr)
        print("  - custom.estimated_time_seconds", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
