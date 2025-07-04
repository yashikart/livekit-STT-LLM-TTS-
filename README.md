
# 💇‍♀️ Voice-Powered Salon Assistant

An AI salon assistant that uses voice to help customers book appointments, get stylist recommendations, and receive confirmations using:

- 🔊 LiveKit for audio
- 🧠 GPT for natural conversation
- 🎙️ TTS for voice output
- ☁️ SST for scalable backend APIs

## 🚀 How It Works
1. User talks via LiveKit
2. Voice → Text → LLM
3. LLM processes the intent
4. Appointment booked via API
5. TTS responds vocally

## 🧱 Stack
- LiveKit
- OpenAI / Local LLM
- TTS (Coqui or Google Cloud)
- SST + AWS Lambda + DynamoDB
