from flask import Blueprint, request, jsonify, render_template, session
from app.services.assistant_engine import process_user_message
from datetime import datetime
from app.services.edge_tts_service import text_to_speech
from app.core.supabase_client import supabase
import os
import uuid
from dotenv import load_dotenv
import traceback

load_dotenv()

chat_bp = Blueprint("chat", __name__)

DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "local-user-001")
GEMINI_KEYS = {}

def get_or_create_chat(user_id):
    """
    Returns latest chat id for user
    Creates new chat if none exists
    """

    res = supabase.table("chats") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if res.data:
        return res.data[0]["id"]

    new_chat = supabase.table("chats").insert({
        "user_id": user_id,
        "title": "New Chat"
    }).execute()

    return new_chat.data[0]["id"]


def user_owns_chat(user_id, chat_id):
    if not chat_id:
        return False

    chat = supabase.table("chats") \
        .select("id") \
        .eq("id", chat_id) \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    return bool(chat.data)

@chat_bp.route("/")
def index():
    return render_template("index.html")


@chat_bp.route("/Madhavium")
@chat_bp.route("/preview")
def Madhavium_preview():
    return render_template("index.html")


def get_current_user_id():
    user = session.get("user")
    return user["id"] if user else None


def mask_key(api_key):
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "saved"
    return f"{api_key[:4]}...{api_key[-4:]}"


def get_session_gemini_key():
    key_id = session.get("gemini_key_id")
    return GEMINI_KEYS.get(key_id) if key_id else None


@chat_bp.get("/settings/gemini-key")
def get_gemini_key_status():
    session_key = get_session_gemini_key()
    return jsonify({
        "has_key": bool(session_key or os.getenv("GOOGLE_API_KEY")),
        "session_key": bool(session_key),
        "masked": mask_key(session_key)
    })


@chat_bp.post("/settings/gemini-key")
def save_gemini_key():
    data = request.get_json(silent=True) or {}
    api_key = (data.get("api_key") or "").strip()

    if not api_key:
        return jsonify({"error": "Gemini API key required"}), 400

    key_id = session.get("gemini_key_id") or str(uuid.uuid4())
    GEMINI_KEYS[key_id] = api_key
    session["gemini_key_id"] = key_id
    session.modified = True
    return jsonify({
        "success": True,
        "has_key": True,
        "session_key": True,
        "masked": mask_key(api_key)
    })


@chat_bp.delete("/settings/gemini-key")
def clear_gemini_key():
    key_id = session.pop("gemini_key_id", None)
    if key_id:
        GEMINI_KEYS.pop(key_id, None)
    session.modified = True
    return jsonify({
        "success": True,
        "has_key": bool(os.getenv("GOOGLE_API_KEY")),
        "session_key": False,
        "masked": None
    })


# ---------------- CREATE NEW CHAT ----------------
@chat_bp.route("/chat/new", methods=["POST"])
def create_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    chat = supabase.table("chats").insert({
        "user_id": user_id,
        "title": "Chat " + datetime.now().strftime("%d %b %H:%M")
    }).execute()

    return jsonify(chat.data[0])


# ---------------- GET ALL CHATS ----------------
@chat_bp.route("/chats")
def get_chats():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    chats = supabase.table("chats") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    return jsonify(chats.data)


# ---------------- GET CHAT MESSAGES ----------------
@chat_bp.route("/chat/<chat_id>", methods=["GET"])
def get_messages(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    chat = supabase.table("chats").select("id").eq("id", chat_id).eq("user_id", user_id).limit(1).execute()
    if not chat.data:
        return jsonify({"error": "Chat not found"}), 404

    messages = supabase.table("messages") \
        .select("*") \
        .eq("chat_id", chat_id) \
        .order("created_at") \
        .execute()

    return jsonify(messages.data)


# ---------------- SEND MESSAGE ----------------
@chat_bp.route("/chat/send", methods=["POST"])
def send_message():
    try:
        data = request.json

        message = data.get("message")
        msg_type = data.get("type", "text")
        requested_chat_id = data.get("chat_id")

        if not message:
            return jsonify({"error": "Message required"}), 400

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Login required"}), 401

        # Use the selected chat when it belongs to this user; otherwise continue latest chat.
        chat_id = requested_chat_id if user_owns_chat(user_id, requested_chat_id) else get_or_create_chat(user_id)

        # ✅ SAVE USER MESSAGE
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "sender": "user",
            "content": message
        }).execute()

        # 🔢 COUNT USER MSGS
        user_msgs = supabase.table("messages") \
            .select("id") \
            .eq("chat_id", chat_id) \
            .eq("sender", "user") \
            .execute()

        # 📝 FIRST MSG → UPDATE TITLE
        if len(user_msgs.data) == 1:
            title = " ".join(message.split()[:5])
            supabase.table("chats").update({
                "title": title
            }).eq("id", chat_id).execute()

        # 🤖 AI RESPONSE
        ai_reply = process_user_message(message, api_key=get_session_gemini_key())

        audio_file = None
        audio_url = None


        # 🔊 VOICE (optional)
        if msg_type == "voice":
            try:
                audio_file = text_to_speech(ai_reply)

                if audio_file:
                    audio_url = f"/audio/{os.path.basename(audio_file)}"
                else:
                    audio_url = None
            
            except Exception as e:
                print("TTS FAILED:", e)
                audio_url = None
        
        # ✅ SAVE AI MESSAGE
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "sender": "bot",
            "content": ai_reply
        }).execute()

        return jsonify({
            "reply": ai_reply,
            "audio": audio_url,
            "chat_id": chat_id
        })
    except Exception as e:
        traceback.print_exc()

        friendly_msg = (
            "AI response failed. Gemini API key check kijiye aur phir try kijiye."
        )

    return jsonify({
        "reply": friendly_msg
    })

# ---------------------DELETE ROUTE---------------------

@chat_bp.route("/chat/delete/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "Login required"}), 401

        chat = supabase.table("chats").select("id").eq("id", chat_id).eq("user_id", user_id).limit(1).execute()
        if not chat.data:
            return jsonify({"success": False, "error": "Chat not found"}), 404

        # delete messages first (FK safety)
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()

        # delete chat
        supabase.table("chats").delete().eq("id", chat_id).execute()

        return jsonify({"success": True})

    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False}), 500

@chat_bp.app_errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
