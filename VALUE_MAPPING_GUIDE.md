# Value Mapping Guide

## Overview

The Value Mapping feature allows you to transform field values during migration. This is useful when:

- Manufacturer names differ between systems (e.g., "DELL" → "Dell Inc.")
- Location names need standardization (e.g., "HQ" → "Headquarters")
- State names are different (e.g., "Active" → "In use")
- User naming conventions differ (e.g., "j.smith" → "jsmith")

## Quick Start

### Step 1: Export Assets

```bash
python glpi_asset_importer.py --export Computer --output computers.csv
```

### Step 2: Create Mapping Template

```bash
python glpi_asset_importer.py --create-mapping-template \
    --file computers.csv \
    --output value_mapping.json
```

This analyzes your CSV and creates a template with all unique values found.

### Step 3: Edit Mapping File

Open `value_mapping.json` and customize the mappings:

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
        "Inactive": "Stored"
    }
}
```

### Step 4: Import with Mapping

```bash
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --value-mapping value_mapping.json \
    --auto-create-models
```

## Mapping File Format

### JSON Structure

```json
{
    "field_name": {
        "source_value": "target_value",
        "source_value2": "target_value2"
    }
}
```

### Example: Complete Mapping File

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "Hewlett-Packard",
        "LENOVO": "Lenovo Group Limited"
    },
    "models_id": {
        "Lat3490": "Latitude 3490",
        "EliteBook": "EliteBook 840 G6"
    },
    "locations_id": {
        "Office > Floor1": "Main Building > 1st Floor",
        "Office > Floor2": "Main Building > 2nd Floor"
    },
    "states_id": {
        "OK": "In use",
        "Broken": "Repair needed",
        "Storage": "Stored"
    },
    "users_id": {
        "j.smith": "jsmith",
        "m.wilson": "mwilson"
    }
}
```

## Use Cases

### Use Case 1: Standardize Manufacturer Names

**Problem**: Source system uses abbreviations, target uses full names

**Source Data**:

```csv
name,manufacturers_id
LAPTOP-001,DELL
LAPTOP-002,HP
```

**Mapping**:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "HP Inc."
    }
}
```

**Result**: Assets created with "Dell Inc." and "HP Inc." manufacturers

---

### Use Case 2: Normalize Location Names

**Problem**: Different location naming conventions

**Source Data**:

```csv
name,locations_id
DESKTOP-001,Bldg A > Fl 1
DESKTOP-002,Bldg B > Fl 2
```

**Mapping**:

```json
{
    "locations_id": {
        "Bldg A > Fl 1": "Building A > Floor 1",
        "Bldg B > Fl 2": "Building B > Floor 2"
    }
}
```

---

### Use Case 3: Map State Names

**Problem**: States named differently in source and target

**Source Data**:

```csv
name,states_id
SERVER-001,Production
SERVER-002,Development
```

**Mapping**:

```json
{
    "states_id": {
        "Production": "In production",
        "Development": "In development",
        "Testing": "In testing"
    }
}
```

---

### Use Case 4: User Login Transformation

**Problem**: Different username formats

**Source Data**:

```csv
name,users_id
LAPTOP-001,john.smith
LAPTOP-002,mary.wilson
```

**Mapping**:

```json
{
    "users_id": {
        "john.smith": "jsmith",
        "mary.wilson": "mwilson"
    }
}
```

---

### Use Case 5: Multiple Field Mappings

**Source Data**:

```csv
name,manufacturers_id,locations_id,states_id
LAPTOP-001,DELL,HQ > IT,Active
LAPTOP-002,HP,Branch > Sales,OK
```

**Mapping**:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "HP Inc."
    },
    "locations_id": {
        "HQ > IT": "Headquarters > IT Department",
        "Branch > Sales": "Branch Office > Sales Department"
    },
    "states_id": {
        "Active": "In use",
        "OK": "In use",
        "Inactive": "Stored"
    }
}
```

## Advanced Features

### Partial Mappings

You don't need to map all values. Unmapped values pass through unchanged:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc."
    }
}
```

In this case:

- "DELL" → "Dell Inc."
- "HP" → "HP" (unchanged)
- "Lenovo" → "Lenovo" (unchanged)

### Case Sensitivity

Mappings are case-sensitive. To handle variations:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "Dell": "Dell Inc.",
        "dell": "Dell Inc."
    }
}
```

### Empty/Null Values

Empty values are not mapped. To handle them, you'd need to edit the CSV directly.

## Complete Workflow Example

### 1. Export from Source System

```bash
# Export computers with key fields
python glpi_asset_importer.py --export Computer \
    --fields name,serial,manufacturers_id,models_id,locations_id,users_id \
    --output source_computers.csv
```

**Output**: `source_computers.csv`

