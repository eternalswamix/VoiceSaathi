import os

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request, session
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.supabase_client import save_universal_data

load_dotenv()

auth_bp = Blueprint("auth", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


@auth_bp.post("/auth/google")
def google_login():
    data = request.get_json(silent=True) or {}
    credential = data.get("credential")

    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "GOOGLE_CLIENT_ID missing in .env"}), 500

    if not credential:
        return jsonify({"error": "Google credential is required"}), 400

    try:
        payload = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        user = {
            "id": payload["sub"],
            "email": payload.get("email"),
            "name": payload.get("name"),
            "avatar_url": payload.get("picture"),
        }

        session.permanent = True
        session["user"] = user

        save_universal_data(
            user_id=user["id"],
            email=user["email"],
            name=user["name"],
            avatar_url=user["avatar_url"],
            data_type="profile",
            data_key="google_profile",
            data={"provider": "google", **user},
        )

        return jsonify({"user": user})
    except Exception as error:
        return jsonify({"error": "Google login failed", "details": str(error)}), 401


@auth_bp.get("/auth/me")
def current_user():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"user": user})


@auth_bp.post("/auth/logout")
def logout():
    key_id = session.get("gemini_key_id")
    if key_id:
        from app.routes.chat_routes import GEMINI_KEYS

        GEMINI_KEYS.pop(key_id, None)
    session.clear()
    return jsonify({"message": "Logged out"})
