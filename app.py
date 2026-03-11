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
st.markdown('<p class="subtitle">英語のYouTube動画を日本語に全文翻訳します</p>', unsafe_allow_html=True)

with st.expander("⚙️ 設定", expanded=True):
    api_key = st.text_input("Gemini APIキー", type="password", placeholder="AIza...")
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

if st.button("🚀 翻訳する"):
    if not api_key:
        st.error("APIキーを入力してください")
    elif not url:
        st.error("URLを入力してください")
    else:
        video_id = get_video_id(url)
        if not video_id:
            st.error("URLが正しくないです")
        else:
            with st.spinner("字幕を取得中..."):
                try:
                    ytt = YouTubeTranscriptApi()
                    transcript = ytt.fetch(video_id)
                except Exception as e:
                    st.error(f"字幕の取得に失敗しました：{e}")
                    st.stop()

            client = genai.Client(api_key=api_key)
            full_text = " ".join([t.text for t in transcript])
            minute_groups = group_by_minute(transcript)

            # 1回のAPIで全分まとめて翻訳
            with st.spinner("翻訳中..."):
                combined = ""
                for minute in sorted(minute_groups.keys()):
                    chunk = " ".join(minute_groups[minute])
                    combined += f"[{minute}分]\n{chunk}\n\n"

                prompt = f"""以下はYouTube動画の英語字幕です。[N分]というタグごとに区切られています。
各区間を自然な日本語に翻訳してください。
以下のルールを必ず守ってください：

1. 各区間の先頭に [N分] タグをそのまま残す
2. タグの直後に改行して翻訳文を書く
3. 話者が変わる場合は「【話者A】」「【話者B】」のように話者名を付ける（名前がわかる場合はその名前を使う）
4. 同じ話者が続く場合はタグを繰り返さない
5. 余計な説明や注釈は不要

字幕：
{combined}"""

                try:
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt
                    )
                    translated_full = response.text.strip()
                except Exception as e:
                    st.error(f"翻訳に失敗しました：{e}")
                    st.stop()

            # 結果をパース
            import re
            sections = re.split(r'(\[\d+分\])', translated_full)

            tab1, tab2 = st.tabs(["🕐 タイムテーブル", "📄 全文翻訳"])

            with tab1:
                st.markdown("### 分ごとの翻訳")
                i = 1
                while i < len(sections) - 1:
                    label = sections[i]
                    text = sections[i + 1].strip() if i + 1 < len(sections) else ""
                    st.markdown(f'<div class="minute-header">⏱ {label}</div><hr class="minute-divider">', unsafe_allow_html=True)
                    st.markdown(f'<div class="translation-block">{text}</div>', unsafe_allow_html=True)
                    i += 2
                st.success("タイムテーブル完成！")
            with tab2:
                import re
                full_translated = re.sub(r'\[\d+分\]', '', translated_full)
                # 話者タグの前で改行を入れる
                full_translated = re.sub(r'(【.+?】)', r'<br><br>\1', full_translated)
                # 句点や？！の後で改行
                full_translated = re.sub(r'([。？！])\s*', r'\1<br>', full_translated)
                full_translated = full_translated.strip()

                st.markdown(f'<div class="full-translation">{full_translated}</div>', unsafe_allow_html=True)
                st.download_button(
                    label="📥 テキストファイルで保存",
                    data=re.sub(r'<br>', '\n', full_translated),
                    file_name="translation.txt",
                    mime="text/plain"
                )