import os
import json
from datetime import datetime, timedelta
import requests

def get_credentials():
    token = None
    account_number = None
    # Adjust path to find .env in root from pruebas/
    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    if not os.path.exists(env_path):
        # Try local path if not found
        env_path = '.env'
        
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('token:'):
                    token = line.split(':', 1)[1].strip()
                elif line.startswith('account_number:'):
                    account_number = line.split(':', 1)[1].strip()
    return token, account_number

def test_location_data():
    token, account_number = get_credentials()
    if not token or not account_number:
        print("Error: No se encontraron las credenciales")
        return

    base_url = f"https://api.keepcon.com/accounts/{account_number}/content/search"
    
    now = datetime.now()
    from_date = now - timedelta(days=2) # 2 days is enough for a sample

    payload = {
        "sources": ["twitter"], # Focusing on Twitter as requested
        "created_at_from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "created_at_to": now.strftime("%Y-%m-%dT%H:%M:%S")
    }

    headers = {"Content-Type": "application/json"}
    url = f"{base_url}?access_token={token}"

    print(f"Consultando Keepcon para buscar datos de ubicación...")
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
        print("No se encontraron items.")
        return

    print(f"Analizando {len(items)} items en busca de ubicación...\n")

    found_any_location = False
    for i, item in enumerate(items[:20]): # Check first 20 items
        content = item.get("content", {})
        user = content.get("user", {})
        tags = item.get("tags", [])
        
        # Look for location in different places
        location_fields = {
            "item_location": item.get("location"),
            "content_location": content.get("location"),
            "user_location": user.get("location"),
            "user_profile_location": user.get("profile", {}).get("location"),
            "tags_location": [t for t in tags if "ubicacion" in t.lower() or "ciudad" in t.lower() or "city" in t.lower()]
        }
        
        # Also check for "extractions" or "attributes" mentioned in docs
        extractions = item.get("extractions", {})
        
        has_loc = any(location_fields.values()) or extractions
        
        if has_loc or i == 0: # Print first one anyway to see structure
            print(f"--- Item {i+1} ---")
            print(f"User: @{user.get('username')} ({user.get('name')})")
            print(f"Text: {content.get('text')[:100]}...")
            print(f"Location fields found: {json.dumps(location_fields, indent=2, ensure_ascii=False)}")
            if extractions:
                print(f"Extractions: {json.dumps(extractions, indent=2, ensure_ascii=False)}")
            
            # Print full item structure for the first one to be 100% sure
            if i == 0:
                print("\nESTRUCTURA COMPLETA DEL PRIMER ITEM (para debug):")
                # Clean up some noise if needed, but here we want to see everything
                print(json.dumps(item, indent=2, ensure_ascii=False))
                print("\n" + "="*50 + "\n")
            
            if has_loc:
                found_any_location = True

    if not found_any_location:
        print("\nNo se encontró información de ubicación (city/address) en los campos estándar de los primeros 20 tweets.")
        print("Es posible que la 'Extracción de Información' para Ciudad/Dirección no esté habilitada o configurada para esta cuenta de Keepcon.")

if __name__ == "__main__":
    test_location_data()
