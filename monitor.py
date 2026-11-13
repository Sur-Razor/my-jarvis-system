import json
import os
import subprocess
import urllib.parse
import requests

CHANNEL_URL = "https://www.youtube.com/@Sur-Razor"
GROQ_KEY = os.environ["GROQ_API_KEY"]
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]
TG_USERNAME = os.environ["TG_USERNAME"]


def get_latest_videos():
  cmd = [
      "yt-dlp",
      "--flat-playlist",
      "--dump-single-json",
      "--playlist-end",
      "5",
      CHANNEL_URL,
  ]
  res = subprocess.run(cmd, capture_output=True, text=True)
  data = json.loads(res.stdout)
  videos = {}
  for entry in data.get("entries", []):
    vid_id = entry.get("id")
    videos[vid_id] = {
        "title": entry.get("title"),
        "views": entry.get("view_count") or 0,
    }
  return videos


def ask_jarvis(prompt):
  url = "https://groq.com"
  headers = {"Authorization": f"Bearer {GROQ_KEY}"}
  payload = {
      "model": "llama-3.3-70b-versatile",
      "messages": [
          {
              "role": "system",
              "content": (
                  "You are J.A.R.V.I.S. Be concise, polite, and address the"
                  " user as Sir. Keep responses under 3 sentences."
              ),
          },
          {"role": "user", "content": prompt},
      ],
  }
  r = requests.post(url, headers=headers, json=payload).json()
  return r["choices"][0]["message"]["content"]


def send_telegram_text(msg):
  url = f"https://telegram.org{TG_TOKEN}/sendMessage"
  requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg})


def call_telegram_phone(spoken_msg):
  encoded = urllib.parse.quote(spoken_msg)
  url = f"http://callmebot.com{TG_USERNAME}&text={encoded}&lang=en-GB-Standard-B"
  requests.get(url)


def main():
  with open("stats.json", "r") as f:
    old_stats = json.load(f)

  current_stats = get_latest_videos()
  updates = []
  urgent_spike = False

  for vid_id, info in current_stats.items():
    old_views = old_stats.get(vid_id, {}).get("views", 0)
    diff = info["views"] - old_views
    if diff > 0:
      updates.append(
          f"'{info['title']}' gained {diff} views (Total: {info['views']})."
      )
    if diff >= 100:  # Triggers a phone call if a video jumps by 100+ views
      urgent_spike = True

  if updates:
    summary = ask_jarvis(f"Summarize these YouTube updates: {' '.join(updates)}")
    send_telegram_text(f"🤖 J.A.R.V.I.S. Update:\n{summary}")
    if urgent_spike:
      call_telegram_phone(summary)

  with open("stats.json", "w") as f:
    json.dump(current_stats, f, indent=2)


if __name__ == "__main__":
  main()
