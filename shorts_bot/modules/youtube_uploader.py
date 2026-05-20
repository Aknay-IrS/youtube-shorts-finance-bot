"""
youtube_uploader.py - Uploads Shorts to YouTube using OAuth2.
"""
import json
import logging
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def _get_token_path():
    """Find token.json - check current dir and parent dirs."""
    candidates = [
        "token.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "token.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "token.json"),
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p):
            log.info(f"Found token.json at: {p}")
            return p
    # Default
    return os.path.normpath(candidates[1])

def get_authenticated_service():
    """Load credentials from token.json and build YouTube service."""
    token_path = _get_token_path()

    if not os.path.exists(token_path):
        raise FileNotFoundError(f"token.json not found. Looked at: {token_path}")

    with open(token_path) as f:
        token_data = json.load(f)

    log.info(f"Token keys: {list(token_data.keys())}")

    # Build credentials directly from our token format
    creds = Credentials(
        token=token_data.get("token") or token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", SCOPES)
    )

    # Refresh if expired
    if not creds.valid:
        if creds.refresh_token:
            log.info("Refreshing token...")
            creds.refresh(Request())
            # Save refreshed token
            updated = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes or SCOPES)
            }
            with open(token_path, "w") as f:
                json.dump(updated, f, indent=2)
        else:
            raise ValueError("Token expired and no refresh_token available.")

    return build("youtube", "v3", credentials=creds)


def upload_short(video_path, title, description, tags, scheduled=True):
    """Upload a Short to YouTube. Returns video_id or None."""
    try:
        youtube = get_authenticated_service()

        full_description = (
            f"{description}\n\n"
            f"{'─' * 30}\n"
            f"💰 Finance tips for India every day\n"
            f"🔔 Subscribe for daily money tips\n\n"
            f"{config.YT_SHORTS_TAG}"
        )

        body = {
            "snippet": {
                "title": title[:100],
                "description": full_description[:5000],
                "tags": tags[:500],
                "categoryId": config.YT_CATEGORY_ID,
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": config.YT_MADE_FOR_KIDS,
            },
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=5*1024*1024)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        log.info(f"Uploading: {video_path}")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id", "")
        log.info(f"✅ Uploaded! https://youtube.com/shorts/{video_id}")
        return video_id

    except HttpError as e:
        log.error(f"YouTube API error: {e}")
        return None
    except Exception as e:
        log.error(f"Upload failed: {e}")
        return None


def set_thumbnail(video_id, thumbnail_path):
    """Upload custom thumbnail."""
    try:
        youtube = get_authenticated_service()
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
        ).execute()
        log.info(f"Thumbnail set for {video_id}")
    except Exception as e:
        log.warning(f"Thumbnail upload failed: {e}")
