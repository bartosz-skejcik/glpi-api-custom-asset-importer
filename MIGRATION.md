# Migration Feature Summary

## Overview

The GLPI Asset Importer now includes comprehensive migration capabilities to help you export assets from one GLPI system and import them into another.

## Key Features

### 1. Export Assets

- ✅ Export any asset type (standard or custom)
- ✅ Select specific fields to export
- ✅ Filter assets by criteria (location, state, etc.)
- ✅ Automatic metadata generation
- ✅ Interactive field selection wizard

### 2. Import Assets

- ✅ Import from exported CSV files
- ✅ Automatic asset type detection from metadata
- ✅ Smart name-to-ID resolution
- ✅ Auto-create missing dropdown items (optional)
- ✅ Duplicate detection

### 3. Migration Workflow

- ✅ Interactive migration wizard
- ✅ Complete export → transfer → import workflow
- ✅ Metadata tracking
- ✅ Progress monitoring

## Quick Commands

### Export

```bash
# Interactive export with field selection
python glpi_asset_importer.py --export-interactive Computer --output computers.csv

# Command-line export with specific fields
python glpi_asset_importer.py --export Computer \
    --fields name,serial,users_id,locations_id \
    --output computers.csv

# Export with filters
python glpi_asset_importer.py --export Computer \
    --filters "states_id=1,locations_id=10" \
    --output filtered_computers.csv
```

### Import

```bash
# Import with auto-create
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --auto-create-models

# Import with metadata auto-detection
python glpi_asset_importer.py --import-migration --file export.csv
```

### Migration Wizard

```bash
# Interactive guided migration
python glpi_asset_importer.py --migrate-wizard
```

## Architecture

### New Files

- **glpi_importer/importer/migration.py** - MigrationManager class
    - `export_assets()` - Export assets to CSV
    - `interactive_export()` - Interactive export wizard
    - `import_from_migration()` - Import from migration file
    - `migrate_wizard()` - Interactive migration wizard

### Enhanced Files

- **glpi_importer/api/client.py** - Added `search_items()` method
- **glpi_importer/cli.py** - Added migration command-line arguments

## How It Works

### Export Process

1. Connect to source GLPI system
2. Query assets with optional filters
3. Extract selected fields
4. Write to CSV file
5. Generate metadata JSON file

### Import Process

1. Read CSV and metadata files
2. Connect to target GLPI system
3. For each asset:
    - Resolve dropdown names to target system IDs
    - Auto-create missing items (if enabled)
    - Create asset
4. Report results

## Name Resolution

The migration feature automatically resolves these fields by name:

- **locations_id** - Location paths (e.g., "Building > Floor > Room")
- **manufacturers_id** - Manufacturer names (e.g., "DELL")
- **models_id** - Model names (e.g., "Latitude 3490")
- **states_id** - State names (e.g., "In use")
- **users_id** - User login names (e.g., "jsmith")
- **groups_id** - Group names (e.g., "IT Department")

This means IDs from the source system are automatically mapped to the target system's IDs.

## Metadata Files

Every export creates two files:

1. **{filename}.csv** - The actual data
2. **{filename}\_metadata.json** - Migration metadata

### Metadata Contents

```json
{
  "asset_type": "Computer",
  "export_date": "timestamp",
  "total_assets": 250,
  "fields": ["name", "serial", "users_id", ...],
  "filters": {"states_id": 1},
  "glpi_url": "http://source-glpi.example.com"
}
```

Benefits:

- Asset type auto-detection during import
- Audit trail of migration source
- Field documentation
- Filter documentation

## Use Cases

### 1. System Upgrade

Migrate assets from old GLPI to new GLPI version:

```bash
# Old system
python glpi_asset_importer.py --export Computer --output computers.csv

# New system
python glpi_asset_importer.py --import-migration --file computers.csv
```

### 2. Data Consolidation

Merge multiple GLPI instances:

```bash
# System A
python glpi_asset_importer.py --export Computer --output system_a.csv

# System B
python glpi_asset_importer.py --export Computer --output system_b.csv

# Target system
python glpi_asset_importer.py --import-migration --file system_a.csv
python glpi_asset_importer.py --import-migration --file system_b.csv
```

### 3. Environment Migration

Move from dev to production:

```bash
# Dev
python glpi_asset_importer.py --export Laptop \
    --filters "states_id=1" \
    --output approved_laptops.csv

# Production
python glpi_asset_importer.py --import-migration --file approved_laptops.csv
```

### 4. Partial Migration

Migrate specific departments or locations:

```bash
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=10" \
    --output building_a.csv
```

## CLI Reference

### Export Arguments

```
--export ASSET_TYPE          Export assets for migration
--export-interactive TYPE    Interactive export with field selection
--fields FIELD_LIST          Comma-separated fields to export
--filters FILTER_LIST        Comma-separated filters (field=value)
--output FILE                Output file (default: template.csv)
```

### Import Arguments

```
--import-migration           Import from migration export file
--file CSV_FILE              CSV file to import
--auto-create-models         Auto-create missing dropdown items
--allow-duplicates           Allow importing duplicates
```

### Wizard

```
--migrate-wizard             Interactive migration wizard
```

## Examples

See [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md) for detailed examples.

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for complete migration workflow.

## Limitations

### What Can Be Migrated

- ✅ Asset basic information
- ✅ Standard fields
- ✅ Custom fields (if asset definition exists)
- ✅ Dropdown relationships (auto-resolved)

### What Cannot Be Migrated

- ❌ Internal GLPI IDs (regenerated in target)
- ❌ Tickets, changes, problems
- ❌ Historical data
- ❌ Files and documents
- ❌ Complex relationships (components, software, etc.)
- ❌ Financial information

## Best Practices

1. **Always test first** - Use a small subset
2. **Keep metadata** - Don't lose the JSON file
3. **Backup databases** - Before importing
4. **Verify exports** - Review CSV in Excel
5. **Use auto-create carefully** - Review what gets created
6. **Document process** - Note manual steps
7. **Validate results** - Spot check critical assets

## Troubleshooting

### Export Issues

- **No data**: Check filters, verify asset type exists
- **Missing fields**: Field doesn't exist for asset type

### Import Issues

- **Duplicate errors**: Adjust duplicate detection or use `--allow-duplicates`
- **Dropdown not found**: Use `--auto-create-models` or create manually
- **User not found**: Create users first or exclude users_id field
- **Custom asset not found**: Create asset definition on target first

## Performance

### Export Performance

- Exports are paginated (100 items per request)
- Large exports automatically handle pagination
- Filters reduce export size and time

### Import Performance

- Imports process one item at a time
- Auto-create makes additional API calls
- Pre-creating dropdowns improves speed
- Batch imports are sequential

### Recommendations

- For >1000 assets: Split by location/department
- Pre-create manufacturers, models, locations
- Use filters to export only needed data
- Import during low-usage periods

## Security Considerations

- Migration files may contain sensitive data
- Secure file transfers (SCP, SFTP, encrypted storage)
- Delete migration files after completion
- Review auto-created items for validity
- Verify user assignments after migration
- Audit migration results

## Future Enhancements

Potential future features:

- Field mapping configuration
- Batch parallel imports
- Relationship migration (components, software)
- Financial data migration
- Incremental sync
- Rollback capability
- Migration validation reports

## Support

For help:

1. Read [README.md](README.md)
2. Check [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
3. Review [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md)
4. Check error messages in console
5. Verify GLPI API documentation

## Version

Migration features added in **Version 1.1**
