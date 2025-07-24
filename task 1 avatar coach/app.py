import streamlit as st
from crm import CoachingCRM
from elevenlabs.client import ElevenLabs
import os
import requests
import uuid
import time
import asyncio
from dotenv import load_dotenv
from st_audiorec import st_audiorec
import io
import hashlib
import base64
from coach_logic import get_coaching_response

# --- Page Configuration ---
st.set_page_config(page_title="AI Avatar Coach", page_icon="🤖", layout="centered")
st.title("🤖 AI Avatar Coach")

# --- Load API Keys & Initialize Clients ---
load_dotenv()
DID_API_KEY = os.getenv("DID_API_KEY")

if not DID_API_KEY:
    st.error("❌ DID_API_KEY not found in .env file! Get one at https://studio.d-id.com/")
    st.stop()

def get_elevenlabs_client():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key: st.error("ELEVENLABS_API_KEY not found.")
    return ElevenLabs(api_key=api_key)
elevenlabs_client = get_elevenlabs_client()

# --- D-ID API Functions ---
DID_API_URL = "https://api.d-id.com"

def create_did_talk_video(text_to_speak: str):
    """Create a talking avatar video using D-ID API"""

    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "script": {
            "type": "text",
            "input": text_to_speak,
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            }
        },
        "config": {
            "fluent": True,
            "stitch": True
        },
        "source_url": "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg"
    }

    try:
        with st.status("Creating D-ID talk video...", expanded=True) as status:
            response = requests.post(
                f"{DID_API_URL}/talks",
                headers=headers,
                json=payload
            )

        if response.status_code != 201:
            st.error(f"D-ID Error ({response.status_code}): {response.text}")
            return None

        talk_data = response.json()
        talk_id = talk_data.get("id")

        if not talk_id:
            st.error("No talk ID received from D-ID")
            return None

        st.success(f"✅ Talk created with ID: {talk_id}")

        return poll_did_video_status(talk_id, headers)

    except Exception as e:
        st.error(f"Error creating D-ID video: {str(e)}")
        return None

def poll_did_video_status(talk_id: str, headers: dict):
    """
    Poll D-ID API for video completion
    """

    max_attempts = 60
    attempt = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    while attempt < max_attempts:
        try:
            response = requests.get(
                f"{DID_API_URL}/talks/{talk_id}",
                headers=headers
            )

            if response.status_code != 200:
                st.error(f"Status check failed: {response.status_code}")
                return None

            data = response.json()
            status = data.get("status")

            status_text.text(f"Status: {status} (Attempt {attempt + 1}/{max_attempts})")
            progress_bar.progress((attempt + 1) / max_attempts)

            if status == "done":
                video_url = data.get("result_url")
                st.success("✅ Video ready!")
                progress_bar.empty()
                status_text.empty()
                return video_url

            elif status == "error" or status == "rejected":
                error_msg = data.get("error", {}).get("description", "Unknown error")
                st.error(f"❌ Video generation failed: {error_msg}")
                progress_bar.empty()
                status_text.empty()
                return None

            else:
                time.sleep(5)
                attempt += 1

        except Exception as e:
            st.error(f"Error checking status: {e}")
            progress_bar.empty()
            status_text.empty()
            return None

    st.error("⏱️ Timeout: Video generation took too long")
    progress_bar.empty()
    status_text.empty()
    return None

# --- Test for D-ID API connection ---
def test_did_connection():
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{DID_API_URL}/credits",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            remaining = data.get("remaining", 0)
            total = data.get("total", 0)
            st.sidebar.success(f"✅ D-ID Connected! Credits: {remaining}/{total}")
            return True
        else:
            st.sidebar.error(f"❌ D-ID Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.sidebar.error(f"❌ Connection Error: {str(e)}")
        return False

# --- Sidebar ---
with st.sidebar:
    st.header("🔧 Settings")

    if st.button("Test D-ID Connection"):
        test_did_connection()

    # Avatar settings
    use_avatar = st.checkbox("Use Avatar Videos", value=True)

    # Voice settings
    voice_provider = st.selectbox(
        "Voice Provider",
        ["ElevenLabs", "D-ID Microsoft", "D-ID Amazon"]
    )

    st.markdown("---")
    st.markdown("[Get D-ID API Key](https://studio.d-id.com/)")
    st.markdown("[D-ID Documentation](https://docs.d-id.com/)")

# --- Session State Management ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I am your AI Coach. How can I help you reflect today?", "type": "text"}
    ]
