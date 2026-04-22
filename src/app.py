import streamlit as st
import io
import re
import asyncio
from src.services import text_to_speech, speech_to_text, text

# Initialize the page
st.set_page_config(page_title="Phonagnosia", layout="centered")

# Map your service instances
stt_client = speech_to_text
llm_client = text  # This is the instance of your Client class
tts_client = text_to_speech

# ── Session state ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0

# ── Chat history container ──────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mpeg", autoplay=False)

# ── User Inputs ─────────────────────────────────────────────────────
user_prompt_text = st.chat_input("Send a message…")

audio_value = st.audio_input(
    "Or record a voice message",
    key=f"audio_{st.session_state.audio_key}",
)

# Handle Voice Input
if not user_prompt_text and audio_value:
    with st.spinner("Transcribing…"):
        try:
            if asyncio.iscoroutinefunction(stt_client):
                user_prompt_text = asyncio.run(stt_client(audio_value))
            else:
                user_prompt_text = stt_client(audio_value)
        except Exception as e:
            st.error(f"Transcription error: {e}")
            user_prompt_text = None
    st.session_state.audio_key += 1

# ── Main Processing Logic ──────────────────────────────────────────
if user_prompt_text:
    # Save and display user message
    st.session_state.messages.append({"role": "user", "content": user_prompt_text})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_prompt_text)

    # ── Assistant Response ──
    with chat_container:
        with st.chat_message("assistant"):
            # We use a dict to store the language to avoid 'nonlocal' SyntaxErrors
            runtime_data = {"lang": "en"}

            async def text_stream_wrapper():
                """
                Consumes the (text, lang) tuple from llm_client 
                and yields only text for st.write_stream.
                """
                async for chunk, lang in llm_client(user_prompt_text):
                    runtime_data["lang"] = lang
                    yield chunk

            # Streamlit 1.40+ natively handles async generators
            full_response = st.write_stream(text_stream_wrapper())

    # ── TTS Generation ──
    audio_bytes = None
    if full_response:
        with st.spinner("Generating speech…"):
            split_pattern = re.compile(r'(?<=[.?!,;:\n])\s+')
            sentences = [s.strip() for s in split_pattern.split(full_response) if s.strip()]

            audio_buffer = io.BytesIO()
            detected_lang = runtime_data["lang"]

            try:
                for phrase_stream in tts_client(iter(sentences), language=detected_lang):
                    for chunk in phrase_stream:
                        if isinstance(chunk, (bytes, bytearray)) and chunk:
                            audio_buffer.write(chunk)

                audio_bytes = audio_buffer.getvalue()
            except Exception as e:
                st.error(f"TTS Error: {e}")

    # ── Play and Save ──
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mpeg", autoplay=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "audio": audio_bytes if audio_bytes else None,
    })
