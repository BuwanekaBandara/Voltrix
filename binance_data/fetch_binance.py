import requests
import pandas as pd
import time
import os
import sys


# ==============================
# Binance API settings
# ==============================

BASE_URL = "https://api.binance.com/api/v3/klines"

SYMBOL = "BTCUSDT"

LIMIT = 1000


# ==============================
# Columns returned by Binance
# ==============================

COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "number_of_trades",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore"
]


# ==============================
# Get data from Binance
# ==============================

def get_klines(interval, start_time):

    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "startTime": start_time,
        "limit": LIMIT
    }

    max_retries = 5

    for attempt in range(max_retries):

        try:

            response = requests.get(
                BASE_URL,
                params=params,
                timeout=30
            )

            # Rate limit
            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:
                    wait_time = int(retry_after)
                else:
                    wait_time = 2 ** attempt

                print(
                    f"Rate limit reached. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            # Binance/server temporary errors
            if response.status_code >= 500:

                wait_time = 2 ** attempt

                print(
                    f"Server error "
                    f"({response.status_code}). "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:

            wait_time = 2 ** attempt

            print(
                f"Request timed out. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

        except requests.exceptions.ConnectionError:

            wait_time = 2 ** attempt

            print(
                f"Connection error. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

    raise RuntimeError(
        "Failed to retrieve data after "
        f"{max_retries} attempts."
    )


# ==============================
# Download historical data
# ==============================

def fetch_historical_data(interval, start_time):

    all_data = []

    current_start = start_time

    while True:

        print(f"Downloading candles... Total collected: {len(all_data)}")

        data = get_klines(
            interval,
            current_start
        )

        # No more data available
        if not data:
            break

        all_data.extend(data)

        # Get timestamp of the last candle
        last_open_time = data[-1][0]

        # Start after the last candle
        current_start = last_open_time + 1

        # If Binance returned fewer than 1000,
        # we have reached the latest available data.
        if len(data) < LIMIT:
            break

        # Small delay between requests
        time.sleep(0.2)

    return all_data


# ==============================
# Process the data
# ==============================

def process_data(data):

    df = pd.DataFrame(
        data,
        columns=COLUMNS
    )

    # Remove unused Binance field
    df = df.drop(
        columns=["ignore"]
    )

    # Convert timestamps
    df["open_time"] = pd.to_datetime(
        df["open_time"],
        unit="ms",
        utc=True
    )

    df["close_time"] = pd.to_datetime(
        df["close_time"],
        unit="ms",
        utc=True
    )

    # Convert numerical columns
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "number_of_trades",
        "taker_buy_base_volume",
        "taker_buy_quote_volume"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column]
        )

    # Remove duplicate candles
    df = df.drop_duplicates(
        subset=["open_time"]
    )

    # Sort chronologically
    df = df.sort_values(
        "open_time"
    )

    return df


# ==============================
# Main program
# ==============================

def main():

    # Check timeframe argument
    if len(sys.argv) != 2:

        print("Usage:")
        print("python fetch_binance.py 15m")
        print("python fetch_binance.py 1w")

        return

    interval = sys.argv[1]

    # Only allow the two project timeframes
    if interval not in ["15m", "1w"]:

        print("Error: timeframe must be 15m or 1w")

        return

    # Create data folder if it doesn't exist
    os.makedirs(
        "data",
        exist_ok=True
    )

    # Binance BTCUSDT historical data starts around 2017.
    start_time = 0

    print()
    print("==============================")
    print(" Binance BTCUSDT Data Fetcher")
    print("==============================")
    print()

    print("Symbol:", SYMBOL)
    print("Timeframe:", interval)
    print()

    print("Starting download...")
    print()

    data = fetch_historical_data(
        interval,
        start_time
    )

    print()
    print("Download complete!")
    print("Total candles:", len(data))

    # Convert to DataFrame
    df = process_data(data)

    # File names
    csv_file = f"data/BTCUSDT_{interval}.csv"

    parquet_file = f"data/BTCUSDT_{interval}.parquet"

    # Save CSV
    df.to_csv(
        csv_file,
        index=False
    )

    # Save Parquet
    df.to_parquet(
        parquet_file,
        index=False
    )

    print()
    print("Files created:")
    print(csv_file)
    print(parquet_file)

    print()
    print("First 5 rows:")
    print(df.head())

    print()
    print("Last 5 rows:")
    print(df.tail())


if __name__ == "__main__":
    main()