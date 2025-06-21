#SMA_functions.py
import pandas as pd
import numpy as np
import time
from numba import jit 
import math
import line_profiler
from utils import CSV_handling, plot_results, update_stoploss
from indicators import calculate_rsi, calculate_atr
from get_data import choose_data

# Check trading conditions: buy signal logic only
# Returns "buy" or "hold" based on indicator conditions

def SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade):
    if np.isnan(last_SMA_50) or np.isnan(last_SMA_200) or np.isnan(last_RSI):
        return "hold"
    if last_SMA_50 > last_SMA_200 and last_RSI < 70 and cash_per_trade >= price * 1.01:
        return "buy"
    return "hold"

# Go through all open trades and check if current price hits stoploss
# Returns list of indices of trades that should be closed

def check_stoploss(trade, price):
    index_list = []
    if len(trade) > 0:
        for l in range(len(trade)):
            if trade[l, 6] == 1:  # Active trade
                if price < trade[l, 1]:  # If price below stoploss
                    index_list.append(l)
    return index_list

# Execute sells for trades that hit stoploss
# Updates trade matrix and cash

def sell_execution(index_list, trade, price, date, cash):
    if len(index_list) > 0:
        for i in range(len(index_list)):
            index = index_list[i]
            adjusted_price = price * 0.999  # Slippage assumption
            cash += trade[index, 2] * adjusted_price  # Sell value added to cash

            trade[index, 5] = date  # Exit date
            trade[index, 11] = adjusted_price  # Exit price
            trade[index, 6] = 0  # Mark trade inactive
            # Determine if trade was profitable
            if trade[index, 9] > trade[index, 8]:
                trade[index, 7] = 1  # Win
            else:
                trade[index, 7] = 0  # Loss
    return trade, cash

# Execute buy signals and update trade log accordingly

def SMAtrade_execution(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade, last_atr, date, position, trade_num, cash, buy_num, stoploss):
    result = SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade)

    if result == "buy":
        adjusted_price = price * 1.001  # Slippage assumption
        position = math.floor(cash_per_trade / adjusted_price)
        cash -= position * adjusted_price
        trade_num += 1
        buy_num += 1
        stoploss = round((adjusted_price - (last_atr * 3)), 2)

        # Create and add new trade row
        new_trade = np.zeros((1, 12), dtype=object)
        new_trade[0, 1] = stoploss             # Stoploss
        new_trade[0, 2] = position             # Shares
        new_trade[0, 3] = date                 # Buy date
        new_trade[0, 4] = adjusted_price       # Price bought
        new_trade[0, 5] = -999                 # Exit date
        new_trade[0, 6] = 1                    # Active flag (true)
        new_trade[0, 7] = -999                 # Win flag (unknown currently)
        new_trade[0, 8] = position * adjusted_price  # Initial value
        new_trade[0, 9] = position * adjusted_price  # Current value
        new_trade[0, 10] = price               # Last update price
        new_trade[0, 11] = -999                # Exit price (unknown currently)

        trade = np.vstack((trade, new_trade))

    return position, trade_num, cash, buy_num, stoploss, trade

# Main strategy runner
# Handles indicator calculation, looping, trade execution, logging, and plotting

def complete_SMA_function():
    trade = np.empty((0, 12), dtype=object)

    data, ticker = choose_data()
    data = data.dropna()

    if len(data) < 200:
        raise ValueError(f"Backtest needs at least 200 days and dataframe only has {len(data)}, Try increasing or checking timeframe format.")

    # Calculate indicators
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    data['RSI'] = calculate_rsi(data)
    data['ATR'] = calculate_atr(data, 14)

    data = data.values  # Convert to NumPy for speed

    # Initialize capital and tracking variables
    capital = 10000
    starting_cap = capital
    position = 0
    cash = capital
    portfolio_value = []
    control_portfolio_value = []
    price_data = []
    trade_num = 0
    buy_num = 0
    stoploss = 0
    total_position = 0
    current_year = 0
    first_price = data[0, 1]
    control_position = math.floor(starting_cap / first_price)
    num_of_years = math.ceil(len(data) / 252)

    print("Starting test, please stand by...")
    time_start = time.time()

    for i in range(len(data)):
        date = data[i, 0]
        price = data[i, 1]
        last_SMA_50 = data[i, 6]
        last_SMA_200 = data[i, 7]
        last_RSI = data[i, 8]
        last_atr = data[i, 9]

        cash_per_trade = cash * 0.05

        index_list = check_stoploss(trade, price)
        trade, cash = sell_execution(index_list, trade, price, date, cash)

        position, trade_num, cash, buy_num, stoploss, trade = SMAtrade_execution(
            last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price,
            trade, last_atr, date, position, trade_num, cash, buy_num, stoploss
        )

        trade = update_stoploss(
            trade, price, last_atr, total_position, portfolio_value,
            control_portfolio_value, cash, control_position
        )

        if num_of_years - current_year >= 1:
            if i % 252 == 0 and not (num_of_years - current_year == 1):
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} years left.")
                current_year += 1
            elif i % 252 == 0 and num_of_years - current_year == 1:
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year left.")
                current_year += 1

    # Wrap-up and export
    end_time = time.time()

    trade

    price_data = pd.DataFrame({
        'Date': data[:, 0],
        'Price': data[:, 1]
    })
    price_df = price_data
    price_df.set_index('Date', inplace=True)

    sell_points = trade[trade[:, 6] == 0]  # Trades that exited
    buy_points = pd.DataFrame({'X': trade[:, 3], 'Y': trade[:, 4]})  # Buy signals

    portfolio_df = pd.DataFrame({
        'Date': data[:, 0],
        'Portfolio_Value': portfolio_value
    })
    portfolio_df.set_index('Date', inplace=True)

    control_portfolio_df = pd.DataFrame({
        'Date': data[:, 0],
        'Control_Portfolio_Value': control_portfolio_value
    })
    control_portfolio_df.set_index('Date', inplace=True)

    if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
        raise ValueError("Cannot save: Empty portfolio data.")

    CSV_handling(
        portfolio_value, trade_num, num_of_years, ticker,
        starting_cap, portfolio_df, control_portfolio_value,
        trade
    )
    plot_results(ticker, buy_points, sell_points, price_df, portfolio_df, control_portfolio_df)

    print(f"Program time: {round(end_time - time_start, 2)} secs")
    print(num_of_years)


complete_SMA_function()
