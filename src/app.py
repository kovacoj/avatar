import streamlit as st
import io
import re

from src.services.stt import Client as STTClient
from src.services.llm import Client as LLMClient
from src.services.tts import Client as TTSClient
from src.config import config

st.set_page_config(page_title="Phonagnosia", layout="centered")

# ── Initialise clients (cached so they survive reruns) ──────────────
@st.cache_resource
def load_clients():
    stt = STTClient(config.get("stt"))
    llm = LLMClient(config.get("text"))
    tts = TTSClient(config.get("audio"))
    return stt, llm, tts

stt_client, llm_client, tts_client = load_clients()

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

# ── Chat text input ─────────────────────────────────────────────────
user_prompt_text = st.chat_input("Send a message…")

# ── Audio input ─────────────────────────────────────────────────────
audio_value = st.audio_input(
    "Or record a voice message",
    key=f"audio_{st.session_state.audio_key}",
)

if not user_prompt_text and audio_value:
    with st.spinner("Transcribing…"):
        user_prompt_text = stt_client(audio_value)
    st.session_state.audio_key += 1

# ── Process prompt ──────────────────────────────────────────────────
if user_prompt_text:
    st.session_state.messages.append({"role": "user", "content": user_prompt_text})

    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_prompt_text)

        # ── Stream LLM response ────────────────────────────────────
        with st.chat_message("assistant"):
            stream, language = llm_client(user_prompt_text)
            full_response = st.write_stream(stream)

    # ── Generate TTS audio ─────────────────────────────────────────
    with st.spinner("Generating speech…"):
        split_pattern = re.compile(r'(?<=[.?!,;:\n])\s+')
        sentences = [s.strip() for s in split_pattern.split(full_response) if s.strip()]
        print(language)
        audio_buffer = io.BytesIO()
        for phrase_stream in tts_client(iter(sentences), language=language):
            for chunk in phrase_stream:
                if isinstance(chunk, (bytes, bytearray)) and chunk:
                    audio_buffer.write(chunk)

        audio_bytes = audio_buffer.getvalue()

    # ── Play audio ─────────────────────────────────────────────────
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mpeg", autoplay=True)

    # ── Store assistant message ─────────────────────────────────────
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "audio": audio_bytes if audio_bytes else None,
    })
