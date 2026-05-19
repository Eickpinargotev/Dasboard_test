import os
import requests
from dotenv import load_dotenv
import json

from datetime import datetime, timedelta

# Load environment variables
token = None
account_number = None

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('token:'):
            token = line.split(':', 1)[1].strip()
        elif line.startswith('account_number:'):
            account_number = line.split(':', 1)[1].strip()

# Keepcon API URL
url = f"https://api.keepcon.com/accounts/{account_number}/content/search?access_token={token}"

# Payload to search for twitter mentions
# The Keepcon API expects a date filter.
now = datetime.now()
thirty_days_ago = now - timedelta(days=30)

payload = {
    "sources": ["twitter"],
    "created_at_from": thirty_days_ago.strftime("%Y-%m-%dT%H:%M:%S"),
    "created_at_to": now.strftime("%Y-%m-%dT%H:%M:%S")
}

headers = {
    "Content-Type": "application/json"
}

def test_keepcon_api():
    print(f"Testing Keepcon API for account {account_number}...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse Data:")
            # Print only first 2 items or just a summary to avoid massive output
            if isinstance(data, list):
                 print(f"Received {len(data)} items. Showing first 2:")
                 print(json.dumps(data[:2], indent=2))
            elif isinstance(data, dict):
                 print(json.dumps(data, indent=2))
            else:
                 print(data)
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_keepcon_api()
