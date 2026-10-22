import argparse
import json
import sys
from urllib.parse import quote

from sumsub_client import request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True)
    parser.add_argument(
        "--external-id",
        default="POC_BANK_ALPHA"
    )
    args = parser.parse_args()

    print("\n=== SUMSUB INDIVIDUAL APPLICANT TEST ===")
    print("ExternalUserId:", args.external_id)
    print("Level:", args.level)

    # Verifica se já existe
    path = f"/resources/applicants/-;externalUserId={args.external_id}/one"
    existing = request("GET", path)

    if existing.status_code == 200:
        data = existing.json()
        print("\nApplicant já existe.")
        print("Applicant ID:", data.get("id"))
        print("Type:", data.get("type"))
        print("Review status:", data.get("review", {}).get("reviewStatus"))
        return

    if existing.status_code != 404:
        print("\nErro ao verificar applicant:")
        print(existing.status_code, existing.text)
        sys.exit(1)

    payload = {
        "externalUserId": args.external_id,
        "type": "individual",
        "fixedInfo": {
            "firstName": "Test",
            "lastName": "Alpha",
            "country": "BRA"
        },
        "metadata": [
            {
                "key": "poc",
                "value": "digital-asset-compliance"
            },
            {
                "key": "network",
                "value": "Hyperledger Besu"
            },
            {
                "key": "chainId",
                "value": "1337"
            }
        ]
    }

    body = json.dumps(payload, separators=(",", ":"))

    path = f"/resources/applicants?levelName={quote(args.level, safe='')}"

    response = request("POST", path, body)

    print("\nHTTP status:", response.status_code)

    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)
        sys.exit(1)

    if response.status_code not in (200, 201):
        sys.exit(1)

    print("\n=== APPLICANT CREATED ===")
    print("Applicant ID:", data.get("id"))
    print("ExternalUserId:", data.get("externalUserId"))
    print("Type:", data.get("type"))
    print("Review status:", data.get("review", {}).get("reviewStatus"))


if __name__ == "__main__":
    main()
