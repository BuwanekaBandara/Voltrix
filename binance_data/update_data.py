import pandas as pd
import time
import os
import sys

from fetch_binance import get_klines, process_data


# ==============================
# Settings
# ==============================

SYMBOL = "BTCUSDT"

DATA_FOLDER = "data"


# ==============================
# Determine interval
# ==============================

if len(sys.argv) != 2:

    print("Usage:")
    print("python update_data.py 15m")
    print("python update_data.py 1w")

    sys.exit()


interval = sys.argv[1]


if interval not in ["15m", "1w"]:

    print("Error: timeframe must be 15m or 1w")

    sys.exit()


# ==============================
# File paths
# ==============================

csv_file = os.path.join(
    DATA_FOLDER,
    f"{SYMBOL}_{interval}.csv"
)

parquet_file = os.path.join(
    DATA_FOLDER,
    f"{SYMBOL}_{interval}.parquet"
)


# ==============================
# Check existing dataset
# ==============================

if not os.path.exists(csv_file):

    print("Error: Existing CSV dataset not found.")

    sys.exit()


# ==============================
# Load existing data
# ==============================

print()
print("==============================")
print(" Binance Incremental Updater")
print("==============================")
print()

print("Symbol:", SYMBOL)
print("Timeframe:", interval)
print()

print("Loading existing dataset...")

df = pd.read_csv(csv_file)

df["open_time"] = pd.to_datetime(
    df["open_time"],
    utc=True
)

df["close_time"] = pd.to_datetime(
    df["close_time"],
    format="mixed",
    utc=True
)

print("Existing candles:", len(df))


# ==============================
# Find latest candle
# ==============================

latest_open_time = df["open_time"].max()

print(
    "Latest stored candle:",
    latest_open_time
)


# ==============================
# Convert timestamp to milliseconds
# ==============================

start_time = int(
    latest_open_time.timestamp() * 1000
)


# ==============================
# Download new candles
# ==============================

print()
print("Checking Binance for new data...")

new_data = get_klines(
    interval,
    start_time
)


print(
    "Candles received:",
    len(new_data)
)


# ==============================
# No new data
# ==============================

if not new_data:

    print()
    print("Dataset is already up to date.")

    sys.exit()


# ==============================
# Process new data
# ==============================

new_df = process_data(new_data)


# ==============================
# Combine datasets
# ==============================

combined_df = pd.concat(
    [
        df,
        new_df
    ],
    ignore_index=True
)


# Remove duplicate candles
combined_df = combined_df.drop_duplicates(
    subset=["open_time"],
    keep="last"
)


# Sort chronologically
combined_df = combined_df.sort_values(
    "open_time"
)

# Save updated dataset
combined_df.to_csv(
    csv_file,
    index=False
)

combined_df.to_parquet(
    parquet_file,
    index=False
)

# ==============================
# Remove currently open candle
# ==============================

print(
    "Final candles:",
    len(combined_df)
)

print(
    "Latest stored candle:",
    combined_df["open_time"].max()
)


# ==============================
# Final information
# ==============================

print()
print("==============================")
print(" Update Complete")
print("==============================")
print()

print(
    "Previous candles:",
    len(df)
)

print(
    "New candles received:",
    len(new_df)
)

print(
    "Final candles:",
    len(combined_df)
)

print(
    "Latest stored candle:",
    combined_df["open_time"].max()
)

print()
print("Updated files:")
print(csv_file)
print(parquet_file)