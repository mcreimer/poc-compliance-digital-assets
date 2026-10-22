import os
from dotenv import load_dotenv

load_dotenv()

app_token = os.getenv("SUMSUB_APP_TOKEN")
secret_key = os.getenv("SUMSUB_SECRET_KEY")

print("=== SUMSUB CONFIGURATION TEST ===")

if app_token:
    print("SUMSUB_APP_TOKEN: OK")
    print("Sandbox token:", app_token.startswith("sbx:"))
else:
    print("SUMSUB_APP_TOKEN: NOT FOUND")

if secret_key:
    print("SUMSUB_SECRET_KEY: OK")
else:
    print("SUMSUB_SECRET_KEY: NOT FOUND")
