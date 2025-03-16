from ..extensions import db
from datetime import datetime

class Message(db.Model):
    msgId = db.Column(db.Integer, primary_key=True)
    senderId = db.Column(db.Integer, nullable=False)  
    receiverId = db.Column(db.Integer, nullable=False) 
    content = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
