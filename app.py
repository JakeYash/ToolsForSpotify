from flask import Flask, render_template, session, request, redirect
from dotenv import load_dotenv
import os
import secrets
import urllib.parse
import requests
import base64
import time

load_dotenv()

client_id = os.getenv("client_Id")
client_secret = os.getenv("client_Secret")
server_secretkey = os.getenv("server_SecretKey")
redirect_uri = "http://127.0.0.1:5000/callback"


app = Flask(__name__)

app.secret_key = server_secretkey

# def refresh():


@app.route('/')
def index():
    return render_template('mainpage.html')

@app.route('/login')
def login():
    state = secrets.token_urlsafe(16)
    session["state"] = state
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state
    }
    
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(url)


@app.route

@app.route("/callback")
def callback():
    # occurs after putting in codes for token
    saved_state = session.get("state")

    if not saved_state:
        return "Missing session state (start login again)", 400

    state = request.args.get("state")
    if state != saved_state:
        return "Invalid state", 403

    code = request.args.get("code")
    
    auth_options = {
        "url": "https://accounts.spotify.com/api/token",
        "data": {
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        },
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode() #encode into bytes, then b64, then decode into string
        }
    }

    response = requests.post(
        auth_options["url"],
        data = auth_options["data"],
        headers = auth_options["headers"]
    )

    # store expire time, refresh token, access token, etc
    if response.status_code != 200:
        return "Token request failed", 400
    token_data = response.json()
    if "access_token" not in token_data:
        return "Invalid token response", 400

    session["access_token"] = token_data["access_token"]
    session["refresh_token"] = token_data.get("refresh_token")
    session["expires_at"] = time.time() + token_data["expires_in"]

    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    access = session.get("access_token")
    if not access:
        return "Missing access token (start login again)", 400

    return render_template('dashboard.html')
