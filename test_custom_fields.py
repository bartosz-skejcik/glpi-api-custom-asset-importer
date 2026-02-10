from glpi_importer.api.client import GLPIAPIClient
from glpi_importer.utils.config import load_config
import json

config_data = load_config()
config = config_data['instances']['old']
client = GLPIAPIClient(**config)
client.authenticate()

print("=== Testing search_items with custom fields ===")
# Get first Modem to see structure
modems = client.search_items('Modem', limit=1)
if modems:
    print("First Modem asset structure:")
    print(json.dumps(modems[0], indent=2))
    print("\n=== Keys in response ===")
    print(list(modems[0].keys()))

    if 'custom_fields' in modems[0]:
        print("\n=== Custom fields found! ===")
        print(json.dumps(modems[0]['custom_fields'], indent=2))
    else:
        print("\n⚠ No 'custom_fields' key in response")
