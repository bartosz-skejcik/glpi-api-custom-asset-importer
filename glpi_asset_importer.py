#!/usr/bin/env python3
"""
GLPI Asset Importer - Entry point script.

A tool to import assets from CSV files into GLPI using the API.
Supports GLPI v11 custom asset definitions.
"""

import sys
from glpi_importer.cli import main

if __name__ == '__main__':
    sys.exit(main())
