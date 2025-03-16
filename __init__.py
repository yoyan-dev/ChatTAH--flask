from flask import Flask, g, session
from .config import Config
from .extensions import db, bcrypt, login_manager
from .models.user import User
from .routes import auth_routes, message_routes, user_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login" 

    app.register_blueprint(auth_routes.bp, url_prefix="/auth")
    app.register_blueprint(message_routes.bp, url_prefix="/messages")
    app.register_blueprint(user_routes.bp, url_prefix="/users")

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = User.query.get(user_id) if user_id else None

    return app