```csv
name,serial,manufacturers_id,models_id,locations_id,users_id
LAPTOP-001,ABC123,DELL,Lat3490,HQ > IT,j.smith
LAPTOP-002,XYZ789,HP,EliteBook,Branch > Sales,m.wilson
```

### 2. Create Mapping Template

```bash
python glpi_asset_importer.py --create-mapping-template \
    --file source_computers.csv \
    --output mappings.json
```

**Output**: `mappings.json` (initial)

```json
{
    "manufacturers_id": {
        "DELL": "DELL",
        "HP": "HP"
    },
    "models_id": {
        "Lat3490": "Lat3490",
        "EliteBook": "EliteBook"
    },
    "locations_id": {
        "HQ > IT": "HQ > IT",
        "Branch > Sales": "Branch > Sales"
    },
    "users_id": {
        "j.smith": "j.smith",
        "m.wilson": "m.wilson"
    }
}
```

### 3. Customize Mappings

Edit `mappings.json`:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "Hewlett-Packard Enterprise"
    },
    "models_id": {
        "Lat3490": "Latitude 3490",
        "EliteBook": "EliteBook 840 G6"
    },
    "locations_id": {
        "HQ > IT": "Headquarters > IT Department",
        "Branch > Sales": "Regional Office > Sales Department"
    },
    "users_id": {
        "j.smith": "john.smith",
        "m.wilson": "mary.wilson"
    }
}
```

### 4. Import to Target System

```bash
# Configure config.json for target system
# Then import with value mapping
python glpi_asset_importer.py --import-migration \
    --file source_computers.csv \
    --value-mapping mappings.json \
    --auto-create-models
```

**What Happens**:

1. CSV is read
2. Values are transformed according to mapping
3. Temporary mapped CSV is created
4. Import proceeds with mapped values
5. "DELL" becomes "Dell Inc." in target system

## Command Reference

### Create Mapping Template

```bash
python glpi_asset_importer.py --create-mapping-template \
    --file <CSV_FILE> \
    --output <MAPPING_JSON>
```

**Arguments**:

- `--file`: CSV file to analyze
- `--output`: Output JSON file (default: value_mapping.json)

### Import with Value Mapping

```bash
python glpi_asset_importer.py --import-migration \
    --file <CSV_FILE> \
    --value-mapping <MAPPING_JSON> \
    [--auto-create-models]
```

**Arguments**:

- `--file`: CSV file to import
- `--value-mapping`: JSON file with value mappings
- `--auto-create-models`: Auto-create missing dropdown items

## Tips & Best Practices

### 1. Always Create Template First

Don't write mappings from scratch. Use `--create-mapping-template` to see what values exist.

### 2. Test with Small Dataset

Test your mappings with a few rows first:

```bash
# Create test CSV with first 5 rows
head -n 6 source_computers.csv > test_computers.csv

# Import test
python glpi_asset_importer.py --import-migration \
    --file test_computers.csv \
    --value-mapping mappings.json
```

### 3. Map Only What's Needed

You don't need to map every field. Focus on fields that actually differ.

### 4. Keep Original CSV

The mapping process creates temporary files. Your original CSV remains unchanged.

### 5. Version Control Mappings

Save your mapping files! They're valuable for documentation and repeatability.

### 6. Combine with Auto-Create

Use `--auto-create-models` to create items that don't exist after mapping:

```bash
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --value-mapping mappings.json \
    --auto-create-models
```

### 7. Document Your Mappings

Add comments to your mapping file (note: JSON doesn't support comments, so use a separate doc):

Create `mappings_notes.md`:

```markdown
# Mapping Notes

## Manufacturers

- DELL → Dell Inc. (company renamed)
- HP → HP Inc. (official name in target)

## Locations

- HQ → Headquarters (standardization)
```

## Troubleshooting

### Problem: Mapping Not Applied

**Check**:

1. Mapping file is valid JSON
2. Field names match exactly (case-sensitive)
3. Source values match exactly (case-sensitive)

**Test**:

```bash
# Validate JSON
python -m json.tool mappings.json
```

### Problem: Values Still Creating with Wrong Names

**Cause**: Auto-create happens before checking existing items

**Solution**: Pre-create items in target system with correct names, or fix after import

### Problem: Some Values Mapped, Others Not

**Check**: Unmapped values pass through unchanged. Add them to mapping file if needed.

### Problem: Mapping File Too Large

**Solution**: Map only values that actually differ. Skip values that are the same in both systems.

## Examples

See [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md) for complete migration examples including value mapping.

## Limitations

- Only applies to string values (not complex objects)
- Case-sensitive matching
- Cannot map empty/null values
- Applied before import (not retroactively)

## Support

For help with value mapping:

1. Use `--create-mapping-template` to see available values
2. Test with small dataset first
3. Check JSON syntax with validators
4. Review console output for mapping confirmations
