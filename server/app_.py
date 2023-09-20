from flask import jsonify, render_template, redirect, url_for, request, session
from random import randint
from uuid import uuid4
from hashlib import sha256
from app import *
from db_models import *


DEBUG = not online_flag
sessions = {}


def gen_hash(password, salt, username):
    return sha256((password + salt + username).encode('utf-8')).hexdigest()


def _login(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return 1
    
    if user.hash == gen_hash(password, user.salt, user.username):
        session['session_key'] = str(uuid4())
        sessions[session['session_key']] = SessionKey(user.id, user.name, user.email, user.personal_key)
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
    user.personal_key = str(uuid4())
    user.salt = ''.join([chr(randint(33, 125)) for _ in range(16)])
    user.hash = gen_hash(password, user.salt, user.username)
    db.session.add(user)
    db.session.commit()
    
    personal_key = AuthKey()
    personal_key.key = user.personal_key
    personal_key.user = user.id
    personal_key.is_user_key = True
    db.session.add(personal_key)
    
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


# Create database tables
with app.app_context():
    db.create_all()


# Pages
@app.route('/')
def index():
    return render_template(
        'index.html',
        session=sessions[session['session_key']] if check_session() else None,
        debug=DEBUG
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
            debug=DEBUG
        )
    
    if request.method == 'POST':
        code = _login(request.form['username'], request.form['password'])
        return redirect(url_for(request.form.get('next', 'index', str))) if not code else redirect(url_for('login', error=code))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if check_session():
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template(
            'register.html',
            session=None,
            error=request.args.get('error', 0, int),
            debug=DEBUG
        )
        
    if request.method == 'POST':
        code = _register(request.form['username'], request.form['password'], request.form['name'], request.form['email'])
        return redirect(url_for('index')) if not code else redirect(url_for('register', error=code))

@app.route('/logout')
def logout():
    session.pop('session_key', None)
    return redirect(url_for('index'))

@app.route('/devices')
def devices():
    if not check_session():
        return redirect(url_for('login'))
    
    devices = Device.query.filter_by(owner=sessions[session['session_key']].id).all()
    return render_template(
        'devices.html',
        session=sessions[session['session_key']],
        debug=DEBUG,
        devices=devices
    )

@app.route('/authkeys')
def authkeys():
    if not check_session():
        return redirect(url_for('login', next='authkeys'))
    
    authkeys = AuthKey.query.filter_by(user=sessions[session['session_key']].user).all()
    authkeys.sort(key=lambda x: x.created)
    
    devices = Device.query.filter_by(owner=sessions[session['session_key']].user).all()
    return render_template(
        'authkeys.html',
        session=sessions[session['session_key']],
        debug=DEBUG,
        authkeys=authkeys
    )



# API
# TODO: Implement
@app.route('/api/v1/get-cmd/<api_key>/<device_id>', methods=['GET'])
def get_cmd(api_key: str, device_id: str):
    return jsonify({
        'error': 0,
        'cmd': 0,
        'cmd_exp': False
    })

# TODO: Implement
@app.route('/api/v1/trigger/<api_key>/<device_id>/<int:btn>', methods=['GET'])
def trigger(api_key: str, device_id: str, btn: int):
    return jsonify({
        'error': 0,
    })

# TODO: Implement
@app.route('/api/v1/change-action/<api_key>/<device_id>/<int:btn>/<action>', methods=['GET'])
def change_action(api_key: str, device_id: str, btn: int, action: str):
    resp = {'error': 0}
    
    if 0 > btn > 2: # Invalid button number
        resp['error'] = 1
        resp['error_msg'] = 'Invalid button number'
    
    return jsonify(resp)

# TODO: Implement
@app.route('/api/v1/state/<api_key>/<device_id>', methods=['PUT'])
def state(api_key: str, device_id: str):
    return jsonify({
        'error': 0
    })

@app.route('/api/v1/register-api-key/<api_key>/<device_id>', methods=['GET'])
def register_api_key(api_key: str, device_id: str):
    resp = {'error': 0}
    
    user_key = AuthKey.query.filter_by(key=api_key).first()
    if user_key is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif not user_key.is_user_key:
        resp['error'] = 2
        resp['error_msg'] = 'API key is not a user key'
    else:
        new_key = AuthKey()
        new_key.user = user_key.user
        new_key.key = str(uuid4())
        db.session.add(new_key)
        db.session.commit()
        resp['key'] = new_key.key
    
    return jsonify(resp)

@app.route('/api/v1/unregister-api-key/<user_api_key>/<target_api_key>', methods=['GET'])
def unregister_api_key(user_api_key: str, target_api_key):
    resp = {'error': 0}
    
    user_key = AuthKey.query.filter_by(key=user_api_key).first()
    target_key = AuthKey.query.filter_by(key=target_api_key).first()
    
    if user_key is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif not user_key.is_user_key:
        resp['error'] = 2
        resp = 'API key is not a user key'
    elif target_key is None:
        resp['error'] = 3
        resp['error_msg'] = 'Target API key does not exist'
    elif target_key.is_user_key:
        resp['error'] = 4
        resp['error_msg'] = 'Cannot unregister a user key'
    elif target_key.user != user_key.user:
        resp['error'] = 5
        resp['error_msg'] = 'User does not own target API key'
    else:
        db.session.delete(target_key)
        db.session.commit()
    
    return jsonify(resp)

# TODO: Implement
@app.route('/api/v1/get-user-info/<api_key>', methods=['GET'])
def get_user_info(api_key: str):
    pass

@app.route('/api/v1/register-device/<api_key>/<int:user_id>/<device_id>', methods=['GET'])
def register_device(api_key: str, user_id: int, device_id: str):
    resp = {'error': 0}
    
    _api_key = AuthKey.query.filter_by(key=api_key).first()
    _user = User.query.filter_by(id=user_id).first()
    
    if _api_key is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    if _user is None:
        resp['error'] = 2
        resp['error_msg'] = 'Invalid user ID'
    elif _api_key.device != device_id:
        resp['error'] = 3
        resp['error_msg'] = 'API key does not match device'
    elif user_id != _api_key.user:
        resp['error'] = 4
        resp['error_msg'] = 'User ID does not match API key'
    else:
        device = Device()
        device.id = device_id
        device.owner = user_id
        db.session.add(device)
        db.session.commit()
    
    return jsonify(resp)

@app.route('/api/v1/unregister-device/<api_key>/<device_id>', methods=['GET'])
def unregister_device(api_key: str, device_id: str):
    resp = {'error': 0}
    
    _api_key = AuthKey.query.filter_by(key=api_key).first()
    _device = Device.query.filter_by(id=device_id).first()
    
    if _api_key is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif _device is None:
        resp['error'] = 2
        resp['error_msg'] = 'Invalid device ID'
    elif _api_key.device != device_id:
        resp['error'] = 3
        resp['error_msg'] = 'API key does not match device'
    elif _device.owner != _api_key.user:
        resp['error'] = 4
        resp['error_msg'] = 'User does not own device'
    else:
        _device_auth_keys = AuthKey.query.filter_by(device=device_id).all()
        for _device_auth_key in _device_auth_keys:
            db.session.delete(_device_auth_key)
        db.session.delete(_device)
        db.session.commit()
        
    return jsonify(resp)
        

if __name__ == '__main__':
    app.run()
