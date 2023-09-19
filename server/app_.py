from flask import jsonify, render_template, redirect, url_for, request, session
from random import randint
from uuid import uuid4
from hashlib import sha256
from app import *
from db_models import *


def gen_hash(password, salt, username):
    return sha256((password + salt + username).encode('utf-8')).hexdigest()


def _login(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return 1
    
    if user.hash == gen_hash(password, user.salt, user.username):
        session['session_key'] = str(uuid4())
        sessions[session['session_key']] = SessionKey(user.id, user.name, user.email)
        return 0
    
    return 2


def _register(username, password, name, email):
    _user = User.query.filter_by(username=username).first()
    if _user is not None:
        return 3
    
    _user = User.query.filter_by(email=email).first()
    if _user is not None:
        return 4
    
    user = User()
    user.username = username
    user.name = name
    user.email = email
    user.salt = ''.join([chr(randint(33, 125)) for _ in range(16)])
    user.hash = gen_hash(password, user.salt, user.username)
    
    db.session.add(user)
    db.session.commit()
    
    return _login(username, password)


def check_session() -> bool:
    if 'session_key' not in session:
        return False
    session_key = session['session_key']
    
    if session_key not in sessions:
        return False
    
    if sessions[session_key].expiry < datetime.utcnow():
        sessions.pop(session_key)
        return False
    
    return True


sessions = {}

# Create database tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template(
        'index.html',
        session=sessions[session['session_key']] if check_session() else None,
        debug=False
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if check_session():
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template(
            'login.html',
            session=None,
            error=request.args.get('error', 0, int),
            debug=False
        )
    
    if request.method == 'POST':
        code = _login(request.form['username'], request.form['password'])
        return redirect(url_for('index')) if not code else redirect(url_for('login', error=code))
        

@app.route('/register', methods=['GET', 'POST'])
def register():
    if check_session():
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template(
            'register.html',
            session=None,
            error=request.args.get('error', 0, int),
            debug=False
        )
        
    if request.method == 'POST':
        code = _register(request.form['username'], request.form['password'], request.form['name'], request.form['email'])
        return redirect(url_for('index')) if not code else redirect(url_for('register', error=code))


@app.route('/logout')
def logout():
    session.pop('session_key', None)
    return redirect(url_for('index'))


@app.route('/api/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run()
