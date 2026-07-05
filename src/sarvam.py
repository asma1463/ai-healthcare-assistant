import base64
import requests

from src.config import (
    SARVAM_STT_MODEL,
    SARVAM_STT_URL,
    SARVAM_TTS_LANGUAGE,
    SARVAM_TTS_MODEL,
    SARVAM_TTS_SPEAKER,
    SARVAM_TTS_URL,
    get_required_env,
)


class SarvamError(RuntimeError):
    pass


def _headers():
    return {
        "api-subscription-key": get_required_env("SARVAM_API_KEY")
    }


# ============================================================
# Speech To Text
# ============================================================
def transcribe_audio(file_storage):
    if not file_storage or not file_storage.filename:
        raise SarvamError("Please upload a valid audio recording.")

    print("\n" + "=" * 70)
    print("🎤 SARVAM SPEECH TO TEXT")
    print("=" * 70)
    print("Filename :", file_storage.filename)
    print("Mimetype :", file_storage.mimetype)
    print("Model    :", SARVAM_STT_MODEL)
    print("Endpoint :", SARVAM_STT_URL)
    print("=" * 70)

    files = {
        "file": (
            file_storage.filename,
            file_storage.stream,
            file_storage.mimetype or "application/octet-stream",
        )
    }

    data = {
        "model": SARVAM_STT_MODEL
    }

    response = None

    try:
        response = requests.post(
            SARVAM_STT_URL,
            headers=_headers(),
            files=files,
            data=data,
            timeout=45,
        )

        print("HTTP Status:", response.status_code)
        print("\nResponse:")
        print(response.text)
        print("=" * 70)

        response.raise_for_status()

        payload = response.json()

    except requests.RequestException as exc:
        message = "Speech transcription failed."

        if response is not None:
            message += f"\n\nStatus Code: {response.status_code}"
            message += f"\n\nResponse:\n{response.text}"

        raise SarvamError(message) from exc

    except ValueError as exc:
        raise SarvamError("Sarvam returned invalid JSON.") from exc

    # Sarvam uses the key "transcript"; fall back to legacy aliases
    if "transcript" in payload:
        transcript = payload["transcript"]
    else:
        transcript = (
            payload.get("text")
            or payload.get("transcription")
            or payload.get("data", {}).get("transcript")
        )

    # transcript key present but empty string → silence / no speech detected.
    # Return None so the Flask route can respond with {"transcript": ""}
    # instead of a 400 error.
    if transcript is None:
        raise SarvamError(
            f"Sarvam response missing a transcript field.\n\nFull response:\n{payload}"
        )

    return transcript.strip() if transcript else None


# ============================================================
# Text To Speech
# ============================================================
def synthesize_speech(text):
    if not text.strip():
        raise SarvamError("There is no response text.")

    body = {
        "text": text,
        "target_language_code": SARVAM_TTS_LANGUAGE,
        "speaker": SARVAM_TTS_SPEAKER,
        "model": SARVAM_TTS_MODEL,
    }

    response = None

    try:
        response = requests.post(
            SARVAM_TTS_URL,
            headers={
                **_headers(),
                "Content-Type": "application/json",
            },
            json=body,
            timeout=45,
        )

        print("\n🔊 SARVAM TEXT TO SPEECH")
        print("HTTP Status:", response.status_code)

        response.raise_for_status()

    except requests.RequestException as exc:
        if response is not None:
            print(response.text)

        raise SarvamError(
            "Speech playback generation failed."
        ) from exc

    content_type = response.headers.get("Content-Type", "")

    if content_type.startswith("audio/"):
        return response.content, content_type

    payload = response.json()

    audio = (
        payload.get("audio")
        or payload.get("audio_content")
        or payload.get("data", {}).get("audio")
        or (payload.get("audios") or [None])[0]
    )

    if not audio:
        raise SarvamError("Sarvam returned no audio.")

    try:
        return base64.b64decode(audio), "audio/wav"

    except Exception as exc:
        raise SarvamError("Invalid audio returned by Sarvam.") from exc