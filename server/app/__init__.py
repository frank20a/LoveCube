from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import os


# Get environment variables
online_flag = bool(int(os.environ.get('ONLINE') or False))
db_host = os.environ.get('DB_HOST') or 'localhost'
db_port = int(os.environ.get('DB_PORT') or 3306)
db_user = os.environ.get('DB_USER') or 'root'
db_pass = os.environ.get('DB_PASS') or 'root'
db_name = os.environ.get('USERS_DB') or 'lovecube_db'
path = '/home/frank20a/LoveCube/server' if online_flag else os.getcwd()

# Create Flask app
app = Flask(
    __name__,
    static_folder=os.path.join(path, 'static'),
    template_folder=os.path.join(path, 'templates')
)
app.config.from_object(__name__)

# Create session
SESSION_TYPE = 'redis'
Session(app)

# Create database
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
db = SQLAlchemy(app)
