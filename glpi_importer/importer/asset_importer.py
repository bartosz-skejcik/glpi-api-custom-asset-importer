"""Asset importer for importing assets from CSV files into GLPI."""

import csv
import os
from typing import Dict, Any

from ..api.client import GLPIAPIClient
from ..utils.console import (
    print_header, print_success, print_error, print_warning, print_info, Colors
)


class AssetImporter:
    """Main asset importer class."""

    def __init__(self, client: GLPIAPIClient, auto_create_all: bool = False):
        """
        Initialize the asset importer.

        Args:
            client: Authenticated GLPI API client
            auto_create_all: If True, automatically create all missing items without prompting
        """
        self.client = client
        self.auto_create_all = auto_create_all
        # Cache for user decisions about creating missing items
        # Key: (dropdown_type, value), Value: True/False
        self._create_cache = {}
        # Mapping of field suffixes to dropdown types
        self.dropdown_mappings = {
            'locations_id': 'Location',
            'manufacturers_id': 'Manufacturer',
            'models_id': 'Model',
            'states_id': 'State',
            'users_id': 'User',
            'groups_id': 'Group',
            'types_id': 'Type',
            # Also map singular forms (from API responses)
            'location': 'Location',
            'manufacturer': 'Manufacturer',
            'model': 'Model',
            'state': 'State',
            'user': 'User',
            'group': 'Group',
            'type': 'Type',
            'user_tech': 'User',
            'group_tech': 'Group',
            # Other known fields
            'computermodels_id': 'ComputerModel',
            'computertypes_id': 'ComputerType',
            'networks_id': 'Network',
            'autoupdatesystems_id': 'AutoUpdateSystem',
        }

    def resolve_field_value(self, field_name: str, value: str, asset_type: str) -> Any:
        """
        Resolve a field value - convert names to IDs for dropdown fields.

        Args:
            field_name: Name of the field
            value: Value to resolve (might be a name or already an ID)
            asset_type: The asset type being imported

        Returns:
            Resolved value (ID for dropdowns, original value otherwise)
        """
        # If field_name is None or empty, return the original value
        if not field_name:
            return value

        # If it's already a number, return as is
        if isinstance(value, int):
            return value

        # Try to parse as integer
        try:
            return int(value)
        except (ValueError, TypeError):
            pass

        # Check if this is a known dropdown field
        dropdown_type = None

        # For models_id on custom assets, use {AssetType}Model
        if field_name == 'models_id' and asset_type:
            dropdown_type = 'Model'  # Will be resolved with asset_type context
        # Direct mapping
        elif field_name in self.dropdown_mappings:
            dropdown_type = self.dropdown_mappings[field_name]
        # Check for custom asset model/type fields
        elif field_name.endswith('models_id'):
            # Extract asset type and try to find model dropdown
            base_type = field_name.replace('models_id', '').strip('_')
            if base_type:
                dropdown_type = f"{base_type.title()}Model"
        elif field_name.endswith('types_id'):
            base_type = field_name.replace('types_id', '').strip('_')
            if base_type:
                dropdown_type = f"{base_type.title()}Type"

        # Try to resolve the name to an ID
        if dropdown_type:
            resolved_id = self.client.resolve_dropdown_id(
                dropdown_type, str(value), asset_type)
            if resolved_id is not None:
                return resolved_id
            else:
                # Check cache first
                cache_key = (dropdown_type, str(value))

                if cache_key in self._create_cache:
                    should_create = self._create_cache[cache_key]
                elif self.auto_create_all:
                    # Auto-create without prompting
                    should_create = True
                    self._create_cache[cache_key] = should_create
                else:
                    # Ask user if they want to create this item
                    from ..utils.console import Colors
                    print_warning(f"Could not find {dropdown_type} '{value}'")
                    response = input(
                        f"  {Colors.OKBLUE}ℹ{Colors.ENDC} Create new {dropdown_type} '{value}'? (y/n): ").strip().lower()
                    should_create = response in ['y', 'yes']
                    # Cache the decision
                    self._create_cache[cache_key] = should_create

                if should_create:
                    print_info(f"Creating new {dropdown_type}: {value}")
                    created_id = self.client.create_dropdown_item(
                        dropdown_type, str(value), asset_type)
                    if created_id is not None:
                        return created_id
                    else:
                        print_warning(
                            f"Could not create {field_name} '{value}'. Using original value.")
                else:
                    print_warning(
                        f"Skipping creation. Using original value for {field_name} '{value}'.")

        return value

    def generate_template(self, asset_type: str, output_file: str = "template.csv"):
        """
        Generate a CSV template for a specific asset type.

        Args:
            asset_type: Type of asset (e.g., Computer, Monitor, or custom asset)
            output_file: Output CSV file path
        """
        print_header(f"Generating Template for {asset_type}")

        # Common fields for most assets
        base_fields = [
            "name",
            "serial",
            "otherserial",
            "comment",
            "locations_id",
            "manufacturers_id",
            "models_id",
            "states_id",
            "users_id",
            "groups_id"
        ]

        # Try to get custom fields from API
        api_fields = self.client.get_asset_fields(asset_type)
        custom_field_names = []
        if api_fields and 'custom_fields' in api_fields:
            custom_fields_info = api_fields['custom_fields']
            if 'properties' in custom_fields_info:
                custom_fields = custom_fields_info['properties']
                # Handle both dictionary and list formats
                if isinstance(custom_fields, dict):
                    custom_field_names = list(custom_fields.keys())
                elif isinstance(custom_fields, list):
                    custom_field_names = [
                        cf.get('name', '') for cf in custom_fields if cf.get('name')]

        # Combine standard fields with custom fields
        fields = base_fields + custom_field_names

        # Try to get schema from API
        schema = self.client.get_schema(asset_type)
        if schema:
            print_info(f"Retrieved schema from API for {asset_type}")
        else:
            print_info(f"Using default fields for {asset_type}")

        # Create template file
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()

                # Add an example row with instructions
                example_row = {field: f"<{field}>" for field in fields}
                example_row["name"] = "Example Asset Name"
                example_row["comment"] = "Add your asset data here"
                writer.writerow(example_row)

            print_success(f"Template created: {output_file}")
            print_info(f"Fields included: {', '.join(fields)}")
            print_info(f"\nPlease fill in the template with your asset data.")
            print_info(f"You can add multiple rows for multiple assets.")
            print_info(f"For *_id fields, you can use either:")
            print_info(f"  - Numeric IDs from GLPI")
            print_info(
                f"  - Names (will be auto-resolved, e.g., 'HP' for manufacturer)")
            print_info(
                f"  - Hierarchical paths for locations (e.g., 'Office > Floor > Room')")

        except Exception as e:
            print_error(f"Failed to create template: {str(e)}")

    def import_from_csv(self, asset_type: str, csv_file: str,
                        skip_duplicates: bool = True) -> Dict[str, int]:
        """
        Import assets from CSV file.

        Args:
            asset_type: Type of asset to import
            csv_file: Path to CSV file
            skip_duplicates: Whether to skip items that already exist

        Returns:
            Dictionary with import statistics
        """
        print_header(f"Importing {asset_type} from CSV")

        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

        if not os.path.exists(csv_file):
            print_error(f"CSV file not found: {csv_file}")
            return stats

        try:
            with open(csv_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                stats["total"] = len(rows)

                print_info(f"Found {stats['total']} items to import\n")

                for i, row in enumerate(rows, 1):
                    # Skip example/template rows
                    name_value = row.get('name', '')
                    # Ensure name_value is a string
                    if isinstance(name_value, list):
                        name_value = name_value[0] if name_value else ''
                    elif not isinstance(name_value, str):
                        name_value = str(name_value) if name_value else ''

                    if name_value.startswith('<') or name_value == 'Example Asset Name':
                        print_warning(
                            f"[{i}/{stats['total']}] Skipping template row")
                        stats["skipped"] += 1
                        continue

                    # Clean up row data
                    item_data = {}
                    for key, value in row.items():
                        # Ensure value is a string
                        if isinstance(value, list):
                            value = value[0] if value else ''
                        elif not isinstance(value, str):
                            value = str(value) if value else ''

                        if value and not value.startswith('<') and value.strip():
                            # Resolve field values (convert names to IDs for dropdowns)
                            resolved_value = self.resolve_field_value(
                                key, value.strip(), asset_type)
                            item_data[key] = resolved_value

                    # Get custom field names for this asset type
                    api_fields = self.client.get_asset_fields(asset_type)
                    custom_field_names = set()
                    if api_fields and 'custom_fields' in api_fields:
                        custom_fields_info = api_fields['custom_fields']
                        if 'properties' in custom_fields_info:
                            custom_fields = custom_fields_info['properties']
                            # Handle both dictionary and list formats
                            if isinstance(custom_fields, dict):
                                custom_field_names = set(custom_fields.keys())
                            elif isinstance(custom_fields, list):
                                custom_field_names = set(
                                    cf.get('name', '') for cf in custom_fields if cf.get('name'))

                    print_info(
                        f"DEBUG: Custom field names from target API: {custom_field_names}")
                    print_info(
                        f"DEBUG: Fields in CSV row: {list(item_data.keys())}")

                    # Transform fields to API format
                    # Also extract custom fields to nest under custom_fields
                    transformed_data = {}
                    extracted_custom_fields = {}

                    for key, value in item_data.items():
                        # Skip None or empty keys
                        if not key:
                            continue

                        # Check if this is a custom field
                        if key in custom_field_names:
                            print_info(
                                f"DEBUG: Identified custom field: {key} = {value}")
                            extracted_custom_fields[key] = value
                        # Check if this is a dropdown field (resolved to an ID)
                        elif isinstance(value, int) and (key in self.dropdown_mappings or key.endswith('_id')):
                            # This is a resolved dropdown ID - wrap it in an object
                            # Determine the field name for the API (without _id suffix)
                            if key.endswith('_id'):
                                field_name = key[:-3]  # Remove '_id' suffix
                            else:
                                field_name = key

                            # Handle plural to singular for some fields
                            if field_name.endswith('s') and field_name not in ['status', 'os']:
                                field_name = field_name[:-1]

                            transformed_data[field_name] = {'id': value}
                        else:
                            # Regular field - use as-is
                            transformed_data[key] = value

                    # Add custom fields as nested object if any exist
                    if extracted_custom_fields:
                        transformed_data['custom_fields'] = extracted_custom_fields
                        print_info(
                            f"DEBUG: Adding custom_fields to payload: {extracted_custom_fields}")
                    else:
                        print_info("DEBUG: No custom fields extracted")

                    print_info(
                        f"DEBUG: Final transformed_data keys: {list(transformed_data.keys())}")

                    item_data = transformed_data

                    if not item_data.get('name'):
                        print_warning(
                            f"[{i}/{stats['total']}] Skipping row without name")
                        stats["skipped"] += 1
                        continue

                    # Check for duplicates
                    if skip_duplicates and item_data.get('serial'):
                        existing = self.client.search_item(
                            asset_type, 'serial', item_data['serial'])
                        if existing:
                            print_warning(
                                f"[{i}/{stats['total']}] Skipping duplicate: {item_data['name']} (serial: {item_data['serial']})")
                            stats["skipped"] += 1
                            continue

                    # Create item
                    print_info(
                        f"[{i}/{stats['total']}] Creating: {item_data['name']}")
                    result = self.client.create_item(asset_type, item_data)

                    if result:
                        print_success(
                            f"[{i}/{stats['total']}] Successfully created: {item_data['name']}")
                        stats["success"] += 1
                    else:
                        print_error(
                            f"[{i}/{stats['total']}] Failed to create: {item_data['name']}")
                        stats["failed"] += 1

        except Exception as e:
            print_error(f"Error reading CSV file: {str(e)}")
            return stats

        # Print summary
        print_header("Import Summary")
        print(f"Total items:      {stats['total']}")
        print_success(f"Successful:       {stats['success']}")
        print_error(f"Failed:           {stats['failed']}")
        print_warning(f"Skipped:          {stats['skipped']}")

        return stats

    def list_asset_types(self):
        """List all available asset types."""
        print_header("Available Asset Types")

        print_info("Fetching asset types from GLPI...")
        asset_types = self.client.get_asset_definitions()

        if asset_types:
            print_success(f"Found {len(asset_types)} asset types:\n")

            print(f"{'Item Type':<30} {'Display Name':<30}")
            print("-" * 60)

            for asset_type in asset_types:
                itemtype = asset_type.get('itemtype', 'N/A')
                name = asset_type.get('name', 'N/A')
                print(f"{itemtype:<30} {name:<30}")
        else:
            print_warning("No asset types found")
            print_info("\nCommon built-in types you can try:")
            common_types = [
                "Computer", "Monitor", "NetworkEquipment",
                "Peripheral", "Phone", "Printer", "Software"
            ]
            for asset_type in common_types:
                print(f"  - {asset_type}")

    def show_fields(self, asset_type: str):
        """Show all available fields for a specific asset type."""
        print_header(f"Fields for {asset_type}")

        print_info(f"Fetching field information for {asset_type}...")
        fields = self.client.get_asset_fields(asset_type)

        if fields:
            print_success(f"Found {len(fields)} standard fields:\n")

            # Separate custom fields from standard fields
            custom_fields_info = fields.pop('custom_fields', None)

            # Display standard fields with their types and descriptions
            print(f"{'Field Name':<30} {'Type':<15} {'Description':<50}")
            print("-" * 95)

            for field_name, field_info in sorted(fields.items()):
                field_type = field_info.get('type', 'unknown')
                description = field_info.get('description', '')

                # Handle object types (show nested reference if available)
                if field_type == 'object' and '$ref' in field_info:
                    ref = field_info['$ref'].split('/')[-1]
                    field_type = f"object ({ref})"
                elif field_type == 'array' and 'items' in field_info:
                    if '$ref' in field_info['items']:
                        ref = field_info['items']['$ref'].split('/')[-1]
                        field_type = f"array of {ref}"
                    else:
                        item_type = field_info['items'].get('type', 'unknown')
                        field_type = f"array of {item_type}"

                # Truncate long descriptions
                if len(description) > 50:
                    description = description[:47] + "..."

                # Show if field is read-only
                if field_info.get('readOnly'):
                    field_name = f"{field_name} (read-only)"

                print(f"{field_name:<30} {field_type:<15} {description:<50}")

            # Display custom fields if they exist
            if custom_fields_info and 'properties' in custom_fields_info:
                custom_fields = custom_fields_info['properties']
                print(
                    f"\n{Colors.OKBLUE}Custom Fields ({len(custom_fields)}):{Colors.ENDC}")
                print("-" * 95)

                # Handle both dictionary and list formats
                if isinstance(custom_fields, dict):
                    for cf_name, cf_info in sorted(custom_fields.items()):
                        cf_type = cf_info.get('type', 'unknown')
                        cf_desc = cf_info.get('description', '')
                        if len(cf_desc) > 50:
                            cf_desc = cf_desc[:47] + "..."
                        print(f"{cf_name:<30} {cf_type:<15} {cf_desc:<50}")
                elif isinstance(custom_fields, list):
                    for cf_item in custom_fields:
                        cf_name = cf_item.get('name', 'unknown')
                        cf_type = cf_item.get('type', 'unknown')
                        cf_desc = cf_item.get('description', '')
                        if len(cf_desc) > 50:
                            cf_desc = cf_desc[:47] + "..."
                        print(f"{cf_name:<30} {cf_type:<15} {cf_desc:<50}")
                else:
                    print_warning("Custom fields format not recognized")

            print_info(
                "\nUse these field names when creating CSV files for import.")
            print_info(
                "Fields marked as 'read-only' are set by GLPI and cannot be imported.")
        else:
            print_warning(
                f"Could not retrieve field information for {asset_type}")
            print_info(
                "This may happen if the asset type is not found in the API documentation.")
