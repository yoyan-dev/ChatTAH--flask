from flask import Flask, render_template, redirect, url_for, request, flash, session, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'secretkey'  

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Message(db.Model):
    msgId = db.Column(db.Integer, primary_key=True)
    senderId = db.Column(db.Integer, nullable=False)  
    receiverId = db.Column(db.Integer, nullable=False) 
    content = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id) 

def get_users():
    users = User.query.all() 
    user_list = [
        {"id": user.id, "name": user.username, "email": user.email}
        for user in users
    ]
    return user_list


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        try:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash('User registered successfully!', 'success')
            return redirect(url_for('login'))
        except:
            message = f'Error! please try again.'
            return render_template('register.html', message=message)

    return render_template('register.html')

@app.route('/ogin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            message = 'Login failed. Check your credentials.'
            return render_template('login.html', message=message)

    return render_template('login.html')

@app.route('/test-messages')
def test_messages():
    messages = Message.query.all()
    return jsonify([msg.content for msg in messages]) 

from flask import jsonify

@app.route('/messages/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    try:
        current_user = g.user 
        messages = Message.query.filter(
            (Message.senderId == current_user.id) & (Message.receiverId == user_id) |
            (Message.senderId == user_id) & (Message.receiverId == current_user.id)
        ).order_by(Message.created_at.desc()).all()

        messages_list = [{
            "msgId": msg.msgId,
            "senderId": msg.senderId,
            "receiverId": msg.receiverId,
            "content": msg.content,
            "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")  
        } for msg in messages]

        return jsonify(messages_list)
    
    except Exception as e:
        return jsonify({"error": "Something went wrong!"}), 500 



@app.route('/send', methods=['GET','POST'])
def send_message():
    data = request.get_json()
    content = data.get('content')
    receiver_id = data.get('receiver_id')
    status = 'unread'
    current_user = g.user  

    if not content or not receiver_id:
        return jsonify({'error': 'Content and Receiver ID are required'}), 400

    try:
        message = Message(senderId=current_user.id, receiverId=receiver_id, content=content, status=status)
        db.session.add(message)
        db.session.flush() 
        db.session.commit()
        return jsonify({'success': 'Message sent successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error!'}), 500

@app.route('/updateMessageStatus/<int:user_id>', methods=['GET'])
@login_required
def update_message_status(user_id):
    current_user = g.user

    messages = Message.query.filter(
        ((Message.senderId == current_user.id) & (Message.receiverId == user_id)) |
        ((Message.senderId == user_id) & (Message.receiverId == current_user.id) & (Message.status == 'unread'))
    ).order_by(Message.created_at.desc()).all()

    if messages:
        for msg in messages:
            msg.status = "read"

        db.session.commit() 
        return jsonify({"message": "Message status updated"})

    return jsonify({"message": "No unread messages found"})

@app.route('/deleteConvo/<int:user_id>', methods=['GET'])
def delete_messages(user_id):
    current_user = g.user

    condition = (
            (Message.senderId == current_user.id) & (Message.receiverId == user_id)
        ) | (
            (Message.senderId == user_id) & (Message.receiverId == current_user.id)
        )

    deleted_count = db.session.query(Message).filter(condition).delete(synchronize_session=False)
    db.session.commit()

    if deleted_count > 0:
        return jsonify({"message": f"Deleted {deleted_count} messages between users."})
    else:
        return jsonify({"message": "No messages found to delete."})

@app.route('/getuser/<int:user_id>', methods=['GET'])
def get_user(user_id):
    current_user = g.user
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    message_count = Message.query.filter(
        ((Message.senderId == user.id) & (Message.receiverId == current_user.id)) |
        ((Message.senderId == current_user.id) & (Message.receiverId == user.id))
    ).count()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message_count": message_count
    })


@app.route('/search/', methods=['GET'])
@app.route('/search/<string:param>', methods=['GET'])
@login_required
def get_search_users(param=None):
    current_user = g.user 

    query = User.query.filter(User.id != current_user.id)

    if param: 
        query = query.filter(User.username.ilike(f"%{param}%"))

    users = query.all()

    if not users:
        return jsonify({'error': 'User not found'}), 404

    user_list = []
    
    for user in users:
        unread_count = Message.query.filter(
            (Message.senderId == user.id) & 
            (Message.receiverId == current_user.id) & 
            (Message.status == 'unread')
        ).count()

        last_message = None
        message_date = None

        last_message_obj = Message.query.filter(
            ((Message.senderId == user.id) & (Message.receiverId == current_user.id)) |
            ((Message.senderId == current_user.id) & (Message.receiverId == user.id))
        ).order_by(Message.created_at.desc()).first()

        if last_message_obj: 
            last_message = last_message_obj.content
            message_date = last_message_obj.created_at 
        else:
            last_message = "send message"
            message_date = None

        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "unread_count": unread_count,
            "last_message": last_message,
            "message_date": message_date  
        })

    return jsonify(user_list)


@app.route('/home')
@login_required
def home():
    if g.user:
        current_user = g.user
        users = User.query.filter(User.id != current_user.id).all()
        return render_template('home.html', user=g.user, users=users)
    else:
        return render_template('index.html')
    
# @app.route('/profile')
# @login_required
# def profile():
#     if g.user:
#         current_user = g.user
#         users = User.query.filter(User.id != current_user.id).all()
#         return render_template('profile.html', user=g.user, users=users)
#     else:
#         return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
