# pyright: reportMissingImports=false
try:
    from vercel_wsgi import handle
except Exception:
    handle = None

import os
import sys

# Ensure project root is on sys.path for `from app import app`
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the Flask app instance
from app import app as flask_app


def handler(event, context):
    if handle is None:
        raise RuntimeError(
            "vercel-wsgi is not installed. Install with `pip install vercel-wsgi` "
            "or ensure Vercel installs dependencies from api/requirements.txt."
        )
    return handle(event, flask_app)
