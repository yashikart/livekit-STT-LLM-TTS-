import asyncio
import uuid
import time
import requests
import openai
import wave
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import datetime
import pandas as pd
from livekit import api, rtc

LIVEKIT_URL="wss://voiceagent-9uc4cj8p.livekit.cloud"
LIVEKIT_API_KEY="APIAi2NKDGwEq3H"
LIVEKIT_API_SECRET="f4TJQFxfiDG17d7yTeqB4DYtHO9j1w4pGqMhltDMLQlA"
ELEVENLABS_API_KEY="sk_7de076d12cfc514222e377f4a19b2ac4eb0dd9df181c41d2"
GROQ_API_KEY="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"
LOG_PATH="logs/metrics_log.xlsx"

# --- Salon Services ---
SALON_SERVICES = {
    "haircut": "Haircut: ₹500 – includes wash and blow dry.",
    "facial": "Facial: ₹1500 – includes deep cleansing and massage.",
    "waxing": "Waxing: ₹800 – includes arms, legs, and underarms.",
    "bridal": "Bridal Package: ₹7000 – includes makeup, hairstyle, facial, and saree draping.",
    "timing": "We are open from 10 AM to 8 PM, Monday to Saturday.",
    "cancellation": "You can cancel or reschedule at least 4 hours before your appointment."
}

openai.api_key = GROQ_API_KEY
AGENT_NAME = "Riya"

# --- Core Functions ---
def speak_text(text):
    print(f"🎤 AI says: {text}")
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    response = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech/MIMWfj3Kntn5eVoJX5er/stream",
        headers=headers, json=data
    )
    with open("temp.wav", "wb") as f:
        f.write(response.content)
    data, fs = sf.read("temp.wav")
    sd.play(data, fs)
    sd.wait()
    os.remove("temp.wav")

def transcribe_bytes(audio_bytes):
    with wave.open("temp_input.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_bytes)
    with open("temp_input.wav", "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    os.remove("temp_input.wav")
    return transcript["text"]

def get_service_info(user_input):
    for key, info in SALON_SERVICES.items():
        if key in user_input.lower():
            return info
    return None

def generate_response(user_input):
    service_info = get_service_info(user_input)
    if service_info:
        return service_info

    messages = [
        {"role": "system", "content": f"You are {AGENT_NAME}, a helpful salon booking assistant. Follow these rules:\n{SALON_SERVICES}"},
        {"role": "user", "content": user_input}
    ]
    response = openai.ChatCompletion.create(
        model="llama3-8b-8192", messages=messages, temperature=0.6
    )
    return response["choices"][0]["message"]["content"]

def monitor_interrupt(audio_chunk):
    audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
    amplitude = np.abs(audio_np).mean()
    return amplitude > 5000

def log_metrics(input_text, response_text, latency):
    now = datetime.datetime.now()
    log_data = {
        "Timestamp": [now],
        "User Input": [input_text],
        "Response": [response_text],
        "Latency (s)": [latency]
    }
    df = pd.DataFrame(log_data)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if os.path.exists(LOG_PATH):
        df.to_excel(LOG_PATH, mode="a", header=False, index=False)
    else:
        df.to_excel(LOG_PATH, index=False)

def welcome():
    print("✨ GlowUp Voice Agent is ready! Waiting for audio input...")

# --- LiveKit Audio Handler ---
async def handle_audio_track(track):
    audio_bytes = b""
    async for frame in track:
        audio_bytes += frame.data
        if monitor_interrupt(frame.data):
            break
    if audio_bytes:
        start = time.time()
        user_input = transcribe_bytes(audio_bytes)
        response = generate_response(user_input)
        latency = round(time.time() - start, 2)
        log_metrics(user_input, response, latency)
        speak_text(response)

# --- Main Entry ---
async def main():
    print("🔗 Connecting to LiveKit...")
    room = rtc.Room()

    token = api.AccessToken(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET
    ).with_identity(f"glowup_{uuid.uuid4()}") \
     .with_name("VoiceAgent") \
     .with_grants(api.VideoGrants(room_join=True, room="VoiceAgent")) \
     .to_jwt()

    await room.connect(url=LIVEKIT_URL, token=token)

    @room.on("track_subscribed")
    def on_track(track, publication, participant):
        if isinstance(track, rtc.AudioStreamTrack):
            asyncio.create_task(handle_audio_track(track))  # ✅ async call in sync function

    welcome()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())