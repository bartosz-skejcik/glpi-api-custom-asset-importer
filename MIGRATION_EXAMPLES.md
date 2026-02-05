# Migration Examples

## Example 1: Simple Computer Migration

### Source System Export

```bash
# Export all computers with basic fields
python glpi_asset_importer.py --export Computer \
    --fields name,serial,otherserial,comment,locations_id,manufacturers_id,models_id,users_id \
    --output computers_export.csv
```

**Output Files:**

- `computers_export.csv`
- `computers_export_metadata.json`

**Sample Export (computers_export.csv):**

```csv
name,serial,otherserial,comment,locations_id,manufacturers_id,models_id,users_id
DESKTOP-001,ABC123,INV-001,John's desktop,10,5,8,15
LAPTOP-042,XYZ789,INV-002,Sales laptop,12,6,9,18
SERVER-DB01,SRV999,INV-003,Database server,20,5,10,20
```

**Sample Metadata (computers_export_metadata.json):**

```json
{
    "asset_type": "Computer",
    "export_date": "1675612800.0",
    "total_assets": 3,
    "fields": [
        "name",
        "serial",
        "otherserial",
        "comment",
        "locations_id",
        "manufacturers_id",
        "models_id",
        "users_id"
    ],
    "filters": {},
    "glpi_url": "http://source-glpi.example.com"
}
```

### Target System Import

```bash
# Import to target system (auto-create missing items)
python glpi_asset_importer.py --import-migration \
    --file computers_export.csv \
    --auto-create-models
```

**What Happens:**

1. Tool reads metadata to determine asset type (Computer)
2. For each row:
    - Resolves location name to target system's location ID
    - Resolves manufacturer name to target system's manufacturer ID
    - Resolves model name (creates if missing with --auto-create-models)
    - Resolves user login to target system's user ID
3. Creates asset in target system
4. Reports success/failure for each item

---

## Example 2: Interactive Export

```bash
python glpi_asset_importer.py --export-interactive Computer --output computers.csv
```

**Interactive Session:**

```
===============================================
Interactive Export: Computer
===============================================

ℹ Fetching available fields...

ℹ Available fields for Computer:
  1. id
  2. name
  3. serial
  4. otherserial
  5. comment
  6. locations_id
  7. manufacturers_id
  8. models_id
  9. states_id
  10. users_id
  11. groups_id
  12. contact
  13. contact_num

Enter field numbers to export (comma-separated), or 'all' for all fields:
> 2,3,4,6,7,8,10

ℹ Selected fields: name, serial, otherserial, locations_id, manufacturers_id, models_id, users_id

Apply filters? (y/n):
> y

ℹ Enter filters (field=value), one per line. Empty line to finish:
> states_id=1
✓ Added filter: states_id = 1
>

===============================================
Exporting Computer Assets
===============================================

ℹ Fetching Computer assets from GLPI...
✓ Found 150 assets to export
ℹ Writing to computers.csv...
✓ Exported 150 assets to computers.csv
ℹ Exported fields: name, serial, otherserial, locations_id, manufacturers_id, models_id, users_id
✓ Created metadata file: computers_metadata.json
```

---

## Example 3: Custom Asset Migration

### Export Custom Laptop Assets

```bash
python glpi_asset_importer.py --export Laptop --output laptops_export.csv
```

Assuming custom asset "Laptop" has custom fields:

- `custom_battery_capacity`
- `custom_screen_size`
- `custom_warranty_date`

**Sample Export:**

```csv
name,serial,locations_id,manufacturers_id,models_id,users_id,custom_battery_capacity,custom_screen_size,custom_warranty_date
LAPTOP-001,LP123,15,6,20,25,5200,15.6,2025-12-31
LAPTOP-002,LP456,15,6,21,26,4500,14.0,2026-01-15
```

### Import Custom Assets

```bash
# Make sure custom asset definition exists on target!
python glpi_asset_importer.py --import-migration \
    --file laptops_export.csv \
    --auto-create-models
```

---

## Example 4: Filtered Export (Specific Location)

### Export Only Assets from Building A

```bash
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=10" \
    --output building_a_export.csv
```

### Export Only Active Assets

```bash
python glpi_asset_importer.py --export Computer \
    --filters "states_id=1" \
    --output active_assets.csv
```

### Export with Multiple Filters

```bash
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=10,states_id=1" \
    --output building_a_active.csv
```

---

## Example 5: Migration Wizard

```bash
python glpi_asset_importer.py --migrate-wizard
```

**Session Example:**

