import os
from google import genai
from dotenv import load_dotenv
from ..prompts.clone import CLONE_PROFILE

load_dotenv()

def get_ai_reply(user_message: str, api_key: str | None = None) -> str:
    selected_key = (api_key or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not selected_key:
        return "Gemini API key missing hai. Settings me apni Gemini API key save kijiye."

    client = genai.Client(api_key=selected_key)
    prompt = f"""
{CLONE_PROFILE}

User: {user_message}
AI:
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    return response.text.strip()
