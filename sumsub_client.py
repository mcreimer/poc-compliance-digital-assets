import os
import time
import hmac
import hashlib

import requests
from dotenv import load_dotenv

load_dotenv()

SUMSUB_APP_TOKEN = os.getenv("SUMSUB_APP_TOKEN")
SUMSUB_SECRET_KEY = os.getenv("SUMSUB_SECRET_KEY")

BASE_URL = "https://api.sumsub.com"


def _validate_config():
    missing = []

    if not SUMSUB_APP_TOKEN:
        missing.append("SUMSUB_APP_TOKEN")

    if not SUMSUB_SECRET_KEY:
        missing.append("SUMSUB_SECRET_KEY")

    if missing:
        raise RuntimeError(
            "Missing Sumsub configuration: "
            + ", ".join(missing)
            + ". Configure the local .env file before calling the API."
        )


def create_signature(ts, method, path, body=""):
    _validate_config()

    message = ts + method.upper() + path + body

    signature = hmac.new(
        SUMSUB_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return signature


def request(method, path, body=""):
    _validate_config()

    ts = str(int(time.time()))

    signature = create_signature(
        ts,
        method,
        path,
        body,
    )

    headers = {
        "X-App-Token": SUMSUB_APP_TOKEN,
        "X-App-Access-Ts": ts,
        "X-App-Access-Sig": signature,
        "Accept": "application/json",
    }

    if body:
        headers["Content-Type"] = "application/json"

    response = requests.request(
        method,
        BASE_URL + path,
        headers=headers,
        data=body if body else None,
        timeout=30,
    )

    return response
