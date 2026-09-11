import requests

url = "https://api.binance.com/api/v3/klines"

params = {
    "symbol": "BTCUSDT",
    "interval": "15m",
    "limit": 5
}

response = requests.get(url, params=params, timeout=30)

print("Status code:", response.status_code)

data = response.json()

print("Number of candles:", len(data))
print("\nFirst candle:")
print(data[0])