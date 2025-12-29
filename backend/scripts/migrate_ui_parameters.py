#!/usr/bin/env python3
"""
Migration script for Custom Model Parameters UI feature.

This script helps migrate existing model configurations to include ui_hidden flags
and optionally configure custom UI controls for parameters.

Usage:
    python scripts/migrate_ui_parameters.py [--config CONFIG_FILE] [--interactive] [--backup]

Options:
    --config PATH       Config file to migrate (default: config/production.json)
    --interactive       Ask questions to configure custom UI controls
    --backup            Create backup before modifying files (default: True)
    --output PATH       Output file path (default: creates local.json)
    --dry-run           Show what would change without modifying files
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import shutil


class ConfigMigrator:
    """Migrates model configurations to support UI parameter controls."""

    # Common parameters that should be hidden by default
    HIDDEN_BY_DEFAULT = {
        'seed', 'random_seed', 'safety_tolerance', 'webhook',
        'webhook_url', 'callback_url', 'api_key', 'token'
    }

    def __init__(self, config_path: Path, interactive: bool = False, dry_run: bool = False):
        self.config_path = config_path
        self.interactive = interactive
        self.dry_run = dry_run
        self.changes: List[str] = []

    def load_config(self) -> Dict[str, Any]:
        """Load configuration file with error handling."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate basic structure
            if not isinstance(config, dict):
                raise ValueError(f"Config must be a JSON object, got {type(config).__name__}")

            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid file encoding (expected UTF-8): {e}") from e
        except Exception as e:
            raise RuntimeError(f"Error reading config file: {e}") from e

    def save_config(self, config: Dict[str, Any], output_path: Path) -> None:
        """Save configuration file with atomic write for safety."""
        if self.dry_run:
            print(f"\n[DRY RUN] Would write to: {output_path}")
            print(json.dumps(config, indent=2))
            return

        # Validate config before writing
        try:
            # Test that config is JSON-serializable
            json_str = json.dumps(config, indent=2)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Config contains non-JSON-serializable data: {e}") from e

        # Atomic write: write to temp file, then rename
        temp_path = output_path.with_suffix('.tmp')
        try:
            # Write to temporary file first
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
                f.write('\n')  # Add trailing newline
                f.flush()  # Ensure data is written
                import os
                os.fsync(f.fileno())  # Sync to disk

            # Atomic rename (works on all platforms)
            temp_path.replace(output_path)

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass  # Best effort cleanup
            raise RuntimeError(f"Error writing config file: {e}") from e

    def backup_config(self) -> None:
        """Create backup of original config file with error handling."""
        if self.dry_run:
            print(f"[DRY RUN] Would create backup of {self.config_path}")
            return

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.config_path.with_suffix(f'.json.backup_{timestamp}')

            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file with metadata preservation
            shutil.copy2(self.config_path, backup_path)

            # Verify backup was created successfully
            if not backup_path.exists():
                raise RuntimeError("Backup file was not created")

            # Verify backup has same size as original
            if backup_path.stat().st_size != self.config_path.stat().st_size:
                backup_path.unlink()  # Remove incomplete backup
                raise RuntimeError("Backup file size mismatch")

            print(f"✅ Backup created: {backup_path}")

        except Exception as e:
            raise RuntimeError(f"Failed to create backup: {e}") from e

    def should_hide_parameter(self, param_name: str) -> bool:
        """Determine if parameter should be hidden by default."""
        param_lower = param_name.lower()
        return any(hidden in param_lower for hidden in self.HIDDEN_BY_DEFAULT)

    def detect_ui_control_type(self, param: Dict[str, Any]) -> str:
        """Auto-detect appropriate UI control type from parameter schema."""
        param_type = param.get('type', 'string')

        # Boolean → toggle
        if param_type == 'boolean':
            return 'toggle'

        # Enum → radio (2-3 options) or dropdown (4+)
        if param_type == 'enum':
            values = param.get('values', [])
            return 'radio' if len(values) <= 3 else 'dropdown'

        # Integer/float with range → slider
        if param_type in ['integer', 'float']:
            has_range = 'min' in param and 'max' in param
            return 'slider' if has_range else 'number'

        # String → text
        return 'text'

    def format_label(self, param_name: str) -> str:
        """Convert snake_case parameter name to Title Case label."""
        return ' '.join(word.capitalize() for word in param_name.split('_'))

    def ask_ui_config(self, param: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Interactively ask user to configure UI control for a parameter."""
        param_name = param['name']
        param_type = param.get('type', 'string')
        default_value = param.get('default')
        description = param.get('description', '')

        print(f"\n{'='*60}")
        print(f"Parameter: {param_name}")
        print(f"Type: {param_type}")
        if default_value is not None:
            print(f"Default: {default_value}")
        if description:
            print(f"Description: {description}")

        # Ask if should be visible
        visible = input("\n  Show in UI? [Y/n]: ").strip().lower()
        if visible == 'n':
            return {'ui_hidden': True}

        # Auto-detect control type
        auto_type = self.detect_ui_control_type(param)
        print(f"\n  Auto-detected control type: {auto_type}")

        custom_type = input(f"  UI control type (auto/text/textarea/number/slider/dropdown/radio/toggle/checkbox) [{auto_type}]: ").strip()

        # Validate control type
        valid_types = ['text', 'textarea', 'number', 'slider', 'dropdown', 'radio', 'toggle', 'checkbox']
        if custom_type and custom_type != 'auto' and custom_type not in valid_types:
            print(f"  ⚠️  Invalid control type '{custom_type}', using auto-detected '{auto_type}'")
            control_type = auto_type
        else:
            control_type = custom_type if custom_type and custom_type != 'auto' else auto_type

        # Build UI control config
        ui_control: Dict[str, Any] = {'type': control_type}

        # Custom label
        auto_label = self.format_label(param_name)
        custom_label = input(f"  Label [{auto_label}]: ").strip()
        if custom_label:
            ui_control['label'] = custom_label

        # Help text
        custom_help = input(f"  Help text [{description[:50]}...]: ").strip()
        if custom_help:
            ui_control['help'] = custom_help

        # Options for dropdown/radio
        if control_type in ['dropdown', 'radio'] and 'values' in param:
            print(f"  Available options: {', '.join(param['values'])}")
            custom_options = input("  Custom order (comma-separated, blank=default): ").strip()
            if custom_options:
                ui_control['options'] = [opt.strip() for opt in custom_options.split(',')]

        # Step for number/slider
        if control_type in ['number', 'slider']:
            custom_step = input("  Step size (blank=default): ").strip()
            if custom_step:
                try:
                    ui_control['step'] = float(custom_step) if '.' in custom_step else int(custom_step)
                except ValueError:
                    pass

        # Marks for slider
        if control_type == 'slider' and 'min' in param and 'max' in param:
            add_marks = input("  Add slider marks? [y/N]: ").strip().lower()
            if add_marks == 'y':
                marks = {}
                min_val = param['min']
                max_val = param['max']
                mid_val = (min_val + max_val) // 2

                min_label = input(f"  Label for {min_val}: ").strip()
                if min_label:
                    marks[str(min_val)] = min_label

                mid_label = input(f"  Label for {mid_val}: ").strip()
                if mid_label:
                    marks[str(mid_val)] = mid_label

                max_label = input(f"  Label for {max_val}: ").strip()
                if max_label:
                    marks[str(max_val)] = max_label

                if marks:
                    ui_control['marks'] = marks

        # Display order
        custom_order = input("  Display order (blank=auto): ").strip()
        if custom_order:
            try:
                order_value = int(custom_order)
                if order_value < 0:
                    print("  ⚠️  Order must be non-negative, skipping")
                else:
                    ui_control['order'] = order_value
            except ValueError:
                print(f"  ⚠️  Invalid order value '{custom_order}', must be an integer")

        return {
            'ui_hidden': False,
            'ui_control': ui_control
        }

    def migrate_model(self, model: Dict[str, Any]) -> bool:
        """Migrate a single model configuration. Returns True if changes were made."""
        model_id = model.get('id', 'unknown')
        model_name = model.get('name', 'Unknown')

        # Only process Replicate models with schema
        if model.get('provider') != 'replicate':
            return False

        schema = model.get('replicate_schema', {})
        input_schema = schema.get('input', {})
        parameters = input_schema.get('parameters', [])

        if not parameters:
            return False

        print(f"\n{'*'*60}")
        print(f"Model: {model_name} ({model_id})")
        print(f"Parameters: {len(parameters)}")
        print('*'*60)

        has_changes = False
        ui_controls = {}

        for param in parameters:
            param_name = param.get('name')
            if not param_name:
                continue

            # Check if already has ui_hidden flag
            has_ui_hidden = 'ui_hidden' in param

            if not has_ui_hidden:
                print(f"\n⚠️  Parameter '{param_name}' missing ui_hidden flag")

                if self.interactive:
                    config = self.ask_ui_config(param)
                    param['ui_hidden'] = config.get('ui_hidden', False)

                    if not config['ui_hidden'] and 'ui_control' in config:
                        ui_controls[param_name] = config['ui_control']
                else:
                    # Auto-assign based on parameter name
                    should_hide = self.should_hide_parameter(param_name)
                    param['ui_hidden'] = should_hide

                    if should_hide:
                        print(f"   → Auto-hidden (matches common internal parameter)")
                    else:
                        print(f"   → Auto-visible (will use auto-detection)")

                has_changes = True
                self.changes.append(f"  - {model_id}: Added ui_hidden to '{param_name}'")

        # Add custom UI controls if configured
        if ui_controls:
            if 'custom' not in model:
                model['custom'] = {}
            model['custom']['ui_controls'] = ui_controls
            has_changes = True
            self.changes.append(f"  - {model_id}: Added custom UI controls")
        elif 'custom' not in model:
            # Ensure custom field exists (even if empty)
            model['custom'] = {}

        return has_changes

    def migrate(self, output_path: Optional[Path] = None) -> None:
        """Run migration on configuration file."""
        print(f"\n🔄 Loading configuration from: {self.config_path}")
        config = self.load_config()

        models = config.get('models', [])
        if not models:
            print("⚠️  No models found in configuration")
            return

        print(f"📋 Found {len(models)} models")

        # Migrate each model
        total_changes = 0
        for model in models:
            if self.migrate_model(model):
                total_changes += 1

        if total_changes == 0:
            print("\n✅ No migration needed - all models already have ui_hidden flags")
            return

        # Show summary
        print(f"\n{'='*60}")
        print("MIGRATION SUMMARY")
        print('='*60)
        for change in self.changes:
            print(change)
        print(f"\nTotal models migrated: {total_changes}/{len(models)}")

        # Save output
        if output_path is None:
            # Default: create local.json with only models
            output_path = self.config_path.parent / 'local.json'
            output_config = {'models': models}
        else:
            output_config = config

        if not self.dry_run:
            confirm = input(f"\n💾 Save changes to {output_path}? [Y/n]: ").strip().lower()
            if confirm == 'n':
                print("❌ Migration cancelled")
                return

        self.save_config(output_config, output_path)
        print(f"\n✅ Migration complete! Configuration saved to: {output_path}")

        if output_path.name == 'local.json':
            print("\n📝 NOTE: local.json will be merged with your environment config at startup")
            print("         Only model configurations are used from local.json")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate model configurations for Custom Model Parameters UI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--config',
        type=Path,
        default=Path('backend/config/production.json'),
        help='Config file to migrate (default: backend/config/production.json)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactively configure custom UI controls'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup file'
    )

    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: creates local.json)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without modifying files'
    )

    args = parser.parse_args()

    # Validate config file exists
    if not args.config.exists():
        print(f"❌ Error: Config file not found: {args.config}")
        print(f"\nSearching for config files...")

        config_dir = Path('backend/config')
        if config_dir.exists():
            config_files = list(config_dir.glob('*.json'))
            if config_files:
                print("\nAvailable config files:")
                for cf in config_files:
                    print(f"  - {cf}")

        sys.exit(1)

    # Create migrator
    migrator = ConfigMigrator(
        config_path=args.config,
        interactive=args.interactive,
        dry_run=args.dry_run
    )

    # Create backup if requested
    if not args.no_backup and not args.dry_run:
        migrator.backup_config()

    # Run migration
    try:
        migrator.migrate(output_path=args.output)
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
