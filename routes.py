import urllib.parse
import requests
import base64
import time
import io
import zipfile
from flask import Flask, render_template, session, request, redirect, send_file
import secrets
from helpers import refresh, retrieve_set_from_cache, insert_files_into_cache
from redis_client import r
import re

def register_routes(app):    

    client_id = app.config["CLIENT_ID"]
    client_secret = app.config["CLIENT_SECRET"]
    redirect_uri = app.config["REDIRECT_URI"]
    upload_folder = app.config["UPLOAD_FOLDER"]

    @app.route("/upload", methods=["POST"])
    def upload():
        access = session.get("access_token")
        if not access:
            return "Missing access token (start login again)", 400
        if (session.get("expires_at") < time.time()):
            refresh()
        
        access_token = session.get("access_token")
        response = requests.get(
            "https://api.spotify.com/v1/me/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        call_result = response.json()
        account_id = call_result["account_id"]
        session["account_id"] = account_id

        files = request.files.getlist('files')
                # redis only stores strings/bytes, need to make set into list to make json serializable
        # then can store, but will have to unserialize and then setify whenever retrieving
        
        insert_files_into_cache(files,account_id)
        

        session["uploaded"] = True
        return '', 200


    @app.route("/download")
    def download():
        access = session.get("access_token")
        if not access:
            return "Missing access token (start login again)", 400
        
        if not (session.get("uploaded")):
            return "Need upload for download", 400

        if (session.get("expires_at") < time.time()):
            refresh()
       
        access_token = session.get("access_token")
        response = requests.get(
            "https://api.spotify.com/v1/me/albums?limit=50&offset=0",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        call_result = response.json()
        total = int(call_result["total"])
    
        buf = io.BytesIO()
    
        account_id = session["account_id"]
        track_set = retrieve_set_from_cache(account_id)

        with zipfile.ZipFile(buf,'w') as zf:
            # make this go for multiple pages, nest it with while(true) and have block that requests again if call_result[next] exists
            # and redefines call_result
            
            if (total > 0):
                items = call_result["items"]
                for item in items:
                    print(item["album"]["name"])
                for item in items:
                    url = item["album"]["images"][0]["url"]
                    trackList = item["album"]["tracks"]["items"]
                    flag = True
                    for track in trackList: 
                        if(track["id"] in track_set): 
                            continue 
                        else: 
                            flag = False 
                            break

                    if (flag):
                        response = requests.get(url)
                        response.raise_for_status()
                        album_name = re.sub(r'[/*]', '_', item["album"]["name"])
                        zf.writestr(f"{album_name}.jpg", response.content)
                        # also add album to list of albums to remove later
 
        #write helper function that removes albums based on list (in batches of 40), and call it after all this with list of albums
    
        buf.seek(0) #rewinds buffer to start so returns properly
        return send_file(buf,as_attachment=True,download_name='albums.zip',mimetype='application/zip')
    
    
    @app.route('/done')
    def done():
        return render_template('donepage.html')
    
    
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
            "state": state,
            "scope": "user-library-read"
        }
        
        url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
        return redirect(url)
    
       
    
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
    
        return redirect("/ask")
    
    @app.route("/ask")
    def ask():
        access = session.get("access_token")
        if not access:
            return "Missing access token (start login again)", 400
        
        return render_template('ask_for_upload.html')


    @app.route("/dashboard")
    def dashboard():
        access = session.get("access_token")
        uploaded = session.get("uploaded")
        if not access:
            return "Missing access token (start login again)", 400
        if not uploaded:
            return "Missing file upload", 400

        return render_template('dashboard.html')


