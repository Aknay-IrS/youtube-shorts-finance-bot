import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys (set these in .env) ──────────────────────────────────────────────
CLAUDE_API_KEY      = os.getenv("CLAUDE_API_KEY", "")
YOUTUBE_CLIENT_FILE = os.getenv("YOUTUBE_CLIENT_FILE", "client_secret.json")
PEXELS_API_KEY      = os.getenv("PEXELS_API_KEY", "aWfRW3CjhYB8j0iPHXUTB7lw1zRZpndnbeTWeZxqgHZtSOQ4ORYEaXC6")
PIXABAY_API_KEY     = os.getenv("PIXABAY_API_KEY", "55951851-7282cb13bfe0431ff6400f2a0")

# ── Channel Settings ──────────────────────────────────────────────────────────
NICHE               = "finance and money tips India"
VIDEOS_PER_RUN      = 2          # How many Shorts to make per run
TARGET_AUDIENCE     = "Indian young adults aged 18-35 learning about personal finance"

# ── Video Settings ────────────────────────────────────────────────────────────
VIDEO_WIDTH         = 1080
VIDEO_HEIGHT        = 1920
VIDEO_FPS           = 30
VIDEO_DURATION_MAX  = 58         # seconds (keep under 60 for Shorts)
VIDEO_BITRATE       = "4000k"

# ── Voice Settings (edge-tts — completely FREE) ───────────────────────────────
# Options: en-IN-NeerjaNeural (female), en-IN-PrabhatNeural (male)
VOICE_NAME          = "en-IN-NeerjaNeural"
VOICE_RATE          = "+5%"      # slightly faster for Shorts energy
VOICE_PITCH         = "+0Hz"

# ── Text Overlay Settings ─────────────────────────────────────────────────────
FONT_SIZE_CAPTION   = 80
FONT_COLOR          = "white"
CAPTION_STROKE      = 4          # outline thickness for readability
CAPTION_MAX_WORDS   = 4          # words shown at a time (caption style)

# ── YouTube Upload Settings ───────────────────────────────────────────────────
# Best times to post for Indian audience (IST)
UPLOAD_TIMES        = ["07:00", "19:00"]
YT_CATEGORY_ID      = "22"       # People & Blogs
YT_PRIVACY          = "public"   # public / private / unlisted
YT_MADE_FOR_KIDS    = False
YT_SHORTS_TAG       = "#Shorts #MoneyTips #PersonalFinance #India"

# ── Claude Model ──────────────────────────────────────────────────────────────
CLAUDE_MODEL        = "claude-haiku-4-5-20251001"   # cheapest — ~₹0.10 per script

# ── Pexels ────────────────────────────────────────────────────────────────────
PEXELS_PER_VIDEO    = 5          # clips to download per video

# ── Finance topics to cycle through ──────────────────────────────────────────
FINANCE_TOPICS = [
    "SIP mutual funds beginner India",
    "how to save money on salary India",
    "credit card mistakes India",
    "emergency fund how to build",
    "PPF vs FD which is better",
    "stock market basics for beginners India",
    "how to reduce income tax India",
    "UPI cashback tricks India",
    "gold vs stocks which is better",
    "how to get out of debt fast India",
    "term insurance why important",
    "NPS national pension scheme benefits",
    "how to budget on low salary",
    "index funds vs active funds India",
    "EPFO EPF account tricks",
]
