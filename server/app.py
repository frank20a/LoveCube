from flask import jsonify, render_template, redirect, url_for, request, session
from hashlib import sha256
from app import *
from db_models import *


sessions = {}

# Create database tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run()
