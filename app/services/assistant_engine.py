from app.services.ai_service import get_ai_reply

def process_user_message(message, api_key=None):
    return get_ai_reply(message, api_key=api_key)
