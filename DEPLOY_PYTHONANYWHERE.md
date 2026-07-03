# Deploying to PythonAnywhere

These steps use PythonAnywhere's free "Manual configuration" web app, which
works well for a small Flask app like this one.

## 1. Upload the project

1. Log in to PythonAnywhere → **Files** tab.
2. Upload `zernio-flask-app.zip` (or use **Consoles → Bash** and `git clone` /
   `wget` it in).
3. In a Bash console, unzip it into your home directory:
   ```bash
   cd ~
   unzip zernio-flask-app.zip
   cd zernio-flask-app
   ```

## 2. Create a virtualenv and install dependencies

In the same Bash console:

```bash
mkvirtualenv --python=/usr/bin/python3.10 zernio-env
pip install -r requirements.txt
```

(If `mkvirtualenv` isn't available, use: `python3.10 -m venv ~/.virtualenvs/zernio-env`
then `source ~/.virtualenvs/zernio-env/bin/activate` and `pip install -r requirements.txt`.)

## 3. Set your environment variables

```bash
cp .env.example .env
nano .env
```

Fill in:
```
ZERNIO_API_KEY=your-real-api-key
FLASK_SECRET_KEY=some-long-random-string
FLASK_DEBUG=0
```
Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

## 4. Create the web app

1. Go to the **Web** tab → **Add a new web app**.
2. Choose **Manual configuration** (not "Flask") → pick the Python version
   matching your virtualenv (e.g. 3.10).
3. Under **Virtualenv**, enter the path: `/home/YOUR_USERNAME/.virtualenvs/zernio-env`
4. Under **Code**:
   - Source code: `/home/YOUR_USERNAME/zernio-flask-app`
   - Working directory: `/home/YOUR_USERNAME/zernio-flask-app`
5. Click the **WSGI configuration file** link and replace its entire contents
   with what's in `pythonanywhere_wsgi.py` from this project — just update
   `YOUR_USERNAME` (and `PROJECT_DIR` if you renamed the folder).

## 5. Reload and test

Click the big green **Reload** button on the Web tab, then open your
`YOUR_USERNAME.pythonanywhere.com` URL. You should see the TikTok
Automation page.

## Notes

- Free PythonAnywhere accounts can only make outbound requests to a limited
  set of external sites. If the Zernio API domain isn't on that allowlist,
  you'll see connection errors — either request it be added (Account →
  "Whitelisted Sites") or use a paid plan, which allows unrestricted
  outbound access.
- Every time you change `app.py` or the templates, click **Reload** on the
  Web tab again for changes to take effect.
- Uploaded files are temporarily written to `uploads/` and deleted right
  after being sent to Zernio, so no extra disk cleanup is needed.
