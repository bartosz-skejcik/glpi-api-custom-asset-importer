"""Migration module for exporting and importing GLPI assets."""

import csv
import json
import os
from typing import Dict, List, Any, Optional

from ..api.client import GLPIAPIClient
from ..utils.console import (
    print_header, print_success, print_error, print_warning, print_info, Colors
)


class MigrationManager:
    """Manage export and import of GLPI assets for migration purposes."""

    def __init__(self, client: GLPIAPIClient):
        """
        Initialize the migration manager.

        Args:
            client: Authenticated GLPI API client
        """
        self.client = client

    def export_assets(
        self,
        asset_type: str,
        fields: Optional[List[str]] = None,
        output_file: str = "export.csv",
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> bool:
        """
        Export assets from GLPI to CSV file.

        Args:
            asset_type: Type of asset to export (e.g., Computer, Monitor)
            fields: List of fields to export (None = all fields)
            output_file: Output CSV file path
            filters: Optional filters for querying assets (e.g., {'states_id': 1})
            include_metadata: If True, create a metadata JSON file with export info

        Returns:
            True if export successful, False otherwise
        """
        print_header(f"Exporting {asset_type} Assets")

        try:
            # Get asset definition
            asset_def = self.client.get_asset_definition(asset_type)
            if not asset_def:
                print_error(f"Asset type '{asset_type}' not found")
                return False

            # Get all assets of this type
            print_info(f"Fetching {asset_type} assets from GLPI...")
            assets = self.client.search_items(asset_type, filters or {})

            if not assets:
                print_warning(f"No {asset_type} assets found")
                return False

            print_success(f"Found {len(assets)} assets to export")

            # Determine fields to export
            if fields is None:
                # Get all available fields from the first asset
                fields = list(assets[0].keys())
            else:
                # Validate that requested fields exist
                available_fields = set(assets[0].keys())
                requested_fields = set(fields)
                missing_fields = requested_fields - available_fields
                if missing_fields:
                    print_warning(
                        f"Some requested fields not found: {', '.join(missing_fields)}")
                fields = [f for f in fields if f in available_fields]

            # Write to CSV
            print_info(f"Writing to {output_file}...")

            # Track which fields are dropdown/relation fields (for metadata)
            dropdown_fields = set()

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()

                for asset in assets:
                    # Flatten custom fields if they exist
                    if 'custom_fields' in asset and isinstance(asset['custom_fields'], dict):
                        # Merge custom fields into main asset dict for easier access
                        asset = {**asset, **asset['custom_fields']}

                    # Filter to only include requested fields and extract names from dropdown objects
                    filtered_asset = {}
                    for k, v in asset.items():
                        if k not in fields:
                            continue

                        # If value is a dict with 'name', extract the name string
                        # This way we export names, not IDs, so they can be resolved in target instance
                        if isinstance(v, dict) and 'name' in v:
                            filtered_asset[k] = v['name']
                            dropdown_fields.add(k)
                        # If value is a list of dicts with names, extract names as comma-separated string
                        elif isinstance(v, list) and v and isinstance(v[0], dict) and 'name' in v[0]:
                            filtered_asset[k] = ', '.join(
                                [item['name'] for item in v if 'name' in item])
                            dropdown_fields.add(k)
                        else:
                            filtered_asset[k] = v

                    writer.writerow(filtered_asset)

            print_success(f"Exported {len(assets)} assets to {output_file}")
            print_info(f"Exported fields: {', '.join(fields)}")

            # Create metadata file if requested
            if include_metadata:
                metadata_file = output_file.replace('.csv', '_metadata.json')
                metadata = {
                    'asset_type': asset_type,
                    'export_date': str(os.path.getmtime(output_file)),
                    'total_assets': len(assets),
                    'fields': fields,
                    'filters': filters or {},
                    'glpi_url': self.client.base_url,
                    'dropdown_fields': list(dropdown_fields)
                }
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                print_success(f"Created metadata file: {metadata_file}")
                if dropdown_fields:
                    print_info(
                        f"Dropdown fields (will be resolved by name): {', '.join(dropdown_fields)}")

            return True

        except Exception as e:
            print_error(f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def interactive_export(self, asset_type: str, output_file: str = "export.csv"):
        """
        Interactive export with field selection.

        Args:
            asset_type: Type of asset to export
            output_file: Output CSV file path
        """
        print_header(f"Interactive Export: {asset_type}")

        try:
            # Get available fields
            print_info("Fetching available fields...")
            schema = self.client.get_asset_fields(asset_type)

            if not schema:
                print_warning(
                    "Could not fetch schema, attempting to get sample asset...")
                # Try to get one asset to see available fields
                sample_assets = self.client.search_items(
                    asset_type, {}, limit=1)
                if not sample_assets:
                    print_error(f"No {asset_type} assets found to inspect")
                    return False
                available_fields = list(sample_assets[0].keys())
            else:
                # get_asset_fields returns the properties dict directly
                # Extract custom fields if they exist
                custom_fields_info = schema.get('custom_fields', {})

                # Get standard fields (excluding custom_fields entry)
                available_fields = [
                    k for k in schema.keys() if k != 'custom_fields']

                # Add individual custom fields
                if custom_fields_info and 'properties' in custom_fields_info:
                    custom_props = custom_fields_info['properties']
                    if isinstance(custom_props, dict):
                        available_fields.extend(custom_props.keys())
                    elif isinstance(custom_props, list):
                        available_fields.extend(
                            [cf.get('name', '') for cf in custom_props if cf.get('name')])

            if not available_fields:
                print_error("Could not determine available fields")
                return False

            # Display available fields
            print_info(f"\nAvailable fields for {asset_type}:")
            for i, field in enumerate(available_fields, 1):
                print(f"  {i}. {field}")

            # Let user select fields
            print(
                f"\n{Colors.OKBLUE}Enter field numbers to export (comma-separated), or 'all' for all fields:{Colors.ENDC}")
            selection = input(f"{Colors.OKGREEN}> {Colors.ENDC}").strip()

            selected_fields = []
            if selection.lower() == 'all':
                selected_fields = available_fields
            else:
                try:
                    indices = [int(x.strip()) -
                               1 for x in selection.split(',')]
                    selected_fields = [available_fields[i]
                                       for i in indices if 0 <= i < len(available_fields)]
                except (ValueError, IndexError):
                    print_error("Invalid selection")
                    return False

            if not selected_fields:
                print_error("No fields selected")
                return False

            print_info(f"\nSelected fields: {', '.join(selected_fields)}")

            # Ask for filters (optional)
            print(f"\n{Colors.OKBLUE}Apply filters? (y/n):{Colors.ENDC}")
            if input(f"{Colors.OKGREEN}> {Colors.ENDC}").strip().lower() in ['y', 'yes']:
                filters = self._interactive_filters()
            else:
                filters = None

            # Perform export
            return self.export_assets(
                asset_type=asset_type,
                fields=selected_fields,
                output_file=output_file,
                filters=filters,
                include_metadata=True
            )

        except Exception as e:
            print_error(f"Interactive export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _interactive_filters(self) -> Dict[str, Any]:
        """
        Get filters from user interactively.

        Returns:
            Dictionary of filters
        """
        filters = {}
        print_info(
            "\nEnter filters (field=value), one per line. Empty line to finish:")

        while True:
            filter_input = input(f"{Colors.OKGREEN}> {Colors.ENDC}").strip()
            if not filter_input:
                break

            if '=' in filter_input:
                key, value = filter_input.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Try to convert to int if possible
                try:
                    value = int(value)
                except ValueError:
                    pass

                filters[key] = value
                print_success(f"Added filter: {key} = {value}")
            else:
                print_warning("Invalid filter format. Use: field=value")

        return filters

    def import_from_migration(
        self,
        csv_file: str,
        asset_type: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        value_mapping: Optional[Dict[str, Dict[str, str]]] = None,
        skip_duplicates: bool = True,
        auto_create_all: bool = False
    ) -> bool:
        """
        Import assets from a migration CSV file.

        Args:
            csv_file: Path to CSV file to import
            asset_type: Type of asset to import (if None, reads from metadata)
            field_mapping: Map source field names to target field names
            value_mapping: Map field values (e.g., {"manufacturers_id": {"DELL": "Dell Inc."}})
            skip_duplicates: Skip assets that already exist
            auto_create_all: Automatically create missing dropdown items

        Returns:
            True if import successful, False otherwise
        """
        print_header(f"Importing Assets from Migration File")

        try:
            # Try to load metadata
            metadata_file = csv_file.replace('.csv', '_metadata.json')
            metadata = None
            if os.path.exists(metadata_file):
                print_info(f"Found metadata file: {metadata_file}")
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                if asset_type is None and 'asset_type' in metadata:
                    asset_type = metadata['asset_type']
                    print_info(f"Using asset type from metadata: {asset_type}")

                print_info(
                    f"Metadata: Exported {metadata.get('total_assets', 'unknown')} assets")
                print_info(
                    f"Source GLPI: {metadata.get('glpi_url', 'unknown')}")

            if not asset_type:
                print_error(
                    "Asset type not specified and not found in metadata")
                return False

            # Apply field name mapping if provided
            if field_mapping:
                print_info("Applying field name mapping...")
                mapped_file = csv_file.replace('.csv', '_field_mapped.csv')
                self._apply_field_mapping(csv_file, mapped_file, field_mapping)
                csv_file = mapped_file

            # Apply value mapping if provided
            if value_mapping:
                print_info("Applying value mapping...")
                value_mapped_file = csv_file.replace(
                    '.csv', '_value_mapped.csv')
                self._apply_value_mapping(
                    csv_file, value_mapped_file, value_mapping)
                csv_file = value_mapped_file

            # Use the standard AssetImporter for the actual import
            from .asset_importer import AssetImporter
            importer = AssetImporter(
                self.client, auto_create_all=auto_create_all)

            # Import the assets
            result = importer.import_from_csv(
                asset_type, csv_file, skip_duplicates)

            return result

        except Exception as e:
            print_error(f"Import from migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _apply_field_mapping(
        self,
        input_file: str,
        output_file: str,
        field_mapping: Dict[str, str]
    ):
        """
        Apply field name mapping to CSV file.

        Args:
            input_file: Source CSV file
            output_file: Target CSV file with mapped field names
            field_mapping: Dictionary mapping old field names to new field names
        """
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)

            # Map field names
            new_fieldnames = [field_mapping.get(
                f, f) for f in reader.fieldnames]

            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
                writer.writeheader()

                for row in reader:
                    # Map row values to new field names
                    new_row = {field_mapping.get(
                        k, k): v for k, v in row.items()}
                    writer.writerow(new_row)

        print_success(f"Applied field name mapping, saved to: {output_file}")

    def _apply_value_mapping(
        self,
        input_file: str,
        output_file: str,
        value_mapping: Dict[str, Dict[str, str]]
    ):
        """
        Apply value mapping to CSV file.

        Args:
            input_file: Source CSV file
            output_file: Target CSV file with mapped values
            value_mapping: Dictionary mapping field names to value transformations
                          e.g., {"manufacturers_id": {"DELL": "Dell Inc.", "HP": "HP Inc."}}
        """
        mapped_count = 0
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)

            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                writer.writeheader()

                for row in reader:
                    # Apply value mappings
                    for field_name, mappings in value_mapping.items():
                        if field_name in row and row[field_name] in mappings:
                            old_value = row[field_name]
                            new_value = mappings[old_value]
                            row[field_name] = new_value
                            mapped_count += 1
                            print_info(
                                f"  Mapped {field_name}: '{old_value}' → '{new_value}'")

                    writer.writerow(row)

        print_success(
            f"Applied {mapped_count} value mappings, saved to: {output_file}")

    def load_value_mapping_file(self, mapping_file: str) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Load value mapping from a JSON file.

        Args:
            mapping_file: Path to JSON mapping file

        Returns:
            Dictionary with value mappings or None if failed
        """
        try:
            if not os.path.exists(mapping_file):
                print_error(f"Mapping file not found: {mapping_file}")
                return None

            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

            print_success(f"Loaded value mapping from {mapping_file}")

            # Display what will be mapped
            for field, value_map in mapping.items():
                print_info(f"  {field}: {len(value_map)} mappings")

            return mapping

        except Exception as e:
            print_error(f"Failed to load mapping file: {str(e)}")
            return None

    def create_value_mapping_template(self, csv_file: str, output_file: str = "value_mapping.json"):
        """
        Create a template value mapping file based on unique values in CSV.

        Args:
            csv_file: Path to CSV file to analyze
            output_file: Output JSON file for mapping template
        """
        print_header("Creating Value Mapping Template")

        try:
            # Read CSV and collect unique values for dropdown fields
            dropdown_fields = [
                'locations_id', 'manufacturers_id', 'models_id',
                'states_id', 'users_id', 'groups_id'
            ]

            unique_values = {}

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    for field in dropdown_fields:
                        if field in row and row[field]:
                            value = row[field].strip()
                            # Skip numeric values (likely already IDs)
                            if not value.isdigit() and value:
                                if field not in unique_values:
                                    unique_values[field] = set()
                                unique_values[field].add(value)

            # Create mapping template
            mapping_template = {}
            for field, values in unique_values.items():
                mapping_template[field] = {
                    value: value for value in sorted(values)}

            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(mapping_template, f, indent=2)

            print_success(f"Created value mapping template: {output_file}")
            print_info(f"\nFound values to map:")
            for field, values in unique_values.items():
                print_info(f"  {field}: {len(values)} unique values")

            print_info(f"\nEdit {output_file} to customize the mappings.")
            print_info(
                f"Example: Change '\"DELL\": \"DELL\"' to '\"DELL\": \"Dell Inc.\"'")

            return True

        except Exception as e:
            print_error(f"Failed to create mapping template: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def migrate_wizard(self):
        """
        Interactive wizard for complete migration workflow.
        """
        print_header("GLPI Migration Wizard")
        print_info("This wizard will help you export assets from one GLPI system")
        print_info("and prepare them for import into another GLPI system.\n")

        # Step 1: Choose operation
        print(f"{Colors.OKBLUE}What would you like to do?{Colors.ENDC}")
        print("  1. Export assets from this GLPI instance")
        print("  2. Import assets from a migration file")
        print("  3. Export and prepare for migration (full workflow)")

        choice = input(
            f"\n{Colors.OKGREEN}Select option (1-3): {Colors.ENDC}").strip()

        if choice == '1':
            # Export workflow
            print(f"\n{Colors.OKBLUE}Select asset type to export:{Colors.ENDC}")
            asset_types = self.client.get_asset_definitions()
            for i, at in enumerate(asset_types, 1):
                print(f"  {i}. {at.get('name', at.get('itemtype', 'Unknown'))}")

            selection = int(
                input(f"\n{Colors.OKGREEN}Select number: {Colors.ENDC}").strip()) - 1
            if 0 <= selection < len(asset_types):
                asset_type = asset_types[selection].get(
                    'itemtype') or asset_types[selection].get('name')
                output_file = input(
                    f"\n{Colors.OKGREEN}Output filename (default: export.csv): {Colors.ENDC}").strip() or "export.csv"
                self.interactive_export(asset_type, output_file)

        elif choice == '2':
            # Import workflow
            csv_file = input(
                f"\n{Colors.OKGREEN}Path to CSV file: {Colors.ENDC}").strip()
            if not os.path.exists(csv_file):
                print_error(f"File not found: {csv_file}")
                return False

            # Ask about value mapping
            print(
                f"\n{Colors.OKBLUE}Do you have a value mapping file? (y/n): {Colors.ENDC}")
            if input(f"{Colors.OKGREEN}> {Colors.ENDC}").strip().lower() in ['y', 'yes']:
                mapping_file = input(
                    f"\n{Colors.OKGREEN}Path to mapping file: {Colors.ENDC}").strip()
                if os.path.exists(mapping_file):
                    value_mapping = self.load_value_mapping_file(mapping_file)
                else:
                    print_warning(f"Mapping file not found: {mapping_file}")
                    value_mapping = None
            else:
                value_mapping = None

            auto_create = input(
                f"\n{Colors.OKBLUE}Auto-create missing items? (y/n): {Colors.ENDC}").strip().lower() in ['y', 'yes']

            self.import_from_migration(
                csv_file=csv_file,
                value_mapping=value_mapping,
                skip_duplicates=True,
                auto_create_all=auto_create
            )

        elif choice == '3':
            print_info("\nFull migration workflow coming soon!")
            print_info("For now, use options 1 and 2 separately.")

        else:
            print_error("Invalid selection")
            return False

        return True
