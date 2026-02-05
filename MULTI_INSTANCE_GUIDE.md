# Multi-Instance Configuration Guide

## Overview

The GLPI Asset Importer now supports multiple GLPI instances in a single configuration file. This allows you to:

- Manage multiple GLPI systems (production, development, test, etc.)
- Easily switch between instances
- Migrate assets between different GLPI systems
- Keep all credentials in one secure file

## Configuration File Format

### Multi-Instance Config (New Format)

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
            "description": "Production GLPI instance"
        },
        "development": {
            "base_url": "http://dev.glpi.local",
            "client_id": "dev_client_id",
            "client_secret": "dev_secret",
            "username": "admin",
            "password": "dev_password",
            "verify_ssl": false,
            "description": "Development GLPI instance"
        },
        "test": {
            "base_url": "http://test.glpi.local",
            "client_id": "test_client_id",
            "client_secret": "test_secret",
            "username": "testuser",
            "password": "test_password",
            "verify_ssl": false,
            "description": "Test environment"
        }
    },
    "default_instance": "production"
}
```

### Legacy Single-Instance Config (Still Supported)

```json
{
    "base_url": "http://your-glpi-server",
    "client_id": "your_client_id",
    "client_secret": "your_secret",
    "username": "admin",
    "password": "password",
    "verify_ssl": true
}
```

**Note**: Legacy configs are automatically converted to multi-instance format with instance name "default".

## Quick Start

### 1. Create Multi-Instance Config

```bash
python glpi_asset_importer.py --init-config
```

This creates a template with two instances (production and development).

### 2. Edit Config

Edit `config.json` and add your GLPI credentials for each instance.

### 3. List Configured Instances

```bash
python glpi_asset_importer.py --list-instances
```

**Output**:

```
===============================================
Configured GLPI Instances
===============================================

