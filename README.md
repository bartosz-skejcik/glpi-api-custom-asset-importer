# GLPI Asset Importer

A powerful command-line tool to import assets from CSV files into GLPI using the v2.1 API. Supports GLPI v11 custom asset definitions with full OAuth2 authentication.

## Features

-   ✅ **OAuth2 Authentication** - Secure password grant authentication
-   ✅ **Custom Asset Support** - Works with GLPI v11 custom asset definitions
-   ✅ **CSV Template Generation** - Automatically generate templates for any asset type
-   ✅ **Batch Import** - Import multiple assets at once from CSV files
-   ✅ **Duplicate Detection** - Skip assets that already exist (based on serial number)
-   ✅ **Error Handling** - Comprehensive error handling with clear messages
-   ✅ **Clean Terminal UI** - Color-coded output for easy reading
-   ✅ **Configuration Management** - Store credentials in a config file

## Requirements

-   Python 3.7 or higher
-   GLPI 10.0+ with API enabled
-   OAuth2 client configured in GLPI

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### Step 1: Create OAuth Client in GLPI

1. Log in to your GLPI instance
2. Go to **Setup > General > OAuth Clients**
3. Click **Add** to create a new client
4. Set the following:
    - **Name**: Asset Importer (or any name you prefer)
    - **Active**: Yes
    - **Grant types**: Select "Password"
5. Save and note down the **Client ID** and **Client Secret**

### Step 2: Create Configuration File

Run the following command to create a default configuration file:

```bash
python glpi_asset_importer.py --init-config
```

This creates a `config.json` file. Edit it with your GLPI credentials:

```json
{
    "base_url": "http://192.168.9.9",
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here",
    "username": "your_glpi_username",
    "password": "your_glpi_password",
    "verify_ssl": true
}
```

**Security Note**: Keep this file secure and don't commit it to version control. Add it to `.gitignore`.

## Usage

### List Available Asset Types

To see all available asset types (including custom ones):

```bash
python glpi_asset_importer.py --list-types
```

### Generate a CSV Template

Generate a template for a specific asset type:

```bash
# For built-in types
python glpi_asset_importer.py --generate-template Computer

# For custom asset types
python glpi_asset_importer.py --generate-template Asset_CustomType

# Specify custom output file
python glpi_asset_importer.py --generate-template Monitor --output monitors_template.csv
```

This creates a CSV file with the appropriate columns for your asset type.

### Fill the Template

Open the generated CSV file in Excel, LibreOffice, or any text editor and fill in your asset data:

-   **name** (required): The name of the asset
-   **serial**: Serial number
-   **otherserial**: Alternative serial/inventory number
-   **comment**: Description or notes
-   **locations_id**: Location ID from GLPI (numeric)
-   **manufacturers_id**: Manufacturer ID from GLPI (numeric)
-   **models_id**: Model ID from GLPI (numeric)
-   **states_id**: State ID from GLPI (numeric)
-   **users_id**: Assigned user ID (numeric)
-   **groups_id**: Assigned group ID (numeric)

**Tips:**

-   You can find IDs by looking at the URL in GLPI when viewing a specific item
-   Leave fields empty if you don't have the information
-   Remove the example row before importing

### Import Assets

Import assets from your filled CSV file:

```bash
# Basic import
python glpi_asset_importer.py --import Computer --file computers.csv

# Import custom asset type
python glpi_asset_importer.py --import Asset_MyCustomAsset --file custom_assets.csv

# Allow duplicate imports (skip duplicate checking)
python glpi_asset_importer.py --import Computer --file computers.csv --allow-duplicates
```

### Advanced Options

```bash
# Use a different config file
python glpi_asset_importer.py --config production.json --list-types

# Disable SSL verification (not recommended for production)
python glpi_asset_importer.py --no-ssl-verify --import Computer --file computers.csv
```

## Common Asset Types

### Built-in Asset Types