```
===============================================
GLPI Migration Wizard
===============================================

ℹ This wizard will help you export assets from one GLPI system
ℹ and prepare them for import into another GLPI system.

What would you like to do?
  1. Export assets from this GLPI instance
  2. Import assets from a migration file
  3. Export and prepare for migration (full workflow)

Select option (1-3): 1

Select asset type to export:
  1. Computer
  2. Monitor
  3. NetworkEquipment
  4. Printer
  5. Laptop (Custom)

Select number: 1

Output filename (default: export.csv): my_computers.csv

[Continues with interactive export flow...]
```

---

## Example 6: Complete Migration Workflow

### Step 1: Configure Source System

Edit `config.json`:

```json
{
    "base_url": "http://source.glpi.local",
    "client_id": "source_client_id",
    "client_secret": "source_secret",
    "username": "admin",
    "password": "admin_password"
}
```

### Step 2: Export from Source

```bash
python glpi_asset_importer.py --export Computer \
    --fields name,serial,users_id,locations_id,manufacturers_id,models_id \
    --output computers_migration.csv
```

**Files Created:**

- `computers_migration.csv` (150 KB)
- `computers_migration_metadata.json` (2 KB)

### Step 3: Transfer Files

Copy both files to target system:

```bash
# Linux/Mac
scp computers_migration.* user@target-server:/path/to/target/

# Windows
# Use WinSCP, FileZilla, or manual copy
```

### Step 4: Configure Target System

Edit `config.json` on target:

```json
{
    "base_url": "http://target.glpi.local",
    "client_id": "target_client_id",
    "client_secret": "target_secret",
    "username": "admin",
    "password": "admin_password"
}
```

### Step 5: Prepare Target System

```bash
# List asset types to verify Computer exists
python glpi_asset_importer.py --list-types

# Show fields to verify structure
python glpi_asset_importer.py --show-fields Computer
```

### Step 6: Import to Target

```bash
# Import with auto-create
python glpi_asset_importer.py --import-migration \
    --file computers_migration.csv \
    --auto-create-models
```

**Expected Output:**

```
===============================================
GLPI Asset Importer
===============================================

Version 1.1
Support for GLPI v11 Custom Assets

ℹ Authenticating with GLPI API...
✓ Authentication successful!

===============================================
Importing Assets from Migration File
===============================================

ℹ Found metadata file: computers_migration_metadata.json
ℹ Using asset type from metadata: Computer
ℹ Metadata: Exported 250 assets
ℹ Source GLPI: http://source.glpi.local

===============================================
Importing 250 Computer Assets
===============================================

Processing row 1/250: DESKTOP-001
  ℹ Creating new Manufacturer: DELL
  ✓ Created new Manufacturer: DELL (ID: 15)
  ✓ Imported: DESKTOP-001 (Serial: ABC123)

Processing row 2/250: LAPTOP-042
  ✓ Imported: LAPTOP-042 (Serial: XYZ789)

...

===============================================
Import Summary
===============================================

✓ Successfully imported: 248
✗ Failed: 2
⊘ Skipped (duplicates): 0

Total processed: 250
```

### Step 7: Verify Migration

```bash
# Check counts in GLPI web interface
# Spot check critical assets
# Verify user assignments
# Verify locations
```

---

## Example 7: Value Mapping - Transform Field Values

### Problem

Source system uses "DELL", target system needs "Dell Inc."

### Step 1: Export from Source

```bash
python glpi_asset_importer.py --export Computer \
    --fields name,serial,manufacturers_id,models_id,locations_id \
    --output computers.csv
```

**Exported Data** (computers.csv):

```csv
name,serial,manufacturers_id,models_id,locations_id
LAPTOP-001,ABC123,DELL,Lat3490,HQ
LAPTOP-002,XYZ789,HP,EliteBook,Branch
```

### Step 2: Create Mapping Template

```bash
python glpi_asset_importer.py --create-mapping-template \
    --file computers.csv \
    --output value_mapping.json
```

**Initial Template** (value_mapping.json):

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
        "HQ": "HQ",
        "Branch": "Branch"
    }
}
```

### Step 3: Customize Mappings

Edit value_mapping.json:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Inc.",
        "HP": "HP Inc."
    },
    "models_id": {
        "Lat3490": "Latitude 3490",
        "EliteBook": "EliteBook 840 G6"
    },
    "locations_id": {
        "HQ": "Headquarters",
        "Branch": "Branch Office"
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

**Console Output**:

```
===============================================
Importing Assets from Migration File
===============================================

