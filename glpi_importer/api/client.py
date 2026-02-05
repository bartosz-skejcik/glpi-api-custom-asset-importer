"""GLPI API Client for OAuth2 authentication and API operations."""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..utils.console import print_info, print_success, print_error, print_warning


class GLPIAPIClient:
    """GLPI API Client using OAuth2 authentication."""

    def __init__(self, base_url: str, client_id: str, client_secret: str,
                 username: str, password: str, verify_ssl: bool = True,
                 entity_id: Optional[int] = None, profile_id: Optional[int] = None,
                 timeout: int = 30):
        """
        Initialize the GLPI API client.

        Args:
            base_url: Base URL of GLPI instance (e.g., http://localhost)
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
        self._custom_assets_cache: Optional[List[str]] = None

        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()

    def authenticate(self) -> bool:
        """
        Authenticate with GLPI API using OAuth2 password grant.

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
                "scope": "email user api inventory status graphql assets"
            }

            response = requests.post(
                token_url, data=data, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)

            if not self.access_token:
                print_error("Failed to get access token from response")
                return False

            # Store token expiry time (with 60 second buffer)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            print_success("Authentication successful!")
            return True

        except requests.exceptions.RequestException as e:
            print_error(f"Authentication failed: {str(e)}")
            if hasattr(e.response, 'text'):
                print_error(f"Response: {e.response.text}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid token, re-authenticating if necessary."""
        if not self.access_token or not self.token_expires_at:
            return self.authenticate()

        if datetime.now() >= self.token_expires_at:
            print_info("Token expired, re-authenticating...")
            return self.authenticate()

        return True

    def _get_headers(self, include_content_type: bool = False) -> Dict[str, str]:
        """
        Get headers for API requests.

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
        """Check if an asset type is a custom asset."""
        try:
            if not self._ensure_authenticated():
                return False

            # Use cached list if available
            if self._custom_assets_cache is None:
                # Get custom assets list
                url = f"{self.api_url}/Assets/Custom/"
                response = requests.get(url, headers=self._get_headers(
                ), verify=self.verify_ssl, timeout=self.timeout)
                if response.status_code == 200:
                    custom_assets = response.json()
                    self._custom_assets_cache = []
                    for asset in custom_assets:
                        itemtype = asset.get('itemtype', '')
                        name = asset.get('name', '')
                        if itemtype:
                            self._custom_assets_cache.append(itemtype)
                        if name and name != itemtype:
                            self._custom_assets_cache.append(name)
                else:
                    self._custom_assets_cache = []

            return item_type in self._custom_assets_cache
        except Exception as e:
            return False

    def get_asset_definitions(self) -> List[Dict[str, Any]]:
        """
        Get all asset types available in GLPI (both standard and custom).

        Returns:
            List of asset types with itemtype, name, and href
        """
        try:
            if not self._ensure_authenticated():
                return []

            all_assets = []

            # Get standard assets
            url = f"{self.api_url}/Assets/"
            response = requests.get(url, headers=self._get_headers(
            ), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            all_assets.extend(response.json())

            # Get custom assets
            url = f"{self.api_url}/Assets/Custom/"
            response = requests.get(url, headers=self._get_headers(
            ), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            all_assets.extend(response.json())

            return all_assets
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to get asset types: {str(e)}")
            return []

    def get_asset_definition(self, asset_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific asset type by itemtype or name.

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
        Get the schema for an item type.

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
                    response = requests.options(url, headers=self._get_headers(
                    ), verify=self.verify_ssl, timeout=self.timeout)
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
        Get all available fields/properties for an asset type from OpenAPI schema.

        Args:
            item_type: Type of item (e.g., Computer, Monitor, Laptop)

        Returns:
            Dictionary of field properties or None if not found
        """
        try:
            # Get the OpenAPI documentation
            doc_url = f"{self.base_url}/api.php/doc.json"
            response = requests.get(
                doc_url, verify=self.verify_ssl, timeout=self.timeout)
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
        Create an item in GLPI.

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
                    print_error(
                        f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print_error(f"Response: {e.response.text}")
            return None

    def search_item(self, item_type: str, field: str, value: str) -> List[Dict[str, Any]]:
        """
        Search for items in GLPI with pagination support.

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

    def search_items(self, item_type: str, filters: Dict[str, Any] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for items in GLPI with optional filters.

        Args:
            item_type: Type of item to search (can be simple name or full itemtype with namespace)
            filters: Optional dictionary of field:value filters (RSQL format)
            limit: Optional limit on number of results (None = all results)

        Returns:
            List of matching items
        """
        try:
            if not self._ensure_authenticated():
                return []

            # Get the asset definition to determine the correct endpoint
            definition = self.get_asset_definition(item_type)
            if definition:
                # Use the href from the definition to determine the correct endpoint
                href = definition.get('href', '')

                # Check if it's a custom asset by looking at the href
                if '/Custom/' in href:
                    # Extract just the simple name after /Custom/
                    # href is like "/Assets/Custom/Dyktafon"
                    simple_name = href.split('/Custom/')[-1]
                    url = f"{self.api_url}/Assets/Custom/{simple_name}"
                else:
                    # Standard asset - use itemtype from definition
                    actual_itemtype = definition.get('itemtype', item_type)
                    url = f"{self.api_url}/Assets/{actual_itemtype}"
            else:
                # Fallback - try to determine if it's a custom asset
                if self._is_custom_asset(item_type):
                    url = f"{self.api_url}/Assets/Custom/{item_type}"
                else:
                    url = f"{self.api_url}/Assets/{item_type}"

            # Build filter query
            filter_parts = []
            if filters:
                for field, value in filters.items():
                    if isinstance(value, str):
                        filter_parts.append(f"{field}=={value}")
                    else:
                        filter_parts.append(f"{field}=={value}")

            filter_query = ";".join(filter_parts) if filter_parts else None

            all_results = []
            start = 0
            page_limit = 100

            while True:
                params = {
                    "start": start,
                    "limit": page_limit,
                    "with_custom_fields": "true"  # Include custom fields in response
                }

                if filter_query:
                    params["filter"] = filter_query

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

                # Check if we've reached the user-specified limit
                if limit and len(all_results) >= limit:
                    all_results = all_results[:limit]
                    break

                # If we got fewer results than the page limit, we've reached the end
                if len(results) < page_limit:
                    break

                start += page_limit

            return all_results

        except requests.exceptions.RequestException as e:
            print_error(f"Failed to search {item_type}: {str(e)}")
            return []

    def resolve_dropdown_id(self, dropdown_type: str, name: str, asset_type: Optional[str] = None) -> Optional[int]:
        """
        Resolve a dropdown item name to its ID.

        Args:
            dropdown_type: Type of dropdown (e.g., Location, Manufacturer, State, User, Group)
            name: Name to search for (for locations, can be hierarchical like "Office > Floor > Room")
            asset_type: Optional asset type for context-aware resolution (e.g., "Laptop" for LaptopModel)

        Returns:
            The ID of the item or None if not found
        """
        try:
            if not self._ensure_authenticated():
                return None

            # Special handling for User - search by username field
            if dropdown_type == 'User':
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

            # For models with asset_type context, check if it's a custom asset
            elif dropdown_type == 'Model' and asset_type and self._is_custom_asset(asset_type):
                url = f"{self.api_url}/Assets/Custom/{asset_type}Model"
                print_info(f"Using custom asset model endpoint: {url}")
            elif dropdown_type.endswith('Model') and asset_type and self._is_custom_asset(asset_type):
                url = f"{self.api_url}/Assets/Custom/{asset_type}Model"
            else:
                # Standard dropdown
                url = f"{self.api_url}/Dropdowns/{dropdown_type}"

            # For hierarchical names (locations), search by completename
            # Otherwise search by name
            # Quote the value if it contains special characters (parentheses, spaces, etc.)
            search_value = name.strip()
            if any(char in search_value for char in ['(', ')', ' ', '-', '&', ',', '.', '/']):
                search_value = f"'{search_value}'"

            if '>' in name:
                filter_query = f"completename=={search_value}"
            else:
                filter_query = f"name=={search_value}"

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
            print_warning(
                f"Failed to resolve {dropdown_type} '{name}': {str(e)}")
            return None

    def create_dropdown_item(self, dropdown_type: str, name: str, asset_type: Optional[str] = None) -> Optional[int]:
        """
        Create a new dropdown item.

        Args:
            dropdown_type: Type of dropdown (e.g., Model, Manufacturer, State)
            name: Name of the item to create
            asset_type: Optional asset type for context-aware creation (e.g., "Tablet" for TabletModel)

        Returns:
            The ID of the created item or None if failed
        """
        try:
            if not self._ensure_authenticated():
                return None

            # Special handling for Model dropdown with custom assets
            if dropdown_type == 'Model' and asset_type and self._is_custom_asset(asset_type):
                url = f"{self.api_url}/Assets/Custom/{asset_type}Model"
                print_info(
                    f"Using custom asset model endpoint for creation: {url}")
            # For custom asset models ending with 'Model'
            elif dropdown_type.endswith('Model') and asset_type and self._is_custom_asset(asset_type):
                url = f"{self.api_url}/Assets/Custom/{asset_type}Model"
                print_info(
                    f"Using custom asset model endpoint for creation: {url}")
            else:
                # Standard dropdown
                url = f"{self.api_url}/Dropdowns/{dropdown_type}"
                print_info(
                    f"Using standard dropdown endpoint for creation: {url}")

            data = {"name": name.strip()}

            response = requests.post(
                url=url,
                headers=self._get_headers(include_content_type=True),
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            created_id = result.get('id')

            if created_id:
                print_success(
                    f"Created new {dropdown_type}: {name} (ID: {created_id})")
                return created_id

            return None

        except requests.exceptions.RequestException as e:
            print_error(f"Failed to create {dropdown_type} '{name}': {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print_error(
                        f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print_error(f"Response: {e.response.text}")
            return None
