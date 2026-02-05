# GLPI Asset Importer

A powerful command-line tool to import assets from CSV files into GLPI using the v2.1 API. Supports GLPI v11 custom asset definitions with full OAuth2 authentication and multi-instance management.

## Features

- ✅ **OAuth2 Authentication** - Secure password grant authentication with proper scopes
- ✅ **Multi-Instance Support** - Manage multiple GLPI systems in one config
- ✅ **Cross-Instance Migration** - Export from one instance and import to another
- ✅ **Custom Asset Support** - Works with GLPI v11 custom asset definitions
- ✅ **Custom Fields Support** - Import custom fields for custom assets
- ✅ **Smart Name Resolution** - Auto-resolves names to IDs for locations, manufacturers, models, states, and users
- ✅ **Hierarchical Locations** - Support for nested location paths (e.g., "Building > Floor > Room")
- ✅ **User Login Support** - Resolve users by their login names (e.g., LDAP usernames)
- ✅ **CSV Template Generation** - Automatically generate templates for any asset type including custom fields
- ✅ **Batch Import** - Import multiple assets at once from CSV files
- ✅ **Duplicate Detection** - Skip assets that already exist (based on serial number)
- ✅ **Migration Support** - Export and import assets for system migrations
- ✅ **Interactive Field Selection** - Choose specific fields to export
- ✅ **Migration Wizard** - Step-by-step guided migration process
- ✅ **Value Mapping** - Transform field values during migration (e.g., "DELL" → "Dell Inc.")
- ✅ **Mapping Templates** - Auto-generate mapping templates from exports
- ✅ **Error Handling** - Comprehensive error handling with clear messages
- ✅ **Clean Terminal UI** - Color-coded output for easy reading
- ✅ **Modular Architecture** - Well-organized codebase for easy maintenance

## Project Structure

```
glpi-api-custom-asset-importer/
├── glpi_importer/              # Main package
│   ├── api/                    # API client module
│   │   ├── __init__.py
│   │   └── client.py           # GLPIAPIClient class
│   ├── importer/               # Import logic module
│   │   ├── __init__.py
│   │   ├── asset_importer.py  # AssetImporter class
│   │   └── migration.py       # MigrationManager class
│   ├── utils/                  # Utilities module
│   │   ├── __init__.py
│   │   ├── console.py          # Terminal output formatting
│   │   └── config.py           # Configuration management
│   ├── __init__.py
│   └── cli.py                  # Command-line interface
├── glpi_asset_importer.py      # Entry point script
├── config.json                 # Configuration file (not in git)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Requirements

- Python 3.7 or higher
- GLPI 10.0+ with API enabled
- OAuth2 client configured in GLPI

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

### Step 2: Configure OAuth Client Scopes

**IMPORTANT**: The OAuth client must have the correct scopes enabled:

1. In GLPI, edit your OAuth client
2. Ensure these scopes are enabled:
    - ✅ **email** - User email access
    - ✅ **user** - User information access (required for username resolution)
    - ✅ **api** - General API access
    - ✅ **inventory** - Inventory access
    - ✅ **status** - Status information
    - ✅ **graphql** - GraphQL access

The tool automatically requests these scopes during authentication.

### Step 3: Create Configuration File

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

**Standard Fields:**

- **name** (required): The name of the asset
- **serial**: Serial number
- **otherserial**: Alternative serial/inventory number
- **comment**: Description or notes
- **locations_id**: Location (can use hierarchical path like "Building > Floor > Room" or numeric ID)
- **manufacturers_id**: Manufacturer (can use name like "DELL" or numeric ID)
- **models_id**: Model (can use name like "Latitude 3490" or numeric ID)
- **states_id**: State (can use name like "In use" or numeric ID)
- **users_id**: Assigned user (can use login name like "jsmith" or numeric ID)
- **groups_id**: Assigned group (can use name or numeric ID)

**Custom Fields:**

- Any custom fields defined for your custom asset type will appear as additional columns
- Fill them in as regular text fields

**Tips:**

- ✨ **Smart Resolution**: You can use names instead of IDs! The tool will automatically resolve:
    - Location paths: `"Office > 6th Floor > IT Department"`
    - User logins: `"jsmith"` or `"glpi"`
    - Manufacturer names: `"DELL"` or `"HP"`
    - Model names: `"Latitude 3490"`
    - State names: `"In use"` or `"Available"`
- Leave fields empty if you don't have the information
- Remove the example row before importing
- For LDAP-synced users, use their login names directly!

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

# Auto-create missing dropdown items
python glpi_asset_importer.py --import Computer --file computers.csv --auto-create-models
```

