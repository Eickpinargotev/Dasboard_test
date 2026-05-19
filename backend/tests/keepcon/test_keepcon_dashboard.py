import os
import json
import csv
from datetime import datetime, timedelta
import requests

# Archivo para guardar los IDs ya procesados
PROCESSED_IDS_FILE = "processed_ids.csv"

def load_processed_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return {row[0] for row in reader if row}

def save_processed_ids(new_ids):
    if not new_ids:
        return
    file_exists = os.path.exists(PROCESSED_IDS_FILE)
    with open(PROCESSED_IDS_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for item_id in new_ids:
            writer.writerow([item_id])

def get_credentials():
    token = None
    account_number = None
    with open('../.env', 'r') as f:
        for line in f:
            if line.startswith('token:'):
                token = line.split(':', 1)[1].strip()
            elif line.startswith('account_number:'):
                account_number = line.split(':', 1)[1].strip()
    return token, account_number

def fetch_and_filter_mentions():
    token, account_number = get_credentials()
    if not token or not account_number:
        print("Error: No se encontraron las credenciales en .env")
        return

    url = f"https://api.keepcon.com/accounts/{account_number}/content/search?access_token={token}"

    now = datetime.now()
    # Simular ejecución buscando los últimos 30 días para obtener datos, 
    # pero en producción con cron de 1 min, esto sería: now - timedelta(minutes=5)
    from_date = now - timedelta(days=30) 

    # Excluir direct-message, fb-message e ig-message
    allowed_content_types = [
        "tweet", "retweet", "quote", 
        "fb-comment", "fb-post", 
        "ig-comment", "ig-media", "ig-image", "ig-story"
    ]

    payload = {
        "sources": ["twitter", "facebook", "instagram"],
        "content_types": allowed_content_types,
        "created_at_from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "created_at_to": now.strftime("%Y-%m-%dT%H:%M:%S")
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("Haciendo petición a Keepcon API...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Error en la petición: {response.status_code} - {response.text}")
        return

    data = response.json()
    if not isinstance(data, list):
        # A veces puede devolver un dict con "items" o similar, la docu muestra una lista o next_page_token
        # Asumiendo que data es una lista de diccionarios si es una respuesta directa
        if "items" in data:
            data = data["items"]
        elif not isinstance(data, list):
            data = [data] # Fallback
            
    processed_ids = load_processed_ids()
    new_ids = set()
    filtered_results = []

    print(f"Se obtuvieron {len(data)} registros de la API.")

    for item in data:
        # Extraer campos de manera segura
        item_id = item.get("id")
        if not item_id or item_id in processed_ids:
            continue # Ya procesado o inválido

        content = item.get("content", {})
        text = content.get("text", "") or ""
        sentiment = item.get("sentiment", "").lower()
        
        # Filtro: Contiene @ClaroEcua (case-insensitive)
        if "@claroecua" not in text.lower():
            continue
            
        # Filtro: Sentimiento negativo
        if sentiment != "negative":
            continue

        # Si pasa los filtros, extraer información relevante para el Dashboard
        dashboard_data = {
            "id": item_id,
            "source": item.get("source"),
            "content_type": item.get("content_type"),
            "text": text,
            "created_at": content.get("createdat"),
            "url": content.get("url"),
            "username": content.get("user", {}).get("username"),
            "user_name": content.get("user", {}).get("name"),
            "sentiment": sentiment,
            "tags": item.get("tags", [])
        }
        
        filtered_results.append(dashboard_data)
        new_ids.add(item_id)

    # Guardar los nuevos IDs
    save_processed_ids(new_ids)

    print(f"Se encontraron {len(filtered_results)} nuevos registros que cumplen los criterios.")
    if filtered_results:
        print("\nEjemplo del primer registro filtrado listo para el Dashboard:")
        print(json.dumps(filtered_results[0], indent=2, ensure_ascii=False))
        
        # Opcional: Guardar los resultados en un JSON para revisar
        with open('latest_dashboard_data.json', 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=2, ensure_ascii=False)
        print("\nDatos guardados en 'latest_dashboard_data.json'")

if __name__ == "__main__":
    fetch_and_filter_mentions()
