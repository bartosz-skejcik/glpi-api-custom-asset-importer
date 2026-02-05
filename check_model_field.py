from glpi_importer.api.client import GLPIAPIClient
from glpi_importer.utils.config import load_config
import json
import requests

config_data = load_config()
config = config_data['instances']['new']
client = GLPIAPIClient(**config)
client.authenticate()

# Get Modem fields
fields = client.get_asset_fields('Modem')

print("=== Model Field Schema ===")
if 'model' in fields:
    print(json.dumps(fields['model'], indent=2))

print("\n=== Testing different endpoints ===")
endpoints_to_try = [
    "/CustomAssets/ModemModel",
    "/Assets/ModemModel",
    "/Dropdowns/ModemModel",
    "/Assets/Custom/ModemModel",
]

print("\n=== List all ModemModels ===")
url = f"{client.api_url}/Assets/Custom/ModemModel"
params = {"limit": 50}
try:
    response = requests.get(url, headers=client._get_headers(
    ), params=params, verify=client.verify_ssl, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 206]:
        data = response.json()
        print(f"Found {len(data)} models:")
        for model in data:
            print(f"  ID: {model.get('id')}, Name: {model.get('name')}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Test filter without quotes ===")
params = {"filter": "name==E3372 (LTE USB Stick)", "limit": 1}
try:
    response = requests.get(url, headers=client._get_headers(
    ), params=params, verify=client.verify_ssl, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 206]:
        data = response.json()
        print(f"Data: {json.dumps(data, indent=2)}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
