from flask import Flask, render_template, request
from flask_socketio import SocketIO, send
from uuid import uuid4
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 닉네임 저장: 세션별 고유 ID
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def connect():
    user_id = str(uuid4())
    users[request.sid] = {'id': user_id, 'nickname': '익명'}
    print(f'User connected: {user_id}')

@socketio.on('set_nickname')
def set_nickname(nick):
    users[request.sid]['nickname'] = nick

@socketio.on('message')
def handle_message(msg):
    nickname = users[request.sid]['nickname']
    full_msg = f"{nickname}: {msg}"
    print(full_msg)
    send(full_msg, broadcast=True)

@socketio.on('disconnect')
def disconnect():
    if request.sid in users:
        print(f"User disconnected: {users[request.sid]['nickname']}")
        del users[request.sid]

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
