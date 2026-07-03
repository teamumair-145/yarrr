import os
from enum import Enum
from flask import Flask, request, render_template, jsonify

from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from zernio import Zernio, ZernioAPIError, ZernioRateLimitError, ZernioValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

import tempfile
UPLOAD_FOLDER = tempfile.gettempdir()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB max upload

ALLOWED_EXTENSIONS = {
# Images
    "png", "jpg", "jpeg", "gif", "webp",
    "bmp", "heic", "heif", "tiff", "tif", "avif",

    # Videos
    "mp4", "mov", "avi", "webm", "mkv",
    "3gp", "3gpp", "3g2", "m4v",
    "mpeg", "mpg", "ts", "mts", "m2ts",
    "wmv", "flv", "f4v", "asf", "ogv",
}

TIKTOK_PRIVACY_LEVELS = {
    "PUBLIC_TO_EVERYONE",
    "MUTUAL_FOLLOW_FRIENDS",
    "FOLLOWER_OF_CREATOR",
    "SELF_ONLY",
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_client() -> Zernio:
    """
    Creates a Zernio client using the API key from the environment
    (ZERNIO_API_KEY, or LATE_API_KEY as a fallback — see SDK docs).
    """
    return Zernio()


def _as_dict(obj):
    """
    The SDK can return either plain dicts or typed response objects
    (e.g. Pydantic models, enums, URL types), depending on version/
    endpoint. Normalize to plain Python values (dict/list/str) so the
    rest of the app can use .get()/[...] and render cleanly.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _as_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_as_dict(v) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    # Pydantic URL types (AnyUrl, HttpUrl, etc.) stringify cleanly but
    # their __dict__ exposes private internals like {'_url': ...} —
    # catch them by class name before the generic __dict__ fallback.
    if "Url" in type(obj).__name__:
        return str(obj)
    if hasattr(obj, "model_dump"):       # pydantic v2
        return _as_dict(obj.model_dump(by_alias=True))
    if hasattr(obj, "dict") and callable(obj.dict):  # pydantic v1
        return _as_dict(obj.dict(by_alias=True))
    if hasattr(obj, "__dict__"):
        return _as_dict(vars(obj))
    return obj


@app.route("/", methods=["GET"])
def index():
    accounts = []
    error = None
    try:
        client = get_client()
        data = _as_dict(client.accounts.list()) or {}
        raw_accounts = data.get("accounts", []) or []
        accounts = []
        for a in raw_accounts:
            acc = _as_dict(a)
            # SocialAccount's id field is aliased as "_id" in the API response
            acc["id"] = acc.get("_id") or acc.get("id") or acc.get("accountId")
            accounts.append(acc)

    except Exception as e:
        error = f"Could not load connected accounts: {e}"
    return render_template("index.html", accounts=accounts, error=error)


@app.route("/post", methods=["POST"])
def create_post():
    """
    Handles the upload+post form submitted via fetch/XHR from the frontend.
    Always responds with JSON: {"success": bool, "message": str}.
    """
    content = request.form.get("content", "").strip()
    selected_platforms = request.form.getlist("platforms")  # e.g. "tiktok|acc_xxx"
    media_file = request.files.get("media")
    tiktok_privacy = request.form.get("tiktok_privacy", "").strip()

    if not selected_platforms:
        return jsonify(success=False, message="Select at least one account to post to."), 400

    client = get_client()

    # 1. Upload media (if provided)
    media_urls = []
    media_type = "image"
    filepath = None
    if media_file and media_file.filename:
        if not allowed_file(media_file.filename):
            return jsonify(success=False, message="Unsupported file type."), 400
        filename = secure_filename(media_file.filename)
        ext = filename.rsplit(".", 1)[1].lower()
        media_type = "video" if ext in {"mp4", "mov", "avi", "webm", "mkv",
    "3gp", "3gpp", "3g2", "m4v",
    "mpeg", "mpg", "ts", "mts", "m2ts",
    "wmv", "flv", "f4v", "asf", "ogv"} 
        else "image"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        media_file.save(filepath)
        try:
            result = _as_dict(client.media.upload(filepath))
            app.logger.info("media.upload() response: %r", result)

            media_url = None
            files = result.get("files")
            if files:
                first_file = _as_dict(files[0])
                raw_url = first_file.get("url")
                if raw_url is not None:
                    media_url = str(raw_url)  # AnyUrl -> plain string

            if not media_url:
                media_url = (
                    result.get("publicUrl")
                    or result.get("public_url")
                    or result.get("url")
                    or result.get("mediaUrl")
                    or result.get("media_url")
                )

            if not media_url:
                return jsonify(
                    success=False,
                    message=f"Media uploaded but no URL was returned. Raw response: {result}",
                ), 502
            media_urls.append(media_url)
        except ZernioAPIError as e:
            return jsonify(success=False, message=f"Media upload failed: {e}"), 502
        finally:
            # Clean up local copy after upload
            if filepath and os.path.exists(filepath):
                os.remove(filepath)

    # 2. Build the platforms payload: each entry is "platform|accountId"
    platforms_payload = []
    for entry in selected_platforms:
        try:
            platform, account_id = entry.split("|", 1)
        except ValueError:
            continue
        platforms_payload.append({"platform": platform, "accountId": account_id})

    # 3. Build the create() kwargs
    # Note: the installed SDK expects `media_items` (list of {"type", "url"}),
    # not `media_urls`.
    media_items = None
    if media_urls:
        media_items = [{"type": media_type, "url": url} for url in media_urls]

    post_kwargs = {
        "content": content,
        "platforms": platforms_payload,
        "publish_now": True,
    }
    if media_items:
        post_kwargs["media_items"] = media_items

    # TikTok requires tiktok_settings on every post targeting it, and the
    # privacy level must be an explicit user choice each time (TikTok's API
    # rules don't allow silently defaulting this).
    if any(p["platform"] == "tiktok" for p in platforms_payload):
        if tiktok_privacy not in TIKTOK_PRIVACY_LEVELS:
            return jsonify(
                success=False,
                message="Choose who can see this on TikTok (Public/Friends/Followers/Private).",
            ), 400
        post_kwargs["tiktok_settings"] = {
            "privacyLevel": tiktok_privacy,
            "disableComment": False,
            "disableDuet": False,
            "disableStitch": False,
        }

    # 4. Create the post
    try:
        post = _as_dict(client.posts.create(**post_kwargs))
        post_data = _as_dict(post.get("post", post))
        num_platforms = len(post_data.get("platforms", platforms_payload))
        return jsonify(success=True, message=f"Sent to {num_platforms} account(s).")

    except ZernioRateLimitError as e:
        return jsonify(success=False, message=f"Rate limited: {e}"), 429
    except ZernioValidationError as e:
        return jsonify(success=False, message=f"Invalid request: {e}"), 400
    except ZernioAPIError as e:
        return jsonify(success=False, message=f"API error: {e}"), 502


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug, port=port)
