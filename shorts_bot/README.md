# 🤖 YouTube Shorts Finance Bot

Fully automated system that:
1. **Detects** trending finance topics (Google Trends + Reddit)
2. **Writes** a punchy 55-second script using Claude AI
3. **Generates** Indian English voiceover (FREE — no API key)
4. **Downloads** relevant stock footage from Pexels (FREE)
5. **Assembles** the video with auto-captions
6. **Uploads** to YouTube on a schedule (7 AM & 7 PM IST)

**Cost: ₹200–800/month** (mostly Claude API — ~₹0.10/script)

---

## 📋 What You Need

| Tool | Cost | What for |
|------|------|---------|
| Claude API | ~₹0.10/script | Script writing |
| Pexels API | FREE | Stock videos |
| Google Cloud | FREE | YouTube upload |
| GitHub | FREE | Auto-scheduling |
| edge-tts | FREE | Voiceover |

---

## ⚡ Quick Setup (Step by Step)

### Step 1: Get API Keys

**Claude API (₹ paid — ~₹500 lasts 2-3 months):**
1. Go to https://console.anthropic.com
2. Sign up → Billing → Add ₹500
3. API Keys → Create Key → Copy it

**Pexels API (FREE):**
1. Go to https://www.pexels.com/api/
2. Sign up → Your Email → API Key → Copy it

**YouTube API (FREE):**
1. Go to https://console.cloud.google.com
2. New Project → name it "ShortsBot"
3. APIs & Services → Enable → search "YouTube Data API v3" → Enable
4. APIs & Services → Credentials → Create → OAuth 2.0 Client ID
5. Application type: Desktop App → Create → Download JSON
6. Save the downloaded file as `client_secret.json` in this folder

---

### Step 2: Install on Your Computer

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/shorts-bot.git
cd shorts-bot

# Install Python 3.11+
# Windows: https://www.python.org/downloads/
# Mac: brew install python@3.11
# Linux: sudo apt install python3.11

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (needed for video)
# Windows: https://ffmpeg.org/download.html → add to PATH
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

---

### Step 3: Configure

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your keys
nano .env   # or open in any text editor
```

Fill in:
```
CLAUDE_API_KEY=sk-ant-api03-...
PEXELS_API_KEY=...
```

---

### Step 4: Authenticate YouTube (One-time)

```bash
python modules/youtube_uploader.py --auth
```

A browser window will open → sign in to your YouTube channel → allow permissions.
A `token.json` file will be saved. **Keep this safe — don't share it.**

---

### Step 5: Test Run

```bash
# Dry run (just generate script, no video) — FREE
python main.py --dry-run

# Make one video but don't upload
python main.py --count 1 --no-upload

# Full run (make + upload to YouTube)
python main.py --count 1

# Make video on a specific topic
python main.py --topic "how to start SIP with 500 rupees"
```

---

## 🚀 Automate with GitHub Actions (Free Cloud Scheduling)

This runs the bot automatically twice a day — no computer needed.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/shorts-bot.git
git push -u origin main
```

### Step 2: Add GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Value |
|-------------|-------|
| `CLAUDE_API_KEY` | Your Claude API key |
| `PEXELS_API_KEY` | Your Pexels API key |
| `YOUTUBE_CLIENT_SECRET_JSON` | Contents of client_secret.json (paste the whole file) |
| `YOUTUBE_TOKEN_JSON` | Contents of token.json (paste the whole file) |

### Step 3: Enable Actions

Go to your repo → Actions → Enable workflows

The bot now runs automatically:
- **7:00 AM IST** — posts morning Short
- **7:00 PM IST** — posts evening Short

You can also trigger manually: Actions → Daily YouTube Shorts → Run workflow

---

## 📁 Project Structure

```
shorts-bot/
├── main.py                    ← Master orchestrator (run this)
├── config.py                  ← All settings (niche, voice, timing)
├── requirements.txt
├── .env                       ← Your API keys (never commit this)
├── client_secret.json         ← YouTube OAuth (never commit this)
├── token.json                 ← YouTube token (never commit this)
├── modules/
│   ├── trend_detector.py      ← Google Trends + Reddit
│   ├── script_generator.py    ← Claude AI script writing
│   ├── voice_generator.py     ← edge-tts voiceover
│   ├── visual_sourcer.py      ← Pexels video download
│   ├── video_assembler.py     ← MoviePy video assembly
│   ├── thumbnail_generator.py ← Pillow thumbnail
│   └── youtube_uploader.py    ← YouTube Data API upload
├── output/                    ← Generated videos (auto-created)
│   └── 20240115_070000/
│       ├── script.json
│       ├── voice.mp3
│       ├── short.mp4
│       ├── thumbnail.jpg
│       └── result.json
├── .github/
│   └── workflows/
│       └── daily_shorts.yml   ← GitHub Actions schedule
└── pipeline.log               ← Run history
```

---

## ⚙️ Customisation

### Change voice accent:
In `config.py`:
```python
VOICE_NAME = "en-IN-NeerjaNeural"   # Indian English female
VOICE_NAME = "en-IN-PrabhatNeural"  # Indian English male
VOICE_NAME = "en-US-JennyNeural"    # US English female
```

### Change topics:
Edit `FINANCE_TOPICS` list in `config.py` — add any topics you want.

### Change posting frequency:
Edit `.github/workflows/daily_shorts.yml` cron schedule.
- `"30 1 * * *"` = 7:00 AM IST daily
- `"30 13 * * *"` = 7:00 PM IST daily

---

## 💰 Monthly Cost Estimate

| Item | Usage | Cost |
|------|-------|------|
| Claude haiku | 60 scripts/month | ~₹300 |
| Pexels API | Unlimited | ₹0 |
| edge-tts | Unlimited | ₹0 |
| GitHub Actions | 2000 min free | ₹0 |
| YouTube API | Free quota | ₹0 |
| **Total** | **60 videos/month** | **~₹300** |

---

## ❓ Troubleshooting

**"No module named moviepy"**
→ `pip install moviepy`

**"ffmpeg not found"**
→ Install FFmpeg and add to PATH

**"YouTube token expired"**
→ Run `python modules/youtube_uploader.py --auth` again

**"Pexels 401 Unauthorized"**
→ Check PEXELS_API_KEY in .env

**Video is black/no background**
→ Check internet connection (Pexels download might have failed)

---

## ⚠️ Important Notes

- All stock footage is from Pexels — royalty-free, safe for YouTube
- Scripts are original (AI-generated) — no copyright issues
- Never reupload someone else's video — instant strikes
- Don't spam — 2 videos/day max for a new channel
- Be patient — new channels take 2-3 months to grow

---

*Built for Indian finance content creators. Good luck! 🚀*
