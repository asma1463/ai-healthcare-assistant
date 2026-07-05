import os


class ConfigError(RuntimeError):
    pass


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"{name} is not configured. Add it to your .env file.")
    return value


PINECONE_INDEX = os.getenv("PINECONE_INDEX", "medichatbot")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SARVAM_STT_URL = os.getenv("SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text")
SARVAM_TTS_URL = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saarika:v2.5")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v2")
SARVAM_TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "anushka")
SARVAM_TTS_LANGUAGE = os.getenv("SARVAM_TTS_LANGUAGE", "en-IN")
