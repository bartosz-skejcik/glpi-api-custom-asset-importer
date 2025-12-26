"""Command-line interface for GLPI Asset Importer."""

import sys
import argparse

from .api.client import GLPIAPIClient
from .importer.asset_importer import AssetImporter
from .utils.console import print_header, print_error, print_info, print_warning, Colors
from .utils.config import load_config, create_default_config


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="GLPI Asset Importer - Import assets from CSV files into GLPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new config file
  python glpi_asset_importer.py --init-config

  # List available asset types
  python glpi_asset_importer.py --list-types

  # Show all fields for an asset type
  python glpi_asset_importer.py --show-fields Computer
  python glpi_asset_importer.py --show-fields Laptop

  # Generate a template for Computer assets
  python glpi_asset_importer.py --generate-template Computer

  # Import computers from CSV
  python glpi_asset_importer.py --import Computer --file computers.csv

  # Import custom assets
  python glpi_asset_importer.py --import Laptop --file laptops.csv
        """
    )

    parser.add_argument('--config', default='config.json',
                       help='Configuration file (default: config.json)')
    parser.add_argument('--init-config', action='store_true',
                       help='Create a default configuration file')
    parser.add_argument('--list-types', action='store_true',
                       help='List all available asset types')
    parser.add_argument('--show-fields', metavar='ASSET_TYPE',
                       help='Show all available fields for a specific asset type')
    parser.add_argument('--generate-template', metavar='ASSET_TYPE',
                       help='Generate a CSV template for the specified asset type')
    parser.add_argument('--import', dest='import_type', metavar='ASSET_TYPE',
                       help='Import assets of the specified type')
    parser.add_argument('--file', metavar='CSV_FILE',
                       help='CSV file to import from')
    parser.add_argument('--output', default='template.csv',
                       help='Output file for template (default: template.csv)')
    parser.add_argument('--allow-duplicates', action='store_true',
                       help='Allow importing duplicate items')
    parser.add_argument('--no-ssl-verify', action='store_true',
                       help='Disable SSL certificate verification')

    args = parser.parse_args()

    # Print banner
    print_header("GLPI Asset Importer")
    print(f"{Colors.OKCYAN}Version 1.0{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Support for GLPI v11 Custom Assets{Colors.ENDC}\n")

    # Handle init config
    if args.init_config:
        create_default_config(args.config)
        return 0

    # Load configuration
    config = load_config(args.config)
    if not config:
        print_error(f"Configuration file not found: {args.config}")
        print_info("Run with --init-config to create a default configuration file")
        return 1

    # Override SSL verification if needed
    if args.no_ssl_verify:
        config['verify_ssl'] = False

    # Initialize API client
    try:
        client = GLPIAPIClient(
            base_url=config['base_url'],
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            username=config['username'],
            password=config['password'],
            verify_ssl=config.get('verify_ssl', True),
            entity_id=config.get('entity_id'),
            profile_id=config.get('profile_id'),
            timeout=config.get('timeout', 30)
        )

        # Authenticate
        if not client.authenticate():
            return 1

        # Initialize importer
        importer = AssetImporter(client)

        # Handle commands
        if args.list_types:
            importer.list_asset_types()

        elif args.show_fields:
            importer.show_fields(args.show_fields)

        elif args.generate_template:
            importer.generate_template(args.generate_template, args.output)

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


if __name__ == '__main__':
    sys.exit(main())
