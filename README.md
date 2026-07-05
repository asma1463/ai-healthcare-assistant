# AI Healthcare Assistant

This project upgrades the normal Flask, LangChain, Pinecone medical RAG chatbot into an AI healthcare assistant with Groq chat completion, Sarvam speech input/output, Google Places healthcare provider search, and source attribution.

The assistant is informational only. It does not diagnose, claim certainty, or replace care from a qualified medical professional.

## Architecture

- `app.py` is the Flask entrypoint and exposes chat, transcription, speech, and provider-search routes.
- `src/helper.py` loads PDFs, splits documents, and creates Hugging Face embeddings.
- `src/prompt.py` contains the healthcare-safe RAG system prompt.
- `src/citations.py` formats retrieved LangChain document metadata into UI citations.
- `src/sarvam.py` handles Sarvam speech-to-text and text-to-speech calls.
- `src/google_places.py` searches nearby healthcare providers with Google Places.
- `src/recommendations.py` maps symptom language to provider categories.
- `templates/chat.html` and `static/style.css` provide the chat UI.

## API Flow

1. The browser sends the user message to `POST /get`.
2. Flask invokes the LangChain retrieval chain.
3. Pinecone returns the top matching medical document chunks.
4. Groq generates a concise response from the retrieved context.
5. The backend formats real retrieved sources and returns JSON.
6. If the message suggests in-person care and browser location is available, the backend searches Google Places and returns nearby providers.

## Voice Pipeline

Speech-to-text:

1. The microphone button records audio in the browser.
2. The browser uploads the recording to `POST /transcribe`.
3. The backend forwards the audio to Sarvam STT.
4. The transcription is returned and placed in the chat input before sending.

Text-to-speech:

1. The speaker button sends assistant response text to `POST /speak`.
2. The backend calls Sarvam TTS.
3. The browser plays the returned audio.
4. Generated audio is cached in the browser for replay.

## Google Places Integration

The assistant can recommend nearby:

- Dermatologists
- Hospitals
- Clinics
- Pharmacies
- General physicians

Provider results include name, rating when available, address, approximate distance, and a Google Maps directions link. The browser must grant location access for automatic provider recommendations inside chat.

You can also call:

```bash
curl "http://localhost:8080/providers?type=hospital&latitude=12.9716&longitude=77.5946"
```

## Setup

Clone the repository:

```bash
git clone https://github.com/entbappy/Build-a-Complete-Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS.git
cd Build-a-Complete-Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS
```

Create and activate a Python environment:

```bash
conda create -n medibot python=3.10 -y
conda activate medibot
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from the example:

```bash
cp .env.example .env
```

Fill in:

```ini
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

SARVAM_API_KEY=
SARVAM_STT_MODEL=saarika:v2.5
SARVAM_TTS_MODEL=bulbul:v2
SARVAM_TTS_SPEAKER=anushka
SARVAM_TTS_LANGUAGE=en-IN

GOOGLE_MAPS_API_KEY=

PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX=medichatbot

HF_TOKEN=
```

## Build the Pinecone Index

Place medical PDFs in `data/`, then run:

```bash
python store_index.py
```

The default index is `medichatbot`. Override it with `PINECONE_INDEX`.

## Run Locally

```bash
python app.py
```

Open:

```text
http://localhost:8080
```

## Endpoints

- `GET /` renders the chat UI.
- `POST /get` accepts `msg`, optional `latitude`, and optional `longitude`; returns answer, sources, and provider recommendations.
- `POST /transcribe` accepts multipart audio field `audio`; returns transcription.
- `POST /speak` accepts JSON `{ "text": "..." }`; returns audio.
- `GET /providers` accepts `type`, `latitude`, and `longitude`; returns nearby providers.

## Error Handling

The app returns friendly JSON errors for missing API keys, invalid audio files, empty transcriptions, Groq failures, Sarvam failures, Pinecone setup issues, Google Places failures, and network timeouts.

## Tech Stack

- Python
- Flask
- LangChain
- Groq via `langchain-groq`
- Pinecone
- Hugging Face embeddings
- Sarvam STT/TTS
- Google Places API

