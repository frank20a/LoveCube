from flask import jsonify, render_template, redirect, url_for, request, session
from random import randint
from uuid import uuid4
from hashlib import sha256
from app import *
from db_models import *


DEBUG = not online_flag
sessions = {}
CMD_OPTIONS = [
    'None',
    'Rainbow',
    'Pulse Red',
    'Pulse Green',
    'Pulse Blue',
    'Pulse Yellow',
    'Pulse Cyan',
    'Pulse Magenta',
    'Pulse White',
]
CMD_OPTIONS_REVERSE = {o: i for i, o in enumerate(CMD_OPTIONS)}


def gen_hash(password, salt, username):
    return sha256((password + salt + username).encode('utf-8')).hexdigest()


def _login(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return 1
    
    user_key = AuthKey.query.filter_by(user=user.id, is_user_key=True).first()
    
    if user.hash == gen_hash(password, user.salt, user.username):
        session['session_key'] = str(uuid4())
        sessions[session['session_key']] = SessionKey(user.id, user.name, user.email, user_key.key)
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
    
    personal_key = AuthKey()
    personal_key.key = str(uuid4())
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


def device_availability_from_last_ping(last_ping: datetime) -> int:
    if last_ping + timedelta(minutes=1) < datetime.utcnow():
        return 1
    elif last_ping + timedelta(hours=1) < datetime.utcnow():
        return 2
    return 0


def fix_key(key: str) -> str:
    if '-' not in key:
        return ('-'.join([key[:8], key[8:12], key[12:16], key[16:20], key[20:]])).lower()
    return key.lower()


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

@app.route('/getting-started')
def getting_started():
    if check_session():
        return redirect(url_for('getting_started'))
    
    with open(os.path.join(path, 'static', 'markdown', 'getting_started.md'), 'r') as f:
        return render_template(
            'markdown_page.html',
            session=sessions[session['session_key']] if check_session() else None,
            debug=DEBUG,
            mkd=f.read()
        )

@app.route('/devices', methods=['GET', 'POST'])
def devices():
    if not check_session():
        return redirect(url_for('login', next='devices'))
    
    if request.method == 'GET':
        devices = Device.query.filter_by(owner=sessions[session['session_key']].user).all()
        _pairs = Pair.query.filter_by(user=sessions[session['session_key']].user, approved=True).all()
        pairs = [Device.query.filter_by(id=_pair.device).first() for _pair in _pairs]
        pair_owners = {pair.id: User.query.filter_by(id=pair.owner).first().username for pair in pairs}
        
        if len(devices) == 0:
            return redirect(url_for('authkeys', error=5))
        else:
            return render_template(
                'devices.html',
                session=sessions[session['session_key']],
                error=request.args.get('error', 0, int),
                debug=DEBUG,
                devices=devices,
                devices_cmd_expired=[device.cmd_exp < datetime.utcnow() for device in devices],
                devices_availability=[device_availability_from_last_ping(device.last_ping) for device in devices],
                pairs=pairs,
                pair_owners=pair_owners,
                cmd_options=CMD_OPTIONS
            )
    
    if request.method == 'POST':
        _device = Device.query.filter_by(id=request.form['device_id']).first()
        
        if _device is None:
            return redirect(url_for('devices', error=6))
        if _device.owner != sessions[session['session_key']].user:
            return redirect(url_for('devices', error=7))
        
        if len(request.form['nickname']) > 0:
            _device.nickname = request.form['nickname']
        if 'btn1_action_target' in request.form:
            _device.btn1_action = f"{request.form['btn1_action_target']}_{request.form['btn1_action_cmd']}_{request.form['btn1_action_time']}"
            _device.btn2_action = f"{request.form['btn2_action_target']}_{request.form['btn2_action_cmd']}_{request.form['btn2_action_time']}"
        
        db.session.commit()
        return redirect(url_for('devices'))

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
        error=request.args.get('error', 0, int),
        debug=DEBUG,
        authkeys=authkeys,
        devices=devices
    )

