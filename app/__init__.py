import os
import secrets

from dotenv import load_dotenv
from flask import Flask
from app.routes.auth_routes import auth_bp
from app.routes.chat_routes import chat_bp

load_dotenv()


def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
    app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID", "")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    @app.context_processor
    def inject_auth_config():
        return {"google_client_id": app.config["GOOGLE_CLIENT_ID"]}

    return app
