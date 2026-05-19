import os
import json
from datetime import datetime, timedelta
import requests

def get_credentials():
    token = os.getenv("KEEPCON_TOKEN")
    account_number = os.getenv("KEEPCON_ACCOUNT_NUMBER")
    return token, account_number

def test_location_data():
    token, account_number = get_credentials()
    if not token or not account_number:
        print("Error: No se encontraron las credenciales")
        return

    base_url = f"https://api.keepcon.com/accounts/{account_number}/content/search"
    
    now = datetime.now()
    from_date = now - timedelta(days=7) # Increase to 7 days to find more samples

    payload = {
        "sources": ["twitter"],
        "content_types": ["tweet", "quote", "retweet"], # Public only
        "created_at_from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "created_at_to": now.strftime("%Y-%m-%dT%H:%M:%S")
    }

    headers = {"Content-Type": "application/json"}
    url = f"{base_url}?access_token={token}"

    print(f"Consultando Keepcon (últimos 7 días) para buscar menciones de ciudades...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return

    data = response.json()
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("items", data.get("data", data.get("results", [])))
        if not items and "0" in data:
            items = [data[k] for k in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else 9999) if k.isdigit()]

    if not items:
        print("No se encontraron items públicos.")
        return

    print(f"Analizando {len(items)} items públicos...\n")

    cities_to_find = ["Quito", "Guayaquil", "Cuenca", "Manta", "Ambato", "Loja", "Duran", "Machala", "Ecuador"]
    found_city = False
    
    for i, item in enumerate(items):
        tags = item.get("tags", [])
        
        # Check if any tag contains a city name
        city_tags = [tag for tag in tags for city in cities_to_find if city.lower() in tag.lower()]
        
        if city_tags:
            print(f"--- ¡Tag de Ciudad encontrado en Item {i+1}! ---")
            print(f"User: @{item.get('content', {}).get('user', {}).get('username')}")
            print(f"Tags detectados: {city_tags}")
            found_city = True

    if not found_city:
        print("\nNo se encontraron tags que mencionen ciudades (Quito, Guayaquil, etc.) en los resultados.")
        print("Esto confirma que Keepcon no está etiquetando geográficamente las menciones para esta cuenta.")

if __name__ == "__main__":
    test_location_data()

