from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from uuid import uuid4
from dotenv import load_dotenv
import os
import json
import html
import jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret')
app.debug = False

# Rate limiter
# 기존 코드 (오류 발생)
# limiter = Limiter(app, key_func=get_remote_address)

# 수정된 코드
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

socketio = SocketIO(app)
online_users = set()
users = {}
LOG_FILE = 'chat_log.json'

if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        chat_history = json.load(f)
else:
    chat_history = []

def broadcast_user_list():
    nicknames = [user['nickname'] for user in users.values()]
    emit('user_list', nicknames, broadcast=True)

@socketio.on('request_chat_history')
def send_history():
    emit('chat_history', chat_history)

@app.route('/')
@limiter.limit("10 per minute")
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect(auth):
#    token = auth.get("token") if auth else None
#    try:
#        decoded = jwt.decode(token, os.getenv('JWT_SECRET', 'default_jwt_secret'), algorithms=["HS256"])
#        users[request.sid] = {
#            'id': decoded.get('user_id', str(uuid4())),
#            'nickname': decoded.get('nickname', '익명')
#        }
#        online_users.add(request.sid)
#        emit('user_count', len(online_users), broadcast=True)
#        socketio.emit('chat_history', chat_history, room=request.sid)
#        broadcast_user_list()
#    except Exception as e:
#        print("Invalid token:", e)
#        return False  # Reject connection
    user_id = str(uuid4())
    users[request.sid] = {'id': user_id, 'nickname': '익명'}
    online_users.add(request.sid)
    emit('user_count', len(online_users), broadcast=True)
    socketio.emit('chat_history', chat_history, room=request.sid)
    broadcast_user_list()


@socketio.on('set_nickname')
def set_nickname(nick):
    if request.sid in users:
        users[request.sid]['nickname'] = html.escape(nick)
        broadcast_user_list()

@socketio.on('message')
@limiter.limit("2 per second")
def handle_message(msg):
    if request.sid in users:
        nickname = html.escape(users[request.sid]['nickname'])
        msg = html.escape(msg)
        full_msg = f"{nickname}: {msg}"
        print(full_msg)
        send(full_msg, broadcast=True)
        chat_history.append(full_msg)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        print(f"User disconnected: {users[request.sid]['nickname']}")
        del users[request.sid]
    online_users.discard(request.sid)
    emit('user_count', len(online_users), broadcast=True)
    broadcast_user_list()

if __name__ == '__main__':
    import eventlet
    import eventlet.wsgi
    port = int(os.environ.get("PORT", 5000))
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port)), app)
