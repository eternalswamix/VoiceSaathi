import asyncio
import os
import tempfile
import uuid

import edge_tts

from app.core.supabase_client import supabase


async def generate_voice(text):
    temp_dir = tempfile.gettempdir()
    filename = f"reply_{uuid.uuid4()}.mp3"
    temp_path = os.path.join(temp_dir, filename)

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-IN-NeerjaNeural",
    )

    await communicate.save(temp_path)

    with open(temp_path, "rb") as audio_file:
        supabase.storage.from_("ai-voice").upload(
            filename,
            audio_file,
            {"content-type": "audio/mpeg"},
        )

    return supabase.storage.from_("ai-voice").get_public_url(filename)


def text_to_speech(text):
    return asyncio.run(generate_voice(text))
