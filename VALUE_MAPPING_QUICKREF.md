# Value Mapping Quick Reference

## What is Value Mapping?

Transform field values during migration. Example: "DELL" → "Dell Inc."

## Quick Commands

### 1. Create Mapping Template

```bash
python glpi_asset_importer.py --create-mapping-template \
    --file export.csv \
    --output mappings.json
```

### 2. Edit Mapping File

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "HP Inc."
    },
    "locations_id": {
        "HQ": "Headquarters"
    }
}
```

### 3. Import with Mapping

```bash
python glpi_asset_importer.py --import-migration \
    --file export.csv \
    --value-mapping mappings.json \
    --auto-create-models
```

## Mapping File Format

```json
{
    "field_name": {
        "source_value": "target_value",
        "another_source": "another_target"
    }
}
```

## Common Use Cases

### Manufacturer Names

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "Hewlett-Packard",
        "LENOVO": "Lenovo Group"
    }
}
```

### Location Standardization

```json
{
    "locations_id": {
        "HQ > IT": "Headquarters > IT Department",
        "Branch": "Branch Office"
    }
}
```

### State Names

```json
{
    "states_id": {
        "Active": "In use",
        "OK": "In use",
        "Broken": "Needs repair"
    }
}
```

### User Logins

```json
{
    "users_id": {
        "j.smith": "john.smith",
        "m.wilson": "mary.wilson"
    }
}
```

## Full Workflow Example

```bash
# 1. Export from source
python glpi_asset_importer.py --export Computer --output computers.csv

# 2. Create mapping template
python glpi_asset_importer.py --create-mapping-template \
    --file computers.csv --output mappings.json

# 3. Edit mappings.json with your transformations

# 4. Import to target with mappings
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --value-mapping mappings.json \
    --auto-create-models
```

## Tips

✅ **Always create template first** - Don't write from scratch
✅ **Test with small dataset** - Verify mappings work correctly
✅ **Map only what differs** - Unmapped values pass through unchanged
✅ **Case sensitive** - "DELL" ≠ "dell" ≠ "Dell"
✅ **Keep mapping files** - Great for documentation

## What Gets Mapped?

- ✅ String values in specified fields
- ✅ Dropdown references (manufacturers, locations, etc.)
- ❌ Numeric IDs (they're already IDs)
- ❌ Empty/null values

## Complete Documentation

See [VALUE_MAPPING_GUIDE.md](VALUE_MAPPING_GUIDE.md) for complete guide.
