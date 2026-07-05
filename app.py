from io import BytesIO

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.citations import format_sources
from src.config import ConfigError, GROQ_MODEL, PINECONE_INDEX, get_required_env
from src.osm_places import OSMPlacesError, search_nearby_providers
from src.helper import download_hugging_face_embeddings
from src.prompt import system_prompt
from src.recommendations import choose_provider_type, recommendation_message
from src.sarvam import SarvamError, synthesize_speech, transcribe_audio
import traceback

load_dotenv()


app = Flask(__name__)


def create_rag_chain():
    get_required_env("PINECONE_API_KEY")
    get_required_env("GROQ_API_KEY")

    embeddings = download_hugging_face_embeddings()
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=PINECONE_INDEX,
        embedding=embeddings,
    )
    retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    chat_model = ChatGroq(model=GROQ_MODEL, temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


try:
    rag_chain = create_rag_chain()
    startup_error = None
    print("✅ RAG chain created successfully")



except Exception as exc:
    rag_chain = None
    startup_error = str(exc)
    print("❌ Failed to create RAG chain")
    traceback.print_exc()


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/get", methods=["POST"])
def chat():
    if rag_chain is None:
        return error_response(
            "The medical assistant is not configured yet. Check your API keys and Pinecone index.",
            503,
            startup_error,
        )

    json_payload = request.get_json(silent=True) or {}
    msg = (request.form.get("msg") or json_payload.get("msg") or "").strip()
    latitude = request.form.get("latitude") or json_payload.get("latitude")
    longitude = request.form.get("longitude") or json_payload.get("longitude")

    if not msg:
        return error_response("Please enter a question before sending.", 400)

    try:
        response = rag_chain.invoke({"input": msg})
    except Exception as exc:
        return error_response(
            "I could not generate an answer right now. Please try again.",
            502,
            str(exc),
        )

    answer = response.get("answer", "")
    source_documents = response.get("context", [])
    sources = format_sources(source_documents)
    provider_type = choose_provider_type(msg, answer)
    providers = []
    provider_note = None

    if provider_type and latitude and longitude:
        provider_note = recommendation_message(provider_type)
        try:
            providers = search_nearby_providers(provider_type, latitude, longitude)
        except (ConfigError, OSMPlacesError) as exc:
            provider_note = f"{provider_note} Provider search is unavailable: {exc}"

    return jsonify(
        {
            "answer": answer,
            "sources": sources,
            "recommendation": {
                "provider_type": provider_type,
                "message": provider_note,
                "providers": providers,
            },
        }
    )


@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_file = request.files.get("audio")

    print("Audio file:", audio_file)

    try:
        transcript = transcribe_audio(audio_file)
        # None means Sarvam returned an empty transcript (silence / no speech).
        # Return 200 with an empty string so the frontend stays quiet.
        return jsonify({"transcript": transcript or ""})

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 400

@app.route("/speak", methods=["POST"])
def speak():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or request.form.get("text") or "").strip()
    try:
        audio_bytes, content_type = synthesize_speech(text)
    except (ConfigError, SarvamError) as exc:
        return error_response(str(exc), 400)

    return send_file(
        BytesIO(audio_bytes),
        mimetype=content_type,
        as_attachment=False,
        download_name="assistant-response.wav",
    )


@app.route("/providers", methods=["GET"])
def providers():
    provider_type = (request.args.get("type") or "hospital").strip()
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    if not latitude or not longitude:
        return error_response("Latitude and longitude are required for provider search.", 400)

    try:
        results = search_nearby_providers(provider_type, latitude, longitude)
    except (ConfigError, OSMPlacesError) as exc:
        return error_response(str(exc), 400)
    return jsonify({"providers": results})


def error_response(message, status_code=400, detail=None):
    payload = {"error": message}
    if app.debug and detail:
        payload["detail"] = detail
    return jsonify(payload), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
