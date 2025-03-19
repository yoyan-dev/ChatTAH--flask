from flask import render_template, Blueprint, jsonify, g, session, request, url_for, current_app, redirect
from flask_login import login_required
from ..models.user import User
from ..models.message import Message
from ..extensions import login_manager, db
from werkzeug.utils import secure_filename
import os

bp = Blueprint("users", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.route('/getuser/<int:user_id>', methods=['GET'])
def get_user(user_id):
    current_user = g.user
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': f'User not found'}), 404

    message_count = Message.query.filter(
        ((Message.senderId == user.id) & (Message.receiverId == current_user.id)) |
        ((Message.senderId == current_user.id) & (Message.receiverId == user.id))
    ).count()

    return jsonify({
        "id": user.id,
        "image": user.image,
        "username": user.username,
        "email": user.email,
        "message_count": message_count
    })


@bp.route('/search/', defaults={'param': None}, methods=['GET'])
@bp.route('/search/<string:param>', methods=['GET'])
@login_required
def get_search_users(param):
    current_user = g.user 

    query = User.query.filter(User.id != current_user.id)

    if param: 
        query = query.filter(User.username.ilike(f"%{param}%"))

    users = query.all()

    if not users:
        return jsonify({'error': f'User not found'}), 404

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
            "image": user.image,
            "email": user.email,
            "unread_count": unread_count,
            "last_message": last_message,
            "message_date": message_date  
        })

    return jsonify(user_list)

@bp.route('/home')
@login_required
def home():
    if g.user:
        return render_template('home.html', user=g.user)
    else:
        return render_template('index.html')

@bp.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')

        try:
            file = request.files["file"]

            if file:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                g.user.image = filename  

            g.user.username = username  
            g.user.email = email  
            db.session.commit()
        except Exception as e:
            return jsonify({"error": str(e)})  

        return jsonify({"message": f"Update successfully"})

    return render_template("profile.html", user=g.user)

@bp.route('/delete/<int:user_id>', methods=['GET'])
@login_required
def deleteUser(user_id):
    try:
        db.session.query(User).filter(User.id == user_id).delete()
        db.session.commit()
        return jsonify({"message": f"Account deleted successfully."})
    except:
        return jsonify({"error": "Error! Please try again."})