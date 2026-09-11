from fetch_binance import get_klines


print("Testing improved Binance fetcher...")

data = get_klines(
    "15m",
    1789153200000
)

print("Request successful!")
print("Candles received:", len(data))

print("\nFirst candle:")
print(data[0])

print("\nLast candle:")
print(data[-1])