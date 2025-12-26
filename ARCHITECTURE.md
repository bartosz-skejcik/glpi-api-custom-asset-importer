# GLPI Asset Importer - Architecture

## Overview

The GLPI Asset Importer has been refactored from a monolithic 1,015-line script into a well-organized, modular Python package with clear separation of concerns.

## Package Structure

```
glpi_importer/
├── api/                    # API Client Layer
│   ├── client.py          # GLPI API client (447 lines)
│   └── __init__.py        # API module exports
├── importer/              # Business Logic Layer
│   ├── asset_importer.py  # Asset import logic (362 lines)
│   └── __init__.py        # Importer module exports
├── utils/                 # Utilities Layer
│   ├── console.py         # Terminal output formatting (41 lines)
│   ├── config.py          # Configuration management (35 lines)
│   └── __init__.py        # Utils module exports
├── cli.py                 # CLI Interface (143 lines)
└── __init__.py           # Package root
```

## Module Responsibilities

### 1. API Layer (`glpi_importer/api/`)

**Purpose**: Handle all direct communication with the GLPI API

**Components**:
- `GLPIAPIClient`: Main API client class
  - OAuth2 authentication with token management
  - Token expiry tracking and auto-renewal
  - HTTP request handling with proper headers
  - Asset CRUD operations
  - Dropdown resolution (locations, users, manufacturers, etc.)
  - Schema introspection via OpenAPI
  - Custom asset detection

**Key Features**:
- Automatic re-authentication on token expiry
- Support for custom asset endpoints
- Smart dropdown resolution (hierarchical locations, user logins)
- Comprehensive error handling

### 2. Business Logic Layer (`glpi_importer/importer/`)

**Purpose**: Implement import logic and data transformation

**Components**:
- `AssetImporter`: Main importer class
  - CSV template generation with custom fields
  - CSV file parsing and validation
  - Field value resolution (names → IDs)
  - Data transformation for GLPI API format
  - Duplicate detection
  - Batch import with progress tracking
  - Asset type listing and field inspection

**Key Features**:
- Smart field resolution (supports both names and IDs)
- Custom field extraction and nesting
- Transform `*_id` fields to GLPI object format
- Comprehensive import statistics

### 3. Utilities Layer (`glpi_importer/utils/`)

**Purpose**: Provide reusable utility functions

**Components**:
- `console.py`: Terminal output formatting
  - Color-coded messages (success, error, warning, info)
  - Styled headers
  - ANSI color codes
  
- `config.py`: Configuration file management
  - Load/save configuration
  - Default config generation
  - JSON serialization

### 4. CLI Layer (`glpi_importer/cli.py`)

**Purpose**: Command-line interface and argument parsing

**Features**:
- Argument parsing with argparse
- Command routing
- Error handling and user feedback
- Banner display

### 5. Entry Point (`glpi_asset_importer.py`)

**Purpose**: Thin wrapper to launch the CLI

**Size**: 13 lines (minimal, as it should be)

## Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- API layer: API communication only
- Business logic: Import workflow and transformations
- Utils: Reusable helpers
- CLI: User interface

### 2. Dependency Flow
```
CLI → AssetImporter → GLPIAPIClient → GLPI API
 ↓         ↓
Utils     Utils
```

No circular dependencies; clean unidirectional flow.

### 3. Modularity
- Each class is self-contained
- Functions are small and focused
- Easy to test individual components
- Simple to extend with new features

### 4. Maintainability
- Clear file organization
- Logical module grouping
- Well-documented code
- Type hints where appropriate

## Key Improvements Over Original

### Before (Monolithic)
- ❌ Single 1,015-line file
- ❌ Mixed concerns (API, UI, logic)
- ❌ Difficult to test
- ❌ Hard to navigate
- ❌ Challenging to extend

### After (Modular)
- ✅ 9 focused modules
- ✅ Clear separation of concerns
- ✅ Easy to test individual components
- ✅ Simple navigation with IDE support
- ✅ Easy to extend (e.g., add new importers)
- ✅ Proper Python package structure
- ✅ Reusable components

## Code Statistics

| Component | Lines | Purpose |
|-----------|-------|---------|
| `api/client.py` | 447 | GLPI API client |
| `importer/asset_importer.py` | 362 | Import logic |
| `cli.py` | 143 | CLI interface |
| `utils/console.py` | 41 | Terminal output |
| `utils/config.py` | 35 | Configuration |
| `__init__.py` files | 27 | Module exports |
| Entry point | 13 | Script launcher |
| **Total** | **1,068** | **Complete package** |

Original monolithic: 1,015 lines

**Result**: Better organized with only 53 additional lines for modularity (5% overhead for massive maintainability gain)

## Usage Patterns

### As a CLI Tool
```bash
python glpi_asset_importer.py --list-types
```

### As a Python Package
```python
from glpi_importer import GLPIAPIClient, AssetImporter

client = GLPIAPIClient(base_url, client_id, client_secret, username, password)
client.authenticate()

importer = AssetImporter(client)
importer.import_from_csv('Laptop', 'laptops.csv')
```

### Extending the Package
```python
from glpi_importer.api import GLPIAPIClient

# Create a custom importer
class CustomImporter:
    def __init__(self, client: GLPIAPIClient):
        self.client = client
    
    def import_from_excel(self, asset_type, excel_file):
        # Your custom logic here
        pass
```

## Future Extension Points

The modular architecture makes it easy to add:
- ✨ Excel file support (new importer class)
- ✨ Export functionality (new module)
- ✨ Web UI (new frontend using the API layer)
- ✨ Scheduled imports (new scheduler module)
- ✨ Custom validation rules (extend AssetImporter)
- ✨ Multiple output formats (extend utils)
- ✨ Plugin system (new plugins directory)

## Testing Strategy

With this architecture, testing becomes straightforward:

```python
# Mock the API client
mock_client = Mock(spec=GLPIAPIClient)
importer = AssetImporter(mock_client)

# Test import logic without hitting real API
stats = importer.import_from_csv('Computer', 'test.csv')
assert stats['success'] == 5
```

## Conclusion

The refactored architecture provides:
- **Maintainability**: Easy to understand and modify
- **Testability**: Components can be tested in isolation
- **Extensibility**: Simple to add new features
- **Reusability**: Components can be used independently
- **Professionalism**: Follows Python best practices

This is production-ready code that can scale with your needs.
