from sumsub_client import request

print("\n=== SUMSUB TRANSACTION MONITORING TEST ===")

path = "/resources/kyt/currency?type=crypto"

response = request("GET", path)

print("HTTP status:", response.status_code)

try:
    data = response.json()

    if response.status_code == 200:
        print("TM API acessível.")
        print("Primeiras moedas suportadas:")

        for item in data[:10]:
            print(
                item.get("currencyCode"),
                item.get("cryptoChain", "")
            )
    else:
        print(data)

except Exception:
    print(response.text)
