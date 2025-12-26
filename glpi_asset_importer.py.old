#!/usr/bin/env python3
"""
GLPI Asset Importer
A tool to import assets from CSV files into GLPI using the API
Supports GLPI v11 custom asset definitions
"""

import csv
import json
import os
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import argparse
from urllib.parse import urljoin

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a styled header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print an info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


class GLPIAPIClient:
    """GLPI API Client using OAuth2 authentication"""

    def __init__(self, base_url: str, client_id: str, client_secret: str,
                 username: str, password: str, verify_ssl: bool = True,
                 entity_id: Optional[int] = None, profile_id: Optional[int] = None,
                 timeout: int = 30):
        """
        Initialize the GLPI API client

        Args:
            base_url: Base URL of GLPI instance (e.g., http://192.168.9.9)
            client_id: OAuth client ID
            client_secret: OAuth client secret
            username: GLPI username
            password: GLPI password
            verify_ssl: Whether to verify SSL certificates
            entity_id: Optional entity ID for multi-entity setups
            profile_id: Optional profile ID
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api.php"
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.entity_id = entity_id
        self.profile_id = profile_id
        self.timeout = timeout
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()

    def authenticate(self) -> bool:
        """
        Authenticate with GLPI API using OAuth2 password grant

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            print_info("Authenticating with GLPI API...")

            token_url = f"{self.base_url}/api.php/token"
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password,
                "scope": "email user api inventory status graphql"
            }

            response = requests.post(token_url, data=data, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)

            if not self.access_token:
                print_error("Failed to get access token from response")
                return False

            # Store token expiry time (with 60 second buffer)
            from datetime import timedelta
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            print_success("Authentication successful!")
            return True

        except requests.exceptions.RequestException as e:
            print_error(f"Authentication failed: {str(e)}")
            if hasattr(e.response, 'text'):
                print_error(f"Response: {e.response.text}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid token, re-authenticating if necessary"""
        if not self.access_token or not self.token_expires_at:
            return self.authenticate()

        if datetime.now() >= self.token_expires_at:
            print_info("Token expired, re-authenticating...")
            return self.authenticate()

        return True

    def _get_headers(self, include_content_type: bool = False) -> Dict[str, str]:
        """Get headers for API requests

        Args:
            include_content_type: Whether to include Content-Type header (only for POST/PATCH)
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        if include_content_type:
            headers["Content-Type"] = "application/json"

        # Add optional entity and profile headers
        if self.entity_id is not None:
            headers["GLPI-Entity"] = str(self.entity_id)
        if self.profile_id is not None:
            headers["GLPI-Profile"] = str(self.profile_id)

        return headers

    def _is_custom_asset(self, item_type: str) -> bool:
        """Check if an asset type is a custom asset"""
        try:
            if not self._ensure_authenticated():
                return False

            # Get custom assets list
            url = f"{self.api_url}/Assets/Custom/"
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            if response.status_code == 200:
                custom_assets = response.json()
                for asset in custom_assets:
                    if asset.get('itemtype') == item_type or asset.get('name') == item_type:
                        return True
            return False
        except:
            return False

    def get_asset_definitions(self) -> List[Dict[str, Any]]:
        """
        Get all asset types available in GLPI (both standard and custom)

        Returns:
            List of asset types with itemtype, name, and href
        """
        try:
            if not self._ensure_authenticated():
                return []

            all_assets = []

            # Get standard assets
            url = f"{self.api_url}/Assets/"
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            all_assets.extend(response.json())

            # Get custom assets
            url = f"{self.api_url}/Assets/Custom/"
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            all_assets.extend(response.json())

            return all_assets
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to get asset types: {str(e)}")
            return []

    def get_asset_definition(self, asset_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific asset type by itemtype or name

        Args:
            asset_type: Itemtype or name of the asset type (e.g., Computer, Monitor)

        Returns:
            Asset type info or None if not found
        """
        try:
            # Get all asset types
            definitions = self.get_asset_definitions()
            for definition in definitions:
                if definition.get('itemtype') == asset_type or definition.get('name') == asset_type:
                    return definition

            print_warning(f"Asset type '{asset_type}' not found")
            return None

        except Exception as e:
            print_error(f"Failed to get asset type: {str(e)}")
            return None

    def get_schema(self, item_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for an item type

        Args:
            item_type: Type of item (e.g., Computer, Monitor)

        Returns:
            Schema definition or None if not found
        """
        try:
            if not self._ensure_authenticated():
                return None

            # Try common endpoints (including custom assets)
            endpoints = [
                f"{self.api_url}/Assets/{item_type}",
                f"{self.api_url}/Assets/Custom/{item_type}",
                f"{self.api_url}/{item_type}"
            ]

            for url in endpoints:
                try:
                    # Use OPTIONS method to get schema
                    response = requests.options(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
                    if response.status_code == 200:
                        return response.json()
                except:
                    continue

            return None

        except Exception as e:
            print_error(f"Failed to get schema for {item_type}: {str(e)}")
            return None

    def get_asset_fields(self, item_type: str) -> Optional[Dict[str, Any]]:
        """
        Get all available fields/properties for an asset type from OpenAPI schema

        Args:
            item_type: Type of item (e.g., Computer, Monitor, Laptop)

        Returns:
            Dictionary of field properties or None if not found
        """
        try:
            # Get the OpenAPI documentation
            doc_url = f"{self.base_url}/api.php/doc.json"
            response = requests.get(doc_url, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()

            doc = response.json()

            # Look for the schema in components.schemas
            if 'components' in doc and 'schemas' in doc['components']:
                schemas = doc['components']['schemas']

                # Try direct match first
                if item_type in schemas:
                    schema = schemas[item_type]
                    if 'properties' in schema:
                        return schema['properties']

                # For custom assets, try with CustomAsset_ prefix
                custom_name = f"CustomAsset_{item_type}"
                if custom_name in schemas:
                    schema = schemas[custom_name]
                    if 'properties' in schema:
                        return schema['properties']

            return None

        except Exception as e:
            print_error(f"Failed to get fields for {item_type}: {str(e)}")
            return None

    def create_item(self, item_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create an item in GLPI

        Args:
            item_type: Type of item to create
            data: Item data

        Returns:
            Created item data or None if failed
        """
        try:
            if not self._ensure_authenticated():
                return None

            # Determine endpoint based on asset type
            if self._is_custom_asset(item_type):
                url = f"{self.api_url}/Assets/Custom/{item_type}"
            else:
                url = f"{self.api_url}/Assets/{item_type}"

            response = requests.post(
                url=url,
                headers=self._get_headers(include_content_type=True),
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print_error(f"Failed to create {item_type}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print_error(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print_error(f"Response: {e.response.text}")
            return None

    def search_item(self, item_type: str, field: str, value: str) -> List[Dict[str, Any]]:
        """
        Search for items in GLPI with pagination support

        Args:
            item_type: Type of item to search
            field: Field to search on
            value: Value to search for (exact match)

        Returns:
            List of matching items
        """
        try:
            if not self._ensure_authenticated():
                return []

            # Determine endpoint based on asset type
            if self._is_custom_asset(item_type):
                url = f"{self.api_url}/Assets/Custom/{item_type}"
            else:
                url = f"{self.api_url}/Assets/{item_type}"

            # Use exact match RSQL filtering and pagination
            filter_query = f"{field}=={value}"
            all_results = []
            start = 0
            limit = 100

            while True:
                params = {
                    "filter": filter_query,
                    "start": start,
                    "limit": limit
                }

                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                response.raise_for_status()

                results = response.json()
                if not results:
                    break

                all_results.extend(results)

                # If we got fewer results than the limit, we've reached the end
                if len(results) < limit:
                    break

                start += limit

            return all_results

        except requests.exceptions.RequestException as e:
            print_error(f"Failed to search {item_type}: {str(e)}")
            return []

    def resolve_dropdown_id(self, dropdown_type: str, name: str, asset_type: Optional[str] = None) -> Optional[int]:
        """
        Resolve a dropdown item name to its ID

        Args:
            dropdown_type: Type of dropdown (e.g., Location, Manufacturer, State, User, Group)
            name: Name to search for (for locations, can be hierarchical like "Biuro > 6 Piętro > IT")
            asset_type: Optional asset type for context-aware resolution (e.g., "Laptop" for LaptopModel)

        Returns:
            The ID of the item or None if not found
        """
        try:
            if not self._ensure_authenticated():
                return None

            # Determine the correct endpoint and method
            # Special handling for User - search by username field
            if dropdown_type == 'User':
                # Users: use /Administration/User endpoint with username filter
                url = f"{self.api_url}/Administration/User"
                filter_query = f"username=={name.strip()}"
                params = {"filter": filter_query, "limit": 1}

                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                response.raise_for_status()

                users = response.json()
                if users and len(users) > 0:
                    return users[0].get('id')
                return None

            # For custom asset models, check if it's a custom asset type
            elif dropdown_type.endswith('Model') and asset_type and self._is_custom_asset(asset_type):
                # Custom asset model - use /Assets/Custom/{AssetType}Model
                url = f"{self.api_url}/Assets/Custom/{asset_type}Model"
            else:
                # Standard dropdown
                url = f"{self.api_url}/Dropdowns/{dropdown_type}"

            # For hierarchical names (locations), search by completename
            # Otherwise search by name
            if '>' in name:
                # Hierarchical path - search by completename
                filter_query = f"completename=={name.strip()}"
            else:
                # Simple name
                filter_query = f"name=={name.strip()}"

            params = {"filter": filter_query, "limit": 1}

            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()

            results = response.json()
            if results and len(results) > 0:
                return results[0].get('id')

            return None

        except requests.exceptions.RequestException as e:
            print_warning(f"Failed to resolve {dropdown_type} '{name}': {str(e)}")
            return None


class AssetImporter:
    """Main asset importer class"""

    def __init__(self, client: GLPIAPIClient):
        self.client = client
        # Mapping of field suffixes to dropdown types
        self.dropdown_mappings = {
            'locations_id': 'Location',
            'manufacturers_id': 'Manufacturer',
            'models_id': 'Model',
            'states_id': 'State',
            'users_id': 'User',  # Resolved by username/login via /Administration/User/username/{username}
            'groups_id': 'Group',
            'types_id': 'Type',
            'computermodels_id': 'ComputerModel',
            'computertypes_id': 'ComputerType',
            'networks_id': 'Network',
            'autoupdatesystems_id': 'AutoUpdateSystem',
        }

    def resolve_field_value(self, field_name: str, value: str, asset_type: str) -> Any:
        """
        Resolve a field value - convert names to IDs for dropdown fields

        Args:
            field_name: Name of the field
            value: Value to resolve (might be a name or already an ID)
            asset_type: The asset type being imported

        Returns:
            Resolved value (ID for dropdowns, original value otherwise)
        """
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
            resolved_id = self.client.resolve_dropdown_id(dropdown_type, str(value), asset_type)
            if resolved_id is not None:
                return resolved_id
            else:
                print_warning(f"Could not resolve {field_name} '{value}' to an ID. Using original value.")

        return value

    def generate_template(self, asset_type: str, output_file: str = "template.csv"):
        """
        Generate a CSV template for a specific asset type

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
                custom_field_names = list(custom_fields_info['properties'].keys())

        # Combine standard fields with custom fields
        fields = base_fields + custom_field_names

        # Try to get schema from API (currently not used to override fields)
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
            print_info(f"  - Names (will be auto-resolved, e.g., 'HP' for manufacturer)")
            print_info(f"  - Hierarchical paths for locations (e.g., 'Biuro > 6 Piętro > IT')")

        except Exception as e:
            print_error(f"Failed to create template: {str(e)}")

    def import_from_csv(self, asset_type: str, csv_file: str,
                       skip_duplicates: bool = True) -> Dict[str, int]:
        """
        Import assets from CSV file

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
                    if row.get('name', '').startswith('<') or row.get('name', '') == 'Example Asset Name':
                        print_warning(f"[{i}/{stats['total']}] Skipping template row")
                        stats["skipped"] += 1
                        continue

                    # Clean up row data
                    item_data = {}
                    for key, value in row.items():
                        if value and not value.startswith('<') and value.strip():
                            # Resolve field values (convert names to IDs for dropdowns)
                            resolved_value = self.resolve_field_value(key, value.strip(), asset_type)
                            item_data[key] = resolved_value

                    # Get custom field names for this asset type
                    api_fields = self.client.get_asset_fields(asset_type)
                    custom_field_names = set()
                    if api_fields and 'custom_fields' in api_fields:
                        custom_fields_info = api_fields['custom_fields']
                        if 'properties' in custom_fields_info:
                            custom_field_names = set(custom_fields_info['properties'].keys())

                    # Transform *_id fields to object format for GLPI API
                    # Also extract custom fields to nest under custom_fields
                    # e.g., locations_id: 3 -> location: {id: 3}
                    transformed_data = {}
                    extracted_custom_fields = {}

                    for key, value in item_data.items():
                        # Check if this is a custom field
                        if key in custom_field_names:
                            extracted_custom_fields[key] = value
                        elif key.endswith('_id') and isinstance(value, int):
                            # Convert field_name_id to field_name with object
                            field_name = key[:-3]  # Remove '_id' suffix
                            # Handle plural to singular (locations -> location, etc.)
                            if field_name.endswith('s'):
                                field_name = field_name[:-1]
                            transformed_data[field_name] = {'id': value}
                        else:
                            transformed_data[key] = value

                    # Add custom fields as nested object if any exist
                    if extracted_custom_fields:
                        transformed_data['custom_fields'] = extracted_custom_fields

                    item_data = transformed_data

                    if not item_data.get('name'):
                        print_warning(f"[{i}/{stats['total']}] Skipping row without name")
                        stats["skipped"] += 1
                        continue

                    # Check for duplicates
                    if skip_duplicates and item_data.get('serial'):
                        existing = self.client.search_item(asset_type, 'serial', item_data['serial'])
                        if existing:
                            print_warning(f"[{i}/{stats['total']}] Skipping duplicate: {item_data['name']} (serial: {item_data['serial']})")
                            stats["skipped"] += 1
                            continue

                    # Create item
                    print_info(f"[{i}/{stats['total']}] Creating: {item_data['name']}")
                    result = self.client.create_item(asset_type, item_data)

                    if result:
                        print_success(f"[{i}/{stats['total']}] Successfully created: {item_data['name']}")
                        stats["success"] += 1
                    else:
                        print_error(f"[{i}/{stats['total']}] Failed to create: {item_data['name']}")
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
        """List all available asset types"""
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
        """Show all available fields for a specific asset type"""
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
                print(f"\n{Colors.OKBLUE}Custom Fields ({len(custom_fields)}):{Colors.ENDC}")
                print("-" * 95)
                for cf_name, cf_info in sorted(custom_fields.items()):
                    cf_type = cf_info.get('type', 'unknown')
                    cf_desc = cf_info.get('description', '')
                    if len(cf_desc) > 50:
                        cf_desc = cf_desc[:47] + "..."
                    print(f"{cf_name:<30} {cf_type:<15} {cf_desc:<50}")

            print_info("\nUse these field names when creating CSV files for import.")
            print_info("Fields marked as 'read-only' are set by GLPI and cannot be imported.")
        else:
            print_warning(f"Could not retrieve field information for {asset_type}")
            print_info("This may happen if the asset type is not found in the API documentation.")


def load_config(config_file: str = "config.json") -> Optional[Dict[str, Any]]:
    """Load configuration from JSON file"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print_error(f"Failed to load config file: {str(e)}")
    return None


def save_config(config: Dict[str, Any], config_file: str = "config.json"):
    """Save configuration to JSON file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print_success(f"Configuration saved to {config_file}")
    except Exception as e:
        print_error(f"Failed to save config file: {str(e)}")


def create_default_config(config_file: str = "config.json"):
    """Create a default configuration file"""
    default_config = {
        "base_url": "http://192.168.9.9",
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "username": "your_username",
        "password": "your_password",
        "verify_ssl": True,
        "entity_id": None,
        "profile_id": None,
        "timeout": 30
    }

    save_config(default_config, config_file)
    print_info(f"Please edit {config_file} with your GLPI credentials")


def main():
    """Main entry point"""
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
  python glpi_asset_importer.py --import Asset_CustomType --file custom.csv
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
