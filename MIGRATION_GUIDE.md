# GLPI Migration Guide

This guide explains how to use the GLPI Asset Importer to migrate assets from one GLPI system to another.

## Overview

The migration feature allows you to:

1. **Export** assets from a source GLPI system with selected fields
2. **Transfer** the exported data to a target system
3. **Import** the assets into the target GLPI system

The tool automatically handles:

- Name-to-ID resolution (locations, manufacturers, models, users, etc.)
- Missing dropdown items creation (optional)
- Duplicate detection
- Custom asset types and custom fields

## Quick Start

### Using the Migration Wizard (Recommended)

The easiest way to migrate is using the interactive wizard:

```bash
python glpi_asset_importer.py --migrate-wizard
```

Follow the on-screen prompts to complete your migration.

## Manual Migration Process

### Step 1: Export from Source System

#### Option A: Interactive Export (Recommended)

```bash
# 1. Configure for source system
# Edit config.json with source GLPI credentials

# 2. Run interactive export
python glpi_asset_importer.py --export-interactive Computer --output computers_export.csv

# 3. Select fields when prompted
# Example: 1,2,3,5,6,7 (name, serial, otherserial, locations_id, manufacturers_id, users_id)

# 4. Add filters if needed (optional)
# Example: states_id=1
```

#### Option B: Command-line Export

```bash
# Export specific fields
python glpi_asset_importer.py --export Computer \
    --fields name,serial,otherserial,locations_id,manufacturers_id,models_id,states_id,users_id \
    --output computers_export.csv

# Export with filters
python glpi_asset_importer.py --export Computer \
    --fields name,serial,users_id,locations_id \
    --filters "states_id=1,locations_id=10" \
    --output active_computers.csv

# Export all fields
python glpi_asset_importer.py --export Computer --output all_computers.csv
```

**Files Created:**

- `computers_export.csv` - The actual data
- `computers_export_metadata.json` - Metadata about the export

### Step 2: Transfer Files

Copy both files to your target system:

- `computers_export.csv`
- `computers_export_metadata.json`

### Step 3: Prepare Target System

Before importing:

1. **Configure OAuth Client** on target GLPI
2. **Update config.json** with target GLPI credentials
3. **Verify Asset Types** exist on target (for custom assets)
4. **Create Required Dropdowns** (optional - or use auto-create)

### Step 4: Import into Target System

```bash
# Basic import (with metadata)
python glpi_asset_importer.py --import-migration --file computers_export.csv

# Auto-create missing items
python glpi_asset_importer.py --import-migration \
    --file computers_export.csv \
    --auto-create-models
```

## Common Migration Scenarios

### Scenario 1: Migrate All Computers with Minimal Fields

```bash
# Source system
python glpi_asset_importer.py --export Computer \
    --fields name,serial,users_id,locations_id \
    --output computers_minimal.csv

# Target system
python glpi_asset_importer.py --import-migration \
    --file computers_minimal.csv \
    --auto-create-models
```

### Scenario 2: Migrate Only Active Assets

```bash
# Source system - export only "In Use" assets
python glpi_asset_importer.py --export Computer \
    --filters "states_id=1" \
    --output active_computers.csv

# Target system
python glpi_asset_importer.py --import-migration \
    --file active_computers.csv \
    --auto-create-models
```

### Scenario 3: Migrate Custom Assets with Custom Fields

```bash
# Source system - custom asset type "Laptop"
python glpi_asset_importer.py --export-interactive Laptop \
    --output laptops_export.csv

# Select all standard and custom fields when prompted

# Target system
# First ensure custom asset definition exists on target
python glpi_asset_importer.py --import-migration \
    --file laptops_export.csv \
    --auto-create-models
```

### Scenario 4: Migrate from Specific Location

```bash
# Source system - export only assets from location ID 5
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=5" \
    --output building_a_computers.csv

# Target system
python glpi_asset_importer.py --import-migration \
    --file building_a_computers.csv \
    --auto-create-models
```

## Field Mapping

### Standard Fields

These fields are automatically resolved by name:

| Field              | Resolution Method       | Example                           |
| ------------------ | ----------------------- | --------------------------------- |
| `locations_id`     | Hierarchical path or ID | "Building A > Floor 2 > Room 201" |
| `manufacturers_id` | Manufacturer name or ID | "DELL"                            |
| `models_id`        | Model name or ID        | "Latitude 3490"                   |
| `states_id`        | State name or ID        | "In use"                          |
| `users_id`         | Username or ID          | "jsmith"                          |
| `groups_id`        | Group name or ID        | "IT Department"                   |

