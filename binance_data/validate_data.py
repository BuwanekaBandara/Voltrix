import pandas as pd
import sys


# ==============================
# Check timeframe argument
# ==============================

if len(sys.argv) != 2:

    print("Usage:")
    print("python validate_data.py 15m")
    print("python validate_data.py 1w")

    sys.exit()


interval = sys.argv[1]


if interval not in ["15m", "1w"]:

    print("Error: timeframe must be 15m or 1w")

    sys.exit()


# ==============================
# File settings
# ==============================

FILE = f"data/BTCUSDT_{interval}.csv"


if interval == "15m":

    expected_difference = pd.Timedelta(minutes=15)

else:

    expected_difference = pd.Timedelta(days=7)


# ==============================
# Load dataset
# ==============================

print("Loading dataset...")

df = pd.read_csv(FILE)


df["open_time"] = pd.to_datetime(
    df["open_time"],
    utc=True
)

df["close_time"] = pd.to_datetime(
    df["close_time"],
    format="mixed",
    utc=True
)


# ==============================
# Basic information
# ==============================

print("\n========== BASIC INFORMATION ==========")

print("Timeframe:", interval)
print("Rows:", len(df))
print("Columns:", len(df.columns))

print("First candle:", df["open_time"].min())
print("Last candle:", df["open_time"].max())


# ==============================
# Missing values
# ==============================

print("\n========== MISSING VALUES ==========")

print(df.isnull().sum())


# ==============================
# Duplicate timestamps
# ==============================

print("\n========== DUPLICATES ==========")

duplicates = df["open_time"].duplicated().sum()

print("Duplicate timestamps:", duplicates)


# ==============================
# OHLC validation
# ==============================

print("\n========== OHLC VALIDATION ==========")

invalid_ohlc = df[
    (df["high"] < df["open"]) |
    (df["high"] < df["close"]) |
    (df["low"] > df["open"]) |
    (df["low"] > df["close"]) |
    (df["high"] < df["low"])
]

print("Invalid OHLC rows:", len(invalid_ohlc))


# ==============================
# Negative values
# ==============================

print("\n========== NEGATIVE VALUES ==========")

negative_volume = (
    df["volume"] < 0
).sum()

negative_prices = (
    (df["open"] < 0) |
    (df["high"] < 0) |
    (df["low"] < 0) |
    (df["close"] < 0)
).sum()

print("Negative volume:", negative_volume)
print("Negative prices:", negative_prices)


# ==============================
# Timestamp gaps
# ==============================

print("\n========== TIMESTAMP GAPS ==========")

time_difference = df["open_time"].diff()

gap_mask = time_difference > expected_difference

gap_indices = df.index[gap_mask]

print("Number of gaps:", len(gap_indices))

if len(gap_indices) > 0:

    gap_data = pd.DataFrame({
        "previous_time": df.loc[gap_indices - 1, "open_time"].values,
        "open_time": df.loc[gap_indices, "open_time"].values,
        "gap_duration": time_difference.loc[gap_indices].values
    })

    print("\nFirst 10 gaps:")

    print(
        gap_data.head(10).to_string(index=False)
    )


# ==============================
# Final result
# ==============================

print("\n========== VALIDATION COMPLETE ==========")

if (
    duplicates == 0
    and len(invalid_ohlc) == 0
    and negative_volume == 0
    and negative_prices == 0
):

    print("Dataset passed basic validation.")

    if len(gap_indices) > 0:

        print(
            f"Note: {len(gap_indices)} timestamp gaps were detected."
        )

else:

    print(
        "Dataset contains issues that should be investigated."
    )