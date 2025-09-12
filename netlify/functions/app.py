# pyright: reportMissingImports=false
import os
import sys

# Ensure project root on sys.path so we can import the Flask app
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import awsgi
except Exception:
    awsgi = None

from app import app as flask_app


def handler(event, context):
    if awsgi is None:
        raise RuntimeError(
            "awsgi is not installed. Ensure it's listed in requirements.txt for Netlify."
        )
    # Adapt Flask WSGI app to AWS Lambda / API Gateway
    return awsgi.response(flask_app, event, context)