if 'user_id' not in st.session_state:
    user_id = asyncio.run(CoachingCRM.create_user(email="test.user@streamlit.app", name="Test User"))
    st.session_state.user_id = user_id
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "processed_audio_hashes" not in st.session_state:
    st.session_state.processed_audio_hashes = set()
if "generating_video" not in st.session_state:
    st.session_state.generating_video = False
if "text_for_video" not in st.session_state:
    st.session_state.text_for_video = None

# --- Core AI Response Function ---
async def process_user_input_async(user_input):
    """
    Gets AI response, logs it, and triggers video generation
    """
    st.session_state.chat_history.append({"role": "user", "content": user_input, "type": "text"})

    with st.spinner("The AI coach is thinking..."):
        ai_response_text, knowledge_context = get_coaching_response(user_input, st.session_state.chat_history)

        await CoachingCRM.log_conversation(st.session_state.user_id, st.session_state.session_id, "user", user_input)
        await CoachingCRM.log_conversation(st.session_state.user_id, st.session_state.session_id, "assistant", ai_response_text)

        st.session_state.text_for_video = ai_response_text
        st.session_state.generating_video = True

# --- Video Generation ---
if st.session_state.generating_video and st.session_state.text_for_video:
    with st.container():
        if use_avatar:
            st.info("🎬 Generating avatar video with D-ID...")
            video_url = create_did_talk_video(st.session_state.text_for_video)
        else:
            video_url = None

        if video_url:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": video_url,
                "type": "video",
                "text": st.session_state.text_for_video
            })
        else:
            st.warning("Using audio response (avatar generation failed or disabled)")

            try:
                if voice_provider == "ElevenLabs":
                    audio_response = elevenlabs_client.text_to_speech.generate(
                        text=st.session_state.text_for_video,
                        voice="Rachel",
                        model="eleven_multilingual_v2"
                    )

                    audio_path = f"audio_{len(st.session_state.chat_history)}.mp3"
                    with open(audio_path, 'wb') as f:
                        f.write(audio_response)
                else:
                    audio_path = None

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": st.session_state.text_for_video,
                    "type": "text_with_audio" if audio_path else "text",
                    "audio_path": audio_path
                })
            except Exception as e:
                st.error(f"Audio generation failed: {e}")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": st.session_state.text_for_video,
                    "type": "text"
                })

        st.session_state.generating_video = False
        st.session_state.text_for_video = None
        st.rerun()

for i, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        if message.get("type") == "video":
            st.video(message["content"])
            with st.expander("View transcript"):
                st.write(message.get("text", ""))
        elif message.get("type") == "text_with_audio":
            st.write(message["content"])
            if message.get("audio_path"):
                st.audio(message.get("audio_path"))
        else:
            st.write(message["content"])

if st.session_state.generating_video and st.session_state.text_for_video:
    generation_container = st.container()

    with generation_container:
        if use_avatar:
            st.info("🎬 Generating avatar video with D-ID...")
            video_url = create_did_talk_video(st.session_state.text_for_video)
        else:
            video_url = None

# --- Custom CSS for better styling ---
st.markdown("""
<style>
    /* Fix the audio recorder without inverting */
    iframe[title="st_audiorec.st_audiorec"] {
        background-color: #262730 !important;
        border: 2px solid #4a4a4a !important;
        border-radius: 8px !important;
        min-height: 80px !important;
        opacity: 1 !important;
    }
    
    /* Make sure the recorder stays visible */
    .stAudioRec, .st-audiorec {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Make videos responsive */
    video {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- Input Handling ---
st.write("--- Speak to the Coach ---")

if "recorder_key" not in st.session_state:
    st.session_state.recorder_key = 0

recorder_container = st.container()
with recorder_container:
    wav_audio_data = st_audiorec()

if wav_audio_data:
    audio_hash = hashlib.md5(wav_audio_data).hexdigest()
    if audio_hash not in st.session_state.processed_audio_hashes:
        st.session_state.processed_audio_hashes.add(audio_hash)
        with st.spinner("Transcribing..."):
            try:
                audio_buffer = io.BytesIO(wav_audio_data)
                transcription_object = elevenlabs_client.speech_to_text.convert(
                    file=audio_buffer,
                    model_id="scribe_v1"
                )
                user_text = transcription_object.text.strip()
                if user_text:
                    st.info(f"Heard you say: '{user_text}'")
                    asyncio.run(process_user_input_async(user_text))
                    st.rerun()
            except Exception as e:
                st.error(f"Transcription failed: {e}")

if prompt := st.chat_input("Type your message here..."):
    asyncio.run(process_user_input_async(prompt))
    st.rerun()