from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
import os


from .session_key import SessionKey


# Get environment variables
online_flag = bool(int(os.environ.get('ONLINE') or False))
db_host = os.environ.get('DB_HOST') or 'localhost'
db_port = int(os.environ.get('DB_PORT') or 3306)
db_user = os.environ.get('DB_USER') or 'root'
db_pass = os.environ.get('DB_PASS') or 'root'
db_name = os.environ.get('DB_NAME') or 'lovecube_db'
path = '/home/frank20a/LoveCube/server' if online_flag else os.path.join(os.getcwd(), 'server')

# Create Flask app
app = Flask(
    __name__,
    static_folder=os.path.join(path, 'static'),
    template_folder=os.path.join(path, 'templates')
)

# Create session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET_KEY') if online_flag else 'tralalalala123'
Session(app)

# Create database

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
db = SQLAlchemy(app)

# Create markdown
Markdown(app)