## Migration Features

The tool now supports exporting and importing assets for system migrations, including cross-instance migrations!

### Multi-Instance Configuration

Manage multiple GLPI systems (production, development, test) in one config file.

#### Create Multi-Instance Config

```bash
python glpi_asset_importer.py --init-config
```

Edit `config.json` with your instances:

```json
{
    "instances": {
        "production": {
            "base_url": "https://glpi.company.com",
            "client_id": "prod_client_id",
            "client_secret": "prod_secret",
            "username": "admin",
            "password": "prod_password",
            "verify_ssl": true,
            "description": "Production GLPI"
        },
        "development": {
            "base_url": "http://dev.glpi.local",
            "client_id": "dev_client_id",
            "client_secret": "dev_secret",
            "username": "admin",
            "password": "dev_password",
            "verify_ssl": false,
            "description": "Development GLPI"
        }
    },
    "default_instance": "development"
}
```

**See [MULTI_INSTANCE_GUIDE.md](MULTI_INSTANCE_GUIDE.md) for detailed multi-instance documentation.**

#### List Configured Instances

```bash
python glpi_asset_importer.py --list-instances
```

#### Use Specific Instance

```bash
# Use default instance
python glpi_asset_importer.py --list-types

# Use specific instance
python glpi_asset_importer.py --instance production --list-types
python glpi_asset_importer.py --instance development --export Computer --output dev_computers.csv
```

### Cross-Instance Migration

Migrate assets directly from one instance to another:

```bash
# Interactive mode
python glpi_asset_importer.py --cross-instance-migrate

# Specify instances
python glpi_asset_importer.py --cross-instance-migrate \
    --source-instance production \
    --target-instance development
```

This will:

1. Export assets from source instance
2. Apply value mapping if needed
3. Import to target instance
4. Report success/failure

### Migration Wizard (Recommended)

The easiest way to perform a migration is using the interactive wizard:

```bash
python glpi_asset_importer.py --migrate-wizard
```

The wizard will guide you through:

1. Choosing to export or import
2. Selecting asset types
3. Choosing fields to export
4. Setting up filters
5. Completing the migration

### Export Assets for Migration

#### Basic Export (All Fields)

Export all assets with all available fields:

```bash
# Export all computers
python glpi_asset_importer.py --export Computer --output computers_export.csv

# Export custom assets
python glpi_asset_importer.py --export Laptop --output laptops_export.csv
```

This creates:

- `computers_export.csv` - The exported data
- `computers_export_metadata.json` - Metadata about the export (asset type, date, field list, etc.)

#### Export Specific Fields

Export only the fields you need:

```bash
# Export only name, serial, and user assignment
python glpi_asset_importer.py --export Computer \
    --fields name,serial,users_id,locations_id \
    --output computers_export.csv
```

#### Export with Filters

Export only specific assets matching criteria:

```bash
# Export only computers in a specific location
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=5,states_id=1" \
    --output active_computers.csv

# Export computers with specific state
python glpi_asset_importer.py --export Computer \
    --filters "states_id=1" \
    --output in_use_computers.csv
```

#### Interactive Export (Field Selection)

Let the tool guide you through field selection:

```bash
python glpi_asset_importer.py --export-interactive Computer --output computers.csv
```

This will:

1. Show all available fields for the asset type
2. Let you select which fields to export
3. Ask if you want to apply filters
4. Export the data with metadata

### Import from Migration File

#### Basic Import

