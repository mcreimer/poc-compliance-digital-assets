from sumsub_client import request

print("\n=== SUMSUB API TEST ===")

path = "/resources/applicants/-/byExternalUserId/POC_TEST_DO_NOT_EXIST"

response = request("GET", path)

print("HTTP status:", response.status_code)

try:
    print("Response:", response.json())
except Exception:
    print("Response:", response.text)