@app.route('/pairs', methods=['GET', 'POST'])
def pairs():
    if not check_session():
        return redirect(url_for('login', next='pairs'))
    
    if request.method == 'GET':
        devices_ = [d.id for d in Device.query.filter_by(owner=sessions[session['session_key']].user).all()]
        return render_template(
            'pairs.html',
            session=sessions[session['session_key']],
            error=request.args.get('error', 0, int),
            debug=DEBUG,
            pairs=[
                {
                    'id': pair.id,
                    'device': Device.query.filter_by(id=pair.device).first(),
                    'approved': pair.approved
                } for pair in Pair.query.filter_by(user=sessions[session['session_key']].user).all()
            ],
            requests=[
                {
                    'id': pair.id,
                    'user': User.query.filter_by(id=pair.user).first().username,
                    'device': Device.query.filter_by(id=pair.device).first(),
                    'created': pair.created.strftime('%d/%m/%Y'),
                    'approved': pair.approved
                } for pair in Pair.query.filter(Pair.device.in_(devices_)).all()
            ]
        )
        
    if request.method == 'POST':
        if request.form['operation'] == 'request':
            device_ = Device.query.filter_by(id=request.form['device_id']).first()
            if device_ is None:
                return redirect(url_for('pairs', error=8))
            if device_.owner == sessions[session['session_key']].user:
                return redirect(url_for('pairs', error=12))
            
            request_ = Pair.query.filter_by(device=request.form['device_id']).first()
            if request_ is not None and request_.approved:
                return redirect(url_for('pairs', error=9))
            
            request_ = Pair()
            request_.user = sessions[session['session_key']].user
            request_.device = request.form['device_id']
            db.session.add(request_)
            db.session.commit()

        elif request.form['operation'] == 'delete':
            request_ = Pair.query.filter_by(id=request.form['pair_id']).first()
            if request_ is None:
                return redirect(url_for('pairs', error=10))
            
            if request_.user != sessions[session['session_key']].user:
                device_ = Device.query.filter_by(id=request_.device).first()
                if device_.owner != sessions[session['session_key']].user:
                    return redirect(url_for('pairs', error=11))
            
            db.session.delete(request_)
            db.session.commit()
        
            return redirect(url_for('pairs'))
        
        elif request.form['operation'] == 'accept':
            request_ = Pair.query.filter_by(id=request.form['pair_id']).first()
            if request_ is None:
                return redirect(url_for('pairs', error=10))
            
            device_ = Device.query.filter_by(id=request_.device).first()
            if device_.owner != sessions[session['session_key']].user:
                return redirect(url_for('pairs', error=11))
                
            request_.approved = True
            db.session.commit()
        
        else:
            return redirect(url_for('pairs', error=13))
            
        return redirect(url_for('pairs'))


# API
@app.route('/api/v1/get-cmd/<api_key>/<device_id>', methods=['GET'])
def get_cmd(api_key: str, device_id: str):
    api_key = fix_key(api_key)
    device_id = device_id.lower()
    
    resp = {'error': 0}
    
    key_ = AuthKey.query.filter_by(key=api_key).first()
    device_ = Device.query.filter_by(id=device_id).first()
    
    if key_ is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif device_ is None:
        resp['error'] = 2
        resp['error_msg'] = 'Invalid device ID'
    elif key_.device != device_.id and not key_.is_user_key:
        resp['error'] = 3
        resp['error_msg'] = 'API key is not for this device'
    elif key_.is_user_key and key_.user != device_.owner:
        resp['error'] = 4
        resp['error_msg'] = 'API key is user key (master) but device is not register to this user'
    else:
        resp['cmd'] = device_.cmd if device_.cmd_exp > datetime.utcnow() else 0
        
    if device_ is not None:
        device_.last_ping = datetime.utcnow()
    db.session.commit()
    
    return jsonify(resp)

@app.route('/api/v1/trigger/<api_key>/<device_id>/<int:btn>', methods=['GET'])
def trigger(api_key: str, device_id: str, btn: int):
    api_key = fix_key(api_key)
    device_id = device_id.lower()
    
    resp = {'error': 0}
    
    key_ = AuthKey.query.filter_by(key=api_key).first()
    device_ = Device.query.filter_by(id=device_id).first()
    
    if key_ is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif device_ is None:
        resp['error'] = 2
        resp['error_msg'] = 'Invalid device ID'
    elif key_.device != device_.id and not key_.is_user_key:
        resp['error'] = 3
        resp['error_msg'] = 'API key is not for this device'
    elif key_.is_user_key and key_.user != device_.owner:
        resp['error'] = 4
        resp['error_msg'] = 'API key is user key (master) but device is not register to this user'
    elif btn not in [1, 2]:
        resp['error'] = 5
        resp['error_msg'] = 'Invalid button number'
    else:
        cmd = (device_.btn1_action if btn == 1 else device_.btn2_action).split('_')
        target_device_ = Device.query.filter_by(id=cmd[0]).first()
        
        if target_device_ is None:
            resp['error'] = 6
            resp['error_msg'] = 'Invalid target device'
        elif target_device_.id not in [pair.device for pair in Pair.query.filter_by(user=device_.owner, approved=True).all()]:
            resp['error'] = 7
            resp['error_msg'] = 'Target device is not paired'
        else:
            target_device_.cmd = int(cmd[1])
            target_device_.cmd_exp = datetime.utcnow() + timedelta(minutes=int(cmd[2]))
    
    if device_ is not None:
        device_.last_ping = datetime.utcnow()
    db.session.commit()
        
    return jsonify(resp)

