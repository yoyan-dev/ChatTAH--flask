import os

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///chattah.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "supersecretkey"

    UPLOAD_FOLDER = os.path.join(os.getcwd(), "static/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
