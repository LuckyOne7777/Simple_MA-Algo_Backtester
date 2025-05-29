#indicators.py
import pandas as pd
import numpy as np

def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    gain_series = pd.Series(gain.flatten(), index=data.index)
    loss_series = pd.Series(loss.flatten(), index=data.index)
    avg_gain = gain_series.rolling(window=window, min_periods=1).mean()
    avg_loss = loss_series.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    rsi = round(rsi, 2)
    return rsi

def calculate_atr(data, window):
    if data.empty:
        raise ValueError("Downloaded data is empty. Check the ticker symbol or internet connection.")

    high = data['high']
    low = data['low']
    close = data['close']
    last_close = close.shift(1)

    required_cols = {'high', 'low', 'close'}
    if not required_cols.issubset(data.columns):
        raise ValueError(f"Missing one of the required columns: {required_cols}")

    tr1 = high - low
    tr2 = abs(high - last_close)
    tr3 = abs(low - last_close)

    # Create a DataFrame with correct indices for each True Range component
    true_range = pd.DataFrame({
        'tr1': tr1,
        'tr2': tr2,
        'tr3': tr3,
    })

    # Find the maximum of the three True Range components for each row
    true_range = true_range.max(axis=1)

    # Calculate the ATR as the rolling mean of true_range
    atr = round(true_range.rolling(window=window).mean(), 2)
    return atr
