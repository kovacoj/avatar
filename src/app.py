import streamlit as st

from src.orchestration import get_chat_controller

# Initialize the page
st.set_page_config(page_title="Phonagnosia", layout="centered")

chat = get_chat_controller()

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
            user_prompt_text = chat.transcribe_audio(audio_value)
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
                Consumes streamed backend response
                and yields only text for st.write_stream.
                """
                async for chunk, lang in chat.stream_response(user_prompt_text):
                    runtime_data["lang"] = lang
                    yield chunk

            # Streamlit 1.40+ natively handles async generators
            full_response = st.write_stream(text_stream_wrapper())

    # ── TTS Generation ──
    audio_bytes = None
    if full_response:
        with st.spinner("Generating speech…"):
            try:
                audio_bytes = chat.synthesize_speech(full_response, runtime_data["lang"])
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
