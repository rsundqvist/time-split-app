"""Health check in Python.

This is basically
    curl --fail http://localhost:8501/_stcore/health
but using requests, since curl is not installed in the final image.
"""

import requests

requests.get("http://localhost:8501/_stcore/health").raise_for_status()
