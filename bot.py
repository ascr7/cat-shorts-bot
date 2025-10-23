import os
import json
import time
from datetime import datetime, timedelta, timezone
import requests
from yt_dlp import YoutubeDL

# Config from environment variables (set these in GitHub Secrets or environment)
YT_API_KEY = os.getenv("YT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # numeric chat id (private user id)
SEARCH_TERMS = ["cat", "meow", "گربه", "میو"]
LIKE_THRESHOLD = int(os.getenv("LIKE_THRESHOLD", "200000"))
SENT_DB_PATH = "sent_videos.json"
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def load_sent_db():
    if os.path.exists(SENT_DB_PATH):
        with open(SENT_DB_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_sent_db(db):
    with open(SENT_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def search_recent_videos():
    # search in last 24 hours
    now = datetime.now(timezone.utc)
    published_after = (now - timedelta(days=1)).isoformat()
    found = []
    for term in SEARCH_TERMS:
        params = {
            "key": YT_API_KEY,
            "q": term,
            "part": "snippet",
            "type": "video",
            "maxResults": 25,
            "order": "date",
            "publishedAfter": published_after,
        }
        r = requests.get(YT_SEARCH_URL, params=params, timeout=30)
        r.raise_for_status()
        items = r.json().get("items", [])
        for it in items:
            video_id = it["id"]["videoId"]
            snippet = it["snippet"]
            found.append({"videoId": video_id, "title": snippet.get("title",""), "publishedAt": snippet.get("publishedAt")})
    # dedupe by id preserving order
    seen = set()
    uniq = []
    for f in found:
        if f["videoId"] not in seen:
            seen.add(f["videoId"])
            uniq.append(f)
    return uniq

def get_video_stats(video_ids):
    results = {}
    if not video_ids:
        return results
    params = {
        "key": YT_API_KEY,
        "id": ",".join(video_ids),
        "part": "statistics,snippet,contentDetails"
    }
    r = requests.get(YT_VIDEOS_URL, params=params, timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    for it in items:
        vid = it["id"]
        stats = it.get("statistics", {})
        snippet = it.get("snippet", {})
        content = it.get("contentDetails", {})
        results[vid] = {
            "title": snippet.get("title"),
            "likeCount": int(stats.get("likeCount", 0)),
            "viewCount": int(stats.get("viewCount", 0)),
            "duration": content.get("duration"),
            "publishedAt": snippet.get("publishedAt")
        }
    return results

def download_video(video_url, outdir):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": os.path.join(outdir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)
        # ensure .mp4 extension after merge
        if not filename.endswith(".mp4"):
            base = os.path.splitext(filename)[0]
            filename = base + ".mp4"
        return filename

def send_video_to_telegram(file_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(file_path, "rb") as f:
        files = {"video": f}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
        r = requests.post(url, data=data, files=files, timeout=120)
    r.raise_for_status()
    return r.json()

def main():
    if not YT_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing required environment variables. Set YT_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.")
        return

    sent_db = load_sent_db()
    recent = search_recent_videos()
    ids = [r["videoId"] for r in recent]
    stats = get_video_stats(ids)

    to_send = []
    for r in recent:
        vid = r["videoId"]
        st = stats.get(vid)
        if not st:
            continue
        # filter like count and not already sent
        if st["likeCount"] >= LIKE_THRESHOLD and vid not in sent_db:
            to_send.append((vid, st))

    if not to_send:
        print("No new qualifying videos to send.")
        return

    for vid, st in to_send:
        url = f"https://www.youtube.com/watch?v={vid}"
        title = st.get("title","")
        try:
            print(f"Downloading {vid} - {title}")
            file_path = download_video(url, DOWNLOAD_DIR)
            caption = f"{title}\n❤️ {st.get('likeCount')} likes — https://youtu.be/{vid}"
            print(f"Sending {file_path} to Telegram")
            send_video_to_telegram(file_path, caption=caption)
            sent_db.append(vid)
            save_sent_db(sent_db)
            # small pause between sends
            time.sleep(3)
        except Exception as e:
            print(f"Error handling {vid}: {e}")
            continue

if __name__ == '__main__':
    main()
