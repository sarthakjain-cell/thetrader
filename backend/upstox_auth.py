import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")

def get_login_url():
    if not API_KEY or not REDIRECT_URI:
        print("Error: UPSTOX_API_KEY or UPSTOX_REDIRECT_URI missing in .env")
        return None
        
    url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    return url

def fetch_access_token(auth_code):
    url = "https://api.upstox.com/v2/login/authorization/token"
    headers = {
        'accept': 'application/json',
        'Api-Version': '2.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'code': auth_code,
        'client_id': API_KEY,
        'client_secret': API_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        json_resp = response.json()
        print("\n✅ Successfully retrieved access token!")
        # Usually tokens are valid for the day, save to a secure file.
        with open("upstox_token.txt", "w") as f:
            f.write(json_resp.get("access_token"))
        print("Token saved to upstox_token.txt")
        return json_resp
    else:
        print("\n❌ Failed to retrieve access token.")
        print(response.text)
        return None

if __name__ == "__main__":
    print("--- Upstox OAuth 2.0 Flow ---")
    print("1. Click the following URL to log in and authorize the app:")
    print(get_login_url())
    print("\n2. After authorizing, you will be redirected to your REDIRECT_URI.")
    print("   Look at the URL in your browser, it will look like:")
    print("   https://127.0.0.1:8000/auth?code=XXXXXXX")
    
    auth_code = input("\n3. Paste the 'code' from the URL here: ").strip()
    
    if auth_code:
        fetch_access_token(auth_code)
    else:
        print("Authorization code is required.")
