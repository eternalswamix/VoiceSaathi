# VoiceSaathi

VoiceSaathi is a minimal black-theme AI voice chat workspace built with Flask, Google Gemini, Google Sign-In, Supabase chat history, and Edge TTS voice replies.

## Features

- Minimal dark horizontal chat layout
- Google Sign-In authentication
- Supabase-backed chat history
- User-provided Gemini API key support
- Voice input through browser speech recognition
- Optional voice replies through Edge TTS and Supabase Storage
- Responsive UI for desktop and mobile

## Tech Stack

- Python + Flask
- Google Gemini via `google-genai`
- Google OAuth ID token verification
- Supabase database and storage
- Tailwind CDN
- Edge TTS

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy the environment template:

```bash
copy .env.example .env
```

3. Fill required values in `.env`:

```env
SECRET_KEY="replace-with-a-long-random-secret"
GOOGLE_CLIENT_ID="your_google_client_id.apps.googleusercontent.com"
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your_supabase_anon_key"
GOOGLE_API_KEY="optional_default_gemini_key"
```

4. Run locally:

```bash
python run.py
```

Open `http://127.0.0.1:5000`.

## Gemini API Key

Users can paste their own Gemini API key inside the app. The key is kept in server memory for the active Flask session and is not stored in Supabase or committed to the repository. If no user key is provided, the app falls back to `GOOGLE_API_KEY` from `.env`.

For production, use a real `SECRET_KEY` and a persistent server/runtime model that matches your deployment needs.

## Required Supabase Resources

The app expects these tables/buckets to exist:

- `chats`
- `messages`
- `universal_user_data`
- Storage bucket: `ai-voice`

Keep `SUPABASE_SERVICE_ROLE_KEY` server-only. Never expose it in frontend code.

## Author

**Madhav Swami - Career Architect & Neural Engineer**

- Network: [LinkedIn](https://www.linkedin.com/in/madhav-swami/)
- Source: [GitHub](https://github.com/eternalswamix)
- Status: [X/Twitter](https://x.com/eternalswamix)
- Protocol: Email

## Security

Do not commit `.env`, API keys, Supabase service-role keys, OAuth secrets, or generated audio files. See [SECURITY.md](SECURITY.md).

## License

Project distributed under the Apache License 2.0. See [LICENSE](LICENSE) for more information.
