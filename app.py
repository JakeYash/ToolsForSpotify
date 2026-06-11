from flask import Flask
from dotenv import load_dotenv
import os
from routes import register_routes

load_dotenv()

app = Flask(__name__)

app.config["CLIENT_ID"] = os.getenv("client_Id")
app.config["CLIENT_SECRET"] = os.getenv("client_Secret")
app.config["SECRET_KEY"] = os.getenv("server_SecretKey")
app.config["REDIRECT_URI"] = "http://127.0.0.1:5000/callback"
app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok = True)

app.secret_key = app.config["SECRET_KEY"]


register_routes(app)
