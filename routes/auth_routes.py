from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user
from ..extensions import db, bcrypt
from ..models.user import User

bp = Blueprint("auth", __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template('register.html', message='Username or email already exists! Please use a different one.')

        try:
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

            user = User(username=username, email=email, password_hash=password_hash, image="avatar.PNG")

            db.session.add(user)
            db.session.commit()

            flash('User registered successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login')) 

        except Exception as e:
            db.session.rollback()
            return render_template('register.html', message=str(e))

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            return redirect(url_for('users.home'))
        else:
            return render_template('login.html', message="Login failed. Check your credentials.")

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
