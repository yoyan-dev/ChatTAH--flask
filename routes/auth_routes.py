from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user
from ..extensions import db, bcrypt
from ..models.user import User

bp = Blueprint("auth", __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        try:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash('User registered successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except:
            return render_template('register.html', message="Error! Please try again.")

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
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
