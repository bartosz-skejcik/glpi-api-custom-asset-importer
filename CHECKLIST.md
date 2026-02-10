# Migration Checklist

## Migration Features Added ✅

The GLPI Asset Importer now supports complete migration workflows!

### New Features

- ✅ Export assets with selected fields
- ✅ Interactive field selection
- ✅ Export filters (by location, state, etc.)
- ✅ Automatic metadata generation
- ✅ Import from migration files
- ✅ Auto-create missing dropdown items
- ✅ Migration wizard for guided process

### Quick Start Commands

#### Export Assets

```bash
# Interactive export (recommended)
python glpi_asset_importer.py --export-interactive Computer --output computers.csv

# Command-line export
python glpi_asset_importer.py --export Computer \
    --fields name,serial,users_id,locations_id \
    --output computers.csv
```

#### Import Assets

```bash
# Import with auto-create
python glpi_asset_importer.py --import-migration \
    --file computers.csv \
    --auto-create-models
```

#### Migration Wizard

```bash
python glpi_asset_importer.py --migrate-wizard
```

---

## Asset Types to Migrate

Stuff to be exported from source:

- [x] Komputery (Computers)
- [x] Laptopy (Laptops)
- [x] Monitory (Monitors)
- [x] Karty SIM (SIM Cards)
- [x] Telefony (Phones)
- [x] Kamery (Cameras)
- [x] Stacje dokujace (Docking Stations)
- [ ] Słuchawki (Headphones)
- [ ] Kartridże (Cartridges)
- [ ] UPSy (UPS)
- [ ] Zestawy klawiatura & mysz (Keyboard & Mouse Sets)
- [ ] Torby (Bags)
- [ ] Uchwyty do monitora (Monitor Mounts)
- [x] Głośniki (Speakers)
- [ ] Klawiatury (Keyboards)
- [x] Modemy (Modems)
- [x] Mysze (Mice)
- [ ] Pamięci zewnętrzne (External Storage)
- [ ] Niszczarki (Shredders)
- [ ] Skanery (Scanners)
- [ ] Tablety (Tablets)
- [x] Dyktafony (Voice Recorders)

Stuff to be imported to target:

- [x] Komputery (Computers)
- [x] Laptopy (Laptops)
- [x] Monitory (Monitors)
- [x] Karty SIM (SIM Cards)
- [x] Telefony (Phones)
- [x] Kamery (Cameras)
- [x] Stacje dokujace (Docking Stations)
- [ ] Słuchawki (Headphones)
- [ ] Kartridże (Cartridges)
- [ ] UPSy (UPS)
- [ ] Zestawy klawiatura & mysz (Keyboard & Mouse Sets)
- [ ] Torby (Bags)
- [ ] Uchwyty do monitora (Monitor Mounts)
- [x] Głośniki (Speakers)
- [ ] Klawiatury (Keyboards)
- [x] Modemy (Modems)
- [x] Mysze (Mice)
- [ ] Pamięci zewnętrzne (External Storage)
- [ ] Niszczarki (Shredders)
- [ ] Skanery (Scanners)
- [ ] Tablety (Tablets)
- [x] Dyktafony (Voice Recorders)

---

## Migration Workflow

### Phase 1: Preparation

- [ ] Backup source GLPI database
- [ ] Backup target GLPI database
- [ ] Configure OAuth on source system
- [ ] Configure OAuth on target system
- [ ] Test connection to source
- [ ] Test connection to target
- [ ] Identify custom asset definitions needed

### Phase 2: Export

- [ ] Export completed asset types (see list above)
- [ ] Verify export files
- [ ] Review metadata files
- [ ] Transfer files to target system

### Phase 3: Import

- [ ] Create custom asset definitions on target
- [ ] Import each asset type
- [ ] Verify import counts
- [ ] Spot check critical assets

### Phase 4: Validation

- [ ] Compare asset counts (source vs target)
- [ ] Verify user assignments
- [ ] Verify location assignments
- [ ] Verify manufacturer/model data
- [ ] Test asset searches
- [ ] Document any issues

### Phase 5: Cleanup

- [ ] Archive migration files
- [ ] Update documentation
- [ ] Train users on new system

---

## For Each Asset Type

Example for "Komputery" (Computers):

### 1. Export from Source

```bash
python glpi_asset_importer.py --export Computer \
    --fields name,serial,otherserial,users_id,locations_id,manufacturers_id,models_id,states_id \
    --output komputery_export.csv
```

### 2. Transfer Files

Copy both files to target:

- `komputery_export.csv`
- `komputery_export_metadata.json`

### 3. Import to Target

```bash
python glpi_asset_importer.py --import-migration \
    --file komputery_export.csv \
    --auto-create-models
```

### 4. Verify

- [ ] Check count matches source
- [ ] Spot check 5-10 random assets
- [ ] Verify critical/expensive assets

---

## Documentation

- ✅ [MIGRATION.md](MIGRATION.md) - Feature summary
- ✅ [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Complete workflow guide
- ✅ [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md) - Command examples
- ✅ [README.md](README.md) - Updated with migration features

---

## Notes

- Migration preserves asset data but not GLPI internal IDs
- Relationships are re-created based on names (auto-resolved)
- Custom asset definitions must exist on target before import
- Use `--auto-create-models` to create missing manufacturers/models
- Always keep metadata files with exports
