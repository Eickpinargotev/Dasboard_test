import os
import json
from datetime import datetime, timedelta
from collections import Counter
import requests

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

def count_sentiments_last_4_days():
    token, account_number = get_credentials()
    if not token or not account_number:
        print("Error: No se encontraron las credenciales en .env")
        return

    base_url = f"https://api.keepcon.com/accounts/{account_number}/content/search"
    
    now = datetime.now()
    from_date = now - timedelta(days=4) 

    payload = {
        "sources": ["twitter", "facebook", "instagram"],
        "created_at_from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "created_at_to": now.strftime("%Y-%m-%dT%H:%M:%S")
    }

    headers = {
        "Content-Type": "application/json"
    }

    from collections import defaultdict
    content_type_counter = Counter()
    source_counter = Counter()
    sentiment_counter = Counter()
    content_type_sentiment = defaultdict(Counter)
    total_records = 0

    print(f"Obteniendo datos desde {from_date.strftime('%Y-%m-%d')} hasta {now.strftime('%Y-%m-%d')} para analizar sentimientos por tipo...")

    next_page_token = None
    page = 1

    while True:
        url = f"{base_url}?access_token={token}"
        if next_page_token:
            url += f"&next_page_token={next_page_token}"

        print(f"Consultando página {page}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error en la petición: {response.status_code} - {response.text}")
            break

        data = response.json()
        
        # Extraer items de la respuesta
        if isinstance(data, list):
            items = data
            next_page_token = None
        elif isinstance(data, dict):
            items = data.get("items", data.get("data", data.get("results", [])))
            next_page_token = data.get("next_page_token")
            if not items and "0" in data:
                items = [data[k] for k in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else 9999) if k.isdigit()]
        else:
            items = []

        if not items:
            break

        total_records += len(items)

        for item in items:
            c_type = item.get("content_type", "unknown")
            source = item.get("source", "unknown")
            sentiment = item.get("sentiment", "unknown_sentiment").lower()
            
            content_type_counter[c_type] += 1
            source_counter[source] += 1
            sentiment_counter[sentiment] += 1
            content_type_sentiment[c_type][sentiment] += 1

        if not next_page_token:
            break
            
        page += 1

    print("\n--- RESULTADOS ---")
    print(f"Total de registros analizados en los últimos 4 días: {total_records}")
    
    print("\nConteo por Red Social (source):")
    for source, count in source_counter.most_common():
        print(f"  - {source}: {count}")

    print("\nDesglose Detallado por Tipo de Contenido y Sentimiento:")
    for c_type, count in content_type_counter.most_common():
        print(f"\n[{c_type}] - Total: {count}")
        for sent, sent_count in content_type_sentiment[c_type].most_common():
            print(f"    - {sent}: {sent_count}")

if __name__ == "__main__":
    count_sentiments_last_4_days()
