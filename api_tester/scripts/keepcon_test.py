import requests
import os
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Constants
BASE_URL = "https://api.keepcon.com"

# Credentials from .env
TOKEN_EMAIL = os.getenv("TOKEN")
PASSWORD_HASH = os.getenv("PASSWORD")

# Try using the password hash as the access token since that's a common pattern
# when a 32-character hash is provided
ACCESS_TOKEN = PASSWORD_HASH

def test_api_access(account_number):
    """
    Test basic API access by fetching groups for the given account number.
    """
    url = f"{BASE_URL}/accounts/{account_number}/groups"
    params = {"access_token": ACCESS_TOKEN}
    
    print(f"Testing access for account: {account_number}")
    print(f"URL: {url}")
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    try:
        print(f"Response: {response.json()}")
    except ValueError:
        print(f"Response (text): {response.text}")
        
    return response.status_code == 200

def test_search_contents(account_number):
    """
    Test the content search endpoint.
    """
    url = f"{BASE_URL}/accounts/{account_number}/content/search"
    params = {"access_token": ACCESS_TOKEN}
    
    # We can add parameters like content_types to get data from all platforms
    data = {
        "content_types": [
            "facebook: fb-comment, fb-message, fb-post",
            "twitter: retweet, tweet, direct-message, quote",
            "instagram: ig-message, ig-media, ig-comment"
        ]
    }
    
    print(f"\nTesting search for account: {account_number}")
    response = requests.post(url, params=params, json=data)
    
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except ValueError:
        print(f"Response (text): {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Keepcon API")
    parser.add_argument("--account", type=str, help="Account number to test", default=TOKEN_EMAIL.split('@')[0] if TOKEN_EMAIL else "claroec")
    args = parser.parse_args()
    
    print(f"Using Token Email: {TOKEN_EMAIL}")
    print(f"Using Access Token (Password Hash): {ACCESS_TOKEN}")
    print("-" * 40)
    
    if args.account:
        test_api_access(args.account)
        # Uncomment to test search as well
        # test_search_contents(args.account)
    else:
        print("Please provide an account number using --account")
