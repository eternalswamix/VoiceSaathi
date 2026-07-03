import os
import uuid
import tempfile
import edge_tts
from app.core.supabase_client import supabase

async def generate_voice(text):
    temp_dir = tempfile.gettempdir()   # /tmp
    filename = f"reply_{uuid.uuid4()}.mp3"
    temp_path = os.path.join(temp_dir, filename)

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-IN-NeerjaNeural"
    )

    await communicate.save(temp_path)
    # ⬆️ Upload to Supabase Storage
    with open(temp_path, "rb") as f:
        supabase.storage.from_("ai-voice").upload(
            filename,
            f,
            {"content-type": "audio/mpeg"}
        )

    # 🔗 Public URL
    public_url = supabase.storage.from_("ai-voice").get_public_url(filename)

    return public_url


def text_to_speech(text):
    import asyncio
    return asyncio.run(generate_voice(text))
