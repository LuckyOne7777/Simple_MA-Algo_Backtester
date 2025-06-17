#SMA_functions.py
import pandas as pd
import numpy as np
import time
from numba import jit 
import math
import line_profiler
from utils import CSV_handling, plot_results
from indicators import calculate_rsi, calculate_atr
from get_data import choose_data


def update_stoploss(trade, price, last_atr, total_position, portfolio_value, control_portfolio_value, cash, control_position):
 #make a mask to filter through inactive trades and run loop over mask
    total_position = 0
    new_stop = price - (3 * last_atr)
    #mask for still active trades
    active_trade_mask = (trade[:, 6] == 1)

    update_condition_mask = (
         (trade[:, 6] == 1) & 
         (trade[:, 10] * price >=  1.2 ) & 
         (trade[:,1] < new_stop ))

    if len(trade) > 0:
        if np.any(trade[:, 6] == 1):
            total_position = trade[active_trade_mask, 2].sum()
            trade[active_trade_mask, 9] = (trade[active_trade_mask, 2] * price).astype(int)

            #conditional for updating stoploss:

            stoploss = new_stop
            trade[update_condition_mask, 10] = price
            trade[update_condition_mask, 1] = stoploss
            total_value = total_position * price + cash
            
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)
        elif np.all(trade[:, 6] == 0):
            total_value = total_position * price + cash
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

    else:
        total_value = total_position * price + cash
        total_control_value = control_position * price
        portfolio_value.append(total_value)
        control_portfolio_value.append(total_control_value)
    return trade

def SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade):
    #skip NaN rows
    if np.isnan(last_SMA_50) or np.isnan(last_SMA_200) or np.isnan(last_RSI):
                    return "hold", None
            #if buy conditions are met, buy and add a row to trade tracking df
    if last_SMA_50 > last_SMA_200 and last_RSI < 70 and cash_per_trade >= price * 1.01:
        return "buy", None
    #check current trades and sell if stoploss has been met
    if len(trade) > 0:
        for l in range (len(trade)):
             if trade[l,6] == 1:
                        if price < trade[l, 1]:
                             index = l
                             return "sell", index
    #return hold otherwise
    return "hold", None


def SMAtrade_execution(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade, last_atr, date, position, trade_num, cash, buy_num, stoploss):
    result, index = SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade)
    #if signaled buy, execute contitions
    if result == "buy":
        #assume slippage was 1% more for buying
        adjusted_price = price * 1.01
        position =  math.floor(cash_per_trade / adjusted_price)
        cash -= position * adjusted_price
        trade_num += 1
        buy_num += 1
        stoploss = round((adjusted_price - (last_atr * 3)), 2)

# Index mapping for trade DataFrame after conversion to NumPy array:
#  0: 'NUMBER'        - Trade number or ID
#  1: 'STOPLOSS'      - Stop-loss price level
#  2: 'SHARE_#'       - Number of shares bought
#  3: 'BUY_DATE'      - Date the position was opened
#  4: 'PRICE_BOUGHT'  - Price at which the asset was purchased
#  5: 'EXITDATE'      - Date the position was closed
#  6: 'ACTIVE?'       - Boolean flag for whether the trade is still open
#  7: 'W_TRADE?'      - Win flag (1 if trade was profitable, 0 if not)
#  8: 'INTIAL_VAL'    - Initial dollar value of the trade
#  9: 'VALUE'         - Current or exit value of the trade
# 10: 'LAST_UPDATE'   - Last price used to update stop-loss
# 11: 'EXIT_PRICE'    - Price at which the trade was exited


# 1 is true and 0 is false, -999 means unused value that will be updated later.

#CHANGE THIS AT SOME POINT, just use another array for dates
        new_trade = np.zeros((1, 12), dtype=object)

        new_trade[0,1] = stoploss
        new_trade[0, 2] = position
        new_trade[0,3] = date
        new_trade[0,4] = adjusted_price
        new_trade[0,5] = -999
        new_trade[0,6] = 1
        new_trade[0,7] = -999
        new_trade[0,8] = position * adjusted_price
        new_trade[0,9] = position * adjusted_price
        new_trade[0,10] = price
        new_trade[0,11] = -999

        trade = np.vstack((trade, new_trade))

    # if signaled sell, go to trade's index and update the row
    if result == "sell":
        #assume slippage was 1% less for selling
        adjusted_price = price * 0.99
        
        cash += trade[index, 2] * adjusted_price

        trade[index, 5] = date
        trade[index, 11] = adjusted_price
        trade[index, 6] = 0
        if trade[index, 9] > trade[index, 8]:
            trade[index, 7] = 1
        else:
            trade[index, 7] = 0
    return position, trade_num, cash, buy_num, stoploss, trade