production ⭐ [default]
  Production GLPI instance (https://glpi.company.com)

development
  Development GLPI instance (http://dev.glpi.local)
```

### 4. Use Specific Instance

```bash
# Use production instance (default)
python glpi_asset_importer.py --list-types

# Use development instance explicitly
python glpi_asset_importer.py --instance development --list-types

# Export from production
python glpi_asset_importer.py --instance production --export Computer --output prod_computers.csv

# Import to development
python glpi_asset_importer.py --instance development --import-migration --file prod_computers.csv
```

## Commands with Instance Selection

### Standard Commands

```bash
# List asset types in specific instance
python glpi_asset_importer.py --instance production --list-types

# Show fields for asset type
python glpi_asset_importer.py --instance development --show-fields Computer

# Generate template from specific instance
python glpi_asset_importer.py --instance production --generate-template Computer

# Import to specific instance
python glpi_asset_importer.py --instance development --import Computer --file computers.csv
```

### Migration Commands

```bash
# Export from production
python glpi_asset_importer.py --instance production --export Computer --output prod_export.csv

# Interactive export from development
python glpi_asset_importer.py --instance development --export-interactive Laptop

# Import to test instance
python glpi_asset_importer.py --instance test --import-migration --file prod_export.csv
```

## Cross-Instance Migration

Migrate assets directly from one instance to another:

```bash
python glpi_asset_importer.py --cross-instance-migrate \
    --source-instance production \
    --target-instance development
```

**Interactive Flow**:

1. Select source instance (if not specified)
2. Select target instance (if not specified)
3. Select asset type to migrate
4. Choose fields to export
5. Apply filters (optional)
6. Export from source
7. Configure value mapping (optional)
8. Import to target

## Use Cases

### Use Case 1: Dev-to-Production Migration

```bash
# Test on development first
python glpi_asset_importer.py --instance development --import Computer --file new_computers.csv

# Verify
python glpi_asset_importer.py --instance development --list-types

# Once verified, import to production
python glpi_asset_importer.py --instance production --import Computer --file new_computers.csv
```

### Use Case 2: Production Backup

```bash
# Export all asset types from production
python glpi_asset_importer.py --instance production --export Computer --output backup_computers.csv
python glpi_asset_importer.py --instance production --export Monitor --output backup_monitors.csv
python glpi_asset_importer.py --instance production --export Printer --output backup_printers.csv
```

### Use Case 3: System Migration

```bash
# Migrate everything from old to new instance
python glpi_asset_importer.py --cross-instance-migrate \
    --source-instance old_system \
    --target-instance new_system
```

### Use Case 4: Multi-Environment Management

```json
{
    "instances": {
        "prod_us": {
            "base_url": "https://glpi-us.company.com",
            "description": "US Production"
        },
        "prod_eu": {
            "base_url": "https://glpi-eu.company.com",
            "description": "EU Production"
        },
        "staging": {
            "base_url": "https://staging.glpi.company.com",
            "description": "Staging Environment"
        },
        "dev": {
            "base_url": "http://localhost:8080",
            "description": "Local Development"
        }
    },
    "default_instance": "dev"
}
```

## Default Instance

The `default_instance` setting determines which instance is used when `--instance` is not specified.

```json
{
  "instances": {
    ...
  },
  "default_instance": "production"
}
```

**Usage**:

```bash
# Uses production (default)
python glpi_asset_importer.py --list-types

# Explicitly use development
python glpi_asset_importer.py --instance development --list-types
```

## Instance Configuration Options

Each instance can have these settings:

| Option          | Required | Description                              |
| --------------- | -------- | ---------------------------------------- |
| `base_url`      | ✅       | GLPI base URL                            |
| `client_id`     | ✅       | OAuth client ID                          |
| `client_secret` | ✅       | OAuth client secret                      |
| `username`      | ✅       | GLPI username                            |
| `password`      | ✅       | GLPI password                            |
| `verify_ssl`    | ❌       | SSL verification (default: true)         |
| `entity_id`     | ❌       | Entity ID for multi-entity setups        |
| `profile_id`    | ❌       | Profile ID                               |
| `timeout`       | ❌       | Request timeout in seconds (default: 30) |
| `description`   | ❌       | Human-readable description               |

## Security Considerations

### Multiple Credentials

- Each instance has its own credentials
- Keep `config.json` secure and out of version control
- Use different passwords for each environment

### Environment-Specific Settings

```json
{
    "instances": {
        "production": {
            "verify_ssl": true,
            "timeout": 60
        },
        "development": {
            "verify_ssl": false,
            "timeout": 30
        }
    }
}
```

## Troubleshooting

### Instance Not Found

```
❌ Instance 'staging' not found in config
ℹ Available instances: production, development
```

**Solution**: Check spelling or add the instance to config.json

### No Default Instance

```bash
# If no default set, you must specify instance
python glpi_asset_importer.py --instance production --list-types
```

**Solution**: Set `default_instance` in config.json

### Legacy Config Warning

If using old single-instance format, you'll see:

```
ℹ Using default instance: default
```

**Solution**: Migrate to new format with `--init-config` and copy your credentials

## Migration from Legacy Config

### Option 1: Manual Migration

Old format:

```json
{
  "base_url": "http://glpi.local",
  "client_id": "abc123",
  ...
}
```

New format:

```json
{
  "instances": {
    "production": {
      "base_url": "http://glpi.local",
      "client_id": "abc123",
      ...
    }
  },
  "default_instance": "production"
}
```

### Option 2: Keep Legacy Format

Legacy configs still work! They're automatically treated as a single instance named "default".

## Best Practices

1. **Use Descriptive Names**: Name instances clearly (production, development, not server1, server2)
2. **Set Default Wisely**: Set `default_instance` to your most-used instance
3. **Document Instances**: Use `description` field to document each instance
4. **Backup Config**: Keep encrypted backups of config.json
5. **Per-Environment SSL**: Use `verify_ssl: true` for production, false for dev/test
6. **Test Migrations**: Always test migrations on non-production first

## Example Workflows

### Workflow 1: Daily Operations

```bash
# Morning: Check production
python glpi_asset_importer.py --instance production --list-types

# Work on development
python glpi_asset_importer.py --instance development --import Computer --file new_assets.csv

# Verify in development
python glpi_asset_importer.py --instance development --export Computer --output verify.csv

# Deploy to production
python glpi_asset_importer.py --instance production --import Computer --file new_assets.csv
```

### Workflow 2: System Consolidation

```bash
# Export from multiple old systems
python glpi_asset_importer.py --instance old_office_a --export Computer --output office_a.csv
python glpi_asset_importer.py --instance old_office_b --export Computer --output office_b.csv

# Import to new consolidated system
python glpi_asset_importer.py --instance new_system --import-migration --file office_a.csv
python glpi_asset_importer.py --instance new_system --import-migration --file office_b.csv
```

## Support

For help with multi-instance configuration:

1. Check `--list-instances` output
2. Verify config.json format
3. Test with `--instance` flag
4. Review this guide

## Version

Multi-instance support added in **Version 1.2**