-   `Computer` - Desktop computers and laptops
-   `Monitor` - Display screens
-   `NetworkEquipment` - Switches, routers, etc.
-   `Peripheral` - Keyboards, mice, etc.
-   `Phone` - Telephones
-   `Printer` - Printers and multifunction devices
-   `Software` - Software licenses

### Custom Asset Types

Custom asset types in GLPI v11 follow the pattern `Asset_<SystemName>`. Use the `--list-types` command to see all available custom asset types in your GLPI instance.

## CSV Format Example

Here's an example CSV file for computers:

```csv
name,serial,otherserial,comment,locations_id,manufacturers_id,models_id,states_id
DESKTOP-001,ABC123456,INV-2024-001,John's workstation,5,2,8,1
LAPTOP-042,XYZ789012,INV-2024-002,Sales team laptop,3,1,15,1
SERVER-DB01,SRV999888,INV-2024-003,Main database server,1,3,22,1
```

## Error Handling

The tool includes comprehensive error handling:

-   **Authentication Errors**: Clear messages if credentials are wrong
-   **Network Errors**: Handles connection issues gracefully
-   **Invalid Data**: Reports which rows have problems
-   **Duplicate Detection**: Warns when assets already exist
-   **API Errors**: Shows detailed error messages from GLPI

## Terminal Output

The tool uses color-coded output for easy reading:

-   🟢 **Green** - Success messages
-   🔴 **Red** - Error messages
-   🟡 **Yellow** - Warning messages
-   🔵 **Cyan** - Information messages

## Troubleshooting

### Authentication Failed

**Problem**: "Authentication failed" error

**Solutions**:

-   Verify your client ID and secret are correct
-   Check that the OAuth client is active in GLPI
-   Ensure "Password" grant type is enabled for the client
-   Verify your username and password

### Asset Type Not Found

**Problem**: "Asset definition not found" error

**Solutions**:

-   Run `--list-types` to see available types
-   For custom assets, use the exact system name shown in the list
-   Ensure you have permissions to access that asset type

### SSL Certificate Error

**Problem**: SSL verification errors

**Solutions**:

-   If using self-signed certificates, use `--no-ssl-verify` flag
-   Better: Install proper SSL certificates on your GLPI server
-   For production, always use valid SSL certificates

### Import Failures

**Problem**: Items fail to import

**Solutions**:

-   Check that all required fields are filled
-   Verify that ID fields (locations_id, etc.) contain valid numeric IDs
-   Ensure you have permissions to create items of that type
-   Check the detailed error messages in the output

## Best Practices

1. **Start Small**: Test with a small CSV file first (2-3 items)
2. **Backup**: Backup your GLPI database before large imports
3. **Validate Data**: Review your CSV file for errors before importing
4. **Use IDs**: Use numeric IDs for relationships (locations, manufacturers, etc.)
5. **Duplicate Check**: Keep duplicate checking enabled unless you need duplicates
6. **Monitor Progress**: Watch the terminal output during import

## API Scope Requirements

The OAuth client needs the following scope:

-   `api` - Access to all API endpoints

This is set automatically when you select the "Password" grant type.

## Security Considerations

-   Store `config.json` securely (it contains credentials)
-   Use environment variables for sensitive data in production
-   Enable SSL verification in production environments
-   Use strong, unique passwords for GLPI accounts
-   Regularly rotate OAuth client secrets
-   Limit OAuth client permissions to what's needed

## License

This tool is provided as-is for use with GLPI installations.

## Support

For GLPI API documentation, visit:

-   High-level API: `http://your-glpi-instance/api.php/v2.1/getting-started`
-   API Reference: `http://your-glpi-instance/api.php/doc`

## Version History

### Version 1.0

-   Initial release
-   OAuth2 authentication support
-   CSV template generation
-   Batch import functionality
-   Custom asset support
-   Duplicate detection
-   Comprehensive error handling
-   Color-coded terminal interface