#@profile #type:ignore
def complete_SMA_function():
#CHANGE THIS AT SOME POINT, just use another array for dates

    trade = np.empty((0, 12), dtype=object)


# Index mapping for trade DataFrame after conversion to NumPy array:
#  0: 'NUMBER'        - Trade number or ID
#  1: 'STOPLOSS'      - Stop-loss price level
#  2: 'SHARE_#'       - Number of shares bought
#  3: 'BUY_DATE'      - Date the position was opened
#  4: 'PRICE_BOUGHT'  - Price at which the asset was purchased
#  5: 'EXITDATE'      - Date the position was closed
#  6: 'ACTIVE?'       - Boolean flag for whether the trade is still open
#  7: 'W_TRADE?'      - Win flag (True if trade was profitable, False if not)
#  8: 'INTIAL_VAL'    - Initial dollar value of the trade
#  9: 'VALUE'         - Current or exit value of the trade
# 10: 'LAST_UPDATE'   - Last price used to update stop-loss
# 11: 'EXIT_PRICE'    - Price at which the trade was exited

    data, ticker = choose_data()
    data = data.dropna()

    if len(data) < 200:
         raise ValueError(f"Backtest needs at least 200 days and timeframe only has {len(data)}, Try increasing or checking timeframe format.")

    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    data['RSI'] = calculate_rsi(data)
    data['ATR'] = calculate_atr(data, 14)

    data = data.values
 
    # Define starting capital and variables
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
    first_price = data[200, 1]
    control_position = math.floor(starting_cap / first_price)
    num_of_years = len(data) / 251

    # Loop over available trading days
    print("Starting test, please stand by...")
    time_start = time.time()

   # Index(['date', 'close', 'high', 'low', 'open', 'volume', 'SMA_50', 'SMA_200', 'RSI', 'ATR'])
#
#indexing works like this:
#   arr[i][0] -> 'date'        (row i, date column)
#   arr[i][1] -> 'close'       (row i, close price)
#   arr[i][2] -> 'high'        (row i, high price)
#   arr[i][3] -> 'low'         (row i, low price)
#   arr[i][4] -> 'open'        (row i, open price)
#   arr[i][5] -> 'volume'      (row i, trading volume)
#   arr[i][6] -> 'SMA_50'      (row i, 50-day simple moving average)
#   arr[i][7] -> 'SMA_200'     (row i, 200-day simple moving average)
#   arr[i][8] -> 'RSI'         (row i, Relative Strength Index)
#   arr[i][9] -> 'ATR'         (row i, Average True Range)

    price_data = []
    for i in range (len(data)):
        date = data[i, 0]
        price = data[i, 1]
        last_SMA_50 = data[i, 6]
        last_SMA_200 = data[i, 7]
        last_RSI = data[i, 8]
        last_atr = data[i, 9]
        
        # Position sizing: 5% of cash
        cash_per_trade = cash * 0.05


        position, trade_num, cash, buy_num, stoploss, trade = SMAtrade_execution(
            last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price,
            trade, last_atr, date, position, trade_num, cash, buy_num, stoploss
        )

        trade = update_stoploss(
            trade, price, last_atr, total_position, portfolio_value,
            control_portfolio_value, cash, control_position
                                )

        if i % 252 == 0:
            current_year += 1
            print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year(s) left.")

    # After loop is over
    end_time = time.time()

    price_data = pd.DataFrame({
            'Date': data[:, 0],
            'Price': data[:, 1]
        })
    price_df = price_data

    price_df.set_index('Date', inplace=True)

    sell_points = trade[trade[:, 6] == 0]
    buy_points = pd.DataFrame({'X': trade[:, 3], 'Y': trade[:, 4]})
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
        starting_cap, portfolio_df, control_portfolio_value
    )
    plot_results(ticker, buy_points, sell_points, price_df, portfolio_df, control_portfolio_df)

    print(f"Results saved successfully! Done with {ticker}")
    print(f"Program time: {round(end_time - time_start, 2)} secs")
    print(len(data))

complete_SMA_function()