Import assets from an exported file:

```bash
# Import with metadata (asset type auto-detected)
python glpi_asset_importer.py --import-migration --file computers_export.csv

# Auto-create missing items (manufacturers, models, etc.)
python glpi_asset_importer.py --import-migration \
    --file computers_export.csv \
    --auto-create-models
```

#### Import Without Metadata

If you don't have a metadata file, specify the asset type:

```bash
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --import Computer
```

#### Import with Value Mapping

Transform field values during import (e.g., "DELL" → "Dell Inc."):

```bash
# Step 1: Create mapping template
python glpi_asset_importer.py --create-mapping-template \
    --file computers_export.csv \
    --output value_mapping.json

# Step 2: Edit value_mapping.json to customize mappings

# Step 3: Import with mappings
python glpi_asset_importer.py --import-migration \
    --file computers_export.csv \
    --value-mapping value_mapping.json \
    --auto-create-models
```

**Example Mapping File** (`value_mapping.json`):

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "HP Inc.",
        "LENOVO": "Lenovo"
    },
    "locations_id": {
        "HQ": "Headquarters",
        "Branch1": "Branch Office 1"
    },
    "states_id": {
        "Active": "In use",
        "OK": "In use"
    }
}
```

See [VALUE_MAPPING_GUIDE.md](VALUE_MAPPING_GUIDE.md) for complete value mapping documentation.

### Complete Migration Workflow Example

```bash
# Step 1: Export from source GLPI system
# Configure config.json for source system
python glpi_asset_importer.py --export-interactive Computer --output computers_export.csv

# Step 2: Transfer files to target system
# Copy computers_export.csv and computers_export_metadata.json to target system

# Step 3: Import into target GLPI system
# Configure config.json for target system
python glpi_asset_importer.py --import-migration \
    --file computers_export.csv \
    --auto-create-models
