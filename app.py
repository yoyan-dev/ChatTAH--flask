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
        g.user = User.query.get(user_id)  # Fetch the logged-in user

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
            message = f'Account created! You can now log in.'
            return render_template('index.html', message=message)
        except:
            message = f'Error! please try again.'
            return render_template('register.html', message=message)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
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
            return render_template('index.html', message=message)

    return render_template('index.html')

@app.route('/test-messages')
def test_messages():
    messages = Message.query.all()
    return jsonify([msg.content for msg in messages]) 

@app.route('/messages', methods=['GET'])
def get_messages():
    current_user = g.user
    messages = Message.query.all()
    messages_list = [{
        "msgId": msg.msgId,
        "senderId": msg.senderId,
        "receiverId": msg.receiverId,
        "content": msg.content,
        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for msg in messages]

    return jsonify(messages_list)


@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    content = data.get('content')
    receiver_id = data.get('receiver_id')
    current_user = g.user  # Ensure this is properly set

    if not content or not receiver_id:
        return jsonify({'error': 'Content and Receiver ID are required'}), 400

    try:
        message = Message(senderId=current_user.id, receiverId=receiver_id, content=content)
        db.session.add(message)
        db.session.flush() 
        db.session.commit()
        return jsonify({'success': 'Message sent successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error!'}), 500

@app.route('/home')
@login_required
def home():
    if g.user:
        current_user = g.user
        users = User.query.filter(User.id != current_user.id).all()
        return render_template('home.html', user=g.user, users=users)
    else:
        return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
