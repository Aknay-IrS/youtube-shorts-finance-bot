"""
youtube_uploader.py
Uploads the rendered Short to YouTube using the Data API v3.
Handles OAuth2 authentication with token refresh.

Setup (one-time):
  1. Go to console.cloud.google.com
  2. Create project → Enable YouTube Data API v3
  3. OAuth2 credentials → Download client_secret.json
  4. Run: python modules/youtube_uploader.py --auth
  5. Paste the token.json path in .env
"""

import argparse
import json
import logging
import os
import pathlib
import pickle
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config

log = logging.getLogger(__name__)

SCOPES          = ["https://www.googleapis.com/auth/youtube.upload",
                   "https://www.googleapis.com/auth/youtube"]
TOKEN_FILE      = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "token.json")
IST             = ZoneInfo("Asia/Kolkata")


def get_authenticated_service():
    """Get or refresh YouTube API credentials."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing YouTube token...")
            creds.refresh(Request())
        else:
            log.info("Starting YouTube OAuth2 flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                config.YOUTUBE_CLIENT_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        log.info("Token saved to token.json")

    return build("youtube", "v3", credentials=creds)


def get_next_upload_time() -> str:
    """
    Returns the next scheduled upload time in ISO 8601 format.
    Posts at 7 AM or 7 PM IST — whichever is next.
    """
    now = datetime.now(IST)
    upload_hours = [7, 19]

    for hour in sorted(upload_hours):
        scheduled = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if scheduled > now + timedelta(minutes=5):
            return scheduled.isoformat()

    # Both times passed today — schedule for 7 AM tomorrow
    tomorrow = now + timedelta(days=1)
    scheduled = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
    return scheduled.isoformat()


def upload_short(
    video_path:  str,
    title:       str,
    description: str,
    tags:        list[str],
    scheduled:   bool = True,
) -> str | None:
    """
    Upload a Short to YouTube.
    Returns video_id on success, None on failure.
    """
    try:
        youtube = get_authenticated_service()

        # Build description with standard footer
        full_description = (
            f"{description}\n\n"
            f"{'─' * 30}\n"
            f"💰 Finance tips for India every day\n"
            f"🔔 Subscribe for daily money tips\n\n"
            f"{config.YT_SHORTS_TAG}"
        )

        # Body
        body = {
            "snippet": {
                "title":       title[:100],    # YouTube limit
                "description": full_description[:5000],
                "tags":        tags[:500],
                "categoryId":  config.YT_CATEGORY_ID,
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus":      config.YT_PRIVACY,
                "selfDeclaredMadeForKids": config.YT_MADE_FOR_KIDS,
            },
        }

        # Schedule if requested
        if scheduled and config.YT_PRIVACY == "public":
            publish_at = get_next_upload_time()
            body["status"]["publishAt"]      = publish_at
            body["status"]["privacyStatus"]  = "private"   # set private until scheduled time
            log.info(f"Scheduled for: {publish_at}")

        # Upload
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5,   # 5MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        log.info(f"Uploading: {video_path}")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                log.info(f"Upload progress: {pct}%")

        video_id = response.get("id", "")
        url = f"https://youtube.com/shorts/{video_id}"
        log.info(f"✅ Uploaded! {url}")
        return video_id

    except HttpError as e:
        log.error(f"YouTube API error: {e}")
        return None
    except Exception as e:
        log.error(f"Upload failed: {e}")
        return None


def set_thumbnail(video_id: str, thumbnail_path: str):
    """Upload custom thumbnail for the video."""
    try:
        youtube = get_authenticated_service()
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
        ).execute()
        log.info(f"Thumbnail set for {video_id}")
    except Exception as e:
        log.warning(f"Thumbnail upload failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", action="store_true",
                        help="Run OAuth2 authentication flow")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.auth:
        svc = get_authenticated_service()
        print("✅ YouTube authentication successful! token.json saved.")
    else:
        print("Run with --auth to authenticate YouTube account.")
