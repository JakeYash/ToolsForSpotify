import base64
import time
import requests

def refresh():
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return "Missing refresh token", 400

    auth_options = {
        "url" : "https://accounts.spotify.com/api/token",
        "data" : {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        },
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        }
    }

    response = requests.post(
            auth_options["url"],
            data = auth_options["data"],
            headers = auth_options["headers"]
        )

    if response.status_code != 200:
        return "Token refresh failed", 400

    token_data = response.json()
    session["access_token"] = token_data["access_token"]
    session["refresh_token"] = token_data.get("refresh_token", refresh_token)
    session["expires_at"] = time.time() + token_data["expires_in"]


