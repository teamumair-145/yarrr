# TikTok Automation — by Umair Hassan

A Flask web app for posting videos/images straight to your connected social
accounts (TikTok and others) using the [Zernio](https://zernio.com/) Python
SDK, with a mobile-friendly upload UI.

## What it does

- Loads your connected accounts (`client.accounts.list()`) and lists them
  as selectable "Send to" rows.
- Lets you drag-and-drop or tap to upload a video/image, write a caption,
  pick which accounts to send to, and (for TikTok) choose who can see the
  post — Public, Friends, Followers, or Private. TikTok requires this
  choice to be made explicitly on every post; there's no saved default.
- On **Send**: uploads the media (`client.media.upload`) with a live
  percentage shown on the button, then creates the post
  (`client.posts.create`), publishing immediately.

## Setup

1. **Unzip and enter the folder**

   ```bash
   cd zernio-flask-app
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set your API key**

   Copy `.env.example` to `.env` and fill in your real values:

   ```bash
   cp .env.example .env
   ```

   ```
   ZERNIO_API_KEY=your-real-api-key
   FLASK_SECRET_KEY=change-me-to-something-random
   FLASK_DEBUG=1
   ```

4. **Run the app**

   ```bash
   python app.py
   ```

   Visit http://localhost:5000

## Deploying

See [`DEPLOY_PYTHONANYWHERE.md`](./DEPLOY_PYTHONANYWHERE.md) for step-by-step
PythonAnywhere deployment instructions, including the ready-made
`pythonanywhere_wsgi.py` file.

## Notes / things you may need to tweak

- **Account ID field**: The app assumes each account returned by
  `client.accounts.list()` has an `id` field, used as the `accountId` when
  posting. If the Zernio API returns a differently-named field (e.g.
  `accountId` instead of `id`), update `templates/index.html` where it
  builds `value="{{ account.platform }}|{{ account.id }}"`.
- **File size limit**: Set via `MAX_CONTENT_LENGTH` in `app.py` (currently
  500 MB). Adjust as needed.
- **TikTok visibility**: `app.py` requires a `tiktok_privacy` value
  (`PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, or
  `SELF_ONLY`) whenever a TikTok account is included, matching TikTok's
  own API requirement that this be a per-post user choice.
- **Platform-specific content**: Not exposed in this UI, but you can
  extend `create_post()` in `app.py` to add a `platformSpecificContent`
  field per platform, following the SDK's example.
- This app calls the synchronous Zernio client. If you'd rather use the
  async client (`client.posts.acreate`, etc.), swap in Flask's async view
  support or a framework like FastAPI.

## Project structure

```
zernio-flask-app/
├── app.py                        # Flask routes & Zernio SDK calls
├── templates/
│   └── index.html                # Upload/post UI
├── uploads/                       # Temp storage for uploads before sending to Zernio
├── requirements.txt
├── .env.example
├── pythonanywhere_wsgi.py        # Drop-in WSGI file for PythonAnywhere
├── DEPLOY_PYTHONANYWHERE.md      # Deployment walkthrough
└── .gitignore
```
