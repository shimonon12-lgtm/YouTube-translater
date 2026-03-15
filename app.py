import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.set_page_config(page_title="YouTube Translator", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f0f0f;
        color: #f1f1f1;
    }
    .main { background-color: #0f0f0f; }
    .block-container { padding-top: 2rem; max-width: 860px; }
    h1 {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ff4e4e, #ff9a3c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        color: #aaa;
        font-size: 0.95rem;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
    }
    .stTextInput > div > div > input {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 8px;
        color: #f1f1f1;
        padding: 0.6rem 1rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #ff4e4e, #ff9a3c);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
    .minute-header {
        color: #ff7043;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-top: 1.5rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .minute-divider {
        border: none;
        border-top: 1px solid #2a2a2a;
        margin: 0.2rem 0 0.8rem 0;
    }
    .translation-block {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        color: #e0e0e0;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .full-translation {
        background-color: #1a1a1a;
        border-radius: 10px;
        padding: 1.5rem;
        line-height: 1.8;
        color: #e0e0e0;
        font-size: 0.95rem;
    }
    .stDownloadButton > button {
        background-color: #1e1e1e;
        border: 1px solid #444;
        color: #ccc;
        border-radius: 8px;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] { color: #aaa; font-weight: 600; }
    .stTabs [aria-selected="true"] {
        color: #ff7043;
        border-bottom: 2px solid #ff7043;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🎬 YouTube Translator")
st.markdown('<p class="subtitle">Translate English YouTube videos into Japanese — full transcript.</p>', unsafe_allow_html=True)

with st.expander("⚙️ Settings", expanded=True):
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

def group_by_minute(transcript):
    groups = {}
    for t in transcript:
        minute = int(t.start // 60)
        if minute not in groups:
            groups[minute] = []
        groups[minute].append(t.text)
    return groups

if st.button("🚀 Translate"):
    if not api_key:
        st.error("Please enter your API key.")
    elif not url:
        st.error("Please enter a YouTube URL.")
    else:
        video_id = get_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL.")
        else:
            with st.spinner("Fetching transcript..."):
                try:
                    ytt = YouTubeTranscriptApi()
                    transcript = ytt.fetch(video_id)
                except Exception as e:
                    st.error(f"Failed to fetch transcript: {e}")
                    st.stop()

            client = genai.Client(api_key=api_key)
            full_text = " ".join([t.text for t in transcript])
            minute_groups = group_by_minute(transcript)

            # Translate all segments in a single API call
            with st.spinner("Translating..."):
                combined = ""
                for minute in sorted(minute_groups.keys()):
                    chunk = " ".join(minute_groups[minute])
                    combined += f"[{minute}min]\n{chunk}\n\n"

                prompt = f"""Below is an English YouTube transcript, divided into segments tagged [Nmin].
Translate each segment into natural Japanese.
Follow these rules strictly:

1. Keep the [Nmin] tag at the start of each segment
2. Write the translation on a new line immediately after the tag
3. If the speaker changes, prefix with the speaker name like [Speaker A] or [Speaker B] (use their real name if known)
4. Do not repeat the speaker tag if the same speaker continues
5. No extra commentary or annotations

Transcript:
{combined}"""

                try:
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt
                    )
                    translated_full = response.text.strip()
                except Exception as e:
                    st.error(f"Translation failed: {e}")
                    st.stop()

            # Parse results
            import re
            sections = re.split(r'(\[\d+min\])', translated_full)

            tab1, tab2 = st.tabs(["🕐 Timetable", "📄 Full Translation"])

            with tab1:
                st.markdown("### Minute-by-minute translation")
                i = 1
                while i < len(sections) - 1:
                    label = sections[i]
                    text = sections[i + 1].strip() if i + 1 < len(sections) else ""
                    st.markdown(f'<div class="minute-header">⏱ {label}</div><hr class="minute-divider">', unsafe_allow_html=True)
                    st.markdown(f'<div class="translation-block">{text}</div>', unsafe_allow_html=True)
                    i += 2
                st.success("Timetable ready!")
            with tab2:
                import re
                full_translated = re.sub(r'\[\d+min\]', '', translated_full)
                # Line break before speaker tags
                full_translated = re.sub(r'(\[.+?\])', r'<br><br>\1', full_translated)
                # Line break after sentence-ending punctuation
                full_translated = re.sub(r'([。？！])\s*', r'\1<br>', full_translated)
                full_translated = full_translated.strip()

                st.markdown(f'<div class="full-translation">{full_translated}</div>', unsafe_allow_html=True)
                st.download_button(
                    label="📥 Save as text file",
                    data=re.sub(r'<br>', '\n', full_translated),
                    file_name="translation.txt",
                    mime="text/plain"
                )
                )