```

### Migration Best Practices

1. **Test First**: Always test migration with a small subset of data
2. **Include Metadata**: Keep the metadata JSON file with your CSV - it contains important context
3. **Field Selection**: Export only fields you need to reduce file size and complexity
4. **Auto-Create**: Use `--auto-create-models` to automatically create missing manufacturers, models, etc.
5. **Backup**: Always backup your target GLPI database before importing
6. **Verify**: After import, verify critical assets were migrated correctly
7. **ID Mapping**: Note that IDs will be different in the target system - the tool handles this automatically by name

### What Gets Migrated

The migration feature can export/import:

- ✅ Asset basic information (name, serial, etc.)
- ✅ Standard fields (locations, manufacturers, models, states, users, groups)
- ✅ Custom fields for custom assets
- ✅ All relationship data (resolved by name in target system)

### What Doesn't Get Migrated

- ❌ GLPI system IDs (these are auto-generated in target)
- ❌ Historical data (tickets, changes, problems)
- ❌ Relationships to items not in the export
- ❌ Files and documents
- ❌ Financial information (needs separate handling)

### Advanced Options

## Common Asset Types

### Built-in Asset Types

- `Computer` - Desktop computers and laptops
- `Monitor` - Display screens
- `NetworkEquipment` - Switches, routers, etc.
- `Peripheral` - Keyboards, mice, etc.
- `Phone` - Telephones
- `Printer` - Printers and multifunction devices
- `Software` - Software licenses

### Custom Asset Types

Custom asset types in GLPI v11 follow the pattern `Asset_<SystemName>`. Use the `--list-types` command to see all available custom asset types in your GLPI instance.

## CSV Format Example

Here's an example CSV file with smart name resolution:

```csv
name,serial,otherserial,comment,locations_id,manufacturers_id,models_id,states_id,users_id
DESKTOP-001,ABC123456,INV-2024-001,John's workstation,Office > 3rd Floor > Sales,DELL,OptiPlex 7080,In use,jsmith
LAPTOP-042,XYZ789012,INV-2024-002,Sales team laptop,Office > 2nd Floor > Marketing,HP,EliteBook 840,Available,mwilson
SERVER-DB01,SRV999888,INV-2024-003,Main database server,DataCenter > Rack A > Shelf 3,Dell,PowerEdge R740,In production,sysadmin
```

**Note**: You can mix IDs and names - the tool will handle both!

## Error Handling

The tool includes comprehensive error handling:

- **Authentication Errors**: Clear messages if credentials are wrong
- **Network Errors**: Handles connection issues gracefully
- **Invalid Data**: Reports which rows have problems
- **Duplicate Detection**: Warns when assets already exist
- **API Errors**: Shows detailed error messages from GLPI

## Terminal Output

The tool uses color-coded output for easy reading:

- 🟢 **Green** - Success messages
- 🔴 **Red** - Error messages
- 🟡 **Yellow** - Warning messages
- 🔵 **Cyan** - Information messages

## Troubleshooting

### Authentication Failed

**Problem**: "Authentication failed" error

**Solutions**:

- Verify your client ID and secret are correct
- Check that the OAuth client is active in GLPI
- Ensure "Password" grant type is enabled for the client
- Verify your username and password

### Asset Type Not Found

**Problem**: "Asset definition not found" error

**Solutions**:

- Run `--list-types` to see available types
- For custom assets, use the exact system name shown in the list
- Ensure you have permissions to access that asset type

### SSL Certificate Error

**Problem**: SSL verification errors

**Solutions**:

- If using self-signed certificates, use `--no-ssl-verify` flag
- Better: Install proper SSL certificates on your GLPI server
- For production, always use valid SSL certificates

### Import Failures

**Problem**: Items fail to import

**Solutions**:

- Check that all required fields are filled
- Verify that ID fields (locations_id, etc.) contain valid numeric IDs
- Ensure you have permissions to create items of that type
- Check the detailed error messages in the output

## Best Practices

1. **Start Small**: Test with a small CSV file first (2-3 items)
2. **Backup**: Backup your GLPI database before large imports
3. **Validate Data**: Review your CSV file for errors before importing
4. **Use IDs**: Use numeric IDs for relationships (locations, manufacturers, etc.)
5. **Duplicate Check**: Keep duplicate checking enabled unless you need duplicates
6. **Monitor Progress**: Watch the terminal output during import

- **Value Mapping** - Transform field values during migration (e.g., "DELL" → "Dell Inc.")
- **Mapping Templates** - Auto-generate value mapping templates from CSV files

## API Scope Requirements

The OAuth client needs the following scope:

- `api` - Access to all API endpoints

This is set automatically when you select the "Password" grant type.

## Security Considerations

- Store `config.json` securely (it contains credentials)
- Use environment variables for sensitive data in production
- Enable SSL verification in production environments
- Use strong, unique passwords for GLPI accounts
- Regularly rotate OAuth client secrets
- Limit OAuth client permissions to what's needed

## License

This tool is provided as-is for use with GLPI installations.

## Support

For GLPI API documentation, visit:

- High-level API: `http://your-glpi-instance/api.php/v2.1/getting-started`
- API Reference: `http://your-glpi-instance/api.php/doc`

## Version History

### Version 1.1

- **Migration Support** - Export and import assets for system migrations
- **Interactive Export** - Field selection wizard for exports
- **Migration Wizard** - Step-by-step guided migration process
- **Field Filtering** - Export only selected fields
- **Export Filters** - Filter assets during export
- **Metadata Files** - Auto-generated metadata for migration tracking
- **Auto-create Models** - Automatically create missing dropdown items during import

### Version 1.0

- Initial release
- OAuth2 authentication support with proper scopes
- CSV template generation with custom fields support
- Batch import functionality
- Custom asset support for GLPI v11
- Custom fields import
- Smart name resolution for dropdowns (locations, manufacturers, models, states, users)
- Hierarchical location path support ("Building > Floor > Room")
- User login name resolution (LDAP-friendly)
- Duplicate detection based on serial numbers
- Comprehensive error handling
- Color-coded terminal interface
- Modular, well-organized codebase
- Field inspection tool (--show-fields)
