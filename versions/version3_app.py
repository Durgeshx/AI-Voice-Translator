import streamlit as st

st.set_page_config(
    page_title="AI Translator",
    layout="wide"
)

st.title("🎤 Live AI Conversation Translator")

language = st.selectbox(
    "Target Language",
    ["hi", "es", "fr"]
)

if "history" not in st.session_state:
    st.session_state.history = []

if st.button("Start Recording"):

    st.session_state.history.append(
        (
            "SPEAKER_00",
            "Hello how are you?",
            "नमस्ते आप कैसे हैं?"
        )
    )

    st.session_state.history.append(
        (
            "SPEAKER_01",
            "I am fine",
            "मैं ठीक हूँ"
        )
    )

for speaker, english, translated in st.session_state.history:

    if speaker == "SPEAKER_00":

        st.markdown(
            f"""
            <div style="
            background:#dbeafe;
            padding:10px;
            border-radius:10px;
            margin-bottom:10px;">
            <b>{speaker}</b><br>
            English: {english}<br>
            Translation: {translated}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div style="
            background:#dcfce7;
            padding:10px;
            border-radius:10px;
            margin-bottom:10px;">
            <b>{speaker}</b><br>
            English: {english}<br>
            Translation: {translated}
            </div>
            """,
            unsafe_allow_html=True
        )