ℹ Found metadata file: computers_metadata.json
ℹ Using asset type from metadata: Computer
ℹ Applying value mapping...
ℹ   Mapped manufacturers_id: 'DELL' → 'Dell Inc.'
ℹ   Mapped manufacturers_id: 'HP' → 'HP Inc.'
ℹ   Mapped models_id: 'Lat3490' → 'Latitude 3490'
ℹ   Mapped models_id: 'EliteBook' → 'EliteBook 840 G6'
ℹ   Mapped locations_id: 'HQ' → 'Headquarters'
ℹ   Mapped locations_id: 'Branch' → 'Branch Office'
✓ Applied 6 value mappings, saved to: computers_value_mapped.csv

===============================================
Importing 2 Computer Assets
===============================================

Processing row 1/2: LAPTOP-001
  ✓ Imported: LAPTOP-001 (Serial: ABC123)

Processing row 2/2: LAPTOP-002
  ✓ Imported: LAPTOP-002 (Serial: XYZ789)

===============================================
Import Summary
===============================================

✓ Successfully imported: 2
✗ Failed: 0
⊘ Skipped (duplicates): 0

Total processed: 2
```

**Result**: Assets created with "Dell Inc." and "HP Inc." instead of "DELL" and "HP"

---

## Example 8: Complex Multi-Field Value Mapping

### Scenario

Migrating from old system with inconsistent naming to standardized target system.

### Source Data (inconsistent.csv)

```csv
name,serial,manufacturers_id,locations_id,states_id,users_id
SRV-001,S123,DELL,DC > R1,Prod,j.smith
SRV-002,S456,HP,DC > R2,Dev,m.wilson
WS-001,W789,LENOVO,Office > IT,OK,admin
```

### Step 1: Export & Create Template

```bash
python glpi_asset_importer.py --create-mapping-template \
    --file inconsistent.csv \
    --output mappings.json
```

### Step 2: Create Comprehensive Mapping

Edit mappings.json:

```json
{
    "manufacturers_id": {
        "DELL": "Dell Technologies",
        "HP": "Hewlett-Packard Enterprise",
        "LENOVO": "Lenovo Group Limited"
    },
    "locations_id": {
        "DC > R1": "Data Center > Rack 1",
        "DC > R2": "Data Center > Rack 2",
        "Office > IT": "Main Office > IT Department"
    },
    "states_id": {
        "Prod": "In production",
        "Dev": "In development",
        "OK": "In use"
    },
    "users_id": {
        "j.smith": "john.smith",
        "m.wilson": "mary.wilson",
        "admin": "administrator"
    }
}
```

### Step 3: Import with Mappings

```bash
python glpi_asset_importer.py --import-migration \
    --file inconsistent.csv \
    --value-mapping mappings.json \
    --auto-create-models
```

### Result

All values transformed to target system's naming conventions:

- Manufacturers: Full company names
- Locations: Standardized hierarchical paths
- States: Consistent state names
- Users: Standardized usernames

---

## Tips & Tricks

### Export Only Recent Assets

```bash
# If your GLPI has a date field
python glpi_asset_importer.py --export Computer \
    --filters "date_creation>=2024-01-01" \
    --output recent_computers.csv
```

### Export Minimal Data for Testing

```bash
# Just name and serial for quick test
python glpi_asset_importer.py --export Computer \
    --fields name,serial \
    --filters "states_id=1" \
    --output test_export.csv
```

### Dry Run (Preview)

```bash
# Export a small sample first
python glpi_asset_importer.py --export Computer \
    --filters "id<=10" \
    --output sample.csv

# Review sample.csv
# Then do full export
```

### Handle Large Datasets

```bash
# For very large migrations, split by location:

# Export Building A
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=10" \
    --output building_a.csv

# Export Building B
python glpi_asset_importer.py --export Computer \
    --filters "locations_id=11" \
    --output building_b.csv

# Import separately
python glpi_asset_importer.py --import-migration --file building_a.csv
python glpi_asset_importer.py --import-migration --file building_b.csv
```

---

## Common Issues & Solutions

### Issue: Export Returns Empty

**Cause:** No assets match the filters
**Solution:** Check filters, try without filters first

### Issue: Import Creates Duplicates

**Cause:** Duplicate detection based on serial number
**Solution:** Ensure serial numbers are unique or use `--allow-duplicates`

### Issue: Custom Fields Not Imported

**Cause:** Custom asset definition missing on target
**Solution:** Create custom asset definition on target first, ensure field names match

### Issue: Users Not Found

**Cause:** User accounts don't exist on target
**Solution:** Create users first, or exclude users_id from export, or use --auto-create (not recommended for users)

---

## Performance Tips

1. **Large exports:** Use filters to split into smaller batches
2. **Network latency:** Export locally, transfer files, import locally
3. **Auto-create:** Creates items one-by-one, can be slow for many new items
4. **Pre-create dropdowns:** Create manufacturers, models, etc. before import for better performance
