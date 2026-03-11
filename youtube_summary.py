from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

# APIキー
API_KEY = "AIzaSyBECPTlBC4s7etK8l6fItW2a7HkH7uKTdI"

# Geminiの設定
client = genai.Client(api_key=API_KEY)

# YouTubeのURLからIDを取り出す関数
def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return None

# メイン処理
def translate_youtube(url):
    video_id = get_video_id(url)
    if not video_id:
        print("URLが正しくないです")
        return

    print("字幕を取得中...")
    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(video_id)
    full_text = " ".join([t.text for t in transcript])

    print("Geminiが翻訳中...")
    prompt = f"""
以下はYouTube動画の英語字幕です。
日本語に自然な文章として全文翻訳してください。
字幕の時間情報は不要です。話し言葉を自然な日本語にしてください。翻訳した文章のみ出力してください。

字幕：
{full_text}
"""
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )
    print("\n========== 翻訳結果 ==========")
    print(response.text)

# 実行
url = input("YouTubeのURLを入力してください：")
translate_youtube(url)