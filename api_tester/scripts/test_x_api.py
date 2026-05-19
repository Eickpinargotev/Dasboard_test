import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

def test_search():
    if not BEARER_TOKEN:
        print("❌ Error: X_BEARER_TOKEN no está definido en el entorno.")
        return

    print("Iniciando prueba de conexión a X API...")
    url = "https://api.twitter.com/2/tweets/search/recent"
    query = '@ClaroEcuador OR #ClaroEcuador OR "Claro Ecuador"'
    
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": 10
    }

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Conexión exitosa. Mostrando primer resultado:")
                data = response.json()
                tweets = data.get("data", [])
                if tweets:
                    print(tweets[0])
                else:
                    print("No se encontraron tweets.")
            else:
                print("❌ Error en la respuesta:")
                print(response.text)
    except Exception as e:
        print(f"❌ Excepción durante la petición: {e}")

if __name__ == "__main__":
    test_search()
