#!/usr/bin/env python3
"""
Configuration documentation generator.

Generates comprehensive documentation from Pydantic config schemas.

Usage:
    python scripts/generate_config_docs.py --output docs/configuration.md
    python scripts/generate_config_docs.py --format json --output config/schema.json
    python scripts/generate_config_docs.py --help
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_schema import ConfigFile
from pydantic.json_schema import JsonSchemaValue

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def format_type(type_info: Any) -> str:
    """Format type information for display."""
    if isinstance(type_info, str):
        return type_info
    elif isinstance(type_info, list):
        return " | ".join(str(t) for t in type_info)
    elif isinstance(type_info, dict):
        if "type" in type_info:
            return str(type_info["type"])
        elif "anyOf" in type_info:
            return " | ".join(format_type(t) for t in type_info["anyOf"])
    return str(type_info)


def generate_markdown_docs(schema: dict[str, Any]) -> str:
    """
    Generate markdown documentation from JSON schema.

    Args:
        schema: JSON schema dictionary

    Returns:
        Markdown documentation string
    """
    lines = [
        "# Configuration Reference",
        "",
        f"Auto-generated configuration documentation. Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Table of Contents",
        "",
    ]

    # Generate table of contents
    if "properties" in schema:
        for section_name in schema["properties"].keys():
            section_title = section_name.replace("_", " ").title()
            lines.append(f"- [{section_title}](#{section_name})")
    lines.append("")

    # Introduction
    lines.extend(
        [
            "## Overview",
            "",
            "This document provides a complete reference for all configuration options in the Photo Restoration API.",
            "",
            "Configuration is loaded from JSON files in the `config/` directory based on the `APP_ENV` environment variable.",
            "",
            "**Loading Priority** (highest to lowest):",
            "1. Environment variables (from `.env` file)",
            "2. Environment-specific config (`config/{APP_ENV}.json`)",
            "3. Default config (`config/default.json`)",
            "",
            "## Configuration Sections",
            "",
        ]
    )

    # Generate sections
    if "properties" in schema:
        definitions = schema.get("$defs", {})

        for section_name, section_schema in schema["properties"].items():
            section_title = section_name.replace("_", " ").title()
            lines.extend([f"## {section_title}", "", f"<a id=\"{section_name}\"></a>", ""])

            # Get section description
            if "description" in section_schema:
                lines.extend([section_schema["description"], ""])

            # Handle $ref
            if "$ref" in section_schema:
                ref_name = section_schema["$ref"].split("/")[-1]
                if ref_name in definitions:
                    section_schema = definitions[ref_name]

            # List properties
            if "properties" in section_schema:
                for prop_name, prop_schema in section_schema["properties"].items():
                    full_name = f"{section_name}.{prop_name}"

                    # Handle nested $ref
                    if "$ref" in prop_schema:
                        ref_name = prop_schema["$ref"].split("/")[-1]
                        if ref_name in definitions:
                            prop_schema = definitions[ref_name]

                    # Property header
                    lines.append(f"### `{full_name}`")
                    lines.append("")

                    # Description
                    if "description" in prop_schema:
                        lines.append(prop_schema["description"])
                        lines.append("")

                    # Type
                    prop_type = format_type(prop_schema.get("type", "any"))
                    if "anyOf" in prop_schema:
                        types = [t.get("type", "any") for t in prop_schema["anyOf"]]
                        prop_type = " | ".join(types)
                    lines.append(f"- **Type:** `{prop_type}`")

                    # Required
                    is_required = prop_name in section_schema.get("required", [])
                    lines.append(f"- **Required:** {'Yes' if is_required else 'No'}")

                    # Default
                    if "default" in prop_schema:
                        default = prop_schema["default"]
                        if isinstance(default, str):
                            default = f'"{default}"'
                        elif isinstance(default, (list, dict)):
                            default = json.dumps(default)
                        lines.append(f"- **Default:** `{default}`")

                    # Constraints
                    if "minimum" in prop_schema:
                        lines.append(f"- **Minimum:** `{prop_schema['minimum']}`")
                    if "maximum" in prop_schema:
                        lines.append(f"- **Maximum:** `{prop_schema['maximum']}`")
                    if "minLength" in prop_schema:
                        lines.append(f"- **Min Length:** `{prop_schema['minLength']}`")
                    if "maxLength" in prop_schema:
                        lines.append(f"- **Max Length:** `{prop_schema['maxLength']}`")
                    if "pattern" in prop_schema:
                        lines.append(f"- **Pattern:** `{prop_schema['pattern']}`")

                    # Enum/Choices
                    if "enum" in prop_schema:
                        choices = ", ".join(f'"{c}"' for c in prop_schema["enum"])
                        lines.append(f"- **Choices:** {choices}")

                    # Environment variable override
                    env_var = f"{section_name.upper()}_{prop_name.upper()}"
                    lines.append(f"- **Environment Override:** `{env_var}`")

                    lines.append("")

            lines.append("---")
            lines.append("")

    # Examples section
    lines.extend(
        [
            "## Examples",
            "",
            "### Minimal Configuration",
            "",
            "```json",
            "{",
            '  "application": {',
            '    "name": "Photo Restoration API"',
            "  },",
            '  "models": [',
            "    {",
            '      "id": "swin2sr-2x",',
            '      "name": "Swin2SR 2x",',
            '      "model": "caidas/swin2SR-classical-sr-x2-64",',
            '      "provider": "huggingface",',
            '      "category": "upscale",',
            '      "description": "Fast 2x upscaling"',
            "    }",
            "  ]",
            "}",
            "```",
            "",
            "### Production Configuration",
            "",
            "See `config/production.json.example` for a complete production example.",
            "",
            "### Development Configuration",
            "",
            "See `config/development.json.example` for a development example with debug settings.",
            "",
            "## Secrets",
            "",
            "The following values should **never** be in config files. They must be in the `.env` file:",
            "",
            "- `HF_API_KEY` - HuggingFace API key",
            "- `REPLICATE_API_TOKEN` - Replicate API token",
            "- `SECRET_KEY` - JWT secret key (minimum 32 characters)",
            "- `AUTH_USERNAME` - Authentication username",
            "- `AUTH_PASSWORD` - Authentication password",
            "",
            "## Validation",
            "",
            "Validate your configuration:",
            "",
            "```bash",
            "python scripts/validate_config.py --env production",
            "```",
            "",
            "## Migration",
            "",
            "Migrate from `.env` to JSON config:",
            "",
            "```bash",
            "python scripts/migrate_env_to_config.py --env-file .env --output config/production.json",
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Main documentation generator."""
    parser = argparse.ArgumentParser(
        description="Generate configuration documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate markdown documentation
  python scripts/generate_config_docs.py --output docs/configuration.md

  # Generate JSON schema for IDE autocomplete
  python scripts/generate_config_docs.py --format json --output config/schema.json

  # Generate both
  python scripts/generate_config_docs.py --output docs/configuration.md --format both
        """,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/configuration.md"),
        help="Output file path (default: docs/configuration.md)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "json", "both"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    try:
        logger.info("Generating configuration documentation...")

        # Get JSON schema from Pydantic model
        schema = ConfigFile.model_json_schema()

        # Generate markdown documentation
        if args.format in ("markdown", "both"):
            markdown_output = args.output if args.format == "markdown" else Path("docs/configuration.md")
            markdown_content = generate_markdown_docs(schema)

            markdown_output.parent.mkdir(parents=True, exist_ok=True)
            with open(markdown_output, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            logger.info(f"✓ Generated markdown documentation: {markdown_output}")

        # Generate JSON schema
        if args.format in ("json", "both"):
            json_output = Path("config/schema.json") if args.format == "both" else args.output
            json_content = json.dumps(schema, indent=2)

            json_output.parent.mkdir(parents=True, exist_ok=True)
            with open(json_output, "w", encoding="utf-8") as f:
                f.write(json_content)

            logger.info(f"✓ Generated JSON schema: {json_output}")

        logger.info("\nDocumentation generation complete!")
        return 0

    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
