from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from uuid import uuid4
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
online_users = set()
users = {}
chat_history = []

def broadcast_user_list():
    nicknames = [user['nickname'] for user in users.values()]
    emit('user_list', nicknames, broadcast=True)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    user_id = str(uuid4())
    users[request.sid] = {'id': user_id, 'nickname': '익명'}
    online_users.add(request.sid)
    print(f'User connected: {user_id}')
    emit('user_count', len(online_users), broadcast=True)
    emit('chat_history', chat_history)
    socketio.emit('chat_history', chat_history, room=request.sid)
    broadcast_user_list()


@socketio.on('set_nickname')
def set_nickname(nick):
    if request.sid in users:
        users[request.sid]['nickname'] = nick
        broadcast_user_list()

@socketio.on('message')
def handle_message(msg):
    if request.sid in users:
        nickname = users[request.sid]['nickname']
        full_msg = f"{nickname}: {msg}"
        print(full_msg)
        send(full_msg, broadcast=True)

@socketio.on('request_chat_history')
def send_history():
    emit('chat_history', chat_history)

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
