# PythonAnywhere WSGI configuration.
#
# On PythonAnywhere, go to the "Web" tab -> your web app -> "WSGI configuration file"
# and REPLACE its contents with the code below (or paste this file's contents in).
# Only change YOUR_USERNAME and, if you renamed the project folder, PROJECT_DIR.

import sys
import os

YOUR_USERNAME = "yourusername"          # <-- change this
PROJECT_DIR = "zernio-flask-app"        # <-- change if you renamed the folder

project_home = f"/home/{YOUR_USERNAME}/{PROJECT_DIR}"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load the .env file that sits next to app.py (ZERNIO_API_KEY, etc.)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, ".env"))

from app import app as application
