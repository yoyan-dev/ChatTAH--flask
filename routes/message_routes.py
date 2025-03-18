from flask import Blueprint, jsonify, request, g
from flask_login import login_required
from ..extensions import db
from ..models.message import Message

bp = Blueprint("messages", __name__)

@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    current_user = g.user
    messages = Message.query.filter(
        ((Message.senderId == current_user.id) & (Message.receiverId == user_id)) |
        ((Message.senderId == user_id) & (Message.receiverId == current_user.id))
    ).order_by(Message.created_at.desc()).all()

    return jsonify([{
        "msgId": msg.msgId,
        "image": current_user.image,
        "senderId": msg.senderId,
        "receiverId": msg.receiverId,
        "content": msg.content,
        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")  
    } for msg in messages])

@bp.route('/send', methods=['POST'])
@login_required
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
        db.session.commit()
        return jsonify({'success': 'Message sent successfully'})
    except:
        db.session.rollback()
        return jsonify({'error': 'Database error!'}), 500

@bp.route('/updateMessageStatus/<int:user_id>', methods=['GET'])
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


@bp.route('/deleteConvo/<int:user_id>', methods=['GET'])
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
