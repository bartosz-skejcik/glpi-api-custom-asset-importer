# Quick Start Guide - Multi-Instance & Migrations

## 5-Minute Setup

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Create Config

```bash
python glpi_asset_importer.py --init-config
```

### 3. Edit config.json

```json
{
    "instances": {
        "production": {
            "base_url": "https://glpi.company.com",
            "client_id": "your_client_id",
            "client_secret": "your_secret",
            "username": "admin",
            "password": "your_password",
            "verify_ssl": true
        }
    },
    "default_instance": "production"
}
```

### 4. Test Connection

```bash
python glpi_asset_importer.py --list-types
```

## Common Tasks

### Task 1: Export Assets for Backup

```bash
# Export all computers
python glpi_asset_importer.py --export Computer --output backup_computers.csv
```

### Task 2: Import Assets

```bash
# Generate template
python glpi_asset_importer.py --generate-template Computer

# Fill template.csv with your data

# Import
python glpi_asset_importer.py --import Computer --file template.csv
```

### Task 3: Migrate Between Systems

```bash
# Option A: Use wizard (easiest)
python glpi_asset_importer.py --migrate-wizard

# Option B: Cross-instance migration
python glpi_asset_importer.py --cross-instance-migrate \
    --source-instance old_system \
    --target-instance new_system
```

### Task 4: Transform Values During Migration

```bash
# 1. Export from source
python glpi_asset_importer.py --instance old --export Computer --output export.csv

# 2. Generate mapping template
# (This is done automatically during import)

# 3. Import with value mapping
python glpi_asset_importer.py --instance new --import-migration --file export.csv
# The tool will offer to create value mapping - say 'y'
# Edit the generated mapping file
# Press Enter to continue with mapping applied
```

### Task 5: Manage Multiple Instances

```bash
# List all instances
python glpi_asset_importer.py --list-instances

# Use production
python glpi_asset_importer.py --instance production --list-types

# Use development
python glpi_asset_importer.py --instance development --list-types

# Export from production
python glpi_asset_importer.py --instance production --export Computer --output prod.csv

# Import to development
python glpi_asset_importer.py --instance development --import-migration --file prod.csv
```

## Typical Workflows

### Workflow 1: Dev → Production Deployment

```bash
# 1. Test on development
python glpi_asset_importer.py --instance dev --import Computer --file new_computers.csv

# 2. Verify
python glpi_asset_importer.py --instance dev --export Computer --output verify.csv

# 3. Deploy to production
python glpi_asset_importer.py --instance prod --import Computer --file new_computers.csv
```

### Workflow 2: System Migration

```bash
# Old system → New system
python glpi_asset_importer.py --cross-instance-migrate \
    --source-instance old_glpi \
    --target-instance new_glpi

# Follow the interactive prompts:
# 1. Select asset type (Computer)
# 2. Choose fields to export (or select all)
# 3. Apply filters if needed
# 4. Configure value mapping for field transformations
# 5. Complete migration
```

### Workflow 3: Consolidate Multiple Systems

```bash
# Export from each old system
python glpi_asset_importer.py --instance office_a --export Computer --output office_a.csv
python glpi_asset_importer.py --instance office_b --export Computer --output office_b.csv
python glpi_asset_importer.py --instance office_c --export Computer --output office_c.csv

# Import all to new system
python glpi_asset_importer.py --instance new_system --import-migration --file office_a.csv
python glpi_asset_importer.py --instance new_system --import-migration --file office_b.csv
python glpi_asset_importer.py --instance new_system --import-migration --file office_c.csv
```

## Value Mapping Example

**Scenario**: You're migrating from an old system where manufacturers are named differently.

### 1. Export from Source

```bash
python glpi_asset_importer.py --instance old --export Computer --output export.csv
```

### 2. Start Import

```bash
python glpi_asset_importer.py --instance new --import-migration --file export.csv
```

### 3. When Prompted, Enable Value Mapping

```
Do you want to apply value mapping? (y/n): y
```

### 4. Edit Generated mapping.json

```json
{
    "manufacturer_name": {
        "DELL": "Dell Inc.",
        "HP": "HP Inc.",
        "LENOVO": "Lenovo"
    },
    "type_name": {
        "DESKTOP": "Desktop",
        "LAPTOP": "Laptop"
    }
}
```

### 5. Press Enter to Continue

The import will apply your transformations automatically.

## Troubleshooting

### "Instance not found"

```bash
# Check available instances
python glpi_asset_importer.py --list-instances

# Use exact instance name
python glpi_asset_importer.py --instance production --list-types
```

### "Authentication failed"

1. Check credentials in config.json
2. Verify OAuth client in GLPI (Setup > General > OAuth Clients)
3. Ensure required scopes are enabled
4. Try with `--no-ssl-verify` for local testing

### "No fields selected"

When exporting, make sure to select at least one field:

- Press space to select/unselect
- Press 'a' to select all
- Press Enter to confirm

### Migration file not found

Ensure you specify the full path:

```bash
python glpi_asset_importer.py --import-migration --file C:\exports\computers.csv
```

## Command Reference

### Configuration

- `--init-config` - Create default config
- `--config FILE` - Use specific config file
- `--list-instances` - List all configured instances
- `--instance NAME` - Use specific instance

### Asset Management

- `--list-types` - List asset types
- `--show-fields TYPE` - Show fields for asset type
- `--generate-template TYPE` - Generate CSV template
- `--import TYPE --file FILE` - Import from CSV

### Migration

- `--export TYPE --output FILE` - Export assets
- `--export-interactive TYPE` - Interactive export with field selection
- `--import-migration --file FILE` - Import from migration export
- `--migrate-wizard` - Interactive migration wizard
- `--value-mapping FILE` - Apply value transformations

### Cross-Instance

- `--cross-instance-migrate` - Migrate between instances
- `--source-instance NAME` - Source for migration
- `--target-instance NAME` - Target for migration

### Other

- `--no-ssl-verify` - Disable SSL verification
- `--allow-duplicates` - Allow duplicate imports

## Need More Help?

- **Detailed Guides**:
    - [MULTI_INSTANCE_GUIDE.md](MULTI_INSTANCE_GUIDE.md) - Multi-instance configuration
    - [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration workflows
    - [VALUE_MAPPING_GUIDE.md](VALUE_MAPPING_GUIDE.md) - Value transformations
    - [README.md](README.md) - Full documentation

- **Examples**:
    - [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md) - Real-world migration scenarios

## Tips

1. **Always test migrations on development first**
2. **Use value mapping for field transformations**
3. **Set default_instance to your most-used instance**
4. **Keep config.json secure and out of git**
5. **Use --export-interactive for custom field selection**
6. **Export to dated files**: `backup_2024-01-15.csv`

## Version

This guide covers features in **Version 1.2+**