### Custom Fields

Custom fields are exported and imported as-is. Make sure:

1. Custom asset definition exists on target
2. Custom field definitions match between source and target
3. Field names are identical

## Troubleshooting

### Problem: Metadata file not found

**Solution**: Make sure both CSV and metadata JSON files are transferred together. If metadata is missing, specify the asset type manually:

```bash
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --import Computer
```

### Problem: Import fails - dropdown items not found

**Solution**: Use `--auto-create-models` to automatically create missing items:

```bash
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --auto-create-models
```

Or manually create the required dropdown items on the target system first.

### Problem: Custom asset type not found

**Solution**: Create the custom asset definition on the target system first:

1. Go to Setup > Assets > Asset definitions
2. Create a definition matching the source system
3. Ensure field names match

### Problem: User not found

**Solution**: Either:

1. Create users on target system first
2. Use `--auto-create-models` (may create invalid users)
3. Export without `users_id` field and assign manually later

### Problem: Duplicates detected

**Solution**: The tool skips duplicates by default (based on serial number). To allow duplicates:

```bash
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --allow-duplicates
```

## Best Practices

### Before Migration

1. ✅ **Backup** both source and target databases
2. ✅ **Test** with a small subset first (5-10 items)
3. ✅ **Document** custom fields and their meanings
4. ✅ **Verify** OAuth clients on both systems
5. ✅ **Plan** which fields to migrate

### During Migration

1. ✅ **Export metadata** - always keep the JSON file
2. ✅ **Validate exports** - open CSV in Excel/LibreOffice to verify
3. ✅ **Monitor progress** - watch console output for errors
4. ✅ **Start small** - migrate one asset type at a time

### After Migration

1. ✅ **Verify counts** - compare source vs target asset counts
2. ✅ **Spot check** - manually verify critical assets
3. ✅ **Check relationships** - verify users, locations are correct
4. ✅ **Update documentation** - note any manual adjustments needed

## Migration Checklist

### Pre-Migration

- [ ] Backup source GLPI database
- [ ] Backup target GLPI database
- [ ] Create OAuth client on source system
- [ ] Create OAuth client on target system
- [ ] Configure config.json for source
- [ ] Test source connection
- [ ] Configure config.json for target
- [ ] Test target connection
- [ ] Identify asset types to migrate
- [ ] Identify required fields
- [ ] Plan for custom asset definitions
- [ ] Plan for dropdown items (manufacturers, models, etc.)

### During Migration

- [ ] Export test subset (5-10 items)
- [ ] Import test subset to target
- [ ] Verify test import
- [ ] Export full data set
- [ ] Validate exported CSV
- [ ] Transfer files to target system
- [ ] Import to target system
- [ ] Monitor for errors

### Post-Migration

- [ ] Verify asset counts match
- [ ] Spot check critical assets
- [ ] Verify user assignments
- [ ] Verify location assignments
- [ ] Verify custom fields
- [ ] Document any issues
- [ ] Update target system if needed
- [ ] Archive migration files

## Advanced Topics

### Field Mapping Between Systems

If field names differ between systems, you can manually edit the CSV headers before import. The metadata file helps document the original field names.

### Batch Migration

To migrate multiple asset types:

```bash
# Export each type
python glpi_asset_importer.py --export Computer --output computers.csv
python glpi_asset_importer.py --export Monitor --output monitors.csv
python glpi_asset_importer.py --export Printer --output printers.csv

# Import each type
python glpi_asset_importer.py --import-migration --file computers.csv --auto-create-models
python glpi_asset_importer.py --import-migration --file monitors.csv --auto-create-models
python glpi_asset_importer.py --import-migration --file printers.csv --auto-create-models
```

### Incremental Migration

To migrate in stages:

```bash
# Day 1: Export department A
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=10" \
    --output dept_a_computers.csv

# Day 2: Export department B
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=11" \
    --output dept_b_computers.csv

# Import separately
python glpi_asset_importer.py --import-migration --file dept_a_computers.csv
python glpi_asset_importer.py --import-migration --file dept_b_computers.csv
```

## Support

For issues or questions:

1. Check the main [README.md](README.md)
2. Review GLPI API documentation
3. Check migration logs for specific errors
4. Verify both systems are compatible GLPI versions

## Tips for Success

1. **Always use metadata files** - they contain critical context
2. **Test extensively** - don't migrate production data without testing
3. **Use auto-create carefully** - review what gets created
4. **Keep backups** - always have a rollback plan
5. **Document everything** - note decisions and manual changes
6. **Validate thoroughly** - check critical assets after migration
