import os
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from config import settings
from logger import log

app = FastAPI()

@app.get("/")
def home():
    # Upstox Login URL format
    login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={settings.UPSTOX_API_KEY}&redirect_uri={settings.UPSTOX_REDIRECT_URI}"
    
    html_content = f"""
    <html>
        <head>
            <title>Upstox OAuth Login</title>
            <style>
                body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #121212; color: white; }}
                .container {{ text-align: center; padding: 40px; background-color: #1e1e1e; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
                .btn {{ display: inline-block; padding: 15px 30px; margin-top: 20px; font-size: 18px; color: white; background-color: #00b852; text-decoration: none; border-radius: 5px; }}
                .btn:hover {{ background-color: #009643; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>AlgoTrade AI</h2>
                <p>Click below to authorize your Upstox Developer App for Historical Data access.</p>
                <a href="{login_url}" class="btn">Login with Upstox</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/callback")
def callback(code: str = None, error: str = None):
    if error:
        log.error(f"OAuth Error: {error}")
        return {"error": error}
    if not code:
        return {"error": "No code provided in the callback"}
        
    url = "https://api.upstox.com/v2/login/authorization/token"
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'code': code,
        'client_id': settings.UPSTOX_API_KEY,
        'client_secret': settings.UPSTOX_API_SECRET,
        'redirect_uri': settings.UPSTOX_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }

    log.info("Attempting to exchange auth code for access token...")
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        # Security: Save token locally. (Added to .gitignore conceptually)
        with open("upstox_token.txt", "w") as f:
            f.write(access_token)
            
        log.info("Access token acquired and saved to upstox_token.txt")
        return HTMLResponse("""
            <h2 style='color: green; text-align: center; margin-top: 50px;'>Successfully Authenticated!</h2>
            <p style='text-align: center;'>The access token has been securely saved locally. You may close this window and run the Upstox Fetcher script.</p>
        """)
    else:
        log.error(f"Failed to fetch token: {response.text}")
        return {"error": "Failed to fetch access token", "details": response.json()}

if __name__ == "__main__":
    log.info(f"Starting Upstox OAuth server on {settings.UPSTOX_REDIRECT_URI}")
    uvicorn.run("auth:app", host="127.0.0.1", port=8000, reload=True)
