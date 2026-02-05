"""Command-line interface for GLPI Asset Importer."""

import sys
import argparse

from .api.client import GLPIAPIClient
from .importer.asset_importer import AssetImporter
from .importer.migration import MigrationManager
from .utils.console import print_header, print_error, print_info, print_warning, print_success, Colors
from .utils.config import (
    load_config,
    create_default_config,
    get_instance_config,
    list_instances,
    interactive_select_instance
)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="GLPI Asset Importer - Import assets from CSV files into GLPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new config file
  python glpi_asset_importer.py --init-config

  # List configured instances
  python glpi_asset_importer.py --list-instances

  # List available asset types (uses default instance)
  python glpi_asset_importer.py --list-types

  # List types from specific instance
  python glpi_asset_importer.py --instance production --list-types

  # Show all fields for an asset type
  python glpi_asset_importer.py --show-fields Computer
  python glpi_asset_importer.py --instance development --show-fields Laptop

  # Generate a template for Computer assets
  python glpi_asset_importer.py --generate-template Computer

  # Import computers from CSV
  python glpi_asset_importer.py --import Computer --file computers.csv
  python glpi_asset_importer.py --instance production --import Computer --file computers.csv

  # Migration commands
  python glpi_asset_importer.py --export Computer --output computers_export.csv
  python glpi_asset_importer.py --export-interactive Laptop
  python glpi_asset_importer.py --import-migration --file computers_export.csv
  python glpi_asset_importer.py --migrate-wizard

  # Cross-instance migration
  python glpi_asset_importer.py --cross-instance-migrate --source-instance prod --target-instance dev
        """
    )

    # Configuration arguments
    parser.add_argument('--config', default='config.json',
                        help='Configuration file (default: config.json)')
    parser.add_argument('--init-config', action='store_true',
                        help='Create a default configuration file')

    # Multi-instance arguments
    parser.add_argument('--instance', metavar='INSTANCE_NAME',
                        help='Specify which GLPI instance to use')
    parser.add_argument('--list-instances', action='store_true',
                        help='List all configured GLPI instances')

    # Asset type arguments
    parser.add_argument('--list-types', action='store_true',
                        help='List all available asset types')
    parser.add_argument('--show-fields', metavar='ASSET_TYPE',
                        help='Show all available fields for a specific asset type')
    parser.add_argument('--generate-template', metavar='ASSET_TYPE',
                        help='Generate a CSV template for the specified asset type')

    # Import/Export arguments
    parser.add_argument('--import', dest='import_type', metavar='ASSET_TYPE',
                        help='Import assets of the specified type')
    parser.add_argument('--file', metavar='CSV_FILE',
                        help='CSV file to import from')
    parser.add_argument('--output', default='template.csv',
                        help='Output file for template (default: template.csv)')
    parser.add_argument('--allow-duplicates', action='store_true',
                        help='Allow importing duplicate items')

    # Migration arguments
    parser.add_argument('--export', metavar='ASSET_TYPE',
                        help='Export assets with custom field selection')
    parser.add_argument('--export-interactive', metavar='ASSET_TYPE',
                        help='Interactive export with field selection and filtering')
    parser.add_argument('--import-migration', action='store_true',
                        help='Import from migration export file')
    parser.add_argument('--migrate-wizard', action='store_true',
                        help='Run the complete migration wizard')
    parser.add_argument('--value-mapping', metavar='MAPPING_FILE',
                        help='JSON file with value mappings for field transformations')

    # Cross-instance migration arguments
    parser.add_argument('--cross-instance-migrate', action='store_true',
                        help='Migrate assets between two GLPI instances')
    parser.add_argument('--source-instance', metavar='INSTANCE_NAME',
                        help='Source instance for cross-instance migration')
    parser.add_argument('--target-instance', metavar='INSTANCE_NAME',
                        help='Target instance for cross-instance migration')

    # Other arguments
    parser.add_argument('--no-ssl-verify', action='store_true',
                        help='Disable SSL certificate verification')

    args = parser.parse_args()

    # Print banner
    print_header("GLPI Asset Importer")
    print(f"{Colors.OKCYAN}Version 1.2 - Multi-Instance & Migration Support{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Support for GLPI v11 Custom Assets{Colors.ENDC}\n")

    # Handle init config
    if args.init_config:
        create_default_config(args.config)
        return 0

    # Load configuration
    config = load_config(args.config)
    if not config:
        print_error(f"Configuration file not found: {args.config}")
        print_info(
            "Run with --init-config to create a default configuration file")
        return 1

    # Handle list instances
    if args.list_instances:
        list_instances(config)
        return 0

    # Handle cross-instance migration
    if args.cross_instance_migrate:
        return handle_cross_instance_migration(config, args)

    # Get instance config
    instance_config = get_instance_config(config, args.instance)
    if not instance_config:
        return 1

    # Override SSL verification if needed
    if args.no_ssl_verify:
        instance_config['verify_ssl'] = False

    # Initialize API client
    try:
        client = GLPIAPIClient(
            base_url=instance_config['base_url'],
            client_id=instance_config['client_id'],
            client_secret=instance_config['client_secret'],
            username=instance_config['username'],
            password=instance_config['password'],
            verify_ssl=instance_config.get('verify_ssl', True),
            entity_id=instance_config.get('entity_id'),
            profile_id=instance_config.get('profile_id'),
            timeout=instance_config.get('timeout', 30)
        )

        # Authenticate
        if not client.authenticate():
            return 1

        # Initialize importer and migration manager
        importer = AssetImporter(client)
        migration = MigrationManager(client)

        # Handle commands
        if args.list_types:
            importer.list_asset_types()

        elif args.show_fields:
            importer.show_fields(args.show_fields)

        elif args.generate_template:
            importer.generate_template(args.generate_template, args.output)

        elif args.export:
            migration.interactive_export(args.export, args.output)

        elif args.export_interactive:
            migration.interactive_export(args.export_interactive, args.output)

        elif args.import_migration:
            if not args.file:
                print_error("Please specify a migration file with --file")
                return 1
            migration.import_from_migration(args.file, args.value_mapping)

        elif args.migrate_wizard:
            migration.migrate_wizard()

        elif args.import_type:
            if not args.file:
                print_error("Please specify a CSV file with --file")
                return 1

            importer.import_from_csv(
                args.import_type,
                args.file,
                skip_duplicates=not args.allow_duplicates
            )

        else:
            parser.print_help()
            return 0

        return 0

    except KeyboardInterrupt:
        print_warning("\n\nOperation cancelled by user")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def handle_cross_instance_migration(config, args):
    """Handle cross-instance migration workflow."""
    try:
        # Select source instance
        if args.source_instance:
            source_config = get_instance_config(config, args.source_instance)
            if not source_config:
                return 1
            source_name = args.source_instance
        else:
            source_name = interactive_select_instance(
                config, "Select source instance to export from")
            if not source_name:
                return 1
            source_config = get_instance_config(config, source_name)

        # Select target instance
        if args.target_instance:
            target_config = get_instance_config(config, args.target_instance)
            if not target_config:
                return 1
            target_name = args.target_instance
        else:
            target_name = interactive_select_instance(
                config, "Select target instance to import to")
            if not target_name:
                return 1
            target_config = get_instance_config(config, target_name)

        # Prevent migration to same instance
        if source_name == target_name:
            print_error("Source and target instances cannot be the same")
            return 1

        print_info(f"\n📤 Source: {source_name}")
        print_info(f"📥 Target: {target_name}\n")

        # Initialize source client
        print_info("Connecting to source instance...")
        source_client = GLPIAPIClient(
            base_url=source_config['base_url'],
            client_id=source_config['client_id'],
            client_secret=source_config['client_secret'],
            username=source_config['username'],
            password=source_config['password'],
            verify_ssl=source_config.get('verify_ssl', True),
            entity_id=source_config.get('entity_id'),
            profile_id=source_config.get('profile_id'),
            timeout=source_config.get('timeout', 30)
        )

        if not source_client.authenticate():
            print_error("Failed to authenticate with source instance")
            return 1

        # Initialize target client
        print_info("Connecting to target instance...")
        target_client = GLPIAPIClient(
            base_url=target_config['base_url'],
            client_id=target_config['client_id'],
            client_secret=target_config['client_secret'],
            username=target_config['username'],
            password=target_config['password'],
            verify_ssl=target_config.get('verify_ssl', True),
            entity_id=target_config.get('entity_id'),
            profile_id=target_config.get('profile_id'),
            timeout=target_config.get('timeout', 30)
        )

        if not target_client.authenticate():
            print_error("Failed to authenticate with target instance")
            return 1

        # Initialize migration managers
        source_importer = AssetImporter(source_client)
        source_migration = MigrationManager(source_client)

        target_importer = AssetImporter(target_client)
        target_migration = MigrationManager(target_client)

        # Run export from source
        print_header("Step 1: Export from Source")
        temp_file = f"migration_{source_name}_to_{target_name}.csv"

        # Get asset types from source
        asset_types_data = source_client.get_asset_definitions()
        if not asset_types_data:
            print_error("No asset types found in source instance")
            return 1

        # Build list with both display name and full itemtype
        asset_options = []
        for asset in asset_types_data:
            if 'itemtype' in asset:
                itemtype = asset['itemtype']
                # Use name for display if available, otherwise use itemtype
                display_name = asset.get('name', itemtype)
                asset_options.append({
                    'itemtype': itemtype,
                    'display': display_name
                })

        if not asset_options:
            print_error("No asset types found in source instance")
            return 1

        # Let user select asset type
        print_info("\nAvailable asset types in source:")
        for i, asset_option in enumerate(asset_options, 1):
            print(f"  {i}. {asset_option['display']}")

        try:
            choice = input(
                f"\n{Colors.BOLD}Select asset type (1-{len(asset_options)}): {Colors.ENDC}")
            idx = int(choice) - 1
            if idx < 0 or idx >= len(asset_options):
                print_error("Invalid choice")
                return 1
            # Use the full itemtype, not the display name
            asset_type = asset_options[idx]['itemtype']
        except (ValueError, KeyboardInterrupt):
            print_error("\nInvalid input")
            return 1

        # Export from source
        result = source_migration.interactive_export(asset_type, temp_file)
        if not result:
            print_error("Export failed")
            return 1

        # Run import to target
        print_header("Step 2: Import to Target")
        print_info(f"\nImporting to {target_name}...")

        # Ask about field mapping
        field_mapping = None
        use_field_mapping = input(
            f"\n{Colors.BOLD}Do you want to map fields? (e.g., map 'serial' to 'comment') (y/n): {Colors.ENDC}").strip().lower()

        if use_field_mapping == 'y':
            print_info("\nField Mapping: Map source fields to target fields")
            print_info("Leave blank to use the same field name\n")

            # Load the exported CSV to get available fields
            import csv
            with open(temp_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                available_fields = reader.fieldnames

            print_info(
                f"Available fields in export: {', '.join(available_fields)}\n")

            field_mapping = {}
            while True:
                source_field = input(
                    f"{Colors.OKBLUE}Source field name (or 'done' to finish): {Colors.ENDC}").strip()
                if source_field.lower() == 'done' or not source_field:
                    break

                if source_field not in available_fields:
                    print_warning(
                        f"Warning: '{source_field}' not in exported fields")
                    confirm = input(
                        f"Continue anyway? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue

                target_field = input(
                    f"{Colors.OKBLUE}Target field name (where to put '{source_field}'): {Colors.ENDC}").strip()
                if target_field:
                    field_mapping[source_field] = target_field
                    print_success(
                        f"✓ Will map '{source_field}' → '{target_field}'")

            if field_mapping:
                print_info(f"\nField mappings configured:")
                for src, tgt in field_mapping.items():
                    print_info(f"  {src} → {tgt}")
            else:
                field_mapping = None
                print_info("No field mappings configured")

        # Ask about value mapping
        value_mapping = None
        use_value_mapping = input(
            f"\n{Colors.BOLD}Do you want to apply value mapping? (map specific values) (y/n): {Colors.ENDC}").strip().lower()

        if use_value_mapping == 'y':
            # Generate mapping template
            template_file = f"value_mapping_{source_name}_to_{target_name}.json"
            print_info(f"\nGenerating value mapping template: {template_file}")
            target_migration.create_value_mapping_template(
                temp_file, template_file)
            print_info(f"✅ Edit {template_file} and press Enter when ready...")
            input()

            # Load value mapping from file
            import json
            with open(template_file, 'r', encoding='utf-8') as f:
                value_mapping = json.load(f)

        # Import to target
        result = target_migration.import_from_migration(
            temp_file,
            asset_type=asset_type,
            field_mapping=field_mapping,
            value_mapping=value_mapping
        )

        if result:
            print_success(
                f"\n✅ Cross-instance migration completed successfully!")
            print_info(f"   Source: {source_name}")
            print_info(f"   Target: {target_name}")
            print_info(f"   Migration file: {temp_file}")
            return 0
        else:
            print_error("Import failed")
            return 1

    except KeyboardInterrupt:
        print_warning("\n\nMigration cancelled by user")
        return 130
    except Exception as e:
        print_error(f"Migration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
