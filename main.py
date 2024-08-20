from flask import Flask, render_template, session, redirect, request, url_for
from flask_socketio import SocketIO,join_room,leave_room,send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "kkipo"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join") is not None
        create = request.form.get("create") is not None
        
        if not name:
            return render_template("home.html", error="please enter a name.", code=code, name=name)
        
        if join and not code:
            return render_template("home.html", error="please enter a room code.", code=code, name=name)
        
        if create:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        else:
            if code not in rooms:
                return render_template("home.html", error="room does not exist.", code=code, name=name)
            room = code
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
        
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message (data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content,to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message":"room ma a gaya gandiya"},to=room)
    rooms[room] ["members"] += 1
    print(f"{name} room ma aa gaya gandiya {room}")
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms [room]
    
    send ({"name":name,"message":"nikal gaya mc"},to=room)
    print(f"{name} nikal gaya mc {room}")        
        
    
if __name__ == "__main__":
    socketio.run(app, debug=True)