@app.route('/api/v1/state/<api_key>/<device_id>', methods=['PUT'])
def state(api_key: str, device_id: str):
    api_key = fix_key(api_key)
    device_id = device_id.lower()
    
    resp = {'error': 0}
    
    key_ = AuthKey.query.filter_by(key=api_key).first()
    device_ = Device.query.filter_by(id=device_id).first()
    
    if key_ is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif device_ is None:
        resp['error'] = 2
        resp['error_msg'] = 'Invalid device ID'
    elif key_.device != device_.id:
        resp['error'] = 3
        resp['error_msg'] = 'API key is not for this device'
    else:
        device_.bat_chrg_flag = request.json['chrg_flag']
        device_.bat_stby_flag = request.json['stby_flag']
        
    if device_ is not None:
        device_.last_ping = datetime.utcnow()
    db.session.commit()
    
    return jsonify(resp)

@app.route('/api/v1/register-api-key/<api_key>/<device_id>', methods=['GET'])
def register_api_key(api_key: str, device_id: str):
    api_key = fix_key(api_key)
    device_id = device_id.lower()
    
    resp = {'error': 0}
    
    device = Device.query.filter_by(id=device_id).first()
    user_key = AuthKey.query.filter_by(key=api_key).first()
    if user_key is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif not user_key.is_user_key:
        resp['error'] = 2
        resp['error_msg'] = 'API key is not a user key'
    elif device is not None and device.owner != user_key.user:
        if device.last_ping + timedelta(days=365) < datetime.utcnow():
            device.owner = user_key.user
            db.session.commit()
            
            keys_ = AuthKey.query.filter_by(device=device_id).all()
            for key_ in keys_:
                db.session.delete(key_)
            db.session.commit()
            
            new_key = AuthKey()
            new_key.user = user_key.user
            new_key.device = device_id
            new_key.key = str(uuid4())
            db.session.add(new_key)
            db.session.commit()
            resp['key'] = new_key.key
        else:
            resp['error'] = 3
            resp['error_msg'] = 'Device already registered to user'
    else:
        if device is None:
            device = Device()
            device.id = device_id
            device.owner = user_key.user
            db.session.add(device)
            db.session.commit()
        
        new_key = AuthKey()
        new_key.user = user_key.user
        new_key.device = device_id
        new_key.key = str(uuid4())
        db.session.add(new_key)
        db.session.commit()
        resp['key'] = new_key.key
    
    return jsonify(resp)

@app.route('/api/v1/unregister-api-key/<user_api_key>/<target_api_key>', methods=['GET'])
def unregister_api_key(user_api_key: str, target_api_key):
    user_api_key = fix_key(user_api_key)
    target_api_key = fix_key(target_api_key)
    
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
    api_key = fix_key(api_key)
    
    res = {'error': 0}
    return jsonify(res)

@app.route('/api/v1/unregister-device/<api_key>/<device_id>', methods=['GET'])
def unregister_device(api_key: str, device_id: str):
    api_key = fix_key(api_key)
    device_id = device_id.lower()
    
    resp = {'error': 0}
    
    _api_key = AuthKey.query.filter_by(key=api_key).first()
    _device = Device.query.filter_by(id=device_id).first()
    
    if _api_key is None:
        resp['error'] = 1
        resp['error_msg'] = 'Invalid API key'
    elif _device is None:
        resp['error'] = 2
        resp['error_msg'] = 'Invalid device ID'
    elif not _api_key.is_user_key:
        resp['error'] = 3
        resp['error_msg'] = 'API key is not user key'
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
    if online_flag:
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run()
