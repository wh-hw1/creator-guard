"""YouTube Data API v3로 영상의 공개 댓글을 가져옵니다."""

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import requests

API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
MAX_COMMENTS = 50
KST = timezone(timedelta(hours=9))

VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}


class YouTubeError(Exception):
    """사용자에게 그대로 보여줄 수 있는 안내 메시지를 담은 오류."""


def extract_video_id(url: str) -> str | None:
    """유튜브 URL에서 영상 ID(11자리)를 꺼냅니다. 찾지 못하면 None.

    지원 형식: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/shorts/ID,
    youtube.com/embed/ID, youtube.com/live/ID
    """
    url = url.strip()
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    parts = [p for p in parsed.path.split("/") if p]

    candidate = None
    if host == "youtu.be" and parts:
        candidate = parts[0]
    elif host in YOUTUBE_HOSTS:
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [None])[0]
        elif len(parts) >= 2 and parts[0] in ("shorts", "embed", "live"):
            candidate = parts[1]

    if candidate and VIDEO_ID_PATTERN.match(candidate):
        return candidate
    return None


def fetch_comments(video_id: str, api_key: str) -> list[dict]:
    """영상의 최상위 공개 댓글을 최대 50개 가져옵니다.

    실패하면 YouTubeError를 발생시킵니다.
    """
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": MAX_COMMENTS,
        "textFormat": "plainText",
        "key": api_key,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=10)
    except requests.RequestException:
        raise YouTubeError("YouTube 서버에 연결하지 못했습니다. 인터넷 연결을 확인하고 잠시 후 다시 시도해 주세요.")

    if response.status_code != 200:
        raise YouTubeError(_error_message(response))

    comments = []
    for item in response.json().get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        comments.append(
            {
                "id": item["snippet"]["topLevelComment"]["id"],
                "author": snippet.get("authorDisplayName", "(이름 없음)"),
                "published_at": _format_time(snippet.get("publishedAt", "")),
                "text": snippet.get("textDisplay", ""),
            }
        )
    return comments


def _error_message(response: requests.Response) -> str:
    try:
        error = response.json().get("error", {})
    except ValueError:
        error = {}
    reasons = {e.get("reason") for e in error.get("errors", [])}

    if "commentsDisabled" in reasons:
        return "이 영상은 댓글이 비활성화되어 있어 댓글을 가져올 수 없습니다."
    if "videoNotFound" in reasons or response.status_code == 404:
        return "영상을 찾을 수 없습니다. 삭제되었거나 비공개 영상인지 확인해 주세요."
    if reasons & {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
        return "오늘 사용할 수 있는 YouTube API 요청량을 모두 사용했습니다. 내일 다시 시도해 주세요."
    if reasons & {"keyInvalid", "keyExpired"} or "API key" in error.get("message", ""):
        return "YouTube API 키가 올바르지 않습니다. Secrets에 저장한 키를 확인해 주세요."
    if reasons & {"accessNotConfigured", "forbidden", "ipRefererBlocked"} or response.status_code == 403:
        return "YouTube API 접근이 거부되었습니다. Google Cloud에서 YouTube Data API v3가 사용 설정되어 있는지, 키 제한 설정이 올바른지 확인해 주세요."
    return f"YouTube API 요청 중 오류가 발생했습니다. (오류 코드 {response.status_code}) 잠시 후 다시 시도해 주세요."


def _format_time(iso_time: str) -> str:
    """'2026-10-14T03:21:00Z' → '2026-10-14 12:21' (한국 시간)."""
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    except ValueError:
        return iso_time
    return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M")
